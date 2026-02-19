# 📋 SoSubmit - Smart Form & Data Management

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=for-the-badge&logo=windows)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**SoSubmit** is a powerful, desktop-based data management application designed to streamline operations. It allows you to create dynamic forms, manage databases, visualize data, and generate schema diagrams—all in a modern, user-friendly interface.

---

## 🚀 Key Features

### 🎨 Modern UI & Experience
- **Dark/Light Mode**: Toggle between themes for a comfortable viewing experience.
- **Custom Date Picker**: Intuitive calendar popup for date fields.
- **Responsive Design**: Clean layout with a collapsible sidebar and smooth navigation.

### 📝 Dynamic Forms
- **Custom Fields**: Create tables with Text, Numeric, Boolean, Date, DateTime, and Timestamp fields.
- **Smart Booleans**: Define custom labels for True/False (e.g., "Active/Inactive", "Yes/No").
- **Auto-Timestamps**: `TIMESTAMP` and `DATETIME` fields automatically capture the submission time.
- **Validation**: Built-in strict validation to ensure data integrity and prevent SQL injection.

### 📊 Data Management & Analysis
- **Table View**: View, edit, and delete records in a responsive grid.
- **Data Analysis**: Built-in charting tool to visualize data with Bar, Line, Scatter, and Pie charts.
- **Excel Export**: Export your entire dataset or selected rows to Excel (`.xlsx`) with a single click.
- **ER Diagrams**: Generate Entity-Relationship (ER) diagrams to visualize your database structure.

### 🛠️ Advanced Tools
- **Database Manager**: View and manage multiple internal SQLite databases.
- **Secure**: Application signed with version metadata to ensure authenticity.

---

## 🛠️ Technology Stack

- **Language**: Python 3.10+
- **GUI Framework**: CustomTkinter types (Modern Tkinter)
- **Database**: SQLite3
- **Data Processing**: Pandas, OpenPyXL
- **Visualization**: Matplotlib
- **Packaging**: PyInstaller, Inno Setup

---

## 📦 Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/shaikhahemad/SoSubmit.git
    cd SoSubmit
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**:
    ```bash
    python main.py
    ```

---

## 📖 Usage Guide

1.  **Create a Form**:
    - Click **"+ Create New Form"** in the sidebar.
    - Enter a Database Name and Table Name.
    - Define your fields and their types (Text, Numeric, Date, Boolean, etc.).
    - Click **"Submit Schema"** to generate the form.

2.  **Add Data**:
    - Navigate to your new form via the sidebar.
    - Click **"Add Row"** to open the entry form.
    - Fill in the details (Date fields have a picker, Booleans use radio buttons).
    - Press **Enter** on the last field to quick-submit!

3.  **Analyze Data**:
    - In the table view, click **"Analyze"**.
    - Select a Chart Type and choose your X/Y axes to visualize trends.

4.  **Export**:
    - Select rows (or select none for all) and click **"Export"** to save as Excel.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 👤 Author

**Shaikh Ahemad**
- **Role**: Developer & SAP ABAP Consultant
- **Website**: [shaikhahemad.github.io](https://shaikhahemad.github.io/mywebsite/)

---

*“S.O. means not only Seven One, but also Streamline Operations, Smart Organizer, Secure Output, Speedy Operations, and Seamless Organization.”*
