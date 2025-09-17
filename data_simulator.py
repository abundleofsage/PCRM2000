import random
import datetime
from faker import Faker
from pcrm import contacts, interactions, occasions, tags, database

# Initialize Faker
fake = Faker()

def create_random_contact(fake_generator):
    """Creates a single random contact."""
    first_name = fake_generator.first_name()
    last_name = fake_generator.last_name()
    email = fake_generator.email()
    birthday = fake_generator.date_of_birth(minimum_age=18, maximum_age=80)
    date_met = fake_generator.date_this_decade()
    how_met = random.choice(["at a conference", "through a friend", "at work", "at a social event"])
    favorite_color = fake_generator.color_name()

    return contacts.add_contact(
        first_name,
        last_name,
        email=email,
        birthday=birthday,
        date_met=date_met,
        how_met=how_met,
        favorite_color=favorite_color
    )

def add_random_phones_to_contact(contact_id, fake_generator):
    """Adds a random number of phones to a contact."""
    for _ in range(random.randint(0, 2)):
        phone_number = fake_generator.phone_number()
        phone_type = random.choice(["mobile", "home", "work"])
        contacts.add_phone_to_contact(contact_id, phone_number, phone_type)

def add_random_pets_to_contact(contact_id, fake_generator):
    """Adds a random number of pets to a contact."""
    if random.random() < 0.2:  # 20% chance of having a pet
        for _ in range(random.randint(1, 2)):
            pet_name = fake_generator.first_name()
            contacts.add_pet_to_contact(contact_id, pet_name)

def add_random_notes_to_contact(full_name, contact_id, fake_generator):
    """Adds a random number of notes to a contact."""
    for _ in range(random.randint(0, 5)):
        note = fake_generator.sentence(nb_words=10)
        interactions.add_note(full_name, note)

def add_random_reminders_to_contact(full_name, contact_id, fake_generator):
    """Adds a random number of reminders to a contact."""
    for _ in range(random.randint(0, 2)):
        message = fake_generator.sentence(nb_words=6)
        reminder_date = fake_generator.future_date(end_date="+1y")
        interactions.add_reminder(full_name, message, reminder_date.strftime('%Y-%m-%d'))

def add_random_special_occasions(full_name, contact_id, fake_generator):
    """Adds a random number of special occasions to a contact."""
    for _ in range(random.randint(0, 3)):
        occasion_name = random.choice(["Anniversary", "Work Anniversary", "Graduation"])
        occasion_date = fake_generator.date_this_decade()
        occasions.add_special_occasion(full_name, occasion_name, occasion_date.strftime('%Y-%m-%d'))

def add_random_gifts(full_name, contact_id, fake_generator):
    """Adds a random number of gifts to a contact."""
    for _ in range(random.randint(0, 4)):
        description = "A nice gift"
        direction = random.choice(["given", "received"])
        gift_date = fake_generator.date_this_decade()
        occasions.add_gift(full_name, description, direction, gift_date.strftime('%Y-%m-%d'))

def add_random_tags_to_contact(full_name, contact_id, tag_options):
    """Adds a random number of tags to a contact."""
    for _ in range(random.randint(1, 3)):
        tag = random.choice(tag_options)
        tags.add_tag_to_contact(full_name, tag)


def get_all_contact_ids():
    """Fetches all contact IDs from the database."""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM contacts")
        return [row['id'] for row in cursor.fetchall()]

def get_contact_name(contact_id):
    """Fetches the full name of a contact by ID."""
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name FROM contacts WHERE id = ?", (contact_id,))
        contact = cursor.fetchone()
        return f"{contact['first_name']} {contact['last_name']}"


def run_simulator(num_contacts=50):
    """Main function to run the data simulator."""
    print("Starting data simulation...")

    # Ensure default tags are in the database
    tags.initialize_default_tags()
    tag_options = tags.DEFAULT_TAGS


    # Generate contacts
    contact_ids = []
    for i in range(num_contacts):
        print(f"Creating contact {i + 1}/{num_contacts}...")
        contact_id = create_random_contact(fake)
        if contact_id:
            contact_ids.append(contact_id)
            full_name = get_contact_name(contact_id)
            add_random_phones_to_contact(contact_id, fake)
            add_random_pets_to_contact(contact_id, fake)
            add_random_notes_to_contact(full_name, contact_id, fake)
            add_random_reminders_to_contact(full_name, contact_id, fake)
            add_random_special_occasions(full_name, contact_id, fake)
            add_random_gifts(full_name, contact_id, fake)
            add_random_tags_to_contact(full_name, contact_id, tag_options)

    # Generate relationships
    print("Creating relationships...")
    all_contact_ids = get_all_contact_ids()
    if len(all_contact_ids) > 1:
        for _ in range(int(num_contacts * 0.75)): # Create relationships for 75% of contacts
            contact1_id, contact2_id = random.sample(all_contact_ids, 2)
            relationship_type = random.choice(["friend", "family", "colleague", "partner"])
            contacts.add_relationship(contact1_id, contact2_id, relationship_type)

    print("Data simulation complete!")

if __name__ == "__main__":
    # To run this script directly for testing
    run_simulator(num_contacts=20)
