import csv
import os
from .contacts import add_contact

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
                # last_name is optional, handle its absence gracefully
                last_name = row.get('last_name', '').strip() or None

                if not first_name:
                    print(f"Skipping a row due to missing first_name.")
                    continue

                contacts_to_add.append({'first_name': first_name, 'last_name': last_name})

        if not contacts_to_add:
            print("No new contacts to import from the file.")
            return

        print(f"Found {len(contacts_to_add)} contacts to import.")
        confirm = input("Proceed with importing these contacts? (y/n): ").lower()

        if confirm == 'y':
            count = 0
            for contact in contacts_to_add:
                add_contact(contact['first_name'], contact['last_name'])
                count += 1
            print(f"\nSuccessfully imported {count} contacts.")
        else:
            print("Import cancelled.")

    except Exception as e:
        print(f"An error occurred during import: {e}")
