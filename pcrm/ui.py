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

    bunny = r"""
       _     _
       \`\ /`/
        \ V /
        /. .\\
       =\ T /=
        / ^ \\
     {}/\\ //\\
     __\ " " /__
jgs (____/^\____)
"""

    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80  # Default width

    bunny_lines = bunny.strip().split('\n')
    bunny_width = len(max(bunny_lines, key=len))
    padding = " " * (terminal_width - bunny_width - 2)


    while True:
        print("\n--- pCRM Main Menu ---")

        menu_items = [
            "(A)dd Contact",
            "(L)ist Contacts",
            "(V)iew Contact",
            "(E)dit Contact",
            "(D)elete Contact",
            "Add (N)ote to Contact",
            "Add (R)eminder for Contact",
            "(T)ag Contact",
            "(U)ntag Contact",
            "Lo(g) Interaction",
            "(S)uggest Contacts",
            "List Re(m)inders",
            "View Das(h)board",
            "E(x)it"
        ]

        for i, item in enumerate(menu_items):
            if i < len(bunny_lines):
                padding = " " * (terminal_width - len(item) - len(bunny_lines[i]))
                print(f"{item}{padding}{bunny_lines[i]}")
            else:
                print(item)


        choice = input_func(f"Enter your choice: ").strip().lower()

        if choice == 'a':
            name = input_func("Enter contact's full name: ")
            name_parts = name.split()
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
            add_contact(first_name, last_name)
        elif choice == 'l':
            tag = input_func("Enter tag to filter by (or press Enter for all): ").strip()
            list_contacts(tag if tag else None)
        elif choice == 'v':
            name = input_func("Enter contact's full name to view: ")
            view_contact(name)
        elif choice == 'e':
            name = input_func("Enter contact's full name to edit: ")
            edit_contact(name)
        elif choice == 'd':
            name = input_func("Enter contact's full name to delete: ")
            delete_contact(name)
        elif choice == 'n':
            name = input_func("Enter contact's full name for the note: ")
            message = input_func("Enter the note: ")
            add_note(name, message)
        elif choice == 'r':
            name = input_func("Enter contact's full name for the reminder: ")
            message = input_func("Enter the reminder message: ")
            date_str = input_func("Enter the reminder date (YYYY-MM-DD): ")
            add_reminder(name, message, date_str)
        elif choice == 't':
            name = input_func("Enter contact's full name to tag: ")
            tag = input_func("Enter the tag: ")
            add_tag_to_contact(name, tag)
        elif choice == 'u':
            name = input_func("Enter contact's full name to untag: ")
            tag = input_func("Enter the tag: ")
            remove_tag_from_contact(name, tag)
        elif choice == 'g':
            name = input_func("Enter contact's full name to log interaction: ")
            message = input_func("Enter the interaction details: ")
            log_interaction(name, message)
        elif choice == 's':
            suggest_contacts()
        elif choice == 'm':
            list_reminders()
        elif choice == 'h':
            show_status_dashboard()
        elif choice == 'x':
            print("Exiting pCRM. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
