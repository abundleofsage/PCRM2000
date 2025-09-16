import datetime
from rich.console import Console
from .database import get_db_connection
from .contacts import choose_contact, _update_last_contacted
from .google_calendar import create_calendar_event

def add_note(full_name, message):
    """Adds a note for a specific contact."""
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (contact_id, note_text) VALUES (?, ?)", (contact_id, message))
        conn.commit()
    _update_last_contacted(contact_id)
    print(f"Note added for {full_name}.")


def log_interaction(full_name, message):
    """Logs an interaction with a contact and updates their last_contacted_at."""
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    # We can log the interaction as a note
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (contact_id, note_text) VALUES (?, ?)", (contact_id, f"Logged interaction: {message}"))
        conn.commit()

    _update_last_contacted(contact_id)
    print(f"Logged interaction for {full_name}.")


def add_reminder(full_name, message, date_str):
    """Adds a reminder for a specific contact."""
    console = Console()
    contact_id = choose_contact(full_name)
    if not contact_id:
        return None

    try:
        # Validate date format and get datetime object
        reminder_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        console.print("Error: Date must be in YYYY-MM-DD format.", style="bold red")
        return None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reminders (contact_id, message, reminder_date) VALUES (?, ?, ?)", (contact_id, message, date_str))
        conn.commit()
    _update_last_contacted(contact_id)
    console.print(f"Reminder set for {full_name} on {date_str}.", style="green")
    return reminder_date

def list_reminders():
    """Lists all upcoming reminders."""
    console = Console()
    with get_db_connection() as conn:
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

    if not reminders:
        console.print("No upcoming reminders.", style="green")
        return

    console.print("--- Upcoming Reminders ---", style="bold yellow")
    for reminder in reminders:
        last_name = reminder['last_name'] or ''
        console.print(f"[{reminder['reminder_date']}] For {reminder['first_name']} {last_name}: {reminder['message']}", style="yellow")
