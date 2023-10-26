## Hello there :wave:

If you are reading this, then you have probably applied for an optimisation role at Flexciton.

Welcome! :rainbow: This challenge should take you approximately 4 hours to complete.

We are very happy to answer any questions you have - email us [here](mailto:opt_task@flexciton.com)


## Challenge Description

### :factory: Overview

The XYZ semiconductor fabrication factory (fab) produces 10 types of chipsets for satellites :artificial_satellite:

A chipset is made by taking a wafer and using a machine to apply a specific recipe to it.
- The fab has a total of 10 machines.
- There are currently 100 wafers waiting to be processed.
- Each wafer has a priority class: red, orange and yellow correspond to high, medium and low priority respectively.
- Each wafer has a single recipe it can be processed with; there are 10 recipes in total.
- Each machine can perform a predefined set of recipes.
- The time it takes to apply a recipe to a wafer (i.e. processing time) depends on both the machine and the recipe being used.

### :gift: The Data
The data is from a snapshot of the fab on the 14th November 2022 09:00.
- `wafers.csv` : each row represents a wafer to be scheduled.
- `machines_recipes.csv` : each row represents a recipe that is available on a machine. NOTE: processing time values are in minutes.

### :golf: KPIs

The fab is interested in measuring two Key Performance Indicators (KPIs):

- *Total priority-weighted cycle time* (PWCT) : the sum of all wafers' cycle times, weighted according to each wafer's priority
  (use weights of 1.0, 0.5 and 0.1 for red, orange and yellow respectively). *NOTE:* a wafer's cycle time is the time from when
  it is available for scheduling (immediately) to the end of its processing.
- *Makespan* : the time span that elapses between the first wafer starts processing and the last wafer finishes processing.

### :gear: The Legacy Scheduler

The current operating policy of the fab is as follows:
1. If all machines are busy, wait until the next machine frees up.
2. Find the highest priority wafer _w_ that can be scheduled immediately (i.e. there is at least one compatible machine that can process it).
   NOTE: If there are multiple wafers of the same priority level, choose the one whose name comes earlier alphabetically.
3. Out of the compatible machine(s) immediately available, find the machine _m_ whose name comes earlier alphabetically.
4. Schedule wafer _w_ on machine _m_ for processing.
5. Repeat steps 1-4 until all wafers have been processed.

### :magic_wand: The Better Scheduler

This is your time to shine!
Do you think that the scheduling rules currently in place are helping the business to achieve the best possible KPIs?
Can you come up with a better way of running this fab?

We do not prescribe the approach to be followed, but some possible options are:
- Introducing your own improved operation rules
- Some other type of heuristic model
- A mathematical programming model (e.g. MILP)
- Constraint Programming
- Reinforcement Learning


## :bulb: The Tasks
Extend the present code base as follows:
1. Implement the csv reading methods `get_machines()` and `get_wafers()`.
2. Implement the legacy scheduling algorithm `LegacyScheduler.schedule()` as described in the section above.
3. Implement the three schedule validation classes in `validators.py` (see docstrings for more details).
4. Implement the two schedule KPIs i.e. properties `Schedule.weighted_cycle_time` and `Schedule.makespan`.
5. Implement the `Schedule.to_csv()` method which writes a schedule to a csv file according to the schema in `output/sample.csv`.
6. Implement your very own method for scheduling the fab in `BetterScheduler.schedule()` to minimize total PWCT.


## :rocket: Submission & Evaluation

- Clone this repo to your local machine.
- Create a new branch e.g. `git checkout -b my_branch`
- `main.py` is the main script; you should not need to change anything in that file.
- Tackle as many of the above tasks as you can. The methods to be implemented currently raise a `NotImplementedError`; replace that with your code.
- When you are happy with your code changes, submit them as a pull request for review. The pull request should include:
  - All code changes required to run your code.
  - If you have used any packages, please add them to the `requirements.txt` file.
  - Two schedule csv files in the `output` folder (if you got this far): `old_schedule.csv` and `better_schedule.csv` (these are generated automatically via `main.py`)
  - If you are using a proprietary solver (e.g. CPLEX/gurobi), please also include a text copy of the solver's log output in the `output` folder.

### Few notes
- The project is to be run with Python `3.10` or later.
- The code provided here is a recommendation: you are free to change things as you see fit.
- You are not limited to a single "better" scheduler implementation - if you experimented with other ideas you would like to
  showcase, please include them (just create a new `Scheduler` subclass and extend `main.py` to call it).
- Although we are interested in efficient code, we are not looking for the most efficient implementation;
  we prefer if you focus on clean and readable code instead.




