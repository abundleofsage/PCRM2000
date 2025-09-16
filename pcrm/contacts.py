import sqlite3
import datetime
from .database import connect_to_db

# This function is internal to the contacts module but will be used by other modules.
def _update_last_contacted(contact_id):
    """Internal function to update the last_contacted_at timestamp for a contact."""
    conn = connect_to_db()
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute("UPDATE contacts SET last_contacted_at = ? WHERE id = ?", (now, contact_id))
    conn.commit()
    conn.close()

def add_contact(first_name, last_name):
    """Adds a new contact to the database."""
    conn = connect_to_db()
    cursor = conn.cursor()
    now = datetime.datetime.now()
    try:
        cursor.execute(
            "INSERT INTO contacts (first_name, last_name, created_at) VALUES (?, ?, ?)",
            (first_name, last_name, now)
        )
        conn.commit()
        print(f"Successfully added {first_name} {last_name}.")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def find_contacts_by_name(full_name):
    """
    Finds contacts by name, case-insensitively.
    Returns a list of matching contacts (as sqlite3.Row objects).
    """
    conn = connect_to_db()
    cursor = conn.cursor()
    name_parts = full_name.strip().split()

    if len(name_parts) == 1:
        # If one name is given, search both first and last names for an exact match
        term = name_parts[0].lower()
        cursor.execute(
            "SELECT id, first_name, last_name FROM contacts WHERE LOWER(first_name) = ? OR LOWER(last_name) = ?",
            (term, term)
        )
    else:
        first_name = name_parts[0].lower()
        last_name = ' '.join(name_parts[1:]).lower()
        cursor.execute(
            "SELECT id, first_name, last_name FROM contacts WHERE LOWER(first_name) = ? AND LOWER(last_name) = ?",
            (first_name, last_name)
        )

    results = cursor.fetchall()
    conn.close()
    return results

def list_contacts(tag_name=None):
    """Lists all contacts, optionally filtering by a tag."""
    conn = connect_to_db()
    cursor = conn.cursor()

    if tag_name:
        cursor.execute("""
            SELECT c.id, c.first_name, c.last_name
            FROM contacts c
            JOIN contact_tags ct ON c.id = ct.contact_id
            JOIN tags t ON ct.tag_id = t.id
            WHERE t.name = ?
            ORDER BY c.first_name, c.last_name
        """, (tag_name,))
        header = f"--- Contacts Tagged '{tag_name}' ---"
    else:
        cursor.execute("SELECT id, first_name, last_name FROM contacts ORDER BY first_name, last_name")
        header = "--- Your Contacts ---"

    contacts = cursor.fetchall()
    conn.close()

    if not contacts:
        if tag_name:
            print(f"No contacts found with the tag '{tag_name}'.")
        else:
            print("No contacts found. Add one with the 'add' command.")
        return

    print(header)
    for contact in contacts:
        last_name = contact['last_name'] or ''
        print(f"- {contact['first_name']} {last_name}")


def choose_contact(full_name):
    """
    Finds contacts by name and handles ambiguity by prompting the user.
    Returns a single contact ID or None if no contact is chosen.
    """
    contacts = find_contacts_by_name(full_name)

    if not contacts:
        print(f"Contact '{full_name}' not found.")
        return None

    if len(contacts) == 1:
        return contacts[0]['id']

    # Multiple contacts found, prompt user to choose
    print(f"\nMultiple contacts found for '{full_name}'. Please choose one:")
    for i, contact in enumerate(contacts):
        last_name = contact['last_name'] or ''
        print(f"  {i + 1}: {contact['first_name']} {last_name} (ID: {contact['id']})")

    while True:
        try:
            choice = input("Enter the number of the contact (or 'q' to cancel): ")
            if choice.lower() == 'q':
                print("Operation cancelled.")
                return None

            choice_index = int(choice) - 1
            if 0 <= choice_index < len(contacts):
                return contacts[choice_index]['id']
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def view_contact(full_name):
    """Displays detailed information for a specific contact."""
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    conn = connect_to_db()
    cursor = conn.cursor()

    # Get contact details
    cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
    contact = cursor.fetchone()

    # Get notes for the contact
    cursor.execute("SELECT note_text, created_at FROM notes WHERE contact_id = ? ORDER BY created_at DESC", (contact_id,))
    notes = cursor.fetchall()

    # Get reminders for the contact
    cursor.execute("SELECT message, reminder_date FROM reminders WHERE contact_id = ? ORDER BY reminder_date ASC", (contact_id,))
    reminders = cursor.fetchall()

    # Get tags for the contact
    cursor.execute("""
        SELECT t.name FROM tags t
        JOIN contact_tags ct ON t.id = ct.tag_id
        WHERE ct.contact_id = ?
    """, (contact_id,))
    tags = [row['name'] for row in cursor.fetchall()]

    conn.close()

    if contact['last_contacted_at']:
        last_contacted_str = contact['last_contacted_at'].strftime('%Y-%m-%d')
    else:
        last_contacted_str = 'Never'

    print(f"\n--- Details for {contact['first_name']} {contact['last_name'] or ''} ---")
    print(f"Last Contacted: {last_contacted_str}")
    print(f"Added on: {contact['created_at'].strftime('%Y-%m-%d')}")

    if tags:
        print(f"Tags: {', '.join(tags)}")

    if notes:
        print("\nNotes:")
        for note in notes:
            note_date = note['created_at'].strftime('%Y-%m-%d')
            print(f"  [{note_date}] {note['note_text']}")
    else:
        print("\nNo notes for this contact yet.")

    if reminders:
        print("\nReminders:")
        for reminder in reminders:
            print(f"  [{reminder['reminder_date']}] {reminder['message']}")
    else:
        print("\nNo reminders for this contact yet.")


def delete_contact(full_name):
    """Deletes a contact and all their associated data."""
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    # To get the name for the confirmation prompt, we need to fetch it.
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name FROM contacts WHERE id = ?", (contact_id,))
    contact = cursor.fetchone()
    conn.close()
    if not contact:
        print(f"Could not find contact with ID {contact_id} to delete.") # Should not happen
        return

    contact_full_name = f"{contact['first_name']} {contact['last_name'] or ''}".strip()

    confirm = input(f"Are you sure you want to delete {contact_full_name}? This cannot be undone. (y/n): ")
    if confirm.lower() == 'y':
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()
        conn.close()
        print(f"Contact {contact_full_name} has been deleted.")
    else:
        print("Deletion cancelled.")


def edit_contact(full_name):
    """Finds a contact and allows the user to edit their name."""
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    # Get the current name for context
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name FROM contacts WHERE id = ?", (contact_id,))
    contact = cursor.fetchone()
    conn.close()
    if not contact:
        print(f"Error: Could not retrieve contact with ID {contact_id}.")
        return

    current_full_name = f"{contact['first_name']} {contact['last_name'] or ''}".strip()
    print(f"Editing contact: {current_full_name}")

    new_first_name = input(f"Enter new first name (current: {contact['first_name']}): ").strip()
    new_last_name = input(f"Enter new last name (current: {contact['last_name'] or ''}): ").strip()

    if not new_first_name:
        print("First name cannot be empty. Edit cancelled.")
        return

    # If last name is empty, it should be stored as NULL
    if not new_last_name:
        new_last_name = None

    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE contacts SET first_name = ?, last_name = ? WHERE id = ?",
        (new_first_name, new_last_name, contact_id)
    )
    conn.commit()
    conn.close()

    new_full_name = f"{new_first_name} {new_last_name or ''}".strip()
    print(f"Successfully updated contact to '{new_full_name}'.")
