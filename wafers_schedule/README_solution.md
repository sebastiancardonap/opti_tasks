## Hello there :wave:

In this README file you will find some info about the solution for the optimisation engineer role at Flexciton presented by Sebastián Cardona.

The structure fot the file follows:
- KPIs of Legacy Scheduler
- KPIs of Better Scheduler, a variation of Legacy Scheduler
- KPIs of MILP Scheduler, a MILP formulation
- Explanation of the difference between Legacy and Better Schedulers
- Some info about the resources used to get the solution of the MILP Scheduler
- Final comments and next steps for the challenge

I do not talk about the business problem, as it is well described in the original README file of the challenge. Also, you may want to <b> create a virtual environment </b> and run <i> pip install -r requirements.txt </i> to run this project.

Finally, note that all of the schedulers, Legacy, Better, and MILP, pass the 3 validators checks.
I have created Better and MILP schedulers for different reasons:

- MILP: Try an exact solution approach. Note that the core of my solution relies on this scheduler
- Better: Prove that following the rules-based approach can provide high quality solutions with small computational and time consumption


## :golf: KPIs

### :gear: KPIs of Legacy Scheduler

- Makespan: 20.5 hours
- Total priority-weighted cycle time (PWCT): 187.3 weighted hours

### :magic_wand: KPIs of Better Scheduler

- Makespan: 20.5 hours
- Total priority-weighted cycle time (PWCT): 178.35 weighted hours

### :artificial_satellite: KPIs of MILP Scheduler

- Makespan: 32.5 hours
- Total priority-weighted cycle time (PWCT): 300.1 weighted hours


## :magic_wand: Difference between Legacy and Better Schedulers

Basically, the Legacy and Better Schedulers are quiet the same, except by a new rule introduced to change the assignment of a wafer to one of its' compatible idling machines.

It means that any time a wafer is going to be assigned to an idle machine, it follows a new additional prioritization rule to choose a machine: the wafer is assigned to the idling compatible machine with the lowest processing time for its' recipe.

Note that Better Scheduler still follows the original initial prioritization rules to pick a wafer to be processed (highest priority and name comes earlier alphabetically), but now it has a new rule to select a machine for this picked wafer. 

This rule aims to set free the busy machines as soon as possible. However, it is still a hard rule that can not guarantee an optimal machine selection.

You can find the scheduler's solution in better_schedule.csv.


## :bulb: Info about MILP formulation of the MILP Scheduler

The MILP Scheduler is a MILP formulation:
- That <b> lets the user specify the importance of the two presented KPIS</b>, makespan and Total priority-weighted cycle time (PWCT) through the pwct_weight input parameter. This parameter has a default value of 100% PWCT importance 
- Where you will not find Recipe set, as this is a <b> dynamic formulation based on a preprocessing step </b>
- The preprocessing step creates a parameter for each compatible wafer-machine assignment. Because of this, I do not need the Recipes set
- Then, the MILPScheduler will use this parameter to create variables and constraints in its' model
- All <b> the magic occurs thanks to two types of constraints</b> :magic_wand: :
  - _define_feasible_sequence_constraint: This constraints guarantee that wafers w and w' can be considered to be processed one after the other if and only if, both wafers are processed by the same machine m
  - _define_sequence_times_preserving_constraint: This constraints guarantee that we correctly estimate and preserve the cycle times of wafers w and w' when are processed one after the other by the same machine m


The solution presented to you in milp_schedule.csv is the output of running the MILP:
- With a <b> time limit of 3 hours, getting a GAP of 93.1% </b>
- Getting the very first feasible solution in around 30 seconds
- In Linux 5.15.0-87-generic x86_64
- In Ubuntu 20.04.6 LTS
- In a machine Intel(R) Core(TM) i7-10610U CPU @ 1.80GHz 16GB Ram 64 bits system
- Installing Pyomo 6.6.2 and glpk 0.4.7, GLPSOL--GLPK LP/MIP Solver 5.0
- With a Python 3.10 virtual environment


## :rocket: Final comments and next steps

- In this project you will find:
  - An implementation to run different Schedulers to solve the XYZ semiconductor fabrication factory (fab) chipsets for satellites problem
  - Three proved Schedulers: Legacy, based on hard rules, Better, based on the Legacy Scheduler and the usage of a new rule to assign idle compatible machines to wafers, and the MILP Scheduler, following a MILP formulation
- Output data for all of the three Schedulers
- The solver takes a lot of time to get a poor quality solution (93.1% GAP) in the MILP Scheduler. It may be a good idea to use other more powerful paid solvers different than the GLPK open source solver, like Gurobi 
- However, even using paid solvers, this scheduling problem may be too complex to use a MILP formulation approach. It is necessary to explore new solutions that follow a different approach to get <b>better quality solutions using less time</b>, for example approaches like:
  - (i) design new rules to improve the Legacy Scheduler logic <b>just like the Better Scheduler does</b>. Those rules may aim to make smart decisions for both "how to prioritize wafers?" and "how to assign wafers to machines?". Note that Better scheduler focuses on the second question, but it is limited to see the information of the idle machines, <b>while it may be useful to take into account busy machines who are about to finish a service and have better (shorter) processing times</b>.
  - (ii) use scheduling-specialized heuristics
- I hope to see you soon, Sebastián.
