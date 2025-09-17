import json
import sqlite3
from .database import get_db_connection

def import_data_from_json(filepath):
    """
    Imports data from a JSON file, replacing all existing data.
    Returns the graph layout if it exists in the file.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # List of tables to clear and import data into
        # Order is important for foreign key constraints (delete from child tables first)
        tables = ["contact_tags", "pets", "phones", "notes", "relationships", "tags", "contacts"]

        try:
            # Disable foreign keys for the duration of the transaction
            cursor.execute("PRAGMA foreign_keys = OFF;")
            conn.commit()

            # Begin a transaction
            cursor.execute("BEGIN TRANSACTION;")

            # Clear existing data from tables
            for table in tables:
                print(f"Clearing table: {table}")
                cursor.execute(f"DELETE FROM {table};")

            # Import new data
            # The order of insertion should be the reverse of deletion
            for table_name in reversed(tables):
                if table_name in data and data[table_name]:
                    print(f"Importing data for table: {table_name}")
                    items = data[table_name]

                    # Get column names from the first item
                    columns = items[0].keys()
                    col_str = ", ".join(columns)
                    placeholders = ", ".join(["?"] * len(columns))

                    # Prepare rows of data
                    rows = [tuple(item.get(col) for col in columns) for item in items]

                    # Use INSERT OR REPLACE to handle potential conflicts and use the old IDs
                    cursor.executemany(f"INSERT OR REPLACE INTO {table_name} ({col_str}) VALUES ({placeholders})", rows)

            # Commit the transaction
            conn.commit()

        except sqlite3.Error as e:
            conn.rollback() # Rollback on error
            raise Exception(f"Database error during import: {e}")
        finally:
            # Re-enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON;")
            conn.commit()

    print("Successfully imported data.")
    return data.get("graph_layout")
