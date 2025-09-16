import os
import datetime
from rich.console import Console
from .database import get_db_connection, create_tables
from .utils import is_valid_date, is_valid_email
from .contacts import (
    add_contact,
    list_contacts,
    view_contact,
    edit_contact,
    delete_contact,
    add_phone_to_contact,
    add_pet_to_contact,
    add_partner_to_contact,
    advanced_search_contacts,
)
from .interactions import (
    add_note,
    add_reminder,
    log_interaction,
    list_reminders,
)
from .tags import (
    add_tag_to_contact,
    remove_tag_from_contact,
)
from .data_exporter import export_data_to_csv
from .data_importer import import_contacts_from_csv
from .occasions import (
    add_special_occasion,
    add_gift,
    view_occasions_for_contact,
    view_gifts_for_contact,
)
from .google_calendar import create_calendar_event


def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def suggest_contacts(days=30):
    """Suggests contacts who have not been contacted recently."""
    console = Console()
    threshold_date = datetime.datetime.now() - datetime.timedelta(days=days)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT first_name, last_name, last_contacted_at
            FROM contacts
            WHERE last_contacted_at < ?
            ORDER BY last_contacted_at ASC
        """, (threshold_date,))
        contacts = cursor.fetchall()

    if not contacts:
        console.print(f"No suggestions. Everyone has been contacted within the last {days} days.", style="green")
        return

    console.print(f"--- Suggestions (not contacted in over {days} days) ---", style="bold cyan")
    for contact in contacts:
        last_name = contact['last_name'] or ''
        last_contacted_str = contact['last_contacted_at'].strftime('%Y-%m-%d')
        console.print(f"- {contact['first_name']} {last_name} (last contacted {last_contacted_str})", style="cyan")

def show_status_dashboard():
    """Displays a dashboard of overdue reminders, upcoming reminders, and suggestions."""
    console = Console()
    console.print("--- pCRM Status Dashboard ---", style="bold blue")
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    next_week_str = (datetime.date.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')

    with get_db_connection() as conn:
        cursor = conn.cursor()
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

    if overdue_reminders:
        console.print("\n--- Overdue Reminders (!) ---", style="bold red")
        for r in overdue_reminders:
            console.print(f"[{r['reminder_date']}] For {r['first_name']} {r['last_name'] or ''}: {r['message']}", style="red")
    else:
        console.print("\n--- No Overdue Reminders ---", style="green")


    if upcoming_reminders:
        console.print("\n--- Reminders (Next 7 Days) ---", style="bold yellow")
        for r in upcoming_reminders:
            console.print(f"[{r['reminder_date']}] For {r['first_name']} {r['last_name'] or ''}: {r['message']}", style="yellow")
    else:
        console.print("\n--- No Upcoming Reminders in the Next 7 Days ---", style="green")

    print("") # Add a blank line for spacing
    suggest_contacts()

def _handle_contact_management(choice, console, input_func):
    """Handles all logic for the Contact Management submenu."""
    if choice == '1':  # Add Contact
        first_name = input_func("Enter first name: ").strip()
        if not first_name:
            console.print("First name cannot be empty.", style="bold red")
            return
        last_name = input_func("Enter last name: ").strip() or None
        while True:
            email = input_func("Enter email: ").strip() or None
            if is_valid_email(email):
                break
            console.print("Invalid email format. Please try again.", style="bold red")
        while True:
            birthday = input_func("Enter birthday (YYYY-MM-DD): ").strip() or None
            if is_valid_date(birthday):
                break
            console.print("Invalid date format. Please use YYYY-MM-DD.", style="bold red")
        while True:
            date_met = input_func("Enter date met (YYYY-MM-DD): ").strip() or None
            if is_valid_date(date_met):
                break
            console.print("Invalid date format. Please use YYYY-MM-DD.", style="bold red")
        how_met = input_func("How did you meet? ").strip() or None
        favorite_color = input_func("Enter favorite color: ").strip() or None

        contact_id = add_contact(first_name, last_name, email, birthday, date_met, how_met, favorite_color)

        if contact_id:
            while True:
                phone = input_func("Add a phone number? (y/n): ").lower()
                if phone == 'y':
                    number = input_func("Enter phone number: ").strip()
                    ptype = input_func("Enter phone type (e.g., mobile): ").strip()
                    add_phone_to_contact(contact_id, number, ptype)
                else:
                    break
            while True:
                pet = input_func("Add a pet? (y/n): ").lower()
                if pet == 'y':
                    name = input_func("Enter pet's name: ").strip()
                    add_pet_to_contact(contact_id, name)
                else:
                    break
            while True:
                partner = input_func("Add a partner? (y/n): ").lower()
                if partner == 'y':
                    name = input_func("Enter partner's name: ").strip()
                    add_partner_to_contact(contact_id, name)
                else:
                    break
    elif choice == '2':  # List Contacts
        tag = input_func("Enter tag to filter by (or press Enter for all): ").strip()
        list_contacts(tag if tag else None)
    elif choice == '3':  # Advanced Search
        console.print("--- Advanced Search ---", style="bold blue")
        console.print("Enter search criteria. Leave blank to skip a field.")
        criteria = {}
        searchable_fields = ["first_name", "last_name", "email", "birthday", "date_met", "how_met", "favorite_color"]
        for field in searchable_fields:
            value = input_func(f"Search by {field.replace('_', ' ')}: ").strip()
            if value:
                criteria[field] = value
        if criteria:
            advanced_search_contacts(criteria)
        else:
            console.print("No search criteria entered.", style="yellow")
    elif choice == '4':  # View Contact
        name = input_func("Enter contact's full name to view: ")
        view_contact(name)
    elif choice == '5':  # Edit Contact
        name = input_func("Enter contact's full name to edit: ")
        edit_contact(name)
    elif choice == '6':  # Delete Contact
        name = input_func("Enter contact's full name to delete: ")
        delete_contact(name)
    elif choice == '7':  # Tag Contact
        name = input_func("Enter contact's full name to tag: ")
        tag = input_func("Enter the tag: ")
        add_tag_to_contact(name, tag)
    elif choice == '8':  # Untag Contact
        name = input_func("Enter contact's full name to untag: ")
        tag = input_func("Enter the tag: ")
        remove_tag_from_contact(name, tag)

def _handle_interactions_reminders(choice, console, input_func):
    """Handles all logic for the Interactions & Reminders submenu."""
    if choice == '9':  # Add Note
        name = input_func("Enter contact's full name for the note: ")
        message = input_func("Enter the note: ")
        add_note(name, message)
    elif choice == '10':  # Add Reminder
        name = input_func("Enter contact's full name for the reminder: ")
        message = input_func("Enter the reminder message: ")
        while True:
            date_str = input_func("Enter the reminder date (YYYY-MM-DD): ")
            if is_valid_date(date_str):
                break
            console.print("Invalid date format. Please use YYYY-MM-DD.", style="bold red")
        reminder_date = add_reminder(name, message, date_str)
        if reminder_date:
            add_to_gcal = input("Add this reminder to Google Calendar? (y/n): ").lower()
            if add_to_gcal == 'y':
                summary = f"Reminder for {name}: {message}"
                # Create a 1-hour event at 9am on the reminder date
                start_time = reminder_date.replace(hour=9, minute=0, second=0)
                end_time = start_time + datetime.timedelta(hours=1)
                create_calendar_event(summary, start_time, end_time)
    elif choice == '11':  # Log Interaction
        name = input_func("Enter contact's full name to log interaction: ")
        message = input_func("Enter the interaction details: ")
        log_interaction(name, message)
    elif choice == '12':  # List Reminders
        list_reminders()
    elif choice == '13':  # Suggest Contacts
        suggest_contacts()
    elif choice == '14':  # View Dashboard
        show_status_dashboard()

def _handle_occasions_gifts(choice, console, input_func):
    """Handles all logic for the Occasions & Gifts submenu."""
    if choice == '15':  # Add Special Occasion
        name = input_func("Enter contact's full name for the occasion: ")
        occasion_name = input_func("Enter the occasion name (e.g., Anniversary): ")
        while True:
            date_str = input_func("Enter the occasion date (YYYY-MM-DD): ")
            if is_valid_date(date_str):
                break
            console.print("Invalid date format. Please use YYYY-MM-DD.", style="bold red")
        occasion_date = add_special_occasion(name, occasion_name, date_str)
        if occasion_date:
            add_to_gcal = input("Add this occasion to Google Calendar? (y/n): ").lower()
            if add_to_gcal == 'y':
                summary = f"{occasion_name} for {name}"
                # Create an all-day event
                start_date = occasion_date.date()
                end_date = start_date + datetime.timedelta(days=1)
                create_calendar_event(summary, start_date, end_date)
    elif choice == '16':  # View Special Occasions
        name = input_func("Enter contact's full name to view occasions: ")
        view_occasions_for_contact(name)
    elif choice == '17':  # Add Gift
        name = input_func("Enter contact's full name for the gift: ")
        description = input_func("Enter the gift description: ")
        direction = input_func("Was the gift given or received? ")
        while True:
            date_str = input_func("Enter the date of the gift (YYYY-MM-DD, optional): ").strip() or None
            if is_valid_date(date_str):
                break
            console.print("Invalid date format. Please use YYYY-MM-DD.", style="bold red")
        add_gift(name, description, direction, date_str)
    elif choice == '18':  # View Gifts
        name = input_func("Enter contact's full name to view gifts: ")
        view_gifts_for_contact(name)

def _handle_data_management(choice, console, input_func):
    """Handles all logic for the Data Management submenu."""
    if choice == '19':  # Export
        export_data_to_csv()
    elif choice == '20':  # Import
        import_contacts_from_csv()

def interactive_menu():
    """Displays the interactive menu and handles user input."""
    create_tables()  # Ensure tables are created at the start
    input_func = input
    console = Console()

    menu = {
        "Contact Management": {
            "1": "Add Contact", "2": "List Contacts", "3": "Advanced Search",
            "4": "View Contact", "5": "Edit Contact", "6": "Delete Contact",
            "7": "Tag Contact", "8": "Untag Contact",
        },
        "Interactions & Reminders": {
            "9": "Add Note to Contact", "10": "Add Reminder for Contact",
            "11": "Log Interaction", "12": "List Reminders",
            "13": "Suggest Contacts", "14": "View Dashboard",
        },
        "Occasions & Gifts": {
            "15": "Add Special Occasion", "16": "View Special Occasions",
            "17": "Add Gift", "18": "View Gifts",
        },
        "Data Management": {
            "19": "Export Data to CSV", "20": "Import Contacts from CSV",
        }
    }

    # Create a flat map of choice to handler
    choice_handlers = {
        **{k: _handle_contact_management for k in menu["Contact Management"]},
        **{k: _handle_interactions_reminders for k in menu["Interactions & Reminders"]},
        **{k: _handle_occasions_gifts for k in menu["Occasions & Gifts"]},
        **{k: _handle_data_management for k in menu["Data Management"]},
    }

    while True:
        clear_screen()
        console.print("--- pCRM Main Menu ---", style="bold magenta")

        total_items = 0
        for category, items in menu.items():
            console.print(f"\n--- {category} ---", style="bold green")
            for number, text in items.items():
                console.print(f"{number}. {text}")
                total_items += 1

        exit_option = total_items + 1
        console.print(f"\n--- Other ---", style="bold green")
        console.print(f"{exit_option}. Exit")

        choice = input_func(f"Enter your choice (1-{exit_option}): ").strip()

        if choice == str(exit_option):
            console.print("Exiting pCRM. Goodbye!", style="bold blue")
            break

        handler = choice_handlers.get(choice)
        if handler:
            handler(choice, console, input_func)
        else:
            console.print("Invalid choice. Please try again.", style="bold red")

        if choice != str(exit_option):
            input_func("\nPress Enter to continue...")
