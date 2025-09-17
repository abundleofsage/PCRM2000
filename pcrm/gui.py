import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import csv
import re
import sqlite3
from .database import get_db_connection
from . import contacts
from . import data_exporter
from .google_calendar import create_calendar_event
import networkx as nx
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("pCRM")
        self.geometry("1200x800")
        self._dragged_node = None

        # Create the tab control
        self.notebook = ttk.Notebook(self)

        # Create the tabs
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.contacts_tab = ttk.Frame(self.notebook)
        self.interactions_tab = ttk.Frame(self.notebook)
        self.occasions_tab = ttk.Frame(self.notebook)
        self.relationships_tab = ttk.Frame(self.notebook)
        self.graph_tab = ttk.Frame(self.notebook)
        self.data_tab = ttk.Frame(self.notebook)

        # Add the tabs to the notebook
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.contacts_tab, text="Contact Management")
        self.notebook.add(self.interactions_tab, text="Interactions & Reminders")
        self.notebook.add(self.occasions_tab, text="Occasions & Gifts")
        self.notebook.add(self.relationships_tab, text="Relationships")
        self.notebook.add(self.graph_tab, text="Graph")
        self.notebook.add(self.data_tab, text="Data Management")

        self.notebook.pack(expand=True, fill="both")

        # 1. Set up all UI elements first
        self.setup_dashboard_tab()
        self.setup_contacts_tab()
        self.setup_interactions_tab()
        self.setup_occasions_tab()
        self.setup_relationships_tab()
        self.setup_graph_tab()
        self.setup_data_tab()

        # 2. Then, populate the UI with data
        self.populate_dashboard()
        self.populate_contacts_tree()
        self.populate_relationship_graph()

    def setup_relationships_tab(self):
        """Sets up the widgets for the relationship management tab."""
        rel_frame = ttk.Frame(self.relationships_tab, padding="10")
        rel_frame.pack(fill="both", expand=True)

        # --- Top frame for adding/removing relationships ---
        add_frame = ttk.LabelFrame(rel_frame, text="Manage Relationship", padding="10")
        add_frame.pack(fill="x", pady=5)

        # Contact 1
        ttk.Label(add_frame, text="Contact 1:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.rel_contact1_combo = ttk.Combobox(add_frame, state="readonly", width=30)
        self.rel_contact1_combo.grid(row=0, column=1, padx=5, pady=5)
        self.rel_contact1_combo.bind("<<ComboboxSelected>>", self.populate_relationships_tree)


        # Contact 2
        ttk.Label(add_frame, text="Contact 2:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.rel_contact2_combo = ttk.Combobox(add_frame, state="readonly", width=30)
        self.rel_contact2_combo.grid(row=1, column=1, padx=5, pady=5)

        # Relationship Type
        ttk.Label(add_frame, text="Relationship is:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.rel_type_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.rel_type_var, width=25).grid(row=0, column=3, padx=5, pady=5)

        # Action Buttons
        ttk.Button(add_frame, text="Add Relationship", command=self.add_relationship).grid(row=1, column=3, padx=5, pady=5, sticky="e")
        ttk.Button(add_frame, text="Remove Relationship", command=self.remove_relationship).grid(row=1, column=2, padx=5, pady=5, sticky="e")


        # --- Bottom frame for displaying existing relationships ---
        display_frame = ttk.LabelFrame(rel_frame, text="Existing Relationships for Contact 1", padding="10")
        display_frame.pack(fill="both", expand=True, pady=10)
        self.relationships_tree = self._create_treeview(display_frame, ["Related Contact", "Relationship"])

    def populate_relationships_tree(self, event=None):
        """Populates the relationships tree for the selected contact."""
        for i in self.relationships_tree.get_children():
            self.relationships_tree.delete(i)

        selected_name = self.rel_contact1_combo.get()
        if not selected_name: return
        contact_id = self.contact_map.get(selected_name)
        if not contact_id: return

        relationships = contacts.get_relationships_for_contact(contact_id)
        for rel in relationships:
            related_contact_name = f"{rel['first_name']} {rel['last_name'] or ''}"
            self.relationships_tree.insert("", "end", values=(related_contact_name, rel['relationship_type']))

    def add_relationship(self):
        """Adds a relationship between the two selected contacts."""
        name1 = self.rel_contact1_combo.get()
        name2 = self.rel_contact2_combo.get()
        rel_type = self.rel_type_var.get().strip()

        if not all([name1, name2, rel_type]):
            messagebox.showwarning("Input Required", "Please select both contacts and enter a relationship type.")
            return

        contact1_id = self.contact_map.get(name1)
        contact2_id = self.contact_map.get(name2)

        if contact1_id == contact2_id:
            messagebox.showerror("Error", "A contact cannot have a relationship with themselves.")
            return

        contacts.add_relationship(contact1_id, contact2_id, rel_type)
        messagebox.showinfo("Success", f"Relationship between {name1} and {name2} added.")
        self.populate_relationships_tree() # Refresh the view

    def remove_relationship(self):
        """Removes the relationship between the two selected contacts."""
        name1 = self.rel_contact1_combo.get()
        name2 = self.rel_contact2_combo.get()

        if not all([name1, name2]):
            messagebox.showwarning("Input Required", "Please select both contacts to remove their relationship.")
            return

        contact1_id = self.contact_map.get(name1)
        contact2_id = self.contact_map.get(name2)

        contacts.remove_relationship(contact1_id, contact2_id)
        messagebox.showinfo("Success", f"Relationship between {name1} and {name2} removed.")
        self.populate_relationships_tree() # Refresh the view

    def setup_data_tab(self):
        """Sets up the widgets for the data management tab."""
        data_frame = ttk.Frame(self.data_tab, padding="20")
        data_frame.pack(fill="both", expand=True)

        import_button = ttk.Button(data_frame, text="Import from CSV...", command=self.import_data, style="Accent.TButton")
        import_button.pack(pady=10)

        export_button = ttk.Button(data_frame, text="Export to CSV...", command=self.export_data)
        export_button.pack(pady=10)

        # Add a style for the accent button
        style = ttk.Style(self)
        style.configure("Accent.TButton", font=("Helvetica", 10, "bold"))

    def export_data(self):
        """Exports all contact data to a CSV file."""
        try:
            data_exporter.export_data_to_csv()
            messagebox.showinfo("Export Successful", "Successfully exported all data to pcrm_export.csv")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred during export: {e}")

    def import_data(self):
        """Imports contacts from a user-selected CSV file."""
        filepath = filedialog.askopenfilename(
            title="Select a CSV file to import",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                if 'first_name' not in reader.fieldnames:
                    messagebox.showerror("Import Error", "CSV file must have a 'first_name' column.")
                    return

                contacts_to_add = [row for row in reader if row.get('first_name', '').strip()]

            if not contacts_to_add:
                messagebox.showinfo("Import", "No new contacts to import from the file.")
                return

            if not messagebox.askyesno("Confirm Import", f"Found {len(contacts_to_add)} contacts to import. Proceed?"):
                return

            count = 0
            for contact_data in contacts_to_add:
                contact_id = contacts.add_contact(
                    first_name=contact_data['first_name'],
                    last_name=contact_data.get('last_name') or None,
                    email=contact_data.get('email') or None,
                    birthday=contact_data.get('birthday') or None,
                    date_met=contact_data.get('date_met') or None,
                    how_met=contact_data.get('how_met') or None,
                    favorite_color=contact_data.get('favorite_color') or None
                )
                if contact_id:
                    if contact_data.get('phones'):
                        for match in re.finditer(r'([^|]+)\(([^)]+)\)', contact_data['phones']):
                            number, type = match.groups()
                            contacts.add_phone_to_contact(contact_id, number.strip(), type.strip())
                    if contact_data.get('pets'):
                        for pet_name in contact_data['pets'].split('|'):
                            if pet_name.strip():
                                contacts.add_pet_to_contact(contact_id, pet_name.strip())
                    count += 1

            messagebox.showinfo("Import Successful", f"Successfully imported {count} contacts.")
            # Refresh all views
            self.populate_contacts_tree()
            self.populate_dashboard()

        except Exception as e:
            messagebox.showerror("Import Failed", f"An error occurred during import: {e}")


    def setup_occasions_tab(self):
        """Sets up the widgets for the occasions and gifts tab."""
        occasions_frame = ttk.Frame(self.occasions_tab, padding="10")
        occasions_frame.pack(fill="both", expand=True)

        # Contact selection
        top_frame = ttk.Frame(occasions_frame)
        top_frame.pack(fill="x", pady=5)
        ttk.Label(top_frame, text="Select Contact:").pack(side="left", padx=(0, 5))
        self.occasion_contact_combo = ttk.Combobox(top_frame, state="readonly")
        self.occasion_contact_combo.pack(side="left", fill="x", expand=True)
        # We will populate this combobox along with the interactions one
        self.occasion_contact_combo.bind("<<ComboboxSelected>>", self.populate_occasion_data)

        # Action buttons
        action_frame = ttk.Frame(occasions_frame)
        action_frame.pack(fill="x", pady=5)
        ttk.Button(action_frame, text="Add Occasion", command=self.add_occasion_window).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Add Gift", command=self.add_gift_window).pack(side="left", padx=5)

        # Data display
        data_frame = ttk.Frame(occasions_frame)
        data_frame.pack(fill="both", expand=True, pady=10)

        # Occasions Tree
        occasions_tree_frame = ttk.LabelFrame(data_frame, text="Special Occasions", padding="10")
        occasions_tree_frame.pack(fill="both", expand=True, side="left", padx=(0, 5))
        self.occasions_tree = self._create_treeview(occasions_tree_frame, ["ID", "Name", "Date"])
        self.occasions_tree.column("ID", width=40, anchor="center")

        # Gifts Tree
        gifts_tree_frame = ttk.LabelFrame(data_frame, text="Gifts", padding="10")
        gifts_tree_frame.pack(fill="both", expand=True, side="left", padx=(5, 0))
        self.gifts_tree = self._create_treeview(gifts_tree_frame, ["ID", "Description", "Direction", "Date"])
        self.gifts_tree.column("ID", width=40, anchor="center")

    def setup_interactions_tab(self):
        """Sets up the widgets for the interactions tab."""
        interactions_frame = ttk.Frame(self.interactions_tab, padding="10")
        interactions_frame.pack(fill="both", expand=True)

        # Contact selection
        top_frame = ttk.Frame(interactions_frame)
        top_frame.pack(fill="x", pady=5)
        ttk.Label(top_frame, text="Select Contact:").pack(side="left", padx=(0, 5))
        self.interaction_contact_combo = ttk.Combobox(top_frame, state="readonly")
        self.interaction_contact_combo.pack(side="left", fill="x", expand=True)
        self.interaction_contact_combo.bind("<<ComboboxSelected>>", self.populate_interaction_data)

        # Action buttons
        action_frame = ttk.Frame(interactions_frame)
        action_frame.pack(fill="x", pady=5)
        ttk.Button(action_frame, text="Add Note", command=self.add_note_window).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Add Reminder", command=self.add_reminder_window).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Log Interaction", command=self.log_interaction_window).pack(side="left", padx=5)

        # Data display
        data_frame = ttk.Frame(interactions_frame)
        data_frame.pack(fill="both", expand=True, pady=10)

        notes_frame = ttk.LabelFrame(data_frame, text="Notes & Interactions", padding="10")
        notes_frame.pack(fill="both", expand=True, side="left", padx=(0, 5))
        self.notes_tree = self._create_treeview(notes_frame, ["Date", "Note"])
        self.notes_tree.column("Note", width=300)

        reminders_frame = ttk.LabelFrame(data_frame, text="Reminders", padding="10")
        reminders_frame.pack(fill="both", expand=True, side="left", padx=(5, 0))
        self.reminders_tree = self._create_treeview(reminders_frame, ["Date", "Message"])
        self.reminders_tree.column("Message", width=300)

    def _refresh_contact_combos(self):
        """Refreshes the list of contacts in all contact selection comboboxes."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, first_name, last_name FROM contacts ORDER BY first_name, last_name")
            contacts = cursor.fetchall()

        self.contact_map = {f"{c['first_name']} {c['last_name'] or ''}": c['id'] for c in contacts}
        contact_names = list(self.contact_map.keys())
        self.interaction_contact_combo['values'] = contact_names
        self.occasion_contact_combo['values'] = contact_names
        self.rel_contact1_combo['values'] = contact_names
        self.rel_contact2_combo['values'] = contact_names

    def populate_occasion_data(self, event=None):
        """Populates the occasions and gifts trees for the selected contact."""
        selected_name = self.occasion_contact_combo.get()
        if not selected_name: return
        contact_id = self.contact_map.get(selected_name)
        if not contact_id: return

        # Clear trees
        for i in self.occasions_tree.get_children(): self.occasions_tree.delete(i)
        for i in self.gifts_tree.get_children(): self.gifts_tree.delete(i)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Populate occasions
            cursor.execute("SELECT id, name, date FROM special_occasions WHERE contact_id = ? ORDER BY date", (contact_id,))
            for occ in cursor.fetchall():
                self.occasions_tree.insert("", "end", values=(occ['id'], occ['name'], occ['date']))
            # Populate gifts
            cursor.execute("SELECT id, description, direction, date FROM gifts WHERE contact_id = ? ORDER BY date DESC", (contact_id,))
            for gift in cursor.fetchall():
                self.gifts_tree.insert("", "end", values=(gift['id'], gift['description'], gift['direction'], gift['date']))

    def _get_selected_occasion_contact_id(self):
        """Helper to get the currently selected contact's ID from the occasion combobox."""
        selected_name = self.occasion_contact_combo.get()
        if not selected_name:
            messagebox.showwarning("No Selection", "Please select a contact first.")
            return None
        return self.contact_map.get(selected_name)

    def add_occasion_window(self):
        contact_id = self._get_selected_occasion_contact_id()
        if not contact_id: return
        self._open_occasion_dialog(contact_id)

    def add_gift_window(self):
        contact_id = self._get_selected_occasion_contact_id()
        if not contact_id: return
        self._open_gift_dialog(contact_id)

    def _open_occasion_dialog(self, contact_id):
        dialog = tk.Toplevel(self)
        dialog.title("Add Special Occasion")

        ttk.Label(dialog, text="Occasion Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Date (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        date_entry = ttk.Entry(dialog, width=40)
        date_entry.grid(row=1, column=1, padx=10, pady=5)
        date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))

        gcal_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="Add to Google Calendar", variable=gcal_var).grid(row=2, column=0, columnspan=2, pady=5)

        def save():
            name = name_entry.get().strip()
            date_str = date_entry.get().strip()
            if not name or not date_str:
                messagebox.showwarning("Input Required", "Name and date are required.")
                return
            try:
                occasion_date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Invalid Format", "Date must be in YYYY-MM-DD format.")
                return

            with get_db_connection() as conn:
                conn.cursor().execute("INSERT INTO special_occasions (contact_id, name, date) VALUES (?, ?, ?)", (contact_id, name, date_str))
                conn.commit()

            if gcal_var.get():
                try:
                    contact_name = self.occasion_contact_combo.get()
                    summary = f"{name} for {contact_name}"
                    start_date = occasion_date_obj.date()
                    end_date = start_date + datetime.timedelta(days=1)
                    create_calendar_event(summary, start_date, end_date)
                    messagebox.showinfo("Google Calendar", "Event created successfully (check console for link).", parent=dialog)
                except Exception as e:
                    messagebox.showerror("Google Calendar Error", f"Could not create event: {e}", parent=dialog)

            self.populate_occasion_data()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(row=3, column=0, columnspan=2, pady=10)
        dialog.transient(self); dialog.grab_set(); self.wait_window(dialog)

    def _open_gift_dialog(self, contact_id):
        dialog = tk.Toplevel(self)
        dialog.title("Add Gift")

        ttk.Label(dialog, text="Description:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        desc_entry = ttk.Entry(dialog, width=40)
        desc_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(dialog, text="Direction (given/received):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        dir_combo = ttk.Combobox(dialog, values=["given", "received"], state="readonly", width=38)
        dir_combo.grid(row=1, column=1, padx=10, pady=5)
        dir_combo.set("given")

        ttk.Label(dialog, text="Date (YYYY-MM-DD, optional):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        date_entry = ttk.Entry(dialog, width=40)
        date_entry.grid(row=2, column=1, padx=10, pady=5)

        def save():
            desc = desc_entry.get().strip()
            direction = dir_combo.get()
            date_str = date_entry.get().strip() or None
            if not desc:
                messagebox.showwarning("Input Required", "Description is required.")
                return
            if date_str:
                try: datetime.datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError: messagebox.showerror("Invalid Format", "Date must be in YYYY-MM-DD format."); return

            with get_db_connection() as conn:
                conn.cursor().execute("INSERT INTO gifts (contact_id, description, direction, date) VALUES (?, ?, ?, ?)", (contact_id, desc, direction, date_str))
                conn.commit()
            self.populate_occasion_data()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(row=3, column=0, columnspan=2, pady=10)
        dialog.transient(self); dialog.grab_set(); self.wait_window(dialog)

    def populate_interaction_data(self, event=None):
        """Populates the notes and reminders trees for the selected contact."""
        selected_name = self.interaction_contact_combo.get()
        if not selected_name:
            return

        contact_id = self.contact_map.get(selected_name)
        if not contact_id:
            return

        # Clear existing data
        for i in self.notes_tree.get_children(): self.notes_tree.delete(i)
        for i in self.reminders_tree.get_children(): self.reminders_tree.delete(i)

        # Populate notes
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT created_at, note_text FROM notes WHERE contact_id = ? ORDER BY created_at DESC", (contact_id,))
            notes = cursor.fetchall()
            for note in notes:
                self.notes_tree.insert("", "end", values=(note['created_at'].strftime('%Y-%m-%d'), note['note_text']))

            # Populate reminders
            cursor.execute("SELECT reminder_date, message FROM reminders WHERE contact_id = ? ORDER BY reminder_date ASC", (contact_id,))
            reminders = cursor.fetchall()
            for reminder in reminders:
                self.reminders_tree.insert("", "end", values=(reminder['reminder_date'], reminder['message']))

    def _get_selected_interaction_contact_id(self):
        """Helper to get the currently selected contact's ID from the combobox."""
        selected_name = self.interaction_contact_combo.get()
        if not selected_name:
            messagebox.showwarning("No Selection", "Please select a contact first.")
            return None
        return self.contact_map.get(selected_name)

    def add_note_window(self):
        contact_id = self._get_selected_interaction_contact_id()
        if not contact_id: return
        self._open_text_input_dialog("Add Note", "Note:", lambda text: self._add_note_by_id(contact_id, text))

    def log_interaction_window(self):
        contact_id = self._get_selected_interaction_contact_id()
        if not contact_id: return
        self._open_text_input_dialog("Log Interaction", "Interaction Details:", lambda text: self._log_interaction_by_id(contact_id, text))

    def add_reminder_window(self):
        contact_id = self._get_selected_interaction_contact_id()
        if not contact_id: return
        self._open_reminder_dialog(contact_id)

    def _add_note_by_id(self, contact_id, message):
        with get_db_connection() as conn:
            conn.cursor().execute("INSERT INTO notes (contact_id, note_text) VALUES (?, ?)", (contact_id, message))
            conn.commit()
        contacts._update_last_contacted(contact_id)
        self.populate_interaction_data() # Refresh view
        self.populate_dashboard() # Refresh dashboard

    def _log_interaction_by_id(self, contact_id, message):
        note = f"Logged interaction: {message}"
        self._add_note_by_id(contact_id, note)

    def _open_text_input_dialog(self, title, prompt, save_callback):
        """Helper to open a generic dialog for single text input."""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("400x200")

        ttk.Label(dialog, text=prompt).pack(padx=10, pady=5, anchor="w")
        text_widget = tk.Text(dialog, height=5, width=50)
        text_widget.pack(padx=10, pady=5, fill="both", expand=True)

        def save():
            text = text_widget.get("1.0", tk.END).strip()
            if text:
                save_callback(text)
                dialog.destroy()
            else:
                messagebox.showwarning("Input Required", "The text field cannot be empty.")

        ttk.Button(dialog, text="Save", command=save).pack(pady=10)
        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)

    def _open_reminder_dialog(self, contact_id):
        """Opens a specific dialog for adding a reminder with a date."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Reminder")
        dialog.geometry("400x300")

        ttk.Label(dialog, text="Reminder Message:").pack(padx=10, pady=5, anchor="w")
        msg_widget = tk.Text(dialog, height=3, width=50)
        msg_widget.pack(padx=10, pady=5, fill="x", expand=True)

        ttk.Label(dialog, text="Reminder Date (YYYY-MM-DD):").pack(padx=10, pady=5, anchor="w")
        date_entry = ttk.Entry(dialog)
        date_entry.pack(padx=10, pady=5, fill="x")
        date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))

        gcal_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="Add to Google Calendar", variable=gcal_var).pack(pady=5)

        def save():
            message = msg_widget.get("1.0", tk.END).strip()
            date_str = date_entry.get().strip()
            if not message or not date_str:
                messagebox.showwarning("Input Required", "Both message and date are required.")
                return

            try:
                reminder_date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Invalid Format", "Date must be in YYYY-MM-DD format.")
                return

            with get_db_connection() as conn:
                conn.cursor().execute("INSERT INTO reminders (contact_id, message, reminder_date) VALUES (?, ?, ?)", (contact_id, message, date_str))
                conn.commit()
            contacts._update_last_contacted(contact_id)

            if gcal_var.get():
                try:
                    contact_name = self.interaction_contact_combo.get()
                    summary = f"Reminder for {contact_name}: {message}"
                    start_time = reminder_date_obj.replace(hour=9, minute=0, second=0)
                    end_time = start_time + datetime.timedelta(hours=1)
                    create_calendar_event(summary, start_time, end_time)
                    messagebox.showinfo("Google Calendar", "Event created successfully (check console for link).", parent=dialog)
                except Exception as e:
                    messagebox.showerror("Google Calendar Error", f"Could not create event: {e}", parent=dialog)

            self.populate_interaction_data()
            self.populate_dashboard()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).pack(pady=10)
        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)

    def setup_dashboard_tab(self):
        """Sets up the widgets for the dashboard tab."""
        # Main frame for the dashboard
        dashboard_frame = ttk.Frame(self.dashboard_tab, padding="10")
        dashboard_frame.pack(fill="both", expand=True)

        # Overdue Reminders
        overdue_frame = ttk.LabelFrame(dashboard_frame, text="Overdue Reminders (!)", padding="10")
        overdue_frame.pack(fill="x", pady=5)
        self.overdue_tree = self._create_treeview(overdue_frame, ["Date", "Contact", "Message"])
        self.overdue_tree.column("Message", width=400)

        # Upcoming Reminders
        upcoming_frame = ttk.LabelFrame(dashboard_frame, text="Reminders (Next 7 Days)", padding="10")
        upcoming_frame.pack(fill="x", pady=5)
        self.upcoming_tree = self._create_treeview(upcoming_frame, ["Date", "Contact", "Message"])
        self.upcoming_tree.column("Message", width=400)


        # Contact Suggestions
        suggestions_frame = ttk.LabelFrame(dashboard_frame, text="Suggestions (not contacted recently)", padding="10")
        suggestions_frame.pack(fill="x", pady=5)
        self.suggestions_tree = self._create_treeview(suggestions_frame, ["Name", "Last Contacted"])

    def setup_contacts_tab(self):
        """Sets up the widgets for the contact management tab."""
        contacts_frame = ttk.Frame(self.contacts_tab, padding="10")
        contacts_frame.pack(fill="both", expand=True)

        # Toolbar
        toolbar = ttk.Frame(contacts_frame)
        toolbar.pack(fill="x", pady=5)

        ttk.Button(toolbar, text="Add Contact", command=self.add_contact_window).pack(side="left", padx=5)
        ttk.Button(toolbar, text="View Details", command=self.view_contact_window).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Edit Contact", command=self.edit_contact_window).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Delete Contact", command=self.delete_contact).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Manage Tags", command=self.manage_tags_window).pack(side="left", padx=5)

        # Search functionality
        ttk.Label(toolbar, text="Search:").pack(side="left", padx=(20, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=25)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<KeyRelease>", self.search_contacts)

        ttk.Button(toolbar, text="Advanced Search", command=self.advanced_search_window).pack(side="left", padx=5)

        # Tag filter
        ttk.Label(toolbar, text="Filter by Tag:").pack(side="left", padx=(20, 5))
        self.tag_filter_combo = ttk.Combobox(toolbar, state="readonly", width=20)
        self.tag_filter_combo.pack(side="left", padx=5)
        self.tag_filter_combo.bind("<<ComboboxSelected>>", self.filter_by_tag)

        ttk.Button(toolbar, text="Refresh List", command=lambda: self.populate_contacts_tree(clear_filters=True)).pack(side="right", padx=5)

        # Contacts List
        tree_frame = ttk.Frame(contacts_frame)
        tree_frame.pack(fill="both", expand=True)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        columns = ["ID", "First Name", "Last Name", "Email", "Birthday", "Tags", "Time Known", "Last Seen"]
        self.contacts_tree = self._create_treeview(tree_frame, columns)
        self.contacts_tree.column("ID", width=40, anchor="center")
        self.contacts_tree.column("Time Known", anchor="e")
        self.contacts_tree.column("Last Seen", anchor="e")
        self.contacts_tree.grid(row=0, column=0, sticky='nsew')


        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.contacts_tree.yview)
        self.contacts_tree.configure(yscroll=v_scrollbar.set)
        v_scrollbar.grid(row=0, column=1, sticky='ns')

        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.contacts_tree.xview)
        self.contacts_tree.configure(xscroll=h_scrollbar.set)
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        self.contacts_tree.bind("<Double-1>", self.on_contact_double_click)

        self._refresh_tags_combo()

    def on_contact_double_click(self, event):
        """Handler for double-clicking a contact in the tree."""
        region = self.contacts_tree.identify_region(event.x, event.y)
        if region == "cell":
            self.view_contact_window()

    def _refresh_tags_combo(self):
        """Refreshes the list of tags in the filter combobox."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM tags ORDER BY name")
            tags = [row['name'] for row in cursor.fetchall()]
        self.tag_filter_combo['values'] = ["All Contacts"] + tags

    def filter_by_tag(self, event=None):
        """Filters the contact list based on the selected tag."""
        tag_name = self.tag_filter_combo.get()
        if tag_name == "All Contacts":
            self.populate_contacts_tree()
        else:
            self.populate_contacts_tree(tag_filter=tag_name)

    def search_contacts(self, event=None):
        """Filters the contacts treeview based on the search query."""
        search_query = self.search_var.get().strip()
        self.populate_contacts_tree(search_query=search_query)

    def populate_contacts_tree(self, search_query=None, tag_filter=None, clear_filters=False):
        """Fetches contact data and populates the contacts treeview, with optional filters."""
        if clear_filters:
            self.search_var.set("")
            self.tag_filter_combo.set("All Contacts")
            search_query = None
            tag_filter = None

        for i in self.contacts_tree.get_children():
            self.contacts_tree.delete(i)

        # Base query with all columns and tag aggregation
        query = """
            SELECT
                c.id, c.first_name, c.last_name, c.email, c.birthday, c.date_met, c.last_contacted_at,
                GROUP_CONCAT(t.name) AS tags
            FROM contacts c
            LEFT JOIN contact_tags ct ON c.id = ct.contact_id
            LEFT JOIN tags t ON ct.tag_id = t.id
        """
        params = []
        where_clauses = []

        if tag_filter:
            # This is tricky with GROUP BY. We filter by contacts that HAVE the tag.
            # We can't just add a WHERE clause here easily.
            # A subquery is a clean way to handle this.
            where_clauses.append("c.id IN (SELECT contact_id FROM contact_tags JOIN tags ON tags.id = contact_tags.tag_id WHERE tags.name = ?)")
            params.append(tag_filter)

        if search_query:
            where_clauses.append("(c.first_name LIKE ? OR c.last_name LIKE ? OR c.email LIKE ?)")
            params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " GROUP BY c.id ORDER BY c.first_name, c.last_name"

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            all_contacts = cursor.fetchall()

        today = datetime.date.today()
        for contact in all_contacts:
            # Calculate time known
            time_known_str = "N/A"
            if contact['date_met']:
                try:
                    # The database connection already converts this to a datetime object.
                    date_met_obj = contact['date_met'].date()
                    delta = today - date_met_obj
                    time_known_str = f"{delta.days} days"
                except (ValueError, TypeError, AttributeError):
                    # AttributeError can happen if date_met is not a datetime object
                    pass # Keep as N/A if format is wrong

            # Calculate time since last seen
            last_seen_str = "N/A"
            if contact['last_contacted_at']:
                try:
                    # The database connection already converts this to a datetime object.
                    last_contacted_obj = contact['last_contacted_at'].date()
                    delta = today - last_contacted_obj
                    last_seen_str = f"{delta.days} days ago"
                except (ValueError, TypeError, AttributeError):
                    # AttributeError can happen if last_contacted_at is not a datetime object
                    pass # Keep as N/A

            values = (
                contact['id'],
                contact['first_name'],
                contact['last_name'] or '',
                contact['email'] or '',
                contact['birthday'] or '',
                contact['tags'] or '',
                time_known_str,
                last_seen_str
            )
            self.contacts_tree.insert("", "end", values=values)

        # Refresh dashboard as well since contact changes can affect it
        if not search_query and not tag_filter: # Avoid refreshing during filters
             self.populate_dashboard()
             self._refresh_contact_combos()

    def add_contact_window(self):
        """Opens a Toplevel window to add a new contact."""
        self._open_contact_dialog("Add New Contact")

    def edit_contact_window(self):
        """Opens a Toplevel window to edit the selected contact."""
        selected_item = self.contacts_tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a contact to edit.")
            return

        contact_id = self.contacts_tree.item(selected_item)['values'][0]

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
            contact_data = cursor.fetchone()

        if contact_data:
            self._open_contact_dialog("Edit Contact", contact_data)
        else:
            messagebox.showerror("Error", f"Could not find contact with ID {contact_id}.")

    def delete_contact(self):
        """Deletes the selected contact."""
        selected_item = self.contacts_tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a contact to delete.")
            return

        values = self.contacts_tree.item(selected_item)['values']
        contact_id = values[0]
        contact_name = f"{values[1]} {values[2] or ''}".strip()

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {contact_name}?"):
            # We need to find the full name to pass to the delete function, which is a bit weird.
            # Let's just delete by ID. I'll modify the delete_contact function later if needed.
            # For now, let's just do it directly.
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
                conn.commit()

            messagebox.showinfo("Success", f"Contact {contact_name} deleted.")
            self.populate_contacts_tree()


    def _open_contact_dialog(self, title, contact_data=None):
        """Helper to open a dialog for adding/editing contacts."""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("400x400")

        fields = ["First Name", "Last Name", "Email", "Birthday (YYYY-MM-DD)", "Date Met (YYYY-MM-DD)", "How Met", "Favorite Color"]
        entries = {}

        for i, field in enumerate(fields):
            ttk.Label(dialog, text=field).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ttk.Entry(dialog, width=40)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[field] = entry

        if contact_data:
            entries["First Name"].insert(0, contact_data['first_name'] or "")
            entries["Last Name"].insert(0, contact_data['last_name'] or "")
            entries["Email"].insert(0, contact_data['email'] or "")
            entries["Birthday (YYYY-MM-DD)"].insert(0, contact_data['birthday'] or "")
            entries["Date Met (YYYY-MM-DD)"].insert(0, contact_data['date_met'] or "")
            entries["How Met"].insert(0, contact_data['how_met'] or "")
            entries["Favorite Color"].insert(0, contact_data['favorite_color'] or "")

        def save_contact():
            first_name = entries["First Name"].get().strip()
            if not first_name:
                messagebox.showerror("Error", "First name is required.")
                return

            # Prepare data for db functions
            data = {
                "first_name": first_name,
                "last_name": entries["Last Name"].get().strip() or None,
                "email": entries["Email"].get().strip() or None,
                "birthday": entries["Birthday (YYYY-MM-DD)"].get().strip() or None,
                "date_met": entries["Date Met (YYYY-MM-DD)"].get().strip() or None,
                "how_met": entries["How Met"].get().strip() or None,
                "favorite_color": entries["Favorite Color"].get().strip() or None,
            }

            try:
                if contact_data: # Editing existing contact
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE contacts SET
                                first_name = ?, last_name = ?, email = ?, birthday = ?,
                                date_met = ?, how_met = ?, favorite_color = ?
                            WHERE id = ?
                        """, (data['first_name'], data['last_name'], data['email'], data['birthday'],
                              data['date_met'], data['how_met'], data['favorite_color'], contact_data['id']))
                        conn.commit()
                else: # Adding new contact
                    contacts.add_contact(**data)

                self.populate_contacts_tree()
                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Database Error", f"An error occurred: {e}")

        save_button = ttk.Button(dialog, text="Save", command=save_contact)
        save_button.grid(row=len(fields), column=0, columnspan=2, pady=10)

    def view_contact_window(self):
        """Opens a Toplevel window to display a comprehensive view of the selected contact."""
        selected_item = self.contacts_tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a contact to view.")
            return
        contact_id = self.contacts_tree.item(selected_item)['values'][0]
        self._view_contact_details_by_id(contact_id)

    def _view_contact_details_by_id(self, contact_id):
        """Helper function to open the details view for a given contact ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,))
            contact = cursor.fetchone()
            if not contact:
                messagebox.showerror("Error", f"Could not retrieve contact with ID {contact_id}.")
                return

            # Fetch all related data
            cursor.execute("SELECT phone_number, phone_type FROM phones WHERE contact_id = ?", (contact_id,))
            phones = cursor.fetchall()
            cursor.execute("SELECT name FROM pets WHERE contact_id = ?", (contact_id,))
            pets = cursor.fetchall()
            relationships = contacts.get_relationships_for_contact(contact_id)
            cursor.execute("SELECT note_text, created_at FROM notes WHERE contact_id = ? ORDER BY created_at DESC", (contact_id,))
            notes = cursor.fetchall()
            cursor.execute("SELECT message, reminder_date FROM reminders WHERE contact_id = ? ORDER BY reminder_date ASC", (contact_id,))
            reminders = cursor.fetchall()
            tags = self._get_tags_for_contact(contact_id)

        # Create the window
        win = tk.Toplevel(self)
        win.title(f"Details for {contact['first_name']} {contact['last_name'] or ''}")
        win.geometry("700x800")

        # Main details frame
        details_frame = ttk.LabelFrame(win, text="Contact Details", padding="10")
        details_frame.pack(fill="x", padx=10, pady=5)

        date_met_str = contact['date_met'].strftime('%Y-%m-%d') if isinstance(contact['date_met'], datetime.datetime) else (contact['date_met'] or 'N/A')
        last_contacted_str = contact['last_contacted_at'].strftime('%Y-%m-%d') if contact['last_contacted_at'] else 'Never'

        details_text = (
            f"Email: {contact['email'] or 'N/A'}\n"
            f"Birthday: {contact['birthday'] or 'N/A'}\n"
            f"Date Met: {date_met_str}\n"
            f"How Met: {contact['how_met'] or 'N/A'}\n"
            f"Favorite Color: {contact['favorite_color'] or 'N/A'}\n"
            f"Last Contacted: {last_contacted_str}\n"
            f"Tags: {', '.join(tags) if tags else 'None'}"
        )
        ttk.Label(details_frame, text=details_text, justify=tk.LEFT).pack(anchor="w")

        # Notebook for related data
        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Helper to create a tab and treeview
        def create_tab_with_tree(tab_name, columns, data):
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=tab_name)
            if data:
                tree = self._create_treeview(tab, columns)
                for row in data:
                    tree.insert("", "end", values=[row[col] for col in columns])
            else:
                ttk.Label(tab, text=f"No {tab_name.lower()} found.").pack(pady=20)

        if phones: create_tab_with_tree("Phones", ['phone_number', 'phone_type'], phones)
        if pets: create_tab_with_tree("Pets", ['name'], pets)
        if relationships:
            rel_data = [{'contact': f"{r['first_name']} {r['last_name'] or ''}", 'type': r['relationship_type']} for r in relationships]
            create_tab_with_tree("Relationships", ['contact', 'type'], rel_data)
        if notes:
            formatted_notes = [{'created_at': n['created_at'].strftime('%Y-%m-%d %H:%M'), 'note_text': n['note_text']} for n in notes]
            create_tab_with_tree("Notes", ['created_at', 'note_text'], formatted_notes)
        if reminders: create_tab_with_tree("Reminders", ['reminder_date', 'message'], reminders)

        win.transient(self); win.grab_set(); self.wait_window(win)

    def advanced_search_window(self):
        """Opens a dialog for advanced, field-specific contact searching."""
        dialog = tk.Toplevel(self)
        dialog.title("Advanced Search")

        searchable_fields = ["first_name", "last_name", "email", "birthday", "date_met", "how_met", "favorite_color"]
        entries = {}

        for i, field in enumerate(searchable_fields):
            ttk.Label(dialog, text=field.replace('_', ' ').title()).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ttk.Entry(dialog, width=40)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries[field] = entry

        def perform_search():
            criteria = {field: entry.get().strip() for field, entry in entries.items() if entry.get().strip()}

            if not criteria:
                messagebox.showwarning("No Input", "Please enter at least one search criterion.")
                return

            base_query = "SELECT id, first_name, last_name, email FROM contacts"
            where_clauses = [f"{key} LIKE ?" for key in criteria.keys()]
            params = [f"%{value}%" for value in criteria.values()]

            query = f"{base_query} WHERE {' AND '.join(where_clauses)} ORDER BY first_name, last_name"

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()

            dialog.destroy()
            self._display_search_results(results)

        ttk.Button(dialog, text="Search", command=perform_search).grid(row=len(searchable_fields), column=0, columnspan=2, pady=10)
        dialog.transient(self); dialog.grab_set(); self.wait_window(dialog)

    def _display_search_results(self, results):
        """Displays search results in a new Toplevel window."""
        results_window = tk.Toplevel(self)
        results_window.title("Search Results")
        results_window.geometry("600x400")

        if not results:
            ttk.Label(results_window, text="No contacts found matching your criteria.").pack(pady=20)
            return

        tree_frame = ttk.Frame(results_window)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ["ID", "First Name", "Last Name", "Email"]
        tree = self._create_treeview(tree_frame, columns)
        tree.column("ID", width=50, anchor="center")

        for contact in results:
            tree.insert("", "end", values=(contact['id'], contact['first_name'], contact['last_name'], contact['email']))

        results_window.transient(self); results_window.grab_set(); self.wait_window(results_window)

    def manage_tags_window(self):
        """Opens a Toplevel window to manage tags for the selected contact."""
        selected_item = self.contacts_tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a contact to manage their tags.")
            return

        values = self.contacts_tree.item(selected_item)['values']
        contact_id = values[0]
        contact_name = f"{values[1]} {values[2] or ''}".strip()

        dialog = tk.Toplevel(self)
        dialog.title(f"Manage Tags for {contact_name}")
        dialog.geometry("400x300")

        # Frame for current tags
        tags_frame = ttk.LabelFrame(dialog, text="Current Tags", padding="10")
        tags_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tags_listbox = tk.Listbox(tags_frame)
        tags_listbox.pack(fill="both", expand=True)

        def populate_tags_list():
            tags_listbox.delete(0, tk.END)
            current_tags = self._get_tags_for_contact(contact_id)
            for tag in current_tags:
                tags_listbox.insert(tk.END, tag)

        # Frame for adding/removing tags
        actions_frame = ttk.Frame(dialog, padding="10")
        actions_frame.pack(fill="x")

        tag_entry_var = tk.StringVar()
        tag_entry = ttk.Entry(actions_frame, textvariable=tag_entry_var, width=30)
        tag_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))

        def add_tag():
            tag_name = tag_entry_var.get().strip()
            if tag_name:
                self._add_tag_to_contact_by_id(contact_id, tag_name)
                populate_tags_list()
                tag_entry_var.set("") # Clear entry

        def remove_tag():
            selected_indices = tags_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select a tag to remove.")
                return
            tag_name = tags_listbox.get(selected_indices[0])
            self._remove_tag_from_contact_by_id(contact_id, tag_name)
            populate_tags_list()

        dialog.protocol("WM_DELETE_WINDOW", lambda: (self._refresh_tags_combo(), dialog.destroy()))
        add_button = ttk.Button(actions_frame, text="Add Tag", command=add_tag)
        add_button.pack(side="left", padx=5)
        remove_button = ttk.Button(actions_frame, text="Remove Selected Tag", command=remove_tag)
        remove_button.pack(side="left")

        populate_tags_list()
        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)

    def _get_tags_for_contact(self, contact_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN contact_tags ct ON t.id = ct.tag_id
                WHERE ct.contact_id = ?
            """, (contact_id,))
            return [row['name'] for row in cursor.fetchall()]

    def _add_tag_to_contact_by_id(self, contact_id, tag_name):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                tag = cursor.fetchone()
                if not tag:
                    cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
                    tag_id = cursor.lastrowid
                else:
                    tag_id = tag['id']
                cursor.execute("INSERT INTO contact_tags (contact_id, tag_id) VALUES (?, ?)", (contact_id, tag_id))
                conn.commit()
        except sqlite3.IntegrityError:
            pass # Tag already exists for this contact, ignore.

    def _remove_tag_from_contact_by_id(self, contact_id, tag_name):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            tag = cursor.fetchone()
            if tag:
                cursor.execute("DELETE FROM contact_tags WHERE contact_id = ? AND tag_id = ?", (contact_id, tag['id']))
                conn.commit()

    def _create_treeview(self, parent, columns):
        """Helper function to create a treeview."""
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="w")
        tree.pack(fill="both", expand=True)
        return tree

    def populate_dashboard(self):
        """Fetches data and populates the dashboard widgets."""
        today = datetime.date.today()
        next_week = today + datetime.timedelta(days=7)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Fetch Overdue reminders
            cursor.execute("""
                SELECT r.reminder_date, r.message, c.first_name, c.last_name
                FROM reminders r JOIN contacts c ON r.contact_id = c.id
                WHERE r.reminder_date < ? ORDER BY r.reminder_date ASC
            """, (today.strftime('%Y-%m-%d'),))
            overdue_reminders = cursor.fetchall()

            # Fetch Upcoming reminders
            cursor.execute("""
                SELECT r.reminder_date, r.message, c.first_name, c.last_name
                FROM reminders r JOIN contacts c ON r.contact_id = c.id
                WHERE r.reminder_date >= ? AND r.reminder_date <= ?
                ORDER BY r.reminder_date ASC
            """, (today.strftime('%Y-%m-%d'), next_week.strftime('%Y-%m-%d')))
            upcoming_reminders = cursor.fetchall()

            # Fetch Contact Suggestions
            threshold_date = datetime.datetime.now() - datetime.timedelta(days=30)
            cursor.execute("""
                SELECT first_name, last_name, last_contacted_at
                FROM contacts
                WHERE last_contacted_at < ?
                ORDER BY last_contacted_at ASC
            """, (threshold_date,))
            suggested_contacts = cursor.fetchall()

        # Clear existing data
        for i in self.overdue_tree.get_children(): self.overdue_tree.delete(i)
        for i in self.upcoming_tree.get_children(): self.upcoming_tree.delete(i)
        for i in self.suggestions_tree.get_children(): self.suggestions_tree.delete(i)

        # Populate overdue reminders
        for r in overdue_reminders:
            name = f"{r['first_name']} {r['last_name'] or ''}"
            self.overdue_tree.insert("", "end", values=(r['reminder_date'], name, r['message']))

        # Populate upcoming reminders
        for r in upcoming_reminders:
            name = f"{r['first_name']} {r['last_name'] or ''}"
            self.upcoming_tree.insert("", "end", values=(r['reminder_date'], name, r['message']))

        # Populate suggestions
        for c in suggested_contacts:
            name = f"{c['first_name']} {c['last_name'] or ''}"
            last_contacted_str = c['last_contacted_at'].strftime('%Y-%m-%d')
            self.suggestions_tree.insert("", "end", values=(name, last_contacted_str))

    def setup_graph_tab(self):
        """Sets up the widgets for the relationship graph tab."""
        graph_frame = ttk.Frame(self.graph_tab, padding="10")
        graph_frame.pack(fill="both", expand=True)

        self.G = nx.Graph()
        self.graph_figure = Figure(figsize=(8, 6), dpi=100)
        self.graph_ax = self.graph_figure.add_subplot(111)
        self.graph_pos = None # To store node positions

        self.canvas = FigureCanvasTkAgg(self.graph_figure, master=graph_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect('button_press_event', self.on_graph_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_graph_motion)
        self.canvas.mpl_connect('button_release_event', self.on_graph_release)


    def populate_relationship_graph(self):
        """Fetches all contacts and relationships and draws the graph."""
        self.G.clear()
        self.graph_ax.clear()

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Fetch all contacts (nodes)
            cursor.execute("SELECT id, first_name, last_name FROM contacts")
            db_contacts = cursor.fetchall()
            # Fetch all relationships (edges)
            cursor.execute("SELECT contact1_id, contact2_id, relationship_type FROM relationships")
            db_relationships = cursor.fetchall()

        if not db_contacts:
            self.graph_ax.text(0.5, 0.5, "No contacts to display.", ha='center', va='center')
            self.canvas.draw()
            return

        # Add nodes to the graph
        for contact in db_contacts:
            self.G.add_node(contact['id'], name=f"{contact['first_name']} {contact['last_name'] or ''}".strip())

        # Add edges to the graph
        for rel in db_relationships:
            # Ensure both nodes exist in the graph before adding an edge
            if rel['contact1_id'] in self.G and rel['contact2_id'] in self.G:
                self.G.add_edge(rel['contact1_id'], rel['contact2_id'], label=rel['relationship_type'])

        # Calculate layout only if it hasn't been calculated before
        if self.graph_pos is None:
            self.graph_pos = nx.spring_layout(self.G, k=0.8, iterations=50)
        self._redraw_graph()


    def _redraw_graph(self):
        """Clears and redraws the graph."""
        self.graph_ax.clear()
        labels = nx.get_node_attributes(self.G, 'name')
        edge_labels = nx.get_edge_attributes(self.G, 'label')

        nx.draw(self.G, self.graph_pos, ax=self.graph_ax, with_labels=True, labels=labels,
                node_color='skyblue', node_size=2000, font_size=8,
                width=1.5, edge_color='gray')
        nx.draw_networkx_edge_labels(self.G, self.graph_pos, edge_labels=edge_labels, ax=self.graph_ax, font_size=7)

        self.graph_ax.set_title("Contact Relationships")
        self.graph_figure.tight_layout()
        self.canvas.draw()

    def _get_node_at_event(self, event):
        """Finds the node at the event's coordinates, if any."""
        if self.graph_pos is None or event.xdata is None or event.ydata is None:
            return None

        for node_id, (x, y) in self.graph_pos.items():
            dist = ((event.xdata - x)**2 + (event.ydata - y)**2)**0.5
            if dist < 0.1: # This threshold might need adjustment
                return node_id
        return None

    def on_graph_click(self, event):
        """Handler for clicking on the relationship graph."""
        if event.inaxes != self.graph_ax or self.graph_pos is None:
            return

        node_id = self._get_node_at_event(event)
        if not node_id:
            return

        if event.dblclick:
            self._view_contact_details_by_id(node_id)
        else:
            self._dragged_node = node_id

    def on_graph_motion(self, event):
        """Handler for mouse motion on the graph."""
        if self._dragged_node is None or event.inaxes != self.graph_ax or event.xdata is None:
            return
        self.graph_pos[self._dragged_node] = (event.xdata, event.ydata)
        self._redraw_graph()

    def on_graph_release(self, event):
        """Handler for releasing the mouse button on the graph."""
        self._dragged_node = None


def main():
    """Main function to run the GUI application."""
    from .database import create_tables
    create_tables()
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
