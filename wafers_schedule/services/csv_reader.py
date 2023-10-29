from domain_models.machine import Machine
from domain_models.wafer import Wafer

import pandas as pd


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
        df = self._read_csv('wafers.csv')

        wafers = []
        for name, priority, recipe in df.to_records(index=False):
            current_wafer = Wafer(name=name, priority=priority, recipe=recipe)
            wafers.append(current_wafer)
        
        return wafers

    def get_machines(self) -> list[Machine]:
        """
        Reads in "machines_recipes.csv" and returns a list of `Machine` objects.
        -------
        machines : list[Machine]
            The list of machines
        """
        df = self._read_csv('machines_recipes.csv')

        machines = []
        for machine in df['machine'].unique():
            current_df = df[df['machine'] == machine]
            processing_time_by_recipe = dict(zip(current_df['recipe'], current_df['processing_time']))
            current_machine = Machine(name=machine, processing_time_by_recipe=processing_time_by_recipe)
            machines.append(current_machine)
        
        return machines
    
    def _read_csv(self, file_name: str) -> pd.DataFrame:
        """
        Reads a csv file whose name is the input of the method and returns its' pandas DataFrame.
        -------
        df : pd.DataFrame
            A pandas DataFrame 
        """
        try:
            path = self._path + file_name
            df = pd.read_csv(path, sep=',')
        except Exception as error:
            raise error
        
        return df
