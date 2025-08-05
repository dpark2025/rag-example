"""
Authored by: Backend Technical Lead (cin)
Date: 2025-08-04

Document Manager Service

Core service for document CRUD operations, metadata management, and ChromaDB integration.
Provides comprehensive document lifecycle management with transaction safety and performance optimization.
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import threading
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel, Field
from .rag_backend import get_rag_system
from .error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity, RecoveryAction
from .performance_cache import get_document_cache

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DocumentMetadata:
    """Document metadata structure."""
    doc_id: str
    title: str
    file_type: str
    original_filename: str
    file_size: int
    upload_timestamp: str
    status: str = "ready"
    chunk_count: int = 0
    content_preview: str = ""
    source: str = "api_upload"
    
    # Document intelligence fields
    document_type: str = "plain_text"
    content_structure: str = "unstructured"
    intelligence_confidence: float = 0.5
    suggested_chunk_size: int = 400
    suggested_overlap: int = 50
    processing_notes: List[str] = None
    
    # PDF-specific fields
    extraction_method: Optional[str] = None
    quality_score: Optional[float] = None
    page_count: Optional[int] = None
    
    # Error handling
    error_message: str = ""
    last_modified: str = ""
    
    def __post_init__(self):
        if self.processing_notes is None:
            self.processing_notes = []
        if not self.last_modified:
            self.last_modified = self.upload_timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = asdict(self)
        # Convert list to string for ChromaDB compatibility
        if data['processing_notes']:
            data['processing_notes'] = "; ".join(data['processing_notes'])
        else:
            data['processing_notes'] = ""
        return data

class DocumentFilter(BaseModel):
    """Document filtering parameters."""
    file_type: Optional[str] = None
    status: Optional[str] = None
    title_contains: Optional[str] = None
    uploaded_after: Optional[datetime] = None
    uploaded_before: Optional[datetime] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = 0

class BulkOperationResult(BaseModel):
    """Result of bulk operations."""
    success_count: int = 0
    error_count: int = 0
    total_chunks_affected: int = 0
    errors: List[Dict[str, str]] = Field(default_factory=list)
    processing_time: float = 0.0

class DocumentManager:
    """
    Core document management service providing CRUD operations with transaction safety,
    performance optimization, and comprehensive error handling.
    """
    
    def __init__(self):
        self.rag_system = get_rag_system()
        self._lock = threading.RLock()  # Thread-safe operations
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="doc_mgr")
        
        # Initialize document cache
        self.document_cache = get_document_cache()
        
        # Batch processing settings
        self.batch_size = 50  # Process documents in batches
        self.bulk_operation_timeout = 300.0  # 5 minutes
        
    async def create_document(self, 
                            title: str, 
                            content: str, 
                            metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, DocumentMetadata]:
        """
        Create a new document with metadata management.
        
        Args:
            title: Document title
            content: Document content
            metadata: Additional metadata
            
        Returns:
            Tuple of (doc_id, DocumentMetadata)
            
        Raises:
            ApplicationError: On creation failure
        """
        try:
            # Generate unique document ID
            timestamp = datetime.now().isoformat()
            doc_id = hashlib.md5(f"{title}_{timestamp}".encode()).hexdigest()[:12]
            
            # Create document metadata
            doc_metadata = DocumentMetadata(
                doc_id=doc_id,
                title=title,
                file_type=metadata.get("file_type", "txt") if metadata else "txt",
                original_filename=metadata.get("original_filename", title) if metadata else title,
                file_size=len(content),
                upload_timestamp=timestamp,
                status="processing",
                source=metadata.get("source", "api_create") if metadata else "api_create"
            )
            
            # Add additional metadata if provided
            if metadata:
                for key, value in metadata.items():
                    if hasattr(doc_metadata, key):
                        setattr(doc_metadata, key, value)
            
            # Create document object for RAG system
            doc_dict = {
                "title": title,
                "content": content,
                "source": doc_metadata.source,
                **doc_metadata.to_dict()
            }
            
            # Add to RAG system with thread safety
            with self._lock:
                result = self.rag_system.add_documents([doc_dict])
                
                # Extract chunk count from result
                chunk_count = 1
                if "(" in result and "chunks)" in result:
                    try:
                        chunk_count = int(result.split("(")[1].split(" chunks)")[0])
                    except ValueError:
                        pass
                
                # Update metadata with chunk count and status
                doc_metadata.chunk_count = chunk_count
                doc_metadata.status = "ready"
                doc_metadata.content_preview = content[:150] + "..." if len(content) > 150 else content
            
            logger.info(f"Created document {doc_id} with {chunk_count} chunks")
            return doc_id, doc_metadata
            
        except Exception as e:
            app_error = handle_error(e)
            logger.error(f"Error creating document: {app_error.to_dict()}")
            raise ApplicationError(
                message=f"Failed to create document: {str(e)}",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                user_message="Could not create document. Please try again.",
                recovery_action=RecoveryAction.RETRY
            ) from e

    async def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        """
        Retrieve document metadata by ID with caching.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            DocumentMetadata if found, None otherwise
        """
        # Try cache first
        cache_key = self.document_cache._generate_key("doc_metadata", doc_id)
        cached_doc = self.document_cache.get(cache_key)
        if cached_doc is not None:
            logger.debug(f"Retrieved document {doc_id} from cache")
            return cached_doc
        
        try:
            with self._lock:
                # Query ChromaDB for document chunks
                results = self.rag_system.collection.get(
                    where={"doc_id": doc_id},
                    include=["metadatas"]
                )
                
                # Try integer conversion if string search fails
                if not results.get("ids"):
                    try:
                        results = self.rag_system.collection.get(
                            where={"doc_id": int(doc_id)},
                            include=["metadatas"]
                        )
                    except (ValueError, TypeError):
                        pass
                
                if not results.get("metadatas"):
                    return None
                
                # Build metadata from first chunk (all chunks share same document metadata)
                metadata_dict = results["metadatas"][0]
                
                # Convert processing_notes back to list
                processing_notes = []
                if metadata_dict.get("processing_notes"):
                    processing_notes = metadata_dict["processing_notes"].split("; ")
                
                doc_metadata = DocumentMetadata(
                    doc_id=str(metadata_dict.get("doc_id", doc_id)),
                    title=metadata_dict.get("title", "Unknown"),
                    file_type=metadata_dict.get("file_type", "txt"),
                    original_filename=metadata_dict.get("original_filename", ""),
                    file_size=int(metadata_dict.get("file_size", 0)),
                    upload_timestamp=metadata_dict.get("upload_timestamp", ""),
                    status=metadata_dict.get("status", "ready"),
                    chunk_count=len(results["ids"]),
                    content_preview=metadata_dict.get("content_preview", ""),
                    source=metadata_dict.get("source", "unknown"),
                    document_type=metadata_dict.get("document_type", "plain_text"),
                    content_structure=metadata_dict.get("content_structure", "unstructured"),
                    intelligence_confidence=float(metadata_dict.get("intelligence_confidence", 0.5)),
                    suggested_chunk_size=int(metadata_dict.get("suggested_chunk_size", 400)),
                    suggested_overlap=int(metadata_dict.get("suggested_overlap", 50)),
                    processing_notes=processing_notes,
                    extraction_method=metadata_dict.get("extraction_method"),
                    quality_score=float(metadata_dict.get("quality_score")) if metadata_dict.get("quality_score") else None,
                    page_count=int(metadata_dict.get("page_count")) if metadata_dict.get("page_count") else None,
                    error_message=metadata_dict.get("error_message", ""),
                    last_modified=metadata_dict.get("last_modified", metadata_dict.get("upload_timestamp", ""))
                )
                
                # Cache the result
                self.document_cache.set(cache_key, doc_metadata, ttl=600.0)  # 10 minutes
                logger.debug(f"Cached document metadata for {doc_id}")
                
                return doc_metadata
                
        except Exception as e:
            app_error = handle_error(e)
            logger.error(f"Error retrieving document {doc_id}: {app_error.to_dict()}")
            return None

    async def list_documents(self, 
                           document_filter: Optional[DocumentFilter] = None) -> Tuple[List[DocumentMetadata], int]:
        """
        List documents with filtering and pagination.
        
        Args:
            document_filter: Filtering criteria
            
        Returns:
            Tuple of (documents_list, total_count)
        """
        try:
            with self._lock:
                # Get all documents from ChromaDB
                results = self.rag_system.collection.get(include=["metadatas"])
                
                if not results.get("metadatas"):
                    return [], 0
                
                # Group by document ID to avoid duplicates
                doc_groups = {}
                for metadata in results["metadatas"]:
                    doc_id = str(metadata.get("doc_id", "unknown"))
                    
                    if doc_id not in doc_groups:
                        # Convert processing_notes back to list
                        processing_notes = []
                        if metadata.get("processing_notes"):
                            processing_notes = metadata["processing_notes"].split("; ")
                        
                        doc_groups[doc_id] = DocumentMetadata(
                            doc_id=doc_id,
                            title=metadata.get("title", "Unknown"),
                            file_type=metadata.get("file_type", "txt"),
                            original_filename=metadata.get("original_filename", ""),
                            file_size=int(metadata.get("file_size", 0)),
                            upload_timestamp=metadata.get("upload_timestamp", ""),
                            status=metadata.get("status", "ready"),
                            chunk_count=0,  # Will be calculated
                            content_preview=metadata.get("content_preview", ""),
                            source=metadata.get("source", "unknown"),
                            document_type=metadata.get("document_type", "plain_text"),
                            content_structure=metadata.get("content_structure", "unstructured"),
                            intelligence_confidence=float(metadata.get("intelligence_confidence", 0.5)),
                            suggested_chunk_size=int(metadata.get("suggested_chunk_size", 400)),
                            suggested_overlap=int(metadata.get("suggested_overlap", 50)),
                            processing_notes=processing_notes,
                            extraction_method=metadata.get("extraction_method"),
                            quality_score=float(metadata.get("quality_score")) if metadata.get("quality_score") else None,
                            page_count=int(metadata.get("page_count")) if metadata.get("page_count") else None,
                            error_message=metadata.get("error_message", ""),
                            last_modified=metadata.get("last_modified", metadata.get("upload_timestamp", ""))
                        )
                    
                    # Increment chunk count
                    doc_groups[doc_id].chunk_count += 1
                
                documents = list(doc_groups.values())
                
                # Apply filters
                if document_filter:
                    documents = self._apply_filters(documents, document_filter)
                
                total_count = len(documents)
                
                # Apply pagination
                if document_filter and document_filter.limit:
                    offset = document_filter.offset or 0
                    documents = documents[offset:offset + document_filter.limit]
                
                # Sort by upload date (newest first) by default
                documents.sort(key=lambda x: x.upload_timestamp, reverse=True)
                
                return documents, total_count
                
        except Exception as e:
            app_error = handle_error(e)
            logger.error(f"Error listing documents: {app_error.to_dict()}")
            return [], 0

    def _apply_filters(self, documents: List[DocumentMetadata], filter_obj: DocumentFilter) -> List[DocumentMetadata]:
        """Apply filtering criteria to document list."""
        filtered = documents
        
        if filter_obj.file_type:
            filtered = [d for d in filtered if d.file_type == filter_obj.file_type]
        
        if filter_obj.status:
            filtered = [d for d in filtered if d.status == filter_obj.status]
        
        if filter_obj.title_contains:
            query = filter_obj.title_contains.lower()
            filtered = [d for d in filtered if query in d.title.lower()]
        
        if filter_obj.min_size:
            filtered = [d for d in filtered if d.file_size >= filter_obj.min_size]
        
        if filter_obj.max_size:
            filtered = [d for d in filtered if d.file_size <= filter_obj.max_size]
        
        if filter_obj.uploaded_after:
            after_str = filter_obj.uploaded_after.isoformat()
            filtered = [d for d in filtered if d.upload_timestamp >= after_str]
        
        if filter_obj.uploaded_before:
            before_str = filter_obj.uploaded_before.isoformat()
            filtered = [d for d in filtered if d.upload_timestamp <= before_str]
        
        return filtered

    async def update_document_metadata(self, 
                                     doc_id: str, 
                                     updates: Dict[str, Any]) -> bool:
        """
        Update document metadata.
        
        Args:
            doc_id: Document identifier
            updates: Metadata updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                # Get current document chunks
                results = self.rag_system.collection.get(
                    where={"doc_id": doc_id},
                    include=["metadatas", "documents"]
                )
                
                # Try integer conversion if string search fails
                if not results.get("ids"):
                    try:
                        results = self.rag_system.collection.get(
                            where={"doc_id": int(doc_id)},
                            include=["metadatas", "documents"]
                        )
                    except (ValueError, TypeError):
                        return False
                
                if not results.get("ids"):
                    return False
                
                # Update metadata for all chunks
                updated_metadatas = []
                for metadata in results["metadatas"]:
                    updated_metadata = metadata.copy()
                    updated_metadata.update(updates)
                    updated_metadata["last_modified"] = datetime.now().isoformat()
                    updated_metadatas.append(updated_metadata)
                
                # Update in ChromaDB
                self.rag_system.collection.update(
                    ids=results["ids"],
                    metadatas=updated_metadatas
                )
                
                logger.info(f"Updated metadata for document {doc_id}")
                return True
                
        except Exception as e:
            app_error = handle_error(e)
            logger.error(f"Error updating document {doc_id}: {app_error.to_dict()}")
            return False

    async def delete_document(self, doc_id: str) -> Tuple[bool, int]:
        """
        Delete a document and all its chunks.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Tuple of (success, chunks_deleted)
        """
        try:
            with self._lock:
                # Get all chunks for this document
                results = self.rag_system.collection.get(
                    where={"doc_id": doc_id},
                    include=["metadatas"]
                )
                
                # Try integer conversion if string search fails
                if not results.get("ids"):
                    try:
                        results = self.rag_system.collection.get(
                            where={"doc_id": int(doc_id)},
                            include=["metadatas"]
                        )
                    except (ValueError, TypeError):
                        pass
                
                chunk_ids = results.get("ids", [])
                if not chunk_ids:
                    logger.warning(f"Document {doc_id} not found for deletion")
                    return False, 0
                
                # Delete all chunks
                self.rag_system.collection.delete(ids=chunk_ids)
                
                logger.info(f"Deleted document {doc_id} with {len(chunk_ids)} chunks")
                return True, len(chunk_ids)
                
        except Exception as e:
            app_error = handle_error(e)
            logger.error(f"Error deleting document {doc_id}: {app_error.to_dict()}")
            return False, 0

    async def bulk_delete_documents(self, doc_ids: List[str]) -> BulkOperationResult:
        """
        Delete multiple documents in bulk with batch processing.
        
        Args:
            doc_ids: List of document identifiers
            
        Returns:
            BulkOperationResult with operation statistics
        """
        start_time = datetime.now()
        result = BulkOperationResult()
        
        # Process in batches for better performance
        batches = [doc_ids[i:i + self.batch_size] for i in range(0, len(doc_ids), self.batch_size)]
        
        logger.info(f"Starting bulk delete of {len(doc_ids)} documents in {len(batches)} batches")
        
        for batch_num, batch in enumerate(batches, 1):
            logger.debug(f"Processing batch {batch_num}/{len(batches)} ({len(batch)} docs)")
            
            # Process batch concurrently
            tasks = [self.delete_document(doc_id) for doc_id in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for doc_id, batch_result in zip(batch, batch_results):
                try:
                    if isinstance(batch_result, Exception):
                        result.error_count += 1
                        result.errors.append({
                            "doc_id": doc_id,
                            "error": str(batch_result)
                        })
                    else:
                        success, chunks_deleted = batch_result
                        if success:
                            result.success_count += 1
                            result.total_chunks_affected += chunks_deleted
                            
                            # Invalidate cache
                            cache_key = self.document_cache._generate_key("doc_metadata", doc_id)
                            self.document_cache.delete(cache_key)
                        else:
                            result.error_count += 1
                            result.errors.append({
                                "doc_id": doc_id,
                                "error": "Document not found or deletion failed"
                            })
                            
                except Exception as e:
                    result.error_count += 1
                    result.errors.append({
                        "doc_id": doc_id,
                        "error": str(e)
                    })
        
        end_time = datetime.now()
        result.processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Bulk delete completed in {result.processing_time:.2f}s: "
                   f"{result.success_count} success, {result.error_count} errors")
        return result

    async def get_document_count(self, status_filter: Optional[str] = None) -> int:
        """
        Get total document count with optional status filtering.
        
        Args:
            status_filter: Optional status to filter by
            
        Returns:
            Document count
        """
        try:
            documents, _ = await self.list_documents()
            
            if status_filter:
                documents = [d for d in documents if d.status == status_filter]
            
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage and performance statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            with self._lock:
                total_chunks = self.rag_system.collection.count()
                documents, doc_count = await self.list_documents()
                
                # Calculate statistics
                total_size = sum(doc.file_size for doc in documents)
                avg_chunks_per_doc = total_chunks / max(doc_count, 1)
                
                # Get file type distribution
                file_types = {}
                for doc in documents:
                    file_types[doc.file_type] = file_types.get(doc.file_type, 0) + 1
                
                return {
                    "total_documents": doc_count,
                    "total_chunks": total_chunks,
                    "total_size_bytes": total_size,
                    "avg_chunks_per_document": round(avg_chunks_per_doc, 2),
                    "file_type_distribution": file_types,
                    "storage_efficiency": round(total_chunks / max(total_size / 1024, 1), 4)  # chunks per KB
                }
                
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}

    def __del__(self):
        """Cleanup resources on destruction."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)

# Global instance
document_manager = DocumentManager()

def get_document_manager() -> DocumentManager:
    """Get the global document manager instance."""
    return document_manager