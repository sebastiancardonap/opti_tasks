from domain_models.machine import Machine
from domain_models.wafer import Wafer
from services.csv_reader import CsvReader


class InputData:
    """
    Place holder of the input data:
    - Wafers
    - Machines
    """
    def __init__(self, wafers: list[Wafer], machines: list[Machine]):
        self.wafers = wafers
        self.machines = machines

    @classmethod
    def from_csv(cls, path: str):
        """ 
        Extract the input data from its' csv files
        """
        csv_reader = CsvReader(path=path)
        wafers = csv_reader.get_wafers()
        machines = csv_reader.get_machines()
        return InputData(wafers=wafers, machines=machines)
