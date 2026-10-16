# RescueRoute: FIFO vs Greedy# RescueRoute: FIFO vs Greedy Comparison Report

## 1. Scheduling Rules and Assumptions

Both strategies do the same checks. The only difference is the order they go through the donations.

- Greedy goes by urgency. The run output says it on every skipped donation: "greedy ranks by earlier expiry, then larger quantity, then input order." So the food that spoils first goes first, and ties go to the bigger load.
- FIFO (first in, first out) goes in the order the donations were listed, position 1 through 8.

Ground rules for the runs:

- Each donation is delivered whole, and the donor, recipient and driver must be in the same area.
- Each trip takes 15 minutes. Delivery has to finish before the food expires, and before the recipient closes and the driver runs out of time.
- Each recipient has a fixed amount of space for the whole run. Once it's used, it's gone.
- "Urgent" means the food expires within 60 minutes.
- A donation that can't be placed is skipped and never retried.

## 2. Metrics Comparison

Greedy rescues 15 units against FIFO's 13, and its urgent rescue rate is 100% against 0%.

| Metric | FIFO | Greedy |
| --- | --- | --- |
| donations_received | 8 | 8 |
| donations_assigned | 2 | 3 |
| donations_unassigned | 6 | 5 |
| food_quantity_rescued | 13 | 15 |
| food_quantity_at_risk | 26 | 24 |
| urgent_donations | 2 | 2 |
| urgent_donations_rescued | 0 | 2 |
| urgent_rescue_rate | 0.0% | 100.0% |
| recipient_capacity_utilization | 52.0% | 60.0% |
| volunteer_capacity_utilization | 31.0% | 35.7% |

In plain terms: greedy saved 2 more units and placed 1 more donation. "Urgent" means the food expires within 60 minutes.

## 3. Changed Donations

Three donations got different results, and all three were fighting over one thing: Community Shelter (R-101), which can take 10 units in total. The run output reports them as:

- D-102: FIFO didn't place it, greedy did (R-101, V-101, pickup at minute 0).
- D-103: FIFO didn't place it, greedy did (R-101, V-101, pickup at minute 15).
- D-101: FIFO placed it (R-101, V-101, pickup at minute 0), greedy didn't.

FIFO reaches D-101 first, and its 8 units use up most of the Shelter's space. That leaves 2 units, so D-102 (6 units) and D-103 (4 units) don't fit. Greedy reaches D-102 and D-103 first because they expire sooner. Together they use all 10 units, so D-101 no longer fits. Greedy saved 10 units at the Shelter and FIFO saved 8, which is the +2 difference. D-104 was handled the same way by both.

## 4. Fairness Analysis

D-101 is the whole fairness story. It was first in line, got skipped 7 times, and ended up unplaced, so its 8 units were lost.

- Skipped 7 times. Greedy put D-106, D-102, D-103, D-105, D-107, D-108 and D-104 ahead of it, because every one of them expires sooner.
- What really cost it. Only D-102 (6 units) and D-103 (4 units), the two urgent donations, used the Shelter's space. When greedy finally got to D-101, nothing was left, and it failed with "recipient has insufficient remaining capacity."
- The cost. FIFO delivered D-101 by minute 15 with lots of shelf life left (it expires at 180). Under greedy, that food is wasted.

This is finite displacement, not starvation. The list ends, so D-101 eventually gets its turn and a final answer. Starvation would need a live stream where urgent donations keep arriving and keep cutting in front of D-101 forever. This project doesn't test that.

## 5. Original Scenario

In this test greedy saves 6 units and FIFO saves 14, and greedy gets nothing in return, because both strategies save the urgent donation. It shows a weakness the sample doesn't: both strategies give a donation the first recipient on the list that works, so a flexible recipient can get used up by the wrong donation.

```json
{

  "donations": [
    {"id": "D-201", "donor_name": "Riverside Farm", "food_type": "produce", "quantity": 8, "expiry": 150, "area": "Central", "ready_time": 0},
    {"id": "D-202", "donor_name": "Corner Deli", "food_type": "prepared meals", "quantity": 6, "expiry": 40, "area": "Central", "ready_time": 0}
  ],
  "recipients": [
    {"id": "R-201", "name": "Flex Pantry", "accepted_food_types": ["prepared meals", "produce"], "capacity": 10, "area": "Central", "closing_time": 120},
    {"id": "R-202", "name": "Meals Kitchen", "accepted_food_types": ["prepared meals"], "capacity": 10, "area": "Central", "closing_time": 120}
  ],
  "volunteers": [
    {"id": "V-201", "vehicle_capacity": 10, "area": "Central", "available_from": 0, "available_until": 120, "max_pickups": 3}
  ]
}
```

| Metric | FIFO | Greedy |
| --- | --- | --- |
| donations_assigned | 2 | 1 |
| food_quantity_rescued | 14 | 6 |
| food_quantity_at_risk | 0 | 8 |
| urgent_rescue_rate | 100.0% | 100.0% |
| recipient_capacity_utilization | 70.0% | 30.0% |
| volunteer_capacity_utilization | 46.7% | 20.0% |

What happened.

- FIFO: D-201 goes to Flex Pantry (8 of 10 units). D-202 no longer fits there, so it goes to Meals Kitchen: picked up at minute 15, delivered at minute 30, before it expires at 40.
- Greedy: D-202 goes first and takes Flex Pantry, the first recipient that works (6 of 10 units). Then D-201 needs 8 units, Flex Pantry has 4, and nobody else takes produce. D-201 is lost, and so are its 8 units.

Greedy's only upside is that D-202 arrives at minute 15 instead of 30. The real problem is the "first recipient that works" rule, which both strategies share, but greedy's ordering is what sets it off. Going by urgency alone doesn't protect scarce space. The output says it plainly: "Greedy minus FIFO: −8 rescued units; −1 assigned donations."

## 6. Trade-offs and Future Improvement

Greedy's win is the urgent rescue rate. On the sample it went from 0% to 100%, because D-102 and D-103 got delivered before they spoiled. "Whatever spoils first goes first" is a sensible local rule when spoilage is the main way food gets lost.

Its failure is D-101's 8 wasted units. The rule only looks at urgency, so it can't tell that a donation that arrived early still has lots of shelf life and needs the same limited space. The README notes a test case where greedy saves 9 fewer units than FIFO, and the Section 5 test shows the same problem with 8 fewer. Greedy isn't the best possible, and it can push early donations back until the space is gone.

One fix is reserved capacity for early arrivals. Each recipient keeps some space (or the first slot for the oldest waiting donation) that urgent donations can't use. The other option is aging, where a donation moves up the line the longer it waits. Either would protect donations like D-101. Neither is part of the two strategies as built.

## 7. Conclusion

In these two runs, which strategy comes out ahead depends on the situation. On the sample, greedy saved 15 units to FIFO's 13 and rescued both urgent donations, but it left D-101, the first donation in line, unplaced. In the Section 5 test, greedy saved 6 units to FIFO's 14 and gained nothing, because handling the urgent donation first used up the only recipient that takes produce. So going by urgency can help rescue urgent food and can also lower the total, depending on how donations compete for the same space. These runs don't show that either strategy is better in general, and this simulation says nothing about whether it's safe for real food handling.

