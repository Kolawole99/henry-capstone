"""
Input validation utilities for the Nexus-Mind API.

Provides validators for UUIDs, strings, files, and other input types
to ensure data integrity and security.
"""

import re
import uuid
from typing import Optional, List
from pathlib import Path


# Validation constants
MAX_MESSAGE_LENGTH = 5000
MIN_MESSAGE_LENGTH = 1

MAX_AGENT_NAME_LENGTH = 100
MIN_AGENT_NAME_LENGTH = 1

MAX_AGENT_DESCRIPTION_LENGTH = 1000
MIN_AGENT_DESCRIPTION_LENGTH = 10

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
ALLOWED_FILE_EXTENSIONS = {'.pdf', '.txt', '.md', '.docx', '.doc'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'text/plain',
    'text/markdown',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword'
}

# Regex patterns
AGENT_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-]+$')
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.]+$')


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_uuid(value: str, field_name: str = "ID") -> str:
    """
    Validate and parse a UUID string.
    
    Args:
        value: UUID string to validate
        field_name: Name of the field for error messages
        
    Returns:
        Validated UUID string
        
    Raises:
        ValidationError: If the UUID is invalid
    """
    try:
        # Try to parse as UUID
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj)
    except (ValueError, AttributeError, TypeError):
        raise ValidationError(f"{field_name} must be a valid UUID")


def validate_string_length(
    value: str,
    min_length: int,
    max_length: int,
    field_name: str = "Field"
) -> str:
    """
    Validate string length.
    
    Args:
        value: String to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        field_name: Name of the field for error messages
        
    Returns:
        Validated string
        
    Raises:
        ValidationError: If the string length is invalid
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    length = len(value.strip())
    
    if length < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} character{'s' if min_length != 1 else ''}"
        )
    
    if length > max_length:
        raise ValidationError(
            f"{field_name} must be at most {max_length} characters"
        )
    
    return value.strip()


def validate_message(message: str) -> str:
    """
    Validate a chat message.
    
    Args:
        message: Message to validate
        
    Returns:
        Validated message
        
    Raises:
        ValidationError: If the message is invalid
    """
    return validate_string_length(
        message,
        MIN_MESSAGE_LENGTH,
        MAX_MESSAGE_LENGTH,
        "Message"
    )


def validate_agent_name(name: str) -> str:
    """
    Validate an agent name.
    
    Args:
        name: Agent name to validate
        
    Returns:
        Validated agent name
        
    Raises:
        ValidationError: If the name is invalid
    """
    validated = validate_string_length(
        name,
        MIN_AGENT_NAME_LENGTH,
        MAX_AGENT_NAME_LENGTH,
        "Agent name"
    )
    
    if not AGENT_NAME_PATTERN.match(validated):
        raise ValidationError(
            "Agent name can only contain letters, numbers, spaces, and hyphens"
        )
    
    return validated


def validate_agent_description(description: str) -> str:
    """
    Validate an agent description.
    
    Args:
        description: Agent description to validate
        
    Returns:
        Validated agent description
        
    Raises:
        ValidationError: If the description is invalid
    """
    return validate_string_length(
        description,
        MIN_AGENT_DESCRIPTION_LENGTH,
        MAX_AGENT_DESCRIPTION_LENGTH,
        "Agent description"
    )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove any path components
    filename = Path(filename).name
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s\-.]', '', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"
    
    return filename


def validate_file_extension(filename: str) -> str:
    """
    Validate file extension.
    
    Args:
        filename: Filename to validate
        
    Returns:
        Validated filename
        
    Raises:
        ValidationError: If the file extension is not allowed
    """
    ext = Path(filename).suffix.lower()
    
    if ext not in ALLOWED_FILE_EXTENSIONS:
        allowed = ', '.join(sorted(ALLOWED_FILE_EXTENSIONS))
        raise ValidationError(
            f"File type '{ext}' is not allowed. Allowed types: {allowed}"
        )
    
    return filename


def validate_file_size(size_bytes: int) -> int:
    """
    Validate file size.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Validated file size
        
    Raises:
        ValidationError: If the file is too large
    """
    if size_bytes > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        actual_mb = size_bytes / (1024 * 1024)
        raise ValidationError(
            f"File size ({actual_mb:.1f}MB) exceeds maximum allowed size ({max_mb:.0f}MB)"
        )
    
    if size_bytes == 0:
        raise ValidationError("File is empty")
    
    return size_bytes


def validate_file(filename: str, size_bytes: int) -> tuple[str, int]:
    """
    Validate a file upload.
    
    Args:
        filename: Original filename
        size_bytes: File size in bytes
        
    Returns:
        Tuple of (sanitized_filename, validated_size)
        
    Raises:
        ValidationError: If the file is invalid
    """
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Validate extension
    validate_file_extension(safe_filename)
    
    # Validate size
    validated_size = validate_file_size(size_bytes)
    
    return safe_filename, validated_size
