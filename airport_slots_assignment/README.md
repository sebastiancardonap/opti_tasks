## Presentation of an optimisation project

- We would like you to present an optimisation project in which you have participated
- The session will take 30 min. You can use at most 15 min (10 min can suffice too) for your presentation
- The main point is to have time for questions and discussion

### :muscle: Requirements

- Present the business problem. You can do this through slides, code or just by describing it orally, your choice.
- Share the actual code implementation, this is mandatory. 
    - Share your code with us. We will share with you a github repository in which you can push your code. We would like to get familiar with it before your presentation. Once we receive we will schedule the final round of interviews. 
    - Provide some simple instructions in case we would like to run your code
    - In your presentation we would like to discuss about how the business problem and the optimisation model translate into an actual solution through the code implementation.
    - Ideally the solution is implemented in Python, but it is also ok to present projects implemented in C++, Java or Julia. For other languages please confirm first with us.
- Discuss strengths and flaws of the project from any point of view: business, optimisation, code.



## Challenge Description

### :airplane: Overview

Airport runaway usage is handled through slots. A slot represents a time in which a certain airline is allowed to perform either take-off or landing operations. Slots are agreed between an airline and an airport management company. A flight taking-off or landing outside a slot incurs a violation. This might lead to issues in busy airports.

As a rule, an airline can take for granted the slots they used in the former year. These are the so-called historic slots and they are identified with a time reference. An aircraft can take-off and land within 30 minutes of the historic slot reference time without leading to a violation. Nevertheless, the closest the operation time to the slot reference time the better. 

Besides, airlines can forecast whether new slots will be granted for a certain airport and time. The forecast consists of a given time window, normally an hour, in which they expect to get a new slot and its capacity. However, these slots may not be granted eventually by airport management. Consequently, scheduling flights in new slots is riskier, as they might lead to violations. In addition, each slot has a capacity, namely, the number of same type operations that could take place within that time window.

Departing flights (stn_flights.csv), historic slots (stn_historic_slots_departure.csv) and new slots (stn_new_slots_departure.csv) from Stansted Airport are provided.


### :rocket: Goal

The goal is to understand how the given departing flights can match the historic slots and new slots for departure. Each departing flight needs a departure slot. The number of flights assigned to a given slot cannot be higher than its capacity. If a flight cannot be assigned to any slot, then it is a violation.

We want to make this assignation in the best possible way that <b>minimizes the risk for the company</b>. Remember that our order of preference is:
- historic slots is better than within 5 minutes of historic slot
- within 5 minutes of historic slot is better than within 6 to 30 minutes of historic slot, where 10 minutes is better than 30!
- within 6 to 30 minutes of historic slot is better than new slot

<b>Anything else that can’t be assigned to any of those is a violation</b>.


### :gear: Output

You are asked to construct a slots usage report in which one can see the following quantities on an hourly basis:

1. Number of flights taking-off meeting exact historic slot times.
2. Number of flights taking-off within 5 minutes of historic slot reference times
3. Number of flights taking-off within 6 to 30 minutes of the historic slot reference times
4. Number of flights taking-off within a new slot
5. Number of violations

We expect a csv as a result with one row per each weekday and hour with the following format:

airport | weekday | time | historic | <=5 | <=30 | new | violations
:---: | :---: | :---: | :---: | :---: | :---: | :---: | :---:
STN | Thursday | 05:00 | 1 | 5 | 18 | 0 | 0
STN | Wednesday | 16:00 | ... | ... | ... | ... | ...
... | ... | ... | ... | ... | ... | ... | ...

The sample row means in STN (Stanstead) on Thursday between 05:00 and 05:59 there is one flight that departs in a historic slot, 5 flights that depart within 5 minutes of an historic slot, 18 flights that depart within 6 to 30 minutes of a historic slot, 0 flights that use new slots and 0 violations.
