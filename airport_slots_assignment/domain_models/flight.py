from datetime import datetime


class Flight:
    def __init__(
        self,
        id: int,
        origin: str,
        destination: str,
        departure_time: datetime, 
        arrival_time: datetime
    ):
        self.id = str(id).zfill(6)
        self.origin = origin
        self.destination = destination
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.departure_weekday_name = self._set_weekday_name_name(departure_time)
        self.arrival_weekday_name = self._set_weekday_name_name(arrival_time)
        self.name = self._set_flight_name()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"
    
    def _set_flight_name(self) -> str:
        """
        Creates a name for the flight object
        -------
        name : str
            The name of the flight
        """
        return self.origin + '_' + self.destination + '_' + self.id
    
    @staticmethod
    def _set_weekday_name_name(time) -> str:
        """
        Returns the weekday name of an input datetime
        -------
        """
        return time.strftime('%A')
