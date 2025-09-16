import argparse
import sqlite3
import datetime
import os

# --- Database Setup and Management ---

DB_FILE = "personal_crm.db"

def connect_to_db():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def create_tables():
    """Creates the necessary database tables if they don't already exist."""
    conn = connect_to_db()
    cursor = conn.cursor()

    # Create contacts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create notes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        note_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
    );
    """)

    # Create reminders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        reminder_date DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

# --- Contact Functions ---

def add_contact(first_name, last_name):
    """Adds a new contact to the database."""
    conn = connect_to_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO contacts (first_name, last_name) VALUES (?, ?)", (first_name, last_name))
        conn.commit()
        print(f"Successfully added {first_name} {last_name}.")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def find_contact_by_name(full_name):
    """Finds a contact by their full name and returns their ID."""
    conn = connect_to_db()
    cursor = conn.cursor()
    name_parts = full_name.split()
    if len(name_parts) == 1:
        cursor.execute("SELECT id FROM contacts WHERE first_name = ?", (name_parts[0],))
    else:
        cursor.execute("SELECT id FROM contacts WHERE first_name = ? AND last_name = ?", (name_parts[0], ' '.join(name_parts[1:])))

    result = cursor.fetchone()
    conn.close()
    if result:
        return result['id']
    return None

def list_contacts():
    """Lists all contacts in the database."""
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name, last_name FROM contacts ORDER BY first_name, last_name")
    contacts = cursor.fetchall()
    conn.close()

    if not contacts:
        print("No contacts found. Add one with the 'add' command.")
        return

    print("--- Your Contacts ---")
    for contact in contacts:
        last_name = contact['last_name'] if contact['last_name'] else ""
        print(f"- {contact['first_name']} {last_name}")

def view_contact(full_name):
    """Displays detailed information for a specific contact."""
    contact_id = find_contact_by_name(full_name)
    if not contact_id:
        print(f"Contact '{full_name}' not found.")
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

    conn.close()

    print(f"\n--- Details for {contact['first_name']} {contact['last_name'] or ''} ---")
    print(f"Added on: {datetime.datetime.strptime(contact['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')}")

    if notes:
        print("\nNotes:")
        for note in notes:
            note_date = datetime.datetime.strptime(note['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
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
    contact_id = find_contact_by_name(full_name)
    if not contact_id:
        print(f"Contact '{full_name}' not found.")
        return

    confirm = input(f"Are you sure you want to delete {full_name}? This cannot be undone. (y/n): ")
    if confirm.lower() == 'y':
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()
        conn.close()
        print(f"Contact {full_name} has been deleted.")
    else:
        print("Deletion cancelled.")

# --- Note and Reminder Functions ---

def add_note(full_name, message):
    """Adds a note for a specific contact."""
    contact_id = find_contact_by_name(full_name)
    if not contact_id:
        print(f"Contact '{full_name}' not found.")
        return

    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (contact_id, note_text) VALUES (?, ?)", (contact_id, message))
    conn.commit()
    conn.close()
    print(f"Note added for {full_name}.")

def add_reminder(full_name, message, date_str):
    """Adds a reminder for a specific contact."""
    contact_id = find_contact_by_name(full_name)
    if not contact_id:
        print(f"Contact '{full_name}' not found.")
        return

    try:
        # Validate date format
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        print("Error: Date must be in YYYY-MM-DD format.")
        return

    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (contact_id, message, reminder_date) VALUES (?, ?, ?)", (contact_id, message, date_str))
    conn.commit()
    conn.close()
    print(f"Reminder set for {full_name} on {date_str}.")


def list_reminders():
    """Lists all upcoming reminders."""
    conn = connect_to_db()
    cursor = conn.cursor()
    today = datetime.date.today().strftime('%Y-%m-%d')

    cursor.execute("""
    SELECT r.reminder_date, r.message, c.first_name, c.last_name
    FROM reminders r
    JOIN contacts c ON r.contact_id = c.id
    WHERE r.reminder_date >= ?
    ORDER BY r.reminder_date ASC
    """, (today,))

    reminders = cursor.fetchall()
    conn.close()

    if not reminders:
        print("No upcoming reminders.")
        return

    print("--- Upcoming Reminders ---")
    for reminder in reminders:
        last_name = reminder['last_name'] or ''
        print(f"[{reminder['reminder_date']}] For {reminder['first_name']} {last_name}: {reminder['message']}")


# --- Main Application Logic & CLI Parsing ---

def main():
    """Main function to run the CLI application."""
    # Ensure the database and tables exist
    create_tables()

    parser = argparse.ArgumentParser(description="A simple command-line CRM to manage personal relationships.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'add' command
    parser_add = subparsers.add_parser("add", help="Add a new contact.")
    parser_add.add_argument("name", type=str, help="Contact's full name (e.g., 'John Doe').")

    # 'list' command
    subparsers.add_parser("list", help="List all contacts.")

    # 'view' command
    parser_view = subparsers.add_parser("view", help="View details for a specific contact.")
    parser_view.add_argument("name", type=str, help="Contact's full name.")

    # 'delete' command
    parser_delete = subparsers.add_parser("delete", help="Delete a contact.")
    parser_delete.add_argument("name", type=str, help="Contact's full name.")

    # 'note' command
    parser_note = subparsers.add_parser("note", help="Add a note for a contact.")
    parser_note.add_argument("name", type=str, help="Contact's full name.")
    parser_note.add_argument("-m", "--message", required=True, type=str, help="The content of the note.")

    # 'reminder' command
    parser_reminder = subparsers.add_parser("reminder", help="Set a reminder for a contact.")
    parser_reminder.add_argument("name", type=str, help="Contact's full name.")
    parser_reminder.add_argument("-d", "--date", required=True, type=str, help="Reminder date in YYYY-MM-DD format.")
    parser_reminder.add_argument("-m", "--message", required=True, type=str, help="The reminder message.")

    # 'reminders' command to list upcoming reminders
    subparsers.add_parser("reminders", help="List all upcoming reminders.")

    args = parser.parse_args()

    if args.command == "add":
        name_parts = args.name.split()
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
        add_contact(first_name, last_name)
    elif args.command == "list":
        list_contacts()
    elif args.command == "view":
        view_contact(args.name)
    elif args.command == "delete":
        delete_contact(args.name)
    elif args.command == "note":
        add_note(args.name, args.message)
    elif args.command == "reminder":
        add_reminder(args.name, args.message, args.date)
    elif args.command == "reminders":
        list_reminders()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
