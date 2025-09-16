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
        last_contacted_at TIMESTAMP,
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

    # Create tags table for categorizing contacts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # Create a join table for the many-to-many relationship between contacts and tags
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contact_tags (
        contact_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (contact_id, tag_id),
        FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

# --- Contact Functions ---

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

    # Get tags for the contact
    cursor.execute("""
        SELECT t.name FROM tags t
        JOIN contact_tags ct ON t.id = ct.tag_id
        WHERE ct.contact_id = ?
    """, (contact_id,))
    tags = [row['name'] for row in cursor.fetchall()]

    conn.close()

    if contact['last_contacted_at']:
        ts_str = contact['last_contacted_at'].split('.')[0]
        last_contacted_str = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    else:
        last_contacted_str = 'Never'

    print(f"\n--- Details for {contact['first_name']} {contact['last_name'] or ''} ---")
    print(f"Last Contacted: {last_contacted_str}")
    print(f"Added on: {datetime.datetime.strptime(contact['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')}")

    if tags:
        print(f"Tags: {', '.join(tags)}")

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

def _update_last_contacted(contact_id):
    """Internal function to update the last_contacted_at timestamp for a contact."""
    conn = connect_to_db()
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute("UPDATE contacts SET last_contacted_at = ? WHERE id = ?", (now, contact_id))
    conn.commit()
    conn.close()

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
    _update_last_contacted(contact_id)
    print(f"Note added for {full_name}.")

def log_interaction(full_name, message):
    """Logs an interaction with a contact and updates their last_contacted_at."""
    contact_id = find_contact_by_name(full_name)
    if not contact_id:
        print(f"Contact '{full_name}' not found.")
        return

    # We can log the interaction as a note
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (contact_id, note_text) VALUES (?, ?)", (contact_id, f"Logged interaction: {message}"))
    conn.commit()
    conn.close()

    _update_last_contacted(contact_id)
    print(f"Logged interaction for {full_name}.")

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
    _update_last_contacted(contact_id)
    print(f"Reminder set for {full_name} on {date_str}.")


# --- Tag Functions ---

def add_tag_to_contact(full_name, tag_name):
    """Adds a tag to a specific contact."""
    contact_id = find_contact_by_name(full_name)
    if not contact_id:
        print(f"Contact '{full_name}' not found.")
        return

    conn = connect_to_db()
    cursor = conn.cursor()

    # Find or create the tag
    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
    tag = cursor.fetchone()
    if not tag:
        cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
        tag_id = cursor.lastrowid
        print(f"Created new tag: '{tag_name}'")
    else:
        tag_id = tag['id']

    # Add the tag to the contact
    try:
        cursor.execute("INSERT INTO contact_tags (contact_id, tag_id) VALUES (?, ?)", (contact_id, tag_id))
        conn.commit()
        print(f"Tagged '{full_name}' with '{tag_name}'.")
    except sqlite3.IntegrityError:
        print(f"'{full_name}' is already tagged with '{tag_name}'.")
    finally:
        conn.close()

def remove_tag_from_contact(full_name, tag_name):
    """Removes a tag from a specific contact."""
    contact_id = find_contact_by_name(full_name)
    if not contact_id:
        print(f"Contact '{full_name}' not found.")
        return

    conn = connect_to_db()
    cursor = conn.cursor()

    # Find the tag
    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
    tag = cursor.fetchone()
    if not tag:
        print(f"Tag '{tag_name}' does not exist.")
        conn.close()
        return

    # Remove the tag from the contact
    cursor.execute("DELETE FROM contact_tags WHERE contact_id = ? AND tag_id = ?", (contact_id, tag['id']))
    conn.commit()
    if cursor.rowcount > 0:
        print(f"Removed tag '{tag_name}' from '{full_name}'.")
    else:
        print(f"'{full_name}' is not tagged with '{tag_name}'.")
    conn.close()


# --- Dashboard and Suggestion Functions ---

def show_status_dashboard():
    """Displays a dashboard of overdue reminders, upcoming reminders, and suggestions."""
    print("--- pCRM Status Dashboard ---")
    conn = connect_to_db()
    cursor = conn.cursor()
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    next_week_str = (datetime.date.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')

    # Overdue reminders
    cursor.execute("""
        SELECT r.reminder_date, r.message, c.first_name, c.last_name
        FROM reminders r JOIN contacts c ON r.contact_id = c.id
        WHERE r.reminder_date < ? ORDER BY r.reminder_date ASC
    """, (today_str,))
    overdue_reminders = cursor.fetchall()

    # Upcoming reminders (next 7 days)
    cursor.execute("""
        SELECT r.reminder_date, r.message, c.first_name, c.last_name
        FROM reminders r JOIN contacts c ON r.contact_id = c.id
        WHERE r.reminder_date >= ? AND r.reminder_date <= ?
        ORDER BY r.reminder_date ASC
    """, (today_str, next_week_str))
    upcoming_reminders = cursor.fetchall()
    conn.close()

    if overdue_reminders:
        print("\n--- Overdue Reminders (!) ---")
        for r in overdue_reminders:
            print(f"[{r['reminder_date']}] For {r['first_name']} {r['last_name'] or ''}: {r['message']}")
    else:
        print("\n--- No Overdue Reminders ---")


    if upcoming_reminders:
        print("\n--- Reminders (Next 7 Days) ---")
        for r in upcoming_reminders:
            print(f"[{r['reminder_date']}] For {r['first_name']} {r['last_name'] or ''}: {r['message']}")
    else:
        print("\n--- No Upcoming Reminders in the Next 7 Days ---")

    print("") # Add a blank line for spacing
    suggest_contacts()


def suggest_contacts(days=30):
    """Suggests contacts who have not been contacted recently."""
    conn = connect_to_db()
    cursor = conn.cursor()
    threshold_date = datetime.datetime.now() - datetime.timedelta(days=days)

    cursor.execute("""
        SELECT first_name, last_name, last_contacted_at
        FROM contacts
        WHERE last_contacted_at < ?
        ORDER BY last_contacted_at ASC
    """, (threshold_date,))

    contacts = cursor.fetchall()
    conn.close()

    if not contacts:
        print(f"No suggestions. Everyone has been contacted within the last {days} days.")
        return

    print(f"--- Suggestions (not contacted in over {days} days) ---")
    for contact in contacts:
        last_name = contact['last_name'] or ''
        ts_str = contact['last_contacted_at'].split('.')[0]
        last_contacted_str = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        print(f"- {contact['first_name']} {last_name} (last contacted {last_contacted_str})")


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
    parser_list = subparsers.add_parser("list", help="List all contacts.")
    parser_list.add_argument("-t", "--tag", type=str, help="Filter contacts by a specific tag.")

    # 'view' command
    parser_view = subparsers.add_parser("view", help="View details for a specific contact.")
    parser_view.add_argument("name", type=str, help="Contact's full name.")

    # 'delete' command
    parser_delete = subparsers.add_parser("delete", help="Delete a contact.")
    parser_delete.add_argument("name", type=str, help="Contact's full name.")

    # 'tag' command
    parser_tag = subparsers.add_parser("tag", help="Add a tag to a contact.")
    parser_tag.add_argument("name", type=str, help="Contact's full name.")
    parser_tag.add_argument("tag_name", type=str, help="The tag to add.")

    # 'untag' command
    parser_untag = subparsers.add_parser("untag", help="Remove a tag from a contact.")
    parser_untag.add_argument("name", type=str, help="Contact's full name.")
    parser_untag.add_argument("tag_name", type=str, help="The tag to remove.")

    # 'note' command
    parser_note = subparsers.add_parser("note", help="Add a note for a contact.")
    parser_note.add_argument("name", type=str, help="Contact's full name.")
    parser_note.add_argument("-m", "--message", required=True, type=str, help="The content of the note.")

    # 'log' command
    parser_log = subparsers.add_parser("log", help="Log an interaction with a contact.")
    parser_log.add_argument("name", type=str, help="Contact's full name.")
    parser_log.add_argument("-m", "--message", required=True, type=str, help="A short description of the interaction.")

    # 'reminder' command
    parser_reminder = subparsers.add_parser("reminder", help="Set a reminder for a contact.")
    parser_reminder.add_argument("name", type=str, help="Contact's full name.")
    parser_reminder.add_argument("-d", "--date", required=True, type=str, help="Reminder date in YYYY-MM-DD format.")
    parser_reminder.add_argument("-m", "--message", required=True, type=str, help="The reminder message.")

    # 'reminders' command to list upcoming reminders
    subparsers.add_parser("reminders", help="List all upcoming reminders.")

    # 'suggest' command
    parser_suggest = subparsers.add_parser("suggest", help="Suggest contacts to reconnect with.")
    parser_suggest.add_argument("--days", type=int, default=30, help="The number of days since last contact.")

    # 'status' command
    subparsers.add_parser("status", help="Show a dashboard of reminders and suggestions.")


    args = parser.parse_args()

    if args.command == "add":
        name_parts = args.name.split()
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
        add_contact(first_name, last_name)
    elif args.command == "list":
        list_contacts(args.tag)
    elif args.command == "view":
        view_contact(args.name)
    elif args.command == "delete":
        delete_contact(args.name)
    elif args.command == "tag":
        add_tag_to_contact(args.name, args.tag_name)
    elif args.command == "untag":
        remove_tag_from_contact(args.name, args.tag_name)
    elif args.command == "note":
        add_note(args.name, args.message)
    elif args.command == "log":
        log_interaction(args.name, args.message)
    elif args.command == "reminder":
        add_reminder(args.name, args.message, args.date)
    elif args.command == "reminders":
        list_reminders()
    elif args.command == "suggest":
        suggest_contacts(args.days)
    elif args.command == "status":
        show_status_dashboard()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
