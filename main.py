import sqlite3
import json
import sys
# from functools import cache
import pandas as pd
import tkinter as tk
import os
import re
import threading

from tkinter import ttk
# from customtkinter import CTk
#from tkinter import PhotoImage
from PIL import Image #,ImageTk
# import time
import customtkinter as ctk
from tkinter import filedialog
import webbrowser
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import Calendar
from datetime import datetime

if getattr(sys, 'frozen', False):
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
img = os.path.join(base_dir, "assets", "img")
dbsrc = os.path.join(base_dir, ".db")
__version__ = "1.0.0"
xlsrc = os.path.join(base_dir, "Excel")

if not os.path.exists(dbsrc): os.makedirs(dbsrc)
if not os.path.exists(xlsrc): os.makedirs(xlsrc)

mconn=sqlite3.connect(os.path.join(dbsrc, "main.db"))
mcursor = mconn.cursor()
mcursor.execute(
    """
    CREATE TABLE IF NOT EXISTS main (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    database_names TEXT NOT NULL,
    table_names TEXT NOT NULL,
    fields TEXT NOT NULL,
    data_types TEXT NOT NULL
    );
    """
    )
    
class CTkDatePicker(ctk.CTkEntry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Button-1>", self.open_calendar)
        self.configure(state="readonly") # Prevent typing, force picker

    def open_calendar(self, event=None):
        if self.cget("state") == "disabled": return
        
        # Check if already open
        if hasattr(self, 'top') and self.top.winfo_exists():
            self.top.lift()
            return
            
        self.top = ctk.CTkToplevel(self)
        self.top.geometry("300x290")
        self.top.title("Select Date")
        self.top.attributes("-topmost", True)
        self.top.grab_set() # Modal

        cal = Calendar(self.top, selectmode='day', date_pattern='yyyy-mm-dd')
        cal.pack(pady=10, padx=10)

        def set_date(event=None):
            selected = cal.get_date()
            self.configure(state="normal")
            self.delete(0, "end")
            self.insert(0, selected)
            self.configure(state="readonly")
            self.top.destroy()

        ctk.CTkButton(self.top, text="Select", command=set_date).pack(pady=10)
        self.top.bind('<Return>', set_date) # Bind Enter key

def validate_identifier(name, context_name="Identifier"):
    """
    Validates a user-provided identifier (Database, Table, Field name).
    Rules:
    1. Must not be empty.
    2. Must start with a letter.
    3. Must contain only alphanumeric characters and underscores.
    4. Must not be a reserved keyword (e.g., 'id', though 'id' handling might be specific).
    
    Returns: (is_valid, error_message)
    """
    if not name:
        return False, f"{context_name} cannot be empty."
    
    if not name[0].isalpha():
        return False, f"{context_name} '{name}' must start with a letter (e.g., 'Name', 'data_1')."
        
    # Check for valid characters (Alphanumeric + Underscore)
    # isidentifier() is a good check but allows some non-ascii. 
    # User specifically asked for "no special chars like ?".
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
        return False, f"{context_name} '{name}' contains invalid characters (Only alphanumeric and underscores allowed)."
        
    return True, ""

def validate_security_input(val, label):
    """
    Validates input value for security risks (SQL Injection, forbidden chars).
    Returns: (is_valid, error_message)
    """
    if val and isinstance(val, str):
        # 1. Block '?'
        if "?" in val:
            return False, f"Field '{label}' contains invalid character '?'."
        
        # 2. Block Common SQL Keywords
        # Regex to find whole words, case-insensitive
        sql_keywords = [
            "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "EXEC", "UNION",
            "CHAR", "NCHAR", "VARCHAR", "NVARCHAR", "BEGIN", "CAST", "CREATE", "CURSOR", "DECLARE", 
            "FETCH", "KILL", "OPEN", "SYS", "SYSOBJECTS", "SYSCOLUMNS", "TABLE"
        ]
        
        # Check for SQL comments
        if "--" in val or "/*" in val or "*/" in val:
             return False, f"Field '{label}' contains SQL comment characters."
        
        if ";" in val:
             return False, f"Field '{label}' contains invalid character ';'."

        # Check keywords
        val_upper = val.upper()
        for kw in sql_keywords:
            # Use regex to match whole word only
            if re.search(r'\b' + re.escape(kw) + r'\b', val_upper):
                return False, f"Field '{label}' contains forbidden SQL keyword: '{kw}'."

    return True, ""

def migrate_db_schema():
    """
    Ensures the 'main' table has all necessary columns.
    Adds 'field_configs' if it doesn't exist.
    """
    try:
        # Check if column exists
        mcursor.execute("PRAGMA table_info(main)")
        columns = [info[1] for info in mcursor.fetchall()]
        
        if 'field_configs' not in columns:
            # print("Migrating database: Adding 'field_configs' column...")
            mcursor.execute("ALTER TABLE main ADD COLUMN field_configs TEXT")
            mconn.commit()
            # print("Migration successful.")
            
        # Check for created_at and updated_at
        if 'created_at' not in columns:
            # print("Migrating database: Adding 'created_at' column...")
            # SQLite limitation: Cannot ADD COLUMN with non-constant default like CURRENT_TIMESTAMP in some versions
            mcursor.execute("ALTER TABLE main ADD COLUMN created_at TIMESTAMP") 
            mcursor.execute("UPDATE main SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            mconn.commit()
            # print("Migration: created_at added.")

        if 'updated_at' not in columns:
            # print("Migrating database: Adding 'updated_at' column...")
            mcursor.execute("ALTER TABLE main ADD COLUMN updated_at TIMESTAMP")
            mcursor.execute("UPDATE main SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
            mconn.commit()
            # print("Migration: updated_at added.")
            
    except Exception as e:
        # print(f"Migration error: {e}")
        pass

def fetch_all_data():
    migrate_db_schema() # Ensure schema is up to date
    
    # Cleanup duplicates: Keep the one with Min ID
    try:
        mcursor.execute('''
            DELETE FROM main
            WHERE ID NOT IN (
                SELECT MIN(ID)
                FROM main
                GROUP BY database_names, table_names
            )
        ''')
        mconn.commit()
    except Exception as e:
        # print(f"Cleanup error: {e}")
        pass

    # Fetch with new columns
    try:
        mcursor.execute('SELECT ID, database_names, table_names, fields, data_types, field_configs, created_at, updated_at FROM main')
    except sqlite3.OperationalError:
        # Fallback if migration failed or legacy connection? Should be handled by migrate_db_schema
        mcursor.execute('SELECT ID, database_names, table_names, fields, data_types FROM main')
        
    rows = mcursor.fetchall()
    main_data = {}
    for row in rows:
        if len(row) == 8:
             ID, database_names, table_names, fields_json, data_types_json, field_configs_json, created_at, updated_at = row
        elif len(row) == 7: # Partial migration state?
             ID, database_names, table_names, fields_json, data_types_json, field_configs_json, created_at = row
             updated_at = created_at
        elif len(row) == 6:
             ID, database_names, table_names, fields_json, data_types_json, field_configs_json = row
             created_at = None
             updated_at = None
        else:
             ID, database_names, table_names, fields_json, data_types_json = row
             field_configs_json = None
             created_at = None
             updated_at = None
             
        fields = json.loads(fields_json)
        data_types = json.loads(data_types_json)
        
        field_configs = {}
        if field_configs_json:
            try:
                field_configs = json.loads(field_configs_json)
            except:
                pass
                
        main_data[ID] = {
            'database_names': database_names,
            'table_names': table_names,
            'fields': fields,
            'data_types': data_types,
            'fields': fields,
            'data_types': data_types,
            'field_configs': field_configs,
            'created_at': created_at,
            'updated_at': updated_at
        }
    return main_data    
main_data=fetch_all_data()
# print(main_data)

def get_db_connection(db_name):
    """Establishes a connection to the specified SQLite database."""
    db_path = os.path.join(dbsrc, f"{db_name}.db")
    return sqlite3.connect(db_path)

class SchemaEditor(ctk.CTkToplevel):
    def __init__(self, parent, form_id, refresh_callback):
        super().__init__(parent)
        self.form_id = form_id
        self.refresh_callback = refresh_callback
        self.title("Schema Editor")

        self.geometry("600x700")
        self.attributes("-topmost", True)
        self.transient(parent)
        
        self.current_data = main_data[form_id]
        self.db_name = self.current_data["database_names"]
        self.table_name = self.current_data["table_names"]
        self.fields = self.current_data["fields"]
        self.data_types = self.current_data["data_types"]
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self.header = ctk.CTkLabel(self, text=f"Edit Schema: {self.table_name}", font=("Arial", 20, "bold"))
        self.header.grid(row=0, column=0, pady=20)
        
        # Fields List Area
        self.fields_frame = ctk.CTkScrollableFrame(self, label_text="Current Fields")
        self.fields_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.fields_frame.grid_columnconfigure(0, weight=1)
        
        self.refresh_fields_list()
        
        # Add Field Area
        self.add_frame = ctk.CTkFrame(self)
        self.add_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(self.add_frame, text="Add New Field").grid(row=0, column=0, columnspan=3, pady=5)
        
        self.new_field_name = ctk.CTkEntry(self.add_frame, placeholder_text="Field Name")
        self.new_field_name.grid(row=1, column=0, padx=5, pady=5)
        
        self.new_field_type = ctk.CTkComboBox(self.add_frame, values=["TEXT", "NUMERIC", "INTEGER", "REAL"])
        self.new_field_type.grid(row=1, column=1, padx=5, pady=5)
        self.new_field_type.set("TEXT")
        
        ctk.CTkButton(self.add_frame, text="➕ Add", command=self.add_field).grid(row=1, column=2, padx=5, pady=5)
        
    def refresh_fields_list(self):
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
            
        for i, (f_name, f_type) in enumerate(zip(self.fields, self.data_types)):
            row_frame = ctk.CTkFrame(self.fields_frame)
            row_frame.grid(row=i, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(row_frame, text=f"{f_name} ({f_type})").grid(row=0, column=0, padx=10, sticky="w")
            
            ctk.CTkButton(row_frame, text="✏️", width=40, fg_color="orange", 
                          command=lambda f=f_name: self.rename_field_dialog(f)).grid(row=0, column=1, padx=5)
            
            ctk.CTkButton(row_frame, text="🗑️", width=40, fg_color="red", 
                          command=lambda f=f_name: self.delete_field(f)).grid(row=0, column=2, padx=5)

    def update_metadata(self):
        # Update main.db
        json_fields = json.dumps(self.fields)
        json_dtypes = json.dumps(self.data_types)
        mcursor.execute("UPDATE main SET fields=?, data_types=?, updated_at=CURRENT_TIMESTAMP WHERE ID=?", 
                        (json_fields, json_dtypes, self.form_id))
        mconn.commit()
        
        # Update global cache
        global main_data
        main_data = fetch_all_data()
        
        self.refresh_fields_list()
        self.refresh_callback()

    def add_field(self):
        name = self.new_field_name.get()
        dtype = self.new_field_type.get()
        
        is_valid, error_msg = validate_identifier(name, "Field name")
        if not is_valid:
            from tkinter import messagebox
            messagebox.showerror("Validation Error", error_msg)
            return

        if name in self.fields:
            from tkinter import messagebox
            messagebox.showerror("Validation Error", f"Field '{name}' already exists.")
            return
            
        try:
            with get_db_connection(self.db_name) as conn:
                conn.execute(f"ALTER TABLE {self.table_name} ADD COLUMN {name} {dtype}")
                conn.commit()
                
            self.fields.append(name)
            self.data_types.append(dtype)
            self.update_metadata()
            self.new_field_name.delete(0, tk.END)
            # print(f"Added field {name}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Error adding field: {e}")
            # print(f"Error adding field: {e}")

    def delete_field(self, field_name):
        from tkinter import messagebox
        if field_name == 'id':
            messagebox.showerror("Error", "Cannot delete primary key 'id'")
            return
            
        if messagebox.askyesno("Confirm Delete", f"Delete field '{field_name}'? ALL DATA in this column will be lost!"):
            try:
                with get_db_connection(self.db_name) as conn:
                    conn.execute(f"ALTER TABLE {self.table_name} DROP COLUMN {field_name}")
                    conn.commit()
                    
                idx = self.fields.index(field_name)
                self.fields.pop(idx)
                self.data_types.pop(idx)
                self.update_metadata()
                # print(f"Deleted field {field_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Delete failed: {e}")

    def rename_field_dialog(self, old_name):
        if old_name == 'id': return
        
        # Create custom modal dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Rename Field")
        dialog.geometry("300x150")
        dialog.attributes("-topmost", True) # Force on top
        dialog.transient(self) # Keep on top of SchemaEditor
        dialog.grab_set() # Make modal
        
        # Center the dialog logic (optional, but good)
        
        ctk.CTkLabel(dialog, text=f"Rename '{old_name}' to:").pack(pady=(20, 5))
        
        entry = ctk.CTkEntry(dialog)
        entry.pack(pady=5, padx=20, fill="x")
        entry.insert(0, old_name)
        entry.focus_set()
        
        def on_rename():
            new_name = entry.get()
            
            is_valid, error_msg = validate_identifier(new_name, "New field name")
            if not is_valid:
                from tkinter import messagebox
                messagebox.showerror("Validation Error", error_msg, parent=dialog)
                return
                
            if new_name in self.fields and new_name != old_name:
                from tkinter import messagebox
                messagebox.showerror("Error", "Field name already exists", parent=dialog)
                return
                
            if new_name == old_name:
                dialog.destroy()
                return

            try:
                with get_db_connection(self.db_name) as conn:
                    # RENAME COLUMN supported in newer SQLite
                    conn.execute(f"ALTER TABLE {self.table_name} RENAME COLUMN {old_name} TO {new_name}")
                    conn.commit()
                    
                idx = self.fields.index(old_name)
                self.fields[idx] = new_name
                self.update_metadata()
                # print(f"Renamed {old_name} to {new_name}")
                dialog.destroy()
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", f"Rename failed: {e}", parent=dialog)
                # print(f"Rename failed: {e}")

        ctk.CTkButton(dialog, text="Rename", command=on_rename).pack(pady=10)
        self.wait_window(dialog)

class Form_Window():
    def on_submit(self):
        
        global fields_value
        self.db_value = self.db_name.get()
        self.table_value = self.table_name.get()
        
        # Validate Database Name
        is_valid, error_msg = validate_identifier(self.db_value, "Database name")
        if not is_valid:
            from tkinter import messagebox
            messagebox.showerror("Validation Error", error_msg)
            return

        # Validate Table Name
        is_valid, error_msg = validate_identifier(self.table_value, "Table name")
        if not is_valid:
             from tkinter import messagebox
             messagebox.showerror("Validation Error", error_msg)
             return
        
        try:
            val = self.no_of_f.get()
            if not val:
                 self.fields_value = 0
            else:
                 self.fields_value = int(val)
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Error", "Number of fields must be an integer")
            return
            
        fields_value = self.fields_value
    
        if self.fields_value > 0:
            self.get_fields()
        else:
            from tkinter import messagebox
            messagebox.showerror("Error", "Number of fields must be > 0. Please enter at least 1 field.")

    def get_fields(self):
        """
        for changing DBFrame to fieldsFrame
        """
        self.DBFrame.pack_forget()
        self.fieldsFrame.pack(fill=tk.BOTH, expand=True)
        self.create_fields()
        
    def create_form(self):
        self.DBFrame.pack_forget()
        self.mainFrame.pack_forget()
        
        # Grid layout for DBFrame
        self.DBFrame.grid_columnconfigure(1, weight=1)
        
        title_l = ctk.CTkLabel(self.DBFrame, text="Create New Form", font=("Arial", 20, "bold"))
        title_l.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 20))
        
        db_l = ctk.CTkLabel(self.DBFrame, text="Database Name:")
        db_l.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        db_entry = ctk.CTkEntry(self.DBFrame, textvariable=self.db_name)
        db_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        tb_l = ctk.CTkLabel(self.DBFrame, text="Form Name:")
        tb_l.grid(row=2, column=0, padx=10, pady=10, sticky="e")
        table_entry = ctk.CTkEntry(self.DBFrame, textvariable=self.table_name)
        table_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        no_f_l = ctk.CTkLabel(self.DBFrame, text="Number of Fields:")
        no_f_l.grid(row=3, column=0, padx=10, pady=10, sticky="e")
        number_entry = ctk.CTkEntry(self.DBFrame, textvariable=self.no_of_f)
        number_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
        submit_button = ctk.CTkButton(self.DBFrame, text="Next", command=self.on_submit)
        submit_button.grid(row=4, column=1, padx=10, pady=20, sticky="e")

        self.DBFrame.pack(fill=tk.BOTH, expand=True)
        
    def start_main(self):
        self.fieldsFrame.pack_forget()
        self.mainFrame.pack(fill=tk.BOTH, expand=True)
        
    def submit_data(self):
        """
        Getting fields names and insert into MAIN table
        and also creating database and table accordingly
        """
        from tkinter import messagebox
        
        # Check for duplicates (Table in DB) - redundant check but safe
        mcursor.execute("SELECT 1 FROM main WHERE database_names=? AND table_names=?", (self.db_value, self.table_value))
        if mcursor.fetchone():
             messagebox.showerror("Error", f"Table '{self.table_value}' already exists in database '{self.db_value}'.")
             return

        _fields = []
        _dtypes = []
        _configs = {}
        
        # Validate Fields First
        seen_fields = set()
        
        for i in range(self.fields_value):
            entry_name = self.entry_fields[i].get()
            
            # Validate Field Name
            is_valid, error_msg = validate_identifier(entry_name, f"Field '{entry_name}' (row {i+1})")
            if not is_valid:
                messagebox.showerror("Validation Error", error_msg)
                return
            
            # Check for duplicates within the current form submission
            if entry_name in seen_fields:
                messagebox.showerror("Validation Error", f"Duplicate field name found: '{entry_name}'. Field names must be unique.")
                return
            seen_fields.add(entry_name)
            
            data_type = self.data_type_comboboxes[i].get()
            _fields.append(entry_name)
            _dtypes.append(data_type)
            
            # Capture Configs for Boolean
            if data_type == "BOOLEAN":
                true_val = self.boolean_configs[i]['true'].get().strip() or "True"
                false_val = self.boolean_configs[i]['false'].get().strip() or "False"
                _configs[entry_name] = {'true_label': true_val, 'false_label': false_val}
            
        json_fields = json.dumps(_fields)
        json_dtypes = json.dumps(_dtypes)
        json_configs = json.dumps(_configs)
        
        try:
            mcursor.execute("INSERT INTO main (database_names, table_names, fields, data_types, field_configs, created_at, updated_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)", (self.db_value, self.table_value, json_fields, json_dtypes, json_configs))
            mconn.commit()
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save metadata: {e}")
            return
        
        # Create table based on user input
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {self.table_value} (id INTEGER PRIMARY KEY, "
        for i in range(self.fields_value):
            entry_name = _fields[i] # Safe to use already validated list
            data_type = _dtypes[i]
            
            if data_type == "BOOLEAN":
                create_table_sql += f"{entry_name} INTEGER, " # Using INTEGER for boolean
            else:
                create_table_sql += f"{entry_name} {data_type}, "
        create_table_sql = create_table_sql.rstrip(", ") + ")"
        
        try:
            with get_db_connection(self.db_value) as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
        except Exception as e:
            # Rollback metadata insert if table creation fails?
            # ideally yes, but for now just show error
            messagebox.showerror("Database Error", f"Error creating table: {e}")
            # print(f"Error creating table: {e}")
            return

        self.Main_Form( self.db_value, self.table_value, _fields, _configs)
        self.start_main()
        
        # Update global main_data with fresh data
        global main_data
        main_data = fetch_all_data()
        if self.Main_app:
            self.Main_app.form_card()
            # self.Main_app.TB.main_table(self.db_value, self.table_value, _fields) # Don't auto-load table yet, user might want to enter data

    def update_values(self, event, i):
        combobox = self.data_type_comboboxes[i]
        selected_type = combobox.get()
        frame = self.boolean_frames[i]
        
        if selected_type == "BOOLEAN":
            frame.grid(row=i, column=3, padx=10, pady=8)
        else:
            frame.grid_forget()
        
    def create_fields(self):
        # Clear existing fields
        for widget in self.fieldsFrame.winfo_children():
            widget.destroy()
            
        self.fieldsFrame.grid_columnconfigure(1, weight=1)
            
        self.entry_fields = []
        self.data_type_comboboxes = []
        self.boolean_frames = []
        self.boolean_configs = [] # List of dicts {'true': entry, 'false': entry}
        self.labels = []
        
        for i in range(self.fields_value):
            _f ="Field name {}: ".format(i+1)
            self.labels.append(_f)
            
        for i, label_text in enumerate(self.labels):    
            label = ctk.CTkLabel(self.fieldsFrame, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=8, sticky="e")
            
            entry = ctk.CTkEntry(self.fieldsFrame)
            entry.grid(row=i, column=1, padx=10, pady=8, sticky="ew")
            self.entry_fields.append(entry)
            
            data_type_combobox = ctk.CTkComboBox(self.fieldsFrame, values=["TEXT", "NUMERIC", "DATE", "DATETIME", "TIMESTAMP", "BOOLEAN"], width=100,
                                                 command=lambda val, idx=i: self.update_values(val, idx))
            data_type_combobox.grid(row=i, column=2, padx=10, pady=8)
            self.data_type_comboboxes.append(data_type_combobox)
            
            # Boolean Config Frame (Hidden by default)
            bool_frame = ctk.CTkFrame(self.fieldsFrame, fg_color="transparent")
            
            ctk.CTkLabel(bool_frame, text="True:").pack(side="left", padx=2)
            true_entry = ctk.CTkEntry(bool_frame, width=60, placeholder_text="Yes")
            true_entry.pack(side="left", padx=2)
            
            ctk.CTkLabel(bool_frame, text="False:").pack(side="left", padx=2)
            false_entry = ctk.CTkEntry(bool_frame, width=60, placeholder_text="No")
            false_entry.pack(side="left", padx=2)
            
            self.boolean_frames.append(bool_frame)
            self.boolean_configs.append({'true': true_entry, 'false': false_entry})
            
        button = ctk.CTkButton(self.fieldsFrame, text="Submit Schema", command=self.submit_data, fg_color="blue")
        n_f = len(self.labels)+1
        button.grid(row=n_f, column=1, padx=10, pady=20, sticky="e")
    
    def Main_Form(self, db, tb, fields, configs=None):
        self.mainFrame.pack_forget()
        self.mainFrame.pack(fill=tk.BOTH, expand=True)
        
        # Clear mainFrame children
        for widget in self.mainFrame.winfo_children():
            widget.destroy()
            
        self.mainFrame.grid_columnconfigure(1, weight=1)
        
        self.current_db = db
        self.current_tb = tb
        self.current_fields = fields
        self.current_configs = configs or {}
        
        # Need data types to decide rendering. 
        # But we only passed 'fields'. We need 'data_types' too for validation and rendering!
        # submit_data has _dtypes locally. We can pass it or fetch from main_data using lookup.
        # Lookup is safer if we want to rely on DB, but passing local _dtypes is faster.
        # Let's rely on looking up because validation needs Config anyway.
        
        # Lookup data types and config if not passed
        # This function is called immediately after creation, so DB might not be refreshed in main_data global var yet
        # But submit_data updates main_data global.
        
        # Wait, submit_data calls self.Main_Form BEFORE updating global main_data? 
        # No, "Update global main_data" is AFTER "self.start_main()"?
        # Actually line 506 is "main_data = fetch_all_data()".
        # Line 501 is "self.Main_Form(...)".
        # So main_data is NOT updated yet.
        # I should use the local lists.
        # I need to update signature to accept dtypes too.
        
        title = ctk.CTkLabel(self.mainFrame, text=f'Enter Data: {self.current_tb}', font=("Arial", 16, "bold"))
        self.main_entry_fields=[] # Can hold Entry widgets or StringVar for RadioButtons
        title.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        
        # If configs passed, use them. If dtypes not passed, we have a problem.
        # Let's fetch dtypes from DB or pass them.
        # Modifying submit_data to pass _dtypes is best but I just edited it.
        # I can query DB here.
        
        configs_map = self.current_configs
        dtypes_map = {} # field -> type
        
        # Quick fetch dtypes from DB since we just committed
        try:
            mcursor.execute("SELECT fields, data_types, field_configs FROM main WHERE database_names=? AND table_names=?", (db, tb))
            row = mcursor.fetchone()
            if row:
                _f = json.loads(row[0])
                _d = json.loads(row[1])
                _c = json.loads(row[2]) if row[2] else {}
                dtypes_map = dict(zip(_f, _d))
                if not configs_map: configs_map = _c
        except:
             pass
        
        self.main_field_types = [] # Store types for validation
        
        for i, label_text in enumerate(self.current_fields):    
            label = ctk.CTkLabel(self.mainFrame, text=f"{label_text}:")
            label.grid(row=i+1, column=0, padx=10, pady=8, sticky="e")
            
            dtype = dtypes_map.get(label_text, "TEXT")
            self.main_field_types.append(dtype)
            
            if dtype == "BOOLEAN":
                # Render Radio Buttons
                var = ctk.IntVar(value=-1) # Default none? Or 0? Let's say -1 implies unselected? 
                # Or default 0 (False).
                var.set(0)
                
                c = configs_map.get(label_text, {})
                t_lbl = c.get('true_label', 'True')
                f_lbl = c.get('false_label', 'False')
                
                frame = ctk.CTkFrame(self.mainFrame, fg_color="transparent")
                frame.grid(row=i+1, column=1, padx=10, pady=8, sticky="ew")
                
                t_btn = ctk.CTkRadioButton(frame, text=t_lbl, variable=var, value=1)
                t_btn.pack(side="left", padx=10)
                f_btn = ctk.CTkRadioButton(frame, text=f_lbl, variable=var, value=0)
                f_btn.pack(side="left", padx=10)
                
                self.main_entry_fields.append(var)
                
                # Bind Enter to Last Field
                if i == len(self.current_fields) - 1:
                    # RadioButton doesn't support bind easily for value submission via Enter on widget itself
                    # But we can bind to frame or buttons.
                    t_btn.bind("<Return>", lambda event: self.main_submit(db, tb, fields))
                    f_btn.bind("<Return>", lambda event: self.main_submit(db, tb, fields))

            
            elif dtype == "DATE":
                # Use Custom CTkDatePicker
                date_entry = CTkDatePicker(self.mainFrame)
                date_entry.grid(row=i+1, column=1, padx=10, pady=8, sticky="ew")
                self.main_entry_fields.append(date_entry)
                
                if i == len(self.current_fields) - 1:
                     date_entry.bind("<Return>", lambda event: self.main_submit(db, tb, fields))

            elif dtype in ["TIMESTAMP", "DATETIME"]:
                # Auto-fill and Read-only (Will be updated on submit)
                entry = ctk.CTkEntry(self.mainFrame)
                entry.grid(row=i+1, column=1, padx=10, pady=8, sticky="ew")
                
                # Show "Auto-filled on Submit" or current time
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry.insert(0, current_time)
                entry.configure(state="readonly")
                
                self.main_entry_fields.append(entry)
                
                if i == len(self.current_fields) - 1:
                     entry.bind("<Return>", lambda event: self.main_submit(db, tb, fields))
                
            else:
                entry = ctk.CTkEntry(self.mainFrame)
                entry.grid(row=i+1, column=1, padx=10, pady=8, sticky="ew")
                self.main_entry_fields.append(entry)
                
                if i == len(self.current_fields) - 1:
                     entry.bind("<Return>", lambda event: self.main_submit(db, tb, fields))
            
        button = ctk.CTkButton(self.mainFrame, text="Submit Data", command=lambda: self.main_submit(db,tb,fields), fg_color="green")
        n_f = len(self.current_fields)+1
        button.grid(row=n_f, column=1, padx=10, pady=20, sticky="e")
        
    def main_submit(self, db, tb, fields, event=None):
        from tkinter import messagebox
        values = []
        for i in range(len(fields)):
            widget = self.main_entry_fields[i]
            val = ""
            if isinstance(widget, ctk.IntVar): # RadioButton
                val = widget.get()
            else: # Entry (and CTkDatePicker inherits from Entry)
                val = widget.get()
                
            # Validation & Override
            dtype = self.main_field_types[i]
            label = fields[i]
            
            if dtype in ["TIMESTAMP", "DATETIME"]:
                # Override with actual submission time
                val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if dtype == "INTEGER":
                if val:
                    try:
                        int(val)
                    except ValueError:
                        messagebox.showerror("Validation Error", f"Field '{label}' must be an Integer.")
                        return
            elif dtype in ["NUMERIC", "REAL"]:
                if val:
                    try:
                        float(val)
                    except ValueError:
                         messagebox.showerror("Validation Error", f"Field '{label}' must be a Number.")
                         return
            
            values.append(val)
            
        # Construct the parameterized SQL query
        try:
            with get_db_connection(db) as conn:
                cursor = conn.cursor()
                placeholders = ', '.join(['?' for _ in fields])
                query = f"INSERT INTO {tb} ({', '.join(fields)}) VALUES ({placeholders})"
                # print(f"Executing SQL query: {query}")
                cursor.execute(query, values)
                conn.commit()
                
            # Clear entries after submit
            for widget in self.main_entry_fields:
                if isinstance(widget, ctk.CTkEntry):
                    widget.delete(0, tk.END)
                elif isinstance(widget, ctk.IntVar):
                    widget.set(0) # Reset to False
            
            messagebox.showinfo("Success", "Data saved successfully.")
                
        except sqlite3.Error as e:
             # raise Exception(f"Error executing SQL query: {e}")
             messagebox.showerror("Database Error", f"Error saving data: {e}")
             # print(f"Error executing SQL query: {e}")
             pass
        else:
            pass
            # print("Data inserted successfully.")
            
            
        if self.Main_app and self.Main_app.is_window_visible:
             # Refresh table if visible
             self.Main_app.fetch_main(get_id_by_table(tb)) # Need a way to get ID or just refresh
             # Alternatively, just recall table load
             self.Main_app.TB.main_table(db, tb, fields)

    # ... to_Excel remains same ...


    def __init__(self, FWf, main_app=None):
        """
        Args:
            FWf (CTkScrollableFrame): Parent frame
            main_app (Main): Reference to main app
        """
        
        # super().__init__() # Form_Window is not a class subclassing anything in original?
        # Original: class Form_Window(): ... super().__init__() -> This will err if it doesn't inherit
        # Original code had `class Form_Window():` but called `super().__init__()`. This likely caused an error unless object has init?
        # object.__init__() takes no args.
        
        self.FW_Frame = FWf
        self.Main_app = main_app
        # self.FW_Frame.place(x=53, y=0) # Removing place call as it is managed by Main grid
        
        self.DBFrame = ctk.CTkFrame(self.FW_Frame, fg_color="transparent")
        self.DBFrame.pack(fill=tk.BOTH, expand=True)
        
        self.fieldsFrame = ctk.CTkFrame(self.FW_Frame, fg_color="transparent")
        
        self.mainFrame = ctk.CTkFrame(self.FW_Frame, fg_color="transparent")
        
        self.field_names = []
        self.fields_value = None
        self.current_db = None   
        self.current_tb= None
        self.current_fields = None
        self.db_name = tk.StringVar()
        self.table_name = tk.StringVar()
        self.no_of_f = tk.StringVar(value="1")
        self.create_form()


class DataEditor(ctk.CTkToplevel):
    def __init__(self, parent, db_name, table_name, fields, data_types, configs=None, row_data=None, row_id=None, refresh_callback=None):
        super().__init__(parent)
        self.db_name = db_name
        self.table_name = table_name
        self.fields = fields
        self.data_types = data_types
        self.configs = configs or {}
        self.row_data = row_data # Tuple of values if editing
        self.row_id = row_id # ID if editing
        self.refresh_callback = refresh_callback
        
        self.title("Edit Data" if row_id else "Add Data")

        self.geometry("400x500")
        self.attributes("-topmost", True)
        self.transient(parent)
        
        self.entries = [] # Stores Entry widgets or IntVars
        
        # UI
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        for i, (f_name, f_type) in enumerate(zip(self.fields, self.data_types)):
            ctk.CTkLabel(self.scroll, text=f"{f_name}:").pack(anchor="w", padx=5, pady=(5,0))
            
            val = None
            if self.row_data:
                try:
                    val = self.row_data[i]
                except IndexError:
                    pass

            if f_type == "BOOLEAN":
                var = ctk.IntVar(value=0)
                
                c = self.configs.get(f_name, {})
                t_lbl = c.get('true_label', 'True')
                f_lbl = c.get('false_label', 'False')

                # Pre-fill
                if val is not None:
                     try:
                         val_str = str(val).lower()
                         # Check standard True values OR Custom Label
                         if val_str in ['1', 'true', 'yes'] or val_str == t_lbl.lower(): 
                             var.set(1)
                         else: 
                             var.set(0)
                     except: var.set(0)
                
                frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
                frame.pack(fill="x", padx=5, pady=5)
                ctk.CTkRadioButton(frame, text=t_lbl, variable=var, value=1).pack(side="left", padx=10)
                ctk.CTkRadioButton(frame, text=f_lbl, variable=var, value=0).pack(side="left", padx=10)
                
                self.entries.append(var)
            elif f_type == "DATE":
                # Custom CTkDatePicker
                entry = CTkDatePicker(self.scroll)
                entry.pack(fill="x", padx=5, pady=5)
                
                if val is not None:
                     entry.configure(state="normal")
                     entry.insert(0, str(val))
                     entry.configure(state="readonly")
                
                self.entries.append(entry)

            elif f_type in ["TIMESTAMP", "DATETIME"]:
                # Read-only Timestamp
                entry = ctk.CTkEntry(self.scroll)
                entry.pack(fill="x", padx=5, pady=5)
                
                # If editing, show existing. If new, show NOW
                if val is not None:
                     entry.insert(0, str(val))
                else:
                     entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                     
                entry.configure(state="readonly")
                self.entries.append(entry)

            else:
                entry = ctk.CTkEntry(self.scroll)
                entry.pack(fill="x", padx=5, pady=5)
                # Pre-fill
                if val is not None:
                    entry.insert(0, str(val))
                if i == len(self.fields) - 1:
                     entry.bind("<Return>", lambda event: self.save_data())
                self.entries.append(entry)

        btn_text = "Update" if row_id else "Add"
        ctk.CTkButton(self, text=btn_text, command=self.save_data).pack(pady=20)
        
    def save_data(self, event=None):
        values = []
        from tkinter import messagebox
        
        for i, widget in enumerate(self.entries):
            val = ""
            if isinstance(widget, ctk.IntVar):
                val = widget.get()
            else:
                val = widget.get()
                
            # Validation
            dtype = self.data_types[i]
            label = self.fields[i]
            
            # Timestamp update on save
            # Only update if we want to track 'Last Modified' or if it's a new record
            # User request: "update datestamp on time of submit"
            if dtype in ["TIMESTAMP", "DATETIME"]:
                 # Update to NOW
                 val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if dtype == "INTEGER":
                if val:
                    try:
                        int(val)
                    except ValueError:
                        messagebox.showerror("Validation Error", f"Field '{label}' must be an Integer.", parent=self)
                        return
            elif dtype in ["NUMERIC", "REAL"]:
                if val:
                    try:
                        float(val)
                    except ValueError:
                         messagebox.showerror("Validation Error", f"Field '{label}' must be a Number.", parent=self)
                         return
            
            # Security Validation (Block ?, SQL Keywords)
            is_valid, error_msg = validate_security_input(val, label)
            if not is_valid:
                messagebox.showerror("Security Alert", error_msg, parent=self)
                return

            values.append(val)
        
        try:
            with get_db_connection(self.db_name) as conn:
                if self.row_id:
                    # UPDATE
                    set_clause = ", ".join([f"{f}=?" for f in self.fields])
                    query = f"UPDATE {self.table_name} SET {set_clause} WHERE id=?"
                    conn.execute(query, values + [self.row_id])
                else:
                    # INSERT
                    placeholders = ", ".join(["?" for _ in self.fields])
                    query = f"INSERT INTO {self.table_name} ({', '.join(self.fields)}) VALUES ({placeholders})"
                    conn.execute(query, values)
                conn.commit()
            
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
            # print("Data saved.")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}", parent=self)

class Table_Window:
    def main_table(self, db, tb, fields):
        self.current_db = db
        self.current_tb = tb
        self.current_fields = fields
        
        # Update Title
        self.title_lbl.configure(text=f"Table: {tb}")

        # Fetch data types for DataEditor
        # Need to find ID to get data types. Expensive loop lookup?
        # Or Just pass from Main? Main passes fields.
        # Let's simple look up from main_data
        self.current_dtypes = []
        self.current_configs = {}
        # Debugging: Print keys to verify match
        # print("DEBUG: fetch_main keys:", main_data.keys())
        for d in main_data.values():
            # print(f"DEBUG: Checking {d['table_names']} in {d['database_names']} vs {tb} in {db}")
            if d['table_names'] == tb and d['database_names'] == db:
                self.current_dtypes = d['data_types']
                self.current_configs = d.get('field_configs', {})
                # print(f"DEBUG: Found configs: {self.current_configs}")
                break

        current_conn(db)
        # Update columns: Add 'ID' implicitly for tracking?
        # Treeview allows hidden columns. Let's try to fetch ID but hide it or show it.
        # It's better to modify SELECT to include ID
        
        # cols = tuple([f"#{i}" for i in range(len(fields))])
        
        # Recreate Treeview to ensure columns are reset cleanly
        display_fields = list(fields)
        
        # Destroy existing tree to prevent column conflicts
        if hasattr(self, 'main_tree') and self.main_tree.winfo_exists():
            self.main_tree.destroy()

        self.main_tree = ttk.Treeview(self.tree_frame, columns=display_fields, show="headings",
                                      yscrollcommand=self.v_scroll.set, 
                                      xscrollcommand=self.h_scroll.set)
        
        # Re-attach scrollbars to new tree
        self.v_scroll.config(command=self.main_tree.yview)
        self.h_scroll.config(command=self.main_tree.xview)
        
        self.main_tree.grid(row=0, column=0, sticky="nsew")

        # Dynamic Sizing Helper
        def get_text_width(text, font_prop):
            return tk.font.Font(font=font_prop).measure(text)

        header_font = ('Arial', 12, 'bold')
        cell_font = ('Arial', 11)

        try:
            # Select ID as well!
            query_fields = "id, " + ", ".join(fields)
            cursor.execute(f"SELECT {query_fields} FROM {tb}")
            datas = cursor.fetchall()
        except Exception as e:
            # print(f"Error fetching data: {e}")
            datas = []

        # Insert Data & Calculate Widths
        # Initialize widths with header width
        col_widths = {f: get_text_width(f, header_font) + 20 for f in display_fields}

        for data in datas:
            row_id = data[0]
            row_values = list(data[1:]) # Convert tuple to list to modify
            
            # Map Boolean Values to Labels
            for idx, val in enumerate(row_values):
                if idx < len(self.current_dtypes):
                     if self.current_dtypes[idx] == "BOOLEAN":
                         # Get Config
                         f_name = self.current_fields[idx]
                         c = self.current_configs.get(f_name, {})
                         t_lbl = c.get('true_label', 'True')
                         f_lbl = c.get('false_label', 'False')
                         
                         try:
                             # Map 1 -> True Label, 0 -> False Label
                             if str(val) == '1':
                                 row_values[idx] = t_lbl
                             else:
                                 row_values[idx] = f_lbl
                         except:
                             row_values[idx] = f_lbl

            # Tag for row coloring (alternating?)
            # Let's just use default or 'fontstyle' equivalent if needed
            self.main_tree.insert("", "end", iid=row_id, values=row_values)

            # Check widths
            for idx, val in enumerate(row_values):
                if idx < len(display_fields):
                    col_name = display_fields[idx]
                    w = get_text_width(str(val), cell_font) + 20
                    if w > col_widths[col_name]:
                        col_widths[col_name] = w

        # Apply Column Config
        for col in display_fields:
            self.main_tree.heading(col, text=col)
            # Cap width (optional) -> e.g., max 400
            w = min(col_widths[col], 400) 
            self.main_tree.column(col, anchor='center', width=w, stretch=False) # stretch=False for horizontal scroll
        
        # Ensure Buttons are visible (pack them if not already)
        # self.btn_frame.pack(fill="x", pady=5) # This was for old pack layout, now it's gridded

    def __init__(self, TBf):
        self.TBFrame = TBf
        self.TBFrame.grid_columnconfigure(0, weight=1)
        self.TBFrame.grid_rowconfigure(1, weight=1) # Row 0: Title, Row 1: Tree, Row 2: Buttons

        # 1. Custom Title Bar
        self.title_frame = ctk.CTkFrame(self.TBFrame, fg_color="#4a4a4a", height=40, corner_radius=0)
        self.title_frame.grid(row=0, column=0, sticky="ew")
        self.title_lbl = ctk.CTkLabel(self.title_frame, text="Table Records", font=("Arial", 18, "bold"), text_color="white")
        self.title_lbl.pack(side="left", padx=20, pady=5)

        # 2. Treeview Container (for Scrollbars)
        self.tree_frame = ctk.CTkFrame(self.TBFrame, fg_color="transparent")
        self.tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Scrollbars
        self.v_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical")
        self.h_scroll = ttk.Scrollbar(self.tree_frame, orient="horizontal")

        # Treeview
        # Check for multiple selections? "extended" is default
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure Treeview Colors/Fonts
        self.style.configure("Treeview.Heading", font=('Arial', 12, 'bold'), background="#d3d3d3", foreground="black")
        self.style.configure("Treeview", font=('Arial', 11), rowheight=25, background="white", fieldbackground="white")
        self.style.map("Treeview", background=[('selected', '#347083')], foreground=[('selected', 'white')])
        
        self.main_tree = ttk.Treeview(self.tree_frame, show="headings", 
                                      yscrollcommand=self.v_scroll.set, 
                                      xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.config(command=self.main_tree.yview)
        self.h_scroll.config(command=self.main_tree.xview)

        self.main_tree.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll.grid(row=1, column=0, sticky="ew")

        # 3. Action Buttons (Bottom)
        self.btn_frame = ctk.CTkFrame(self.TBFrame, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkButton(self.btn_frame, text="➕ Add Row", fg_color="green", width=120, command=self.add_row).pack(side="left", padx=5)
        ctk.CTkButton(self.btn_frame, text="✏️ Edit Row", fg_color="orange", width=120, command=self.update_row).pack(side="left", padx=5)
        ctk.CTkButton(self.btn_frame, text="🗑️ Delete Row", fg_color="red", width=120, command=self.delete_row).pack(side="left", padx=5)
        ctk.CTkButton(self.btn_frame, text="📤 Export", fg_color="#3B8ED0", width=120, command=self.export_data).pack(side="left", padx=5)
        ctk.CTkButton(self.btn_frame, text="📊 Analyze", fg_color="#9146FF", width=120, command=self.analyze_data).pack(side="left", padx=5)

    def refresh_table(self):
         if hasattr(self, 'current_db'):
             self.main_table(self.current_db, self.current_tb, self.current_fields)

    def add_row(self):
        if not hasattr(self, 'current_db'): return
        DataEditor(self.TBFrame, self.current_db, self.current_tb, 
                   self.current_fields, self.current_dtypes, configs=self.current_configs,
                   refresh_callback=self.refresh_table)

    def update_row(self):
        selected = self.main_tree.selection()
        if not selected: return
        iid = selected[0] # This is the ID
        values = self.main_tree.item(iid)['values']
        
        DataEditor(self.TBFrame, self.current_db, self.current_tb, 
                   self.current_fields, self.current_dtypes, configs=self.current_configs,
                   row_data=values, row_id=iid,
                   refresh_callback=self.refresh_table)

    def delete_row(self):
        selected = self.main_tree.selection()
        if not selected: return
        
        iid = selected[0]
        from tkinter import messagebox
        if messagebox.askyesno("Confirm", "Delete selected row?"):
            try:
                with get_db_connection(self.current_db) as conn:
                    conn.execute(f"DELETE FROM {self.current_tb} WHERE id=?", (iid,))
                    conn.commit()
                self.refresh_table()
            except Exception as e:
                messagebox.showerror("Error", f"Delete failed: {e}")

    def export_data(self):
        if not hasattr(self, 'current_db') or not hasattr(self, 'current_tb'):
            return

        selected_items = self.main_tree.selection()
        export_selected_only = False

        from tkinter import messagebox
        if selected_items:
            # Ask user if they want to export only selected
            ans = messagebox.askyesnocancel("Export Options", "Export only selected rows?\nYes = Selected Only\nNo = Export All")
            if ans is None: return # Cancel
            export_selected_only = ans
        
        
        # Calculate next filename
        # Pattern: table_name_1.xlsx, table_name_2.xlsx, ...
        # Check existing files in xlsrc
        existing_files = os.listdir(xlsrc)
        max_num = 0
        base_name = self.current_tb
        
        for f in existing_files:
            if f.startswith(base_name) and (f.endswith('.xlsx') or f.endswith('.csv')):
                # Extract number
                # Expected format: name_N.ext
                try:
                    # Remove extension
                    name_no_ext = os.path.splitext(f)[0]
                    # Check if it follows pattern name_N
                    if name_no_ext.startswith(base_name + "_"):
                        num_part = name_no_ext[len(base_name)+1:]
                        if num_part.isdigit():
                            num = int(num_part)
                            if num > max_num:
                                max_num = num
                except:
                    pass
        
        next_num = max_num + 1
        default_filename = f"{base_name}_{next_num}"

        # Get file path
        file_path = filedialog.asksaveasfilename(
            initialdir=xlsrc,
            initialfile=default_filename,
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Data"
        )
        
        if not file_path: return

        try:
            df = None
            if export_selected_only:
                # Get data from treeview
                data_list = []
                for iid in selected_items:
                    row_values = self.main_tree.item(iid)['values']
                    data_list.append(row_values)
                
                # We need columns. self.current_fields has them.
                # Note: row_values usually excludes ID if we hid it, or includes it if we showed it.
                # In main_table, we did: 
                # row_values = data[1:] (excluding ID)
                # columns=display_fields (which is fields)
                
                df = pd.DataFrame(data_list, columns=self.current_fields)
            else:
                # Fetch all from DB
                with get_db_connection(self.current_db) as conn:
                    query = f"SELECT * FROM {self.current_tb}" # This fetches ID too usually
                    # But wait, logic in main_table was:
                    # query_fields = "id, " + ", ".join(fields)
                    # So if we want to match user view (no ID), we should exclude ID or fetch specific fields
                    
                    # Let's fetch what user defined
                    fields_str = ", ".join(self.current_fields)
                    query = f"SELECT {fields_str} FROM {self.current_tb}"
                    df = pd.read_sql_query(query, conn)
            
            if df is not None:
                if file_path.endswith('.csv'):
                    df.to_csv(file_path, index=False)
                else:
                    # Default to Excel
                    if not file_path.endswith('.xlsx'):
                        file_path += '.xlsx'
                    df.to_excel(file_path, index=False)
                
                messagebox.showinfo("Success", f"Data exported successfully to:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {e}")
            # print(f"Export Error: {e}")

    def analyze_data(self):
        if not hasattr(self, 'current_db') or not hasattr(self, 'current_tb'):
            return
        
        # Open Analysis Window
        # Pass self.current_fields, not just display fields
        # Use TBFrame.winfo_toplevel() as self is not a widget
        AnalysisWindow(self.TBFrame.winfo_toplevel(), self.current_db, self.current_tb, self.current_fields, self.current_dtypes)

# Helper for ID lookup
def get_id_by_table(table_name):
    global main_data
    for _id, data in main_data.items():
        if data['table_names'] == table_name:
            return _id
    return None

def current_conn(db_name):
    global conn, cursor
    conn = get_db_connection(db_name)
    cursor = conn.cursor()

class AnalysisWindow(ctk.CTkToplevel):
    def __init__(self, parent, db_name, table_name, fields, data_types):
        super().__init__(parent)
        self.title("Data Analysis")
        self.geometry("1000x600")
        
        # Bring to front
        self.lift()
        self.focus_force()
        self.grab_set()
        
        self.db_name = db_name
        self.table_name = table_name
        self.fields = fields
        self.data_types = data_types
        
        # Layout: Sidebar (Left) + Chart (Right)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="Analysis Options", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Chart Type
        ctk.CTkLabel(self.sidebar, text="Chart Type:", anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        self.chart_type = ctk.CTkComboBox(self.sidebar, values=["Bar", "Line", "Scatter", "Pie"])
        self.chart_type.set("Bar")
        self.chart_type.pack(fill="x", padx=20, pady=5)
        
        # X Axis
        ctk.CTkLabel(self.sidebar, text="X Axis (Category):", anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        self.x_axis = ctk.CTkComboBox(self.sidebar, values=self.fields)
        self.x_axis.pack(fill="x", padx=20, pady=5)
        
        # Y Axis (Multi-select)
        ctk.CTkLabel(self.sidebar, text="Y Axis (Values):", anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        self.y_scroll = ctk.CTkScrollableFrame(self.sidebar, height=200)
        self.y_scroll.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.y_vars = {} # map field -> IntVar
        
        numeric_types = ['INTEGER', 'NUMERIC', 'REAL', 'BOOLEAN']
        
        for f, t in zip(self.fields, self.data_types):
            if t in numeric_types:
                var = ctk.IntVar()
                chk = ctk.CTkCheckBox(self.y_scroll, text=f, variable=var)
                chk.pack(anchor="w", pady=2)
                self.y_vars[f] = var
                
        # Generate Button
        ctk.CTkButton(self.sidebar, text="Generate Chart", command=self.generate_chart).pack(padx=20, pady=20)
        
        # Chart Area
        self.chart_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chart_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
    def generate_chart(self):
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        c_type = self.chart_type.get()
        x_field = self.x_axis.get()
        
        # Get selected Y fields
        y_fields = [f for f, var in self.y_vars.items() if var.get() == 1]
        
        if not x_field or not y_fields:
            from tkinter import messagebox
            messagebox.showwarning("Missing Input", "Please select an X Axis and at least one Y Axis field.")
            return

        try:
             with get_db_connection(self.db_name) as conn:
                # Construct Query
                cols = [x_field] + y_fields
                cols_str = ", ".join(cols)
                df = pd.read_sql_query(f"SELECT {cols_str} FROM {self.table_name}", conn)
            
             # Process Data
             # Convert numeric Y fields
             for y in y_fields:
                 df[y] = pd.to_numeric(df[y], errors='coerce')
             
             # Drop NaN
             df.dropna(subset=y_fields, inplace=True)
             
             # Plotting
             fig, ax = plt.subplots(figsize=(8, 6), dpi=100)
             
             x_data = df[x_field].astype(str)
             
             if c_type == "Bar":
                 df.plot(kind='bar', x=x_field, y=y_fields, ax=ax, rot=45)
                 ax.set_ylabel("Values")
                 ax.set_title(f"{', '.join(y_fields)} by {x_field}")
                 
             elif c_type == "Line":
                 df.plot(kind='line', x=x_field, y=y_fields, ax=ax, marker='o', rot=45)
                 ax.set_ylabel("Values")
                 ax.set_title(f"{', '.join(y_fields)} by {x_field}")
                 
             elif c_type == "Scatter":
                 # Fallback to range index for X if it's string, then set ticks
                 x_indices = range(len(x_data))
                 
                 for y in y_fields:
                     ax.scatter(x_indices, df[y], label=y)
                 
                 ax.set_xticks(x_indices)
                 ax.set_xticklabels(x_data, rotation=45, ha='right')
                 ax.legend()
                 ax.set_title(f"{', '.join(y_fields)} vs {x_field}")
                 
             elif c_type == "Pie":
                 y = y_fields[0]
                 if len(y_fields) > 1:
                     from tkinter import messagebox
                     messagebox.showinfo("Info", f"Pie chart supports single data series. Using '{y}'.")
                 
                 df_grouped = df.groupby(x_field)[y].sum()
                 ax.pie(df_grouped, labels=df_grouped.index, autopct='%1.1f%%', startangle=90)
                 ax.set_title(f"Distribution of {y} by {x_field}")

             plt.tight_layout()
             
             canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
             canvas.draw()
             canvas.get_tk_widget().pack(fill="both", expand=True)
             
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Chart generation failed: {e}")

class Main(ctk.CTk):
    def toggle_form(self):
        if not self.is_window_visible:
            self.window_frame.grid(row=0, column=1, sticky="nsew", padx=2)
            self.grid_columnconfigure(1, weight=0, minsize=250)
            self.is_window_visible = True
            self.form_card()
        else:
            self.window_frame.grid_forget()
            self.grid_columnconfigure(1, weight=0, minsize=0)
            self.is_window_visible = False

    def show_databases(self):
        self.welcome_frame.grid_forget()
        self.TB_Frame.grid_forget()
        self.FW_Frame.grid_forget()
        self.help_frame.grid_forget()
        self.about_frame.grid_forget()
        self.DB_View_Frame.configure(label_text="Databases")
        self.DB_View_Frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        self.grid_columnconfigure(2, weight=1)
        
        # Clear existing
        for widget in self.DB_View_Frame.winfo_children():
            widget.destroy()
            
        # Get unique databases and dates
        db_info = {}
        for data in main_data.values():
            db_name = data['database_names']
            c_date = data.get('created_at')
            u_date = data.get('updated_at')
            
            if db_name not in db_info:
                db_info[db_name] = {'created_at': c_date, 'updated_at': u_date}
            else:
                # Update Min Created
                if c_date:
                    curr_c = db_info[db_name]['created_at']
                    if not curr_c or c_date < curr_c:
                         db_info[db_name]['created_at'] = c_date
                
                # Update Max Updated
                if u_date:
                    curr_u = db_info[db_name]['updated_at']
                    if not curr_u or u_date > curr_u:
                         db_info[db_name]['updated_at'] = u_date
            
        if not db_info:
            ctk.CTkLabel(self.DB_View_Frame, text="No databases found", font=("Arial", 16)).pack(pady=20)
            return

        for db, info in db_info.items():
            card = ctk.CTkFrame(self.DB_View_Frame, fg_color="#4a4a4a", corner_radius=10)
            card.pack(fill="x", padx=10, pady=5)
            
            # DB Name
            ctk.CTkLabel(card, text=f"🗄️ {db}", font=("Arial", 16, "bold"), text_color="white").pack(side="left", padx=20, pady=15)
            
            # Dates Frame
            d_frame = ctk.CTkFrame(card, fg_color="transparent")
            d_frame.pack(side="left", padx=10)
            
            # Creation Date
            c_str = "Unknown"
            if info['created_at']:
                try: c_str = str(info['created_at']).split()[0]
                except: pass
            ctk.CTkLabel(d_frame, text=f"Created: {c_str}", font=("Arial", 10), text_color="lightgray").pack(anchor="w")
            
            # Update Date
            u_str = "Unknown"
            if info['updated_at']:
                try: u_str = str(info['updated_at']).split()[0]
                except: pass
            ctk.CTkLabel(d_frame, text=f"Updated: {u_str}", font=("Arial", 10), text_color="lightgray").pack(anchor="w")
            
            ctk.CTkButton(card, text="Open", command=lambda d=db: self.show_tables_in_db(d)).pack(side="right", padx=20, pady=10)

    def show_tables_in_db(self, db_name):
        # reuse DB_View_Frame but change content
        for widget in self.DB_View_Frame.winfo_children():
            widget.destroy()
            
        self.DB_View_Frame.configure(label_text=f"Database: {db_name}")
        
        # Back Button
        ctk.CTkButton(self.DB_View_Frame, text="⬅ Back to Databases", fg_color="gray", 
                      command=self.show_databases).pack(anchor="w", padx=10, pady=10)
        
        # List Tables
        found = False
        for _id, data in main_data.items():
            if data['database_names'] == db_name:
                found = True
                card = ctk.CTkFrame(self.DB_View_Frame, fg_color="#8E8FFA", corner_radius=10)
                card.pack(fill="x", padx=10, pady=5)
                
                ctk.CTkLabel(card, text=f"📄 {data['table_names']}", font=("Arial", 14, "bold"), text_color="white").pack(side="left", padx=20, pady=15)
                
                ctk.CTkButton(card, text="View Data", fg_color="green", 
                              command=lambda i=_id: self.fetch_main(i)).pack(side="right", padx=20, pady=10)
        
        if not found:
             ctk.CTkLabel(self.DB_View_Frame, text="No tables in this database.").pack(pady=20)

    def show_welcome(self):
        self.FW_Frame.grid_forget()
        self.TB_Frame.grid_forget()
        self.DB_View_Frame.grid_forget()
        self.help_frame.grid_forget()
        self.about_frame.grid_forget()
        self.welcome_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        self.grid_columnconfigure(2, weight=1)
        
    def show_editor_layout(self):
        self.welcome_frame.grid_forget()
        self.TB_Frame.grid_forget()
        self.DB_View_Frame.grid_forget()
        self.help_frame.grid_forget()
        self.about_frame.grid_forget()
        self.FW_Frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        self.grid_columnconfigure(2, weight=1)
        
        # Ensure Form_Window is ready for new input
        self.FW.create_form()

    def show_help(self):
        self.welcome_frame.grid_forget()
        self.TB_Frame.grid_forget()
        self.FW_Frame.grid_forget()
        self.DB_View_Frame.grid_forget()
        self.about_frame.grid_forget()
        self.help_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        self.grid_columnconfigure(2, weight=1)

    def show_about(self):
        self.welcome_frame.grid_forget()
        self.TB_Frame.grid_forget()
        self.FW_Frame.grid_forget()
        self.DB_View_Frame.grid_forget()
        self.help_frame.grid_forget()
        self.about_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        self.grid_columnconfigure(2, weight=1)

    def show_data_layout(self):
        self.welcome_frame.grid_forget()
        self.FW_Frame.grid_forget()
        self.DB_View_Frame.grid_forget()
        self.help_frame.grid_forget()
        self.about_frame.grid_forget()
        self.TB_Frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        self.grid_columnconfigure(2, weight=1)

    def form_card(self):
        global Widget_names, ids, w_name
        Widget_names = {}
        def create_form_():
            self.show_editor_layout()

        # Clear existing widgets in window_frame to prevent duplicates
        for widget in self.window_frame.winfo_children():
            widget.destroy()

        crt_btn= ctk.CTkButton(self.window_frame, text="+ Create New Form", fg_color="green", text_color="white", command=create_form_)
        crt_btn.grid(row=0, column=0,padx=10, pady=10, sticky="ew")
        
        # Icon Path Fix
        try:
             icon_path = os.path.join(img, "form_card.webp")
             imagef = ctk.CTkImage(light_image=Image.open(icon_path),    
                                   dark_image=Image.open(icon_path),
                                   size=(80, 80)) 
        except Exception:
             imagef = None
        
        for _id, data in main_data.items():
            w_name = str(_id)
            self.nav_form = ctk.CTkFrame(self.window_frame, fg_color="#8E8FFA")
            self.nav_form.grid(row=_id+1, column=0, pady=10, padx=5, sticky='ew')
            
            Widget_names[w_name] = self.nav_form
            
            form_label = ctk.CTkLabel(self.nav_form, text=f"""{data["table_names"]}\n[{data["database_names"]}]""", text_color="white")
            form_label.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=5)
            
            fetch_img = ctk.CTkButton(self.nav_form, command=lambda _id=_id: self.fetch_main(_id), text=None, fg_color="#8E8FFA", image=imagef)
            fetch_img.image = imagef
            
            up_btn = ctk.CTkButton(self.nav_form, text="✏️", fg_color="orange", text_color="white", width=40,
                                   command=lambda _id=_id: self.update_form(_id))
            del_btn = ctk.CTkButton(self.nav_form, text="🗑️", fg_color="red", text_color="white", width=40,
                                    command=lambda _id=_id, data=data: self.delete_form(_id, data["table_names"], data["database_names"]))
            
            fetch_img.grid(row=1, columnspan=2, padx=2, pady=2)
            up_btn.grid(row=2, column=0, padx=5, pady=5)
            del_btn.grid(row=2, column=1, padx=5, pady=5)
            
            self.nav_form.columnconfigure(0, weight=1)
            self.nav_form.columnconfigure(1, weight=1)
            
    def delete_form(self, _id, table_name, db_name):
        from tkinter import messagebox
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete form '{table_name}'?\nThis will permanently delete the table and all its data."):
            try:
                # 1. Delete from metadata table (main.db)
                mcursor.execute("DELETE FROM main WHERE ID=?", (_id,))
                mconn.commit()
                
                # 2. Drop the actual data table (user's db)
                with get_db_connection(db_name) as temp_conn:
                     temp_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                     temp_conn.commit()
                     
                # 3. Refresh UI & Data
                global main_data
                main_data = fetch_all_data()
                self.form_card()
                
                if hasattr(self, 'current_view_id') and self.current_view_id == _id:
                    self.show_welcome()
                
                # print(f"Deleted form {_id}: {table_name}")

                # 4. Check if database is empty (no tables left in main_data for this db)
                tables_in_db = [d for d in main_data.values() if d['database_names'] == db_name]
                if not tables_in_db:
                    # Database is empty (in terms of registered tables)
                    # Check if db file exists and prompt to delete
                    db_path = os.path.join(dbsrc, f"{db_name}.db")
                    if os.path.exists(db_path):
                        if messagebox.askyesno("Delete Database?", f"Database '{db_name}' is now empty. Do you want to delete the database file?"):
                            try:
                                # Close any potential open connection to this DB to release file lock
                                try:
                                    if 'conn' in globals() and globals()['conn']:
                                        globals()['conn'].close()
                                except:
                                    pass

                                os.remove(db_path)
                                messagebox.showinfo("Deleted", f"Database file '{db_name}.db' deleted.")
                            except Exception as e:
                                messagebox.showerror("Error", f"Failed to delete database file: {e}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete form: {e}")
                # print(f"Delete failed: {e}")

    def update_form(self, _id):
        # Open Schema Editor
        def on_refresh():
            global main_data
            main_data = fetch_all_data()
            self.form_card()
            if hasattr(self, 'current_view_id') and self.current_view_id == _id:
                self.fetch_main(_id)
            
        SchemaEditor(self, _id, refresh_callback=on_refresh)
            
    def fetch_main(self, _id):
        self.current_view_id = _id
        current_data = main_data[_id]
        # self.TB_Frame.configure(label_text=f"Table: {current_data['table_names']}") # TB_Frame is no longer Scrollable with label
        self.show_data_layout()
        # print(f"{main_data[_id]}")
        current_data = main_data[_id]
        
        # We ensure FW frame is hidden but we might need to recreate FW object if it depends on data?
        # Actually Main passes current_conn info to TB.main_table.
        
        self.TB.main_table(current_data["database_names"], current_data["table_names"], current_data["fields"])
        
    # --- Robust Shutdown ---
    def on_closing(self):
        try:
            # 1. Close DB Connection if open
            try:
                if 'mconn' in globals() and globals()['mconn']:
                    globals()['mconn'].close()
                if 'conn' in globals() and globals()['conn']:
                    globals()['conn'].close()
            except: pass
            
            # 2. Stop Mainloop
            self.quit()
            
            # 3. Destroy Window
            self.destroy()
        except:
            pass
        finally:
            # 4. Force Exit Process to kill pending threads/callbacks
            import os
            os._exit(0)

    def switch_event(self):
        if self.appearance_mode_var.get() == "on":
            ctk.set_appearance_mode("Dark")
            self.switch.configure(text="Dark")
        else:
            ctk.set_appearance_mode("Light")
            self.switch.configure(text="Light")

    def __init__(self):
        super().__init__()
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        global main_data
        main_data = fetch_all_data()
        self.nav_form= None
        
        # Screen dimensions
        self.w = self.winfo_screenwidth()
        self.h = self.winfo_screenheight()
        
        self.title("Seven1Form")
        try:
            self.iconphoto(False, tk.PhotoImage(file=os.path.join(img, "sosubmit.png")))
        except Exception as e:
            # print(f"Error setting icon: {e}")
            pass
        
        # Fix geometry: 80% of screen size
        width = int(self.w * 0.8)
        height = int(self.h * 0.8)
        self.geometry(f"{width}x{height}")
        
        # onfiguration ---
        self.grid_rowconfigure(0, weight=1)
        # Col 0: NavBar
        # Col 1: Sidebar List (window_frame)
        # Col 2: Main Content Area (Stack of Welcome, Editor, Data)
        
        self.grid_columnconfigure(0, weight=0, minsize=80) 
        self.grid_columnconfigure(1, weight=0) # Sidebar Hidden initially
        self.grid_columnconfigure(2, weight=1) # Main Content
        
        # --- Navigation Bar ---
        navBG = "#6495ed"
        self.NavBar_frame = ctk.CTkFrame(self, fg_color=navBG, width=80, corner_radius=0)
        self.NavBar_frame.grid(row=0, column=0, sticky="nsew")
        self.NavBar_frame.grid_columnconfigure(0, weight=1)
        self.NavBar_frame.grid_rowconfigure(5, weight=1) # Push bottom elements down

        
        # Navigation Buttons
        img_hw=45
        filename_d = ["form_d.png", "database_d.png", "help_d.png", "about_d.png"]
        filename_l = ["form_l.png", "database_l.png", "help_l.png", "about_l.png"]
        
        def create_nav_btn(icon_l, icon_d, cmd, y_pos):
            try:
                img_p = ctk.CTkImage(light_image=Image.open(os.path.join(img, icon_l)),
                                   dark_image=Image.open(os.path.join(img, icon_d)),
                                   size=(img_hw, img_hw))
            except: img_p = None
            
            btn = ctk.CTkButton(self.NavBar_frame, width=img_hw, height=img_hw, text="", 
                                image=img_p, fg_color="transparent", hover_color="lightblue", 
                                command=cmd)
            btn.image = img_p
            btn.grid(row=y_pos, column=0, pady=15, padx=10)
            
        create_nav_btn(filename_l[0], filename_d[0], lambda: self.toggle_form(), 0)
        create_nav_btn(filename_l[1], filename_d[1], lambda: self.show_databases(), 1)
        create_nav_btn(filename_l[2], filename_d[2], lambda: self.show_help(), 2)
        create_nav_btn(filename_l[3], filename_d[3], lambda: self.show_about(), 3)
        
        # Appearance Mode Switch
        self.appearance_mode_var = ctk.StringVar(value="on") # Default Dark
        self.switch = ctk.CTkSwitch(self.NavBar_frame, text="Dark", command=self.switch_event,
                                    variable=self.appearance_mode_var, onvalue="on", offvalue="off",
                                    width=40, height=20, font=("Arial", 10), text_color="white")
        self.switch.grid(row=6, column=0, padx=10, pady=20, sticky="s")

        # --- Sidebar List (window_frame) ---
        self.window_frame = ctk.CTkScrollableFrame(self, fg_color="skyblue", label_text="Forms")
        
        # --- Help Page ---
        self.help_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", label_text="Help & Instructions")
        
        help_text = """
        Welcome to SoSubmit Help!

        1. Navigation & Appearance:
           - Sidebar: Switch between Forms, Databases, Help, and About.
           - Dark/Light Mode: Use the toggle switch at the bottom of the sidebar to change the theme.

        2. Forms & Data Management:
           - Create New Form: Click '+ Create New Form', enter details, and define fields.
           - View Data: Click a form card in the sidebar to open its table.
           - Add/Edit Data: Use 'Add Row' or 'Edit Row' buttons.
           - Delete Data: Select a row and click 'Delete Row'.
           - Keyboard Shortcuts: Press Enter on the last field to auto-submit.

        3. Analysis & Visualization:
           - Click 'Analyze' in the table view to open the Analysis Window.
           - Creating Charts: Select a Chart Type (Bar, Line, Scatter, Pie), then choose X and Y axes.
           - Visualizing Data: Gain insights from your data through dynamic charts.

        4. Database Management (DB Tab):
           - Click the Database icon in the sidebar.
           - View all raw SQLite tables stored in the system.
           - Useful for verifying data integrity or viewing internal structure.

        5. Exporting Data:
           - Export All: Click 'Export' -> 'All Data' to save the entire table to Excel.
           - Export Selected: Highlight specific rows, then click 'Export' -> 'Selected Rows' to save only the selection.
        """
        
        ctk.CTkLabel(self.help_frame, text=help_text, justify="left", font=("Arial", 14), anchor="w").pack(padx=20, pady=10, fill="x")
        
        # --- About Page ---
        self.about_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", label_text="About")
        
        # --- Software Info ---
        ctk.CTkLabel(self.about_frame, text="SoSubmit", font=("Arial", 32, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self.about_frame, text=f"v{__version__}", font=("Arial", 14), text_color="gray").pack(pady=(0, 10))
        
        try:
            sw_icon_path = os.path.join(img, "sosubmit.png")
            if os.path.exists(sw_icon_path):
                sw_img = ctk.CTkImage(light_image=Image.open(sw_icon_path),
                                      dark_image=Image.open(sw_icon_path),
                                      size=(120, 120))
                ctk.CTkLabel(self.about_frame, text="", image=sw_img).pack(pady=10)
        except Exception as e:
            # print(f"Error loading SW icon: {e}")
            pass

        sw_desc = """
        S.O. means not only Seven One, But also:
        • Streamline Operations
        • Smart Organizer
        • Secure Output
        • Speedy Operations
        • Seamless Organization
        """
        ctk.CTkLabel(self.about_frame, text=sw_desc, font=("Arial", 14), justify="center").pack(pady=10)
        
        # Separator (Visual)
        ctk.CTkLabel(self.about_frame, text="__________________________________________________", text_color="gray").pack(pady=10)

        # --- Developer Info ---
        ctk.CTkLabel(self.about_frame, text="Developer Profile", font=("Arial", 20, "bold")).pack(pady=(20, 10))

        # Profile Image
        try:
            profile_path = os.path.join(img, "profile.jpeg")
            if os.path.exists(profile_path):
                prof_img = ctk.CTkImage(light_image=Image.open(profile_path), 
                                      dark_image=Image.open(profile_path),
                                      size=(120, 120))
                ctk.CTkLabel(self.about_frame, text="", image=prof_img).pack(pady=10)
        except Exception as e:
            ctk.CTkLabel(self.about_frame, text="[Profile Image]").pack(pady=10)

        # Name & Title
        ctk.CTkLabel(self.about_frame, text="Shaikh Ahemad", font=("Arial", 24, "bold")).pack(pady=5)
        ctk.CTkLabel(self.about_frame, text="Developer & SAP ABAP Consultant", font=("Arial", 16, "italic"), text_color="gray").pack(pady=(0, 20))
        
        # Bio
        bio_text = """
        Passionate programming enthusiast with skills in Python, SQL, JavaScript, SAP ABAP and more. 
        Interested in exploring new technologies, contributing to open-source, 
        and solving challenging problems in Computer Science.
        
        Education: BSc in CS, Electronics & Physics (SRTMUN).
        """
        ctk.CTkLabel(self.about_frame, text=bio_text, font=("Arial", 14), justify="center").pack(padx=40, pady=10)
        
        # GitHub Button
        def open_github():
            webbrowser.open("https://github.com/shaikhahemad")
            
        ctk.CTkButton(self.about_frame, text="Visit GitHub Profile", command=open_github, fg_color="#333", hover_color="#555").pack(pady=20)

        # --- Welcome Page ---
        self.welcome_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkLabel(self.welcome_frame, text="Welcome to SoSubmit", font=("Arial", 36, "bold")).pack(expand=True, pady=(100,20))
        ctk.CTkLabel(self.welcome_frame, text="Select a form from the sidebar to view data\nor create a new form to get started.", font=("Arial", 16)).pack(pady=10)

        # --- Form Editor Window (FW_Frame) ---
        self.FW_Frame = ctk.CTkScrollableFrame(self, fg_color=("white", "grey"), label_text="Editor")
        self.FW = Form_Window(self.FW_Frame, main_app=self)
        
        # --- Table View Window (TB_Frame) ---
        # --- Table View Window (TB_Frame) ---
        self.TB_Frame = ctk.CTkFrame(self, fg_color="transparent") # Changed to standard Frame
        self.TB = Table_Window(self.TB_Frame)
        
        # --- Database View Frame ---
        self.DB_View_Frame = ctk.CTkScrollableFrame(self, fg_color="transparent", label_text="Databases")
        self.DB_View_Frame.grid_columnconfigure(0, weight=1)

        self.is_window_visible = True # Sidebar is visible by default
        self.window_frame.grid(row=0, column=1, sticky="nsew", padx=2)
        self.grid_columnconfigure(1, weight=0, minsize=250)
        self.form_card()
        self.show_welcome()
if __name__ == "__main__":
  app = Main()
  app.mainloop()