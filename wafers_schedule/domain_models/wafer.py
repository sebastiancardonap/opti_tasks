from typing import Type, TypeVar

from domain_models.recipe import RecipeId


PriorityType = TypeVar("PriorityType", bound=str)


class Priority:
    RED: PriorityType = "red"
    ORANGE: PriorityType = "orange"
    YELLOW: PriorityType = "yellow"


PRIORITY_WEIGHTS: dict[PriorityType, float] = {
    Priority.RED: 1.0,
    Priority.ORANGE: 0.5,
    Priority.YELLOW: 0.1,
}


class Wafer:
    def __init__(self, name: str, priority: PriorityType, recipe: RecipeId):
        self.name = name
        self.priority = priority
        self.recipe = recipe
        self.priority_number = self._initialize_priority_number()
        self.compatible_machines = []

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"
    
    def _initialize_priority_number(self) -> float:
        return PRIORITY_WEIGHTS[self.priority]
