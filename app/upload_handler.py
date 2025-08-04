"""
Authored by: Backend Technical Lead (cin)
Date: 2025-08-04

Upload Handler Service

Comprehensive file upload processing pipeline with real-time status updates,
error handling, retry mechanisms, and WebSocket integration for the RAG system.
"""

import asyncio
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable, AsyncGenerator, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import weakref
from concurrent.futures import ThreadPoolExecutor
import threading

from fastapi import UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from document_manager import get_document_manager, DocumentMetadata
from document_processing_tracker import processing_tracker, ProcessingStatus
from pdf_processor import pdf_processor, ExtractionMethod
from document_intelligence import document_intelligence, DocumentType
from error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity, RecoveryAction

# Configure logging
logger = logging.getLogger(__name__)

class UploadStatus(str, Enum):
    """Upload processing status."""
    PENDING = "pending"
    VALIDATING = "validating"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    INTELLIGENCE_ANALYSIS = "intelligence_analysis"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class FileValidationError(Exception):
    """File validation error."""
    pass

@dataclass
class UploadTask:
    """Upload task tracking."""
    task_id: str
    filename: str
    file_size: int
    file_type: str
    status: UploadStatus = UploadStatus.PENDING
    progress: float = 0.0
    error_message: str = ""
    doc_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def update_status(self, status: UploadStatus, progress: float = None, error: str = ""):
        """Update task status and progress."""
        self.status = status
        if progress is not None:
            self.progress = progress
        self.error_message = error
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

class UploadProgress(BaseModel):
    """Upload progress update message."""
    task_id: str
    filename: str
    status: UploadStatus
    progress: float = Field(ge=0.0, le=100.0)
    message: str = ""
    error: str = ""
    doc_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class BulkUploadResult(BaseModel):
    """Result of bulk upload operation."""
    total_files: int
    successful_uploads: int
    failed_uploads: int
    upload_tasks: List[str] = Field(default_factory=list)
    processing_time: float = 0.0
    errors: List[Dict[str, str]] = Field(default_factory=list)

class WebSocketManager:
    """WebSocket connection manager for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_tasks: Dict[str, set] = {}  # Track tasks per connection
        self._lock = threading.Lock()

    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        with self._lock:
            self.active_connections[client_id] = websocket
            self.connection_tasks[client_id] = set()
        logger.info(f"WebSocket client {client_id} connected")

    def disconnect(self, client_id: str):
        """Disconnect a WebSocket client."""
        with self._lock:
            self.active_connections.pop(client_id, None)
            self.connection_tasks.pop(client_id, None)
        logger.info(f"WebSocket client {client_id} disconnected")

    async def send_progress_update(self, task_id: str, progress: UploadProgress):
        """Send progress update to all connected clients."""
        message = progress.dict()
        disconnected_clients = []
        
        with self._lock:
            connections_copy = self.active_connections.copy()
        
        for client_id, websocket in connections_copy.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send update to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    def subscribe_to_task(self, client_id: str, task_id: str):
        """Subscribe client to specific task updates."""
        with self._lock:
            if client_id in self.connection_tasks:
                self.connection_tasks[client_id].add(task_id)

    def get_active_connections(self) -> int:
        """Get number of active connections."""
        with self._lock:
            return len(self.active_connections)

class UploadHandler:
    """
    Comprehensive upload handler with file processing pipeline,
    real-time status updates, and error recovery mechanisms.
    """
    
    # Supported file types with size limits (bytes)
    SUPPORTED_TYPES = {
        "text/plain": {"ext": [".txt"], "max_size": 10 * 1024 * 1024},  # 10MB
        "application/pdf": {"ext": [".pdf"], "max_size": 50 * 1024 * 1024},  # 50MB
        "text/markdown": {"ext": [".md"], "max_size": 5 * 1024 * 1024},  # 5MB
        "text/csv": {"ext": [".csv"], "max_size": 25 * 1024 * 1024},  # 25MB
    }
    
    def __init__(self):
        self.document_manager = get_document_manager()
        self.websocket_manager = WebSocketManager()
        self.active_tasks: Dict[str, UploadTask] = {}
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="upload_handler")
        self._lock = threading.RLock()
        
    async def validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file against supported types and size limits.
        
        Args:
            file: Uploaded file object
            
        Raises:
            FileValidationError: If file validation fails
        """
        # Check file exists and has content
        if not file.filename:
            raise FileValidationError("File must have a name")
        
        # Check content type
        if file.content_type not in self.SUPPORTED_TYPES:
            supported = ", ".join(self.SUPPORTED_TYPES.keys())
            raise FileValidationError(
                f"Unsupported file type: {file.content_type}. "
                f"Supported types: {supported}"
            )
        
        # Check file extension
        file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
        supported_extensions = self.SUPPORTED_TYPES[file.content_type]["ext"]
        if file_ext not in supported_extensions:
            raise FileValidationError(
                f"File extension {file_ext} doesn't match content type {file.content_type}"
            )
        
        # Check file size (if available)
        if hasattr(file, 'size') and file.size:
            max_size = self.SUPPORTED_TYPES[file.content_type]["max_size"]
            if file.size > max_size:
                raise FileValidationError(
                    f"File size ({file.size} bytes) exceeds maximum allowed "
                    f"size ({max_size} bytes) for {file.content_type}"
                )

    def _generate_task_id(self, filename: str) -> str:
        """Generate unique task ID for upload."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{filename}_{timestamp}".encode()).hexdigest()[:16]

    async def _send_progress_update(self, task: UploadTask, message: str = ""):
        """Send progress update via WebSocket."""
        progress = UploadProgress(
            task_id=task.task_id,
            filename=task.filename,
            status=task.status,
            progress=task.progress,
            message=message,
            error=task.error_message,
            doc_id=task.doc_id
        )
        
        await self.websocket_manager.send_progress_update(task.task_id, progress)

    async def _process_text_file(self, content: bytes, task: UploadTask) -> str:
        """Process text file content."""
        try:
            # Decode text content
            text_content = content.decode('utf-8')
            
            # Update progress
            task.update_status(UploadStatus.PROCESSING, 30.0)
            await self._send_progress_update(task, "Processing text content")
            
            return text_content
            
        except UnicodeDecodeError as e:
            raise ApplicationError(
                message=f"Failed to decode text file: {str(e)}",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.MEDIUM,
                user_message="File appears to be corrupted or not in UTF-8 encoding",
                recovery_action=RecoveryAction.RETRY
            )

    async def _process_pdf_file(self, content: bytes, task: UploadTask) -> Tuple[str, Dict[str, Any]]:
        """Process PDF file content and extract metadata."""
        try:
            task.update_status(UploadStatus.PROCESSING, 20.0)
            await self._send_progress_update(task, "Extracting text from PDF")
            
            # Extract text from PDF
            pdf_result = pdf_processor.process_pdf(content, task.filename)
            
            if not pdf_result.success:
                raise ApplicationError(
                    message=f"PDF extraction failed: {pdf_result.error_message}",
                    category=ErrorCategory.PROCESSING,
                    severity=ErrorSeverity.HIGH,
                    user_message="Could not extract text from PDF file",
                    recovery_action=RecoveryAction.RETRY
                )
            
            task.update_status(UploadStatus.PROCESSING, 50.0)
            await self._send_progress_update(task, "PDF text extraction completed")
            
            # Prepare metadata
            pdf_metadata = {
                "pdf_metadata": pdf_result.metadata.to_dict(),
                "extraction_method": pdf_result.extraction_method.value,
                "quality_score": pdf_result.quality_score,
                "page_count": pdf_result.metadata.page_count
            }
            
            return pdf_result.text, pdf_metadata
            
        except Exception as e:
            if isinstance(e, ApplicationError):
                raise
            
            raise ApplicationError(
                message=f"PDF processing error: {str(e)}",
                category=ErrorCategory.PROCESSING,
                severity=ErrorSeverity.HIGH,
                user_message="Error processing PDF file",
                recovery_action=RecoveryAction.RETRY
            )

    async def _perform_intelligence_analysis(self, 
                                           content: str, 
                                           task: UploadTask) -> Dict[str, Any]:
        """Perform document intelligence analysis."""
        try:
            task.update_status(UploadStatus.INTELLIGENCE_ANALYSIS, 60.0)
            await self._send_progress_update(task, "Analyzing document structure")
            
            intelligence_result = document_intelligence.analyze_document(
                content=content,
                title=task.filename,
                file_type=task.file_type
            )
            
            # Prepare intelligence metadata
            intelligence_metadata = {
                "document_type": intelligence_result.document_type.value,
                "content_structure": intelligence_result.structure.value,
                "intelligence_confidence": intelligence_result.confidence,
                "suggested_chunk_size": intelligence_result.suggested_chunk_size,
                "suggested_overlap": intelligence_result.suggested_overlap,
                "processing_notes": intelligence_result.processing_notes,
                "content_features": intelligence_result.features.__dict__
            }
            
            task.update_status(UploadStatus.INTELLIGENCE_ANALYSIS, 70.0)
            await self._send_progress_update(task, "Document analysis completed")
            
            return intelligence_metadata
            
        except Exception as e:
            logger.warning(f"Document intelligence analysis failed for {task.filename}: {e}")
            # Return default values on analysis failure
            return {
                "document_type": "plain_text",
                "content_structure": "unstructured",
                "intelligence_confidence": 0.5,
                "processing_notes": [f"Intelligence analysis failed: {str(e)}"]
            }

    async def process_single_file(self, file: UploadFile) -> UploadTask:
        """
        Process a single uploaded file with comprehensive error handling.
        
        Args:
            file: Uploaded file object
            
        Returns:
            UploadTask with processing results
        """
        # Generate task ID and create task
        task_id = self._generate_task_id(file.filename or "unknown")
        task = UploadTask(
            task_id=task_id,
            filename=file.filename or "unknown",
            file_size=0,  # Will be updated after reading
            file_type=file.content_type or "text/plain"
        )
        
        # Store task
        with self._lock:
            self.active_tasks[task_id] = task
        
        try:
            # Initial status update
            task.update_status(UploadStatus.VALIDATING, 5.0)
            await self._send_progress_update(task, "Validating file")
            
            # Validate file
            await self.validate_file(file)
            
            # Read file content
            task.update_status(UploadStatus.UPLOADING, 10.0)
            await self._send_progress_update(task, "Reading file content")
            
            content = await file.read()
            task.file_size = len(content)
            
            # Process based on file type
            processed_content = ""
            additional_metadata = {}
            
            if file.content_type == "application/pdf":
                processed_content, pdf_metadata = await self._process_pdf_file(content, task)
                additional_metadata.update(pdf_metadata)
            else:
                processed_content = await self._process_text_file(content, task)
            
            # Perform document intelligence analysis
            intelligence_metadata = await self._perform_intelligence_analysis(
                processed_content, task
            )
            additional_metadata.update(intelligence_metadata)
            
            # Create document via document manager
            task.update_status(UploadStatus.INDEXING, 80.0)
            await self._send_progress_update(task, "Indexing document")
            
            document_metadata = {
                "file_type": task.file_type.split("/")[-1],  # Extract just the type part
                "original_filename": task.filename,
                "source": "file_upload",
                **additional_metadata
            }
            
            doc_id, doc_metadata = await self.document_manager.create_document(
                title=task.filename,
                content=processed_content,
                metadata=document_metadata
            )
            
            # Update task with success
            task.doc_id = doc_id
            task.update_status(UploadStatus.COMPLETED, 100.0)
            await self._send_progress_update(task, f"Document indexed successfully as {doc_id}")
            
            logger.info(f"Successfully processed file {task.filename} as document {doc_id}")
            
        except (FileValidationError, ApplicationError) as e:
            task.update_status(UploadStatus.FAILED, error=str(e))
            await self._send_progress_update(task, f"Processing failed: {str(e)}")
            logger.error(f"File processing failed for {task.filename}: {e}")
            
        except Exception as e:
            app_error = handle_error(e)
            task.update_status(UploadStatus.FAILED, error=app_error.user_message)
            await self._send_progress_update(task, f"Unexpected error: {app_error.user_message}")
            logger.error(f"Unexpected error processing {task.filename}: {app_error.to_dict()}")
        
        return task

    async def process_multiple_files(self, files: List[UploadFile]) -> BulkUploadResult:
        """
        Process multiple files with parallel processing and progress tracking.
        
        Args:
            files: List of uploaded files
            
        Returns:
            BulkUploadResult with processing statistics
        """
        start_time = datetime.now()
        
        # Process files concurrently (with reasonable limit)
        max_concurrent = min(len(files), 3)  # Limit concurrent processing
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(file: UploadFile) -> UploadTask:
            async with semaphore:
                return await self.process_single_file(file)
        
        # Start processing all files
        tasks = [process_with_semaphore(file) for file in files]
        upload_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect results
        successful_uploads = 0
        failed_uploads = 0
        task_ids = []
        errors = []
        
        for i, result in enumerate(upload_tasks):
            if isinstance(result, Exception):
                failed_uploads += 1
                errors.append({
                    "filename": files[i].filename or "unknown",
                    "error": str(result)
                })
            elif isinstance(result, UploadTask):
                task_ids.append(result.task_id)
                if result.status == UploadStatus.COMPLETED:
                    successful_uploads += 1
                else:
                    failed_uploads += 1
                    if result.error_message:
                        errors.append({
                            "filename": result.filename,
                            "error": result.error_message
                        })
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        result = BulkUploadResult(
            total_files=len(files),
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            upload_tasks=task_ids,
            processing_time=processing_time,
            errors=errors
        )
        
        logger.info(f"Bulk upload completed: {successful_uploads}/{len(files)} successful "
                   f"in {processing_time:.2f}s")
        
        return result

    def get_task_status(self, task_id: str) -> Optional[UploadTask]:
        """Get upload task status."""
        with self._lock:
            return self.active_tasks.get(task_id)

    def get_all_tasks(self) -> List[UploadTask]:
        """Get all upload tasks."""
        with self._lock:
            return list(self.active_tasks.values())

    def cleanup_completed_tasks(self, older_than_hours: int = 24) -> int:
        """Clean up completed tasks older than specified hours."""
        cutoff_time = datetime.now()
        cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - older_than_hours)
        cutoff_str = cutoff_time.isoformat()
        
        with self._lock:
            to_remove = []
            for task_id, task in self.active_tasks.items():
                if (task.status in [UploadStatus.COMPLETED, UploadStatus.FAILED] and 
                    task.updated_at < cutoff_str):
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.active_tasks[task_id]
            
            return len(to_remove)

    async def handle_websocket_connection(self, websocket: WebSocket, client_id: str):
        """Handle WebSocket connection for real-time updates."""
        try:
            await self.websocket_manager.connect(websocket, client_id)
            
            # Send current task statuses to new client
            with self._lock:
                current_tasks = list(self.active_tasks.values())
            
            for task in current_tasks:
                if task.status not in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
                    progress = UploadProgress(
                        task_id=task.task_id,
                        filename=task.filename,
                        status=task.status,
                        progress=task.progress,
                        doc_id=task.doc_id
                    )
                    await websocket.send_text(json.dumps(progress.dict()))
            
            # Keep connection alive
            while True:
                try:
                    # Ping every 30 seconds to keep connection alive
                    await asyncio.sleep(30)
                    await websocket.send_text(json.dumps({"type": "ping", "timestamp": datetime.now().isoformat()}))
                except WebSocketDisconnect:
                    break
                    
        except WebSocketDisconnect:
            pass
        finally:
            self.websocket_manager.disconnect(client_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Get upload handler statistics."""
        with self._lock:
            tasks = list(self.active_tasks.values())
        
        status_counts = {}
        for status in UploadStatus:
            status_counts[status.value] = len([t for t in tasks if t.status == status])
        
        return {
            "total_tasks": len(tasks),
            "active_websocket_connections": self.websocket_manager.get_active_connections(),
            "status_distribution": status_counts,
            "supported_file_types": list(self.SUPPORTED_TYPES.keys())
        }

    def __del__(self):
        """Cleanup resources on destruction."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)

# Global instance
upload_handler = UploadHandler()

def get_upload_handler() -> UploadHandler:
    """Get the global upload handler instance."""
    return upload_handler