from domain_models.input_data import InputData
from services.schedulers import LegacyScheduler, BetterScheduler
from services.validators import ScheduleChecker

if __name__ == "__main__":

    input_data = InputData.from_csv(path="data/")

    print("-- Legacy Scheduler ---------------")
    old_schedule = LegacyScheduler(input_data=input_data).schedule()
    ScheduleChecker(input_data=input_data, schedule=old_schedule).check()
    print(f"Makespan                     : {old_schedule.makespan:,.2f} hours")
    print(
        f"Priority-weighted cycle time : {old_schedule.priority_weighted_cycle_time:,.2f} weighted hours"
    )
    old_schedule.to_csv(output_file="output/old_schedule.csv")

    print("\n\n-- Better Scheduler ---------------")
    new_schedule = BetterScheduler(input_data=input_data).schedule()
    ScheduleChecker(input_data=input_data, schedule=new_schedule).check()
    print(f"Makespan                  : {new_schedule.makespan:,.2f} hours")
    print(
        f"Priority-weighted cycle time : {new_schedule.priority_weighted_cycle_time:,.2f} hours"
    )
    new_schedule.to_csv(output_file="output/better_schedule.csv")
