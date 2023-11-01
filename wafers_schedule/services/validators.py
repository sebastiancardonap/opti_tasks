from abc import ABC, abstractmethod

from domain_models.input_data import InputData
from domain_models.machine import Machine
from domain_models.schedule import Schedule

from datetime import datetime


class ScheduleValidator(ABC):
    """
    This is an Abstract Base Class (ABC): it simply defines the base constructor 
    and some public methods for all its children classes.
    You do not need to change anything in this class.
    """
    def __init__(self, input_data: InputData, schedule: Schedule):
        self._input_data = input_data
        self._schedule = schedule

    @abstractmethod
    def validate(self):
        """
        Abstract method: run a validation process
        """
        raise NotImplementedError


class AllWafersHaveBeenScheduled(ScheduleValidator):
    """
    Class to check that all wafers have been scheduled.
    """
    def validate(self) -> bool:
        """
        Checks that all wafers have been scheduled.
        """
        wafers_list = self._input_data.wafers
        scheduled_wafers = [decision.wafer for decision in self._schedule.dispatch_decisions]

        return all(wafer in scheduled_wafers for wafer in wafers_list)


class AllWafersAreOnCompatibleMachines(ScheduleValidator):
    """
    Class to check if all Wafers are assigned to compatible Machines
    """
    def validate(self) -> bool:
        """
        Checks that each wafer has been scheduled on a machine with a compatible recipe.
        """
        return all(decision.wafer.recipe in decision.machine.processing_time_by_recipe for decision in self._schedule.dispatch_decisions)


class NoOverlapsOnSameMachine(ScheduleValidator):
    """
    Class to check if all Machines have none overlapping assignments
    """
    def validate(self) -> bool:
        """
        Checks that there are no overlapping wafers scheduled on the same machine.
        """
        machines_dict = self._extract_intervals_data()
        sequence_condition = all((decision.end - decision.start).total_seconds() >= 0 for decision in self._schedule.dispatch_decisions)
        overlapping_condition = self._evaluate_overlapping(machines_dict)
        return min(sequence_condition, overlapping_condition)

    def _extract_intervals_data(self) -> dict[Machine, list[dict[str, datetime]]]:
        """
        Estimates and returns the starting and ending times of all the services of 
        the machines
        """
        machines_dict = {}

        for decision in self._schedule.dispatch_decisions:
            time_interval_dict = {'start': decision.start, 'end': decision.end}

            if decision.machine in machines_dict:
                machines_dict[decision.machine].append(time_interval_dict)
            else:
                machines_dict[decision.machine] = [time_interval_dict]

        return machines_dict

    @staticmethod
    def _evaluate_overlapping(machines_dict: dict) -> bool:
        booleans_list = []
        for assignments in machines_dict.values():
            for ix, current_assignment in enumerate(assignments[:-1]):
                booleans_list.append(current_assignment['end'] <= assignments[ix+1]['start'])

        overlapping = min(booleans_list)
        return overlapping


class ScheduleChecker:
    """
    Class to run all the feasibility evaluators checking processes
    """
    def __init__(self, input_data: InputData, schedule: Schedule):
        self._input_data = input_data
        self._schedule = schedule
        self._validator_classes = [
            AllWafersHaveBeenScheduled,
            AllWafersAreOnCompatibleMachines,
            NoOverlapsOnSameMachine,
        ]

    def check(self) -> None:
        """
        Method to run all evaluations one by one
        """
        for validator_cls in self._validator_classes:
            is_valid = validator_cls(
                schedule=self._schedule, input_data=self._input_data
            ).validate()
            print(f"{validator_cls.__name__:45s} : {'PASS' if is_valid else 'FAIL'}")
