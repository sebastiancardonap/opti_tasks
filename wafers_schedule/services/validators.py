from abc import ABC, abstractmethod

from domain_models.input_data import InputData
from domain_models.schedule import Schedule


class ScheduleValidator(ABC):
    """
    This is an Abstract Base Class (ABC): it simply defines the base constructor and some public methods for
    all its children classes.
    You do not need to change anything in this class.
    """
    def __init__(self, input_data: InputData, schedule: Schedule):
        self._input_data = input_data
        self._schedule = schedule

    @abstractmethod
    def validate(self):
        raise NotImplementedError


class AllWafersHaveBeenScheduled(ScheduleValidator):
    def validate(self) -> bool:
        """
        Checks that all wafers have been scheduled.
        """
        raise NotImplementedError


class AllWafersAreOnCompatibleMachines(ScheduleValidator):
    def validate(self) -> bool:
        """
        Checks that each wafer has been scheduled on a machine with a compatible recipe.
        """
        raise NotImplementedError


class NoOverlapsOnSameMachine(ScheduleValidator):
    def validate(self) -> bool:
        """
        Checks that there are no overlapping wafers scheduled on the same machine.
        """
        raise NotImplementedError


class ScheduleChecker:
    def __init__(self, input_data: InputData, schedule: Schedule):
        self._input_data = input_data
        self._schedule = schedule
        self._validator_classes = [
            AllWafersHaveBeenScheduled,
            AllWafersAreOnCompatibleMachines,
            NoOverlapsOnSameMachine,
        ]

    def check(self) -> None:
        for validator_cls in self._validator_classes:
            is_valid = validator_cls(
                schedule=self._schedule, input_data=self._input_data
            ).validate()
            print(f"{validator_cls.__name__:45s} : {'PASS' if is_valid else 'FAIL'}")
