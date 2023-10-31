from datetime import datetime


class Slot:
    def __init__(
        self,
        id: int,
        airport: str, 
        start: datetime, 
        end: datetime,
        is_historic: bool, 
        capacity: int
    ):
        self.id = str(id).zfill(6)
        self.airport = airport
        self.start = start
        self.end = end
        self.is_historic = is_historic
        self.is_historic_str = 'historic' if is_historic else 'new'
        self.capacity = capacity
        self.name = self._set_slot_name()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"
    
    def _set_slot_name(self) -> str:
        """
        Creates a name for the slot object
        -------
        name : str
            The name of the slot
        """
        return self.airport + '_' + self.is_historic_str + '_' + self.id
