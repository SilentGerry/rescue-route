"""Explainable surplus-food scheduling using simulated minutes and quantity units."""

import argparse
import json
from pathlib import Path

import RescueRoute as foundation


def _text(record, field):
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{field} must not have leading or trailing whitespace")


def _integer(record, field, minimum=0):
    value = record.get(field)
    if type(value) is not int or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")


def validate_data(data):
    """Reject malformed records; expired donations are valid scheduling inputs."""
    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object")
    specifications = {
        "donations": (["id", "donor_name", "food_type", "area"],
                      {"quantity": 1, "expiry": 0, "ready_time": 0}),
        "recipients": (["id", "name", "area"], {"capacity": 0, "closing_time": 0}),
        "volunteers": (["id", "area"], {"vehicle_capacity": 1, "available_from": 0,
                       "available_until": 0, "max_pickups": 0}),
    }
    for entity, (strings, numbers) in specifications.items():
        records = data.get(entity)
        if not isinstance(records, list):
            raise ValueError(f"{entity} must be a list")
        seen = set()
        for record in records:
            if not isinstance(record, dict):
                raise ValueError(f"Each {entity} record must be an object")
            for field in strings:
                _text(record, field)
            if record["id"] in seen:
                raise ValueError(f"Duplicate {entity} ID: {record['id']}")
            seen.add(record["id"])
            for field, minimum in numbers.items():
                _integer(record, field, minimum)
            if entity == "recipients":
                types = record.get("accepted_food_types")
                if not isinstance(types, list) or not types:
                    raise ValueError("accepted_food_types must be a non-empty list")
                for food in types:
                    _text({"food": food}, "food")
            if entity == "volunteers" and "pickup_times" in record:
                times = record["pickup_times"]
                if not isinstance(times, list) or not times:
                    raise ValueError("pickup_times must be a non-empty list")
                for time in times:
                    _integer({"pickup_time": time}, "pickup_time")
                    if not record["available_from"] <= time <= record["available_until"]:
                        raise ValueError("pickup_times must be within volunteer availability")
            if entity == "volunteers" and record["available_until"] < record["available_from"]:
                raise ValueError("available_until must be >= available_from")
    tuples = foundation_records(data)
    foundation.validate_donations(tuples[0])
    foundation.validate_recipiets(tuples[1])
    foundation.validate_volunteers(tuples[2])
    return data


def foundation_records(data):
    """Adapt named JSON records to the existing teammate-authored tuple validators."""
    areas = {}
    for entity in ("donations", "recipients", "volunteers"):
        for record in data[entity]:
            area = record["area"].casefold()
            if area not in areas:
                areas[area] = len(areas)
    donations = [(d["id"], d["donor_name"], d["food_type"], d["quantity"],
                  d["expiry"], areas[d["area"].casefold()], d["ready_time"])
                 for d in data["donations"]]
    recipients = [(r["id"], r["name"], r["accepted_food_types"], r["capacity"],
                   areas[r["area"].casefold()], r["closing_time"])
                  for r in data["recipients"]]
    volunteers = [(v["id"], v["vehicle_capacity"], areas[v["area"].casefold()],
                   [v["available_from"], v["available_until"]], v["max_pickups"])
                  for v in data["volunteers"]]
    return donations, recipients, volunteers


def schedule_legacy(donations, recipients, volunteers, strategy):
    """Run the original tuple API; availability lists are discrete pickup minutes.

    The original recipient's final time field serves as the delivery deadline.
    One simulated minute per trip lets the original samples run unchanged.
    """
    foundation.validate_donations(donations)
    foundation.validate_recipiets(recipients)
    foundation.validate_volunteers(volunteers)
    for volunteer in volunteers:
        if any(type(t) is not int or t < 0 for t in volunteer[3]):
            raise ValueError("Tuple availability must contain nonnegative integer minutes")
    data = {
        "donations": [dict(id=d[0], donor_name=d[1], food_type=d[2], quantity=d[3],
                           expiry=d[4], area=str(d[5]), ready_time=d[6]) for d in donations],
        "recipients": [dict(id=r[0], name=r[1], accepted_food_types=r[2], capacity=r[3],
                            area=str(r[4]), closing_time=r[5]) for r in recipients],
        "volunteers": [dict(id=v[0], vehicle_capacity=v[1], area=str(v[2]),
                            available_from=min(v[3]), available_until=max(v[3]) + 1,
                            pickup_times=v[3], max_pickups=v[4]) for v in volunteers],
    }
    return schedule(data, strategy, trip_minutes=1)


def load_data(path):
    try:
        with Path(path).open(encoding="utf-8") as source:
            return validate_data(json.load(source))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot load {path}: {error}") from error


def schedule(data, strategy="fifo", now=0, trip_minutes=15, urgent_minutes=60):
    """Whole donations, same-area trips, reusable vehicles, cumulative recipient capacity."""
    validate_data(data)
    for field, value, minimum in [("now", now, 0), ("trip_minutes", trip_minutes, 1),
                                  ("urgent_minutes", urgent_minutes, 0)]:
        _integer({field: value}, field, minimum)
    if strategy not in ("fifo", "greedy"):
        raise ValueError("strategy must be fifo or greedy")
    donations = data["donations"]
    recipients = data["recipients"]
    volunteers = data["volunteers"]
    recipient_tuples = foundation_records(data)[1]
    remaining = {r["id"]: r["capacity"] for r in recipients}
    next_free = {v["id"]: max(now, v["available_from"]) for v in volunteers}
    pickups = {v["id"]: 0 for v in volunteers}
    order = list(range(len(donations)))
    if strategy == "greedy":
        order.sort(key=lambda i: (donations[i]["expiry"], -donations[i]["quantity"], i))
    decisions, deferrals = [], []
    processed = set()
    first_pending = 0
    for rank, index in enumerate(order, 1):
        donation = donations[index]
        identifier = donation["id"]
        quantity = donation["quantity"]
        if strategy == "greedy" and index != first_pending:
            earlier = donations[first_pending]
            deferrals.append({"donation_id": earlier["id"], "status": "deferred",
                "reason": f"{earlier['id']} was deferred while {identifier} was considered: "
                          f"greedy ranks by earlier expiry, then larger quantity, then input order "
                          f"(expiry {donation['expiry']} vs {earlier['expiry']}; "
                          f"quantity {quantity} vs {earlier['quantity']})."})
        processed.add(index)
        while first_pending in processed:
            first_pending += 1
        priority = (f"FIFO input position {index + 1}." if strategy == "fifo" else
                    f"Greedy priority {rank}: expiry {donation['expiry']}, quantity {quantity}, "
                    f"input position {index + 1}.")
        assignment = None
        failures = set()
        if donation["expiry"] <= now:
            failures.add("the donation is already expired at the simulation start")
        else:
            compatible_ids = {r[0] for r in foundation.recipients_by_food_type(
                donation["food_type"], recipient_tuples)}
            for recipient in recipients:
                if recipient["id"] not in compatible_ids:
                    failures.add("recipient does not accept the food type")
                    continue
                if recipient["area"].casefold() != donation["area"].casefold():
                    failures.add("recipient is outside the pickup area")
                    continue
                if remaining[recipient["id"]] < quantity:
                    failures.add("recipient has insufficient remaining capacity")
                    continue
                for volunteer in volunteers:
                    if volunteer["area"].casefold() != donation["area"].casefold():
                        failures.add("volunteer is outside the pickup area")
                        continue
                    if volunteer["vehicle_capacity"] < quantity:
                        failures.add("volunteer vehicle cannot carry the whole donation")
                        continue
                    if pickups[volunteer["id"]] >= volunteer["max_pickups"]:
                        failures.add("volunteer has reached the maximum pickups")
                        continue
                    start = max(now, donation["ready_time"], next_free[volunteer["id"]])
                    if "pickup_times" in volunteer:
                        eligible = [t for t in volunteer["pickup_times"] if t >= start]
                        if not eligible:
                            failures.add("volunteer has no remaining permitted pickup time")
                            continue
                        start = min(eligible)
                    finish = start + trip_minutes
                    if finish >= donation["expiry"]:
                        failures.add("delivery cannot finish strictly before expiry")
                        continue
                    if finish > recipient["closing_time"]:
                        failures.add("delivery would finish after recipient closing")
                        continue
                    if finish > volunteer["available_until"]:
                        failures.add("volunteer availability ends before delivery completes")
                        continue
                    assignment = {"donation_id": identifier, "recipient_id": recipient["id"],
                        "volunteer_id": volunteer["id"], "scheduled_time": start,
                        "delivery_time": finish, "quantity": quantity, "status": "assigned",
                        "reason": f"{priority} Assigned {identifier} from {donation['donor_name']} "
                                  f"to {recipient['name']} with {volunteer['id']}: the organization "
                                  f"accepts {donation['food_type']}, has {remaining[recipient['id']]} "
                                  f"units remaining, and the vehicle holds {volunteer['vehicle_capacity']} "
                                  f"units. All are in {donation['area']}. Pickup at minute {start}, "
                                  f"delivery at {finish}, before expiry {donation['expiry']}, within "
                                  f"closing {recipient['closing_time']} and volunteer availability "
                                  f"ending {volunteer['available_until']}; pickup "
                                  f"{pickups[volunteer['id']] + 1}/{volunteer['max_pickups']}."}
                    remaining[recipient["id"]] -= quantity
                    pickups[volunteer["id"]] += 1
                    next_free[volunteer["id"]] = finish
                    break
                if assignment:
                    break
            if not recipients:
                failures.add("no recipient records were supplied")
            if not volunteers:
                failures.add("no volunteer records were supplied")
        decisions.append(assignment or {"donation_id": identifier, "recipient_id": None,
            "volunteer_id": None, "scheduled_time": None, "delivery_time": None,
            "quantity": quantity, "status": "unassigned",
            "reason": f"{priority} Unassigned {identifier}: no feasible pair. "
                      f"Constraints encountered: {'; '.join(sorted(failures))}."})
    assigned = [decision for decision in decisions if decision["status"] == "assigned"]
    rescued = sum(decision["quantity"] for decision in assigned)
    total = sum(donation["quantity"] for donation in donations)
    urgent_ids = {d["id"] for d in donations if 0 < d["expiry"] - now <= urgent_minutes}
    urgent_rescued = sum(a["donation_id"] in urgent_ids for a in assigned)
    recipient_capacity = sum(r["capacity"] for r in recipients)
    vehicle_budget = sum(v["vehicle_capacity"] * v["max_pickups"] for v in volunteers)
    metrics = {"donations_received": len(donations), "donations_assigned": len(assigned),
        "donations_unassigned": len(donations) - len(assigned), "food_quantity_rescued": rescued,
        "food_quantity_at_risk": total - rescued, "urgent_donations": len(urgent_ids),
        "urgent_donations_rescued": urgent_rescued,
        "urgent_rescue_rate": urgent_rescued / len(urgent_ids) if urgent_ids else None,
        "recipient_capacity_utilization": rescued / recipient_capacity if recipient_capacity else None,
        "volunteer_capacity_utilization": rescued / vehicle_budget if vehicle_budget else None}
    return {"strategy": strategy, "decisions": decisions, "deferrals": deferrals, "metrics": metrics}


def first_in_first_out_assignment(data, **options):
    return schedule(data, "fifo", **options)


def greedy_urgency_first_assignment(data, **options):
    return schedule(data, "greedy", **options)


def compare(data, **options):
    fifo = first_in_first_out_assignment(data, **options)
    greedy = greedy_urgency_first_assignment(data, **options)
    fifo_by_id = {d["donation_id"]: d for d in fifo["decisions"]}
    changes = []
    for decision in greedy["decisions"]:
        baseline = fifo_by_id[decision["donation_id"]]
        fields = ("status", "recipient_id", "volunteer_id", "scheduled_time")
        if any(baseline[field] != decision[field] for field in fields):
            changes.append({"donation_id": decision["donation_id"],
                "fifo": {field: baseline[field] for field in fields},
                "greedy": {field: decision[field] for field in fields}})
    return {"fifo": fifo, "greedy": greedy, "comparison": {
        "quantity_rescued_delta": greedy["metrics"]["food_quantity_rescued"] -
                                  fifo["metrics"]["food_quantity_rescued"],
        "donations_assigned_delta": greedy["metrics"]["donations_assigned"] -
                                    fifo["metrics"]["donations_assigned"],
        "changed_donations": changes,
        "explanation": "Both strategies start with identical unused resources. Greedy changes only "
                       "donation processing order. Earlier-expiring donations can take recipient "
                       "capacity or volunteer slots before donations that arrived earlier. "
                       "Read each decision's constraints to see why a changed donation succeeded "
                       "or failed. Greedy does not guarantee more rescued quantity or fairness."}}


def render_report(result):
    lines = ["RescueRoute — simulated educational prototype"]
    for name in ("fifo", "greedy"):
        run = result[name]
        lines.append(f"\n{name.upper()}")
        lines.extend(event["reason"] for event in run["deferrals"])
        lines.extend(decision["reason"] for decision in run["decisions"])
    lines.append("\nMetric                              FIFO          GREEDY")
    for metric, value in result["fifo"]["metrics"].items():
        other = result["greedy"]["metrics"][metric]
        def display(number):
            if number is None:
                return "N/A"
            return f"{number:.1%}" if isinstance(number, float) else str(number)
        lines.append(f"{metric:35} {display(value):>10} {display(other):>15}")
    comparison = result["comparison"]
    lines.append(f"\nGreedy minus FIFO: {comparison['quantity_rescued_delta']:+d} rescued units; "
                 f"{comparison['donations_assigned_delta']:+d} assigned donations.")
    lines.append(comparison["explanation"])
    for change in comparison["changed_donations"]:
        lines.append(f"Changed {change['donation_id']}: FIFO {change['fifo']}; greedy {change['greedy']}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).parent / "data" / "sample.json")
    parser.add_argument("--now", type=int, default=0, help="Simulation start minute")
    parser.add_argument("--trip-minutes", type=int, default=15)
    parser.add_argument("--urgent-minutes", type=int, default=60)
    parser.add_argument("--json", action="store_true", help="Print machine-readable results")
    args = parser.parse_args(argv)
    try:
        result = compare(load_data(args.data), now=args.now, trip_minutes=args.trip_minutes,
                         urgent_minutes=args.urgent_minutes)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2) if args.json else render_report(result))


if __name__ == "__main__":
    main()
