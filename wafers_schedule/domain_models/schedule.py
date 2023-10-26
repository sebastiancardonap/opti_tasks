from datetime import datetime

from domain_models.machine import Machine
from domain_models.wafer import Wafer


class DispatchDecision:
    def __init__(
        self,
        wafer: Wafer,
        machine: Machine,
        start: datetime,
        end: datetime,
    ):
        self.wafer = wafer
        self.machine = machine
        self.start = start
        self.end = end


class Schedule:
    def __init__(self, dispatch_decisions: list[DispatchDecision]):
        self.dispatch_decisions = dispatch_decisions

    @property
    def makespan(self) -> float:
        """

        Returns
        -------
        float : Schedule's makespan in hours
        """
        raise NotImplementedError

    @property
    def priority_weighted_cycle_time(self) -> float:
        """

        Returns
        -------
        float : Schedule's priority-weighted cycle times summed for all wafers.
        """
        raise NotImplementedError

    def to_csv(self, output_file: str) -> None:
        """
        Writes schedule to a csv file.

        Parameters
        ----------
        output_file: str
            The output csv file path

        Returns
        -------

        """
        raise NotImplementedError
