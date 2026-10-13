# Original foundation and added work

This document describes file history, not a completed individual contribution
statement. Each person must identify their actual work.

## Existing teammate work

The repository's original implementation is recorded under gerry / SilentGerry:

- `1ad807b`: sample data, tuple schemas, validation functions, matching helper, and
  function outlines.
- `6d555b1`: list-field validation changes.

`RescueRoute.py` retains the original sample tuples, globals, validator names and
bodies, and food-type helper. The spelling `validate_recipiets` is retained for
compatibility. The completed JSON application converts records to those tuple
schemas and calls all three validators. Its scheduler also uses the original
`recipients_by_food_type` helper. The original work remains part of the running app.

## Small fixes to existing code

These are integration fixes to teammate-authored code, not newly authored validators:

- Add the missing quantity field to the donation-schema comment.
- Validate ready time as a nonnegative integer, consistent with the existing samples.
- Correct the accepted-food-type empty-string condition, which previously rejected
  non-empty strings.
- In volunteer validation, replace the undefined `recipient` with `volunteer` in
  the length check and unpacking.
- Correct `casfold()` to `casefold()` in food matching.
- Allow zero recipient capacity, zero maximum pickups, and a zero recipient deadline
  so unavailable resources can be represented and explained by the scheduler.

## Added implementations

- Complete previously unfinished location, availability, assignment, rejection,
  FIFO, and greedy function outlines in `RescueRoute.py`.
- Add `rescue_route_app.py` for JSON loading, supplementary validation, tuple adapters,
  scheduling, metrics, comparisons, output, and CLI support.
- Add sample JSON, tests, demo guidance, README sections, and contribution templates.

The original tuple APIs are supported. Their availability lists denote discrete
permitted pickup minutes. The final recipient time field (originally named
`next_delivery_day`) is interpreted as the delivery deadline. These formerly
unfinished scheduling semantics are now explicit. Tuple entry points use a
one-minute simulated trip, preserving the original sample records unchanged.
JSON records use explicit closing times and availability windows, with 15-minute
trips by default; optional `pickup_times` can restrict their pickup times too.

The earlier broad rewrite was replaced by this integration. README's original
opening is retained, with new sections appended. No commits have been reattributed.

## Remaining teammate task

The short comparison report and its original experimental scenario remain reserved
for the third teammate. See `TEAMMATE_HANDOFF.md`. Contribution statements should
credit the original foundation separately from the later additions and fixes.
