import sqlite3
import datetime
from contextlib import contextmanager

# --- Datetime handling for SQLite ---
# The default adapter is deprecated in Python 3.12
def adapt_datetime_iso(dt):
    """Adapter to store datetimes as ISO 8601 strings."""
    return dt.isoformat()

def convert_timestamp(ts):
    """Converter to parse ISO 8601 strings back to datetime objects."""
    # The timestamp is stored as a string, which sqlite3 returns as bytes.
    return datetime.datetime.fromisoformat(ts.decode('utf-8'))

sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
sqlite3.register_converter("timestamp", convert_timestamp)


# --- Database Setup and Management ---

DB_FILE = "personal_crm.db"

def connect_to_db():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

@contextmanager
def get_db_connection():
    """
    A context manager for handling database connections.
    It ensures the connection is automatically closed.
    """
    conn = connect_to_db()
    try:
        yield conn
    finally:
        conn.close()

def create_tables():
    """Creates the necessary database tables if they don't already exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create contacts table
        cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT,
        email TEXT,
        birthday DATE,
        date_met TIMESTAMP,
        how_met TEXT,
        favorite_color TEXT,
        last_contacted_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create phones table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS phones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        phone_number TEXT NOT NULL,
        phone_type TEXT,
        FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
    );
    """)

    # Create pets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
    );
    """)

    # Create partners table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS partners (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
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

    # Create special occasions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS special_occasions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        date DATE NOT NULL,
        FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE
    );
    """)

    # Create gifts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        occasion_id INTEGER,
        description TEXT NOT NULL,
        direction TEXT NOT NULL, -- "given" or "received"
        date DATE,
        FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE CASCADE,
        FOREIGN KEY (occasion_id) REFERENCES special_occasions (id) ON DELETE SET NULL
    );
    """)

    conn.commit()
    conn.close()
