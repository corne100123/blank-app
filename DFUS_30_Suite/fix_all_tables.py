import sqlite3
import os

# Pointing to your specific database location
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "NewLoanManager.db")

def run_fix():
    print(f"🔧 Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # --- 1. FIX LOANS TABLE (Often missing 'due_date' or 'status') ---
    print("Checking 'loans' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            principal REAL,
            balance REAL,
            status TEXT,
            due_date DATE
        )
    """)
    
    # Attempt to add columns that might be missing
    columns_to_add = ["due_date DATE", "status TEXT DEFAULT 'Active'", "balance REAL", "principal REAL"]
    
    for col in columns_to_add:
        try:
            # We try to add the column. If it exists, this fails silently.
            col_name = col.split()[0]
            cursor.execute(f"ALTER TABLE loans ADD COLUMN {col}")
            print(f"   -> Added missing column: {col_name}")
        except:
            pass # Column already exists, skip it.

    # --- 2. FIX PAYMENTS TABLE (Likely missing entirely) ---
    print("Checking 'payment_history' table...")
    # This table is required for the Dashboard. If missing, Dashboard crashes.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_history (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER,
            amount REAL,
            date_paid DATE,
            method TEXT
        )
    """)
    print("   -> Payment table verified.")

    # --- 3. FIX CLIENTS TABLE (Double check) ---
    print("Checking 'clients' table...")
    client_cols = ["total_gross REAL", "employer TEXT", "bank_name TEXT"]
    for col in client_cols:
        try:
            col_name = col.split()[0]
            cursor.execute(f"ALTER TABLE clients ADD COLUMN {col}")
            print(f"   -> Added missing column: {col_name}")
        except:
            pass

    conn.commit()
    conn.close()
    print("\n✅ REPAIR COMPLETE. All tables should now match the code.")

if __name__ == "__main__":
    run_fix()