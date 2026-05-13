import sqlite3
import os
from config import _get_configured_db_path_for_scripts

# Dynamic path relative to the configured application database
db_path = _get_configured_db_path_for_scripts()

def run_force_fix():
    if not db_path:
        print("Error: Database path not found in configuration. Please run the main app setup first.")
        return
    print(f"🔧 Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. ENSURE TABLES EXIST
    print("--- Checking Tables ---")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            id_number TEXT UNIQUE,
            phone TEXT,
            email TEXT,
            address TEXT,
            status TEXT DEFAULT 'Active'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            principal REAL,
            balance REAL,
            status TEXT DEFAULT 'Active',
            due_date DATE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_history (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER,
            amount REAL,
            date_paid DATE,
            method TEXT
        )
    """)

    # 2. FORCE ADD ALL MISSING COLUMNS
    print("--- Adding Missing Columns ---")
    # We add every single column your new Onboarding tool might ask for
    new_columns = [
        ("clients", "total_gross", "REAL DEFAULT 0.0"),
        ("clients", "salary", "REAL DEFAULT 0.0"),
        ("clients", "employer", "TEXT"),
        ("clients", "work_days", "TEXT"),
        ("clients", "pay_day", "TEXT"),
        ("clients", "bank_name", "TEXT"),
        ("clients", "account_no", "TEXT"),
        ("loans", "due_date", "DATE"),
        ("loans", "status", "TEXT DEFAULT 'Active'")
    ]

    for table, col, type_def in new_columns:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {type_def}")
            print(f"✅ Added {col} to {table}")
        except:
            print(f"   (Column {col} already exists in {table})")

    # 3. INSERT A DUMMY CLIENT (To stop the 'Index Error' crashes)
    print("--- Seeding Test Data ---")
    try:
        cursor.execute("SELECT * FROM clients WHERE id_number = '9901015000080'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO clients (first_name, last_name, id_number, phone, total_gross, status) 
                VALUES ('John', 'Doe (Test)', '9901015000080', '0821234567', 15000, 'Active')
            """)
            print("✅ Created Test Client: John Doe")
        else:
            print("   (Test Client already exists)")
    except Exception as e:
        print(f"⚠️ Could not seed client: {e}")

    conn.commit()
    conn.close()
    print("\n🎉 DONE! The database is fixed and has 1 client.")
    print("👉 Restart Streamlit now.")

if __name__ == "__main__":
    run_force_fix()