from datetime import datetime

from domain_models.flight import Flight
from domain_models.slot import Slot

import pandas as pd


class IndividualDecision:
    def __init__(
        self,
        flight: Flight,
        slot: Slot
    ):
        self.flight = flight
        self.slot = slot


class Assignment:
    def __init__(self, dispatch_decisions: list[IndividualDecision]):
        self.dispatch_decisions = dispatch_decisions

    def to_csv(self, output_file: str) -> None:
        """
        Writes the assignment to a csv file: csv as a result with one row per each weekday and hour

        Parameters
        ----------
        output_file: str
            The output csv file path

        Returns
        -------
        None
        """
        data = []
        for decision in self.dispatch_decisions:
            start = decision.start.strftime("%Y-%m-%d %H:%M:%S")
            decision_list = [decision.flight.airport, decision.wafer.priority, decision.machine.name, start,'<=5', '<=30', 'new', 'violations']
            data.append(decision_list)

        df = pd.DataFrame(data, columns=['airport','weekday','time','historic','<=5', '<=30', 'new', 'violations'])
        df.to_csv(path_or_buf=output_file, sep=',', index=False, header=True)
