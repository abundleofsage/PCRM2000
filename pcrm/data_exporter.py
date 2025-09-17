import csv
import json
from .database import get_db_connection

def export_data_to_json(app_instance):
    """Exports all application data to a JSON file."""
    # Get graph layout from the GUI instance
    graph_layout = {}
    if app_instance and app_instance.graph_pos:
        # Convert numpy arrays to lists for JSON serialization
        for node_id, pos in app_instance.graph_pos.items():
            graph_layout[node_id] = pos.tolist()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Fetch all data from the database
        cursor.execute("SELECT * FROM contacts")
        contacts = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM relationships")
        relationships = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM tags")
        tags = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM contact_tags")
        contact_tags = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM phones")
        phones = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM pets")
        pets = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM notes")
        notes = [dict(row) for row in cursor.fetchall()]

    # Combine into a single exportable object
    export_data = {
        "contacts": contacts,
        "relationships": relationships,
        "tags": tags,
        "contact_tags": contact_tags,
        "phones": phones,
        "pets": pets,
        "notes": notes,
        "graph_layout": graph_layout
    }

    filename = "pcrm_export.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=4, default=str) # Use default=str for any non-serializable types like dates

    print(f"Successfully exported all data to {filename}")


def export_data_to_csv():
    """Exports all contact data to a CSV file."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get all contacts
        cursor.execute("SELECT * FROM contacts")
        contacts = cursor.fetchall()

        if not contacts:
            print("No contacts to export.")
            return

        filename = "pcrm_export.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'contact_id', 'first_name', 'last_name', 'email', 'birthday',
                'date_met', 'how_met', 'favorite_color', 'phones', 'pets',
                'notes', 'tags'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for contact in contacts:
                contact_id = contact['id']

                # Get phones
                cursor.execute("SELECT phone_number, phone_type FROM phones WHERE contact_id = ?", (contact_id,))
                phones = cursor.fetchall()
                phones_str = " | ".join([f"{p['phone_number']}({p['phone_type']})" for p in phones])

                # Get pets
                cursor.execute("SELECT name FROM pets WHERE contact_id = ?", (contact_id,))
                pets = cursor.fetchall()
                pets_str = " | ".join([p['name'] for p in pets])

                # Get notes for the contact
                cursor.execute("SELECT note_text FROM notes WHERE contact_id = ?", (contact_id,))
                notes = cursor.fetchall()
                notes_str = " | ".join([note['note_text'] for note in notes])

                # Get tags for the contact
                cursor.execute("""
                    SELECT t.name FROM tags t
                    JOIN contact_tags ct ON t.id = ct.tag_id
                    WHERE ct.contact_id = ?
                """, (contact_id,))
                tags = cursor.fetchall()
                tags_str = ", ".join([tag['name'] for tag in tags])

                writer.writerow({
                    'contact_id': contact_id,
                    'first_name': contact['first_name'],
                    'last_name': contact['last_name'] or '',
                    'email': contact['email'],
                    'birthday': contact['birthday'],
                    'date_met': contact['date_met'],
                    'how_met': contact['how_met'],
                    'favorite_color': contact['favorite_color'],
                    'phones': phones_str,
                    'pets': pets_str,
                    'notes': notes_str,
                    'tags': tags_str,
                })

    print(f"Successfully exported all data to {filename}")
