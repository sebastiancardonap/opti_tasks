from domain_models.input_data import InputData
from services.assigner import MIPAssigner


input_data = InputData.from_csv(path="data/input_data/")

assigner = MIPAssigner(input_data=input_data)
assigner.assign(mip_gap=0.2, seconds_time_limit=2*60)




# Note that I need to know whether I am in or not (inside) the range!!! Not just the difference
# Being inside has a cost of zero risk
# Being close (but less than 30 minutes) has a cost of the minimum difference vs start/end

# For new slots... it is just being inside of the range
# And assign value of RISK BIG M if inside

# It all can be one single variable x_ 0, 1-t-5, 6-t-30, new (60)

# FO may be like
# MIN sum_flights [ M*(1-y_f) * sum_slots (c*x_fs) ]      Where Big M does the magic... it is turning x=1

# for all flight f, sum_slots (x_fs) <= 1
# for all flight f, y_f == sum_slots (x_fs)
# for all slot s, sum_flights (x_fs) <= capacity_s




if __name__ == "__main__":

    print("-- MIP Slot Assigner ---------------")
    input_data = InputData.from_csv(path="data/input_data/")
    assigner = MIPAssigner(input_data=input_data).schedule()
    print(f"Makespan: {assigner.makespan:,.2f} hours")
    #assigner.to_csv(output_file="data/output_data/slot_assignment.csv")
