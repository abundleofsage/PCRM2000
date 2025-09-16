import sqlite3
import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .database import get_db_connection

# This function is internal to the contacts module but will be used by other modules.
def _update_last_contacted(contact_id):
    """Internal function to update the last_contacted_at timestamp for a contact."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        now = datetime.datetime.now()
        cursor.execute("UPDATE contacts SET last_contacted_at = ? WHERE id = ?", (now, contact_id))
        conn.commit()

def add_contact(first_name, last_name, email=None, birthday=None, date_met=None, how_met=None, favorite_color=None):
    """Adds a new contact to the database."""
    now = datetime.datetime.now()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO contacts
                   (first_name, last_name, email, birthday, date_met, how_met, favorite_color, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (first_name, last_name, email, birthday, date_met, how_met, favorite_color, now)
            )
            contact_id = cursor.lastrowid
            conn.commit()
            print(f"Successfully added {first_name} {last_name}.")
            return contact_id
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")
        return None

def add_phone_to_contact(contact_id, phone_number, phone_type):
    """Adds a phone number to a contact."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO phones (contact_id, phone_number, phone_type) VALUES (?, ?, ?)",
                (contact_id, phone_number, phone_type)
            )
            conn.commit()
            print(f"Successfully added phone number to contact.")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")

def add_pet_to_contact(contact_id, name):
    """Adds a pet to a contact."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO pets (contact_id, name) VALUES (?, ?)",
                (contact_id, name)
            )
            conn.commit()
            print(f"Successfully added pet to contact.")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")

def add_partner_to_contact(contact_id, name):
    """Adds a partner to a contact."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO partners (contact_id, name) VALUES (?, ?)",
                (contact_id, name)
            )
            conn.commit()
            print(f"Successfully added partner to contact.")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")

def find_contacts_by_name(full_name):
    """
    Finds contacts by name, case-insensitively.
    Returns a list of matching contacts (as sqlite3.Row objects).
    """
    with get_db_connection() as conn:
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
        return results

def advanced_search_contacts(criteria):
    """
    Searches for contacts based on a dictionary of criteria.
    Criteria keys should be valid column names in the contacts table.
    Values will be searched for using a LIKE query.
    """
    console = Console()
    base_query = "SELECT id, first_name, last_name, email, birthday, date_met, how_met, favorite_color FROM contacts"
    where_clauses = []
    params = []

    for key, value in criteria.items():
        # Basic validation to ensure key is a valid column name
        if key in ["first_name", "last_name", "email", "birthday", "date_met", "how_met", "favorite_color"]:
            where_clauses.append(f"{key} LIKE ?")
            params.append(f"%{value}%")

    if not where_clauses:
        console.print("No valid search criteria provided.", style="bold red")
        return

    query = f"{base_query} WHERE {' AND '.join(where_clauses)} ORDER BY first_name, last_name"

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            contacts = cursor.fetchall()
    except sqlite3.Error as e:
        console.print(f"Database error: {e}", style="bold red")
        return

    if not contacts:
        console.print("No contacts found matching your criteria.", style="yellow")
        return

    table = Table(title="Advanced Search Results", show_header=True, header_style="bold blue")
    table.add_column("ID", style="dim")
    table.add_column("First Name")
    table.add_column("Last Name")
    table.add_column("Email")
    for contact in contacts:
        table.add_row(
            str(contact['id']),
            contact['first_name'],
            contact['last_name'] or '',
            contact['email'] or ''
        )
    console.print(table)


def list_contacts(tag_name=None):
    """Lists all contacts, optionally filtering by a tag."""
    console = Console()
    with get_db_connection() as conn:
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

    if not contacts:
        if tag_name:
            console.print(f"No contacts found with the tag '{tag_name}'.", style="yellow")
        else:
            console.print("No contacts found. Add one with the 'add' command.", style="yellow")
        return

    console.print(header, style="bold blue")
    for contact in contacts:
        last_name = contact['last_name'] or ''
        console.print(f"- {contact['first_name']} {last_name}", style="blue")


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
    """Displays detailed information for a specific contact using rich."""
    console = Console()
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get all data in one go
        cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
        contact = cursor.fetchone()
        cursor.execute("SELECT phone_number, phone_type FROM phones WHERE contact_id = ?", (contact_id,))
        phones = cursor.fetchall()
        cursor.execute("SELECT name FROM pets WHERE contact_id = ?", (contact_id,))
        pets = cursor.fetchall()
        cursor.execute("SELECT name FROM partners WHERE contact_id = ?", (contact_id,))
        partners = cursor.fetchall()
        cursor.execute("SELECT note_text, created_at FROM notes WHERE contact_id = ? ORDER BY created_at DESC", (contact_id,))
        notes = cursor.fetchall()
        cursor.execute("SELECT message, reminder_date FROM reminders WHERE contact_id = ? ORDER BY reminder_date ASC", (contact_id,))
        reminders = cursor.fetchall()
        cursor.execute("SELECT t.name FROM tags t JOIN contact_tags ct ON t.id = ct.tag_id WHERE ct.contact_id = ?", (contact_id,))
        tags = [row['name'] for row in cursor.fetchall()]

    # Main Details Panel
    last_contacted_str = contact['last_contacted_at'].strftime('%Y-%m-%d') if contact['last_contacted_at'] else '[red]Never[/red]'

    details = (
        f"[b]Email:[/b] {contact['email'] or 'N/A'}\n"
        f"[b]Birthday:[/b] {contact['birthday'] or 'N/A'}\n"
        f"[b]Date Met:[/b] {contact['date_met'] or 'N/A'}\n"
        f"[b]How Met:[/b] {contact['how_met'] or 'N/A'}\n"
        f"[b]Favorite Color:[/b] {contact['favorite_color'] or 'N/A'}\n"
        f"[b]Last Contacted:[/b] {last_contacted_str}\n"
        f"[b]Added on:[/b] {contact['created_at'].strftime('%Y-%m-%d')}"
    )

    if tags:
        details += f"\n[b]Tags:[/b] [cyan]{', '.join(tags)}[/cyan]"

    panel_title = f"[bold white]{contact['first_name']} {contact['last_name'] or ''}[/bold white]"
    console.print(Panel(details, title=panel_title, border_style="blue", expand=False))

    # Associated Info in Tables
    if phones:
        table = Table(title="Phone Numbers", show_header=True, header_style="bold magenta")
        table.add_column("Number")
        table.add_column("Type")
        for phone in phones:
            table.add_row(phone['phone_number'], phone['phone_type'])
        console.print(table)

    if pets:
        table = Table(title="Pets", show_header=True, header_style="bold green")
        table.add_column("Name")
        for pet in pets:
            table.add_row(pet['name'])
        console.print(table)

    if partners:
        table = Table(title="Partners", show_header=True, header_style="bold green")
        table.add_column("Name")
        for partner in partners:
            table.add_row(partner['name'])
        console.print(table)

    if notes:
        table = Table(title="Notes", show_header=True, header_style="bold yellow")
        table.add_column("Date", style="dim")
        table.add_column("Note")
        for note in notes:
            table.add_row(note['created_at'].strftime('%Y-%m-%d'), note['note_text'])
        console.print(table)

    if reminders:
        table = Table(title="Reminders", show_header=True, header_style="bold red")
        table.add_column("Date", style="dim")
        table.add_column("Message")
        for reminder in reminders:
            table.add_row(reminder['reminder_date'], reminder['message'])
        console.print(table)


def delete_contact(full_name):
    """Deletes a contact and all their associated data."""
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    # To get the name for the confirmation prompt, we need to fetch it.
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT first_name, last_name FROM contacts WHERE id = ?", (contact_id,))
        contact = cursor.fetchone()

    if not contact:
        print(f"Could not find contact with ID {contact_id} to delete.") # Should not happen
        return

    contact_full_name = f"{contact['first_name']} {contact['last_name'] or ''}".strip()

    confirm = input(f"Are you sure you want to delete {contact_full_name}? This cannot be undone. (y/n): ")
    if confirm.lower() == 'y':
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
            conn.commit()
        print(f"Contact {contact_full_name} has been deleted.")
    else:
        print("Deletion cancelled.")


def edit_contact(full_name):
    """Finds a contact and allows the user to edit their details."""
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    while True:
        # Fetch fresh contact details each time in the loop
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
            contact = cursor.fetchone()
        if not contact:
            print(f"Error: Could not retrieve contact with ID {contact_id}.")
            return

        current_full_name = f"{contact['first_name']} {contact['last_name'] or ''}".strip()
        print(f"\n--- Editing Contact: {current_full_name} ---")
        print("1. Edit Name")
        print("2. Edit Email")
        print("3. Edit Birthday")
        print("4. Edit Date Met")
        print("5. Edit How Met")
        print("6. Edit Favorite Color")
        print("7. Add Phone Number")
        print("8. Add Pet")
        print("9. Add Partner")
        print("10. Back to Main Menu")

        choice = input("What would you like to edit? ")

        if choice == '1':
            new_first_name = input(f"Enter new first name (current: {contact['first_name']}): ").strip()
            new_last_name = input(f"Enter new last name (current: {contact['last_name'] or ''}): ").strip()
            if new_first_name:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE contacts SET first_name = ?, last_name = ? WHERE id = ?",
                                   (new_first_name, new_last_name or None, contact_id))
                    conn.commit()
                print("Name updated.")
            else:
                print("First name cannot be empty.")
        elif choice == '2':
            new_email = input(f"Enter new email (current: {contact['email'] or 'N/A'}): ").strip()
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE contacts SET email = ? WHERE id = ?", (new_email, contact_id))
                conn.commit()
            print("Email updated.")
        elif choice == '3':
            new_birthday = input(f"Enter new birthday (YYYY-MM-DD) (current: {contact['birthday'] or 'N/A'}): ").strip()
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE contacts SET birthday = ? WHERE id = ?", (new_birthday, contact_id))
                conn.commit()
            print("Birthday updated.")
        elif choice == '4':
            new_date_met = input(f"Enter new date met (YYYY-MM-DD) (current: {contact['date_met'] or 'N/A'}): ").strip()
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE contacts SET date_met = ? WHERE id = ?", (new_date_met, contact_id))
                conn.commit()
            print("Date met updated.")
        elif choice == '5':
            new_how_met = input(f"Enter new how met (current: {contact['how_met'] or 'N/A'}): ").strip()
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE contacts SET how_met = ? WHERE id = ?", (new_how_met, contact_id))
                conn.commit()
            print("How met updated.")
        elif choice == '6':
            new_favorite_color = input(f"Enter new favorite color (current: {contact['favorite_color'] or 'N/A'}): ").strip()
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE contacts SET favorite_color = ? WHERE id = ?", (new_favorite_color, contact_id))
                conn.commit()
            print("Favorite color updated.")
        elif choice == '7':
            phone_number = input("Enter phone number: ").strip()
            phone_type = input("Enter phone type (e.g., mobile, home, work): ").strip()
            if phone_number:
                add_phone_to_contact(contact_id, phone_number, phone_type)
        elif choice == '8':
            pet_name = input("Enter pet's name: ").strip()
            if pet_name:
                add_pet_to_contact(contact_id, pet_name)
        elif choice == '9':
            partner_name = input("Enter partner's name: ").strip()
            if partner_name:
                add_partner_to_contact(contact_id, partner_name)
        elif choice == '10':
            break
        else:
            print("Invalid choice. Please try again.")
