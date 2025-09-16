import os
import datetime
from .database import connect_to_db, create_tables
from .contacts import (
    add_contact,
    list_contacts,
    view_contact,
    edit_contact,
    delete_contact,
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


def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


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
        last_contacted_str = contact['last_contacted_at'].strftime('%Y-%m-%d')
        print(f"- {contact['first_name']} {last_name} (last contacted {last_contacted_str})")

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

def interactive_menu():
    """Displays the interactive menu and handles user input."""
    create_tables()  # Ensure tables are created at the start
    input_func = input

    while True:
        clear_screen()
        print("--- pCRM Main Menu ---")

        menu_items = [
            "Add Contact",
            "List Contacts",
            "View Contact",
            "Edit Contact",
            "Delete Contact",
            "Add Note to Contact",
            "Add Reminder for Contact",
            "Tag Contact",
            "Untag Contact",
            "Log Interaction",
            "Suggest Contacts",
            "List Reminders",
            "View Dashboard",
            "Export Data to CSV",
            "Import Contacts from CSV",
            "Exit"
        ]

        for i, item in enumerate(menu_items, 1):
            print(f"{i}. {item}")

        choice = input_func("Enter your choice (1-16): ").strip()

        if choice == '1':
            name = input_func("Enter contact's full name: ")
            name_parts = name.split()
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
            add_contact(first_name, last_name)
        elif choice == '2':
            tag = input_func("Enter tag to filter by (or press Enter for all): ").strip()
            list_contacts(tag if tag else None)
        elif choice == '3':
            name = input_func("Enter contact's full name to view: ")
            view_contact(name)
        elif choice == '4':
            name = input_func("Enter contact's full name to edit: ")
            edit_contact(name)
        elif choice == '5':
            name = input_func("Enter contact's full name to delete: ")
            delete_contact(name)
        elif choice == '6':
            name = input_func("Enter contact's full name for the note: ")
            message = input_func("Enter the note: ")
            add_note(name, message)
        elif choice == '7':
            name = input_func("Enter contact's full name for the reminder: ")
            message = input_func("Enter the reminder message: ")
            date_str = input_func("Enter the reminder date (YYYY-MM-DD): ")
            add_reminder(name, message, date_str)
        elif choice == '8':
            name = input_func("Enter contact's full name to tag: ")
            tag = input_func("Enter the tag: ")
            add_tag_to_contact(name, tag)
        elif choice == '9':
            name = input_func("Enter contact's full name to untag: ")
            tag = input_func("Enter the tag: ")
            remove_tag_from_contact(name, tag)
        elif choice == '10':
            name = input_func("Enter contact's full name to log interaction: ")
            message = input_func("Enter the interaction details: ")
            log_interaction(name, message)
        elif choice == '11':
            suggest_contacts()
        elif choice == '12':
            list_reminders()
        elif choice == '13':
            show_status_dashboard()
        elif choice == '14':
            export_data_to_csv()
        elif choice == '15':
            import_contacts_from_csv()
        elif choice == '16':
            print("Exiting pCRM. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

        if choice != '16':
            input_func("\nPress Enter to continue...")
