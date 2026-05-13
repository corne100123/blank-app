"""
Product/Service Catalog Module - Core Data Component
Manages product and service items with pricing and descriptions
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Product:
    """Product/Service data structure"""
    product_id: Optional[int] = None
    sku: str = ""  # Stock Keeping Unit
    name: str = ""
    description: str = ""
    category: str = ""
    unit_price: float = 0.0
    currency: str = "ZAR"
    unit_of_measure: str = "Each"  # Each, Hour, Day, Month, etc.
    tax_rate: float = 15.0  # Default VAT rate
    is_taxable: bool = True
    is_active: bool = True
    created_date: Optional[str] = None
    last_updated: Optional[str] = None

class ProductCatalog:
    """Manages product/service catalog in SQLite database"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "products.db"

        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    unit_price REAL NOT NULL DEFAULT 0.0,
                    currency TEXT DEFAULT 'ZAR',
                    unit_of_measure TEXT DEFAULT 'Each',
                    tax_rate REAL DEFAULT 15.0,
                    is_taxable BOOLEAN DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)")

    def create_product(self, product: Product) -> int:
        """Create a new product and return product_id"""
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO products (
                    sku, name, description, category, unit_price, currency,
                    unit_of_measure, tax_rate, is_taxable, is_active,
                    created_date, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product.sku, product.name, product.description, product.category,
                product.unit_price, product.currency, product.unit_of_measure,
                product.tax_rate, product.is_taxable, product.is_active,
                now, now
            ))

            product_id = cursor.lastrowid
            return product_id

    def get_product(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))

            row = cursor.fetchone()
            if row:
                return Product(**dict(row))
            return None

    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM products WHERE sku = ? AND is_active = 1", (sku,))

            row = cursor.fetchone()
            if row:
                return Product(**dict(row))
            return None

    def update_product(self, product: Product) -> bool:
        """Update existing product"""
        if not product.product_id:
            return False

        product.last_updated = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE products SET
                    sku = ?, name = ?, description = ?, category = ?,
                    unit_price = ?, currency = ?, unit_of_measure = ?,
                    tax_rate = ?, is_taxable = ?, is_active = ?,
                    last_updated = ?
                WHERE product_id = ?
            """, (
                product.sku, product.name, product.description, product.category,
                product.unit_price, product.currency, product.unit_of_measure,
                product.tax_rate, product.is_taxable, product.is_active,
                product.last_updated, product.product_id
            ))

            return conn.total_changes > 0

    def delete_product(self, product_id: int) -> bool:
        """Soft delete product (set inactive)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE products SET is_active = 0, last_updated = ? WHERE product_id = ?",
                (datetime.now().isoformat(), product_id)
            )
            return conn.total_changes > 0

    def search_products(self, query: str, category: str = None, active_only: bool = True) -> List[Product]:
        """Search products by name, SKU, or description"""
        search_term = f"%{query}%"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if category:
                if active_only:
                    cursor = conn.execute("""
                        SELECT * FROM products
                        WHERE is_active = 1 AND category = ? AND (
                            name LIKE ? OR sku LIKE ? OR description LIKE ?
                        )
                        ORDER BY name
                    """, (category, search_term, search_term, search_term))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM products
                        WHERE category = ? AND (
                            name LIKE ? OR sku LIKE ? OR description LIKE ?
                        )
                        ORDER BY name
                    """, (category, search_term, search_term, search_term))
            else:
                if active_only:
                    cursor = conn.execute("""
                        SELECT * FROM products
                        WHERE is_active = 1 AND (
                            name LIKE ? OR sku LIKE ? OR description LIKE ?
                        )
                        ORDER BY name
                    """, (search_term, search_term, search_term))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM products
                        WHERE name LIKE ? OR sku LIKE ? OR description LIKE ?
                        ORDER BY name
                    """, (search_term, search_term, search_term))

            return [Product(**dict(row)) for row in cursor.fetchall()]

    def get_products_by_category(self, category: str, active_only: bool = True) -> List[Product]:
        """Get all products in a specific category"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if active_only:
                cursor = conn.execute(
                    "SELECT * FROM products WHERE category = ? AND is_active = 1 ORDER BY name",
                    (category,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM products WHERE category = ? ORDER BY name",
                    (category,)
                )

            return [Product(**dict(row)) for row in cursor.fetchall()]

    def get_all_categories(self, active_only: bool = True) -> List[str]:
        """Get list of all categories"""
        with sqlite3.connect(self.db_path) as conn:
            if active_only:
                cursor = conn.execute(
                    "SELECT DISTINCT category FROM products WHERE is_active = 1 AND category != '' ORDER BY category"
                )
            else:
                cursor = conn.execute(
                    "SELECT DISTINCT category FROM products WHERE category != '' ORDER BY category"
                )

            return [row[0] for row in cursor.fetchall()]

    def get_all_products(self, active_only: bool = True) -> List[Product]:
        """Get all products"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if active_only:
                cursor = conn.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY category, name")
            else:
                cursor = conn.execute("SELECT * FROM products ORDER BY category, name")

            return [Product(**dict(row)) for row in cursor.fetchall()]

    def validate_product(self, product: Product) -> Dict[str, str]:
        """Validate product data"""
        errors = {}

        if not product.sku.strip():
            errors["sku"] = "SKU is required"

        if not product.name.strip():
            errors["name"] = "Product name is required"

        if product.unit_price < 0:
            errors["unit_price"] = "Unit price cannot be negative"

        if product.tax_rate < 0 or product.tax_rate > 100:
            errors["tax_rate"] = "Tax rate must be between 0 and 100"

        # Check for duplicate SKU
        if product.sku:
            existing = self.get_product_by_sku(product.sku)
            if existing and existing.product_id != product.product_id:
                errors["sku"] = "SKU already exists"

        return errors

    def bulk_import_products(self, products_data: List[Dict]) -> Dict[str, int]:
        """Bulk import products from list of dictionaries"""
        success_count = 0
        error_count = 0

        for product_data in products_data:
            try:
                product = Product(**product_data)
                errors = self.validate_product(product)
                if not errors:
                    self.create_product(product)
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1

        return {"success": success_count, "errors": error_count}

# Global instance for easy access
product_catalog = ProductCatalog()

def get_product_catalog() -> ProductCatalog:
    """Convenience function to get product catalog instance"""
    return product_catalog