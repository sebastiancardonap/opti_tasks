from domain_models.input_data import InputData
from services.schedulers.legacy_scheduler import LegacyScheduler
from services.schedulers.better_scheduler import BetterScheduler
from services.schedulers.milp_scheduler import MILPScheduler
from services.validators import ScheduleChecker


if __name__ == "__main__":

    print("-- Legacy Scheduler ---------------")
    input_data = InputData.from_csv(path="data/")
    old_schedule = LegacyScheduler(input_data=input_data).schedule()
    ScheduleChecker(input_data=input_data, schedule=old_schedule).check()
    print(f"Makespan: {old_schedule.makespan:,.2f} hours")
    print(
        f"Priority-weighted cycle time: {old_schedule.priority_weighted_cycle_time:,.2f} weighted hours"
    )
    old_schedule.to_csv(output_file="output/old_schedule.csv")

    print("\n\n-- Better Scheduler ---------------")
    better_input_data = InputData.from_csv(path="data/")
    better_schedule = BetterScheduler(input_data=better_input_data).schedule()
    ScheduleChecker(input_data=better_input_data, schedule=better_schedule).check()
    print(f"Makespan: {better_schedule.makespan:,.2f} hours")
    print(
        f"Priority-weighted cycle time: {better_schedule.priority_weighted_cycle_time:,.2f} hours"
    )
    better_schedule.to_csv(output_file="output/better_schedule.csv")

    print("\n\n-- Better Scheduler ---------------")
    milp_input_data = InputData.from_csv(path="data/")
    milp_schedule = MILPScheduler(input_data=milp_input_data).schedule(mip_gap=0.99, seconds_time_limit=3600 * 3, pwct_weight=1)
    ScheduleChecker(input_data=milp_input_data, schedule=milp_schedule).check()
    print(f"Makespan: {milp_schedule.makespan:,.2f} hours")
    print(
        f"Priority-weighted cycle time: {milp_schedule.priority_weighted_cycle_time:,.2f} hours"
    )
    milp_schedule.to_csv(output_file="output/milp_schedule.csv")
