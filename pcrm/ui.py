import os
import datetime
from rich.console import Console
from .database import connect_to_db, create_tables
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


def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def suggest_contacts(days=30):
    """Suggests contacts who have not been contacted recently."""
    console = Console()
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

def interactive_menu():
    """Displays the interactive menu and handles user input."""
    create_tables()  # Ensure tables are created at the start
    input_func = input
    console = Console()

    while True:
        clear_screen()
        console.print("--- pCRM Main Menu ---", style="bold magenta")

        menu = {
            "Contact Management": {
                "1": "Add Contact",
                "2": "List Contacts",
                "3": "Advanced Search",
                "4": "View Contact",
                "5": "Edit Contact",
                "6": "Delete Contact",
                "7": "Tag Contact",
                "8": "Untag Contact",
            },
            "Interactions & Reminders": {
                "9": "Add Note to Contact",
                "10": "Add Reminder for Contact",
                "11": "Log Interaction",
                "12": "List Reminders",
                "13": "Suggest Contacts",
                "14": "View Dashboard",
            },
            "Occasions & Gifts": {
                "15": "Add Special Occasion",
                "16": "View Special Occasions",
                "17": "Add Gift",
                "18": "View Gifts",
            },
            "Data Management": {
                "19": "Export Data to CSV",
                "20": "Import Contacts from CSV",
            }
        }

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

        if choice == '1': # Add Contact
            first_name = input_func("Enter first name: ").strip()
            if not first_name:
                print("First name cannot be empty.")
                continue
            last_name = input_func("Enter last name: ").strip() or None
            email = input_func("Enter email: ").strip() or None
            birthday = input_func("Enter birthday (YYYY-MM-DD): ").strip() or None
            date_met = input_func("Enter date met (YYYY-MM-DD): ").strip() or None
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
        elif choice == '2': # List Contacts
            tag = input_func("Enter tag to filter by (or press Enter for all): ").strip()
            list_contacts(tag if tag else None)
        elif choice == '3': # Advanced Search
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
        elif choice == '4': # View Contact
            name = input_func("Enter contact's full name to view: ")
            view_contact(name)
        elif choice == '5': # Edit Contact
            name = input_func("Enter contact's full name to edit: ")
            edit_contact(name)
        elif choice == '6': # Delete Contact
            name = input_func("Enter contact's full name to delete: ")
            delete_contact(name)
        elif choice == '7': # Tag Contact
            name = input_func("Enter contact's full name to tag: ")
            tag = input_func("Enter the tag: ")
            add_tag_to_contact(name, tag)
        elif choice == '8': # Untag Contact
            name = input_func("Enter contact's full name to untag: ")
            tag = input_func("Enter the tag: ")
            remove_tag_from_contact(name, tag)
        elif choice == '9': # Add Note
            name = input_func("Enter contact's full name for the note: ")
            message = input_func("Enter the note: ")
            add_note(name, message)
        elif choice == '10': # Add Reminder
            name = input_func("Enter contact's full name for the reminder: ")
            message = input_func("Enter the reminder message: ")
            date_str = input_func("Enter the reminder date (YYYY-MM-DD): ")
            add_reminder(name, message, date_str)
        elif choice == '11': # Log Interaction
            name = input_func("Enter contact's full name to log interaction: ")
            message = input_func("Enter the interaction details: ")
            log_interaction(name, message)
        elif choice == '12': # List Reminders
            list_reminders()
        elif choice == '13': # Suggest Contacts
            suggest_contacts()
        elif choice == '14': # View Dashboard
            show_status_dashboard()
        elif choice == '15': # Add Special Occasion
            name = input_func("Enter contact's full name for the occasion: ")
            occasion_name = input_func("Enter the occasion name (e.g., Anniversary): ")
            date_str = input_func("Enter the occasion date (YYYY-MM-DD): ")
            add_special_occasion(name, occasion_name, date_str)
        elif choice == '16': # View Special Occasions
            name = input_func("Enter contact's full name to view occasions: ")
            view_occasions_for_contact(name)
        elif choice == '17': # Add Gift
            name = input_func("Enter contact's full name for the gift: ")
            description = input_func("Enter the gift description: ")
            direction = input_func("Was the gift given or received? ")
            date_str = input_func("Enter the date of the gift (YYYY-MM-DD, optional): ").strip() or None
            add_gift(name, description, direction, date_str)
        elif choice == '18': # View Gifts
            name = input_func("Enter contact's full name to view gifts: ")
            view_gifts_for_contact(name)
        elif choice == '19': # Export
            export_data_to_csv()
        elif choice == '20': # Import
            import_contacts_from_csv()
        elif choice == str(exit_option): # Exit
            print("Exiting pCRM. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

        if choice != str(exit_option):
            input_func("\nPress Enter to continue...")
