"""
Authored by: Backend Technical Lead (cin)
Date: 2025-08-05

Document Versioning Validators

Comprehensive validation and safety checks for document versioning operations.
Provides robust error handling, data integrity validation, and security checks
to ensure reliable version control functionality.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from document_versioning import DocumentVersion, VersionOperation, ConflictResolution, VersionStatus
from error_handlers import ApplicationError, ErrorCategory, ErrorSeverity, RecoveryAction

logger = logging.getLogger(__name__)

class ValidationResult(Enum):
    """Validation result types."""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationError:
    """Validation error information."""
    code: str
    message: str
    severity: ValidationResult
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class DocumentVersionValidator:
    """
    Comprehensive validator for document versioning operations.
    
    Provides validation for version creation, rollback operations,
    conflict resolution, and data integrity checks.
    """
    
    def __init__(self):
        # Validation limits and thresholds
        self.max_content_size = 50 * 1024 * 1024  # 50MB
        self.max_change_summary_length = 1000
        self.max_author_length = 100
        self.max_title_length = 500
        self.min_similarity_for_duplicate = 0.99
        
        # Security constraints
        self.allowed_operations = [op.value for op in VersionOperation]
        self.allowed_statuses = [status.value for status in VersionStatus]
        self.max_rollback_distance = 100  # Maximum versions to rollback
        
    def validate_version_creation(self, 
                                doc_id: str,
                                content: str,
                                author: str,
                                operation: str,
                                change_summary: str = "",
                                title: str = "") -> List[ValidationError]:
        """
        Validate version creation parameters.
        
        Args:
            doc_id: Document identifier
            content: Document content
            author: Version author
            operation: Version operation type
            change_summary: Change description
            title: Document title
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate required fields
        if not doc_id or not doc_id.strip():
            errors.append(ValidationError(
                code="MISSING_DOC_ID",
                message="Document ID is required",
                severity=ValidationResult.CRITICAL,
                field="doc_id"
            ))
        
        if not content:
            errors.append(ValidationError(
                code="MISSING_CONTENT",
                message="Document content is required",
                severity=ValidationResult.CRITICAL,
                field="content"
            ))
        
        if not author or not author.strip():
            errors.append(ValidationError(
                code="MISSING_AUTHOR",
                message="Author is required",
                severity=ValidationResult.CRITICAL,
                field="author"
            ))
        
        # Validate field lengths and formats
        if content and len(content.encode('utf-8')) > self.max_content_size:
            errors.append(ValidationError(
                code="CONTENT_TOO_LARGE",
                message=f"Content size exceeds maximum of {self.max_content_size} bytes",
                severity=ValidationResult.ERROR,
                field="content",
                details={"max_size": self.max_content_size, "actual_size": len(content.encode('utf-8'))}
            ))
        
        if author and len(author) > self.max_author_length:
            errors.append(ValidationError(
                code="AUTHOR_TOO_LONG",
                message=f"Author name exceeds maximum length of {self.max_author_length}",
                severity=ValidationResult.ERROR,
                field="author"
            ))
        
        if change_summary and len(change_summary) > self.max_change_summary_length:
            errors.append(ValidationError(
                code="SUMMARY_TOO_LONG",
                message=f"Change summary exceeds maximum length of {self.max_change_summary_length}",
                severity=ValidationResult.ERROR,
                field="change_summary"
            ))
        
        if title and len(title) > self.max_title_length:
            errors.append(ValidationError(
                code="TITLE_TOO_LONG",
                message=f"Title exceeds maximum length of {self.max_title_length}",
                severity=ValidationResult.ERROR,
                field="title"
            ))
        
        # Validate operation type
        if operation not in self.allowed_operations:
            errors.append(ValidationError(
                code="INVALID_OPERATION",
                message=f"Invalid operation type: {operation}",
                severity=ValidationResult.ERROR,
                field="operation",
                details={"allowed_operations": self.allowed_operations}
            ))
        
        # Content quality checks
        if content:
            content_errors = self._validate_content_quality(content)
            errors.extend(content_errors)
        
        # Security validation
        security_errors = self._validate_security_constraints(doc_id, author, content)
        errors.extend(security_errors)
        
        return errors
    
    def validate_rollback_operation(self,
                                  doc_id: str,
                                  target_version_id: str,
                                  author: str,
                                  current_version_number: int,
                                  target_version_number: int) -> List[ValidationError]:
        """
        Validate rollback operation parameters and safety.
        
        Args:
            doc_id: Document identifier
            target_version_id: Target version for rollback
            author: User performing rollback
            current_version_number: Current version number
            target_version_number: Target version number
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Required field validation
        if not doc_id or not doc_id.strip():
            errors.append(ValidationError(
                code="MISSING_DOC_ID",
                message="Document ID is required for rollback",
                severity=ValidationResult.CRITICAL,
                field="doc_id"
            ))
        
        if not target_version_id or not target_version_id.strip():
            errors.append(ValidationError(
                code="MISSING_TARGET_VERSION",
                message="Target version ID is required",
                severity=ValidationResult.CRITICAL,
                field="target_version_id"
            ))
        
        if not author or not author.strip():
            errors.append(ValidationError(
                code="MISSING_AUTHOR",
                message="Author is required for rollback operation",
                severity=ValidationResult.CRITICAL,
                field="author"
            ))
        
        # Rollback distance validation
        if current_version_number and target_version_number:
            rollback_distance = current_version_number - target_version_number
            
            if rollback_distance <= 0:
                errors.append(ValidationError(
                    code="INVALID_ROLLBACK_TARGET",
                    message="Cannot rollback to current or future version",
                    severity=ValidationResult.ERROR,
                    field="target_version_id",
                    details={"current_version": current_version_number, "target_version": target_version_number}
                ))
            elif rollback_distance > self.max_rollback_distance:
                errors.append(ValidationError(
                    code="ROLLBACK_TOO_DISTANT",
                    message=f"Rollback distance ({rollback_distance}) exceeds maximum allowed ({self.max_rollback_distance})",
                    severity=ValidationResult.WARNING,
                    field="target_version_id",
                    details={"rollback_distance": rollback_distance, "max_allowed": self.max_rollback_distance}
                ))
        
        return errors
    
    def validate_conflict_resolution(self,
                                   conflict_id: str,
                                   resolution_strategy: str,
                                   author: str,
                                   merged_content: Optional[str] = None) -> List[ValidationError]:
        """
        Validate conflict resolution parameters.
        
        Args:
            conflict_id: Conflict identifier
            resolution_strategy: Resolution strategy
            author: User resolving conflict
            merged_content: Merged content (for manual resolution)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Required fields
        if not conflict_id or not conflict_id.strip():
            errors.append(ValidationError(
                code="MISSING_CONFLICT_ID",
                message="Conflict ID is required",
                severity=ValidationResult.CRITICAL,
                field="conflict_id"
            ))
        
        if not author or not author.strip():
            errors.append(ValidationError(
                code="MISSING_AUTHOR",
                message="Author is required for conflict resolution",
                severity=ValidationResult.CRITICAL,
                field="author"
            ))
        
        # Validate resolution strategy
        try:
            resolution = ConflictResolution(resolution_strategy)
        except ValueError:
            errors.append(ValidationError(
                code="INVALID_RESOLUTION_STRATEGY",
                message=f"Invalid resolution strategy: {resolution_strategy}",
                severity=ValidationResult.ERROR,
                field="resolution_strategy",
                details={"allowed_strategies": [r.value for r in ConflictResolution]}
            ))
            return errors
        
        # Manual resolution requires merged content
        if resolution == ConflictResolution.MANUAL:
            if not merged_content:
                errors.append(ValidationError(
                    code="MISSING_MERGED_CONTENT",
                    message="Merged content is required for manual conflict resolution",
                    severity=ValidationResult.CRITICAL,
                    field="merged_content"
                ))
            elif len(merged_content.encode('utf-8')) > self.max_content_size:
                errors.append(ValidationError(
                    code="MERGED_CONTENT_TOO_LARGE",
                    message=f"Merged content size exceeds maximum of {self.max_content_size} bytes",
                    severity=ValidationResult.ERROR,
                    field="merged_content"
                ))
        
        return errors
    
    def validate_version_data_integrity(self, version: DocumentVersion) -> List[ValidationError]:
        """
        Validate version data integrity and consistency.
        
        Args:
            version: Version object to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Content hash validation
        if version.content:
            calculated_hash = hashlib.sha256(version.content.encode('utf-8')).hexdigest()
            if version.content_hash != calculated_hash:
                errors.append(ValidationError(
                    code="INVALID_CONTENT_HASH",
                    message="Content hash does not match calculated hash",
                    severity=ValidationResult.CRITICAL,
                    field="content_hash",
                    details={"expected": calculated_hash, "actual": version.content_hash}
                ))
        
        # File size consistency
        if version.content:
            calculated_size = len(version.content.encode('utf-8'))
            if version.file_size != calculated_size:
                errors.append(ValidationError(
                    code="INCONSISTENT_FILE_SIZE",
                    message="File size does not match content length",
                    severity=ValidationResult.WARNING,
                    field="file_size",
                    details={"calculated": calculated_size, "stored": version.file_size}
                ))
        
        # Version number validation
        if version.version_number <= 0:
            errors.append(ValidationError(
                code="INVALID_VERSION_NUMBER",
                message="Version number must be positive",
                severity=ValidationResult.ERROR,
                field="version_number"
            ))
        
        # Timestamp validation
        try:
            timestamp = datetime.fromisoformat(version.timestamp.replace('Z', '+00:00'))
            if timestamp > datetime.now(timezone.utc):
                errors.append(ValidationError(
                    code="FUTURE_TIMESTAMP",
                    message="Version timestamp cannot be in the future",
                    severity=ValidationResult.WARNING,
                    field="timestamp"
                ))
        except ValueError:
            errors.append(ValidationError(
                code="INVALID_TIMESTAMP",
                message="Invalid timestamp format",
                severity=ValidationResult.ERROR,
                field="timestamp"
            ))
        
        # Status validation
        if version.status not in self.allowed_statuses:
            errors.append(ValidationError(
                code="INVALID_STATUS",
                message=f"Invalid version status: {version.status}",
                severity=ValidationResult.ERROR,
                field="status"
            ))
        
        return errors
    
    def _validate_content_quality(self, content: str) -> List[ValidationError]:
        """Validate content quality and detect potential issues."""
        errors = []
        
        # Check for extremely short content
        if len(content.strip()) < 10:
            errors.append(ValidationError(
                code="CONTENT_TOO_SHORT",
                message="Content appears to be too short (less than 10 characters)",
                severity=ValidationResult.WARNING,
                field="content"
            ))
        
        # Check for potential encoding issues
        try:
            content.encode('utf-8')
        except UnicodeEncodeError as e:
            errors.append(ValidationError(
                code="ENCODING_ERROR",
                message="Content contains invalid characters that cannot be encoded",
                severity=ValidationResult.ERROR,
                field="content",
                details={"encoding_error": str(e)}
            ))
        
        # Check for suspicious binary content
        if '\x00' in content:
            errors.append(ValidationError(
                code="BINARY_CONTENT_DETECTED",
                message="Content appears to contain binary data",
                severity=ValidationResult.WARNING,
                field="content"
            ))
        
        # Check for extremely repetitive content (potential spam)
        lines = content.split('\n')
        if len(lines) > 10:
            unique_lines = set(lines)
            if len(unique_lines) < len(lines) * 0.3:  # Less than 30% unique lines
                errors.append(ValidationError(
                    code="HIGHLY_REPETITIVE_CONTENT",
                    message="Content appears to be highly repetitive",
                    severity=ValidationResult.WARNING,
                    field="content"
                ))
        
        return errors
    
    def _validate_security_constraints(self, doc_id: str, author: str, content: str) -> List[ValidationError]:
        """Validate security constraints and detect potential threats."""
        errors = []
        
        # Check for SQL injection patterns (basic detection)
        sql_patterns = ['DROP TABLE', 'DELETE FROM', 'INSERT INTO', 'UPDATE SET', '--', ';--']
        content_upper = content.upper()
        
        for pattern in sql_patterns:
            if pattern in content_upper:
                errors.append(ValidationError(
                    code="POTENTIAL_SQL_INJECTION",
                    message=f"Content contains potential SQL injection pattern: {pattern}",
                    severity=ValidationResult.WARNING,
                    field="content",
                    details={"pattern": pattern}
                ))
                break
        
        # Check for script injection (basic detection)
        script_patterns = ['<script', 'javascript:', 'eval(', 'document.cookie']
        content_lower = content.lower()
        
        for pattern in script_patterns:
            if pattern in content_lower:
                errors.append(ValidationError(
                    code="POTENTIAL_SCRIPT_INJECTION",
                    message=f"Content contains potential script injection pattern: {pattern}",
                    severity=ValidationResult.WARNING,
                    field="content",
                    details={"pattern": pattern}
                ))
                break
        
        # Validate author format (basic email or username validation)
        if author:
            if len(author) > 100:
                errors.append(ValidationError(
                    code="AUTHOR_TOO_LONG",
                    message="Author name is suspiciously long",
                    severity=ValidationResult.WARNING,
                    field="author"
                ))
            
            # Check for potential injection in author field
            if any(char in author for char in ['<', '>', '"', "'"]):
                errors.append(ValidationError(
                    code="AUTHOR_CONTAINS_SUSPICIOUS_CHARS",
                    message="Author field contains potentially unsafe characters",
                    severity=ValidationResult.WARNING,
                    field="author"
                ))
        
        return errors
    
    def validate_cleanup_operation(self, 
                                 doc_id: Optional[str],
                                 keep_versions: int,
                                 total_versions: int) -> List[ValidationError]:
        """
        Validate version cleanup operation parameters.
        
        Args:
            doc_id: Document ID (None for global cleanup)
            keep_versions: Number of versions to keep
            total_versions: Total number of versions
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate keep_versions parameter
        if keep_versions <= 0:
            errors.append(ValidationError(
                code="INVALID_KEEP_VERSIONS",
                message="Number of versions to keep must be positive",
                severity=ValidationResult.ERROR,
                field="keep_versions"
            ))
        
        if keep_versions > 100:
            errors.append(ValidationError(
                code="KEEP_VERSIONS_TOO_HIGH",
                message="Number of versions to keep seems excessive (>100)",
                severity=ValidationResult.WARNING,
                field="keep_versions"
            ))
        
        # Check if cleanup would delete too many versions
        if total_versions > 0 and keep_versions < total_versions:
            versions_to_delete = total_versions - keep_versions
            deletion_percentage = (versions_to_delete / total_versions) * 100
            
            if deletion_percentage > 80:
                errors.append(ValidationError(
                    code="EXCESSIVE_VERSION_DELETION",
                    message=f"Cleanup would delete {deletion_percentage:.1f}% of versions",
                    severity=ValidationResult.WARNING,
                    field="keep_versions",
                    details={"versions_to_delete": versions_to_delete, "total_versions": total_versions}
                ))
        
        return errors

# Global validator instance
version_validator = DocumentVersionValidator()

def get_version_validator() -> DocumentVersionValidator:
    """Get the global version validator instance."""
    return version_validator