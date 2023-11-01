from domain_models.wafer import Wafer
from services.schedulers.legacy_scheduler import LegacyScheduler
from utils.evaluation import Evaluation


class BetterScheduler(LegacyScheduler):
    def _evaluate_wafer_machine_assignment(self, current_wafer: Wafer) -> Evaluation:
        """
        Checks if the input Wafer object can be assigned to a compatible free machine
        Note that this method is the only one different to the Legacy Scheduler, due to a 
        change in the prioritization rule, it is an additional step of sorting the available 
        machines list based on processing time
        -------
        evaluation : Evaluation
            Evaluation object with the information of the assignment operation for 
            the Wafer object input parameter
        """
        available_machines = [machine for machine in self.machines_list if (machine.name in current_wafer.compatible_machines) and (not machine.is_busy)]
        machines_sorted_by_processing_time = sorted(available_machines, key=lambda x: x.processing_time_by_recipe[current_wafer.recipe])
        evaluation = Evaluation(True, current_wafer.name, machines_sorted_by_processing_time[0].name) if bool(available_machines) else Evaluation(False, None, None)
        return evaluation
