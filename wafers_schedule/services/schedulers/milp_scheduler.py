from datetime import datetime, timedelta
from itertools import product

import pyomo.environ as pe
import pyomo.opt as po

from domain_models.input_data import InputData
from domain_models.schedule import DispatchDecision, Schedule
from services.schedulers.base_scheduler import Scheduler
from utils.mip_parameters import MipParameters


class MILPScheduler(Scheduler):
    def __init__(self, input_data: InputData):
        super().__init__(input_data)
        self.wafers_list = self._initialize_wafers_list()
        self.machines_list = self._input_data.machines
        self.mip_parameters : MipParameters
        self.mip_model = None
        self.results = None
        self.mip_gap = None
        self.seconds_time_limit = None
        self.objective_value = None

    def schedule(self, mip_gap: float = 0.1, seconds_time_limit: int = 60*60, pwct_weight: float = 1) -> Schedule:
        """
        Runs the process of the BetterScheduler, it is, a MILP formulation, and 
        returns its' final `Schedule` object
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

        self._create_parameters_placeholder(pwct_weight)
        self._create_model()
        self._solve_model()
        self._extract_results()

        final_schedule_object = self._create_final_schedule_object()
        return final_schedule_object

    def _create_parameters_placeholder(self, pwct_weight: float) -> None:
        """
        Creates the placeholder that contains all the parameters of the model 
        -------
        None
        """
        priority_number = self._define_priority_number_parameter()
        compatible_assignments = self._define_compatible_assignments_parameter()
        processing_times = self._define_processing_times_parameter()
        big_m = self._define_processing_time_big_m(processing_times)
        pwct_weight, makespan_weight = self._define_objective_function_weights(pwct_weight)

        placeholder = MipParameters(priority_number, compatible_assignments, processing_times, big_m, pwct_weight, makespan_weight)
        self.mip_parameters = placeholder

    def _create_model(self) -> None:
        """
        Creates the model and all its' elements: sets, parameters, variables, 
        constraints, and objective function
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

        self.mip_model = pe.ConcreteModel()
        self.mip_model.wafers = pe.Set(initialize=wafers_set)
        self.mip_model.machines = pe.Set(initialize=machines_set)
    
    def _define_parameters(self) -> None:
        """
        Creates the parameters of the model: big M for the processing times, priority number of the wafer,
        and processing time of the wafer in the machine
        Also, here is the compatible_assignments parameter, with the aim of creating a dynamic formulation
        -------
        None
        """
        self.mip_model.priority_number = pe.Param(self.mip_model.wafers, initialize=self.mip_parameters.priority_number)
        self.mip_model.compatible_assignments = pe.Param(self.mip_model.wafers, self.mip_model.machines, initialize=self.mip_parameters.compatible_assignments)
        self.mip_model.processing_times = pe.Param(self.mip_model.wafers, self.mip_model.machines, initialize=self.mip_parameters.processing_times)
        self.mip_model.big_m = pe.Param(initialize=self.mip_parameters.big_m)
        self.mip_model.pwct_weight = pe.Param(initialize=self.mip_parameters.pwct_weight)
        self.mip_model.makespan_weight = pe.Param(initialize=self.mip_parameters.makespan_weight)

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
        self.mip_model.end_variable = pe.Var(self.mip_model.wafers, domain=pe.Reals)

    def _define_wafer_machine_assignment_variable(self) -> None:
        """
        Creates the variables to define if wafer w is processed by machine m
        -------
        None
        """
        self.mip_model.assignment_variable = pe.Var(self.mip_model.wafers, self.mip_model.machines, domain=pe.Binary)

        for wafer, machine in product(self.mip_model.wafers, self.mip_model.machines):
            if (wafer, machine) not in self.mip_model.compatible_assignments:
                del self.mip_model.assignment_variable[wafer, machine]

    def _define_wafers_to_same_machine_assignment_variable(self) -> None:
        """
        Creates the variables to define if wafer w and wafer w' are processed by machine m
        -------
        None
        """
        self.mip_model.binary_variable = pe.Var(self.mip_model.wafers, self.mip_model.wafers, self.mip_model.machines, domain=pe.Binary)

        for first_wafer, second_wafer, machine in product(self.mip_model.wafers, self.mip_model.wafers, self.mip_model.machines):
            if ((first_wafer, machine) not in self.mip_model.compatible_assignments) or ((second_wafer, machine) not in self.mip_model.compatible_assignments):
                del self.mip_model.binary_variable[first_wafer, second_wafer, machine]
    
    def _define_sequential_assignment_variable(self) -> None:
        """
        Creates the variables to define if wafer w is processed before wafer w' by machine m
        -------
        None
        """
        self.mip_model.sequence_variable = pe.Var(self.mip_model.wafers, self.mip_model.wafers, self.mip_model.machines, domain=pe.Binary)

        for first_wafer, second_wafer, machine in product(self.mip_model.wafers, self.mip_model.wafers, self.mip_model.machines):
            if ((first_wafer, machine) not in self.mip_model.compatible_assignments) or ((second_wafer, machine) not in self.mip_model.compatible_assignments) or (first_wafer >= second_wafer):
                del self.mip_model.sequence_variable[first_wafer, second_wafer, machine]
    
    def _define_makespan_variable(self) -> None:
        """
        Creates the variables to save the makespan
        -------
        None
        """
        self.mip_model.makespan_variable = pe.Var(domain=pe.Reals)
    
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
        def minimum_processing_time_rule(model, wafer, machine):
            if (wafer, machine) in model.compatible_assignments:
                expr = model.end_variable[wafer] >= model.processing_times[(wafer, machine)] * model.assignment_variable[wafer, machine]
            else:
                expr = pe.Constraint.Skip
            
            return expr
        
        self.mip_model.minimum_processing_time_constraint = pe.Constraint(self.mip_model.wafers, self.mip_model.machines, rule=minimum_processing_time_rule)
    
    def _define_one_single_machine_assignment_constraint(self) -> None:
        """
        This constraints guarantee that a wafer must be processed by one single machine
        - Note that we do not need to specify a subset of machines that can process the wafer's recipe,
        as the preprocessing step guarantees that the machine is compatible
        -------
        None
        """
        def sum_binary_constraint_rule(model, wafer):
            return sum(model.assignment_variable[wafer, machine] for machine in model.machines if (wafer, machine) in model.compatible_assignments) == 1
        
        self.mip_model.sum_binary_constraint = pe.Constraint(self.mip_model.wafers, rule=sum_binary_constraint_rule)

    def _define_feasible_sequence_constraint(self) -> None:
        """
        This constraints guarantee that wafers w and w' can be considered to be processed one after the other if and only if, 
        both wafers are processed by the same machine m
        - Note that we do not need to specify a subset of machines that can process the wafer's recipe,
        as the preprocessing step guarantees that the machine is compatible
        -------
        None
        """
        def feasible_sequence_rule(model, first_wafer, second_wafer, machine):
            if first_wafer >= second_wafer:
                expr = pe.Constraint.Skip
            elif ((first_wafer, machine) in model.compatible_assignments) and ((second_wafer, machine) in model.compatible_assignments):
                left = model.sequence_variable[first_wafer, second_wafer, machine]
                right = (model.assignment_variable[first_wafer, machine] + model.assignment_variable[second_wafer, machine]) / 2
                expr = left <= right
            else:
                expr = pe.Constraint.Skip
            return expr

        self.mip_model.feasible_sequence_constraint = pe.Constraint(self.mip_model.wafers, self.mip_model.wafers, self.mip_model.machines, rule=feasible_sequence_rule)

    def _define_sequence_times_preserving_constraint(self) -> None:
        """
        This constraints guarantee that we correctly estimate and preserve the cycle times 
        of wafers w and w' when are processed one after the other by the same machine m
        - Note that we do not need to specify a subset of machines that can process the 
        wafer's recipe, as the preprocessing step guarantees that the machine is compatible
        -------
        None
        """
        def sequence_times_preserving_before_rule(model, first_wafer, second_wafer, machine):
            if first_wafer >= second_wafer:
                expr = pe.Constraint.Skip
            elif ((first_wafer, machine) in model.compatible_assignments) and ((second_wafer, machine) in model.compatible_assignments) and (first_wafer < second_wafer):
                left = model.end_variable[first_wafer] + model.processing_times[(second_wafer, machine)] - model.end_variable[second_wafer]
                right = model.big_m * (1 - model.sequence_variable[first_wafer, second_wafer, machine]) + model.big_m * (2 - model.assignment_variable[first_wafer, machine] - model.assignment_variable[second_wafer, machine])
                expr = left <= right
            else:
                expr = pe.Constraint.Skip
            return expr

        def sequence_times_preserving_after_rule(model, first_wafer, second_wafer, machine):
            if first_wafer >= second_wafer:
                expr = pe.Constraint.Skip
            elif ((first_wafer, machine) in model.compatible_assignments) and ((second_wafer, machine) in model.compatible_assignments) and (first_wafer < second_wafer):
                left = model.end_variable[second_wafer] + model.processing_times[(first_wafer, machine)] - model.end_variable[first_wafer]
                right = model.big_m * (model.sequence_variable[first_wafer, second_wafer, machine]) + model.big_m * (2 - model.assignment_variable[first_wafer, machine] - model.assignment_variable[second_wafer, machine])
                expr = left <= right
            else:
                expr = pe.Constraint.Skip
            return expr

        self.mip_model.sequence_times_preserving_before_constraint = pe.Constraint(self.mip_model.wafers, self.mip_model.wafers, self.mip_model.machines, rule=sequence_times_preserving_before_rule)
        self.mip_model.sequence_times_preserving_after_constraint = pe.Constraint(self.mip_model.wafers, self.mip_model.wafers, self.mip_model.machines, rule=sequence_times_preserving_after_rule)

    def _define_makespan_constraint(self) -> None:
        """
        This constraints save the maximum cycle time to estimate the makespan
        -------
        None
        """
        def makespan_rule(model, wafer):
            return model.makespan_variable >= model.end_variable[wafer]
        self.mip_model.makespan_constraint = pe.Constraint(self.mip_model.wafers, rule=makespan_rule)

    def _define_objective_function(self) -> None:
        """
        It defines the objective function to be minimized
        It is a weighted function between PWCT and Makespan
        """
        def objective_function_expression(model):
            pwct_function = model.pwct_weight * sum(model.priority_number[wafer] * model.end_variable[wafer] for wafer in model.wafers)
            makespan_function = model.makespan_weight * model.makespan_variable
            return pwct_function + makespan_function

        self.mip_model.objective_function = pe.Objective(sense=pe.minimize, expr=objective_function_expression)

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

        results = solver.solve(self.mip_model, tee=True)
        self.results = results

    def _extract_results(self) -> None:
        """
        Creates the results object once the model has been solved 
        -------
        None
        """
        if (self.results.solver.status == po.SolverStatus.ok) and (self.results.solver.termination_condition in [po.TerminationCondition.optimal, po.TerminationCondition.feasible]):
            self.objective_value = pe.value(self.mip_model.objective_function)
        else:
            message = f'Problem with solver: status - {self.results.solver.status} and termination_condition - {self.results.solver.termination_condition}'
            raise Exception(message)

    def _define_priority_number_parameter(self) -> dict[str, float]:
        """
        Creates a parameter with the numeric value of the priority for each wafer 
        -------
        priority_number : dict
            Dictionary with the priority number parameter
        """
        priority_number = {wafer.name: wafer.priority_number for wafer in self.wafers_list}
        return priority_number

    def _define_compatible_assignments_parameter(self) -> dict[tuple[str, str], int]:
        """
        Creates a parameter with value 1 for the combinations wafer-machine where machine can 
        process the wafer's recipe 
        -------
        compatible_assignments : dict
            Dictionary with the compatible assignments parameter
        """
        compatible_assignments = {(wafer.name, machine.name): 1 for wafer in self.wafers_list for machine in self.machines_list if wafer.recipe in machine.processing_time_by_recipe}
        return compatible_assignments

    def _define_processing_times_parameter(self) -> dict[tuple[str, str], float]:
        """
        Creates a parameter with the processing time of a wafer in its' compatible machines 
        -------
        times : dict
            Dictionary with the processing time parameter
        """
        processing_times = {(wafer.name, machine.name): machine.processing_time_by_recipe[wafer.recipe] for wafer in self.wafers_list for machine in self.machines_list if wafer.recipe in machine.processing_time_by_recipe}
        return processing_times

    def _create_final_schedule_object(self) -> Schedule:
        """
        Creates and returns the output of the BetterScheduler
        -------
        final_schedule : Schedule
            The final Schedule object
        """
        final_schedule = []
        for wafer_name, machine_name in product(self.mip_model.wafers, self.mip_model.machines):
            if self.mip_model.assignment_variable[wafer_name, machine_name].value == 1:
                start, end = self._get_decision_times(wafer_name, machine_name)
                wafer, machine = self._pick_wafer_by_name(wafer_name), self._pick_machine_by_name(machine_name)
                decision = DispatchDecision(wafer, machine, start, end)
                final_schedule.append(decision)

        machines_sorted_by_processing_time = sorted(final_schedule, key=lambda x: (x.machine.name, x.start))
        return Schedule(machines_sorted_by_processing_time)

    def _get_decision_times(self, wafer_name: str, machine_name: str) -> tuple[datetime, datetime]:
        """
        Estimates and returns the starting and ending times of a decision: A wafer
        to machine assignment 
        """
        processing_time = self.mip_parameters.processing_times[(wafer_name, machine_name)]

        start_timedelta = self.mip_model.end_variable[wafer_name].value - processing_time
        end_timedelta = self.mip_model.end_variable[wafer_name].value

        start = self.initial_timestamp + timedelta(minutes=start_timedelta)
        end = self.initial_timestamp + timedelta(minutes=end_timedelta)
        return start, end

    @staticmethod
    def _define_objective_function_weights(pwct_weight: float) -> tuple[float, float]:
        """
        Creates the parameters of the weights of the two KPIs in the objective function, 
        PWCT and Makespan
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
        return sum(value for value in processing_times.values())
