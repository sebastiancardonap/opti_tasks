from datetime import datetime

from domain_models.machine import Machine
from domain_models.wafer import Wafer

import pandas as pd


class DispatchDecision:
    """
    Class of an individual dispatch decision: How to serve a Wafer
    """
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
    """
    Class with dispatch decisions
    Capable of estimate the KPIs and save the solution to csv file
    """
    def __init__(self, dispatch_decisions: list[DispatchDecision]):
        self.dispatch_decisions = dispatch_decisions

    @property
    def makespan(self) -> float:
        """
        Returns
        -------
        float : Schedule's makespan in hours
        """
        initial_time = min([decision.start for decision in self.dispatch_decisions])
        final_time = max([decision.end for decision in self.dispatch_decisions])
        makespan_seconds = (final_time - initial_time).total_seconds()
        return self._from_seconds_to_hours(makespan_seconds)

    @property
    def priority_weighted_cycle_time(self) -> float:
        """
        Returns
        -------
        float : Schedule's priority-weighted cycle times summed for all wafers.
        """
        initial_time = min([decision.start for decision in self.dispatch_decisions])
        cycles = [decision.wafer.priority_number * (decision.end - initial_time).total_seconds() for decision in self.dispatch_decisions]
        weighted_cycle_time = sum(cycles)
        return self._from_seconds_to_hours(weighted_cycle_time)

    def to_csv(self, output_file: str) -> None:
        """
        Writes schedule to a csv file.

        Parameters
        ----------
        output_file: str
            The output csv file path

        Returns
        -------
        None
        """
        data = []
        time_format = "%Y-%m-%d %H:%M:%S"
        for decision in self.dispatch_decisions:
            start, end = decision.start.strftime(time_format), decision.end.strftime(time_format)
            decision_list = [decision.wafer.name, decision.wafer.priority, decision.machine.name, start, end]
            data.append(decision_list)

        df = pd.DataFrame(data, columns=['wafer','priority','machine','start','end'])
        df.to_csv(path_or_buf=output_file, sep=',', index=False, header=True)

    @staticmethod
    def _from_seconds_to_hours(seconds: float) -> float:
        return seconds / 3600
