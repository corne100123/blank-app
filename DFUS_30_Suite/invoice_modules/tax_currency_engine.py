"""
Tax & Currency Engine Module - Logic & Calculation Component
Handles multi-currency transactions and tax calculations
"""
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path

@dataclass
class CurrencyRate:
    """Currency exchange rate data"""
    from_currency: str
    to_currency: str
    rate: float
    last_updated: str
    source: str = "manual"

@dataclass
class TaxCalculation:
    """Tax calculation result"""
    subtotal: float
    tax_amount: float
    tax_rate: float
    total: float
    currency: str
    tax_type: str = "VAT"  # VAT, GST, etc.

class TaxCurrencyEngine:
    """Handles tax calculations and currency conversions"""

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rates_cache_file = self.cache_dir / "currency_rates.json"

        # Default tax rates by country/region
        self.default_tax_rates = {
            "ZA": {"VAT": 15.0},  # South Africa
            "US": {"GST": 0.0},   # No federal GST
            "GB": {"VAT": 20.0},  # UK
            "EU": {"VAT": 21.0},  # EU average
            "AU": {"GST": 10.0},  # Australia
        }

        # Supported currencies
        self.supported_currencies = ["ZAR", "USD", "EUR", "GBP", "AUD"]

    def calculate_tax(self, amount: float, tax_rate: float, tax_type: str = "VAT",
                     currency: str = "ZAR") -> TaxCalculation:
        """Calculate tax for a given amount"""
        tax_amount = amount * (tax_rate / 100)
        total = amount + tax_amount

        return TaxCalculation(
            subtotal=round(amount, 2),
            tax_amount=round(tax_amount, 2),
            tax_rate=tax_rate,
            total=round(total, 2),
            currency=currency,
            tax_type=tax_type
        )

    def calculate_line_item_tax(self, unit_price: float, quantity: float,
                               tax_rate: float, discount: float = 0.0,
                               tax_type: str = "VAT") -> Dict[str, float]:
        """Calculate tax for a line item"""
        subtotal = unit_price * quantity
        discount_amount = subtotal * (discount / 100)
        taxable_amount = subtotal - discount_amount
        tax_amount = taxable_amount * (tax_rate / 100)
        total = taxable_amount + tax_amount

        return {
            "unit_price": round(unit_price, 2),
            "quantity": quantity,
            "subtotal": round(subtotal, 2),
            "discount_percent": discount,
            "discount_amount": round(discount_amount, 2),
            "taxable_amount": round(taxable_amount, 2),
            "tax_rate": tax_rate,
            "tax_amount": round(tax_amount, 2),
            "total": round(total, 2)
        }

    def get_default_tax_rate(self, country_code: str = "ZA", tax_type: str = "VAT") -> float:
        """Get default tax rate for a country"""
        return self.default_tax_rates.get(country_code, {}).get(tax_type, 15.0)

    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Tuple[float, float]:
        """Convert amount between currencies"""
        if from_currency == to_currency:
            return amount, 1.0

        rate = self.get_exchange_rate(from_currency, to_currency)
        if rate:
            converted = amount * rate
            return round(converted, 2), rate
        else:
            # Return original amount if conversion fails
            return amount, 1.0

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate from cache or API"""
        # Check cache first
        cached_rate = self._get_cached_rate(from_currency, to_currency)
        if cached_rate:
            return cached_rate

        # Try to fetch from API
        rate = self._fetch_exchange_rate(from_currency, to_currency)
        if rate:
            self._cache_rate(from_currency, to_currency, rate, "api")
            return rate

        return None

    def _get_cached_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get cached exchange rate"""
        if not self.rates_cache_file.exists():
            return None

        try:
            with open(self.rates_cache_file, 'r') as f:
                cache = json.load(f)

            key = f"{from_currency}_{to_currency}"
            if key in cache:
                rate_data = cache[key]
                # Check if rate is less than 24 hours old
                updated = datetime.fromisoformat(rate_data['last_updated'])
                if datetime.now() - updated < timedelta(hours=24):
                    return rate_data['rate']

        except (json.JSONDecodeError, KeyError, ValueError):
            pass

        return None

    def _cache_rate(self, from_currency: str, to_currency: str, rate: float, source: str):
        """Cache exchange rate"""
        cache = {}
        if self.rates_cache_file.exists():
            try:
                with open(self.rates_cache_file, 'r') as f:
                    cache = json.load(f)
            except json.JSONDecodeError:
                cache = {}

        key = f"{from_currency}_{to_currency}"
        cache[key] = {
            "rate": rate,
            "last_updated": datetime.now().isoformat(),
            "source": source
        }

        with open(self.rates_cache_file, 'w') as f:
            json.dump(cache, f, indent=2)

    def _fetch_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Fetch exchange rate from external API"""
        # Using exchangerate-api.com (free tier)
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                return rates.get(to_currency)

        except (requests.RequestException, KeyError, ValueError):
            pass

        return None

    def set_manual_exchange_rate(self, from_currency: str, to_currency: str, rate: float):
        """Manually set exchange rate"""
        self._cache_rate(from_currency, to_currency, rate, "manual")

    def calculate_invoice_totals(self, line_items: List[Dict], currency: str = "ZAR") -> Dict[str, float]:
        """Calculate totals for entire invoice"""
        subtotal = 0.0
        total_tax = 0.0
        total_discount = 0.0

        for item in line_items:
            subtotal += item.get('subtotal', 0)
            total_tax += item.get('tax_amount', 0)
            total_discount += item.get('discount_amount', 0)

        grand_total = subtotal - total_discount + total_tax

        return {
            "subtotal": round(subtotal, 2),
            "total_discount": round(total_discount, 2),
            "total_tax": round(total_tax, 2),
            "grand_total": round(grand_total, 2),
            "currency": currency
        }

    def format_currency(self, amount: float, currency: str) -> str:
        """Format amount with currency symbol"""
        currency_symbols = {
            "ZAR": "R",
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "AUD": "A$"
        }

        symbol = currency_symbols.get(currency, currency)
        return f"{symbol}{amount:,.2f}"

    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies"""
        return self.supported_currencies.copy()

    def validate_tax_rate(self, tax_rate: float) -> bool:
        """Validate tax rate (0-100%)"""
        return 0 <= tax_rate <= 100

    def get_tax_breakdown(self, line_items: List[Dict]) -> Dict[str, float]:
        """Get tax breakdown by rate"""
        breakdown = {}

        for item in line_items:
            rate = item.get('tax_rate', 0)
            tax_amount = item.get('tax_amount', 0)

            if rate not in breakdown:
                breakdown[rate] = 0.0
            breakdown[rate] += tax_amount

        return {f"{rate}%": round(amount, 2) for rate, amount in breakdown.items()}

# Global instance for easy access
tax_currency_engine = TaxCurrencyEngine()

def get_tax_currency_engine() -> TaxCurrencyEngine:
    """Convenience function to get tax/currency engine instance"""
    return tax_currency_engine