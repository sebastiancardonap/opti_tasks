from domain_models.flight import Flight
from domain_models.slot import Slot
from services.csv_reader import CsvReader


class InputData:
    def __init__(self, flights: list[Flight], slots: list[Slot]):
        self.flights = flights
        self._latest_departure = None
        self.slots = slots

    @classmethod
    def from_csv(cls, path: str):
        """
        Class method to instantiate the input data objects based on the respective csv files
        """
        csv_reader = CsvReader(path=path)
        flights = csv_reader.get_flights()
        earliest_departure_time, latest_departure_time = min(flight.departure_time for flight in flights), max(flight.departure_time for flight in flights)
        slots = csv_reader.get_slots(earliest_departure_time, latest_departure_time)
        return InputData(flights=flights, slots=slots)
