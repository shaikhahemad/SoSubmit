# SOSubmit
 
****S. O. meane not only Seven One, But also****
- **Streamline Operations**
- **Smart Organizer**
- **Secure Output**
- **Speedy Operations**
- **Seamless Organization**

<hr>

## Features

### 1. Dynamic Form Creation
- Create custom forms with user-defined fields.
- Supports multiple data types: Text, Numeric, Date, Datetime, Timestamp, and Boolean.
- **Custom Boolean Labels**: Customize "True" and "False" values (e.g., "Active/Inactive", "Yes/No").
- **Strict Validation**: 
  - Identifiers (Database, Table, Field names) must start with a letter and contain only alphanumeric characters or underscores.
  - Prevents SQL Injection and ensures data integrity.

### 2. Data Entry & Management
- User-friendly data entry forms generated automatically from your schema.
- **Smart Inputs**: 
  - Boolean fields rendered as Radio Buttons with custom labels.
  - Date pickers for date fields (planned).
- **Data Validation**: 
  - Prevents entering text in numeric fields.
  - Checks for duplicate entries where applicable.

### 3. Table View & Editing
- View data in a responsive table layout.
- **Inline Editing**: Double-click or select rows to edit data easily.
- **Data Integrity**: 
  - Boolean values displayed as their custom labels (e.g., "Active" instead of "1").
- **Export**: Export data to Excel (.xlsx) or CSV formats. Choose to export all data or only selected rows.

### 4. Data Analysis
- Built-in charting tool to visualize your data.
- Supports Bar, Line, Scatter, and Pie charts.
- customizable X and Y axes based on your form fields.

### 5. Database Management
- Create and manage multiple SQLite databases within the app.
- Delete forms and databases with safety checks.

<hr>

## Technologies Used
- *Python Programming*
- *Tkinter [GUI]*
- *CustomeTkinter*
- *SQLite3 [Database]*
- *Pandas*
- *OpenPyXL*

<hr>

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/shaikhahemad/SOSubmit
    ```

2. Install dependencies:
   ```bash
   cd SOSubmit
   ```
    ```bash
   pip install -r requirements.txt
    ```
<hr>

## Usage

  ```bash
   python src/main.py
  ```
or
  ```bash
   python3 src/main.py
  ```

<hr>