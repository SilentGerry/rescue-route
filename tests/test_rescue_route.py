import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from rescue_route_app import compare, load_data, schedule, validate_data


def example():
    return {
        "donations": [{"id": "D1", "donor_name": "Cafe", "food_type": "meals",
                       "quantity": 6, "expiry": 100, "area": "Central", "ready_time": 0}],
        "recipients": [{"id": "R1", "name": "Shelter", "accepted_food_types": ["meals"],
                        "capacity": 10, "area": "Central", "closing_time": 100}],
        "volunteers": [{"id": "V1", "vehicle_capacity": 10, "area": "Central",
                        "available_from": 0, "available_until": 100, "max_pickups": 2}],
    }


class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.data = example()

    def decision(self):
        return schedule(self.data)["decisions"][0]

    def test_normal_match_and_explanation(self):
        decision = self.decision()
        self.assertEqual((decision["status"], decision["recipient_id"], decision["volunteer_id"]),
                         ("assigned", "R1", "V1"))
        self.assertEqual((decision["scheduled_time"], decision["delivery_time"]), (0, 15))
        self.assertIn("Shelter", decision["reason"])
        self.assertIn("accepts meals", decision["reason"])

    def test_duplicate_ids_for_each_entity(self):
        for entity in self.data:
            with self.subTest(entity=entity):
                data = copy.deepcopy(self.data)
                data[entity].append(copy.deepcopy(data[entity][0]))
                with self.assertRaisesRegex(ValueError, "Duplicate"):
                    validate_data(data)

    def test_expired_and_nearly_expired(self):
        for expiry in (0, 1, 15):
            with self.subTest(expiry=expiry):
                self.data["donations"][0]["expiry"] = expiry
                self.assertEqual(self.decision()["status"], "unassigned")
        self.data["donations"][0]["expiry"] = 16
        self.assertEqual(self.decision()["status"], "assigned")

    def test_food_type_incompatible(self):
        self.data["recipients"][0]["accepted_food_types"] = ["produce"]
        self.assertIn("does not accept", self.decision()["reason"])
        self.assertEqual(self.decision()["status"], "unassigned")

    def test_recipient_capacity(self):
        self.data["recipients"][0]["capacity"] = 5
        self.assertIn("insufficient remaining capacity", self.decision()["reason"])
        self.assertEqual(self.decision()["status"], "unassigned")

    def test_vehicle_capacity(self):
        self.data["volunteers"][0]["vehicle_capacity"] = 5
        self.assertIn("vehicle cannot carry", self.decision()["reason"])
        self.assertEqual(self.decision()["status"], "unassigned")

    def test_volunteer_window(self):
        self.data["volunteers"][0]["available_from"] = 95
        self.assertEqual(self.decision()["status"], "unassigned")
        self.data["volunteers"][0].update(available_from=0, available_until=14)
        self.assertIn("availability ends", self.decision()["reason"])

    def test_competing_donations_consume_capacity(self):
        self.data["donations"].append(dict(self.data["donations"][0], id="D2"))
        result = schedule(self.data)
        self.assertEqual([d["status"] for d in result["decisions"]], ["assigned", "unassigned"])
        self.assertEqual(result["metrics"]["food_quantity_rescued"], 6)

    def test_fifo_and_greedy_differ_and_fairness_is_explained(self):
        self.data["donations"].append(dict(self.data["donations"][0], id="D2", expiry=30))
        result = compare(self.data)
        self.assertEqual(result["fifo"]["decisions"][0]["donation_id"], "D1")
        self.assertEqual(result["greedy"]["decisions"][0]["donation_id"], "D2")
        self.assertEqual(result["greedy"]["decisions"][1]["status"], "unassigned")
        self.assertEqual(result["greedy"]["deferrals"][0]["donation_id"], "D1")
        self.assertIn("D2", result["greedy"]["deferrals"][0]["reason"])
        self.assertIn("earlier expiry", result["greedy"]["deferrals"][0]["reason"])
        self.assertEqual(len(result["comparison"]["changed_donations"]), 2)

    def test_empty_lists(self):
        result = compare({entity: [] for entity in self.data})
        for strategy in ("fifo", "greedy"):
            self.assertEqual(result[strategy]["metrics"]["donations_received"], 0)
            self.assertEqual(result[strategy]["metrics"]["food_quantity_rescued"], 0)
            self.assertIsNone(result[strategy]["metrics"]["urgent_rescue_rate"])
            self.assertIsNone(result[strategy]["metrics"]["recipient_capacity_utilization"])

    def test_empty_and_malformed_files_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for contents in ("", "{", "{}", "[]"):
                path.write_text(contents, encoding="utf-8")
                with self.subTest(contents=contents), self.assertRaises(ValueError):
                    load_data(path)

    def test_valid_file_loads(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(self.data), encoding="utf-8")
            self.assertEqual(load_data(path), self.data)

    def test_recipient_closing_boundary(self):
        self.data["recipients"][0]["closing_time"] = 14
        self.assertIn("after recipient closing", self.decision()["reason"])
        self.data["recipients"][0]["closing_time"] = 15
        self.assertEqual(self.decision()["status"], "assigned")

    def test_ready_time_and_vehicle_reuse_without_overlap(self):
        self.data["recipients"][0]["capacity"] = 20
        self.data["donations"][0]["ready_time"] = 10
        self.data["donations"].append(dict(self.data["donations"][0], id="D2", ready_time=0))
        decisions = schedule(self.data)["decisions"]
        self.assertEqual([d["scheduled_time"] for d in decisions], [10, 25])
        self.assertEqual([d["delivery_time"] for d in decisions], [25, 40])
        self.assertTrue(all(d["status"] == "assigned" for d in decisions))

    def test_maximum_pickups(self):
        self.data["recipients"][0]["capacity"] = 20
        self.data["volunteers"][0]["max_pickups"] = 1
        self.data["donations"].append(dict(self.data["donations"][0], id="D2"))
        result = schedule(self.data)
        self.assertEqual(result["decisions"][1]["status"], "unassigned")
        self.assertIn("maximum pickups", result["decisions"][1]["reason"])

    def test_same_area_constraints(self):
        self.data["recipients"][0]["area"] = "North"
        self.assertIn("recipient is outside", self.decision()["reason"])
        self.data["recipients"][0]["area"] = "Central"
        self.data["volunteers"][0]["area"] = "North"
        self.assertIn("volunteer is outside", self.decision()["reason"])

    def test_metrics_and_urgent_threshold(self):
        self.data["donations"][0]["expiry"] = 60
        metrics = schedule(self.data)["metrics"]
        self.assertEqual(metrics["urgent_rescue_rate"], 1)
        self.assertEqual(metrics["recipient_capacity_utilization"], 0.6)
        self.assertEqual(metrics["volunteer_capacity_utilization"], 0.3)
        self.assertEqual(metrics["food_quantity_at_risk"], 0)
        self.data["donations"][0]["expiry"] = 61
        self.assertIsNone(schedule(self.data)["metrics"]["urgent_rescue_rate"])

    def test_greedy_quantity_and_input_order_tiebreakers(self):
        self.data["recipients"][0]["capacity"] = 100
        self.data["volunteers"][0]["max_pickups"] = 5
        self.data["donations"].extend([
            dict(self.data["donations"][0], id="D2", quantity=8),
            dict(self.data["donations"][0], id="D3", quantity=8)])
        result = schedule(self.data, "greedy")
        self.assertEqual([d["donation_id"] for d in result["decisions"]], ["D2", "D3", "D1"])

    def test_first_feasible_pair_in_input_order(self):
        self.data["recipients"].insert(0, dict(self.data["recipients"][0], id="R0", capacity=0))
        self.data["volunteers"].insert(0, dict(self.data["volunteers"][0], id="V0", vehicle_capacity=1))
        self.assertEqual((self.decision()["recipient_id"], self.decision()["volunteer_id"]), ("R1", "V1"))

    def test_no_mutation_or_state_leak_between_runs(self):
        original = copy.deepcopy(self.data)
        self.assertEqual(schedule(self.data), schedule(self.data))
        compare(self.data)
        self.assertEqual(self.data, original)

    def test_invalid_fields(self):
        cases = [("donations", "quantity", True), ("donations", "quantity", 0),
                 ("donations", "expiry", -1), ("donations", "ready_time", "9"),
                 ("donations", "food_type", ""), ("donations", "id", " D1"),
                 ("recipients", "capacity", -1), ("recipients", "accepted_food_types", [""]),
                 ("volunteers", "max_pickups", 1.5), ("volunteers", "area", 2),
                 ("volunteers", "available_until", -1)]
        for entity, field, value in cases:
            data = copy.deepcopy(self.data)
            data[entity][0][field] = value
            with self.subTest(entity=entity, field=field), self.assertRaises(ValueError):
                validate_data(data)
        self.data["volunteers"][0].update(available_from=10, available_until=9)
        with self.assertRaisesRegex(ValueError, "available_until"):
            validate_data(self.data)

    def test_missing_resources_and_zero_capacity(self):
        for entity in ("recipients", "volunteers"):
            data = copy.deepcopy(self.data)
            data[entity] = []
            self.assertEqual(schedule(data)["decisions"][0]["status"], "unassigned")
        self.data["recipients"][0]["capacity"] = 0
        self.data["volunteers"][0]["max_pickups"] = 0
        metrics = schedule(self.data)["metrics"]
        self.assertIsNone(metrics["recipient_capacity_utilization"])
        self.assertIsNone(metrics["volunteer_capacity_utilization"])

    def test_nonzero_now_and_case_insensitive_matching(self):
        self.data["recipients"][0].update(accepted_food_types=["MEALS"], area="central")
        result = schedule(self.data, now=50)
        self.assertEqual(result["decisions"][0]["scheduled_time"], 50)
        self.assertEqual(result["metrics"]["urgent_rescue_rate"], 1)

    def test_greedy_can_rescue_less_quantity(self):
        self.data["donations"][0]["quantity"] = 10
        self.data["donations"].append(dict(self.data["donations"][0], id="D2", quantity=1, expiry=30))
        result = compare(self.data)
        self.assertEqual(result["comparison"]["quantity_rescued_delta"], -9)

    def test_sample_and_cli(self):
        root = Path(__file__).resolve().parents[1]
        result = compare(load_data(root / "data" / "sample.json"))
        self.assertEqual(result["fifo"]["metrics"]["food_quantity_rescued"], 13)
        self.assertEqual(result["greedy"]["metrics"]["food_quantity_rescued"], 15)
        self.assertEqual(result["fifo"]["metrics"]["urgent_rescue_rate"], 0)
        self.assertEqual(result["greedy"]["metrics"]["urgent_rescue_rate"], 1)
        cli = subprocess.run([sys.executable, str(root / "RescueRoute.py"), "--json"],
                             capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(cli.stdout), result)

    def test_invalid_scheduler_options(self):
        for options in ({"strategy": "unknown"}, {"now": -1}, {"trip_minutes": 0},
                        {"urgent_minutes": -1}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                schedule(self.data, **options)


if __name__ == "__main__":
    unittest.main()
