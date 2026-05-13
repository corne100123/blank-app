"""
Template Engine Module - Document & Formatting Component
Handles HTML/CSS templates for invoice rendering
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from dataclasses import dataclass

@dataclass
class InvoiceTemplate:
    """Invoice template data"""
    name: str
    html_template: str
    css_styles: str
    description: str = ""
    is_default: bool = False

class TemplateEngine:
    """Handles invoice template rendering using Jinja2"""

    def __init__(self, templates_dir: Path = None):
        self.templates_dir = templates_dir or Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)

        # Set up Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Create default templates if they don't exist
        self._create_default_templates()

    def _create_default_templates(self):
        """Create default invoice templates"""
        # Professional template
        professional_html = self._get_professional_template_html()
        professional_css = self._get_professional_template_css()

        self._save_template_file("professional.html", professional_html)
        self._save_template_file("professional.css", professional_css)

        # Minimal template
        minimal_html = self._get_minimal_template_html()
        minimal_css = self._get_minimal_template_css()

        self._save_template_file("minimal.html", minimal_html)
        self._save_template_file("minimal.css", minimal_css)

        # Creative template
        creative_html = self._get_creative_template_html()
        creative_css = self._get_creative_template_css()

        self._save_template_file("creative.html", creative_html)
        self._save_template_file("creative.css", creative_css)

    def _save_template_file(self, filename: str, content: str):
        """Save template file"""
        template_path = self.templates_dir / filename
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def render_invoice(self, template_name: str, invoice_data: Dict[str, Any]) -> str:
        """Render invoice using specified template"""
        try:
            # Load HTML template
            template = self.jinja_env.get_template(f"{template_name}.html")

            # Add CSS to template data
            css_content = self._load_css(template_name)
            invoice_data['css_styles'] = css_content

            # Render template
            return template.render(**invoice_data)

        except Exception as e:
            print(f"Error rendering template {template_name}: {e}")
            # Fallback to professional template
            return self.render_invoice("professional", invoice_data)

    def _load_css(self, template_name: str) -> str:
        """Load CSS file for template"""
        css_path = self.templates_dir / f"{template_name}.css"
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                return f"<style>{f.read()}</style>"
        return ""

    def get_available_templates(self) -> list:
        """Get list of available templates"""
        templates = []
        for html_file in self.templates_dir.glob("*.html"):
            template_name = html_file.stem
            css_file = self.templates_dir / f"{template_name}.css"

            if css_file.exists():
                templates.append({
                    'name': template_name,
                    'html_file': html_file.name,
                    'css_file': css_file.name,
                    'description': self._get_template_description(template_name)
                })

        return templates

    def _get_template_description(self, template_name: str) -> str:
        """Get template description"""
        descriptions = {
            'professional': 'Clean, professional layout suitable for corporate clients',
            'minimal': 'Simple, minimal design focusing on essential information',
            'creative': 'Modern, creative design with visual elements'
        }
        return descriptions.get(template_name, f"{template_name.title()} template")

    def _get_professional_template_html(self) -> str:
        """Professional template HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Invoice {{ invoice_number }}</title>
    {{ css_styles }}
</head>
<body>
    <div class="invoice-container">
        <!-- Header -->
        <div class="header">
            <div class="company-info">
                <h1>{{ business_profile.company_name }}</h1>
                <div class="company-details">
                    <p>{{ business_profile.physical_address | replace('\\n', '<br>') }}</p>
                    {% if business_profile.phone %}
                    <p>Phone: {{ business_profile.phone }}</p>
                    {% endif %}
                    {% if business_profile.email %}
                    <p>Email: {{ business_profile.email }}</p>
                    {% endif %}
                    {% if business_profile.tax_id %}
                    <p>VAT No: {{ business_profile.tax_id }}</p>
                    {% endif %}
                </div>
            </div>
            <div class="invoice-header">
                <h2>INVOICE</h2>
                <div class="invoice-details">
                    <p><strong>Invoice #:</strong> {{ invoice_number }}</p>
                    <p><strong>Date:</strong> {{ issue_date | strftime('%d %B %Y') }}</p>
                    <p><strong>Due Date:</strong> {{ due_date | strftime('%d %B %Y') }}</p>
                </div>
            </div>
        </div>

        <!-- Client Information -->
        <div class="client-section">
            <h3>Bill To:</h3>
            <div class="client-info">
                <p><strong>{{ client.first_name }} {{ client.last_name }}</strong></p>
                {% if client.physical_address %}
                <p>{{ client.physical_address | replace('\\n', '<br>') }}</p>
                {% endif %}
                {% if client.phone %}
                <p>Phone: {{ client.phone }}</p>
                {% endif %}
                {% if client.email %}
                <p>Email: {{ client.email }}</p>
                {% endif %}
                {% if client.tax_id %}
                <p>VAT No: {{ client.tax_id }}</p>
                {% endif %}
            </div>
        </div>

        <!-- Line Items -->
        <div class="items-section">
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Description</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                        <th>Discount</th>
                        <th>Tax Rate</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in line_items %}
                    <tr>
                        <td>{{ item.description }}</td>
                        <td>{{ item.quantity }}</td>
                        <td>{{ currency_symbol }}{{ item.unit_price | round(2) }}</td>
                        <td>{{ item.discount_percent }}%</td>
                        <td>{{ item.tax_rate }}%</td>
                        <td>{{ currency_symbol }}{{ item.total | round(2) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Totals -->
        <div class="totals-section">
            <div class="totals-table">
                <div class="total-row">
                    <span>Subtotal:</span>
                    <span>{{ currency_symbol }}{{ totals.subtotal | round(2) }}</span>
                </div>
                {% if totals.total_discount > 0 %}
                <div class="total-row">
                    <span>Discount:</span>
                    <span>-{{ currency_symbol }}{{ totals.total_discount | round(2) }}</span>
                </div>
                {% endif %}
                {% if totals.total_tax > 0 %}
                <div class="total-row">
                    <span>Tax (VAT):</span>
                    <span>{{ currency_symbol }}{{ totals.total_tax | round(2) }}</span>
                </div>
                {% endif %}
                <div class="total-row grand-total">
                    <span>Total:</span>
                    <span>{{ currency_symbol }}{{ totals.grand_total | round(2) }}</span>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="payment-info">
                <h4>Payment Information</h4>
                <p><strong>Payment Terms:</strong> {{ payment_terms }}</p>
                {% if business_profile.bank_name %}
                <p><strong>Bank:</strong> {{ business_profile.bank_name }}</p>
                <p><strong>Account:</strong> {{ business_profile.account_number }}</p>
                {% if business_profile.branch_code %}
                <p><strong>Branch Code:</strong> {{ business_profile.branch_code }}</p>
                {% endif %}
                {% endif %}
            </div>
            <div class="footer-note">
                <p>Thank you for your business!</p>
                {% if business_profile.company_footer %}
                <p>{{ business_profile.company_footer }}</p>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
        """.strip()

    def _get_professional_template_css(self) -> str:
        """Professional template CSS"""
        return """
body {
    font-family: 'Arial', sans-serif;
    margin: 0;
    padding: 20px;
    color: #333;
    line-height: 1.6;
}

.invoice-container {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #007acc;
}

.company-info h1 {
    color: #007acc;
    margin: 0 0 10px 0;
    font-size: 24px;
}

.company-details p {
    margin: 2px 0;
    font-size: 12px;
}

.invoice-header h2 {
    color: #007acc;
    margin: 0 0 15px 0;
    font-size: 28px;
}

.invoice-details p {
    margin: 3px 0;
    text-align: right;
}

.client-section {
    margin-bottom: 30px;
}

.client-section h3 {
    color: #007acc;
    margin: 0 0 10px 0;
    font-size: 16px;
}

.client-info p {
    margin: 2px 0;
}

.items-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
}

.items-table th {
    background: #007acc;
    color: white;
    padding: 10px;
    text-align: left;
    font-weight: normal;
}

.items-table td {
    padding: 8px 10px;
    border-bottom: 1px solid #ddd;
}

.items-table tbody tr:nth-child(even) {
    background: #f9f9f9;
}

.totals-section {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 30px;
}

.totals-table {
    width: 250px;
}

.total-row {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
    border-bottom: 1px solid #ddd;
}

.grand-total {
    font-weight: bold;
    font-size: 16px;
    border-bottom: 2px solid #007acc;
    margin-top: 10px;
}

.footer {
    display: flex;
    justify-content: space-between;
    padding-top: 20px;
    border-top: 1px solid #ddd;
}

.payment-info h4 {
    color: #007acc;
    margin: 0 0 10px 0;
}

.footer-note {
    text-align: right;
}

.footer-note p {
    margin: 2px 0;
    font-size: 12px;
}
        """.strip()

    def _get_minimal_template_html(self) -> str:
        """Minimal template HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Invoice {{ invoice_number }}</title>
    {{ css_styles }}
</head>
<body>
    <div class="invoice">
        <header>
            <div class="company">
                <h1>{{ business_profile.company_name }}</h1>
                <p>{{ business_profile.physical_address | replace('\\n', ', ') }}</p>
            </div>
            <div class="invoice-info">
                <h2>Invoice {{ invoice_number }}</h2>
                <p>Date: {{ issue_date | strftime('%d/%m/%Y') }}</p>
                <p>Due: {{ due_date | strftime('%d/%m/%Y') }}</p>
            </div>
        </header>

        <div class="bill-to">
            <h3>Bill To</h3>
            <p>{{ client.first_name }} {{ client.last_name }}</p>
            <p>{{ client.physical_address | replace('\\n', ', ') }}</p>
        </div>

        <table class="items">
            <tr>
                <th>Description</th>
                <th>Qty</th>
                <th>Rate</th>
                <th>Amount</th>
            </tr>
            {% for item in line_items %}
            <tr>
                <td>{{ item.description }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ currency_symbol }}{{ item.unit_price | round(2) }}</td>
                <td>{{ currency_symbol }}{{ item.total | round(2) }}</td>
            </tr>
            {% endfor %}
        </table>

        <div class="total">
            <p>Total: {{ currency_symbol }}{{ totals.grand_total | round(2) }}</p>
        </div>
    </div>
</body>
</html>
        """.strip()

    def _get_minimal_template_css(self) -> str:
        """Minimal template CSS"""
        return """
body {
    font-family: 'Helvetica', sans-serif;
    margin: 40px;
    color: #333;
}

.invoice {
    max-width: 600px;
    margin: 0 auto;
}

header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 40px;
}

.company h1 {
    margin: 0;
    font-size: 24px;
}

.invoice-info {
    text-align: right;
}

.invoice-info h2 {
    margin: 0;
    font-size: 20px;
}

.bill-to {
    margin-bottom: 40px;
}

.items {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
}

.items th, .items td {
    padding: 8px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

.items th {
    background: #f5f5f5;
}

.total {
    text-align: right;
    font-size: 18px;
    font-weight: bold;
}
        """.strip()

    def _get_creative_template_html(self) -> str:
        """Creative template HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Invoice {{ invoice_number }}</title>
    {{ css_styles }}
</head>
<body>
    <div class="creative-invoice">
        <div class="header-wave">
            <div class="company-brand">
                <h1>{{ business_profile.company_name }}</h1>
                <div class="tagline">Professional Services</div>
            </div>
            <div class="invoice-badge">
                <div class="badge">INVOICE</div>
                <div class="number">{{ invoice_number }}</div>
            </div>
        </div>

        <div class="content-grid">
            <div class="client-card">
                <h3>👤 Client Details</h3>
                <div class="client-name">{{ client.first_name }} {{ client.last_name }}</div>
                <div class="client-address">{{ client.physical_address | replace('\\n', '<br>') }}</div>
                {% if client.email %}
                <div class="client-contact">📧 {{ client.email }}</div>
                {% endif %}
            </div>

            <div class="dates-card">
                <h3>📅 Important Dates</h3>
                <div class="date-item">
                    <span>Issue Date:</span>
                    <span>{{ issue_date | strftime('%d %b %Y') }}</span>
                </div>
                <div class="date-item">
                    <span>Due Date:</span>
                    <span>{{ due_date | strftime('%d %b %Y') }}</span>
                </div>
                <div class="date-item">
                    <span>Terms:</span>
                    <span>{{ payment_terms }}</span>
                </div>
            </div>
        </div>

        <div class="items-section">
            <h3>📋 Services & Products</h3>
            <div class="items-container">
                {% for item in line_items %}
                <div class="item-card">
                    <div class="item-header">
                        <div class="item-description">{{ item.description }}</div>
                        <div class="item-total">{{ currency_symbol }}{{ item.total | round(2) }}</div>
                    </div>
                    <div class="item-details">
                        <span>Qty: {{ item.quantity }}</span>
                        <span>Rate: {{ currency_symbol }}{{ item.unit_price | round(2) }}</span>
                        {% if item.discount_percent > 0 %}
                        <span>Discount: {{ item.discount_percent }}%</span>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="summary-section">
            <div class="summary-card">
                <div class="summary-row">
                    <span>Subtotal:</span>
                    <span>{{ currency_symbol }}{{ totals.subtotal | round(2) }}</span>
                </div>
                {% if totals.total_discount > 0 %}
                <div class="summary-row discount">
                    <span>Discount:</span>
                    <span>-{{ currency_symbol }}{{ totals.total_discount | round(2) }}</span>
                </div>
                {% endif %}
                {% if totals.total_tax > 0 %}
                <div class="summary-row">
                    <span>VAT ({{ line_items[0].tax_rate }}%):</span>
                    <span>{{ currency_symbol }}{{ totals.total_tax | round(2) }}</span>
                </div>
                {% endif %}
                <div class="summary-row total">
                    <span>TOTAL:</span>
                    <span>{{ currency_symbol }}{{ totals.grand_total | round(2) }}</span>
                </div>
            </div>
        </div>

        <div class="footer-section">
            <div class="payment-card">
                <h4>💳 Payment Details</h4>
                {% if business_profile.bank_name %}
                <p><strong>{{ business_profile.bank_name }}</strong></p>
                <p>Account: {{ business_profile.account_number }}</p>
                {% endif %}
            </div>
            <div class="thank-you">
                <h4>Thank You! 🎉</h4>
                <p>We appreciate your business</p>
            </div>
        </div>
    </div>
</body>
</html>
        """.strip()

    def _get_creative_template_css(self) -> str:
        """Creative template CSS"""
        return """
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.creative-invoice {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}

.header-wave {
    background: linear-gradient(45deg, #007acc, #005999);
    color: white;
    padding: 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.company-brand h1 {
    margin: 0;
    font-size: 28px;
}

.tagline {
    font-size: 14px;
    opacity: 0.9;
}

.invoice-badge {
    text-align: center;
}

.badge {
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 5px;
}

.number {
    font-size: 24px;
    font-weight: bold;
}

.content-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    padding: 30px;
}

.client-card, .dates-card {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #007acc;
}

.client-card h3, .dates-card h3 {
    margin: 0 0 15px 0;
    color: #007acc;
}

.client-name {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 10px;
}

.date-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.items-section {
    padding: 0 30px 30px;
}

.items-section h3 {
    color: #007acc;
    margin-bottom: 20px;
}

.items-container {
    display: grid;
    gap: 15px;
}

.item-card {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
    transition: box-shadow 0.3s ease;
}

.item-card:hover {
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.item-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    margin-bottom: 10px;
}

.item-description {
    font-weight: 500;
}

.item-total {
    font-size: 18px;
    font-weight: bold;
    color: #007acc;
}

.item-details {
    display: flex;
    gap: 20px;
    font-size: 14px;
    color: #6c757d;
}

.summary-section {
    background: #f8f9fa;
    padding: 30px;
}

.summary-card {
    max-width: 300px;
    margin-left: auto;
}

.summary-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #dee2e6;
}

.summary-row.discount {
    color: #dc3545;
}

.summary-row.total {
    font-size: 20px;
    font-weight: bold;
    color: #007acc;
    border-bottom: 3px solid #007acc;
    margin-top: 10px;
    padding-top: 15px;
}

.footer-section {
    background: #007acc;
    color: white;
    padding: 30px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
}

.payment-card h4, .thank-you h4 {
    margin: 0 0 15px 0;
}

.thank-you {
    text-align: right;
}
        """.strip()

# Global instance for easy access
template_engine = TemplateEngine()

def get_template_engine() -> TemplateEngine:
    """Convenience function to get template engine instance"""
    return template_engine
        """.strip()

    def _get_minimal_template_css(self) -> str:
        """Minimal template CSS"""
        return """
body {
    font-family: 'Helvetica', sans-serif;
    margin: 40px;
    color: #333;
}

.invoice {
    max-width: 600px;
    margin: 0 auto;
}

header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 40px;
}

.company h1 {
    margin: 0;
    font-size: 24px;
}

.invoice-info {
    text-align: right;
}

.invoice-info h2 {
    margin: 0;
    font-size: 20px;
}

.bill-to {
    margin-bottom: 40px;
}

.items {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
}

.items th, .items td {
    padding: 8px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

.items th {
    background: #f5f5f5;
}

.total {
    text-align: right;
    font-size: 18px;
    font-weight: bold;
}
        """.strip()

    def _get_creative_template_html(self) -> str:
        """Creative template HTML"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Invoice {{ invoice_number }}</title>
    {{ css_styles }}
</head>
<body>
    <div class="creative-invoice">
        <div class="header-wave">
            <div class="company-brand">
                <h1>{{ business_profile.company_name }}</h1>
                <div class="tagline">Professional Services</div>
            </div>
            <div class="invoice-badge">
                <div class="badge">INVOICE</div>
                <div class="number">{{ invoice_number }}</div>
            </div>
        </div>

        <div class="content-grid">
            <div class="client-card">
                <h3>👤 Client Details</h3>
                <div class="client-name">{{ client.first_name }} {{ client.last_name }}</div>
                <div class="client-address">{{ client.physical_address | replace('\\n', '<br>') }}</div>
                {% if client.email %}
                <div class="client-contact">📧 {{ client.email }}</div>
                {% endif %}
            </div>

            <div class="dates-card">
                <h3>📅 Important Dates</h3>
                <div class="date-item">
                    <span>Issue Date:</span>
                    <span>{{ issue_date | strftime('%d %b %Y') }}</span>
                </div>
                <div class="date-item">
                    <span>Due Date:</span>
                    <span>{{ due_date | strftime('%d %b %Y') }}</span>
                </div>
                <div class="date-item">
                    <span>Terms:</span>
                    <span>{{ payment_terms }}</span>
                </div>
            </div>
        </div>

        <div class="items-section">
            <h3>📋 Services & Products</h3>
            <div class="items-container">
                {% for item in line_items %}
                <div class="item-card">
                    <div class="item-header">
                        <div class="item-description">{{ item.description }}</div>
                        <div class="item-total">{{ currency_symbol }}{{ item.total | round(2) }}</div>
                    </div>
                    <div class="item-details">
                        <span>Qty: {{ item.quantity }}</span>
                        <span>Rate: {{ currency_symbol }}{{ item.unit_price | round(2) }}</span>
                        {% if item.discount_percent > 0 %}
                        <span>Discount: {{ item.discount_percent }}%</span>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="summary-section">
            <div class="summary-card">
                <div class="summary-row">
                    <span>Subtotal:</span>
                    <span>{{ currency_symbol }}{{ totals.subtotal | round(2) }}</span>
                </div>
                {% if totals.total_discount > 0 %}
                <div class="summary-row discount">
                    <span>Discount:</span>
                    <span>-{{ currency_symbol }}{{ totals.total_discount | round(2) }}</span>
                </div>
                {% endif %}
                {% if totals.total_tax > 0 %}
                <div class="summary-row">
                    <span>VAT ({{ line_items[0].tax_rate }}%):</span>
                    <span>{{ currency_symbol }}{{ totals.total_tax | round(2) }}</span>
                </div>
                {% endif %}
                <div class="summary-row total">
                    <span>TOTAL:</span>
                    <span>{{ currency_symbol }}{{ totals.grand_total | round(2) }}</span>
                </div>
            </div>
        </div>

        <div class="footer-section">
            <div class="payment-card">
                <h4>💳 Payment Details</h4>
                {% if business_profile.bank_name %}
                <p><strong>{{ business_profile.bank_name }}</strong></p>
                <p>Account: {{ business_profile.account_number }}</p>
                {% endif %}
            </div>
            <div class="thank-you">
                <h4>Thank You! 🎉</h4>
                <p>We appreciate your business</p>
            </div>
        </div>
    </div>
</body>
</html>
        """.strip()

    def _get_creative_template_css(self) -> str:
        """Creative template CSS"""
        return """
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
}

.creative-invoice {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}

.header-wave {
    background: linear-gradient(45deg, #007acc, #005999);
    color: white;
    padding: 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.company-brand h1 {
    margin: 0;
    font-size: 28px;
}

.tagline {
    font-size: 14px;
    opacity: 0.9;
}

.invoice-badge {
    text-align: center;
}

.badge {
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 5px;
}

.number {
    font-size: 24px;
    font-weight: bold;
}

.content-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    padding: 30px;
}

.client-card, .dates-card {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #007acc;
}

.client-card h3, .dates-card h3 {
    margin: 0 0 15px 0;
    color: #007acc;
}

.client-name {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 10px;
}

.date-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.items-section {
    padding: 0 30px 30px;
}

.items-section h3 {
    color: #007acc;
    margin-bottom: 20px;
}

.items-container {
    display: grid;
    gap: 15px;
}

.item-card {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
    transition: box-shadow 0.3s ease;
}

.item-card:hover {
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.item-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    margin-bottom: 10px;
}

.item-description {
    font-weight: 500;
}

.item-total {
    font-size: 18px;
    font-weight: bold;
    color: #007acc;
}

.item-details {
    display: flex;
    gap: 20px;
    font-size: 14px;
    color: #6c757d;
}

.summary-section {
    background: #f8f9fa;
    padding: 30px;
}

.summary-card {
    max-width: 300px;
    margin-left: auto;
}

.summary-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #dee2e6;
}

.summary-row.discount {
    color: #dc3545;
}

.summary-row.total {
    font-size: 20px;
    font-weight: bold;
    color: #007acc;
    border-bottom: 3px solid #007acc;
    margin-top: 10px;
    padding-top: 15px;
}

.footer-section {
    background: #007acc;
    color: white;
    padding: 30px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
}

.payment-card h4, .thank-you h4 {
    margin: 0 0 15px 0;
}

.thank-you {
    text-align: right;
}
        """.strip()

# Global instance for easy access
template_engine = TemplateEngine()

def get_template_engine() -> TemplateEngine:
    """Convenience function to get template engine instance"""
    return template_engine