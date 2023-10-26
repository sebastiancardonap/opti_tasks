from domain_models.machine import Machine
from domain_models.wafer import Wafer


class CsvReader:
    def __init__(self, path: str):
        """

        Parameters
        ----------
        path: str
            The directory path containing the two csv files to be read.
        """
        self._path = path

    def get_wafers(self) -> list[Wafer]:
        """

        Reads in "wafers.csv" and returns a list of `Wafer` objects.
        -------
        wafers : list[Wafer]
            The list of wafers
        """
        raise NotImplementedError

    def get_machines(self) -> list[Machine]:
        """

        Reads in "machines_recipes.csv" and returns a list of `Machine` objects.
        -------
        machines : list[Machine]
            The list of machines

        """
        raise NotImplementedError
