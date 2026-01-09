# file_utils.py - Utilities for file handling and validation
import os
import uuid
import re
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

# Configuration
UPLOADS_BASE_DIR = os.path.join("static", "uploads")
ATTACHMENTS_DIR = os.path.join(UPLOADS_BASE_DIR, "attachments")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file
MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB total per message

# Allowed MIME types and extensions
ALLOWED_EXTENSIONS = {
    # Images
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/webp': ['.webp'],
    'image/gif': ['.gif'],
    # Documents
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'text/plain': ['.txt'],
    # Add more as needed
}

ALLOWED_EXTENSIONS_FLAT = set()
for exts in ALLOWED_EXTENSIONS.values():
    ALLOWED_EXTENSIONS_FLAT.update(exts)

def ensure_attachments_dir():
    """Ensure attachments directory exists"""
    if not os.path.exists(ATTACHMENTS_DIR):
        os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

def is_allowed_file(filename, mime_type=None):
    """Check if file is allowed based on extension and optionally MIME type"""
    if not filename:
        return False
    
    # Get extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS_FLAT:
        return False
    
    # If MIME type provided, verify it matches extension
    if mime_type:
        allowed_exts = ALLOWED_EXTENSIONS.get(mime_type, [])
        if ext not in allowed_exts:
            return False
    
    return True

def sanitize_filename(filename):
    """Sanitize filename to prevent directory traversal and other attacks"""
    # Remove path components
    filename = os.path.basename(filename)
    # Use werkzeug's secure_filename
    filename = secure_filename(filename)
    # Remove any remaining dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    return filename

def save_attachment(file_storage, subfolder=''):
    """Save an uploaded file and return metadata
    
    Args:
        file_storage: Werkzeug FileStorage object
        subfolder: Optional subfolder (e.g., 'emails', 'messages')
    
    Returns:
        dict with: filename, original_name, mime_type, size, file_path
    """
    ensure_attachments_dir()
    
    # Validate
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided")
    
    original_name = file_storage.filename
    mime_type = file_storage.content_type
    
    # Validate file
    if not is_allowed_file(original_name, mime_type):
        raise ValueError(f"Tipo de archivo no permitido: {original_name}")
    
    # Check size
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise ValueError(f"Archivo muy grande: {size} bytes (máximo: {MAX_FILE_SIZE})")
    
    if size == 0:
        raise ValueError("Archivo vacío")
    
    # Sanitize filename
    safe_name = sanitize_filename(original_name)
    
    # Generate unique filename
    ext = os.path.splitext(safe_name)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    # Determine save path
    if subfolder:
        save_dir = os.path.join(ATTACHMENTS_DIR, subfolder)
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, unique_filename)
        relative_path = f"attachments/{subfolder}/{unique_filename}"
    else:
        file_path = os.path.join(ATTACHMENTS_DIR, unique_filename)
        relative_path = f"attachments/{unique_filename}"
    
    # Save file
    file_storage.save(file_path)
    
    # Convertir a path absoluto para uso en email_sender
    absolute_path = os.path.abspath(file_path)
    
    return {
        'filename': unique_filename,
        'original_name': safe_name,
        'mime_type': mime_type,
        'size': size,
        'file_path': relative_path,
        'absolute_path': absolute_path  # Path absoluto real
    }

def validate_attachments(files):
    """Validate multiple files
    
    Args:
        files: List of FileStorage objects or dict with 'file' key
    
    Returns:
        tuple: (is_valid, error_message, total_size)
    """
    if not files:
        return True, None, 0
    
    total_size = 0
    for file_item in files:
        if isinstance(file_item, dict):
            file_storage = file_item.get('file')
        else:
            file_storage = file_item
        
        if not file_storage or not file_storage.filename:
            continue
        
        # Check extension
        if not is_allowed_file(file_storage.filename):
            return False, f"Tipo de archivo no permitido: {file_storage.filename}", 0
        
        # Check size
        file_storage.seek(0, os.SEEK_END)
        size = file_storage.tell()
        file_storage.seek(0)
        
        if size > MAX_FILE_SIZE:
            return False, f"Archivo muy grande: {file_storage.filename} ({size} bytes)", 0
        
        total_size += size
    
    if total_size > MAX_TOTAL_SIZE:
        return False, f"Tamaño total excede el límite: {total_size} bytes (máximo: {MAX_TOTAL_SIZE})", 0
    
    return True, None, total_size

def get_file_icon(mime_type, filename):
    """Get icon emoji based on file type"""
    if mime_type:
        if mime_type.startswith('image/'):
            return '🖼️'
        elif mime_type == 'application/pdf':
            return '📄'
        elif 'word' in mime_type or filename.endswith(('.doc', '.docx')):
            return '📝'
        elif 'excel' in mime_type or filename.endswith(('.xls', '.xlsx')):
            return '📊'
        elif mime_type == 'text/plain':
            return '📄'
    
    return '📎'

def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

