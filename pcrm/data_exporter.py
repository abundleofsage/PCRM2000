import csv
from .database import connect_to_db

def export_data_to_csv():
    """Exports all contact data to a CSV file."""
    conn = connect_to_db()
    cursor = conn.cursor()

    # Get all contacts
    cursor.execute("SELECT id, first_name, last_name FROM contacts")
    contacts = cursor.fetchall()

    if not contacts:
        print("No contacts to export.")
        conn.close()
        return

    filename = "pcrm_export.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['contact_id', 'first_name', 'last_name', 'notes', 'tags']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for contact in contacts:
            contact_id = contact['id']

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
                'notes': notes_str,
                'tags': tags_str,
            })

    conn.close()
    print(f"Successfully exported all data to {filename}")
