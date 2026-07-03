# 🏪 Canteen Inventory Management System

A data-driven desktop dashboard designed to automate canteen inventory control, track sales transactions, manage supplier logs, and monitor stock lifecycles in real-time. 

This application bridges the gap between a robust relational database engine (**Microsoft SQL Server**) and an intuitive data visualization front-end (**Python & Streamlit**), replacing manual spreadsheets with automated reorder workflows.

---

## 🛠️ Tech Stack & Dependencies

* **Frontend Dashboard:** Python (Streamlit, Plotly Express)
* **Database Infrastructure:** Microsoft SQL Server (SSMS)
* **Database Driver:** `pyodbc` (with Pandas for SQL-to-DataFrame parsing)
* **Automation:** Windows Batch Scripting (`RunApp.bat`)

---

## 🚀 Core Features

* **📊 Real-Time Operations Metrics:** Dynamic high-level cards showing total product variations, total stock valuation, low-stock alerts, and active suppliers.
* **📈 Transaction & Revenue Tracking:** Dedicated ledgers for sales entries that automatically adjust physical stock levels and generate 30-day moving revenue insights.
* **🔄 Inventory Flow Control:** Dual-action tracking for stock updates, managing inbound shipments (`IN`) and outbound waste/damage adjustments (`OUT`).
* **🚨 Procurement Forecasting:** An automated reorder tool that lists items below safety levels, displays corresponding vendor contact details, and calculates target restocking quantities.

---

## 📦 Local Installation & Setup Guide

### Prerequisites
1. **Python 3.9+** installed on your machine.
2. **Microsoft SQL Server & SSMS** running locally.
3. **ODBC Driver 17 for SQL Server** installed (Required for Python to communicate with your database).

### 1. Database Initialization
1. Launch **SQL Server Management Studio (SSMS)**.
2. Execute the script found in `database/Canteen query.sql` (or run it via your query analyzer) to initialize the `CanteenDB` database structure, create the relational schemas (Suppliers, Products, Sales, StockMovements), and seed the sample data.

### 2. Environment Configuration
Ensure your libraries are installed by opening your command terminal and running:
```bash
pip install streamlit pandas pyodbc plotly
