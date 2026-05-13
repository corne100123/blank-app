"""
File Storage Module - Persistence & Management Component
Handles file storage and management for generated invoices and documents
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import json
from dataclasses import dataclass

@dataclass
class FileMetadata:
    """File metadata information"""
    filename: str
    original_name: str
    file_path: Path
    file_size: int
    mime_type: str
    checksum: str
    created_at: datetime
    modified_at: datetime
    invoice_number: Optional[str] = None
    file_type: str = 'pdf'  # pdf, docx, xlsx, etc.
    status: str = 'active'  # active, archived, deleted

class FileStorage:
    """Handles file storage operations for the invoice system"""

    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or Path(__file__).parent / "file_storage"
        self.storage_dir.mkdir(exist_ok=True)

        # Create subdirectories
        self._create_directories()

        # Metadata file
        self.metadata_file = self.storage_dir / "metadata.json"
        self._load_metadata()

    def _create_directories(self):
        """Create organized subdirectories for file storage"""
        subdirs = [
            'invoices',      # Generated invoice PDFs
            'documents',     # Other documents
            'templates',     # Template files
            'backups',       # Database backups
            'temp',          # Temporary files
            'archive'        # Archived files
        ]

        for subdir in subdirs:
            (self.storage_dir / subdir).mkdir(exist_ok=True)

        # Create year/month subdirectories for invoices
        current_year = datetime.now().year
        for year in range(current_year - 2, current_year + 2):  # Last 2 years + current + next
            year_dir = self.storage_dir / 'invoices' / str(year)
            year_dir.mkdir(exist_ok=True)
            for month in range(1, 13):
                month_dir = year_dir / f"{month:02d}"
                month_dir.mkdir(exist_ok=True)

    def _load_metadata(self):
        """Load file metadata from JSON file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.metadata = {k: FileMetadata(**v) for k, v in data.items()}
            except Exception as e:
                print(f"Error loading metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_metadata(self):
        """Save file metadata to JSON file"""
        try:
            data = {}
            for filename, meta in self.metadata.items():
                data[filename] = {
                    'filename': meta.filename,
                    'original_name': meta.original_name,
                    'file_path': str(meta.file_path),
                    'file_size': meta.file_size,
                    'mime_type': meta.mime_type,
                    'checksum': meta.checksum,
                    'created_at': meta.created_at.isoformat(),
                    'modified_at': meta.modified_at.isoformat(),
                    'invoice_number': meta.invoice_number,
                    'file_type': meta.file_type,
                    'status': meta.status
                }

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving metadata: {e}")

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type of file"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'

    def _get_invoice_directory(self, invoice_date: Optional[datetime] = None) -> Path:
        """Get the appropriate directory for storing invoice files"""
        if invoice_date is None:
            invoice_date = datetime.now()

        year_dir = self.storage_dir / 'invoices' / str(invoice_date.year)
        month_dir = year_dir / f"{invoice_date.month:02d}"
        return month_dir

    def save_invoice_file(self, file_path: Path, invoice_number: str,
                         original_name: Optional[str] = None,
                         invoice_date: Optional[datetime] = None) -> Optional[str]:
        """
        Save an invoice file to storage

        Args:
            file_path: Path to the file to save
            invoice_number: Invoice number for organization
            original_name: Original filename (optional)
            invoice_date: Date of invoice for directory organization

        Returns:
            str: Unique filename if successful, None otherwise
        """
        try:
            if not file_path.exists():
                print(f"Source file does not exist: {file_path}")
                return None

            # Determine target directory
            target_dir = self._get_invoice_directory(invoice_date)

            # Generate unique filename
            file_ext = file_path.suffix.lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{invoice_number}_{timestamp}{file_ext}"

            target_path = target_dir / unique_filename

            # Copy file
            shutil.copy2(file_path, target_path)

            # Calculate metadata
            checksum = self._calculate_checksum(target_path)
            mime_type = self._get_mime_type(target_path)
            file_size = target_path.stat().st_size
            created_at = datetime.fromtimestamp(target_path.stat().st_ctime)
            modified_at = datetime.fromtimestamp(target_path.stat().st_mtime)

            # Create metadata entry
            original_name = original_name or file_path.name
            metadata = FileMetadata(
                filename=unique_filename,
                original_name=original_name,
                file_path=target_path,
                file_size=file_size,
                mime_type=mime_type,
                checksum=checksum,
                created_at=created_at,
                modified_at=modified_at,
                invoice_number=invoice_number,
                file_type=file_ext[1:] if file_ext else 'unknown'
            )

            self.metadata[unique_filename] = metadata
            self._save_metadata()

            print(f"Saved invoice file: {unique_filename}")
            return unique_filename

        except Exception as e:
            print(f"Error saving invoice file: {e}")
            return None

    def save_document_file(self, file_path: Path, category: str = 'documents',
                          original_name: Optional[str] = None) -> Optional[str]:
        """
        Save a general document file

        Args:
            file_path: Path to the file to save
            category: Category subdirectory
            original_name: Original filename

        Returns:
            str: Unique filename if successful, None otherwise
        """
        try:
            if not file_path.exists():
                return None

            # Ensure category directory exists
            category_dir = self.storage_dir / category
            category_dir.mkdir(exist_ok=True)

            # Generate unique filename
            file_ext = file_path.suffix.lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{file_path.stem}{file_ext}"

            target_path = category_dir / unique_filename

            # Copy file
            shutil.copy2(file_path, target_path)

            # Calculate metadata
            checksum = self._calculate_checksum(target_path)
            mime_type = self._get_mime_type(target_path)
            file_size = target_path.stat().st_size
            created_at = datetime.fromtimestamp(target_path.stat().st_ctime)
            modified_at = datetime.fromtimestamp(target_path.stat().st_mtime)

            # Create metadata entry
            original_name = original_name or file_path.name
            metadata = FileMetadata(
                filename=unique_filename,
                original_name=original_name,
                file_path=target_path,
                file_size=file_size,
                mime_type=mime_type,
                checksum=checksum,
                created_at=created_at,
                modified_at=modified_at,
                file_type=file_ext[1:] if file_ext else 'unknown'
            )

            self.metadata[unique_filename] = metadata
            self._save_metadata()

            return unique_filename

        except Exception as e:
            print(f"Error saving document file: {e}")
            return None

    def get_file_path(self, filename: str) -> Optional[Path]:
        """
        Get the full path to a stored file

        Args:
            filename: Unique filename

        Returns:
            Path: Full path to file or None if not found
        """
        if filename in self.metadata:
            return self.metadata[filename].file_path
        return None

    def get_invoice_files(self, invoice_number: str) -> List[FileMetadata]:
        """
        Get all files associated with an invoice

        Args:
            invoice_number: Invoice number

        Returns:
            list: List of FileMetadata objects
        """
        return [
            meta for meta in self.metadata.values()
            if meta.invoice_number == invoice_number and meta.status == 'active'
        ]

    def delete_file(self, filename: str, permanent: bool = False) -> bool:
        """
        Delete or archive a file

        Args:
            filename: Unique filename
            permanent: If True, permanently delete; if False, move to archive

        Returns:
            bool: True if successful
        """
        try:
            if filename not in self.metadata:
                return False

            meta = self.metadata[filename]

            if permanent:
                # Permanently delete
                if meta.file_path.exists():
                    meta.file_path.unlink()
                del self.metadata[filename]
            else:
                # Move to archive
                archive_dir = self.storage_dir / 'archive'
                archive_path = archive_dir / meta.filename

                if meta.file_path.exists():
                    shutil.move(meta.file_path, archive_path)
                    meta.file_path = archive_path
                    meta.status = 'archived'
                else:
                    return False

            self._save_metadata()
            return True

        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def list_files(self, file_type: Optional[str] = None,
                  status: str = 'active') -> List[FileMetadata]:
        """
        List files with optional filtering

        Args:
            file_type: Filter by file type (pdf, docx, etc.)
            status: Filter by status (active, archived, deleted)

        Returns:
            list: List of FileMetadata objects
        """
        files = [
            meta for meta in self.metadata.values()
            if meta.status == status
        ]

        if file_type:
            files = [meta for meta in files if meta.file_type == file_type]

        return files

    def get_file_metadata(self, filename: str) -> Optional[FileMetadata]:
        """
        Get metadata for a specific file

        Args:
            filename: Unique filename

        Returns:
            FileMetadata: Metadata object or None
        """
        return self.metadata.get(filename)

    def verify_file_integrity(self, filename: str) -> bool:
        """
        Verify file integrity using checksum

        Args:
            filename: Unique filename

        Returns:
            bool: True if file is intact
        """
        try:
            if filename not in self.metadata:
                return False

            meta = self.metadata[filename]
            if not meta.file_path.exists():
                return False

            current_checksum = self._calculate_checksum(meta.file_path)
            return current_checksum == meta.checksum

        except Exception as e:
            print(f"Error verifying file integrity: {e}")
            return False

    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified hours

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            int: Number of files cleaned up
        """
        try:
            temp_dir = self.storage_dir / 'temp'
            if not temp_dir.exists():
                return 0

            cleaned_count = 0
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

            for file_path in temp_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1

            return cleaned_count

        except Exception as e:
            print(f"Error cleaning up temp files: {e}")
            return 0

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics

        Returns:
            dict: Storage statistics
        """
        try:
            stats = {
                'total_files': len(self.metadata),
                'active_files': len([m for m in self.metadata.values() if m.status == 'active']),
                'archived_files': len([m for m in self.metadata.values() if m.status == 'archived']),
                'total_size_bytes': sum(m.file_size for m in self.metadata.values()),
                'files_by_type': {}
            }

            # Count files by type
            for meta in self.metadata.values():
                file_type = meta.file_type
                if file_type not in stats['files_by_type']:
                    stats['files_by_type'][file_type] = 0
                stats['files_by_type'][file_type] += 1

            # Convert bytes to MB
            stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)

            return stats

        except Exception as e:
            print(f"Error getting storage stats: {e}")
            return {}

    def export_files(self, export_dir: Path, invoice_numbers: Optional[List[str]] = None) -> bool:
        """
        Export files to a directory

        Args:
            export_dir: Directory to export to
            invoice_numbers: List of invoice numbers to export (None for all)

        Returns:
            bool: True if successful
        """
        try:
            export_dir.mkdir(exist_ok=True)

            files_to_export = self.metadata.values()
            if invoice_numbers:
                files_to_export = [
                    meta for meta in files_to_export
                    if meta.invoice_number in invoice_numbers
                ]

            for meta in files_to_export:
                if meta.file_path.exists():
                    # Create subdirectory structure
                    relative_path = meta.file_path.relative_to(self.storage_dir)
                    export_path = export_dir / relative_path
                    export_path.parent.mkdir(parents=True, exist_ok=True)

                    shutil.copy2(meta.file_path, export_path)

            return True

        except Exception as e:
            print(f"Error exporting files: {e}")
            return False

    def create_backup(self, backup_dir: Path) -> bool:
        """
        Create a complete backup of the file storage

        Args:
            backup_dir: Directory to create backup in

        Returns:
            bool: True if successful
        """
        try:
            backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"file_storage_backup_{timestamp}"

            backup_path = backup_dir / backup_name

            # Copy entire storage directory
            shutil.copytree(self.storage_dir, backup_path)

            print(f"Created file storage backup: {backup_path}")
            return True

        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

# Global instance for easy access
file_storage = FileStorage()

def get_file_storage() -> FileStorage:
    """Convenience function to get file storage instance"""
    return file_storage