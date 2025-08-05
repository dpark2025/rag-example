"""
Shared types and enums for document versioning system.

This module contains all shared data structures to avoid circular imports
between document_versioning.py and versioning_validators.py.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class VersionStatus(Enum):
    """Status of a document version."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"


class VersionOperation(Enum):
    """Types of version operations."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ROLLBACK = "rollback"
    MERGE = "merge"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    MANUAL = "manual"
    AUTO_MERGE = "auto_merge"
    LATEST_WINS = "latest_wins"
    OLDEST_WINS = "oldest_wins"
    USER_CHOICE = "user_choice"


@dataclass
class DocumentVersion:
    """Represents a version of a document with metadata."""
    version_id: str
    document_id: str
    version_number: int
    content_hash: str
    title: str
    content: str
    author: str = "system"
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: VersionStatus = VersionStatus.ACTIVE
    change_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_version: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class VersionDiff:
    """Represents differences between two document versions."""
    from_version: str
    to_version: str
    from_version_number: int
    to_version_number: int
    similarity_score: float
    unified_diff: str
    added_lines: int
    removed_lines: int
    modified_lines: int
    change_percentage: float
    significant_changes: List[str] = field(default_factory=list)
    metadata_changes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackSafetyCheck:
    """Safety validation result for rollback operations."""
    is_safe: bool
    risk_level: str  # "low", "medium", "high"
    warnings: List[str] = field(default_factory=list)
    blocking_issues: List[str] = field(default_factory=list)
    impact_assessment: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    estimated_affected_documents: int = 0
    rollback_strategy: Optional[str] = None


@dataclass
class VersionConflict:
    """Represents a conflict between document versions."""
    conflict_id: str
    document_id: str
    base_version: str
    conflicting_versions: List[str]
    conflict_type: str
    conflict_details: Dict[str, Any] = field(default_factory=dict)
    resolution_strategy: Optional[ConflictResolution] = None
    resolution_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation operations."""
    is_valid: bool
    score: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_time: Optional[datetime] = field(default_factory=datetime.utcnow)
    validator_version: str = "1.0.0"


@dataclass
class VersionQuery:
    """Query parameters for version operations."""
    document_id: Optional[str] = None
    version_number: Optional[int] = None
    status: Optional[VersionStatus] = None
    author: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = 50
    offset: int = 0
    include_content: bool = False
    include_metadata: bool = True


@dataclass
class BulkVersionOperation:
    """Represents a bulk operation on multiple versions."""
    operation_id: str
    operation_type: VersionOperation
    target_versions: List[str]
    operation_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    results: List[Dict[str, Any]] = field(default_factory=list)
    error_count: int = 0
    success_count: int = 0


# Type aliases for convenience
VersionList = List[DocumentVersion]
DiffList = List[VersionDiff]
ConflictList = List[VersionConflict]
ValidationResults = List[ValidationResult]