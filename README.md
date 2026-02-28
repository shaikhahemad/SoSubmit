<div align="center">

<img src="assets/img/logo.png" alt="SoSubmit Logo" width="120" />

# 📋 SoSubmit

### Smart Form & Data Management — Simplified.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=for-the-badge&logo=windows)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v1.1.1-orange?style=for-the-badge)](https://github.com/shaikhahemad/SoSubmit/releases/tag/v1.1.1)
[![Stars](https://img.shields.io/github/stars/shaikhahemad/SoSubmit?style=for-the-badge&color=yellow)](https://github.com/shaikhahemad/SoSubmit/stargazers)

**SoSubmit** is a powerful, offline-first desktop application for building custom databases, managing records, analyzing data, and exporting reports — all through an elegant, no-code interface. No SQL knowledge required. No cloud dependency. Just pure productivity on your machine.

[🚀 Get Started](#-installation) · [📖 Usage Guide](#-usage-guide) · [✨ Features](#-features) · [🛠️ Tech Stack](#%EF%B8%8F-technology-stack) · [🤝 Contributing](#-contributing)

---

</div>

## 🌟 What is SoSubmit?

SoSubmit is a **desktop-based data management suite** that bridges the gap between simple spreadsheets and complex database tools. Whether you're a business professional managing operational data, a consultant tracking client records, or a hobbyist organizing a personal collection — SoSubmit gives you the power of a relational database with the ease of a form builder.

You design the structure. SoSubmit handles the rest.

> 💡 **S.O.** doesn't just stand for one thing — it means *Streamline Operations*, *Smart Organizer*, *Secure Output*, *Speedy Operations*, and *Seamless Organization*. All at once.

---

## ✨ Features

### 🎨 Modern UI & User Experience

| Feature | Description |
|---|---|
| **Dark / Light Mode** | Toggle between themes to suit your environment or preference |
| **Collapsible Sidebar** | Navigate between your forms and databases with a clean, space-efficient sidebar |
| **Custom Date Picker** | An intuitive calendar popup for any date-type field — no manual typing |
| **Keyboard Shortcuts** | Press `Enter` on the last field to instantly submit a record |
| **Responsive Layout** | UI adapts cleanly regardless of window size |

---

### 📝 Dynamic Form Builder

This is the heart of SoSubmit. You define your schema; the app builds the form and database table for you.

**Supported Field Types:**

| Type | Behavior |
|---|---|
| `Text` | Standard string input with length validation |
| `Numeric` | Accepts integers and decimals; rejects non-numeric input |
| `Boolean` | Rendered as radio buttons with customizable True/False labels (e.g., "Active / Inactive", "Yes / No") |
| `Date` | Calendar popup picker; stored in `YYYY-MM-DD` format |
| `DateTime` | Combines date picker with time input; stored in `YYYY-MM-DD HH:MM:SS` |
| `Timestamp` | Automatically captures the exact date and time of submission — no manual input required |

**Schema Design highlights:**
- Name your database and table independently for clean multi-table setups
- Add, reorder, and remove fields before finalizing the schema
- Submit Schema to generate both the SQLite table and the live data-entry form in one click

---

### 📊 Data Management & Table View

Once data is entered, every form has a **Table View** that acts as your live data grid:

- View all records in a clean, scrollable table
- **Edit** any record inline with the same validated form
- **Delete** individual records with a confirmation prompt
- **Search / Filter** records to find what you need fast
- Column headers are auto-generated from your field definitions

---

### 📈 Data Analysis & Visualization

SoSubmit includes a built-in charting tool — no third-party software needed.

**Available Chart Types:**
- 📊 **Bar Chart** — Compare quantities across categories
- 📉 **Line Chart** — Track trends over time
- 🔵 **Scatter Plot** — Spot correlations between two numeric fields
- 🥧 **Pie Chart** — See proportional breakdowns at a glance

**How it works:**
1. Open any table and click **"Analyze"**
2. Select your Chart Type
3. Choose your X and Y axes from a dropdown of your field names
4. The chart renders instantly in a dedicated window

---

### 📤 Excel Export

Export your data to industry-standard `.xlsx` files in seconds:

- Export **all records** or only **selected rows**
- Output file is fully formatted and ready to share
- Powered by **OpenPyXL** for reliable Excel compatibility

---

### 🛠️ Database Manager

A built-in utility panel to manage your SQLite databases:

- View all databases created within SoSubmit
- See tables and record counts at a glance
- Switch between databases without restarting the app

---

### 🔐 Security & Validation

SoSubmit takes data integrity seriously:

- **SQL Injection Prevention**: All user inputs are parameterized before hitting the database
- **Strict Type Validation**: Numeric fields reject text; date fields enforce format correctness
- **Version Signing**: The compiled executable embeds version metadata for authenticity verification
- **Local Storage Only**: All your data stays on your machine — nothing is sent over a network

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.10+ | Core application logic |
| GUI Framework | CustomTkinter | Modern, styled desktop UI |
| Database | SQLite3 | Local, serverless data storage |
| Data Processing | Pandas | Record manipulation and filtering |
| Excel Export | OpenPyXL | `.xlsx` file generation |
| Visualization | Matplotlib | Charts and graphs |
| Packaging | PyInstaller | Compile to standalone `.exe` |
| Installer | Inno Setup | Windows installation wizard |

---

## 📁 Project Structure

```
SoSubmit/
│
├── main.py               # Core application — all UI, logic, and database operations
├── requirements.txt      # Python dependencies
├── run.bat               # One-click launcher for Windows (dev mode)
│
├── SoSubmit.spec         # PyInstaller build spec for compiling the .exe
├── setup.iss             # Inno Setup script for building the Windows installer
├── version_info.txt      # Version metadata embedded in the compiled executable
│
└── assets/
    └── img/              # UI icons, logos, and image assets
```

---

## 📦 Installation

### Option 1 — Windows Installer (Recommended)

Download the latest `.exe` installer from the [Releases Page](https://github.com/shaikhahemad/SoSubmit/releases/tag/v1.1.1).

Run the installer and follow the setup wizard. SoSubmit will be available from your Start Menu.

---

### Option 2 — Run from Source

**Prerequisites:** Python 3.10 or higher must be installed.

**Step 1 — Clone the repository:**
```bash
git clone https://github.com/shaikhahemad/SoSubmit.git
cd SoSubmit
```

**Step 2 — Install dependencies:**
```bash
pip install -r requirements.txt
```

**Step 3 — Launch the app:**
```bash
python main.py
```

Or on Windows, simply double-click `run.bat`.

---

### Option 3 — Build the Installer Yourself

To compile a standalone `.exe`:
```bash
pyinstaller SoSubmit.spec
```

To build the Windows installer (requires [Inno Setup](https://jrsoftware.org/isinfo.php)):
```
Open setup.iss in Inno Setup Compiler → Click Build
```

---

## 📖 Usage Guide

### 1. Creating a Form

1. Click **"+ Create New Form"** in the left sidebar
2. Enter a **Database Name** (the `.db` file name) and a **Table Name**
3. Add fields one by one — set the field name and select its type
4. For Boolean fields, optionally set custom labels for True and False
5. Click **"Submit Schema"** — your form is live instantly

---

### 2. Entering Data

1. Click your form name in the sidebar to open it
2. Click **"Add Row"** to open the data entry panel
3. Fill in each field (date pickers and radio buttons appear automatically for the right types)
4. Press **Enter** on the last field or click **"Submit"** to save the record

---

### 3. Editing and Deleting Records

1. In the Table View, click on any row to select it
2. Click **"Edit"** to open the record in the entry form with pre-filled values
3. Make your changes and submit to save
4. Click **"Delete"** to remove a record (a confirmation prompt will appear)

---

### 4. Analyzing Data

1. In any Table View, click **"Analyze"**
2. Select a **Chart Type** (Bar, Line, Scatter, or Pie)
3. Choose the **X Axis** and **Y Axis** from your field names
4. The chart renders in a new window — ready to screenshot or export

---

### 5. Exporting to Excel

1. In the Table View, optionally select specific rows (or select none for all)
2. Click **"Export"**
3. Choose a save location — your `.xlsx` file is generated immediately

---

## 🖥️ System Requirements

| Requirement | Minimum |
|---|---|
| OS | Windows 10 / 11 |
| Python | 3.10+ (source mode only) |
| RAM | 256 MB |
| Storage | ~50 MB (installer) |
| Display | 1280 × 720 or higher |

---

## 🗺️ Roadmap

Here are features planned or under consideration for future releases:

- [ ] **CSV Import** — Bulk-load data from existing spreadsheets
- [ ] **Relation Support** — Link tables together with foreign keys
- [ ] **PDF Report Export** — Generate printable reports from table data
- [ ] **Data Backup & Restore** — One-click database backup to a zip archive
- [ ] **macOS / Linux Support** — Cross-platform compatibility via packaging updates
- [ ] **Search & Advanced Filters** — Filter records by multiple conditions simultaneously
- [ ] **Field Reordering** — Drag-and-drop column arrangement in the table view

---

## 🐛 Known Issues & Troubleshooting

**App doesn't launch from source:**
Make sure all dependencies are installed (`pip install -r requirements.txt`) and you're using Python 3.10 or higher (`python --version`).

**Date picker not appearing:**
Ensure your system display scaling is set to 100% or 125%. Very high DPI scaling can occasionally affect popup positioning.

**Export file is empty:**
If you selected specific rows but the export is empty, try deselecting all rows and exporting again to get the full dataset.

**Database not showing in sidebar:**
Restart the app. New databases created outside of SoSubmit's interface may require a manual refresh.

---

## 🤝 Contributing

Contributions are warmly welcome! Here's how to get involved:

1. **Fork** the repository
2. Create your feature branch:
   ```bash
   git checkout -b feature/YourFeatureName
   ```
3. Make your changes and commit:
   ```bash
   git commit -m "Add: YourFeatureName"
   ```
4. Push to your branch:
   ```bash
   git push origin feature/YourFeatureName
   ```
5. Open a **Pull Request** with a clear description of what you've changed and why

Please keep code clean, commented where necessary, and consistent with the existing style.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details.

You are free to use, modify, and distribute this software with attribution.

---

## 👤 Author

**Shaikh Ahemad**
*Developer & SAP ABAP Consultant*

[![Website](https://img.shields.io/badge/Website-Visit-blue?style=flat-square&logo=google-chrome)](https://shaikhahemad.github.io/mywebsite/)
[![GitHub](https://img.shields.io/badge/GitHub-shaikhahemad-black?style=flat-square&logo=github)](https://github.com/shaikhahemad)

---

<div align="center">

**If SoSubmit made your work easier, consider giving it a ⭐ on GitHub — it means a lot!**

*"S.O. means not only Seven One, but also Streamline Operations, Smart Organizer, Secure Output, Speedy Operations, and Seamless Organization."*

</div>
