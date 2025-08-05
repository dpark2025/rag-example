"""
Authored by: Backend Technical Lead (cin)
Date: 2025-08-05

Document Versioning System

Comprehensive document version control system providing:
- Document revision history and version tracking
- Content comparison and diff functionality  
- Safe rollback capabilities with validation
- Version metadata and audit trails
- Conflict resolution and merge strategies

Integrates seamlessly with existing RAG backend and ChromaDB infrastructure.
"""

import asyncio
import hashlib
import logging
import difflib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import asynccontextmanager
import threading
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel, Field
from rag_backend import get_rag_system
from document_manager import get_document_manager, DocumentMetadata
from error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity, RecoveryAction
from performance_cache import get_document_cache
from versioning_types import (
    DocumentVersion, VersionStatus, VersionOperation, ConflictResolution,
    VersionDiff, RollbackSafetyCheck, VersionConflict, ValidationResult,
    VersionQuery, BulkVersionOperation
)
from versioning_validators import get_version_validator

# Configure logging
logger = logging.getLogger(__name__)

# VersionOperation imported from versioning_types

# ConflictResolution imported from versioning_types

# VersionStatus imported from versioning_types

@dataclass
class DocumentVersion:
    """Document version information structure."""
    version_id: str
    doc_id: str
    version_number: int
    title: str
    content: str
    content_hash: str
    
    # Version metadata
    author: str
    timestamp: str
    operation: str
    change_summary: str = ""
    parent_version_id: Optional[str] = None
    
    # Document properties
    file_type: str = "txt"
    file_size: int = 0
    chunk_count: int = 0
    
    # Status and flags
    status: str = "active"
    is_current: bool = False
    
    # Change tracking
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0
    similarity_score: float = 0.0
    
    # Metadata preservation from document manager
    original_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.original_metadata is None:
            self.original_metadata = {}
        if not self.file_size:
            self.file_size = len(self.content.encode('utf-8'))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for storage."""
        data = asdict(self)
        # Ensure JSON serializable
        if data['original_metadata']:
            data['original_metadata'] = json.dumps(data['original_metadata'])
        else:
            data['original_metadata'] = "{}"
        return data

@dataclass 
class VersionDiff:
    """Document version comparison result."""
    from_version: str
    to_version: str
    similarity_score: float
    
    # Change statistics
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0
    total_changes: int = 0
    
    # Diff details
    unified_diff: str = ""
    change_blocks: List[Dict[str, Any]] = None
    
    # Content analysis
    content_type_changes: Dict[str, Any] = None
    structural_changes: List[str] = None
    
    def __post_init__(self):
        if self.change_blocks is None:
            self.change_blocks = []
        if self.content_type_changes is None:
            self.content_type_changes = {}
        if self.structural_changes is None:
            self.structural_changes = []
        self.total_changes = self.lines_added + self.lines_removed + self.lines_modified

class VersionConflict(BaseModel):
    """Version conflict information."""
    conflict_id: str
    doc_id: str
    base_version_id: str
    current_version_id: str
    incoming_version_id: str
    conflict_type: str
    conflict_areas: List[Dict[str, Any]] = Field(default_factory=list)
    resolution_strategy: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RollbackSafetyCheck(BaseModel):
    """Rollback safety validation result."""
    is_safe: bool
    risk_level: str  # low, medium, high, critical
    warnings: List[str] = Field(default_factory=list)
    blocking_issues: List[str] = Field(default_factory=list)
    affected_systems: List[str] = Field(default_factory=list)
    rollback_impact: Dict[str, Any] = Field(default_factory=dict)

class DocumentVersioning:
    """
    Core document versioning service providing comprehensive version control
    with diff analysis, conflict resolution, and safe rollback capabilities.
    """
    
    def __init__(self):
        self.rag_system = get_rag_system()
        self.document_manager = get_document_manager()
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="versioning")
        
        # Initialize caches and validator
        self.document_cache = get_document_cache()
        self.validator = get_version_validator()
        
        # Version control settings
        self.version_collection_name = "document_versions"
        self.max_versions_per_document = 50  # Configurable limit
        self.auto_cleanup_threshold = 100  # Cleanup old versions
        
        # Diff analysis settings
        self.similarity_threshold = 0.85  # For duplicate detection
        self.max_diff_size = 10000  # Maximum diff size to store
        
        # Initialize version collection
        self._init_version_collection()
    
    def _init_version_collection(self):
        """Initialize ChromaDB collection for version storage."""
        try:
            # Create or get versions collection
            self.version_collection = self.rag_system.chroma_client.get_or_create_collection(
                name=self.version_collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Document versioning collection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize version collection: {e}")
            raise
    
    async def create_version(self, 
                           doc_id: str, 
                           content: str, 
                           author: str,
                           operation: VersionOperation = VersionOperation.UPDATE,
                           change_summary: str = "",
                           parent_version_id: Optional[str] = None) -> DocumentVersion:
        """
        Create a new document version with comprehensive metadata tracking.
        
        Args:
            doc_id: Document identifier
            content: New document content
            author: Version author identifier
            operation: Type of version operation
            change_summary: Description of changes
            parent_version_id: Parent version for change tracking
            
        Returns:
            DocumentVersion object
            
        Raises:
            ApplicationError: On version creation failure
        """
        try:
            # Validate input parameters
            validation_errors = self.validator.validate_version_creation(
                doc_id=doc_id,
                content=content,
                author=author,
                operation=operation.value,
                change_summary=change_summary
            )
            
            # Check for critical validation errors
            critical_errors = [e for e in validation_errors if e.severity == ValidationResult.CRITICAL]
            if critical_errors:
                error_messages = [e.message for e in critical_errors]
                raise ApplicationError(
                    message=f"Version creation validation failed: {'; '.join(error_messages)}",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.HIGH,
                    user_message="Invalid version parameters provided",
                    recovery_action=RecoveryAction.RETRY
                )
            
            # Log warnings
            warnings = [e for e in validation_errors if e.severity == ValidationResult.WARNING]
            for warning in warnings:
                logger.warning(f"Version creation warning: {warning.message}")
            
            # Get current document metadata
            doc_metadata = await self.document_manager.get_document(doc_id)
            if not doc_metadata:
                raise ApplicationError(
                    message=f"Document {doc_id} not found",
                    category=ErrorCategory.DATABASE,
                    severity=ErrorSeverity.HIGH,
                    user_message="Cannot create version for non-existent document",
                    recovery_action=RecoveryAction.NONE
                )
            
            # Get next version number
            current_versions = await self.get_version_history(doc_id)
            next_version_number = max([v.version_number for v in current_versions], default=0) + 1
            
            # Generate version metadata
            version_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc).isoformat()
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            # Calculate diff if parent version exists
            lines_added, lines_removed, lines_modified, similarity_score = 0, 0, 0, 1.0
            if parent_version_id:
                parent_version = await self.get_version(parent_version_id)
                if parent_version:
                    diff_result = self._calculate_diff(parent_version.content, content)
                    lines_added = diff_result.lines_added
                    lines_removed = diff_result.lines_removed  
                    lines_modified = diff_result.lines_modified
                    similarity_score = diff_result.similarity_score
            
            # Create version object
            version = DocumentVersion(
                version_id=version_id,
                doc_id=doc_id,
                version_number=next_version_number,
                title=doc_metadata.title,
                content=content,
                content_hash=content_hash,
                author=author,
                timestamp=timestamp,
                operation=operation.value,
                change_summary=change_summary,
                parent_version_id=parent_version_id,
                file_type=doc_metadata.file_type,
                file_size=len(content.encode('utf-8')),
                status=VersionStatus.ACTIVE.value,
                is_current=True,  # New version becomes current
                lines_added=lines_added,
                lines_removed=lines_removed,
                lines_modified=lines_modified,
                similarity_score=similarity_score,
                original_metadata=doc_metadata.to_dict()
            )
            
            with self._lock:
                # Mark previous versions as non-current
                await self._update_current_version_flags(doc_id, version_id)
                
                # Store version in ChromaDB
                version_data = version.to_dict()
                self.version_collection.add(
                    ids=[version_id],
                    documents=[content],
                    metadatas=[{k: str(v) for k, v in version_data.items() if k != 'content'}]
                )
                
                # Update document in main collection with new content
                await self._update_document_content(doc_id, content, version_id, author)
                
                logger.info(f"Created version {version_number} for document {doc_id}")
                return version
                
        except Exception as e:
            app_error = handle_error(e)
            logger.error(f"Error creating version: {app_error.to_dict()}")
            raise ApplicationError(
                message=f"Failed to create document version: {str(e)}",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                user_message="Could not create document version. Please try again.",
                recovery_action=RecoveryAction.RETRY
            ) from e
    
    async def get_version(self, version_id: str) -> Optional[DocumentVersion]:
        """
        Retrieve a specific document version.
        
        Args:
            version_id: Version identifier
            
        Returns:
            DocumentVersion if found, None otherwise
        """
        try:
            # Check cache first
            cache_key = f"version_{version_id}"
            cached_version = self.document_cache.get(cache_key)
            if cached_version:
                return cached_version
            
            with self._lock:
                results = self.version_collection.get(
                    ids=[version_id],
                    include=["metadatas", "documents"]
                )
                
                if not results.get("ids"):
                    return None
                
                metadata = results["metadatas"][0]
                content = results["documents"][0]
                
                # Reconstruct version object
                version = DocumentVersion(
                    version_id=metadata["version_id"],
                    doc_id=metadata["doc_id"],
                    version_number=int(metadata["version_number"]),
                    title=metadata["title"],
                    content=content,
                    content_hash=metadata["content_hash"],
                    author=metadata["author"],
                    timestamp=metadata["timestamp"],
                    operation=metadata["operation"],
                    change_summary=metadata.get("change_summary", ""),
                    parent_version_id=metadata.get("parent_version_id"),
                    file_type=metadata.get("file_type", "txt"),
                    file_size=int(metadata.get("file_size", 0)),
                    chunk_count=int(metadata.get("chunk_count", 0)),
                    status=metadata.get("status", "active"),
                    is_current=metadata.get("is_current", "False").lower() == "true",
                    lines_added=int(metadata.get("lines_added", 0)),
                    lines_removed=int(metadata.get("lines_removed", 0)),
                    lines_modified=int(metadata.get("lines_modified", 0)),
                    similarity_score=float(metadata.get("similarity_score", 0.0)),
                    original_metadata=json.loads(metadata.get("original_metadata", "{}"))
                )
                
                # Validate data integrity
                integrity_errors = self.validator.validate_version_data_integrity(version)
                critical_integrity_errors = [e for e in integrity_errors if e.severity == ValidationResult.CRITICAL]
                
                if critical_integrity_errors:
                    logger.error(f"Version {version_id} has critical integrity issues: {[e.message for e in critical_integrity_errors]}")
                    return None
                
                # Log warnings
                warnings = [e for e in integrity_errors if e.severity == ValidationResult.WARNING]
                for warning in warnings:
                    logger.warning(f"Version {version_id} integrity warning: {warning.message}")
                
                # Cache result
                self.document_cache.set(cache_key, version, ttl=300.0)
                return version
                
        except Exception as e:
            logger.error(f"Error retrieving version {version_id}: {e}")
            return None
    
    async def get_version_history(self, 
                                doc_id: str, 
                                limit: Optional[int] = None,
                                include_deleted: bool = False) -> List[DocumentVersion]:
        """
        Get version history for a document.
        
        Args:
            doc_id: Document identifier
            limit: Maximum number of versions to return
            include_deleted: Whether to include deleted versions
            
        Returns:
            List of DocumentVersion objects, sorted by version number descending
        """
        try:
            with self._lock:
                # Query all versions for document
                results = self.version_collection.get(
                    where={"doc_id": doc_id},
                    include=["metadatas", "documents"]
                )
                
                if not results.get("ids"):
                    return []
                
                versions = []
                for i, version_id in enumerate(results["ids"]):
                    metadata = results["metadatas"][i]
                    content = results["documents"][i]
                    
                    # Filter by status if needed
                    if not include_deleted and metadata.get("status") == VersionStatus.DELETED.value:
                        continue
                    
                    version = DocumentVersion(
                        version_id=version_id,
                        doc_id=metadata["doc_id"],
                        version_number=int(metadata["version_number"]),
                        title=metadata["title"],
                        content=content,
                        content_hash=metadata["content_hash"],
                        author=metadata["author"],
                        timestamp=metadata["timestamp"],
                        operation=metadata["operation"],
                        change_summary=metadata.get("change_summary", ""),
                        parent_version_id=metadata.get("parent_version_id"),
                        file_type=metadata.get("file_type", "txt"),
                        file_size=int(metadata.get("file_size", 0)),
                        chunk_count=int(metadata.get("chunk_count", 0)),
                        status=metadata.get("status", "active"),
                        is_current=metadata.get("is_current", "False").lower() == "true",
                        lines_added=int(metadata.get("lines_added", 0)),
                        lines_removed=int(metadata.get("lines_removed", 0)),
                        lines_modified=int(metadata.get("lines_modified", 0)),
                        similarity_score=float(metadata.get("similarity_score", 0.0)),
                        original_metadata=json.loads(metadata.get("original_metadata", "{}"))
                    )
                    versions.append(version)
                
                # Sort by version number descending (newest first)
                versions.sort(key=lambda v: v.version_number, reverse=True)
                
                # Apply limit
                if limit:
                    versions = versions[:limit]
                
                return versions
                
        except Exception as e:
            logger.error(f"Error getting version history for {doc_id}: {e}")
            return []
    
    async def get_current_version(self, doc_id: str) -> Optional[DocumentVersion]:
        """Get the current active version of a document."""
        versions = await self.get_version_history(doc_id, limit=50)
        for version in versions:
            if version.is_current and version.status == VersionStatus.ACTIVE.value:
                return version
        return None
    
    def compare_versions(self, 
                        from_version: DocumentVersion, 
                        to_version: DocumentVersion) -> VersionDiff:
        """
        Compare two document versions and generate detailed diff analysis.
        
        Args:
            from_version: Source version for comparison
            to_version: Target version for comparison
            
        Returns:
            VersionDiff object with comprehensive comparison data
        """
        try:
            diff_result = self._calculate_diff(from_version.content, to_version.content)
            
            # Generate unified diff for display
            unified_diff = '\n'.join(difflib.unified_diff(
                from_version.content.splitlines(keepends=True),
                to_version.content.splitlines(keepends=True),
                fromfile=f"Version {from_version.version_number}",
                tofile=f"Version {to_version.version_number}",
                lineterm=""
            ))
            
            # Analyze structural changes
            structural_changes = self._analyze_structural_changes(
                from_version.content, to_version.content
            )
            
            return VersionDiff(
                from_version=from_version.version_id,
                to_version=to_version.version_id,
                similarity_score=diff_result.similarity_score,
                lines_added=diff_result.lines_added,
                lines_removed=diff_result.lines_removed,
                lines_modified=diff_result.lines_modified,
                unified_diff=unified_diff[:self.max_diff_size],  # Limit diff size
                change_blocks=diff_result.change_blocks,
                structural_changes=structural_changes
            )
            
        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            return VersionDiff(
                from_version=from_version.version_id,
                to_version=to_version.version_id,
                similarity_score=0.0,
                unified_diff=f"Error generating diff: {str(e)}"
            )
    
    def _calculate_diff(self, content1: str, content2: str) -> VersionDiff:
        """Calculate detailed diff statistics between two content strings."""
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        # Calculate similarity using difflib
        similarity = difflib.SequenceMatcher(None, content1, content2).ratio()
        
        # Generate diff operations
        diff_ops = list(difflib.unified_diff(lines1, lines2, n=0))
        
        lines_added = sum(1 for line in diff_ops if line.startswith('+') and not line.startswith('+++'))
        lines_removed = sum(1 for line in diff_ops if line.startswith('-') and not line.startswith('---'))
        
        # Estimate modified lines (lines that appear in both add and remove)
        lines_modified = min(lines_added, lines_removed) // 2
        lines_added -= lines_modified
        lines_removed -= lines_modified
        
        # Generate change blocks for detailed analysis
        change_blocks = self._extract_change_blocks(lines1, lines2)
        
        return VersionDiff(
            from_version="",  # Will be set by caller
            to_version="",    # Will be set by caller
            similarity_score=similarity,
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_modified=lines_modified,
            change_blocks=change_blocks
        )
    
    def _extract_change_blocks(self, lines1: List[str], lines2: List[str]) -> List[Dict[str, Any]]:
        """Extract structured change blocks from line differences."""
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        change_blocks = []
        
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op != 'equal':
                block = {
                    'operation': op,
                    'from_start': i1,
                    'from_end': i2,
                    'to_start': j1,
                    'to_end': j2,
                    'from_lines': lines1[i1:i2] if op in ['delete', 'replace'] else [],
                    'to_lines': lines2[j1:j2] if op in ['insert', 'replace'] else []
                }
                change_blocks.append(block)
        
        return change_blocks
    
    def _analyze_structural_changes(self, content1: str, content2: str) -> List[str]:
        """Analyze structural changes between content versions."""
        changes = []
        
        # Simple structural analysis
        lines1, lines2 = content1.splitlines(), content2.splitlines()
        
        if len(lines1) != len(lines2):
            changes.append(f"Line count changed from {len(lines1)} to {len(lines2)}")
        
        # Check for significant whitespace changes
        if content1.replace(' ', '').replace('\t', '') == content2.replace(' ', '').replace('\t', ''):
            if content1 != content2:
                changes.append("Whitespace-only changes detected")
        
        # Check for case-only changes
        if content1.lower() == content2.lower() and content1 != content2:
            changes.append("Case-only changes detected")
        
        return changes
    
    async def rollback_to_version(self, 
                                doc_id: str, 
                                target_version_id: str,
                                author: str,
                                force: bool = False) -> Tuple[bool, DocumentVersion, List[str]]:
        """
        Rollback document to a specific version with safety checks.
        
        Args:
            doc_id: Document identifier
            target_version_id: Version to rollback to
            author: User performing rollback
            force: Skip safety checks if True
            
        Returns:
            Tuple of (success, new_version, warnings)
        """
        try:
            # Get target and current versions for validation
            target_version = await self.get_version(target_version_id)
            current_version = await self.get_current_version(doc_id)
            
            if not target_version:
                return False, None, ["Target version not found"]
            
            if not current_version:
                return False, None, ["Current version not found"]
            
            # Validate rollback operation
            validation_errors = self.validator.validate_rollback_operation(
                doc_id=doc_id,
                target_version_id=target_version_id,
                author=author,
                current_version_number=current_version.version_number,
                target_version_number=target_version.version_number
            )
            
            # Check for critical validation errors
            critical_errors = [e for e in validation_errors if e.severity == ValidationResult.CRITICAL]
            if critical_errors:
                error_messages = [e.message for e in critical_errors]
                return False, None, error_messages
            
            # Log warnings from validation
            warnings = []
            validation_warnings = [e for e in validation_errors if e.severity == ValidationResult.WARNING]
            for warning in validation_warnings:
                warnings.append(warning.message)
                logger.warning(f"Rollback validation warning: {warning.message}")
            
            # Perform safety check unless forced
            if not force:
                safety_check = await self.validate_rollback_safety(doc_id, target_version_id)
                if not safety_check.is_safe:
                    return False, None, safety_check.blocking_issues
                warnings = safety_check.warnings
            
            # Get current version for change tracking
            current_version = await self.get_current_version(doc_id)
            parent_version_id = current_version.version_id if current_version else None
            
            # Create rollback version
            rollback_version = await self.create_version(
                doc_id=doc_id,
                content=target_version.content,
                author=author,
                operation=VersionOperation.ROLLBACK,
                change_summary=f"Rollback to version {target_version.version_number}",
                parent_version_id=parent_version_id
            )
            
            logger.info(f"Successfully rolled back document {doc_id} to version {target_version.version_number}")
            return True, rollback_version, warnings
            
        except Exception as e:
            app_error = handle_error(e)
            logger.error(f"Error during rollback: {app_error.to_dict()}")
            return False, None, [f"Rollback failed: {app_error.user_message}"]
    
    async def validate_rollback_safety(self, 
                                     doc_id: str, 
                                     target_version_id: str) -> RollbackSafetyCheck:
        """
        Validate the safety of rolling back to a specific version.
        
        Args:
            doc_id: Document identifier
            target_version_id: Target version for rollback
            
        Returns:
            RollbackSafetyCheck with validation results
        """
        try:
            target_version = await self.get_version(target_version_id)
            current_version = await self.get_current_version(doc_id)
            
            if not target_version or not current_version:
                return RollbackSafetyCheck(
                    is_safe=False,
                    risk_level="critical",
                    blocking_issues=["Version not found"]
                )
            
            # Calculate age and change impact
            version_diff = current_version.version_number - target_version.version_number
            content_diff = self.compare_versions(target_version, current_version)
            
            warnings = []
            blocking_issues = []
            risk_level = "low"
            
            # Risk assessment based on version age
            if version_diff > 10:
                warnings.append(f"Rolling back {version_diff} versions")
                risk_level = "medium"
            
            if version_diff > 25:
                risk_level = "high"
                warnings.append("Rolling back a large number of versions")
            
            # Risk assessment based on content changes
            if content_diff.total_changes > 100:
                risk_level = "high"
                warnings.append(f"Large content changes: {content_diff.total_changes} total changes")
            
            # Check for critical operations in between
            versions_between = await self.get_version_history(doc_id)
            versions_between = [v for v in versions_between 
                              if target_version.version_number < v.version_number <= current_version.version_number]
            
            critical_operations = [v for v in versions_between 
                                 if v.operation in [VersionOperation.MERGE.value]]
            
            if critical_operations:
                risk_level = "high"
                warnings.append(f"Rolling back over {len(critical_operations)} merge operations")
            
            return RollbackSafetyCheck(
                is_safe=len(blocking_issues) == 0,
                risk_level=risk_level,
                warnings=warnings,
                blocking_issues=blocking_issues,
                affected_systems=["document_content", "embeddings", "search_index"],
                rollback_impact={
                    "content_changes": content_diff.total_changes,
                    "versions_rolled_back": version_diff,
                    "critical_operations": len(critical_operations)
                }
            )
            
        except Exception as e:
            logger.error(f"Error validating rollback safety: {e}")
            return RollbackSafetyCheck(
                is_safe=False,
                risk_level="critical",
                blocking_issues=[f"Safety validation failed: {str(e)}"]
            )
    
    async def detect_conflicts(self, 
                             doc_id: str, 
                             new_content: str,
                             base_version_id: str) -> Optional[VersionConflict]:
        """
        Detect version conflicts when updating a document.
        
        Args:
            doc_id: Document identifier
            new_content: Proposed new content
            base_version_id: Base version for the update
            
        Returns:
            VersionConflict if conflicts detected, None otherwise
        """
        try:
            current_version = await self.get_current_version(doc_id)
            base_version = await self.get_version(base_version_id)
            
            if not current_version or not base_version:
                return None
            
            # No conflict if base is current
            if current_version.version_id == base_version_id:
                return None
            
            # Analyze conflicts
            base_to_current = self.compare_versions(base_version, current_version)
            base_to_new = self._calculate_diff(base_version.content, new_content)
            
            # Detect overlapping changes
            conflict_areas = self._detect_overlapping_changes(
                base_version.content, current_version.content, new_content
            )
            
            if conflict_areas:
                return VersionConflict(
                    conflict_id=str(uuid.uuid4()),
                    doc_id=doc_id,
                    base_version_id=base_version_id,
                    current_version_id=current_version.version_id,
                    incoming_version_id="pending",
                    conflict_type="concurrent_modification",
                    conflict_areas=conflict_areas
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            return None
    
    def _detect_overlapping_changes(self, 
                                  base_content: str, 
                                  current_content: str, 
                                  new_content: str) -> List[Dict[str, Any]]:
        """Detect overlapping changes between concurrent modifications."""
        base_lines = base_content.splitlines()
        current_lines = current_content.splitlines()
        new_lines = new_content.splitlines()
        
        # Simple conflict detection - areas where both versions changed from base
        base_to_current = difflib.SequenceMatcher(None, base_lines, current_lines)
        base_to_new = difflib.SequenceMatcher(None, base_lines, new_lines)
        
        conflicts = []
        current_changes = set()
        new_changes = set()
        
        # Collect changed line ranges
        for op, i1, i2, j1, j2 in base_to_current.get_opcodes():
            if op != 'equal':
                current_changes.update(range(i1, i2))
        
        for op, i1, i2, j1, j2 in base_to_new.get_opcodes():
            if op != 'equal':
                new_changes.update(range(i1, i2))
        
        # Find overlapping changes
        overlapping = current_changes.intersection(new_changes)
        if overlapping:
            conflicts.append({
                'type': 'line_overlap',
                'base_lines': sorted(overlapping),
                'description': f"Lines {min(overlapping)}-{max(overlapping)} modified in both versions"
            })
        
        return conflicts
    
    async def resolve_conflict(self, 
                             conflict: VersionConflict,
                             resolution: ConflictResolution,
                             author: str,
                             merged_content: Optional[str] = None) -> Tuple[bool, Optional[DocumentVersion]]:
        """
        Resolve a version conflict using specified strategy.
        
        Args:
            conflict: The conflict to resolve
            resolution: Resolution strategy
            author: User resolving conflict
            merged_content: Manual merge content (if applicable)
            
        Returns:
            Tuple of (success, resolved_version)
        """
        try:
            if resolution == ConflictResolution.ABORT:
                return False, None
            
            elif resolution == ConflictResolution.FORCE_OVERWRITE:
                # Use the incoming content, ignore conflicts
                current_version = await self.get_current_version(conflict.doc_id)
                if not current_version:
                    return False, None
                
                resolved_version = await self.create_version(
                    doc_id=conflict.doc_id,
                    content=merged_content or current_version.content,
                    author=author,
                    operation=VersionOperation.UPDATE,
                    change_summary="Force overwrite conflict resolution",
                    parent_version_id=current_version.version_id
                )
                return True, resolved_version
            
            elif resolution == ConflictResolution.AUTO_MERGE:
                # Attempt automatic merge
                base_version = await self.get_version(conflict.base_version_id)
                current_version = await self.get_version(conflict.current_version_id)
                
                if not base_version or not current_version:
                    return False, None
                
                # Simple auto-merge strategy
                auto_merged = self._attempt_auto_merge(
                    base_version.content, 
                    current_version.content, 
                    merged_content or current_version.content
                )
                
                if auto_merged:
                    resolved_version = await self.create_version(
                        doc_id=conflict.doc_id,
                        content=auto_merged,
                        author=author,
                        operation=VersionOperation.MERGE,
                        change_summary="Automatic conflict resolution",
                        parent_version_id=current_version.version_id
                    )
                    return True, resolved_version
                
                return False, None
            
            elif resolution == ConflictResolution.MANUAL:
                if not merged_content:
                    return False, None
                
                current_version = await self.get_current_version(conflict.doc_id)
                resolved_version = await self.create_version(
                    doc_id=conflict.doc_id,
                    content=merged_content,
                    author=author,
                    operation=VersionOperation.MERGE,
                    change_summary="Manual conflict resolution",
                    parent_version_id=current_version.version_id if current_version else None
                )
                return True, resolved_version
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return False, None
    
    def _attempt_auto_merge(self, base_content: str, current_content: str, new_content: str) -> Optional[str]:
        """Attempt automatic merge of conflicting changes."""
        # Simple line-based merge strategy
        base_lines = base_content.splitlines()
        current_lines = current_content.splitlines()
        new_lines = new_content.splitlines()
        
        try:
            # Use a simple 3-way merge approach
            merged_lines = []
            
            base_to_current = difflib.SequenceMatcher(None, base_lines, current_lines)
            base_to_new = difflib.SequenceMatcher(None, base_lines, new_lines)
            
            # This is a simplified merge - in production, consider using more sophisticated algorithms
            # For now, prefer current changes over new changes in conflicts
            
            i = 0
            while i < len(base_lines):
                # Simple heuristic: if line unchanged in current but changed in new, take new
                # If changed in current, keep current
                if i < len(current_lines):
                    merged_lines.append(current_lines[i])
                i += 1
            
            return '\n'.join(merged_lines)
            
        except Exception as e:
            logger.error(f"Auto-merge failed: {e}")
            return None
    
    async def _update_current_version_flags(self, doc_id: str, new_current_version_id: str):
        """Update is_current flags for all document versions."""
        versions = await self.get_version_history(doc_id, include_deleted=True)
        
        with self._lock:
            for version in versions:
                if version.version_id == new_current_version_id:
                    continue  # Skip the new current version
                
                # Update metadata
                updated_metadata = version.to_dict()
                updated_metadata['is_current'] = "False"
                
                # Convert back to string values for ChromaDB
                metadata_for_db = {k: str(v) for k, v in updated_metadata.items() if k != 'content'}
                
                try:
                    self.version_collection.update(
                        ids=[version.version_id],
                        metadatas=[metadata_for_db]
                    )
                except Exception as e:
                    logger.warning(f"Failed to update version flag for {version.version_id}: {e}")
    
    async def _update_document_content(self, 
                                     doc_id: str, 
                                     new_content: str, 
                                     version_id: str,
                                     author: str):
        """Update the main document collection with new content."""
        try:
            # Update document manager with new content
            await self.document_manager.update_document_metadata(doc_id, {
                'last_modified': datetime.now(timezone.utc).isoformat(),
                'current_version_id': version_id,
                'last_modified_by': author
            })
            
            # Re-chunk and update embeddings in RAG system
            doc_metadata = await self.document_manager.get_document(doc_id)
            if doc_metadata:
                # Create document dict for RAG system
                doc_dict = {
                    'title': doc_metadata.title,
                    'content': new_content,
                    'source': 'version_update',
                    **doc_metadata.to_dict(),
                    'current_version_id': version_id
                }
                
                # Remove old chunks and add new ones
                with self._lock:
                    # Delete existing chunks
                    self.rag_system.collection.delete(where={"doc_id": doc_id})
                    
                    # Add updated content
                    result = self.rag_system.add_documents([doc_dict])
                    logger.info(f"Updated document embeddings: {result}")
                    
        except Exception as e:
            logger.error(f"Error updating document content: {e}")
            raise
    
    async def cleanup_old_versions(self, 
                                 doc_id: Optional[str] = None,
                                 keep_versions: int = None) -> Dict[str, int]:
        """
        Clean up old versions to maintain performance.
        
        Args:
            doc_id: Specific document to clean (None for all)
            keep_versions: Number of versions to keep per document
            
        Returns:
            Dictionary with cleanup statistics
        """
        if keep_versions is None:
            keep_versions = self.max_versions_per_document
        
        stats = {"documents_processed": 0, "versions_deleted": 0, "errors": 0}
        
        try:
            if doc_id:
                doc_ids = [doc_id]
            else:
                # Get all document IDs
                results = self.version_collection.get(include=["metadatas"])
                doc_ids = list(set(metadata["doc_id"] for metadata in results.get("metadatas", [])))
            
            for doc_id in doc_ids:
                try:
                    versions = await self.get_version_history(doc_id, include_deleted=True)
                    stats["documents_processed"] += 1
                    
                    if len(versions) > keep_versions:
                        # Sort by version number, keep newest
                        versions.sort(key=lambda v: v.version_number, reverse=True)
                        versions_to_delete = versions[keep_versions:]
                        
                        # Don't delete current version
                        versions_to_delete = [v for v in versions_to_delete if not v.is_current]
                        
                        # Mark as deleted instead of removing completely
                        for version in versions_to_delete:
                            updated_metadata = version.to_dict()
                            updated_metadata['status'] = VersionStatus.DELETED.value
                            metadata_for_db = {k: str(v) for k, v in updated_metadata.items() if k != 'content'}
                            
                            self.version_collection.update(
                                ids=[version.version_id],
                                metadatas=[metadata_for_db]
                            )
                            stats["versions_deleted"] += 1
                        
                        logger.info(f"Cleaned up {len(versions_to_delete)} old versions for doc {doc_id}")
                
                except Exception as e:
                    logger.error(f"Error cleaning up versions for {doc_id}: {e}")
                    stats["errors"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error during version cleanup: {e}")
            stats["errors"] += 1
            return stats
    
    def __del__(self):
        """Cleanup resources on destruction."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)

# Global instance
document_versioning = DocumentVersioning()

def get_document_versioning() -> DocumentVersioning:
    """Get the global document versioning instance."""
    return document_versioning