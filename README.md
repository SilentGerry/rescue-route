# rescue-route
Surplus Food Matching &amp; Pickup Planner - Group Project: CPSC 335-03 Group 3

RescueRoute is a runnable Python command-line application that loads simulated
donations, recipients, and volunteers from JSON, compares FIFO with an urgency-first
greedy scheduler, and explains every assignment, failure, and priority deferral.
It is an educational prototype, not food-safety certified or approved for real food
handling, medical, emergency, or operational deployment.

## Run and test

Python 3.10 or newer; no third-party packages or API keys are required.
From the repository folder:

```sh
python3 RescueRoute.py
python3 -m unittest discover -s tests -v
```

Custom input and machine-readable output:

```sh
python3 RescueRoute.py --data data/sample.json --now 0 --trip-minutes 15 --urgent-minutes 60
python3 RescueRoute.py --json
```

All CLI runs calculate both strategies from the same input and fresh resources.
An invalid input or option prints an actionable error and exits with status 2.

## Architecture

- `RescueRoute.py`: the original teammate-authored tuple samples, validators, and
  food-matching helper, with small fixes and completed function outlines.
- `rescue_route_app.py`: added JSON adapters, supplementary validation, shared
  scheduling, metrics, comparison, explanations, and CLI implementation. It uses
  the original validators and food-matching helper.
- `docs/CHANGE_PROVENANCE.md`: original contributions, precise fixes, and additions.
- `data/sample.json`: repeatable simulated examples, including competition,
  expiry, food incompatibility, area mismatch, and vehicle limits.
- `tests/`: 35 automated tests covering scheduling, CLI integration, fairness,
  input errors, boundaries, state isolation, original sample compatibility, and
  actual integration with the preserved validators and food-matching helper.
- `docs/DEMO.md`: live-demo steps and discussion prompts.
- `docs/TEAMMATE_HANDOFF.md`: the one reserved deliverable, the short comparison report.
- `docs/CONTRIBUTIONS.md`: individual contribution statement template.

Lists preserve file order and decision history. Dictionaries keyed by ID track
recipient capacity, volunteer pickup counts, and next available times. Sets detect
duplicate IDs, check food acceptance, track processed donations, and collect failure
reasons. Greedy uses a sorted list because the priority rule is fixed for each run.
The new scheduler keeps state local and never modifies input. The original
`assignments` and `rejections` globals remain for the completed standalone tuple
recording helpers; the new scheduler does not use those globals.

## Data model

The input is a JSON object with three required lists: `donations`, `recipients`,
and `volunteers`. Empty lists are valid; an empty file is invalid JSON.

| Entity | Required fields |
| --- | --- |
| Donation | `id`, `donor_name`, `food_type`, `quantity`, `expiry`, `area`, `ready_time` |
| Recipient | `id`, `name`, `accepted_food_types`, `capacity`, `area`, `closing_time` |
| Volunteer | `id`, `vehicle_capacity`, `area`, `available_from`, `available_until`, `max_pickups` |
| Output decision | `donation_id`, `recipient_id`, `volunteer_id`, `scheduled_time`, `delivery_time`, `quantity`, `status`, `reason` |

Times are integer minutes on the same simulated clock, starting at minute zero;
they are not calendar dates. Quantity is an abstract integer unit used consistently
for food and capacity. Strings must be non-empty and have no surrounding whitespace.
IDs must be unique within each entity list. Food types and areas match without case
sensitivity; any non-empty food type or area is allowed, rather than a fixed vocabulary.
Numbers must be integers (booleans are rejected). Quantities and vehicle capacities
are positive; other numeric fields are nonnegative. Availability must end at or after
it begins. Zero recipient capacity and zero maximum pickups represent unavailable
resources. Expired donations, or donations ready too late for their expiry, are
accepted as data and receive scheduling failure explanations.

## Scheduling assumptions

1. The donation list represents arrival order. Recipients and volunteers are searched
   in their JSON list order; the first feasible pair is selected for both strategies.
2. Each donation must fit as a whole. Donations are neither split nor combined.
3. Donor, recipient, and volunteer must share an area. There is no cross-area routing.
4. One pickup/delivery occupies a volunteer for `trip_minutes` (default 15).
   Pickup begins at the latest of simulation start, donation ready time, volunteer
   availability start, and completion of that volunteer's previous assigned trip.
5. Delivery must complete **strictly before expiry**, at or before recipient closing,
   and at or before volunteer availability ends. Vehicles never overlap trips.
6. Optional volunteer `pickup_times` is a non-empty list of nonnegative integer
   pickup minutes within the availability window. When supplied, only those pickup
   times are permitted.
7. Recipient capacity is a cumulative budget for the run. Vehicle capacity is a
   per-trip limit and can be reused after delivery, subject to maximum pickups.
8. This is a static reservation scheduler: a future pickup may reserve a volunteer
   and leave unused time before it. The scheduler does not backfill those gaps,
   reconsider rejected donations, or optimize route duration.

## FIFO baseline and greedy rule

FIFO processes donations in input/arrival order and assigns the first feasible
recipient–volunteer pair. A failed donation does not consume resources.

Greedy sorts ascending by the tuple:

```text
(absolute expiry minute, negative quantity, original input index)
```

Thus earlier expiration wins, then larger quantity, then earlier arrival. With a
fixed simulation start, ordering by absolute expiry is identical to ordering by
remaining shelf life. Expired inputs are considered and rejected normally. Greedy
uses exactly the same matching checks and pair-selection order as FIFO.

This rule locally prioritizes the most time-sensitive donation and, on equal
expiry, a larger potential rescue. It is reasonable when expiry threatens loss,
but is not globally optimal. A small urgent donation can consume capacity needed
for a large later-expiring donation and reduce total rescued food. A future-ready
urgent donation can reserve a vehicle and prevent a useful earlier trip. Selecting
the first compatible recipient can also consume a flexible recipient that a later
donation needed. The test suite includes a greedy result with nine fewer rescued
units than FIFO.

FIFO rewards arrival order but may sacrifice urgent donations. Greedy can defer
earlier arrivals and leave them unassigned after capacity is consumed. Each priority
inversion against the earliest pending arrival creates a named deferral explanation;
every donation still receives one final assigned/unassigned decision. Repeated urgent
arrivals could create starvation in a future streaming system; this finite prototype
demonstrates displacement, not an actual infinite stream. Aging priorities or reserved
capacity could address fairness, but are not part of these two strategies.

## Metrics and explanations

Each assignment names the donor, recipient, and volunteer and includes times,
accepted food, capacity, area, and pickup limits. Failures list the constraints
encountered during the pair search. These are aggregated reasons from different
candidates, not a claim that every candidate failed every listed constraint.

| Metric | Definition |
| --- | --- |
| Donations received | Number of donation records |
| Donations assigned / unassigned | Final outcome counts; deferrals are not double-counted |
| Food quantity rescued | Sum of quantities assigned |
| Food quantity at risk | Total quantity minus rescued quantity, including already-expired inputs |
| Urgent rescue rate | Assigned urgent donations / urgent donations; urgent means `0 < expiry - now <= urgent_minutes` |
| Recipient capacity utilization | Rescued units / total initial recipient capacity |
| Volunteer capacity utilization | Rescued units / sum of `vehicle_capacity * max_pickups` |

Utilization is aggregated across all resources, including incompatible ones.
Volunteer utilization measures the nominal carrying budget across allowed trips,
not busy-time utilization; availability may prevent reaching that budget. Ratios
with a zero denominator are `N/A` in text and `null` in JSON. Comparisons report
greedy-minus-FIFO deltas and identify donations whose outcome, pair, or pickup time
changed. The sample is designed to show a difference, not to establish general superiority.

## Complexity

Let D be donations, R recipients, V volunteers, and F the maximum accepted-food-type
list length. Let A be the maximum optional pickup-time list length (zero for
window-only inputs). Validation and tuple conversion are O(D + RF + V(A + 1)).
The original food helper scans RF entries per donation. Matching checks up to R
recipients and V volunteers and may search A pickup times per volunteer:
O(DR(F + V(A + 1))) worst case. FIFO ordering is O(D); greedy adds O(D log D).
Computing metrics and comparisons is O(D + R + V). Auxiliary storage is
O(D + RF + V + A), excluding input and the length of explanation strings. Running
both strategies doubles matching work without changing the asymptotic bound.

## Limitations

Simulated travel time and area equality do not model real geography, traffic,
refrigeration, nutrition, allergens, storage, opening times, multiple volunteer
availability windows, or real food safety. Inputs must use a consistent time origin
and quantity unit. Neither strategy guarantees fairness or optimal total rescue.
The application works offline with JSON; it has no dashboard or external service.

## Using the original tuple interface

The original `SAMPLE_DONATIONS`, `SAMPLE_RECIPIENTS`, and `SAMPLE_VOLUNTEERS`
remain unchanged. Both original scheduler functions accept the three tuple lists:

```python
from RescueRoute import (SAMPLE_DONATIONS, SAMPLE_RECIPIENTS, SAMPLE_VOLUNTEERS,
                         first_in_first_out_assignment)
result = first_in_first_out_assignment(
    SAMPLE_DONATIONS, SAMPLE_RECIPIENTS, SAMPLE_VOLUNTEERS)
```

For that interface, availability lists mean permitted pickup minutes, the recipient's
last time field is a delivery deadline, and each trip takes one simulated minute.
The JSON CLI uses explicit windows and a configurable trip duration. This distinction
keeps the original samples useful while making the added scheduling assumptions clear.

## Team roles and contributions

# Nathan Hoang - Algorithm & Optimaztion Lead:
Adding JSON input loading and additional validation checks.
Implementing FIFO and urgency-first greedy scheduling.
Adding checks for recipient capacity, volunteer availability, vehicle capacity, pickup limits, locations, and deadlines.
Adding explanations for assignments, rejections, and deferrals.
Implementing rescue metrics and FIFO-versus-greedy comparisons.
Adding sample input data and 35 automated tests.
Expanding the README with setup instructions, algorithm explanations, complexity analysis, and limitations.

# Gerardo D. Saucedo - Data & Matching Lead:
Implemented data validation functions for Donation, Volunteer, and Recipient data sets.
Implemented matching helper function for Recipient data sets by accepted food types.
Established function outlines.
Established initial data schema.
Created and Managed GitHub repository for the project.

# Dapinder Sidhu - Product & Quality Lead:
Created FIFO vs Greedy comparison report. Including Fairness Analysis and Output Explanation.
Reviewed completed project to ensure assignment requirements were met.


## References

- Course assignment: “RescueRoute Group Project,” CPSC 335-03, due October 15, 2026.
- Python standard library: [JSON](https://docs.python.org/3/library/json.html),
  [argparse](https://docs.python.org/3/library/argparse.html), and
  [unittest](https://docs.python.org/3/library/unittest.html).
- [Python sorting guide](https://docs.python.org/3/howto/sorting.html): key functions
  and deterministic multi-field sorting.

Repository: https://github.com/SilentGerry/rescue-route
