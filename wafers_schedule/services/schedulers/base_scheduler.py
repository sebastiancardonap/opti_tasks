from abc import ABC, abstractmethod
from datetime import datetime

from domain_models.input_data import InputData
from domain_models.machine import Machine
from domain_models.schedule import Schedule
from domain_models.wafer import Wafer


class Scheduler(ABC):
    """
    This is an Abstract Base Class (ABC): it simply defines the base constructor and some 
    public methods for all its children classes.
    You do not need to change anything in this class.
    """
    def __init__(self, input_data: InputData):
        self._input_data = input_data
        self.wafers_list = None
        self.machines_list = None
        self.initial_timestamp = datetime(year=2022, month=11, day=14, hour=9, minute=0)

    @abstractmethod
    def schedule(self) -> Schedule:
        """
        Abstract method: Execute Scheduler scheduling process
        """
        raise NotImplementedError

    @abstractmethod
    def _create_final_schedule_object(self) -> Schedule:
        """
        Abstract method: Create a Schedule object based on the scheduling solution
        """
        raise NotImplementedError

    def _initialize_wafers_list(self) -> list[Wafer]:
        """
        Initializes the list of wafers based on its' priority and name, and returns it.
        -------
        wafers_list : list
            The list of wafers sorted by priority and name
        """
        wafers_list = self._input_data.wafers
        return sorted(wafers_list, key=lambda x: (-x.priority_number, x.name), reverse=False)

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
