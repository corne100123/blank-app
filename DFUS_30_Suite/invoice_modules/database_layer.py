"""
Database Layer Module - Persistence & Management Component
Handles database operations using SQLAlchemy
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

Base = declarative_base()

class Invoice(Base):
    """Invoice database model"""
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    payment_terms = Column(String(100), default='Net 30')
    currency_code = Column(String(3), default='USD')
    currency_symbol = Column(String(5), default='$')
    status = Column(String(20), default='draft')  # draft, sent, paid, overdue, cancelled

    # Financial data
    subtotal = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    grand_total = Column(Float, default=0.0)

    # Additional data stored as JSON
    line_items = Column(Text)  # JSON string
    notes = Column(Text)
    footer_text = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

    # Relationships
    client = relationship("Client", back_populates="invoices")

class Client(Base):
    """Client database model"""
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    physical_address = Column(Text)
    tax_id = Column(String(50))

    # Business info
    company_name = Column(String(255))
    business_type = Column(String(100))

    # Additional data
    notes = Column(Text)
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoices = relationship("Invoice", back_populates="client")

class Product(Base):
    """Product/Service database model"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    sku = Column(String(100), unique=True)
    unit_price = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0.0)  # Percentage

    # Categorization
    category = Column(String(100))
    subcategory = Column(String(100))

    # Inventory (optional)
    stock_quantity = Column(Float, default=0)
    min_stock_level = Column(Float, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    is_taxable = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BusinessProfile(Base):
    """Business profile database model"""
    __tablename__ = 'business_profiles'

    id = Column(Integer, primary_key=True)
    company_name = Column(String(255), nullable=False)
    physical_address = Column(Text)
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    tax_id = Column(String(50))

    # Banking information
    bank_name = Column(String(255))
    account_number = Column(String(100))
    branch_code = Column(String(50))
    swift_code = Column(String(20))

    # Business details
    registration_number = Column(String(100))
    industry = Column(String(100))
    company_footer = Column(Text)

    # Logo and branding (file paths)
    logo_path = Column(String(500))
    signature_path = Column(String(500))

    # Tax settings
    default_tax_rate = Column(Float, default=0.0)
    currency_code = Column(String(3), default='USD')
    currency_symbol = Column(String(5), default='$')

    # Metadata
    is_default = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class InvoiceTemplate(Base):
    """Invoice template database model"""
    __tablename__ = 'invoice_templates'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    html_content = Column(Text, nullable=False)
    css_content = Column(Text)

    # Template settings
    is_default = Column(Boolean, default=False)
    category = Column(String(50), default='professional')  # professional, minimal, creative

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

class DatabaseLayer:
    """Handles all database operations for the invoice system"""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path(__file__).parent / "invoice_system.db"
        self.db_url = f"sqlite:///{self.db_path}"

        # Create engine
        self.engine = create_engine(self.db_url, echo=False)

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        self._create_tables()

    def _create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    # Invoice operations
    def save_invoice(self, invoice_data: Dict[str, Any]) -> Optional[int]:
        """Save invoice to database"""
        session = self.get_session()
        try:
            # Convert line items to JSON
            line_items_json = json.dumps(invoice_data.get('line_items', []))

            invoice = Invoice(
                invoice_number=invoice_data['invoice_number'],
                client_id=invoice_data['client_id'],
                issue_date=invoice_data.get('issue_date', datetime.utcnow()),
                due_date=invoice_data['due_date'],
                payment_terms=invoice_data.get('payment_terms', 'Net 30'),
                currency_code=invoice_data.get('currency_code', 'USD'),
                currency_symbol=invoice_data.get('currency_symbol', '$'),
                status=invoice_data.get('status', 'draft'),
                subtotal=invoice_data.get('subtotal', 0.0),
                discount_amount=invoice_data.get('discount_amount', 0.0),
                tax_amount=invoice_data.get('tax_amount', 0.0),
                grand_total=invoice_data.get('grand_total', 0.0),
                line_items=line_items_json,
                notes=invoice_data.get('notes'),
                footer_text=invoice_data.get('footer_text'),
                created_by=invoice_data.get('created_by')
            )

            session.add(invoice)
            session.commit()
            return invoice.id

        except Exception as e:
            session.rollback()
            print(f"Error saving invoice: {e}")
            return None
        finally:
            session.close()

    def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get invoice by ID"""
        session = self.get_session()
        try:
            invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            if invoice:
                return self._invoice_to_dict(invoice)
            return None
        except Exception as e:
            print(f"Error getting invoice: {e}")
            return None
        finally:
            session.close()

    def get_invoice_by_number(self, invoice_number: str) -> Optional[Dict[str, Any]]:
        """Get invoice by invoice number"""
        session = self.get_session()
        try:
            invoice = session.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()
            if invoice:
                return self._invoice_to_dict(invoice)
            return None
        except Exception as e:
            print(f"Error getting invoice by number: {e}")
            return None
        finally:
            session.close()

    def update_invoice(self, invoice_id: int, update_data: Dict[str, Any]) -> bool:
        """Update invoice"""
        session = self.get_session()
        try:
            invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                return False

            # Update fields
            for key, value in update_data.items():
                if key == 'line_items' and isinstance(value, list):
                    value = json.dumps(value)
                if hasattr(invoice, key):
                    setattr(invoice, key, value)

            invoice.updated_at = datetime.utcnow()
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Error updating invoice: {e}")
            return False
        finally:
            session.close()

    def delete_invoice(self, invoice_id: int) -> bool:
        """Delete invoice"""
        session = self.get_session()
        try:
            invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            if invoice:
                session.delete(invoice)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error deleting invoice: {e}")
            return False
        finally:
            session.close()

    def list_invoices(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List invoices with optional filtering"""
        session = self.get_session()
        try:
            query = session.query(Invoice)
            if status:
                query = query.filter(Invoice.status == status)

            invoices = query.order_by(Invoice.created_at.desc()).limit(limit).all()
            return [self._invoice_to_dict(invoice) for invoice in invoices]

        except Exception as e:
            print(f"Error listing invoices: {e}")
            return []
        finally:
            session.close()

    def _invoice_to_dict(self, invoice: Invoice) -> Dict[str, Any]:
        """Convert invoice object to dictionary"""
        try:
            line_items = json.loads(invoice.line_items) if invoice.line_items else []
        except:
            line_items = []

        return {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'client_id': invoice.client_id,
            'issue_date': invoice.issue_date.isoformat() if invoice.issue_date else None,
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'payment_terms': invoice.payment_terms,
            'currency_code': invoice.currency_code,
            'currency_symbol': invoice.currency_symbol,
            'status': invoice.status,
            'subtotal': invoice.subtotal,
            'discount_amount': invoice.discount_amount,
            'tax_amount': invoice.tax_amount,
            'grand_total': invoice.grand_total,
            'line_items': line_items,
            'notes': invoice.notes,
            'footer_text': invoice.footer_text,
            'created_at': invoice.created_at.isoformat() if invoice.created_at else None,
            'updated_at': invoice.updated_at.isoformat() if invoice.updated_at else None,
            'created_by': invoice.created_by,
            'client': {
                'id': invoice.client.id,
                'first_name': invoice.client.first_name,
                'last_name': invoice.client.last_name,
                'email': invoice.client.email,
                'company_name': invoice.client.company_name
            } if invoice.client else None
        }

    # Client operations
    def save_client(self, client_data: Dict[str, Any]) -> Optional[int]:
        """Save client to database"""
        session = self.get_session()
        try:
            client = Client(
                first_name=client_data['first_name'],
                last_name=client_data['last_name'],
                email=client_data.get('email'),
                phone=client_data.get('phone'),
                physical_address=client_data.get('physical_address'),
                tax_id=client_data.get('tax_id'),
                company_name=client_data.get('company_name'),
                business_type=client_data.get('business_type'),
                notes=client_data.get('notes'),
                is_active=client_data.get('is_active', True)
            )

            session.add(client)
            session.commit()
            return client.id

        except Exception as e:
            session.rollback()
            print(f"Error saving client: {e}")
            return None
        finally:
            session.close()

    def get_client(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Get client by ID"""
        session = self.get_session()
        try:
            client = session.query(Client).filter(Client.id == client_id).first()
            if client:
                return {
                    'id': client.id,
                    'first_name': client.first_name,
                    'last_name': client.last_name,
                    'email': client.email,
                    'phone': client.phone,
                    'physical_address': client.physical_address,
                    'tax_id': client.tax_id,
                    'company_name': client.company_name,
                    'business_type': client.business_type,
                    'notes': client.notes,
                    'is_active': client.is_active,
                    'created_at': client.created_at.isoformat() if client.created_at else None,
                    'updated_at': client.updated_at.isoformat() if client.updated_at else None
                }
            return None
        except Exception as e:
            print(f"Error getting client: {e}")
            return None
        finally:
            session.close()

    def update_client(self, client_id: int, update_data: Dict[str, Any]) -> bool:
        """Update client"""
        session = self.get_session()
        try:
            client = session.query(Client).filter(Client.id == client_id).first()
            if not client:
                return False

            for key, value in update_data.items():
                if hasattr(client, key):
                    setattr(client, key, value)

            client.updated_at = datetime.utcnow()
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"Error updating client: {e}")
            return False
        finally:
            session.close()

    def list_clients(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all clients"""
        session = self.get_session()
        try:
            query = session.query(Client)
            if active_only:
                query = query.filter(Client.is_active == True)

            clients = query.order_by(Client.last_name, Client.first_name).all()
            return [{
                'id': client.id,
                'first_name': client.first_name,
                'last_name': client.last_name,
                'email': client.email,
                'phone': client.phone,
                'company_name': client.company_name,
                'is_active': client.is_active
            } for client in clients]

        except Exception as e:
            print(f"Error listing clients: {e}")
            return []
        finally:
            session.close()

    # Product operations
    def save_product(self, product_data: Dict[str, Any]) -> Optional[int]:
        """Save product to database"""
        session = self.get_session()
        try:
            product = Product(
                name=product_data['name'],
                description=product_data.get('description'),
                sku=product_data.get('sku'),
                unit_price=product_data['unit_price'],
                tax_rate=product_data.get('tax_rate', 0.0),
                category=product_data.get('category'),
                subcategory=product_data.get('subcategory'),
                stock_quantity=product_data.get('stock_quantity', 0),
                min_stock_level=product_data.get('min_stock_level', 0),
                is_active=product_data.get('is_active', True),
                is_taxable=product_data.get('is_taxable', True)
            )

            session.add(product)
            session.commit()
            return product.id

        except Exception as e:
            session.rollback()
            print(f"Error saving product: {e}")
            return None
        finally:
            session.close()

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        session = self.get_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                return {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'sku': product.sku,
                    'unit_price': product.unit_price,
                    'tax_rate': product.tax_rate,
                    'category': product.category,
                    'subcategory': product.subcategory,
                    'stock_quantity': product.stock_quantity,
                    'min_stock_level': product.min_stock_level,
                    'is_active': product.is_active,
                    'is_taxable': product.is_taxable
                }
            return None
        except Exception as e:
            print(f"Error getting product: {e}")
            return None
        finally:
            session.close()

    def list_products(self, category: Optional[str] = None, active_only: bool = True) -> List[Dict[str, Any]]:
        """List products with optional filtering"""
        session = self.get_session()
        try:
            query = session.query(Product)
            if active_only:
                query = query.filter(Product.is_active == True)
            if category:
                query = query.filter(Product.category == category)

            products = query.order_by(Product.name).all()
            return [{
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'unit_price': product.unit_price,
                'category': product.category,
                'is_active': product.is_active
            } for product in products]

        except Exception as e:
            print(f"Error listing products: {e}")
            return []
        finally:
            session.close()

    # Business profile operations
    def save_business_profile(self, profile_data: Dict[str, Any]) -> Optional[int]:
        """Save business profile"""
        session = self.get_session()
        try:
            profile = BusinessProfile(
                company_name=profile_data['company_name'],
                physical_address=profile_data.get('physical_address'),
                phone=profile_data.get('phone'),
                email=profile_data.get('email'),
                website=profile_data.get('website'),
                tax_id=profile_data.get('tax_id'),
                bank_name=profile_data.get('bank_name'),
                account_number=profile_data.get('account_number'),
                branch_code=profile_data.get('branch_code'),
                swift_code=profile_data.get('swift_code'),
                registration_number=profile_data.get('registration_number'),
                industry=profile_data.get('industry'),
                company_footer=profile_data.get('company_footer'),
                logo_path=profile_data.get('logo_path'),
                signature_path=profile_data.get('signature_path'),
                default_tax_rate=profile_data.get('default_tax_rate', 0.0),
                currency_code=profile_data.get('currency_code', 'USD'),
                currency_symbol=profile_data.get('currency_symbol', '$'),
                is_default=profile_data.get('is_default', True)
            )

            session.add(profile)
            session.commit()
            return profile.id

        except Exception as e:
            session.rollback()
            print(f"Error saving business profile: {e}")
            return None
        finally:
            session.close()

    def get_business_profile(self, profile_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get business profile (default or by ID)"""
        session = self.get_session()
        try:
            query = session.query(BusinessProfile)
            if profile_id:
                query = query.filter(BusinessProfile.id == profile_id)
            else:
                query = query.filter(BusinessProfile.is_default == True)

            profile = query.first()
            if profile:
                return {
                    'id': profile.id,
                    'company_name': profile.company_name,
                    'physical_address': profile.physical_address,
                    'phone': profile.phone,
                    'email': profile.email,
                    'website': profile.website,
                    'tax_id': profile.tax_id,
                    'bank_name': profile.bank_name,
                    'account_number': profile.account_number,
                    'branch_code': profile.branch_code,
                    'swift_code': profile.swift_code,
                    'registration_number': profile.registration_number,
                    'industry': profile.industry,
                    'company_footer': profile.company_footer,
                    'logo_path': profile.logo_path,
                    'signature_path': profile.signature_path,
                    'default_tax_rate': profile.default_tax_rate,
                    'currency_code': profile.currency_code,
                    'currency_symbol': profile.currency_symbol,
                    'is_default': profile.is_default
                }
            return None
        except Exception as e:
            print(f"Error getting business profile: {e}")
            return None
        finally:
            session.close()

    # Template operations
    def save_template(self, template_data: Dict[str, Any]) -> Optional[int]:
        """Save invoice template"""
        session = self.get_session()
        try:
            template = InvoiceTemplate(
                name=template_data['name'],
                description=template_data.get('description'),
                html_content=template_data['html_content'],
                css_content=template_data.get('css_content'),
                is_default=template_data.get('is_default', False),
                category=template_data.get('category', 'professional'),
                created_by=template_data.get('created_by')
            )

            session.add(template)
            session.commit()
            return template.id

        except Exception as e:
            session.rollback()
            print(f"Error saving template: {e}")
            return None
        finally:
            session.close()

    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        session = self.get_session()
        try:
            template = session.query(InvoiceTemplate).filter(InvoiceTemplate.id == template_id).first()
            if template:
                return {
                    'id': template.id,
                    'name': template.name,
                    'description': template.description,
                    'html_content': template.html_content,
                    'css_content': template.css_content,
                    'is_default': template.is_default,
                    'category': template.category,
                    'created_at': template.created_at.isoformat() if template.created_at else None,
                    'updated_at': template.updated_at.isoformat() if template.updated_at else None,
                    'created_by': template.created_by
                }
            return None
        except Exception as e:
            print(f"Error getting template: {e}")
            return None
        finally:
            session.close()

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all templates"""
        session = self.get_session()
        try:
            templates = session.query(InvoiceTemplate).order_by(InvoiceTemplate.name).all()
            return [{
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'is_default': template.is_default,
                'category': template.category
            } for template in templates]

        except Exception as e:
            print(f"Error listing templates: {e}")
            return []
        finally:
            session.close()

    # Utility methods
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        session = self.get_session()
        try:
            stats = {
                'total_invoices': session.query(Invoice).count(),
                'total_clients': session.query(Client).count(),
                'total_products': session.query(Product).count(),
                'draft_invoices': session.query(Invoice).filter(Invoice.status == 'draft').count(),
                'sent_invoices': session.query(Invoice).filter(Invoice.status == 'sent').count(),
                'paid_invoices': session.query(Invoice).filter(Invoice.status == 'paid').count(),
                'overdue_invoices': session.query(Invoice).filter(Invoice.status == 'overdue').count()
            }
            return stats
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
        finally:
            session.close()

    def backup_database(self, backup_path: Path) -> bool:
        """Create database backup"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Error backing up database: {e}")
            return False

# Global instance for easy access
database_layer = DatabaseLayer()

def get_database_layer() -> DatabaseLayer:
    """Convenience function to get database layer instance"""
    return database_layer