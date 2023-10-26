from abc import ABC, abstractmethod

from domain_models.input_data import InputData
from domain_models.schedule import Schedule


class Scheduler(ABC):
    """
    This is an Abstract Base Class (ABC): it simply defines the base constructor and some public methods for
    all its children classes.
    You do not need to change anything in this class.
    """
    def __init__(self, input_data: InputData):
        self._input_data = input_data

    @abstractmethod
    def schedule(self) -> Schedule:
        raise NotImplementedError


class LegacyScheduler(Scheduler):
    def schedule(self) -> Schedule:
        raise NotImplementedError


class BetterScheduler(LegacyScheduler):
    def schedule(self) -> Schedule:
        raise NotImplementedError

