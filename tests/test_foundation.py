"""Integration checks for the preserved teammate-authored foundation."""
import unittest
from unittest.mock import patch

import RescueRoute as foundation
from rescue_route_app import schedule, validate_data
from test_rescue_route import example


class FoundationTests(unittest.TestCase):
    def test_original_samples_validate(self):
        foundation.validate_donations(foundation.SAMPLE_DONATIONS)
        foundation.validate_recipiets(foundation.SAMPLE_RECIPIENTS)
        foundation.validate_volunteers(foundation.SAMPLE_VOLUNTEERS)

    def test_original_samples_work_with_both_original_entry_points(self):
        for strategy in (foundation.first_in_first_out_assignment,
                         foundation.greedy_urgency_first_assignment):
            with self.subTest(strategy=strategy.__name__):
                result = strategy(foundation.SAMPLE_DONATIONS, foundation.SAMPLE_RECIPIENTS,
                                  foundation.SAMPLE_VOLUNTEERS)
                self.assertEqual(result['metrics']['donations_assigned'], 4)
                self.assertEqual(result['metrics']['food_quantity_rescued'], 40)
                self.assertTrue(all(d['scheduled_time'] == 3 for d in result['decisions']))
                self.assertEqual(len({d['volunteer_id'] for d in result['decisions']}), 4)

    def test_json_app_uses_existing_validators(self):
        for name in ('validate_donations', 'validate_recipiets', 'validate_volunteers'):
            with self.subTest(name=name):
                with patch.object(foundation, name, wraps=getattr(foundation, name)) as validator:
                    validate_data(example())
                    validator.assert_called_once()
                    self.assertIsInstance(validator.call_args.args[0][0], tuple)

    def test_scheduler_uses_original_food_matching_helper(self):
        with patch.object(foundation, 'recipients_by_food_type',
                          wraps=foundation.recipients_by_food_type) as helper:
            result = schedule(example())
            helper.assert_called_once()
            self.assertEqual(result['decisions'][0]['status'], 'assigned')

    def test_tuple_duplicate_donation_rejected(self):
        donations = [foundation.SAMPLE_DONATIONS[0]] * 2
        with self.assertRaisesRegex(ValueError, 'Duplicate donation ID'):
            foundation.first_in_first_out_assignment(donations, foundation.SAMPLE_RECIPIENTS,
                                                     foundation.SAMPLE_VOLUNTEERS)

    def test_tuple_food_matching_and_location_helpers(self):
        matches = foundation.recipients_by_food_type('baby formula', foundation.SAMPLE_RECIPIENTS)
        self.assertEqual(matches, foundation.SAMPLE_RECIPIENTS)
        donation = foundation.SAMPLE_DONATIONS[0]
        volunteers, recipients = foundation.volunteers_by_location(
            foundation.SAMPLE_VOLUNTEERS, donation, foundation.SAMPLE_RECIPIENTS)
        self.assertEqual(volunteers, foundation.SAMPLE_VOLUNTEERS)
        self.assertEqual(recipients, foundation.SAMPLE_RECIPIENTS)
        self.assertEqual(foundation.volunteers_by_availability(volunteers, donation), volunteers)

    def test_discrete_pickup_times_are_not_treated_as_continuous(self):
        donations = [('D1', 'Donor', 'meals', 1, 12, 0, 2),
                     ('D2', 'Donor', 'meals', 1, 12, 0, 2)]
        recipients = [('R1', 'Shelter', ['meals'], 10, 0, 12)]
        volunteers = [('V1', 10, 0, [1, 10], 2)]
        result = foundation.first_in_first_out_assignment(donations, recipients, volunteers)
        self.assertEqual(result['decisions'][0]['scheduled_time'], 10)
        self.assertEqual(result['decisions'][1]['status'], 'unassigned')
        self.assertIn('permitted pickup time', result['decisions'][1]['reason'])

    def test_added_assignment_and_rejection_helpers(self):
        foundation.assignments.clear()
        foundation.rejections.clear()
        try:
            assigned = foundation.assign_donation(foundation.SAMPLE_DONATIONS[0],
                foundation.SAMPLE_RECIPIENTS[0], foundation.SAMPLE_VOLUNTEERS[0],
                'Compatible donation', 'assigned')
            rejected = foundation.reject_donation(foundation.SAMPLE_DONATIONS[1], 'No capacity')
            self.assertEqual(foundation.assignments, [assigned])
            self.assertEqual(foundation.rejections, [rejected])
            self.assertEqual(assigned['donation_id'], 'D-101')
            self.assertEqual(rejected['status'], 'unassigned')
        finally:
            foundation.assignments.clear()
            foundation.rejections.clear()

    def test_invalid_optional_pickup_times(self):
        for times in ([], [True], [-1], [101], '10'):
            data = example()
            data['volunteers'][0]['pickup_times'] = times
            with self.subTest(times=times), self.assertRaises(ValueError):
                validate_data(data)


if __name__ == '__main__':
    unittest.main()
