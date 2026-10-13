# Live demo guide

Allow approximately five minutes. The team must still choose a live demo or submit
a video link; this guide is not a confirmation of either option.

1. Introduce the problem: surplus donations compete for compatible recipient capacity
   and volunteer pickup slots. State that all data and timing are simulated.
2. Show `data/sample.json`. Point out the shared Central recipient capacity and the
   three prepared-meal donations with different quantities and expiry times.
3. Run `python3 RescueRoute.py`. Explain one successful assignment and one failed
   donation using the printed reasons, not just the IDs.
4. Compare FIFO and greedy. Trace a priority deferral, recipient capacity consumption,
   and an urgent donation's changed outcome. Explain why the same resources produce
   different results when donation ordering changes.
5. Show the metrics table. Define urgent rescue rate and both utilization denominators.
   Point out that an inapplicable ratio is N/A, not zero.
6. Run `python3 -m unittest discover -s tests -v`. Highlight tests for capacity
   competition, expiry boundaries, availability, fairness, and the case where greedy
   rescues less quantity.
7. Once your teammate completes the reserved report, demonstrate their original
   scenario and have them explain its results.

Be prepared to explain: why expiry is strict but closing is inclusive, why vehicle
capacity is reusable, why recipient capacity is cumulative, why greedy is not
globally optimal, and how future-ready pickups may leave scheduling gaps.
