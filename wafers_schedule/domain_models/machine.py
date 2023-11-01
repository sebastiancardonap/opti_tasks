from datetime import timedelta

from domain_models.recipe import RecipeId


class Machine:
    """
    Class of machines who serve Wafers
    """
    def __init__(
        self,
        name: str,
        processing_time_by_recipe: dict[RecipeId, timedelta],
    ):
        self.name = name
        self.processing_time_by_recipe = processing_time_by_recipe
        self.is_busy = False
        self.free_time = 0

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name})"
