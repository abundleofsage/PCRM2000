import sqlite3
from .database import connect_to_db
from .contacts import choose_contact

def add_tag_to_contact(full_name, tag_name):
    """Adds a tag to a specific contact."""
    contact_id = choose_contact(full_name)
    if not contact_id:
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
    contact_id = choose_contact(full_name)
    if not contact_id:
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
