from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from itertools import product

import pyomo.environ as pe
import pyomo.opt as po

from domain_models.input_data import InputData
from domain_models.machine import Machine
from domain_models.schedule import DispatchDecision, Schedule
from domain_models.wafer import Wafer


class Scheduler(ABC):
    """
    This is an Abstract Base Class (ABC): it simply defines the base constructor and some public methods for
    all its children classes.
    You do not need to change anything in this class.
    """
    def __init__(self, input_data: InputData):
        self._input_data = input_data
        self.initial_timestamp = datetime(year=2022, month=11, day=14, hour=9, minute=0)

    @abstractmethod
    def schedule(self) -> Schedule:
        raise NotImplementedError
    
    @abstractmethod
    def _create_final_schedule_object(self) -> Schedule:
        raise NotImplementedError
    
    def _initialize_wafers_list(self) -> list:
        """
        Initializes the list of wafers based on its' priority and name, and returns it.
        -------
        wafers_list : list
            The list of wafers sorted by priority and name
        """
        wafers_list = self._input_data.wafers
        wafers_list.sort(key=lambda x: (-x.priority_number, x.name), reverse=False)
        return wafers_list
    
    def _pick_wafer_by_name(self, name: str) -> Wafer:
        """
        Finds and returns the Wafer object of the input wafer name
        -------
        wafer : Wafer
            The Wafer object to be found
        """
        return next((wafer for wafer in self.wafers_list if wafer.name == name), None)
    
    def _pick_machine_by_name(self, name: str) -> Machine:
        """
        Finds and returns the Machine object of the input machine name
        -------
        machine : Machine
            The Machine object to be found
        """
        return next((machine for machine in self.machines_list if machine.name == name), None)


class LegacyScheduler(Scheduler):
    def __init__(self, input_data: InputData):
        super().__init__(input_data)
        self.wafers_list = self._initialize_wafers_list()
        self.machines_list = self._input_data.machines
        self.scheduled_wafers_names_dict = dict()
        self.current_time = 0
        self._update_wafers_compatible_assignments_by_name()
    
    def schedule(self) -> Schedule:
        """
        Runs the whole simulation process of the LegacyScheduler and returns its' final `Schedule` object.
        -------
        final_schedule_object : Schedule
            The output of the LegacyScheduler as a `Schedule` object
        """
        terminate_simulation = False
        while not terminate_simulation:
            terminate_simulation = self._run_simulation()
        
        final_schedule_object = self._create_final_schedule_object()
        
        return final_schedule_object
    
    def _update_wafers_compatible_assignments_by_name(self) -> None:
        """
        Assigns value to the attribute compatible_machines of each wafer in the concrete instance
        It is the list of names of those machines that can process the wafer's recipe 
        -------
        None
        """
        for wafer in self.wafers_list:
            compatible_machines = [machine.name for machine in self.machines_list if wafer.recipe in machine.processing_time_by_recipe.keys()]
            wafer.compatible_machines = compatible_machines
    
    def _run_simulation(self) -> bool:
        """
        Runs the simulation one event at the time and returns a boolean that indicates the end of the simulation
        Running the simulation means:
        - Assign a wafer to a machine (if there is at least one wafer waiting for a machine and there is an available compatible machine)
        - Set a machine free (Based on the comparison of the timer vs its' free_time and the usage of its' busy boolean)
        - Terminate the simulation (All the wafers have been assigned)
        -------
        simulation_terminated : bool
            Indicates the end of the simulation
        """
        self._update_remaining_wafers()
        self._update_busy_machines()
        simulation_terminated = self._check_simulation_termination()
        return simulation_terminated
    
    def _update_remaining_wafers(self) -> None:
        """
        For all the remaining wafers to be assigned, checks if it can be assigned to a compatible free machine
        -------
        None
        """
        remaining_wafers = [wafer for wafer in self.wafers_list if wafer.name not in self.scheduled_wafers_names_dict.keys()]

        if bool(remaining_wafers):
            for wafer in remaining_wafers:
                evaluation_dict = self._evaluate_wafer_machine_assignment(wafer)

                if evaluation_dict['wafer_selected']:
                    self._update_assignment(evaluation_dict)
    
    def _update_busy_machines(self) -> None:
        """
        For all the machines, checks if its' status can be changed to free/available
        -------
        None
        """
        busy_machines = [machine for machine in self.machines_list if machine.busy is True]

        if bool(busy_machines):
            next_time = min([machine.free_time for machine in busy_machines])

            for machine in self.machines_list:
                if machine.free_time == next_time:
                    machine.busy = False
            
            self.current_time = next_time
    
    def _check_simulation_termination(self) -> bool:
        """
        Checks if the simulation is already finished and returns a boolean the respective boolean
        -------
        remaining_wafers : bool
            Boolean that indicates if the simulation is already finished
        """
        remaining_wafers = [wafer for wafer in self.wafers_list if wafer.name not in self.scheduled_wafers_names_dict.keys()]
        return not bool(remaining_wafers)
    
    def _evaluate_wafer_machine_assignment(self, current_wafer: Wafer) -> dict:
        """
        Checks if the input Wafer object can be assigned to a compatible free machine
        -------
        evaluation : dict
            Dictionary with the information of the assignment operation for the input Wafer object
        """
        available_machines = [machine for machine in self.machines_list if (machine.name in current_wafer.compatible_machines) and (machine.busy is False)]

        if bool(available_machines):
            evaluation = {'wafer_selected': True, 'wafer_name': current_wafer.name, 'machine_name': available_machines[0].name}
        else:
            evaluation = {'wafer_selected': False, 'wafer_name': None, 'machine_name': None}
        
        return evaluation
    
    def _update_assignment(self, evaluation_dict: dict) -> None:
        """
        Includes the information of a feasible Wafer-Machine assignment in the schedule solution
        -------
        None

        """
        wafer_name, machine_name = evaluation_dict['wafer_name'], evaluation_dict['machine_name']
        wafer, machine = self._pick_wafer_by_name(wafer_name), self._pick_machine_by_name(machine_name)
        
        recipe = wafer.recipe
        processing_time = machine.processing_time_by_recipe[recipe]

        initial_time, final_time = self.current_time, self.current_time + processing_time
        
        self.scheduled_wafers_names_dict[wafer_name] = (machine_name, initial_time, final_time)
        machine.busy, machine.free_time = True, final_time
    
    def _create_final_schedule_object(self) -> Schedule:
        """
        Creates and returns the output of the LegacyScheduler
        -------
        final_schedule : Schedule
            The final Schedule object
        """
        final_schedule = []
        for wafer_name, (machine_name, start, end) in self.scheduled_wafers_names_dict.items():
            start, end = self.initial_timestamp + timedelta(minutes=start), self.initial_timestamp + timedelta(minutes=end)
            decision = DispatchDecision(self._pick_wafer_by_name(wafer_name), self._pick_machine_by_name(machine_name), start, end)
            final_schedule.append(decision)
        
        final_schedule.sort(key=lambda x: (x.machine.name, x.start))
        return Schedule(final_schedule)


class BetterScheduler(LegacyScheduler):
    def __init__(self, input_data: InputData):
        super().__init__(input_data)
    
    def _evaluate_wafer_machine_assignment(self, current_wafer: Wafer) -> dict:
        """
        Checks if the input Wafer object can be assigned to a compatible free machine
        Note that this method is the only one different to the Legacy Scheduler, due to a 
        change in the prioritization rule, it is an additional step of sorting the available 
        machines list based on processing time
        -------
        evaluation : dict
            Dictionary with the information of the assignment operation for the input Wafer object
        """
        available_machines = [machine for machine in self.machines_list if (machine.name in current_wafer.compatible_machines) and (machine.busy is False)]

        if bool(available_machines):
            available_machines.sort(key=lambda x: x.processing_time_by_recipe[current_wafer.recipe])
            evaluation = {'wafer_selected': True, 'wafer_name': current_wafer.name, 'machine_name': available_machines[0].name}
        else:
            evaluation = {'wafer_selected': False, 'wafer_name': None, 'machine_name': None}
        
        return evaluation


class MILPScheduler(Scheduler):
    def __init__(self, input_data: InputData):
        super().__init__(input_data)
        self.wafers_list = self._initialize_wafers_list()
        self.machines_list = self._input_data.machines
        self.parameters_dict = dict()
        self.model = None
        self.results = None
        self.mip_gap = None
        self.seconds_time_limit = None

    def schedule(self, mip_gap=0.1, seconds_time_limit=60*60, pwct_weight: float = 1) -> Schedule:
        """
        Runs the process of the BetterScheduler, it is, a MILP formulation, and returns its' final `Schedule` object
        -------
        Parameters

        path: str
            The directory path containing the two csv files to be read.
        ----------
        Returns

        final_schedule_object : Schedule
            The output of the BetterScheduler as a `Schedule` object
        """
        self.mip_gap = mip_gap
        self.seconds_time_limit = seconds_time_limit
        self.objective_value = None

        self._define_parameters_dict(pwct_weight)
        self._create_model()
        self._solve_model()
        self._extract_results()

        final_schedule_object = self._create_final_schedule_object()
        return final_schedule_object
    
    def _define_parameters_dict(self, pwct_weight: float) -> None:
        """
        Creates the dictionary that contains all the parameters of the model 
        -------
        None
        """
        priority_number = self._define_priority_number_parameter()
        compatible_assignments = self._define_compatible_assignments_parameter()
        processing_times = self._define_processing_times_parameter()
        big_m = self._define_processing_time_big_m(processing_times)
        pwct_weight, makespan_weight = self._define_objective_function_weights(pwct_weight)

        parameters_dict = {'priority_number': priority_number, 'compatible_assignments': compatible_assignments, 'processing_times': processing_times, 
                           'big_m': big_m, 'pwct_weight': pwct_weight, 'makespan_weight': makespan_weight}
        
        self.parameters_dict = parameters_dict
    
    def _create_model(self) -> None:
        """
        Creates the model and all its' elements: sets, parameters, variables, constraints, and objective function
        -------
        None
        """
        self._initialize_optimization_model()
        self._define_parameters()
        self._define_variables()
        self._define_constraints()
        self._define_objective_function()
    
    def _initialize_optimization_model(self) -> None:
        """
        Creates the concrete model and its' sets
        - Note that there is no recipes set as it will be a dynamic formulation based on a preprocessing step
        - The preprocessing step creates a parameter for each compatible wafer-machine assignment
        - Then, the BetterScheduler will use this parameter to create variables and constraints in its' model
        -------
        None
        """
        wafers_set = [wafer.name for wafer in self.wafers_list]
        machines_set = [machine.name for machine in self.machines_list]

        self.model = pe.ConcreteModel()
        self.model.wafers = pe.Set(initialize=wafers_set)
        self.model.machines = pe.Set(initialize=machines_set)
    
    def _define_parameters(self) -> None:
        """
        Creates the parameters of the model: big M for the processing times, priority number of the wafer,
        and processing time of the wafer in the machine
        Also, here is the compatible_assignments parameter, with the aim of creating a dynamic formulation
        -------
        None
        """
        self.model.priority_number = pe.Param(self.model.wafers, initialize=self.parameters_dict['priority_number'])
        self.model.compatible_assignments = pe.Param(self.model.wafers, self.model.machines, initialize=self.parameters_dict['compatible_assignments'])
        self.model.processing_times = pe.Param(self.model.wafers, self.model.machines, initialize=self.parameters_dict['processing_times'])
        self.model.big_m = pe.Param(initialize=self.parameters_dict['big_m'])
        self.model.pwct_weight = pe.Param(initialize=self.parameters_dict['pwct_weight'])
        self.model.makespan_weight = pe.Param(initialize=self.parameters_dict['makespan_weight'])

    def _define_variables(self) -> None:
        """
        Creates the variables of the model: note the usage of the compatible_assignments parameter
        to execute a dynamic formulation of variables with multiple indexes
        -------
        None
        """
        self._define_cycle_time_variables()
        self._define_wafer_machine_assignment_variable()
        self._define_wafers_to_same_machine_assignment_variable()
        self._define_sequential_assignment_variable()
        self._define_makespan_variable()
    
    def _define_cycle_time_variables(self) -> None:
        """
        Creates the variables to define the time a wafer finishes its' cycle
        -------
        None
        """
        self.model.end_variable = pe.Var(self.model.wafers, domain=pe.Reals)

    def _define_wafer_machine_assignment_variable(self) -> None:
        """
        Creates the variables to define if wafer w is processed by machine m
        -------
        None
        """
        self.model.assignment_variable = pe.Var(self.model.wafers, self.model.machines, domain=pe.Binary)

        for wafer, machine in product(self.model.wafers, self.model.machines):
            if (wafer, machine) not in self.model.compatible_assignments:
                del self.model.assignment_variable[wafer, machine]

    def _define_wafers_to_same_machine_assignment_variable(self) -> None:
        """
        Creates the variables to define if wafer w and wafer w' are processed by machine m
        -------
        None
        """
        self.model.binary_variable = pe.Var(self.model.wafers, self.model.wafers, self.model.machines, domain=pe.Binary)

        for first_wafer, second_wafer, machine in product(self.model.wafers, self.model.wafers, self.model.machines):
            if ((first_wafer, machine) not in self.model.compatible_assignments) or ((second_wafer, machine) not in self.model.compatible_assignments):
                del self.model.binary_variable[first_wafer, second_wafer, machine]
    
    def _define_sequential_assignment_variable(self) -> None:
        """
        Creates the variables to define if wafer w is processed before wafer w' by machine m
        -------
        None
        """
        self.model.sequence_variable = pe.Var(self.model.wafers, self.model.wafers, self.model.machines, domain=pe.Binary)

        for first_wafer, second_wafer, machine in product(self.model.wafers, self.model.wafers, self.model.machines):
            if ((first_wafer, machine) not in self.model.compatible_assignments) or ((second_wafer, machine) not in self.model.compatible_assignments) or (first_wafer >= second_wafer):
                del self.model.sequence_variable[first_wafer, second_wafer, machine]
    
    def _define_makespan_variable(self) -> None:
        """
        Creates the variables to save the makespan
        -------
        None
        """
        self.model.makespan_variable = pe.Var(domain=pe.Reals)
    
    def _define_constraints(self) -> None:
        """
        Creates the constraints of the model: note the usage of the compatible_assignments parameter
        to execute a dynamic formulation of constraints that use variables with multiple indexes
        -------
        None
        """
        self._define_minimum_processing_time_constraint()
        self._define_one_single_machine_assignment_constraint()
        self._define_feasible_sequence_constraint()
        self._define_sequence_times_preserving_constraint()
        self._define_makespan_constraint()
    
    def _define_minimum_processing_time_constraint(self) -> None:
        """
        This constraints guarantee that the earliest time a wafer finishes its' cycle is at least equal to the processing time
        that its' assigned machine takes to process its' recipe
        - Note that we do not need to specify a recipe, as the preprocessing step guarantees that the machine already knows 
        the processing time of the wafer
        -------
        None
        """
        def minimum_processing_time_rule(m, wafer, machine):
            if (wafer, machine) in m.compatible_assignments:
                expr = m.end_variable[wafer] >= m.processing_times[(wafer, machine)] * m.assignment_variable[wafer, machine]
            else:
                expr = pe.Constraint.Skip
            
            return expr
        
        self.model.minimum_processing_time_constraint = pe.Constraint(self.model.wafers, self.model.machines, rule=minimum_processing_time_rule)
    
    def _define_one_single_machine_assignment_constraint(self) -> None:
        """
        This constraints guarantee that a wafer must be processed by one single machine
        - Note that we do not need to specify a subset of machines that can process the wafer's recipe,
        as the preprocessing step guarantees that the machine is compatible
        -------
        None
        """
        def sum_binary_constraint_rule(m, wafer):
            return sum(m.assignment_variable[wafer, machine] for machine in m.machines if (wafer, machine) in m.compatible_assignments) == 1
        
        self.model.sum_binary_constraint = pe.Constraint(self.model.wafers, rule=sum_binary_constraint_rule)

    def _define_feasible_sequence_constraint(self) -> None:
        """
        This constraints guarantee that wafers w and w' can be considered to be processed one after the other if and only if, 
        both wafers are processed by the same machine m
        - Note that we do not need to specify a subset of machines that can process the wafer's recipe,
        as the preprocessing step guarantees that the machine is compatible
        -------
        None
        """
        def feasible_sequence_rule(m, first_wafer, second_wafer, machine):
            if first_wafer >= second_wafer:
                expr = pe.Constraint.Skip
            elif ((first_wafer, machine) in m.compatible_assignments) and ((second_wafer, machine) in m.compatible_assignments):
                expr = m.sequence_variable[first_wafer, second_wafer, machine] <= (m.assignment_variable[first_wafer, machine] + m.assignment_variable[second_wafer, machine]) / 2
            else:
                expr = pe.Constraint.Skip
            return expr
                
        self.model.feasible_sequence_constraint = pe.Constraint(self.model.wafers, self.model.wafers, self.model.machines, rule=feasible_sequence_rule)
    
    def _define_sequence_times_preserving_constraint(self) -> None:
        """
        This constraints guarantee that we correctly estimate and preserve the cycle times of wafers w and w'
        when are processed one after the other by the same machine m
        - Note that we do not need to specify a subset of machines that can process the wafer's recipe,
        as the preprocessing step guarantees that the machine is compatible
        -------
        None
        """
        def sequence_times_preserving_before_rule(m, first_wafer, second_wafer, machine):
            if first_wafer >= second_wafer:
                expr = pe.Constraint.Skip
            elif ((first_wafer, machine) in m.compatible_assignments) and ((second_wafer, machine) in m.compatible_assignments) and (first_wafer < second_wafer):
                expr = m.end_variable[first_wafer] + m.processing_times[(second_wafer, machine)] - m.end_variable[second_wafer] <= m.big_m * (1 - m.sequence_variable[first_wafer, second_wafer, machine]) + m.big_m * (2 - m.assignment_variable[first_wafer, machine] - m.assignment_variable[second_wafer, machine])
            else:
                expr = pe.Constraint.Skip
            return expr
        
        def sequence_times_preserving_after_rule(m, first_wafer, second_wafer, machine):
            if first_wafer >= second_wafer:
                expr = pe.Constraint.Skip
            elif ((first_wafer, machine) in m.compatible_assignments) and ((second_wafer, machine) in m.compatible_assignments) and (first_wafer < second_wafer):
                expr = m.end_variable[second_wafer] + m.processing_times[(first_wafer, machine)] - m.end_variable[first_wafer] <= m.big_m * (m.sequence_variable[first_wafer, second_wafer, machine]) + m.big_m * (2 - m.assignment_variable[first_wafer, machine] - m.assignment_variable[second_wafer, machine])
            else:
                expr = pe.Constraint.Skip
            return expr
        
        self.model.sequence_times_preserving_before_constraint = pe.Constraint(self.model.wafers, self.model.wafers, self.model.machines, rule=sequence_times_preserving_before_rule)
        self.model.sequence_times_preserving_after_constraint = pe.Constraint(self.model.wafers, self.model.wafers, self.model.machines, rule=sequence_times_preserving_after_rule)
    
    def _define_makespan_constraint(self) -> None:
        """
        This constraints save the maximum cycle time to estimate the makespan
        -------
        None
        """
        def makespan_rule(m, wafer):
            return m.makespan_variable >= m.end_variable[wafer]        
        self.model.makespan_constraint = pe.Constraint(self.model.wafers, rule=makespan_rule)

    def _define_objective_function(self) -> None:
        def objective_function_expression(m):
            return m.pwct_weight * sum(m.priority_number[wafer] * m.end_variable[wafer] for wafer in m.wafers) + m.makespan_weight * m.makespan_variable
        
        self.model.objective_function = pe.Objective(sense=pe.minimize, expr=objective_function_expression)

    def _solve_model(self) -> None:
        """
        Runs the solver 
        -------
        None
        """
        solver = po.SolverFactory('glpk')
        solver.options["mipgap"] = self.mip_gap
        solver.options["tmlim"] = self.seconds_time_limit
        solver.options['wlp'] = 'output/glpk.log'

        results = solver.solve(self.model, tee=True)
        self.results = results

    def _extract_results(self) -> None:
        """
        Creates the results object once the model has been solved 
        -------
        None
        """
        if (self.results.solver.status == po.SolverStatus.ok) and (self.results.solver.termination_condition in [po.TerminationCondition.optimal, po.TerminationCondition.feasible]):
            self.objective_value = pe.value(self.model.objective_function)
        else:
            raise Exception(f'Problem with solver: status - {self.results.solver.status} and termination_condition - {self.results.solver.termination_condition}')

    def _define_priority_number_parameter(self) -> dict:
        """
        Creates a parameter with the numeric value of the priority for each wafer 
        -------
        priority_number : dict
            Dictionary with the priority number parameter
        """
        priority_number = {wafer.name: wafer.priority_number for wafer in self.wafers_list}
        return priority_number
    
    def _define_compatible_assignments_parameter(self) -> dict:
        """
        Creates a parameter with value 1 for the combinations wafer-machine where machine can process the wafer's recipe 
        -------
        compatible_assignments : dict
            Dictionary with the compatible assignments parameter
        """
        compatible_assignments = {(wafer.name, machine.name): 1 for wafer in self.wafers_list for machine in self.machines_list if wafer.recipe in machine.processing_time_by_recipe.keys()}
        return compatible_assignments
    
    def _define_processing_times_parameter(self) -> dict:
        """
        Creates a parameter with the processing time of a wafer in its' compatible machines 
        -------
        times : dict
            Dictionary with the processing time parameter
        """
        processing_times = {(wafer.name, machine.name): machine.processing_time_by_recipe[wafer.recipe] for wafer in self.wafers_list for machine in self.machines_list if wafer.recipe in machine.processing_time_by_recipe.keys()}
        return processing_times
    
    def _create_final_schedule_object(self) -> Schedule:
        """
        Creates and returns the output of the BetterScheduler
        -------
        final_schedule : Schedule
            The final Schedule object
        """
        final_schedule = []
        for wafer_name, machine_name in product(self.model.wafers, self.model.machines):
            if self.model.assignment_variable[wafer_name, machine_name].value == 1:
                processing_time = self.parameters_dict['processing_times'][(wafer_name, machine_name)]
                start_timedelta, end_timedelta = self.model.end_variable[wafer_name].value - processing_time, self.model.end_variable[wafer_name].value
                start, end = self.initial_timestamp + timedelta(minutes=start_timedelta), self.initial_timestamp + timedelta(minutes=end_timedelta)
                
                decision = DispatchDecision(self._pick_wafer_by_name(wafer_name), self._pick_machine_by_name(machine_name), start, end)
                final_schedule.append(decision)

        final_schedule.sort(key=lambda x: (x.machine.name, x.start))
        return Schedule(final_schedule)
    
    @staticmethod
    def _define_objective_function_weights(pwct_weight: float) -> tuple[float, float]:
        """
        Creates the parameters of the weights of the two KPIs in the objective function, PWCT and Makespan
        -------
        pwct_weight, makespan_weight : float, float
            Tuple of floats of the weights of the two KPIs in the objective function
        """
        if (pwct_weight < 0) or (pwct_weight > 1):
            raise Exception('pwct_weight parameter must be in [0, 1] range')
        return pwct_weight, 1 - pwct_weight
    
    @staticmethod
    def _define_processing_time_big_m(processing_times: dict) -> float:
        """
        Creates a parameter with the sum of all the processing times available in the data
        It defines a big m upper bound fir the maximum cycle time 
        -------
        big_m : float
            Float equal to the sum of all the processing times
        """
        return sum([value for value in processing_times.values()])
