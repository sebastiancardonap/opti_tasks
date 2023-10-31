from domain_models.flight import Flight
from domain_models.slot import Slot

from datetime import datetime, timedelta
from dateutil import parser, tz

import pandas as pd


class CsvReader:
    def __init__(self, path: str):
        """
        Parameters
        ----------
        path: str
            The directory path containing the csvs files to be read.
        """
        self._path = path

    def get_flights(self) -> list[Flight]:
        """
        Reads in "stn_flights_departure.csv" and returns a list of `Flight` objects.
        -------
        flights_list : list[Flight]
            The list of flights
        """
        df = self._read_csv('stn_flights_departure.csv')

        current_id, flights_list = 0, list()
        for flight in df.to_dict('records'):
            origin, destination, departure_time, arrival_time = self._get_flight_data(flight)
            current_flight = Flight(id=current_id, origin=origin, destination=destination, departure_time=departure_time, arrival_time=arrival_time)
            current_id += 1
            flights_list.append(current_flight)
        
        return flights_list

    def get_slots(self, earliest_departure_time: datetime, latest_departure_time: datetime) -> list[Slot]:
        """
        Reads the slots csv files and returns a list of `Slot` objects.
        -------
        slots : list[Slot]
            The list of slots
        """
        historic_slots_list = self._get_historic_slots_list(latest_departure_time)
        new_slots_list = self._get_new_slots_list(earliest_departure_time, latest_departure_time)

        slots_list = historic_slots_list + new_slots_list
        return slots_list
    
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
    
    def _get_historic_slots_list(self, latest_time: datetime) -> list[Slot]:
        """
        Reads in "stn_historic_slots_departure.csv" and returns a list of `Slot` objects.
        -------
        slots : list[Slot]
            The list of slots
        """
        df = self._read_csv('stn_historic_slots_departure.csv')
        df = self._prepare_historic_slots_dataframe(df)
        df = self._estimate_historic_slots_closing_time(df, latest_time)

        slots_list = self._get_slots_list_from_dataframe(df=df, is_historic=True)
        return slots_list
    
    def _get_new_slots_list(self, earliest_time: datetime, latest_time: datetime) -> list[Slot]:
        """
        Reads in "stn_new_slots_departure.csv" and returns a list of `Slot` objects.
        -------
        slots : list[Slot]
            The list of slots
        """
        df = self._read_csv('stn_new_slots_departure.csv')
        df = df[df['capacity'] > 0].reset_index(drop=True)

        days_dict, current_tzinfo = self._get_weekdays_info(earliest_time, latest_time)
        df[['start', 'end']] = df.apply(lambda x: self._get_new_slot_time_range(x, days_dict, current_tzinfo), axis=1, result_type='expand')

        slots_list = self._get_slots_list_from_dataframe(df=df, is_historic=False)
        return slots_list
    
    @staticmethod
    def _get_flight_data(flight: dict) -> [str, str, datetime, datetime]:
        """
        Reads a dict with all the information of a flight and returns the attributes that the Flights Class
        needs to instantiate an object: origin, destination, departure_time, arrival_time
        -------
        origin, destination, departure_time, arrival_time
        """
        origin, destination = flight['origin'], flight['destination']
        departure_time, arrival_time = parser.parse(flight['departure']), parser.parse(flight['departure'])
        departure_time, arrival_time = departure_time.replace(second=0, microsecond=0), arrival_time.replace(second=0, microsecond=0)
        return origin, destination, departure_time, arrival_time
    
    @staticmethod
    def _prepare_historic_slots_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Gets a DataFrame with the info of the historic slots as input, and returns it back with some 
        specific characteristics, like a time column datetime format, for example
        -------
        df : pd.DataFrame
            DataFrame with the info of the historic slots
        """
        df = df[df['capacity'] > 0]
        df['time'] = df['time'].apply(pd.to_datetime)
        df = (df
              .sort_values(by='time')
              .reset_index(drop=True))
        return df
    
    @staticmethod
    def _estimate_historic_slots_closing_time(df: pd.DataFrame, latest_time: datetime) -> pd.DataFrame:
        """
        Assumption:
        As there is not a reference to estimate the closing time of the last historic slot, I assume that it
        ends 5 minutes later than the latest departing flight in the data, it is, the last slot is long enough 
        to serve the latest departure without risk

        This assumption does not have a big impact in the final results as long as the instance to solve 
        has a low capacity for this last historic slot
        """
        last_slot_closing_time = latest_time + timedelta(minutes=5)

        df.loc[len(df)] = ['generic', last_slot_closing_time, 0]
        df['one_minute_before'] = df.apply(lambda x: x.time + timedelta(minutes=-1), axis=1)
        df['end'] = df['one_minute_before'].shift(-1)
        df.drop(df.tail(1).index, inplace=True)
        return df[['airport', 'time', 'end', 'capacity']]
    
    @staticmethod
    def _get_weekdays_info(earliest_time: datetime, latest_time: datetime) -> [dict, tz]:
        """
        Returns a dict with the dates of the new slots based on their weekdays name
        Also, it returns the right time zone to continue using it in the rest of the process
        -------
        days_dict, earliest_time.tzinfo : dict, tzinfo
        """
        current_time, days_dict = earliest_time.date(), dict()
        while current_time <= latest_time.date():
            days_dict[current_time.strftime('%A')] = current_time
            current_time += timedelta(days=1)
        
        return days_dict, earliest_time.tzinfo
    
    @staticmethod
    def _get_new_slot_time_range(x: pd.Series, days_dict: dict, current_tzinfo: tz) -> [datetime, datetime]:
        """
        Uses the information of the new slots to estimate its closing time, and returns both start and closing
        times in the correct datetime format
        -------
        start, end : datetime, datetime
            start and closing times of the new slot
        """
        date, hour = days_dict[x.start_date], int(x.start_time)
        start = datetime(year=date.year, month=date.month, day=date.day, hour=hour, minute=0, second=0, tzinfo=current_tzinfo)
        end = start + timedelta(minutes=59)
        return start, end
    
    @staticmethod
    def _get_slots_list_from_dataframe(df: pd.DataFrame, is_historic: bool) -> list[Slot]:
        """
        Uses a DataFrame with the slots info as input to create a list of Slots objects
        Note the usage of a second input parameter, historic, to define whether the pipeline
        belongs to historic or new slots
        -------
        slots_list : list[Slot]
            A list of SLot objects
        """
        start_column = 'time' if is_historic else 'start'

        current_id, slots_list = 0, list()
        for slot in df.to_dict('records'):
            airport, start, end, capacity = slot['airport'], slot[start_column], slot['end'], slot['capacity']
            current_slot = Slot(id=current_id, airport=airport, start=start, end=end, is_historic=is_historic, capacity=capacity)
            slots_list.append(current_slot)
            current_id += 1
        
        return slots_list
