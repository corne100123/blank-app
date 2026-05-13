"""
Math Module - Logic & Calculation Component
Handles all mathematical calculations for invoices
"""
from typing import List, Dict, Tuple
from decimal import Decimal, ROUND_HALF_UP

class InvoiceMath:
    """Mathematical calculations for invoices"""

    @staticmethod
    def calculate_subtotal(line_items: List[Dict[str, float]]) -> float:
        """
        Calculate subtotal from line items
        Formula: Σ(quantity × unit_price)
        """
        subtotal = sum(
            item.get('quantity', 0) * item.get('unit_price', 0)
            for item in line_items
        )
        return float(Decimal(str(subtotal)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculate_discount(subtotal: float, discount_percent: float = 0.0,
                          discount_amount: float = 0.0) -> Tuple[float, float]:
        """
        Calculate discount amount
        Returns: (discounted_subtotal, discount_amount)
        """
        if discount_percent > 0:
            discount_amount = subtotal * (discount_percent / 100)
        elif discount_amount > 0:
            discount_amount = min(discount_amount, subtotal)  # Can't discount more than subtotal

        discounted_subtotal = subtotal - discount_amount

        return (
            float(Decimal(str(discounted_subtotal)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            float(Decimal(str(discount_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        )

    @staticmethod
    def calculate_tax(taxable_amount: float, tax_rate: float) -> float:
        """
        Calculate tax amount
        Formula: taxable_amount × (tax_rate / 100)
        """
        tax_amount = taxable_amount * (tax_rate / 100)
        return float(Decimal(str(tax_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculate_grand_total(subtotal: float, discount_amount: float,
                             tax_amount: float) -> float:
        """
        Calculate grand total
        Formula: (subtotal - discount_amount) + tax_amount
        """
        grand_total = (subtotal - discount_amount) + tax_amount
        return float(Decimal(str(grand_total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculate_line_total(unit_price: float, quantity: float,
                           discount_percent: float = 0.0, tax_rate: float = 0.0) -> Dict[str, float]:
        """
        Calculate complete line item totals
        Returns dictionary with all calculated values
        """
        # Basic calculations
        subtotal = unit_price * quantity
        discount_amount = subtotal * (discount_percent / 100)
        taxable_amount = subtotal - discount_amount
        tax_amount = taxable_amount * (tax_rate / 100)
        total = taxable_amount + tax_amount

        # Round all values to 2 decimal places
        return {
            'unit_price': float(Decimal(str(unit_price)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'quantity': quantity,
            'subtotal': float(Decimal(str(subtotal)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'discount_percent': discount_percent,
            'discount_amount': float(Decimal(str(discount_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'taxable_amount': float(Decimal(str(taxable_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'tax_rate': tax_rate,
            'tax_amount': float(Decimal(str(tax_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'total': float(Decimal(str(total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        }

    @staticmethod
    def calculate_invoice_summary(line_items: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Calculate complete invoice summary from line items
        """
        if not line_items:
            return {
                'subtotal': 0.00,
                'total_discount': 0.00,
                'total_tax': 0.00,
                'grand_total': 0.00,
                'item_count': 0
            }

        # Sum up all line items
        subtotal = sum(item.get('subtotal', 0) for item in line_items)
        total_discount = sum(item.get('discount_amount', 0) for item in line_items)
        total_tax = sum(item.get('tax_amount', 0) for item in line_items)
        grand_total = sum(item.get('total', 0) for item in line_items)
        item_count = len(line_items)

        # Round final totals
        return {
            'subtotal': float(Decimal(str(subtotal)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'total_discount': float(Decimal(str(total_discount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'total_tax': float(Decimal(str(total_tax)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'grand_total': float(Decimal(str(grand_total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'item_count': item_count
        }

    @staticmethod
    def calculate_percentage(part: float, total: float) -> float:
        """
        Calculate percentage: (part / total) × 100
        Returns 0 if total is 0 to avoid division by zero
        """
        if total == 0:
            return 0.0
        percentage = (part / total) * 100
        return float(Decimal(str(percentage)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    @staticmethod
    def calculate_proportion(amount: float, total: float, target_total: float) -> float:
        """
        Calculate proportional amount
        Formula: (amount / total) × target_total
        """
        if total == 0:
            return 0.0
        proportion = (amount / total) * target_total
        return float(Decimal(str(proportion)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    @staticmethod
    def round_to_currency(amount: float, decimals: int = 2) -> float:
        """
        Round amount to specified decimal places for currency
        """
        decimal_places = Decimal('1.' + '0' * decimals)
        rounded = Decimal(str(amount)).quantize(decimal_places, rounding=ROUND_HALF_UP)
        return float(rounded)

    @staticmethod
    def validate_calculation(amount: float, min_value: float = 0.0,
                           max_value: float = None) -> bool:
        """
        Validate calculation result
        """
        if amount < min_value:
            return False
        if max_value is not None and amount > max_value:
            return False
        return True

# Global instance for easy access
invoice_math = InvoiceMath()

def get_invoice_math() -> InvoiceMath:
    """Convenience function to get invoice math instance"""
    return invoice_math