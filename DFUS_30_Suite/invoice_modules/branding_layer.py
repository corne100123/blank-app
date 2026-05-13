"""
Branding Layer Module - Document & Formatting Component
Handles logos, signatures, watermarks, and other branding assets
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image
import base64
from dataclasses import dataclass

@dataclass
class BrandingAsset:
    """Branding asset information"""
    name: str
    file_path: Path
    asset_type: str  # 'logo', 'signature', 'watermark', 'icon'
    description: str = ""
    dimensions: Tuple[int, int] = None
    file_size: int = 0

class BrandingLayer:
    """Manages branding assets for invoices"""

    def __init__(self, assets_dir: Path = None):
        self.assets_dir = assets_dir or Path(__file__).parent / "assets"
        self.assets_dir.mkdir(exist_ok=True)

        # Create subdirectories for different asset types
        self._create_asset_directories()

        # Supported image formats
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}

    def _create_asset_directories(self):
        """Create organized subdirectories for assets"""
        subdirs = ['logos', 'signatures', 'watermarks', 'icons', 'templates']
        for subdir in subdirs:
            (self.assets_dir / subdir).mkdir(exist_ok=True)

    def add_logo(self, logo_path: Path, name: str, description: str = "") -> bool:
        """
        Add a company logo

        Args:
            logo_path: Path to logo file
            name: Name for the logo
            description: Optional description

        Returns:
            bool: True if successful
        """
        return self._add_asset(logo_path, name, 'logo', description, 'logos')

    def add_signature(self, signature_path: Path, name: str, description: str = "") -> bool:
        """
        Add a signature image

        Args:
            signature_path: Path to signature file
            name: Name for the signature
            description: Optional description

        Returns:
            bool: True if successful
        """
        return self._add_asset(signature_path, name, 'signature', description, 'signatures')

    def add_watermark(self, watermark_path: Path, name: str, description: str = "") -> bool:
        """
        Add a watermark image

        Args:
            watermark_path: Path to watermark file
            name: Name for the watermark
            description: Optional description

        Returns:
            bool: True if successful
        """
        return self._add_asset(watermark_path, name, 'watermark', description, 'watermarks')

    def add_icon(self, icon_path: Path, name: str, description: str = "") -> bool:
        """
        Add an icon

        Args:
            icon_path: Path to icon file
            name: Name for the icon
            description: Optional description

        Returns:
            bool: True if successful
        """
        return self._add_asset(icon_path, name, 'icon', description, 'icons')

    def _add_asset(self, source_path: Path, name: str, asset_type: str,
                  description: str, subdir: str) -> bool:
        """Generic method to add an asset"""
        try:
            if not source_path.exists():
                print(f"Source file does not exist: {source_path}")
                return False

            # Validate file extension
            if source_path.suffix.lower() not in self.supported_formats:
                print(f"Unsupported file format: {source_path.suffix}")
                return False

            # Create destination path
            dest_dir = self.assets_dir / subdir
            dest_path = dest_dir / f"{name}{source_path.suffix}"

            # Copy file
            import shutil
            shutil.copy2(source_path, dest_path)

            # Get image dimensions if possible
            dimensions = None
            try:
                if source_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}:
                    with Image.open(dest_path) as img:
                        dimensions = img.size
            except Exception:
                pass

            print(f"Added {asset_type}: {name} to {dest_path}")
            return True

        except Exception as e:
            print(f"Error adding {asset_type}: {e}")
            return False

    def get_logo_data_uri(self, name: str) -> Optional[str]:
        """
        Get logo as data URI for embedding in HTML

        Args:
            name: Logo name

        Returns:
            str: Data URI or None if not found
        """
        return self._get_asset_data_uri(name, 'logos')

    def get_signature_data_uri(self, name: str) -> Optional[str]:
        """
        Get signature as data URI

        Args:
            name: Signature name

        Returns:
            str: Data URI or None if not found
        """
        return self._get_asset_data_uri(name, 'signatures')

    def get_watermark_data_uri(self, name: str) -> Optional[str]:
        """
        Get watermark as data URI

        Args:
            name: Watermark name

        Returns:
            str: Data URI or None if not found
        """
        return self._get_asset_data_uri(name, 'watermarks')

    def get_icon_data_uri(self, name: str) -> Optional[str]:
        """
        Get icon as data URI

        Args:
            name: Icon name

        Returns:
            str: Data URI or None if not found
        """
        return self._get_asset_data_uri(name, 'icons')

    def _get_asset_data_uri(self, name: str, subdir: str) -> Optional[str]:
        """Get asset as data URI"""
        try:
            asset_path = self._find_asset(name, subdir)
            if not asset_path:
                return None

            with open(asset_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode()

            # Determine MIME type
            ext = asset_path.suffix.lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.webp': 'image/webp'
            }

            mime_type = mime_types.get(ext, 'application/octet-stream')
            return f"data:{mime_type};base64,{data}"

        except Exception as e:
            print(f"Error getting data URI for {name}: {e}")
            return None

    def _find_asset(self, name: str, subdir: str) -> Optional[Path]:
        """Find asset file by name"""
        asset_dir = self.assets_dir / subdir

        # Try different extensions
        for ext in self.supported_formats:
            asset_path = asset_dir / f"{name}{ext}"
            if asset_path.exists():
                return asset_path

        return None

    def list_assets(self, asset_type: Optional[str] = None) -> List[BrandingAsset]:
        """
        List all branding assets

        Args:
            asset_type: Filter by asset type ('logo', 'signature', etc.)

        Returns:
            list: List of BrandingAsset objects
        """
        assets = []

        subdirs = {
            'logos': 'logo',
            'signatures': 'signature',
            'watermarks': 'watermark',
            'icons': 'icon'
        }

        for subdir, type_name in subdirs.items():
            if asset_type and type_name != asset_type:
                continue

            asset_dir = self.assets_dir / subdir
            if not asset_dir.exists():
                continue

            for asset_file in asset_dir.iterdir():
                if asset_file.is_file() and asset_file.suffix.lower() in self.supported_formats:
                    try:
                        # Get file info
                        stat = asset_file.stat()
                        dimensions = None

                        # Get dimensions for images
                        try:
                            if asset_file.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}:
                                with Image.open(asset_file) as img:
                                    dimensions = img.size
                        except Exception:
                            pass

                        asset = BrandingAsset(
                            name=asset_file.stem,
                            file_path=asset_file,
                            asset_type=type_name,
                            dimensions=dimensions,
                            file_size=stat.st_size
                        )

                        assets.append(asset)

                    except Exception as e:
                        print(f"Error processing asset {asset_file}: {e}")

        return assets

    def remove_asset(self, name: str, asset_type: str) -> bool:
        """
        Remove a branding asset

        Args:
            name: Asset name
            asset_type: Asset type ('logo', 'signature', etc.)

        Returns:
            bool: True if successful
        """
        try:
            subdir_map = {
                'logo': 'logos',
                'signature': 'signatures',
                'watermark': 'watermarks',
                'icon': 'icons'
            }

            subdir = subdir_map.get(asset_type)
            if not subdir:
                return False

            asset_path = self._find_asset(name, subdir)
            if not asset_path:
                return False

            asset_path.unlink()
            print(f"Removed {asset_type}: {name}")
            return True

        except Exception as e:
            print(f"Error removing asset: {e}")
            return False

    def optimize_image(self, asset_path: Path, max_width: int = 800,
                      max_height: int = 600, quality: int = 85) -> bool:
        """
        Optimize image for web use

        Args:
            asset_path: Path to image file
            max_width: Maximum width
            max_height: Maximum height
            quality: JPEG quality (1-100)

        Returns:
            bool: True if successful
        """
        try:
            if not asset_path.exists():
                return False

            with Image.open(asset_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Resize if too large
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                # Save optimized version
                img.save(asset_path, 'JPEG', quality=quality, optimize=True)

            print(f"Optimized image: {asset_path}")
            return True

        except Exception as e:
            print(f"Error optimizing image: {e}")
            return False

    def create_default_watermark(self, text: str = "DRAFT") -> bool:
        """
        Create a default text-based watermark

        Args:
            text: Watermark text

        Returns:
            bool: True if successful
        """
        try:
            # Create a simple text watermark image
            img = Image.new('RGBA', (400, 200), (255, 255, 255, 0))
            from PIL import ImageDraw, ImageFont

            draw = ImageDraw.Draw(img)

            # Try to use a default font
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()

            # Draw text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (400 - text_width) // 2
            y = (200 - text_height) // 2

            draw.text((x, y), text, fill=(128, 128, 128, 128), font=font)

            # Save watermark
            watermark_path = self.assets_dir / "watermarks" / f"{text.lower()}.png"
            img.save(watermark_path, 'PNG')

            print(f"Created default watermark: {watermark_path}")
            return True

        except Exception as e:
            print(f"Error creating watermark: {e}")
            return False

    def get_asset_info(self, name: str, asset_type: str) -> Optional[BrandingAsset]:
        """
        Get detailed information about an asset

        Args:
            name: Asset name
            asset_type: Asset type

        Returns:
            BrandingAsset: Asset information or None
        """
        assets = self.list_assets(asset_type)
        for asset in assets:
            if asset.name == name:
                return asset
        return None

    def export_assets(self, export_dir: Path) -> bool:
        """
        Export all assets to a directory

        Args:
            export_dir: Directory to export to

        Returns:
            bool: True if successful
        """
        try:
            export_dir.mkdir(exist_ok=True)

            assets = self.list_assets()
            for asset in assets:
                dest_path = export_dir / f"{asset.asset_type}s" / asset.file_path.name
                dest_path.parent.mkdir(exist_ok=True)

                import shutil
                shutil.copy2(asset.file_path, dest_path)

            print(f"Exported {len(assets)} assets to {export_dir}")
            return True

        except Exception as e:
            print(f"Error exporting assets: {e}")
            return False

# Global instance for easy access
branding_layer = BrandingLayer()

def get_branding_layer() -> BrandingLayer:
    """Convenience function to get branding layer instance"""
    return branding_layer