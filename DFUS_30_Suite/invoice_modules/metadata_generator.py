"""
Metadata Generator Module - Logic & Calculation Component
Handles invoice numbering, dates, and metadata generation
"""
import sqlite3
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class InvoiceMetadata:
    """Invoice metadata structure"""
    invoice_number: str = ""
    issue_date: str = ""
    due_date: str = ""
    status: str = "Draft"  # Draft, Sent, Paid, Overdue, Cancelled
    currency: str = "ZAR"
    payment_terms: str = "30 days"

class MetadataGenerator:
    """Generates invoice metadata including numbering and dates"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "invoice_metadata.db"

        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize metadata tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS invoice_numbers (
                    year INTEGER,
                    month INTEGER,
                    last_number INTEGER DEFAULT 0,
                    PRIMARY KEY (year, month)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS invoice_metadata (
                    invoice_number TEXT PRIMARY KEY,
                    issue_date TEXT,
                    due_date TEXT,
                    status TEXT DEFAULT 'Draft',
                    currency TEXT DEFAULT 'ZAR',
                    payment_terms TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def generate_invoice_number(self, prefix: str = "INV", year: int = None, month: int = None) -> str:
        """Generate unique invoice number with format: PREFIX-YYYY-NNN"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month

        with sqlite3.connect(self.db_path) as conn:
            # Get or create the counter for this year/month
            cursor = conn.execute("""
                SELECT last_number FROM invoice_numbers
                WHERE year = ? AND month = ?
            """, (year, month))

            row = cursor.fetchone()

            if row:
                next_number = row[0] + 1
                conn.execute("""
                    UPDATE invoice_numbers SET last_number = ?
                    WHERE year = ? AND month = ?
                """, (next_number, year, month))
            else:
                next_number = 1
                conn.execute("""
                    INSERT INTO invoice_numbers (year, month, last_number)
                    VALUES (?, ?, ?)
                """, (year, month, next_number))

            # Format: INV-2026-001
            return f"{prefix}-{year}-{next_number:03d}"

    def calculate_due_date(self, issue_date: str, payment_terms: str) -> str:
        """Calculate due date based on payment terms"""
        try:
            issue_dt = datetime.fromisoformat(issue_date)

            # Parse payment terms (e.g., "30 days", "Net 15", "End of month")
            terms_lower = payment_terms.lower().strip()

            if "days" in terms_lower:
                # Extract number of days
                days = int(''.join(filter(str.isdigit, terms_lower)))
                due_dt = issue_dt + timedelta(days=days)
            elif "net" in terms_lower:
                # Extract number after "net"
                days = int(''.join(filter(str.isdigit, terms_lower)))
                due_dt = issue_dt + timedelta(days=days)
            elif "end of month" in terms_lower:
                # Last day of the month
                if issue_dt.month == 12:
                    due_dt = issue_dt.replace(year=issue_dt.year + 1, month=1, day=31)
                else:
                    due_dt = issue_dt.replace(month=issue_dt.month + 1, day=1) - timedelta(days=1)
            else:
                # Default to 30 days
                due_dt = issue_dt + timedelta(days=30)

            return due_dt.date().isoformat()

        except (ValueError, AttributeError):
            # Fallback to 30 days from now
            return (datetime.now() + timedelta(days=30)).date().isoformat()

    def create_invoice_metadata(self, invoice_number: str, issue_date: str = None,
                              payment_terms: str = "30 days", currency: str = "ZAR") -> InvoiceMetadata:
        """Create complete invoice metadata"""
        if issue_date is None:
            issue_date = datetime.now().date().isoformat()

        due_date = self.calculate_due_date(issue_date, payment_terms)

        metadata = InvoiceMetadata(
            invoice_number=invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            status="Draft",
            currency=currency,
            payment_terms=payment_terms
        )

        # Save to database
        self.save_metadata(metadata)

        return metadata

    def save_metadata(self, metadata: InvoiceMetadata) -> bool:
        """Save invoice metadata to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO invoice_metadata
                    (invoice_number, issue_date, due_date, status, currency, payment_terms)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    metadata.invoice_number,
                    metadata.issue_date,
                    metadata.due_date,
                    metadata.status,
                    metadata.currency,
                    metadata.payment_terms
                ))
            return True
        except Exception as e:
            print(f"Error saving metadata: {e}")
            return False

    def get_metadata(self, invoice_number: str) -> Optional[InvoiceMetadata]:
        """Get invoice metadata by invoice number"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM invoice_metadata WHERE invoice_number = ?",
                (invoice_number,)
            )

            row = cursor.fetchone()
            if row:
                return InvoiceMetadata(**dict(row))
            return None

    def update_status(self, invoice_number: str, status: str) -> bool:
        """Update invoice status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE invoice_metadata SET status = ?
                    WHERE invoice_number = ?
                """, (status, invoice_number))
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False

    def get_invoices_by_status(self, status: str) -> list:
        """Get all invoices with specific status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM invoice_metadata WHERE status = ? ORDER BY issue_date DESC",
                (status,)
            )
            return [InvoiceMetadata(**dict(row)) for row in cursor.fetchall()]

    def get_overdue_invoices(self) -> list:
        """Get all overdue invoices"""
        today = datetime.now().date().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM invoice_metadata
                WHERE status IN ('Sent', 'Draft') AND due_date < ?
                ORDER BY due_date ASC
            """, (today,))

            return [InvoiceMetadata(**dict(row)) for row in cursor.fetchall()]

    def reset_counters(self, year: int, month: int):
        """Reset invoice number counter for a specific month (admin function)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE invoice_numbers SET last_number = 0
                WHERE year = ? AND month = ?
            """, (year, month))

# Global instance for easy access
metadata_generator = MetadataGenerator()

def get_metadata_generator() -> MetadataGenerator:
    """Convenience function to get metadata generator instance"""
    return metadata_generator