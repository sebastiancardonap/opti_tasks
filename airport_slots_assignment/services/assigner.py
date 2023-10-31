from datetime import datetime, timedelta
from itertools import product

import pyomo.environ as pe
import pyomo.opt as po

from domain_models.input_data import InputData
from domain_models.assignment import IndividualDecision, Assignment
from domain_models.flight import Flight
from domain_models.slot import Slot


class MIPAssigner:
    def __init__(self, input_data: InputData):
        self._input_data = input_data
        self.flights_list = self._input_data.flights
        self.slots_list = self._input_data.slots
        self.parameters_dict = dict()
        self.all_coefficients_are_integer = None
        self.model = None
        self.results = None
        self.mip_gap = None
        self.seconds_time_limit = None
        self._new_slot_risk, self._violation_penalty = int(2.5 * 60), int(5 * 60)

    def assign(self, mip_gap=0.1, seconds_time_limit=60*60) -> Assignment:
        """
        Runs the process of a MIP formulation Slots Assignment, and returns its' final `Assignment` object
        -------
        Parameters

        mip_gap: float
            The solver will stop if gets a solution with a GAP equal to this parameter 
        seconds_time_limit: int
            The solver will stop if runs during this time before reaching a solution with a GAP equal to mip_gap 
        ----------
        Returns

        assignment_object : Assignment
            The output of the MIPAssigner as a `Assignment` object
        """
        self.mip_gap = mip_gap
        self.seconds_time_limit = seconds_time_limit
        self.objective_value = None

        self._define_parameters_dict()
        self._create_model()
        self._solve_model()
        self._check_correct_termination()

        print('Creating final solution object')
        assignment_object = self._create_assignment_object()
        return assignment_object
    
    def _define_parameters_dict(self) -> None:
        """
        Creates the dictionary that contains all the parameters of the model 
        -------
        None
        """
        print('Estimating parameters')

        risk_cost = self._define_risk_cost_parameter()
        slot_capacity = self._define_slot_capacity_parameter()
        parameters_dict = {'risk_cost': risk_cost, 'slot_capacity': slot_capacity, 'violation_penalty': self._violation_penalty}
        
        self.parameters_dict = parameters_dict
        self._check_coefficients_integrality(slot_capacity)
    
    def _define_risk_cost_parameter(self) -> dict:
        """
        Creates and returns the dict with the risk cost in minutes of every possible flight-slot assignment
        that does not imply a violation
        """
        compatible_assignments = dict()
        for flight, slot in product(self.flights_list, self.slots_list):
            minutes_risk = self._get_historic_slot_minutes_risk(slot.start, slot.end, flight.departure_time) if slot.is_historic else self._get_new_slot_minutes_risk(slot.start, slot.end, flight.departure_time)
            
            if minutes_risk < self._violation_penalty:
                compatible_assignments[(flight.name, slot.name)] = minutes_risk

        reduction = 1 - len(compatible_assignments) / (len(self.flights_list) * len(self.slots_list))
        format_reduction = "{:.2f}".format(100 * reduction)
        #print(f'Reduction in {format_reduction}% of the possible slots-flights assignments')
        return compatible_assignments
    
    def _define_slot_capacity_parameter(self) -> dict:
        """
        Creates and returns the dict with the capacity of all the slots
        """
        slot_capacity = dict()
        for slot in self.slots_list:
            slot_capacity[slot.name] = int(slot.capacity)
        
        return slot_capacity
    
    def _check_coefficients_integrality(self, slot_capacity: dict) -> None:
        """
        Checks if all the capacity parameters are integer values, other way raises an error
        - Note that we may use variables with Reals domain, as all of our Matrix A  and vector b
        coefficients are integers
        """
        self.all_coefficients_are_integer = all(type(value) is int for value in slot_capacity.values())
        if not self.all_coefficients_are_integer:
            print('Not all of the slots capacities are integer values. \nDouble check your data, the model will run with binary variables and may take a long time to find a solution otherwise')

    
    def _create_model(self) -> None:
        """
        Creates the model and all its' elements: sets, parameters, variables, constraints, and objective function
        -------
        None
        """
        print('Creating model')

        self._initialize_optimization_model()
        self._define_parameters()
        self._define_variables()
        self._define_constraints()
        self._define_objective_function()
    
    def _initialize_optimization_model(self) -> None:
        """
        Creates the concrete model and its' sets
        -------
        None
        """
        flights = [flight.name for flight in self.flights_list]
        slots = [slot.name for slot in self.slots_list]

        self.model = pe.ConcreteModel()
        self.model.flights = pe.Set(initialize=flights)
        self.model.slots = pe.Set(initialize=slots)
    
    def _define_parameters(self) -> None:
        """
        Creates the parameters of the model: risk in time of an assignment, capacity of each slot, and penalty 
        risk for the violations
        - Note that the risk_cost parameter only contains assignments that do not imply a violation, so then, it is 
        used to create a dynamic formulation that only takes into account those "compatible" assignments
        -------
        None
        """
        self.model.risk_cost = pe.Param(self.model.flights, self.model.slots, initialize=self.parameters_dict['risk_cost'])
        self.model.slot_capacity = pe.Param(self.model.slots, initialize=self.parameters_dict['slot_capacity'])
        self.model.violation_penalty = pe.Param(initialize=self.parameters_dict['violation_penalty'])

    def _define_variables(self) -> None:
        """
        Creates the variables of the model: note the usage of the compatible_assignments parameter
        to execute a dynamic formulation of variables
        -------
        None
        """
        self._define_flight_slot_assignment_variables()
        self._define_assigned_flight_variable()

    def _define_flight_slot_assignment_variables(self) -> None:
        """
        Creates the variables to define if flight f is assigned to slot s

        - Note that regardless of the check_coefficients_integrality, the model uses binary variables anyway
        Binary variables still take advantage of the integrality of the coefficients, because the solver will 
        use LP relaxations to find a solution
        -------
        None
        """
        self.model.flight_slot_variable = pe.Var(self.model.flights, self.model.slots, domain=pe.Binary)

        for flight, slot in product(self.model.flights, self.model.slots):
            if (flight, slot) not in self.model.risk_cost:
                del self.model.flight_slot_variable[flight, slot]
    
    def _define_assigned_flight_variable(self) -> None:
        """
        Creates the variables to define whether a flight is assigned or implies a penalty

        - Note that regardless of the check_coefficients_integrality, the model uses binary variables anyway
        Binary variables still take advantage of the integrality of the coefficients, because the solver will 
        use LP relaxations to find a solution
        -------
        None
        """
        self.model.assigned_flight_variable = pe.Var(self.model.flights, domain=pe.Binary)
    
    def _define_constraints(self) -> None:
        """
        Creates the constraints of the model: note the usage of the risk_cost parameter
        to execute a dynamic formulation of constraints
        -------
        None
        """
        self._define_flight_assigned_once_at_most_constraint()
        self._define_know_if_flight_is_assigned_constraint()
        self._define_slot_capacity_constraint()
    
    def _define_flight_assigned_once_at_most_constraint(self) -> None:
        """
        This constraints guarantee that a flight is assigned to one single slot at most
        -------
        None
        """
        def flight_assigned_once_at_most_rule(m, flight):
            expr = sum(m.flight_slot_variable[flight, slot] for slot in m.slots if (flight, slot) in m.risk_cost) <= 1
            return expr
        
        self.model.flight_assigned_once_at_most_constraint = pe.Constraint(self.model.flights, rule=flight_assigned_once_at_most_rule)
    
    def _define_know_if_flight_is_assigned_constraint(self) -> None:
        """
        This constraints guarantee that we can know if a flight is assigned without penalty
        -------
        None
        """
        def know_if_flight_is_assigned_rule(m, flight):
            expr = m.assigned_flight_variable[flight] == sum(m.flight_slot_variable[flight, slot] for slot in m.slots if (flight, slot) in m.risk_cost)
            return expr
        
        self.model.know_if_flight_is_assigned_constraint = pe.Constraint(self.model.flights, rule=know_if_flight_is_assigned_rule)
    
    def _define_slot_capacity_constraint(self) -> None:
        """
        This constraints guarantee that a flight is assigned to one single slot at most
        -------
        None
        """
        def slot_capacity_rule(m, slot):
            expr = sum(m.flight_slot_variable[flight, slot] for flight in m.flights if (flight, slot) in m.risk_cost) <= m.slot_capacity[slot]
            return expr
        
        self.model.slot_capacity_constraint = pe.Constraint(self.model.slots, rule=slot_capacity_rule)
    
    def _define_objective_function(self) -> None:
        """
        It defines the objective function to be minimized
        It is the risk of the assignment taking into account the violations penalty
        """
        def objective_function_expression(m):
            risk = sum(m.risk_cost[flight, slot] * m.flight_slot_variable[flight, slot] for flight, slot in product(self.model.flights, self.model.slots) if (flight, slot) in m.risk_cost)
            penalties = sum(m.violation_penalty * (1 - m.assigned_flight_variable[flight]) for flight in self.model.flights)
            return risk + penalties
        
        self.model.objective_function = pe.Objective(sense=pe.minimize, expr=objective_function_expression)
    
    def _solve_model(self) -> None:
        """
        Runs the solver 
        -------
        None
        """
        print('Solving model')

        solver = po.SolverFactory('glpk')
        solver.options["mipgap"] = self.mip_gap
        solver.options["tmlim"] = self.seconds_time_limit
        solver.options['wlp'] = 'data/output_data/glpk.log'

        results = solver.solve(self.model, tee=True)
        self.results = results
    
    def _check_correct_termination(self) -> None:
        """
        Creates the results object once the model has been solved 
        -------
        None
        """
        if (self.results.solver.status == po.SolverStatus.ok) and (self.results.solver.termination_condition in [po.TerminationCondition.optimal, po.TerminationCondition.feasible]):
            self.objective_value = pe.value(self.model.objective_function)
        else:
            raise Exception(f'Problem with solver: status - {self.results.solver.status} and termination_condition - {self.results.solver.termination_condition}')
    
    def _create_assignment_object(self) -> Assignment:
        """
        Creates and returns the output of the BetterScheduler
        -------
        final_schedule : Schedule
            The final Schedule object
        """
        final_schedule = []

        m = 0
        for flight_name in product(self.model.flights):
            if self.model.assigned_flight_variable[flight_name].value == 1:
                print(flight_name)
                m += 1
                #processing_time = self.parameters_dict['processing_times'][(wafer_name, machine_name)]
                #start_timedelta, end_timedelta = self.model.end_variable[wafer_name].value - processing_time, self.model.end_variable[wafer_name].value
                #start, end = self.initial_timestamp + timedelta(minutes=start_timedelta), self.initial_timestamp + timedelta(minutes=end_timedelta)
                
                #decision = IndividualDecision(self._pick_wafer_by_name(wafer_name), self._pick_machine_by_name(machine_name), start, end)
                #final_schedule.append(decision)
        
        print(len(self.model.assigned_flight_variable), m)
        print(a)

        #final_schedule.sort(key=lambda x: (x.machine.name, x.start))
        return Assignment(final_schedule)
    
    def _pick_flight_by_name(self, name: str) -> Flight:
        """
        Finds and returns the flight object of the input flight name
        -------
        flight : Flight
            The Flight object to be found
        """
        return next((flight for flight in self.flights_list if flight.name == name), None)
    
    def _pick_slot_by_name(self, name: str) -> Slot:
        """
        Finds and returns the Slot object of the input slot name
        -------
        slot : Slot
            The Slot object to be found
        """
        return next((slot for slot in self.slots_list if slot.name == name), None)
    
    def _get_historic_slot_minutes_risk(self, slot_start: datetime, slot_end: datetime, flight_departure_time: datetime) -> int:
        """
        Estimates and returns the risk of a flight-historic slot assignment as the difference in minutes
        between the departure and the slot's range

        If the assignment implies a violation, the method returns a violation_penalty as the risk
        """
        if (slot_start <= flight_departure_time) and (flight_departure_time <= slot_end):
            total_risk = 0
        else:
            start_risk = abs((slot_start - flight_departure_time).total_seconds()) / 60
            end_risk = abs((slot_end - flight_departure_time).total_seconds()) / 60
            total_risk = min(start_risk, end_risk)
        return int(total_risk) if total_risk <= 30 else self._violation_penalty

    def _get_new_slot_minutes_risk(self, slot_start: datetime, slot_end: datetime, flight_departure_time: datetime) -> int:
        """
        Estimates and returns the risk of a flight-new slot assignment as the new_slot_risk
        if the flight departure time is inside of the slot's range

        If the assignment implies a violation, the method returns a violation_penalty as the risk
        """
        total_risk = self._new_slot_risk if (slot_start <= flight_departure_time) and (flight_departure_time <= slot_end) else self._violation_penalty
        return int(total_risk)
