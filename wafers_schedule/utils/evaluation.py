from dataclasses import dataclass


@dataclass
class Evaluation:
    """
    Data class for wafer-machine assignment
    """
    is_wafer_selected: bool
    wafer_name: str
    machine_name: str
