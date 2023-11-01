from datetime import datetime, timedelta

from domain_models.input_data import InputData
from domain_models.schedule import DispatchDecision, Schedule
from domain_models.wafer import Wafer
from services.schedulers.base_scheduler import Scheduler
from utils.evaluation import Evaluation


class LegacyScheduler(Scheduler):
    """
    Basic hard rules Scheduler
    """
    def __init__(self, input_data: InputData):
        super().__init__(input_data)
        self.wafers_list = self._initialize_wafers_list()
        self.machines_list = self._input_data.machines
        self.scheduled_wafers_names_dict: dict[str, tuple[str, datetime, datetime]] = {}
        self.current_time = 0
        self._update_wafers_compatible_assignments_by_name()

    def schedule(self) -> Schedule:
        """
        Runs the whole simulation process of the LegacyScheduler and returns its' 
        final `Schedule` object.
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
            compatible_machines = [machine.name for machine in self.machines_list if wafer.recipe in machine.processing_time_by_recipe]
            wafer.compatible_machines = compatible_machines

    def _run_simulation(self) -> bool:
        """
        Runs the simulation one event at the time and returns a boolean that indicates the 
        end of the simulation.
        Running the simulation means:
        - Assign a wafer to a machine (if there is at least one wafer waiting for a machine and 
        there is an available compatible machine)
        - Set a machine free (Based on the comparison of the timer vs its' free_time and the 
        usage of its' is_busy boolean)
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
        For all the remaining wafers to be assigned, checks if it can be assigned 
        to a compatible free machine
        -------
        None
        """
        remaining_wafers = [wafer for wafer in self.wafers_list if wafer.name not in self.scheduled_wafers_names_dict]

        if bool(remaining_wafers):
            for wafer in remaining_wafers:
                evaluation = self._evaluate_wafer_machine_assignment(wafer)

                if evaluation.is_wafer_selected:
                    self._update_assignment(evaluation)

    def _update_busy_machines(self) -> None:
        """
        For all the machines, checks if its' status can be changed to free/available
        -------
        None
        """
        busy_machines = [machine for machine in self.machines_list if machine.is_busy]

        if bool(busy_machines):
            next_time = min(machine.free_time for machine in busy_machines)

            for machine in self.machines_list:
                if machine.free_time == next_time:
                    machine.is_busy = False

            self.current_time = next_time

    def _check_simulation_termination(self) -> bool:
        """
        Checks if the simulation is already finished and returns a boolean the respective boolean
        -------
        remaining_wafers : bool
            Boolean that indicates if the simulation is already finished
        """
        remaining_wafers = [wafer for wafer in self.wafers_list if wafer.name not in self.scheduled_wafers_names_dict]
        return not bool(remaining_wafers)

    def _evaluate_wafer_machine_assignment(self, current_wafer: Wafer) -> Evaluation:
        """
        Checks if the input Wafer object can be assigned to a compatible free machine
        -------
        evaluation : Evaluation
            Evaluation object with the information of the assignment operation for 
            the Wafer object input parameter
        """
        available_machines = [machine for machine in self.machines_list if (machine.name in current_wafer.compatible_machines) and (not machine.is_busy)]
        evaluation = Evaluation(True, current_wafer.name, available_machines[0].name) if bool(available_machines) else Evaluation(False, None, None)
        return evaluation

    def _update_assignment(self, evaluation: Evaluation) -> None:
        """
        Includes the information of a feasible Wafer-Machine assignment in the schedule solution
        -------
        None

        """
        wafer_name, machine_name = evaluation.wafer_name, evaluation.machine_name
        wafer, machine = self._pick_wafer_by_name(wafer_name), self._pick_machine_by_name(machine_name)

        recipe = wafer.recipe
        processing_time = machine.processing_time_by_recipe[recipe]

        initial_time, final_time = self.current_time, self.current_time + processing_time

        self.scheduled_wafers_names_dict[wafer_name] = (machine_name, initial_time, final_time)
        machine.is_busy, machine.free_time = True, final_time

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
            wafer, machine = self._pick_wafer_by_name(wafer_name), self._pick_machine_by_name(machine_name)
            decision = DispatchDecision(wafer, machine, start, end)
            final_schedule.append(decision)

        machines_sorted_by_processing_time = sorted(final_schedule, key=lambda x: (x.machine.name, x.start))
        return Schedule(machines_sorted_by_processing_time)
