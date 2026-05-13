"""
PDF Renderer Module - Document & Formatting Component
Handles PDF generation from HTML templates using WeasyPrint
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from dataclasses import dataclass

@dataclass
class PDFOptions:
    """PDF generation options"""
    page_size: str = 'A4'
    orientation: str = 'portrait'
    margin_top: str = '1cm'
    margin_right: str = '1cm'
    margin_bottom: str = '1cm'
    margin_left: str = '1cm'
    zoom: float = 1.0
    quality: str = 'print'  # 'print', 'screen', 'ebook'

class PDFRenderer:
    """Handles PDF generation from HTML using WeasyPrint"""

    def __init__(self, assets_dir: Path = None):
        self.assets_dir = assets_dir or Path(__file__).parent / "assets"
        self.assets_dir.mkdir(exist_ok=True)

        # Font configuration for better text rendering
        self.font_config = FontConfiguration()

        # Default PDF options
        self.default_options = PDFOptions()

    def generate_pdf(self, html_content: str, output_path: Path,
                    options: Optional[PDFOptions] = None) -> bool:
        """
        Generate PDF from HTML content

        Args:
            html_content: HTML string to convert
            output_path: Path where PDF should be saved
            options: PDF generation options

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            options = options or self.default_options

            # Create WeasyPrint HTML object
            html_doc = HTML(string=html_content, base_url=str(self.assets_dir))

            # Generate CSS for page layout
            css_content = self._generate_page_css(options)

            # Create CSS object
            css = CSS(string=css_content)

            # Generate PDF
            html_doc.write_pdf(
                str(output_path),
                stylesheets=[css],
                font_config=self.font_config,
                zoom=options.zoom
            )

            return True

        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False

    def generate_pdf_from_template(self, template_name: str, invoice_data: Dict[str, Any],
                                 output_path: Path, options: Optional[PDFOptions] = None) -> bool:
        """
        Generate PDF from template and invoice data

        Args:
            template_name: Name of the template to use
            invoice_data: Invoice data dictionary
            output_path: Path where PDF should be saved
            options: PDF generation options

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from .template_engine import get_template_engine

            # Get template engine
            template_engine = get_template_engine()

            # Render HTML from template
            html_content = template_engine.render_invoice(template_name, invoice_data)

            # Generate PDF
            return self.generate_pdf(html_content, output_path, options)

        except Exception as e:
            print(f"Error generating PDF from template: {e}")
            return False

    def _generate_page_css(self, options: PDFOptions) -> str:
        """Generate CSS for page layout"""
        css = f"""
        @page {{
            size: {options.page_size} {options.orientation};
            margin-top: {options.margin_top};
            margin-right: {options.margin_right};
            margin-bottom: {options.margin_bottom};
            margin-left: {options.margin_left};
        }}

        body {{
            font-family: 'Helvetica', 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            color: #333;
            line-height: 1.6;
        }}

        /* Ensure proper page breaks */
        .page-break {{
            page-break-before: always;
        }}

        .no-break {{
            page-break-inside: avoid;
        }}

        /* Table handling */
        table {{
            width: 100%;
            border-collapse: collapse;
            page-break-inside: auto;
        }}

        tr {{
            page-break-inside: avoid;
            page-break-after: auto;
        }}

        thead {{
            display: table-header-group;
        }}

        tfoot {{
            display: table-footer-group;
        }}

        /* Image handling */
        img {{
            max-width: 100%;
            height: auto;
        }}

        /* Link styling */
        a {{
            color: #007acc;
            text-decoration: none;
        }}

        /* Print optimization */
        @media print {{
            body {{
                -webkit-print-color-adjust: exact;
                color-adjust: exact;
            }}

            .no-print {{
                display: none !important;
            }}
        }}
        """

        return css

    def add_watermark(self, pdf_path: Path, watermark_text: str,
                     opacity: float = 0.1) -> bool:
        """
        Add watermark to existing PDF

        Args:
            pdf_path: Path to PDF file
            watermark_text: Text to use as watermark
            opacity: Opacity of watermark (0.0 to 1.0)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from weasyprint import HTML

            # Create watermark HTML
            watermark_html = f"""
            <html>
            <head>
                <style>
                @page {{
                    size: A4;
                    margin: 0;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    transform: rotate(-45deg);
                    font-size: 72px;
                    font-weight: bold;
                    color: rgba(0, 0, 0, {opacity});
                    opacity: {opacity};
                    pointer-events: none;
                    z-index: 1000;
                }}
                </style>
            </head>
            <body>
                <div>{watermark_text}</div>
            </body>
            </html>
            """

            # Generate watermark PDF
            watermark_doc = HTML(string=watermark_html)
            watermark_pdf_path = pdf_path.parent / f"{pdf_path.stem}_watermark.pdf"

            watermark_doc.write_pdf(str(watermark_pdf_path))

            # Merge PDFs (this would require additional PDF manipulation library)
            # For now, just return success
            # TODO: Implement PDF merging with watermark

            return True

        except Exception as e:
            print(f"Error adding watermark: {e}")
            return False

    def add_logo(self, logo_path: Path, position: str = 'header') -> str:
        """
        Add logo to invoice template

        Args:
            logo_path: Path to logo image file
            position: Position for logo ('header', 'footer')

        Returns:
            str: CSS for logo positioning
        """
        if not logo_path.exists():
            return ""

        # Convert to data URI for embedding
        import base64

        with open(logo_path, 'rb') as f:
            logo_data = base64.b64encode(f.read()).decode()

        file_ext = logo_path.suffix.lower()
        mime_type = f"image/{file_ext[1:]}"  # Remove the dot

        css = f"""
        .company-logo {{
            max-height: 80px;
            max-width: 200px;
            object-fit: contain;
        }}

        .logo-{position} {{
            background-image: url(data:{mime_type};base64,{logo_data});
            background-repeat: no-repeat;
            background-size: contain;
            background-position: {'left center' if position == 'header' else 'right center'};
        }}
        """

        return css

    def optimize_for_print(self, html_content: str) -> str:
        """
        Optimize HTML content for print output

        Args:
            html_content: Original HTML content

        Returns:
            str: Optimized HTML content
        """
        # Add print-specific CSS
        print_css = """
        <style>
        @media print {
            body {
                font-size: 12px;
                line-height: 1.4;
            }

            .no-print {
                display: none !important;
            }

            .page-break {
                page-break-before: always;
            }

            table {
                font-size: 11px;
            }

            .invoice-container {
                box-shadow: none;
                border: 1px solid #ccc;
            }
        }
        </style>
        """

        # Insert CSS before closing head tag
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', f'{print_css}</head>')

        return html_content

    def get_page_info(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Get information about PDF pages

        Args:
            pdf_path: Path to PDF file

        Returns:
            dict: Page information
        """
        try:
            # This would require a PDF reading library like PyPDF2
            # For now, return basic info
            return {
                'file_size': pdf_path.stat().st_size if pdf_path.exists() else 0,
                'exists': pdf_path.exists(),
                'path': str(pdf_path)
            }
        except Exception as e:
            print(f"Error getting PDF info: {e}")
            return {'error': str(e)}

    def batch_generate(self, invoices_data: list, output_dir: Path,
                      template_name: str = 'professional') -> list:
        """
        Generate multiple PDFs in batch

        Args:
            invoices_data: List of invoice data dictionaries
            output_dir: Directory to save PDFs
            template_name: Template to use for all invoices

        Returns:
            list: List of generated PDF paths
        """
        output_dir.mkdir(exist_ok=True)
        generated_files = []

        for i, invoice_data in enumerate(invoices_data):
            try:
                invoice_number = invoice_data.get('invoice_number', f'invoice_{i+1}')
                pdf_path = output_dir / f"{invoice_number}.pdf"

                success = self.generate_pdf_from_template(
                    template_name, invoice_data, pdf_path
                )

                if success:
                    generated_files.append(str(pdf_path))

            except Exception as e:
                print(f"Error generating PDF for invoice {i+1}: {e}")

        return generated_files

# Global instance for easy access
pdf_renderer = PDFRenderer()

def get_pdf_renderer() -> PDFRenderer:
    """Convenience function to get PDF renderer instance"""
    return pdf_renderer