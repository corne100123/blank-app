import sqlite3

db_path = r"D:\DFUS_30_Suite\NewLoanManager.db"

def run_fix():
    print(f"🔧 Connecting to {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. FIX CLIENTS TABLE
        print("Checking 'clients' table...")
        # Create table if it doesn't exist at all
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
        
        # List of columns we expect to have now
        expected_columns = [
            ("total_gross", "REAL DEFAULT 0.0"),
            ("salary", "REAL DEFAULT 0.0"),  # Keeping both for safety
            ("employer", "TEXT"),
            ("bank_name", "TEXT"),
            ("account_no", "TEXT")
        ]

        # Get current columns
        cursor.execute("PRAGMA table_info(clients)")
        existing_cols = [row[1] for row in cursor.fetchall()]

        for col_name, col_type in expected_columns:
            if col_name not in existing_cols:
                print(f"   -> Adding missing column: {col_name}")
                try:
                    cursor.execute(f"ALTER TABLE clients ADD COLUMN {col_name} {col_type}")
                except Exception as e:
                    print(f"      Warning: Could not add {col_name} ({e})")
            else:
                print(f"   -> {col_name} exists.")

        # 2. FIX LOANS TABLE
        print("\nChecking 'loans' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                principal REAL,
                balance REAL,
                status TEXT,
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(client_id)
            )
        """)
        print("   -> Loans table verified.")

        conn.commit()
        conn.close()
        print("\n✅ SUCCESS! Database is now compatible with the new tools.")
        print("👉 You can now restart Streamlit.")
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")

if __name__ == "__main__":
    run_fix()