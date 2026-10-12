# [donation_id, donor_name, food_type, expiration_date, location, ready_time]
SAMPLE_DONATIONS = [
	("D-101", "Bob Michael", "Baby Formula", 10, 23, 2, 3),
	("D-102", "Bob Michael", "Baby Formula", 10, 23, 2, 3),
	("D-103", "Bob Michael", "Baby Formula", 10, 23, 2, 3),
	("D-104", "Bob Michael", "Baby Formula", 10, 23, 2, 3)
]

# [recipient_id, org_name, [food_types], capacity, location, next_delivery_day]
SAMPLE_RECIPIENTS = [
	("R-101", "Main Street Pantry", ["Baby Formula", "Canned Goods", "Baked Goods"], 100, 2, 10),
	("R-102", "Main Street Pantry", ["Baby Formula", "Canned Goods", "Baked Goods"], 100, 2, 10),
	("R-103", "Main Street Pantry", ["Baby Formula", "Canned Goods", "Baked Goods"], 100, 2, 10),
	("R-104", "Main Street Pantry", ["Baby Formula", "Canned Goods", "Baked Goods"], 100, 2, 10)
]

# [volunteer_id, capacity, location, [availability], max_pickups]
SAMPLE_VOLUNTEERS = [
	("V-101", 30, 2,[1,2,3], 10),
	("V-102", 30, 2,[1,2,3], 10),
	("V-103", 30, 2,[1,2,3], 10),
	("V-104", 30, 2,[1,2,3], 10)
]


assignments = []
rejections = []


def validate_donations(donations):
	seen_ids = set()

	for donation in donations:
		if len(donation) != 7:
			raise ValueError("Each donatoin must contain id, donor name, food type, quantity, expiration date, pickup location, ready time")
		donation_id, donor_name, food_type, quantity, expiration_date, pickup_location, ready_time = donation

		if not isinstance(donation_id, str) or not donation_id.strip():
			raise ValueError(f"Each donation ID must be a non-empty string.")
		if donation_id in seen_ids:
			raise ValueError(f"Duplicate donation ID: {donation_id}")
		seen_ids.add(donation_id)
		if not isinstance(donor_name, str) or not donor_name.strip():
			raise ValueError(f"Donation {donation_id} must include the donor's name.")
		if not isinstance(food_type, str) or not food_type.strip():
			raise ValueError(f"Donation {donation_id} must include what type of food it is.")
		if not isinstance(quantity, int) or not quantity > 0:
			raise ValueError(f"Donation {donation_id} must have a quantity greater than 0.")
		if not isinstance(expiration_date, int):
			raise ValueError(f"Donation {donation_id} must include the expiration date of the food item.")
		if not isinstance(pickup_location, int) or not pickup_location >= 0:
			raise ValueError(f"Donation {donation_id} must include the pickup location.")
		if not isinstance(ready_time, str):
			raise ValueError(f"Donation {donation_id} must include the expiration date of the food item.")

def validate_recipiets(recipients):
	seen_ids = set()

	for recipient in recipients:
		if len(recipient) != 6:
			raise ValueError("Each recipient must contain, id, organization name, accepted food types, capacity, location, and next delivery date")
		recipient_id, org_name, accepted_food_types, capacity, location, next_delivery_day = recipient

		if not isinstance(recipient_id, str) or not recipient_id.strip():
			raise ValueError(f"Each recipient ID must be a non-empty string.")
		if recipient_id in seen_ids:
			raise ValueError(f"Duplicate recipient ID: {recipient_id}")
		seen_ids.add(recipient_id)
		if not isinstance(org_name, str) or not org_name.strip():
			raise ValueError(f"Recipient {recipient_id} must include the organization's name.")
		if not isinstance(accepted_food_types, list) or not bool(accepted_food_types):
			raise ValueError(f"Recipient {recipient_id} must include what food types it accepts as donations.")
		for accepted_food_type in accepted_food_types:
			if not isinstance(accepted_food_type, str) or accepted_food_type.strip():
				raise ValueError(f"Recipient {recipient_id} accepted food types must be non-empty strings.")
		if not isinstance(capacity, int) or not capacity > 0:
			raise ValueError(f"Recipient {recipient_id} must have a capacity greater than 0 to receive donations.")
		if not isinstance(location, int):
			raise ValueError(f"Recipient {recipient_id} must include their location to recieve donations.")
		if not isinstance(next_delivery_day, int) or not next_delivery_day > 0:
			raise ValueError(f"Recipient {recipient_id} must have a next deilvery day to recieve donations.")

def validate_volunteers(volunteers):
	seen_ids = set()

	for volunteer in volunteers:
		if len(recipient) != 5:
			raise ValueError("Each volunteer must contain, id, vehicle capacity, location covered, availability, and maximum pickups")
		volunteer_id, capacity, location, availability, max_pickups = recipient

		if not isinstance(volunteer_id, str) or not volunteer_id.strip():
			raise ValueError(f"Each recipient ID must be a non-empty string.")
		if volunteer_id in seen_ids:
			raise ValueError(f"Duplicate volunteer ID: {volunteer_id}")
		seen_ids.add(volunteer_id)
		if not isinstance(capacity, int) or not capacity > 0:
			raise ValueError(f"Volunteer {volunteer_id} must a capacity greater than 0 for donation pickups and dropoffs.")
		if not isinstance(location, int) or not location >= 0:
			raise ValueError(f"Volunteer {volunteer_id} must have a location for donation pickups and dropoffs.")
		if not isinstance(availability, list) or not bool(availability):
			raise ValueError(f"Volunteer {volunteer_id} must have list of available days for pickups and dropoffs.")
		for availability_item in availability:
			if not isinstance(availability_item, int):
				raise ValueError(f"Volunteer {volunteer_id} availibility list must consist of integers greater than or equal to 0")
		if not isinstance(max_pickups, int) or not max_pickups > 0:
			raise ValueError(f"Volunteer {volunteer_id} must have a maximum number of pickups greater than 0.")


# returns the list of recipients that accept the food_type
def recipients_by_food_type(food_type, recipients):
	matched_recipients = []
	for recipient in recipients:
		for recipient_food_type in recipient[2]:
			if recipient_food_type.casefold() == food_type.casfold():
				matched_recipients.append(recipient)
	return matched_recipients

# returns lists of volunteers and recipients matching the donation location
def volunteers_by_location(volunteers, donation, recipients):
	locatoin_matched_volunteers = []
	location_matched_recipients = []

	for volunteer in volunteers:
		if volunteer[]

def volunteers_by_availability(volunteers, donation,):

def reject_donation(donation, rejection_reason):

def assign_donation(donation, recipient, volunteer, reason, status):

def first_in_first_out_assignment(donations, recipients, volunteers):
	validate_donations(donations)
	validate_recipiets(recipients)
	validate_volunteers(volunteers)

	for donation in donations:
		food_matched_recipients = recipients_by_food_type(donation[2])

def greedy_urgency_first_assignment(donations, recipients, volunteers):
