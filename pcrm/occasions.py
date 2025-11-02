import datetime
from .database import get_db_connection
from .contacts import choose_contact
from rich.console import Console
from rich.table import Table

def add_special_occasion(full_name, name, date_str):
    """Adds a special occasion for a contact."""
    console = Console()
    contact_id = choose_contact(full_name)
    if not contact_id:
        return None

    try:
        occasion_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        console.print("Error: Date must be in YYYY-MM-DD format.", style="bold red")
        return None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO special_occasions (contact_id, name, date) VALUES (?, ?, ?)", (contact_id, name, date_str))
        conn.commit()
    console.print(f"Special occasion '{name}' on {date_str} added for {full_name}.", style="green")
    return occasion_date

def add_gift(full_name, description, direction, date_str=None, occasion_id=None):
    """Adds a gift for a contact."""
    console = Console()
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    if date_str:
        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            console.print("Error: Date must be in YYYY-MM-DD format.", style="bold red")
            return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO gifts (contact_id, occasion_id, description, direction, date) VALUES (?, ?, ?, ?, ?)",
            (contact_id, occasion_id, description, direction, date_str)
        )
        conn.commit()
    console.print(f"Gift '{description}' ({direction}) added for {full_name}.", style="green")

def view_occasions_for_contact(full_name):
    """Views all special occasions for a contact."""
    console = Console()
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, date FROM special_occasions WHERE contact_id = ? ORDER BY date", (contact_id,))
        occasions = cursor.fetchall()

    if not occasions:
        console.print(f"No special occasions found for {full_name}.", style="yellow")
        return

    table = Table(title=f"Special Occasions for {full_name}", show_header=True, header_style="bold magenta")
    table.add_column("Occasion")
    table.add_column("Date")
    for occasion in occasions:
        table.add_row(occasion['name'], occasion['date'])
    console.print(table)

def view_gifts_for_contact(full_name):
    """Views all gifts for a contact."""
    console = Console()
    contact_id = choose_contact(full_name)
    if not contact_id:
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.description, g.direction, g.date, s.name as occasion_name
            FROM gifts g
            LEFT JOIN special_occasions s ON g.occasion_id = s.id
            WHERE g.contact_id = ?
            ORDER BY g.date DESC
        """, (contact_id,))
        gifts = cursor.fetchall()

    if not gifts:
        console.print(f"No gifts found for {full_name}.", style="yellow")
        return

    table = Table(title=f"Gifts for {full_name}", show_header=True, header_style="bold green")
    table.add_column("Description")
    table.add_column("Direction")
    table.add_column("Date")
    table.add_column("Associated Occasion")
    for gift in gifts:
        table.add_row(
            gift['description'],
            gift['direction'],
            gift['date'] or 'N/A',
            gift['occasion_name'] or 'N/A'
        )
    console.print(table)
