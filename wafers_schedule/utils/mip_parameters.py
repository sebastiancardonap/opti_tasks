from dataclasses import dataclass


@dataclass
class MipParameters:
    """
    Data class for the parameters of the MIP model
    """
    priority_number: dict[str, float]
    compatible_assignments: dict[tuple[str, str], int]
    processing_times: dict[tuple[str, str], float]
    big_m: float
    pwct_weight: float
    makespan_weight: float
