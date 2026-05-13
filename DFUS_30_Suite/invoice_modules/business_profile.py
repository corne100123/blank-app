"""
Business Profile Module - Core Data Component
Manages company information, branding, and business details
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict

@dataclass
class BusinessProfile:
    """Business profile data structure"""
    company_name: str = ""
    tax_id: str = ""  # VAT/TRN number
    registration_number: str = ""
    physical_address: str = ""
    postal_address: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""

    # Banking details
    bank_name: str = ""
    account_number: str = ""
    branch_code: str = ""
    swift_code: str = ""

    # Branding
    logo_path: str = ""
    signature_path: str = ""

    # Tax settings
    vat_registered: bool = True
    vat_rate: float = 15.0  # South African standard VAT

    # Invoice settings
    invoice_prefix: str = "INV"
    default_currency: str = "ZAR"
    payment_terms: str = "30 days"

class BusinessProfileManager:
    """Manages business profile data persistence and operations"""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.profile_file = self.data_dir / "business_profile.json"

    def load_profile(self) -> BusinessProfile:
        """Load business profile from disk"""
        if self.profile_file.exists():
            with open(self.profile_file, 'r') as f:
                data = json.load(f)
                return BusinessProfile(**data)
        return BusinessProfile()

    def save_profile(self, profile: BusinessProfile) -> bool:
        """Save business profile to disk"""
        try:
            with open(self.profile_file, 'w') as f:
                json.dump(asdict(profile), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving business profile: {e}")
            return False

    def get_formatted_address(self, profile: BusinessProfile) -> str:
        """Get formatted business address for invoices"""
        address_parts = []
        if profile.physical_address:
            address_parts.append(profile.physical_address)
        if profile.postal_address and profile.postal_address != profile.physical_address:
            address_parts.append(f"Postal: {profile.postal_address}")
        return "\n".join(address_parts)

    def get_banking_details(self, profile: BusinessProfile) -> Dict[str, str]:
        """Get formatted banking details"""
        return {
            "bank_name": profile.bank_name,
            "account_number": profile.account_number,
            "branch_code": profile.branch_code,
            "swift_code": profile.swift_code
        }

    def validate_profile(self, profile: BusinessProfile) -> Dict[str, str]:
        """Validate business profile data"""
        errors = {}

        if not profile.company_name.strip():
            errors["company_name"] = "Company name is required"

        if profile.vat_registered and not profile.tax_id.strip():
            errors["tax_id"] = "VAT/TRN number is required for VAT registered businesses"

        if profile.vat_rate < 0 or profile.vat_rate > 100:
            errors["vat_rate"] = "VAT rate must be between 0 and 100"

        return errors

# Global instance for easy access
business_profile_manager = BusinessProfileManager()

def get_business_profile() -> BusinessProfile:
    """Convenience function to get current business profile"""
    return business_profile_manager.load_profile()

def save_business_profile(profile: BusinessProfile) -> bool:
    """Convenience function to save business profile"""
    return business_profile_manager.save_profile(profile)