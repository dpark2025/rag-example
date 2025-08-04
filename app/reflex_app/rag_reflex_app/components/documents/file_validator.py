"""
File validation utilities for document uploads with comprehensive error handling.

Authored by: AI/ML Engineer (Jackson Brown)
Date: 2025-08-04
"""

import reflex as rx
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum
import mimetypes
import os


class FileValidationError(Enum):
    """File validation error types."""
    INVALID_TYPE = "invalid_type"
    TOO_LARGE = "too_large"
    TOO_SMALL = "too_small"
    INVALID_NAME = "invalid_name"
    EMPTY_FILE = "empty_file"
    SECURITY_RISK = "security_risk"
    ENCODING_ERROR = "encoding_error"


class ValidationResult(rx.Base):
    """File validation result."""
    is_valid: bool = True
    error_type: Optional[str] = None
    error_message: str = ""
    file_info: Dict[str, Union[str, int]] = {}
    warnings: List[str] = []


class FileValidator:
    """Comprehensive file validation for document uploads."""
    
    # Supported file types and their MIME types
    SUPPORTED_TYPES = {
        'txt': ['text/plain'],
        'md': ['text/markdown', 'text/x-markdown'],
        'pdf': ['application/pdf'],
        'doc': ['application/msword'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'html': ['text/html'],
        'xml': ['text/xml', 'application/xml'],
        'json': ['application/json'],
        'csv': ['text/csv'],
        'rtf': ['application/rtf'],
        'odt': ['application/vnd.oasis.opendocument.text']
    }
    
    # File size limits (in bytes)
    MIN_FILE_SIZE = 1  # 1 byte minimum
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB maximum
    
    # Security: potentially dangerous file extensions
    BLOCKED_EXTENSIONS = {
        'exe', 'bat', 'cmd', 'com', 'scr', 'pif', 'vbs', 'js', 'jar',
        'app', 'deb', 'pkg', 'dmg', 'rpm', 'msi', 'dll', 'bin'
    }
    
    # Content validation patterns
    SUSPICIOUS_PATTERNS = [
        b'<script',
        b'javascript:',
        b'data:text/html',
        b'<?php',
        b'<%',
        b'#!/bin/',
        b'powershell'
    ]
    
    @classmethod
    def validate_file(cls, file_data: bytes, filename: str, 
                     content_type: Optional[str] = None) -> ValidationResult:
        """
        Comprehensive file validation.
        
        Args:
            file_data: Raw file content as bytes
            filename: Original filename
            content_type: MIME type from upload (optional)
            
        Returns:
            ValidationResult with validation status and details
        """
        result = ValidationResult()
        result.file_info = {
            'filename': filename,
            'size': len(file_data),
            'content_type': content_type or 'unknown'
        }
        
        # 1. Filename validation
        filename_result = cls._validate_filename(filename)
        if not filename_result.is_valid:
            return filename_result
        
        # 2. File size validation
        size_result = cls._validate_file_size(len(file_data))
        if not size_result.is_valid:
            return size_result
            
        # 3. File type validation
        type_result = cls._validate_file_type(filename, content_type, file_data)
        if not type_result.is_valid:
            return type_result
            
        # 4. Security validation
        security_result = cls._validate_security(file_data, filename)
        if not security_result.is_valid:
            return security_result
            
        # 5. Content validation (for text files)
        content_result = cls._validate_content(file_data, filename)
        if content_result.warnings:
            result.warnings.extend(content_result.warnings)
            
        # Merge file info
        result.file_info.update({
            'extension': cls._get_file_extension(filename),
            'detected_type': cls._detect_file_type(filename, file_data),
            'is_text': cls._is_text_file(filename)
        })
        
        return result
    
    @classmethod
    def _validate_filename(cls, filename: str) -> ValidationResult:
        """Validate filename safety and format."""
        result = ValidationResult()
        
        if not filename or filename.strip() == "":
            result.is_valid = False
            result.error_type = FileValidationError.INVALID_NAME.value
            result.error_message = "Filename cannot be empty"
            return result
            
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in filename for char in dangerous_chars):
            result.is_valid = False
            result.error_type = FileValidationError.SECURITY_RISK.value
            result.error_message = f"Filename contains invalid characters: {', '.join(dangerous_chars)}"
            return result
            
        # Check filename length
        if len(filename) > 255:
            result.is_valid = False
            result.error_type = FileValidationError.INVALID_NAME.value
            result.error_message = "Filename too long (max 255 characters)"
            return result
            
        # Check for blocked extensions
        ext = cls._get_file_extension(filename).lower()
        if ext in cls.BLOCKED_EXTENSIONS:
            result.is_valid = False
            result.error_type = FileValidationError.SECURITY_RISK.value
            result.error_message = f"File type '.{ext}' is not allowed for security reasons"
            return result
            
        return result
    
    @classmethod
    def _validate_file_size(cls, size: int) -> ValidationResult:
        """Validate file size is within acceptable limits."""
        result = ValidationResult()
        
        if size < cls.MIN_FILE_SIZE:
            result.is_valid = False
            result.error_type = FileValidationError.EMPTY_FILE.value
            result.error_message = "File is empty or too small"
            return result
            
        if size > cls.MAX_FILE_SIZE:
            result.is_valid = False
            result.error_type = FileValidationError.TOO_LARGE.value
            result.error_message = f"File too large (max {cls.MAX_FILE_SIZE // (1024*1024)}MB)"
            return result
            
        return result
    
    @classmethod
    def _validate_file_type(cls, filename: str, content_type: Optional[str], 
                          file_data: bytes) -> ValidationResult:
        """Validate file type is supported."""
        result = ValidationResult()
        
        # Get file extension
        ext = cls._get_file_extension(filename).lower()
        
        # Check if extension is supported
        if ext not in cls.SUPPORTED_TYPES:
            result.is_valid = False
            result.error_type = FileValidationError.INVALID_TYPE.value
            result.error_message = f"File type '.{ext}' is not supported. Supported types: {', '.join(cls.SUPPORTED_TYPES.keys())}"
            return result
            
        # Validate MIME type if provided
        if content_type:
            expected_types = cls.SUPPORTED_TYPES[ext]
            if content_type not in expected_types:
                result.warnings.append(f"MIME type '{content_type}' doesn't match expected types for .{ext} files")
                
        return result
    
    @classmethod
    def _validate_security(cls, file_data: bytes, filename: str) -> ValidationResult:
        """Perform security validation on file content."""
        result = ValidationResult()
        
        # Check for suspicious patterns in content
        content_lower = file_data.lower()
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if pattern in content_lower:
                result.is_valid = False
                result.error_type = FileValidationError.SECURITY_RISK.value
                result.error_message = "File contains potentially dangerous content"
                return result
                
        # Additional security checks for specific file types
        ext = cls._get_file_extension(filename).lower()
        
        # For text files, check encoding
        if ext in ['txt', 'md', 'html', 'xml', 'json', 'csv']:
            try:
                # Try to decode as UTF-8
                file_data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    # Try other common encodings
                    file_data.decode('latin-1')
                    result.warnings.append("File encoding may not be UTF-8")
                except UnicodeDecodeError:
                    result.is_valid = False
                    result.error_type = FileValidationError.ENCODING_ERROR.value
                    result.error_message = "File has invalid text encoding"
                    return result
                    
        return result
    
    @classmethod
    def _validate_content(cls, file_data: bytes, filename: str) -> ValidationResult:
        """Validate file content quality and structure."""
        result = ValidationResult()
        
        ext = cls._get_file_extension(filename).lower()
        
        # Text file content validation
        if ext in ['txt', 'md']:
            try:
                content = file_data.decode('utf-8')
                
                # Check for minimum content
                if len(content.strip()) < 10:
                    result.warnings.append("File content seems very short")
                    
                # Check for very long lines (potential formatting issues)
                lines = content.split('\n')
                long_lines = [i for i, line in enumerate(lines) if len(line) > 1000]
                if long_lines:
                    result.warnings.append(f"File has very long lines (may affect processing)")
                    
            except UnicodeDecodeError:
                result.warnings.append("Could not validate text content due to encoding issues")
                
        return result
    
    @classmethod
    def _get_file_extension(cls, filename: str) -> str:
        """Get file extension from filename."""
        return os.path.splitext(filename)[1][1:].lower() if '.' in filename else ''
    
    @classmethod
    def _detect_file_type(cls, filename: str, file_data: bytes) -> str:
        """Detect file type from content and filename."""
        ext = cls._get_file_extension(filename)
        
        # Use mimetypes library for additional validation
        mime_type, _ = mimetypes.guess_type(filename)
        
        return mime_type or f"application/{ext}" if ext else "application/octet-stream"
    
    @classmethod
    def _is_text_file(cls, filename: str) -> bool:
        """Check if file is a text-based file."""
        ext = cls._get_file_extension(filename).lower()
        text_extensions = {'txt', 'md', 'html', 'xml', 'json', 'csv', 'rtf'}
        return ext in text_extensions
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of supported file extensions."""
        return list(cls.SUPPORTED_TYPES.keys())
    
    @classmethod
    def get_max_file_size_mb(cls) -> int:
        """Get maximum file size in MB."""
        return cls.MAX_FILE_SIZE // (1024 * 1024)
    
    @classmethod
    def format_file_size(cls, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


def validate_upload_file(file_data: bytes, filename: str, 
                        content_type: Optional[str] = None) -> ValidationResult:
    """
    Convenience function for validating uploaded files.
    
    Args:
        file_data: Raw file content
        filename: Original filename
        content_type: MIME type from upload
        
    Returns:
        ValidationResult with validation status
    """
    return FileValidator.validate_file(file_data, filename, content_type)


def get_validation_summary() -> Dict[str, Union[List[str], int]]:
    """Get summary of validation rules for UI display."""
    return {
        'supported_types': FileValidator.get_supported_extensions(),
        'max_size_mb': FileValidator.get_max_file_size_mb(),
        'blocked_extensions': list(FileValidator.BLOCKED_EXTENSIONS),
        'security_features': [
            'Filename safety validation',
            'Content security scanning',
            'File type verification',
            'Size limit enforcement',
            'Encoding validation'
        ]
    }