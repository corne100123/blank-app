import sqlite3
import pandas as pd
import datetime
from config import get_default_db_path

# 1. SETUP: Create the new Database
conn = sqlite3.connect(get_default_db_path())
cursor = conn.cursor()

# Create Clients Table (No changes here)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients (
        client_id INTEGER PRIMARY KEY,
        surname TEXT,
        initials TEXT,
        id_number TEXT,
        gender TEXT,
        phone_cell TEXT,
        phone_work TEXT,
        phone_home TEXT,
        employer TEXT,
        address TEXT,
        area TEXT,
        status TEXT
    )
''')

# Create Loans Table (UPDATED with 'loan_amount' and 'status')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER,
        due_date TEXT,
        loan_amount REAL,     -- New Column: Original Principal
        amount_owe REAL,      -- Current Total Due
        amount_paid REAL,
        balance REAL,
        status TEXT,          -- New Column: From the "S" header
        FOREIGN KEY(client_id) REFERENCES clients(client_id)
    )
''')

print("Database structure created successfully.")

# 2. IMPORT: Read your Excel files
try:
    # Load the Client List (Zero Balance Sheet)
    df_clients = pd.read_excel("client_list.xlsx", dtype=str)
    
    # Load the Active Loans (Active List)
    df_loans = pd.read_excel("active_loans.xlsx", dtype=str)

    print("Excel files loaded. Starting migration...")

    # 3. MIGRATE CLIENTS
    for index, row in df_clients.iterrows():
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO clients (client_id, surname, initials, id_number, gender, phone_cell, employer, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('Client No'), 
                row.get('Surname'), 
                row.get('Initials'), 
                row.get('Identity No'), 
                row.get('Gender'), 
                row.get('Cell No'), 
                row.get('Employers Name'), 
                row.get('Status')
            ))
        except Exception as e:
            print(f"Error adding client {row.get('Client No')}: {e}")

    # 4. MIGRATE ACTIVE LOANS (UPDATED)
    for index, row in df_loans.iterrows():
        # Update client address/details from active list
        cursor.execute('''
            UPDATE clients SET address = ?, area = ?, phone_work = ? 
            WHERE client_id = ?
        ''', (
            row.get('Address'), 
            row.get('Area'), 
            row.get('Work Phone'), 
            row.get('Client No')
        ))

        # Insert the Loan with the new columns
        # IMPORTANT: Make sure your Excel header for Loan Amount matches 'Loan Amount' below
        cursor.execute('''
            INSERT INTO loans (client_id, due_date, loan_amount, amount_owe, amount_paid, balance, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            row.get('Client No'),
            row.get('Due Date'),
            row.get('Loan Amount'),  # Needs to match your Excel Header!
            row.get('owe'),
            row.get('payd'),
            row.get('balance'),
            row.get('S')             # Mapping column "S" to Status
        ))

    conn.commit()
    print(f"Migration Complete! Your data is now in '{get_default_db_path()}'")

except FileNotFoundError:
    print("WARNING: Could not find 'client_list.xlsx' or 'active_loans.xlsx'. Please create them first.")
except Exception as e:
    print(f"An error occurred: {e}")

conn.close()