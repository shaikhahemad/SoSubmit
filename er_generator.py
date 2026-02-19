
import os
import json
import sqlite3
import webbrowser

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Check standard location first
DB_DIR = os.path.join(BASE_DIR, ".db")
MAIN_DB_PATH = os.path.join(DB_DIR, "main.db")

# Fallback to dist if empty (common when using PyInstaller)
if not os.path.exists(MAIN_DB_PATH) or os.path.getsize(MAIN_DB_PATH) < 20000: # Heuristic
    possible_dist = os.path.join(BASE_DIR, "dist", "sosubmit", ".db", "main.db") # Example path
    # We will search for it dynamically in the script if needed
    pass

def fetch_all_data():
    """
    Fetches schema metadata from main.db.
    Replicates logic from main.py to be standalone.
    """
    if not os.path.exists(MAIN_DB_PATH):
        print(f"Error: Database not found at {MAIN_DB_PATH}")
        return {}

    try:
        conn = sqlite3.connect(MAIN_DB_PATH)
        cursor = conn.cursor()
        
        # Ensure schema is roughly what we expect
        cursor.execute("PRAGMA table_info(main)")
        columns = [info[1] for info in cursor.fetchall()]
        
        query = 'SELECT ID, database_names, table_names, fields, data_types FROM main'
        # Adjust query if fields are missing (basic compatibility)
        cursor.execute(query)
        rows = cursor.fetchall()
        
        main_data = {}
        for row in rows:
            ID, database_names, table_names, fields_json, data_types_json = row
            
            try:
                fields = json.loads(fields_json)
                data_types = json.loads(data_types_json)
            except json.JSONDecodeError:
                # Fallback or skip
                continue
                
            main_data[ID] = {
                'database_names': database_names,
                'table_names': table_names,
                'fields': fields,
                'data_types': data_types
            }
            
        conn.close()
        return main_data
        
    except Exception as e:
        print(f"Error reading database: {e}")
        return {}

def extract_schema_for_db(db_name, main_data):
    """
    Extracts table and field information for a specific database from main_data.
    """
    schema = []
    for data in main_data.values():
        if data['database_names'] == db_name:
            schema.append({
                'table': data['table_names'],
                'fields': data['fields'],
                'types': data['data_types']
            })
    return schema

def generate_mermaid_code(db_name, schema):
    """
    Generates Mermaid.js ER diagram syntax from the schema.
    """
    mermaid_lines = ["erDiagram"]
    
    table_names = {item['table'] for item in schema}
    
    for item in schema:
        table = item['table']
        fields = item['fields']
        types = item['types']
        
        mermaid_lines.append(f"    {table} {{")
        for f_name, f_type in zip(fields, types):
            safe_type = f_type.replace(" ", "_")
            mermaid_lines.append(f"        {safe_type} {f_name}")
        mermaid_lines.append("    }")
        
        # Infer Relationships (field_id -> field table)
        for f_name in fields:
            if f_name.endswith("_id") and f_name != "id":
                target_table = f_name[:-3]
                if target_table in table_names:
                    mermaid_lines.append(f"    {target_table} ||--o{{ {table} : \"has\"")
                    
    return "\n".join(mermaid_lines)

def generate_html_content(mermaid_code, db_name):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ER Diagram - {db_name}</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true }});
    </script>
    <style>
        body {{ font-family: sans-serif; padding: 20px; display: flex; flex-direction: column; align-items: center; background-color: #f4f4f4; }}
        h1 {{ color: #333; }}
        .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 80%; }}
        .mermaid {{ display: flex; justify-content: center; }}
    </style>
</head>
<body>
    <h1>Database Schema: {db_name}</h1>
    <div class="container">
        <div class="mermaid">
{mermaid_code}
        </div>
    </div>
</body>
</html>"""

def fetch_system_schema():
    """
    Fetches the schema of the internal tables in main.db
    (e.g. 'main' table itself).
    """
    if not os.path.exists(MAIN_DB_PATH):
        return []
        
    try:
        conn = sqlite3.connect(MAIN_DB_PATH)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [r[0] for r in cursor.fetchall()]
        
        schema = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall() # cid, name, type, notnull, dflt_value, pk
            
            fields = [col[1] for col in columns]
            types = [col[2] for col in columns]
            
            schema.append({
                'table': table,
                'fields': fields,
                'types': types
            })
            
        conn.close()
        return schema
        
    except Exception as e:
        print(f"Error fetching system schema: {e}")
        return []

def main():
    print("--- SoSubmit ER Diagram Generator ---")
    data = fetch_all_data()
    
    # Check if we have user data
    has_user_data = bool(data)
    
    selected_db_name = None
    schema_to_draw = []

    if has_user_data:
        # Find unique databases
        databases = sorted(list(set(d['database_names'] for d in data.values())))
        
        print(f"Found {len(databases)} user-defined database(s):")
        for idx, db in enumerate(databases):
            print(f"{idx + 1}. {db}")
            
        print(f"{len(databases) + 1}. [Internal System Schema] (main.db structure)")
            
        choice = input(f"\nEnter number (1-{len(databases)+1}) or 'all': ").strip()
        
        selected_dbs = []
        if choice.lower() == 'all':
            selected_dbs = databases
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(databases):
                selected_dbs = [databases[idx]]
            elif idx == len(databases):
                # System Schema
                selected_dbs = ["__SYSTEM__"]
            else:
                print("Invalid selection.")
                return
        else:
             if choice in databases:
                selected_dbs = [choice]
             else:
                print("Invalid selection.")
                return
                
        # Generate
        for db in selected_dbs:
            if db == "__SYSTEM__":
                print("Generating diagram for Internal System Schema...")
                schema = fetch_system_schema()
                db_label = "SoSubmit_Internal"
            else:
                print(f"Generating diagram for '{db}'...")
                schema = extract_schema_for_db(db, data)
                db_label = db

            if not schema:
                print(f"Skipping {db_label}: No tables found.")
                continue
                
            code = generate_mermaid_code(db_label, schema)
            html = generate_html_content(code, db_label)
            
            filename = f"ER_Diagram_{db_label}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
                
            print(f"Saved: {filename}")
            webbrowser.open('file://' + os.path.realpath(filename))

    else:
        print("\nNo user-defined databases found (main.db is empty of user metadata).")
        print("Required: Create a form in the SoSubmit app first to generate user schemas.")
        
        choice = input("Would you like to generate the Internal System Schema instead? (Y/n): ").strip().lower()
        if choice in ['y', 'yes', '']:
            print("Generating diagram for Internal System Schema...")
            schema = fetch_system_schema()
            
            if not schema:
                 print("Error: Could not read internal schema either.")
                 return
                 
            db_label = "SoSubmit_Internal"
            code = generate_mermaid_code(db_label, schema)
            html = generate_html_content(code, db_label)
            
            filename = f"ER_Diagram_{db_label}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
                
            print(f"Saved: {filename}")
            webbrowser.open('file://' + os.path.realpath(filename))
        else:
            print("Exiting.")


if __name__ == "__main__":
    main()

