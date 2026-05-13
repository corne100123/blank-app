"""
Business Profile Module for FUS30.
Manages company information, branding, and banking details.
"""
import json
import sqlite3
from pathlib import Path


class BusinessProfile:
    """Manages business configuration and profile data."""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_profile(self):
        """Retrieve full business profile."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM business_config LIMIT 1")
        profile = cursor.fetchone()
        conn.close()
        
        return dict(profile) if profile else self._default_profile()
    
    def _default_profile(self):
        """Return default profile structure."""
        return {
            "business_name": "FUS30 Suite",
            "tax_id": "",
            "vat_number": "",
            "registration_number": "",
            "address": "",
            "phone": "",
            "email": "",
            "website": "",
            "logo_path": None,
            "currency": "ZAR",
            "vat_rate": 0.15,
            "banking": {
                "account_name": "",
                "account_number": "",
                "bank_name": "",
                "branch_code": ""
            }
        }
    
    def update_profile(self, profile_data):
        """Update business profile."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        profile = self.get_profile()
        profile.update(profile_data)
        
        cursor.execute("""
            UPDATE business_config
            SET business_name = ?
            WHERE config_id = 1
        """, (profile_data.get('business_name', 'FUS30 Suite'),))
        
        conn.commit()
        conn.close()
        return profile
    
    def get_vat_rate(self):
        """Get VAT rate for South Africa (standard 15%)."""
        profile = self.get_profile()
        return profile.get('vat_rate', 0.15)
    
    def set_vat_rate(self, rate):
        """Update VAT rate."""
        profile = self.get_profile()
        profile['vat_rate'] = rate
        return self.update_profile(profile)


class InvoiceNumberGenerator:
    """Generate sequential invoice numbers."""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def next_number(self, prefix="INV", year=None):
        """
        Generate next invoice number.
        Format: INV-2026-0001
        """
        from datetime import datetime
        
        if year is None:
            year = datetime.now().year
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count invoices created this year
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM invoices
            WHERE strftime('%Y', created_at) = ?
        """, (str(year),))
        
        count = cursor.fetchone()[0] + 1
        conn.close()
        
        return f"{prefix}-{year}-{count:04d}"


class TaxCalculator:
    """Handles tax calculations for invoices."""
    
    def __init__(self, db_path, currency="ZAR"):
        self.db_path = db_path
        self.currency = currency
        
        profile = BusinessProfile(db_path)
        self.vat_rate = profile.get_vat_rate()
    
    def calculate_totals(self, line_items, discount=0):
        """
        Calculate invoice totals.
        
        Args:
            line_items: List of {"quantity": int, "unit_price": float, "description": str}
            discount: Total discount amount
        
        Returns:
            {
                "subtotal": float,
                "discount": float,
                "subtotal_after_discount": float,
                "vat": float,
                "grand_total": float
            }
        """
        subtotal = sum(item['quantity'] * item['unit_price'] for item in line_items)
        subtotal_after_discount = subtotal - discount
        vat = subtotal_after_discount * self.vat_rate
        grand_total = subtotal_after_discount + vat
        
        return {
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "subtotal_after_discount": round(subtotal_after_discount, 2),
            "vat": round(vat, 2),
            "vat_rate": self.vat_rate,
            "grand_total": round(grand_total, 2),
            "currency": self.currency
        }


class InvoiceMetadata:
    """Generates and manages invoice metadata."""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.number_gen = InvoiceNumberGenerator(db_path)
    
    def create_metadata(self, client_id, agent_id, due_days=30):
        """
        Create metadata for a new invoice.
        
        Args:
            client_id: Client ID
            agent_id: Agent ID
            due_days: Days until due (default 30)
        
        Returns:
            Metadata dictionary
        """
        from datetime import datetime, timedelta
        
        now = datetime.now()
        due_date = now + timedelta(days=due_days)
        
        return {
            "invoice_number": self.number_gen.next_number(),
            "issued_date": now.isoformat(),
            "due_date": due_date.isoformat(),
            "client_id": client_id,
            "agent_id": agent_id,
            "status": "Draft"
        }
