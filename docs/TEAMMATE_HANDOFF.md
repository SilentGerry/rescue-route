# Reserved task: short FIFO-versus-greedy comparison report

The application is complete. The one reserved project deliverable is your written
comparison report. Create `docs/COMPARISON_REPORT.md` and commit it yourself with a
small original input scenario, such as `data/report_scenario.json`.

## How to start

```sh
python3 -m unittest discover -s tests -v
python3 RescueRoute.py
python3 RescueRoute.py --json
```

Read `schedule()` and `compare()` in `rescue_route_app.py` and the README's scheduling
assumptions. The output supplies measurements and explanations; your job is to
interpret them and evaluate the trade-offs.

## Report requirements

Write about one to two pages covering:

1. The precise FIFO and greedy rules, and the experiment's time/capacity assumptions.
2. A side-by-side table of all required metrics from the supplied sample.
3. Which donation IDs changed and which shared resources explain the difference.
4. A fairness analysis: identify an earlier donation displaced by urgency and explain
   its final outcome. Distinguish finite displacement from possible streaming starvation.
5. An original scenario you design to test a limitation or counterexample. Save the
   JSON, run both strategies, and interpret the measured outcomes. For example,
   explore a small urgent donation competing with a larger less urgent donation.
6. Why the rule is useful locally, where it fails, and one possible future improvement.
7. A conclusion limited to these simulated examples, without claiming universal
   superiority, global optimality, or real-world safety readiness.

Run your added scenario with:

```sh
python3 RescueRoute.py --data data/report_scenario.json
```

Use your own words and understanding. Update your contribution statement with what
you actually did. This task is substantive analysis and experiment design; it does
not require implementing or repairing the completed scheduler.
