import csv
import os
import re
from .contacts import add_contact, add_phone_to_contact, add_pet_to_contact, add_partner_to_contact

def import_contacts_from_csv():
    """Imports contacts from a CSV file named 'pcrm_import.csv'."""
    filename = "pcrm_import.csv"
    if not os.path.exists(filename):
        print(f"Error: Import file not found at '{filename}'")
        print("Please create a 'pcrm_import.csv' file with 'first_name' and 'last_name' columns.")
        return

    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Check for required columns
            if 'first_name' not in reader.fieldnames:
                print("Error: CSV file must have a 'first_name' column.")
                return

            contacts_to_add = []
            for row in reader:
                first_name = row.get('first_name', '').strip()
                if not first_name:
                    print(f"Skipping a row due to missing first_name.")
                    continue

                # last_name is optional, handle its absence gracefully
                last_name = row.get('last_name', '').strip() or None

                contacts_to_add.append(row)

        if not contacts_to_add:
            print("No new contacts to import from the file.")
            return

        print(f"Found {len(contacts_to_add)} contacts to import.")
        confirm = input("Proceed with importing these contacts? (y/n): ").lower()

        if confirm == 'y':
            count = 0
            for contact_data in contacts_to_add:
                contact_id = add_contact(
                    first_name=contact_data['first_name'],
                    last_name=contact_data.get('last_name') or None,
                    email=contact_data.get('email') or None,
                    birthday=contact_data.get('birthday') or None,
                    date_met=contact_data.get('date_met') or None,
                    how_met=contact_data.get('how_met') or None,
                    favorite_color=contact_data.get('favorite_color') or None
                )

                if contact_id:
                    # Import phones
                    if contact_data.get('phones'):
                        phones_str = contact_data['phones']
                        # Regex to handle "number(type)" format
                        for phone_match in re.finditer(r'([^|]+)\(([^)]+)\)', phones_str):
                            number, type = phone_match.groups()
                            add_phone_to_contact(contact_id, number.strip(), type.strip())

                    # Import pets
                    if contact_data.get('pets'):
                        for pet_name in contact_data['pets'].split('|'):
                            if pet_name.strip():
                                add_pet_to_contact(contact_id, pet_name.strip())

                    # Import partners
                    if contact_data.get('partners'):
                        for partner_name in contact_data['partners'].split('|'):
                            if partner_name.strip():
                                add_partner_to_contact(contact_id, partner_name.strip())

                    count += 1

            print(f"\nSuccessfully imported {count} contacts.")
        else:
            print("Import cancelled.")

    except Exception as e:
        print(f"An error occurred during import: {e}")
