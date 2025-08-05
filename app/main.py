"""
Main FastAPI application for the Local RAG System
Provides REST API endpoints for the RAG functionality
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Query, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple, Any
import uvicorn
import logging
from datetime import datetime
import hashlib
import asyncio
from .rag_backend import get_rag_system
from .document_processing_tracker import processing_tracker, ProcessingStatus
from .pdf_processor import pdf_processor, ExtractionMethod
from .document_intelligence import document_intelligence, DocumentType
from .error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity, RecoveryAction, get_error_stats
from .health_monitor import health_monitor, HealthStatus
from .document_manager import get_document_manager, DocumentFilter, BulkOperationResult
from .upload_handler import get_upload_handler, BulkUploadResult, UploadStatus
from .document_versioning import get_document_versioning, DocumentVersion, VersionDiff, VersionConflict, RollbackSafetyCheck, VersionOperation, ConflictResolution
from .export_manager import get_export_manager, ExportRequest, ExportResult, BulkExportResult, ExportFormat, ExportType, ExportOptions
from .sharing_service import get_sharing_service, ShareRequest, ShareLink, AccessLevel, ShareType, CollaborationInvite

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local RAG System API",
    description="Fully local RAG system with ChromaDB and Ollama",
    version="1.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class Document(BaseModel):
    title: str
    content: str
    source: Optional[str] = "api_upload"

class QueryRequest(BaseModel):
    question: str
    max_chunks: Optional[int] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, str]]
    context_used: int
    context_tokens: int
    efficiency_ratio: float

class HealthResponse(BaseModel):
    status: str
    components: Dict[str, bool]
    document_count: int

class DocumentInfo(BaseModel):
    doc_id: str
    title: str
    file_type: str
    upload_date: str
    chunk_count: int
    file_size: int
    status: str = "ready"
    error_message: str = ""

class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total_count: int

class DeleteResponse(BaseModel):
    message: str
    deleted_chunks: int

class BulkDeleteRequest(BaseModel):
    doc_ids: List[str]

class BulkDeleteResponse(BaseModel):
    success_count: int
    error_count: int
    total_chunks_deleted: int
    processing_time: float
    errors: List[Dict[str, str]] = []

class DocumentStatusResponse(BaseModel):
    doc_id: str
    status: str
    processing_progress: float = 0.0
    error_message: str = ""
    last_updated: str

class StorageStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_size_bytes: int
    avg_chunks_per_document: float
    file_type_distribution: Dict[str, int]
    storage_efficiency: float

class ErrorResponse(BaseModel):
    error_code: str
    user_message: str
    recovery_action: str
    technical_message: Optional[str] = None

# Document Versioning API Models
class CreateVersionRequest(BaseModel):
    content: str
    author: str
    change_summary: str = ""
    parent_version_id: Optional[str] = None

class VersionResponse(BaseModel):
    version_id: str
    doc_id: str
    version_number: int
    title: str
    author: str
    timestamp: str
    operation: str
    change_summary: str
    status: str
    is_current: bool
    lines_added: int
    lines_removed: int
    lines_modified: int
    similarity_score: float
    file_size: int

class VersionHistoryResponse(BaseModel):
    versions: List[VersionResponse]
    total_count: int

class VersionDiffResponse(BaseModel):
    from_version: str
    to_version: str
    similarity_score: float
    lines_added: int
    lines_removed: int
    lines_modified: int
    total_changes: int
    unified_diff: str
    structural_changes: List[str]

class RollbackRequest(BaseModel):
    target_version_id: str
    author: str
    force: bool = False

class RollbackResponse(BaseModel):
    success: bool
    new_version: Optional[VersionResponse]
    warnings: List[str]

class ConflictResolutionRequest(BaseModel):
    resolution_strategy: str  # abort, auto_merge, manual, force_overwrite
    author: str
    merged_content: Optional[str] = None

class ConflictResponse(BaseModel):
    conflict_id: str
    doc_id: str
    conflict_type: str
    conflict_areas: List[Dict[str, Any]]
    base_version_id: str
    current_version_id: str

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        # Initialize RAG system
        rag_system = get_rag_system()
        logger.info(f"RAG system initialized with {rag_system.collection.count()} documents")
        
        # Initialize document manager and upload handler
        document_manager = get_document_manager()
        upload_handler = get_upload_handler()
        logger.info("Document management services initialized")
        
        # Initialize document versioning system
        versioning = get_document_versioning()
        logger.info("Document versioning system initialized")
        
        # Initialize export and sharing services
        export_manager = get_export_manager()
        sharing_service = get_sharing_service()
        logger.info("Export and sharing services initialized")
        
        # Start health monitoring
        await health_monitor.start_monitoring()
        logger.info("Health monitoring started")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        # Don't prevent startup, but log the error

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    try:
        await health_monitor.stop_monitoring()
        logger.info("Health monitoring stopped")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint - redirect to API documentation"""
    return RedirectResponse(url="/docs", status_code=307)

@app.get("/info")
async def api_info():
    """API information and available endpoints"""
    return {
        "name": "Local RAG System API",
        "version": "1.0.0",
        "description": "Fully local RAG system with ChromaDB and Ollama",
        "ui": "http://localhost:3000",
        "documentation": "/docs",
        "endpoints": {
            "health": {
                "method": "GET",
                "path": "/health", 
                "description": "Check system health status"
            },
            "query": {
                "method": "POST",
                "path": "/query",
                "description": "Query the knowledge base",
                "example": {"question": "What documents do you have?", "max_chunks": 3}
            },
            "documents": {
                "list": {"method": "GET", "path": "/api/v1/documents", "description": "List documents with filtering"},
                "upload": {"method": "POST", "path": "/api/v1/documents/upload", "description": "Upload files with real-time status"},
                "bulk_upload": {"method": "POST", "path": "/api/v1/documents/bulk-upload", "description": "Upload multiple files"},
                "delete": {"method": "DELETE", "path": "/api/v1/documents/{doc_id}", "description": "Delete single document"},
                "bulk_delete": {"method": "DELETE", "path": "/api/v1/documents/bulk", "description": "Delete multiple documents"},
                "status": {"method": "GET", "path": "/api/v1/documents/{doc_id}/status", "description": "Get document processing status"},
                "stats": {"method": "GET", "path": "/api/v1/documents/stats", "description": "Get storage statistics"},
                "websocket": {"method": "WebSocket", "path": "/api/v1/documents/ws/{client_id}", "description": "Real-time upload progress"}
            },
            "versioning": {
                "create_version": {"method": "POST", "path": "/api/v1/documents/{doc_id}/versions", "description": "Create new document version"},
                "version_history": {"method": "GET", "path": "/api/v1/documents/{doc_id}/versions", "description": "Get document version history"},
                "current_version": {"method": "GET", "path": "/api/v1/documents/{doc_id}/versions/current", "description": "Get current document version"},
                "get_version": {"method": "GET", "path": "/api/v1/versions/{version_id}", "description": "Get specific version by ID"},
                "version_content": {"method": "GET", "path": "/api/v1/versions/{version_id}/content", "description": "Get version content"},
                "compare_versions": {"method": "GET", "path": "/api/v1/versions/{from_id}/compare/{to_id}", "description": "Compare two versions"},
                "rollback": {"method": "POST", "path": "/api/v1/documents/{doc_id}/rollback", "description": "Rollback to specific version"},
                "safety_check": {"method": "GET", "path": "/api/v1/documents/{doc_id}/rollback/{version_id}/safety-check", "description": "Validate rollback safety"},
                "detect_conflicts": {"method": "POST", "path": "/api/v1/documents/{doc_id}/detect-conflicts", "description": "Detect version conflicts"},
                "cleanup": {"method": "POST", "path": "/api/v1/documents/{doc_id}/versions/cleanup", "description": "Clean up old versions"}
            },
            "settings": {
                "get": {"method": "GET", "path": "/settings", "description": "Get RAG settings"},
                "update": {"method": "POST", "path": "/settings", "description": "Update RAG settings"}
            }
        },
        "quick_test": "curl http://localhost:8000/health"
    }

@app.get("/health")
async def health_check():
    """Check comprehensive system health with detailed monitoring."""
    try:
        # Get comprehensive health summary
        health_summary = health_monitor.get_health_summary()
        
        # Get basic RAG system info
        rag_sys = get_rag_system()
        doc_count = rag_sys.collection.count()
        
        # Map component status to boolean for backward compatibility
        components = {}
        for component_name, check in health_summary["checks"].items():
            components[component_name] = check["status"] in ["healthy", "degraded"]
        
        # Include error statistics
        error_stats = get_error_stats()
        
        return {
            "status": health_summary["overall_status"],
            "components": components,
            "document_count": doc_count,
            "health_details": health_summary,
            "error_statistics": error_stats,
            "monitoring": {
                "enabled": health_monitor.is_monitoring,
                "check_interval": health_monitor.check_interval,
                "last_check": health_summary["last_check"]
            }
        }
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Health check failed: {app_error.to_dict()}")
        
        # Return degraded health status instead of failing
        return {
            "status": "unhealthy",
            "components": {},
            "document_count": 0,
            "error": app_error.to_dict(),
            "monitoring": {"enabled": False}
        }

@app.get("/health/errors")
async def get_error_statistics():
    """Get detailed error statistics for monitoring."""
    try:
        stats = get_error_stats()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        app_error = handle_error(e)
        return {
            "success": False,
            "error": app_error.to_dict()
        }

@app.get("/health/metrics")
async def get_system_metrics(minutes: int = 30):
    """Get system metrics history."""
    try:
        metrics = health_monitor.get_metrics_history(minutes)
        return {
            "success": True,
            "metrics": metrics,
            "period_minutes": minutes
        }
    except Exception as e:
        app_error = handle_error(e)
        return {
            "success": False,
            "error": app_error.to_dict()
        }

@app.post("/documents")
async def add_documents(documents: List[Document]):
    """Add documents to the knowledge base"""
    try:
        rag_sys = get_rag_system()
        doc_dicts = [doc.dict() for doc in documents]
        result = rag_sys.add_documents(doc_dicts)
        return {"message": result, "count": len(documents)}
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error adding documents: {app_error.to_dict()}")
        
        return ErrorResponse(
            error_code=app_error.error_code,
            user_message=app_error.user_message,
            recovery_action=app_error.recovery_action.value,
            technical_message=str(e) if logger.level <= logging.DEBUG else None
        ).dict(), 500

@app.post("/documents/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload text files and add to knowledge base with processing status tracking"""
    try:
        documents = []
        processing_tasks = []
        
        # Create processing tasks for each file
        for file in files:
            if file.content_type not in ["text/plain", "application/pdf"]:
                raise HTTPException(status_code=400, detail=f"File {file.filename} must be a text file (.txt) or PDF (.pdf)")
            
            content = await file.read()
            
            # Handle different file types
            if file.content_type == "application/pdf":
                file_type = "pdf"
                # Content will be processed by PDF processor
                content_str = None  # Will be extracted later
            else:
                file_type = "txt"
                content_str = content.decode('utf-8')
            
            # Generate doc_id using filename and timestamp hash
            doc_id = hashlib.md5(f"{file.filename}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
            
            # Create processing task
            task = processing_tracker.create_task(
                doc_id=doc_id,
                filename=file.filename,
                file_size=len(content)
            )
            processing_tasks.append(task)
            
            # Store document info for processing
            doc_info = {
                "title": file.filename,
                "source": "file_upload",
                "file_type": file_type,
                "original_filename": file.filename,
                "file_size": len(content),
                "upload_timestamp": datetime.now().isoformat(),
                "doc_id": doc_id,
                "raw_content": content,  # Raw bytes for PDF processing
                "content": content_str   # Text content for TXT files
            }
            documents.append(doc_info)
        
        # Process documents with status tracking
        rag_sys = get_rag_system()
        processed_docs = []
        
        for doc, task in zip(documents, processing_tasks):
            try:
                # Start processing
                processing_tracker.start_processing(task.doc_id)
                processing_tracker.update_progress(task.doc_id, 20.0)
                
                # Handle PDF extraction
                if doc["file_type"] == "pdf":
                    processing_tracker.update_progress(task.doc_id, 30.0)
                    
                    # Extract text from PDF
                    pdf_result = pdf_processor.process_pdf(
                        doc["raw_content"], 
                        doc["original_filename"]
                    )
                    
                    if not pdf_result.success:
                        raise Exception(f"PDF extraction failed: {pdf_result.error_message}")
                    
                    # Update document with extracted content and metadata
                    doc["content"] = pdf_result.text
                    doc["pdf_metadata"] = pdf_result.metadata.to_dict()
                    doc["extraction_method"] = pdf_result.extraction_method.value
                    doc["quality_score"] = pdf_result.quality_score
                    doc["page_count"] = pdf_result.metadata.page_count
                    
                    processing_tracker.update_progress(task.doc_id, 60.0)
                else:
                    processing_tracker.update_progress(task.doc_id, 50.0)
                
                # Perform document intelligence analysis (if enabled)
                processing_tracker.update_progress(task.doc_id, 65.0)
                
                try:
                    intelligence_result = document_intelligence.analyze_document(
                        content=doc["content"],
                        title=doc["title"],
                        file_type=doc["file_type"]
                    )
                    
                    # Add intelligence results to document metadata
                    doc["document_type"] = intelligence_result.document_type.value
                    doc["content_structure"] = intelligence_result.structure.value
                    doc["intelligence_confidence"] = intelligence_result.confidence
                    doc["suggested_chunk_size"] = intelligence_result.suggested_chunk_size
                    doc["suggested_overlap"] = intelligence_result.suggested_overlap
                    doc["processing_notes"] = intelligence_result.processing_notes
                    doc["content_features"] = intelligence_result.features.__dict__
                    
                    use_intelligent_chunking = True
                    logger.info(f"Document intelligence analysis completed for {doc['title']}")
                    
                except Exception as e:
                    logger.warning(f"Document intelligence analysis failed for {doc['title']}: {e}")
                    # Fall back to default values
                    doc["document_type"] = "plain_text"
                    doc["content_structure"] = "unstructured"
                    doc["intelligence_confidence"] = 0.5
                    doc["processing_notes"] = [f"Intelligence analysis failed: {str(e)}"]
                    use_intelligent_chunking = False
                
                processing_tracker.update_progress(task.doc_id, 75.0)
                
                # Remove raw content before sending to RAG system
                rag_doc = {k: v for k, v in doc.items() if k != "raw_content"}
                
                # Process document with RAG system
                if use_intelligent_chunking and 'suggested_chunk_size' in doc:
                    result = rag_sys.add_documents([rag_doc], 
                                                 chunk_size=doc["suggested_chunk_size"],
                                                 chunk_overlap=doc["suggested_overlap"])
                else:
                    result = rag_sys.add_documents([rag_doc])
                
                processing_tracker.update_progress(task.doc_id, 90.0)
                
                # Extract chunk count from result message
                chunks_created = 1  # Default, could parse from result
                if "(" in result and "chunks)" in result:
                    try:
                        chunks_created = int(result.split("(")[1].split(" chunks)")[0])
                    except:
                        pass
                
                # Complete processing
                processing_tracker.complete_task(task.doc_id, chunks_created)
                processed_docs.append(doc)
                
            except Exception as e:
                app_error = handle_error(e)
                processing_tracker.fail_task(task.doc_id, app_error.user_message)
                logger.error(f"Error processing document {doc['title']}: {app_error.to_dict()}")
        
        return {
            "message": f"Successfully uploaded {len(processed_docs)} of {len(files)} files",
            "files_processed": len(processed_docs),
            "processing_tasks": [task.doc_id for task in processing_tasks]
        }
    
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error uploading files: {app_error.to_dict()}")
        
        return ErrorResponse(
            error_code=app_error.error_code,
            user_message=app_error.user_message,
            recovery_action=app_error.recovery_action.value,
            technical_message=str(e) if logger.level <= logging.DEBUG else None
        ).dict(), 500

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base with enhanced error handling."""
    try:
        rag_sys = get_rag_system()
        
        # Check if we have documents
        if rag_sys.collection.count() == 0:
            raise ApplicationError(
                message="No documents in knowledge base",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.MEDIUM,
                user_message="There are no documents to search. Please upload some documents first.",
                recovery_action=RecoveryAction.NONE
            )
        
        result = rag_sys.rag_query(request.question, max_chunks=request.max_chunks)
        return QueryResponse(**result)
    except ApplicationError as e:
        app_error = e
    except Exception as e:
        app_error = handle_error(e)
    
    logger.error(f"Error processing query: {app_error.to_dict()}")
    
    # For queries, we can return a partial response with error info
    return {
        "answer": f"I'm sorry, I couldn't process your query. {app_error.user_message}",
        "sources": [],
        "context_used": 0,
        "context_tokens": 0,
        "efficiency_ratio": 0.0,
        "error": app_error.to_dict()
    }

# Processing Status Endpoints

@app.get("/processing/status")
async def get_processing_status():
    """Get overall processing queue status"""
    try:
        return processing_tracker.get_queue_status()
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/processing/tasks")
async def get_all_processing_tasks():
    """Get all processing tasks"""
    try:
        tasks = processing_tracker.get_all_tasks()
        return {"tasks": [task.to_dict() for task in tasks]}
    except Exception as e:
        logger.error(f"Error getting processing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/processing/tasks/{doc_id}")
async def get_processing_task(doc_id: str):
    """Get specific processing task status"""
    try:
        task = processing_tracker.get_task(doc_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task.to_dict()
    except Exception as e:
        logger.error(f"Error getting processing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/processing/cleanup")
async def cleanup_old_tasks():
    """Clean up old completed/failed tasks"""
    try:
        removed_count = processing_tracker.cleanup_old_tasks()
        return {"message": f"Cleaned up {removed_count} old tasks"}
    except Exception as e:
        logger.error(f"Error cleaning up tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """Get list of all documents with metadata"""
    try:
        rag_sys = get_rag_system()
        
        # Get all documents from ChromaDB
        results = rag_sys.collection.get(include=["metadatas"])
        
        # Process documents and group by doc_id
        doc_groups = {}
        for i, metadata in enumerate(results.get("metadatas", [])):
            doc_id = str(metadata.get("doc_id", "unknown"))
            
            if doc_id not in doc_groups:
                doc_groups[doc_id] = {
                    "doc_id": str(doc_id),  # Ensure string type
                    "title": str(metadata.get("title", "Unknown Document")),
                    "file_type": str(metadata.get("file_type", "txt")),
                    "upload_date": str(metadata.get("upload_timestamp", datetime.now().isoformat())),
                    "chunk_count": 0,
                    "file_size": 0,
                    "status": "ready"
                }
            
            doc_groups[doc_id]["chunk_count"] += 1
            # Estimate file size from content preview length
            preview_len = len(metadata.get("content_preview", ""))
            if preview_len > 0:
                doc_groups[doc_id]["file_size"] = max(doc_groups[doc_id]["file_size"], preview_len * 10)
        
        # Debug: Check doc_data before creating DocumentInfo
        documents = []
        for doc_data in doc_groups.values():
            try:
                # Ensure all fields are proper types
                doc_data["doc_id"] = str(doc_data["doc_id"])
                doc_data["chunk_count"] = int(doc_data["chunk_count"])
                doc_data["file_size"] = int(doc_data["file_size"])
                documents.append(DocumentInfo(**doc_data))
            except Exception as e:
                logger.error(f"Error creating DocumentInfo for {doc_data}: {e}")
                continue
        documents.sort(key=lambda x: x.upload_date, reverse=True)
        
        return DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str):
    """Delete a specific document and all its chunks"""
    try:
        rag_sys = get_rag_system()
        
        # Get all chunks for this document (try both string and int versions)
        results = rag_sys.collection.get(
            where={"doc_id": doc_id},
            include=["metadatas"]
        )
        
        # If not found as string, try as integer
        if not results.get("ids"):
            try:
                results = rag_sys.collection.get(
                    where={"doc_id": int(doc_id)},
                    include=["metadatas"]
                )
            except ValueError:
                pass
        
        chunk_ids = results.get("ids", [])
        if not chunk_ids:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        # Delete all chunks for this document
        rag_sys.collection.delete(ids=chunk_ids)
        
        logger.info(f"Deleted document {doc_id} with {len(chunk_ids)} chunks")
        
        return DeleteResponse(
            message=f"Document {doc_id} deleted successfully",
            deleted_chunks=len(chunk_ids)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/count")
async def get_document_count():
    """Get total number of document chunks"""
    try:
        rag_sys = get_rag_system()
        count = rag_sys.collection.count()
        return {"total_chunks": count}
    except Exception as e:
        logger.error(f"Error getting document count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents")
async def clear_documents():
    """Clear all documents from the knowledge base"""
    try:
        rag_sys = get_rag_system()
        rag_sys.collection.delete(where={})
        return {"message": "All documents cleared"}
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings")
async def get_settings():
    """Get current RAG system settings"""
    rag_sys = get_rag_system()
    return {
        "similarity_threshold": rag_sys.similarity_threshold,
        "max_context_tokens": rag_sys.max_context_tokens,
        "chunk_size": rag_sys.chunk_size,
        "chunk_overlap": rag_sys.chunk_overlap
    }

@app.post("/settings")
async def update_settings(
    similarity_threshold: Optional[float] = None,
    max_context_tokens: Optional[int] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
):
    """Update RAG system settings"""
    try:
        rag_sys = get_rag_system()
        if similarity_threshold is not None:
            rag_sys.similarity_threshold = similarity_threshold
        if max_context_tokens is not None:
            rag_sys.max_context_tokens = max_context_tokens
        if chunk_size is not None:
            rag_sys.chunk_size = chunk_size
        if chunk_overlap is not None:
            rag_sys.chunk_overlap = chunk_overlap
        
        return {"message": "Settings updated successfully"}
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Document Management API Endpoints

@app.get("/api/v1/documents", response_model=DocumentListResponse)
async def list_documents_v1(
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    title_contains: Optional[str] = Query(None, description="Filter by title content"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit results"),
    offset: Optional[int] = Query(0, ge=0, description="Offset for pagination")
):
    """Enhanced document listing with filtering and pagination."""
    try:
        document_manager = get_document_manager()
        
        # Create filter object
        document_filter = DocumentFilter(
            file_type=file_type,
            status=status,
            title_contains=title_contains,
            limit=limit,
            offset=offset
        )
        
        documents, total_count = await document_manager.list_documents(document_filter)
        
        # Convert to API response format
        document_infos = []
        for doc in documents:
            document_infos.append(DocumentInfo(
                doc_id=doc.doc_id,
                title=doc.title,
                file_type=doc.file_type,
                upload_date=doc.upload_timestamp,
                chunk_count=doc.chunk_count,
                file_size=doc.file_size,
                status=doc.status,
                error_message=doc.error_message
            ))
        
        return DocumentListResponse(
            documents=document_infos,
            total_count=total_count
        )
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error listing documents: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/documents/upload")
async def upload_single_file_v1(file: UploadFile = File(...)):
    """Upload a single file with real-time status tracking."""
    try:
        upload_handler = get_upload_handler()
        task = await upload_handler.process_single_file(file)
        
        return {
            "message": f"File {file.filename} processed",
            "task_id": task.task_id,
            "status": task.status.value,
            "doc_id": task.doc_id,
            "success": task.status == UploadStatus.COMPLETED
        }
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error uploading file: {app_error.to_dict()}")
        return {
            "message": f"Upload failed: {app_error.user_message}",
            "success": False,
            "error": app_error.to_dict()
        }

@app.post("/api/v1/documents/bulk-upload", response_model=BulkUploadResult)
async def bulk_upload_files_v1(files: List[UploadFile] = File(...)):
    """Upload multiple files with parallel processing."""
    try:
        upload_handler = get_upload_handler()
        result = await upload_handler.process_multiple_files(files)
        return result
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error in bulk upload: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.delete("/api/v1/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document_v1(doc_id: str):
    """Delete a specific document and all its chunks."""
    try:
        document_manager = get_document_manager()
        success, chunks_deleted = await document_manager.delete_document(doc_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        return DeleteResponse(
            message=f"Document {doc_id} deleted successfully",
            deleted_chunks=chunks_deleted
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error deleting document {doc_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.delete("/api/v1/documents/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_documents_v1(request: BulkDeleteRequest):
    """Delete multiple documents in bulk."""
    try:
        document_manager = get_document_manager()
        result = await document_manager.bulk_delete_documents(request.doc_ids)
        
        return BulkDeleteResponse(
            success_count=result.success_count,
            error_count=result.error_count,
            total_chunks_deleted=result.total_chunks_affected,
            processing_time=result.processing_time,
            errors=result.errors
        )
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error in bulk delete: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/documents/{doc_id}/status", response_model=DocumentStatusResponse)
async def get_document_status_v1(doc_id: str):
    """Get document processing status."""
    try:
        # Check upload handler for active processing
        upload_handler = get_upload_handler()
        active_tasks = upload_handler.get_all_tasks()
        
        # Find task by doc_id or task_id
        for task in active_tasks:
            if task.doc_id == doc_id or task.task_id == doc_id:
                return DocumentStatusResponse(
                    doc_id=task.doc_id or task.task_id,
                    status=task.status.value,
                    processing_progress=task.progress,
                    error_message=task.error_message,
                    last_updated=task.updated_at
                )
        
        # Check document manager for completed documents
        document_manager = get_document_manager()
        doc_metadata = await document_manager.get_document(doc_id)
        
        if not doc_metadata:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        return DocumentStatusResponse(
            doc_id=doc_metadata.doc_id,
            status=doc_metadata.status,
            processing_progress=100.0 if doc_metadata.status == "ready" else 0.0,
            error_message=doc_metadata.error_message,
            last_updated=doc_metadata.last_modified
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error getting document status {doc_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/documents/stats", response_model=StorageStatsResponse)
async def get_storage_stats_v1():
    """Get comprehensive storage statistics."""
    try:
        document_manager = get_document_manager()
        stats = await document_manager.get_storage_stats()
        
        return StorageStatsResponse(**stats)
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error getting storage stats: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.websocket("/api/v1/documents/ws/{client_id}")
async def websocket_upload_progress(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time upload progress updates."""
    upload_handler = get_upload_handler()
    await upload_handler.handle_websocket_connection(websocket, client_id)

# Upload Handler Status Endpoints

@app.get("/api/v1/upload/tasks")
async def get_upload_tasks():
    """Get all upload tasks with their current status."""
    try:
        upload_handler = get_upload_handler()
        tasks = upload_handler.get_all_tasks()
        
        return {
            "tasks": [task.to_dict() for task in tasks],
            "total_tasks": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"Error getting upload tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/upload/tasks/{task_id}")
async def get_upload_task_status(task_id: str):
    """Get specific upload task status."""
    try:
        upload_handler = get_upload_handler()
        task = upload_handler.get_task_status(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting upload task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/upload/cleanup")
async def cleanup_upload_tasks():
    """Clean up old completed/failed upload tasks."""
    try:
        upload_handler = get_upload_handler()
        removed_count = upload_handler.cleanup_completed_tasks()
        
        return {
            "message": f"Cleaned up {removed_count} old tasks",
            "removed_count": removed_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/upload/stats")
async def get_upload_stats():
    """Get upload handler statistics."""
    try:
        upload_handler = get_upload_handler()
        return upload_handler.get_statistics()
        
    except Exception as e:
        logger.error(f"Error getting upload stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document Versioning API Endpoints

@app.post("/api/v1/documents/{doc_id}/versions", response_model=VersionResponse)
async def create_document_version(doc_id: str, request: CreateVersionRequest):
    """
    Create a new version of a document.
    
    This endpoint creates a new version with comprehensive change tracking,
    diff analysis, and metadata preservation.
    """
    try:
        versioning = get_document_versioning()
        
        # Create version with specified operation type
        version = await versioning.create_version(
            doc_id=doc_id,
            content=request.content,
            author=request.author,
            operation=VersionOperation.UPDATE,
            change_summary=request.change_summary,
            parent_version_id=request.parent_version_id
        )
        
        return VersionResponse(
            version_id=version.version_id,
            doc_id=version.doc_id,
            version_number=version.version_number,
            title=version.title,
            author=version.author,
            timestamp=version.timestamp,
            operation=version.operation,
            change_summary=version.change_summary,
            status=version.status,
            is_current=version.is_current,
            lines_added=version.lines_added,
            lines_removed=version.lines_removed,
            lines_modified=version.lines_modified,
            similarity_score=version.similarity_score,
            file_size=version.file_size
        )
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error creating version for {doc_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/documents/{doc_id}/versions", response_model=VersionHistoryResponse)
async def get_document_version_history(
    doc_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of versions"),
    include_deleted: bool = Query(False, description="Include deleted versions")
):
    """
    Get version history for a document.
    
    Returns comprehensive version history with change tracking metrics
    and metadata for analysis and rollback operations.
    """
    try:
        versioning = get_document_versioning()
        versions = await versioning.get_version_history(
            doc_id=doc_id,
            limit=limit,
            include_deleted=include_deleted
        )
        
        version_responses = []
        for version in versions:
            version_responses.append(VersionResponse(
                version_id=version.version_id,
                doc_id=version.doc_id,
                version_number=version.version_number,
                title=version.title,
                author=version.author,
                timestamp=version.timestamp,
                operation=version.operation,
                change_summary=version.change_summary,
                status=version.status,
                is_current=version.is_current,
                lines_added=version.lines_added,
                lines_removed=version.lines_removed,
                lines_modified=version.lines_modified,
                similarity_score=version.similarity_score,
                file_size=version.file_size
            ))
        
        return VersionHistoryResponse(
            versions=version_responses,
            total_count=len(version_responses)
        )
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error getting version history for {doc_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/documents/{doc_id}/versions/current", response_model=VersionResponse)
async def get_current_document_version(doc_id: str):
    """Get the current active version of a document."""
    try:
        versioning = get_document_versioning()
        version = await versioning.get_current_version(doc_id)
        
        if not version:
            raise HTTPException(status_code=404, detail="No current version found")
        
        return VersionResponse(
            version_id=version.version_id,
            doc_id=version.doc_id,
            version_number=version.version_number,
            title=version.title,
            author=version.author,
            timestamp=version.timestamp,
            operation=version.operation,
            change_summary=version.change_summary,
            status=version.status,
            is_current=version.is_current,
            lines_added=version.lines_added,
            lines_removed=version.lines_removed,
            lines_modified=version.lines_modified,
            similarity_score=version.similarity_score,
            file_size=version.file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error getting current version for {doc_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/versions/{version_id}", response_model=VersionResponse)
async def get_version_by_id(version_id: str):
    """Get a specific version by ID with full content and metadata."""
    try:
        versioning = get_document_versioning()
        version = await versioning.get_version(version_id)
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return VersionResponse(
            version_id=version.version_id,
            doc_id=version.doc_id,
            version_number=version.version_number,
            title=version.title,
            author=version.author,
            timestamp=version.timestamp,
            operation=version.operation,
            change_summary=version.change_summary,
            status=version.status,
            is_current=version.is_current,
            lines_added=version.lines_added,
            lines_removed=version.lines_removed,
            lines_modified=version.lines_modified,
            similarity_score=version.similarity_score,
            file_size=version.file_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error getting version {version_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/versions/{version_id}/content")
async def get_version_content(version_id: str):
    """Get the raw content of a specific version."""
    try:
        versioning = get_document_versioning()
        version = await versioning.get_version(version_id)
        
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return {
            "version_id": version.version_id,
            "content": version.content,
            "content_hash": version.content_hash,
            "file_size": version.file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error getting version content {version_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/versions/{from_version_id}/compare/{to_version_id}", response_model=VersionDiffResponse)
async def compare_document_versions(from_version_id: str, to_version_id: str):
    """
    Compare two document versions with detailed diff analysis.
    
    Provides comprehensive comparison including line changes, similarity scores,
    structural analysis, and unified diff format for display.
    """
    try:
        versioning = get_document_versioning()
        
        from_version = await versioning.get_version(from_version_id)
        to_version = await versioning.get_version(to_version_id)
        
        if not from_version or not to_version:
            raise HTTPException(status_code=404, detail="One or both versions not found")
        
        diff = versioning.compare_versions(from_version, to_version)
        
        return VersionDiffResponse(
            from_version=diff.from_version,
            to_version=diff.to_version,
            similarity_score=diff.similarity_score,
            lines_added=diff.lines_added,
            lines_removed=diff.lines_removed,
            lines_modified=diff.lines_modified,
            total_changes=diff.total_changes,
            unified_diff=diff.unified_diff,
            structural_changes=diff.structural_changes or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error comparing versions {from_version_id} to {to_version_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/documents/{doc_id}/rollback", response_model=RollbackResponse)
async def rollback_document_version(doc_id: str, request: RollbackRequest):
    """
    Rollback document to a specific version with safety checks.
    
    Performs comprehensive safety validation before rollback and creates
    a new version representing the rollback operation for audit trail.
    """
    try:
        versioning = get_document_versioning()
        
        success, new_version, warnings = await versioning.rollback_to_version(
            doc_id=doc_id,
            target_version_id=request.target_version_id,
            author=request.author,
            force=request.force
        )
        
        new_version_response = None
        if new_version:
            new_version_response = VersionResponse(
                version_id=new_version.version_id,
                doc_id=new_version.doc_id,
                version_number=new_version.version_number,
                title=new_version.title,
                author=new_version.author,
                timestamp=new_version.timestamp,
                operation=new_version.operation,
                change_summary=new_version.change_summary,
                status=new_version.status,
                is_current=new_version.is_current,
                lines_added=new_version.lines_added,
                lines_removed=new_version.lines_removed,
                lines_modified=new_version.lines_modified,
                similarity_score=new_version.similarity_score,
                file_size=new_version.file_size
            )
        
        return RollbackResponse(
            success=success,
            new_version=new_version_response,
            warnings=warnings
        )
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error during rollback for {doc_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/documents/{doc_id}/rollback/{version_id}/safety-check")
async def validate_rollback_safety(doc_id: str, version_id: str):
    """
    Validate the safety of rolling back to a specific version.
    
    Performs comprehensive risk assessment including change impact analysis,
    version history validation, and conflict detection.
    """
    try:
        versioning = get_document_versioning()
        safety_check = await versioning.validate_rollback_safety(doc_id, version_id)
        
        return {
            "is_safe": safety_check.is_safe,
            "risk_level": safety_check.risk_level,
            "warnings": safety_check.warnings,
            "blocking_issues": safety_check.blocking_issues,
            "affected_systems": safety_check.affected_systems,
            "rollback_impact": safety_check.rollback_impact
        }
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error validating rollback safety: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/documents/{doc_id}/detect-conflicts")
async def detect_version_conflicts(
    doc_id: str,
    new_content: str = Query(..., description="New content to check for conflicts"),
    base_version_id: str = Query(..., description="Base version for conflict detection")
):
    """
    Detect potential version conflicts before creating a new version.
    
    Analyzes concurrent modifications and identifies conflicting changes
    that require resolution before version creation.
    """
    try:
        versioning = get_document_versioning()
        conflict = await versioning.detect_conflicts(doc_id, new_content, base_version_id)
        
        if not conflict:
            return {"has_conflicts": False, "message": "No conflicts detected"}
        
        return {
            "has_conflicts": True,
            "conflict": ConflictResponse(
                conflict_id=conflict.conflict_id,
                doc_id=conflict.doc_id,
                conflict_type=conflict.conflict_type,
                conflict_areas=conflict.conflict_areas,
                base_version_id=conflict.base_version_id,
                current_version_id=conflict.current_version_id
            )
        }
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error detecting conflicts for {doc_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/conflicts/{conflict_id}/resolve")
async def resolve_version_conflict(conflict_id: str, request: ConflictResolutionRequest):
    """
    Resolve a version conflict using specified strategy.
    
    Supports multiple resolution strategies including automatic merge,
    manual merge, force overwrite, and abort operations.
    """
    try:
        versioning = get_document_versioning()
        
        # For this endpoint, we'd need to store conflicts temporarily
        # This is a simplified implementation
        # In production, you'd store conflicts in a temporary collection
        
        # Parse resolution strategy
        try:
            resolution = ConflictResolution(request.resolution_strategy)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid resolution strategy: {request.resolution_strategy}")
        
        # This would need to be implemented with proper conflict storage
        # For now, return a placeholder response
        return {
            "success": False,
            "message": "Conflict resolution requires conflict storage implementation",
            "supported_strategies": [e.value for e in ConflictResolution]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error resolving conflict {conflict_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/documents/{doc_id}/versions/cleanup")
async def cleanup_document_versions(
    doc_id: str,
    keep_versions: Optional[int] = Query(50, ge=1, le=100, description="Number of versions to keep")
):
    """
    Clean up old versions for a document to maintain performance.
    
    Marks old versions as deleted while preserving version history
    and maintaining referential integrity.
    """
    try:
        versioning = get_document_versioning()
        stats = await versioning.cleanup_old_versions(doc_id, keep_versions)
        
        return {
            "message": f"Cleanup completed for document {doc_id}",
            "statistics": stats
        }
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error cleaning up versions for {doc_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/versions/cleanup")
async def cleanup_all_versions(
    keep_versions: Optional[int] = Query(50, ge=1, le=100, description="Number of versions to keep per document")
):
    """Clean up old versions for all documents."""
    try:
        versioning = get_document_versioning()
        stats = await versioning.cleanup_old_versions(None, keep_versions)
        
        return {
            "message": "Global version cleanup completed",
            "statistics": stats
        }
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error during global version cleanup: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

# ============================================================================
# Export and Sharing API Endpoints
# ============================================================================

# Export API Models
class ExportDocumentRequest(BaseModel):
    format: ExportFormat
    options: Optional[Dict[str, Any]] = None

class ExportChatRequest(BaseModel):
    conversation_data: List[Dict[str, Any]]
    format: ExportFormat
    options: Optional[Dict[str, Any]] = None

class BulkExportRequest(BaseModel):
    export_requests: List[ExportRequest]

# Sharing API Models  
class ShareLinkResponse(BaseModel):
    share_id: str
    share_url: str
    expires_at: Optional[str] = None
    access_level: str
    created_at: str

class CollaborationInviteRequest(BaseModel):
    email: str
    access_level: AccessLevel
    expires_in_hours: int = 168
    personal_message: Optional[str] = None

# Export Endpoints
@app.post("/api/v1/export/document/{doc_id}", response_model=ExportResult)
async def export_document(
    doc_id: str,
    request: ExportDocumentRequest
):
    """Export a single document to specified format."""
    try:
        export_manager = get_export_manager()
        
        options = None
        if request.options:
            options = ExportOptions(format=request.format, **request.options)
        
        result = await export_manager.export_document(doc_id, request.format, options)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
        
        return result
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error exporting document {doc_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/export/chat", response_model=ExportResult)
async def export_chat_conversation(request: ExportChatRequest):
    """Export a chat conversation to specified format."""
    try:
        export_manager = get_export_manager()
        
        options = None
        if request.options:
            options = ExportOptions(format=request.format, **request.options)
        
        result = await export_manager.export_chat_conversation(
            request.conversation_data, 
            request.format, 
            options
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)
        
        return result
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error exporting chat conversation: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/export/bulk", response_model=BulkExportResult)
async def bulk_export(request: BulkExportRequest):
    """Perform bulk export operations with ZIP compression."""
    try:
        export_manager = get_export_manager()
        result = await export_manager.bulk_export(request.export_requests)
        
        if not result.success:
            raise HTTPException(status_code=400, detail="Bulk export failed")
        
        return result
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error in bulk export: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/export/{export_id}/download")
async def download_export(export_id: str):
    """Download an exported file."""
    try:
        export_manager = get_export_manager()
        export_result = await export_manager.get_export_status(export_id)
        
        if not export_result:
            raise HTTPException(status_code=404, detail="Export not found")
        
        if not export_result.success:
            raise HTTPException(status_code=400, detail="Export failed or incomplete")
        
        if not export_result.file_path or not Path(export_result.file_path).exists():
            raise HTTPException(status_code=404, detail="Export file not found")
        
        return FileResponse(
            path=export_result.file_path,
            filename=export_result.filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error downloading export {export_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/export/{export_id}/status")
async def get_export_status(export_id: str):
    """Get the status of an export operation."""
    try:
        export_manager = get_export_manager()
        result = await export_manager.get_export_status(export_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Export not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error getting export status {export_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/export", response_model=List)
async def list_exports(limit: int = Query(50, ge=1, le=100)):
    """List recent exports."""
    try:
        export_manager = get_export_manager()
        exports = await export_manager.list_exports(limit)
        return exports
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error listing exports: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.delete("/api/v1/export/{export_id}")
async def delete_export(export_id: str):
    """Delete an export and its files."""
    try:
        export_manager = get_export_manager()
        success = await export_manager.delete_export(export_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Export not found")
        
        return {"message": f"Export {export_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error deleting export {export_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

# Sharing Endpoints
@app.post("/api/v1/share", response_model=ShareLinkResponse)
async def create_share_link(
    request: ShareRequest,
    creator_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """Create a shared link for documents or conversations."""
    try:
        sharing_service = get_sharing_service()
        share_link = await sharing_service.create_share_link(request, creator_id)
        
        return ShareLinkResponse(
            share_id=share_link.share_id,
            share_url=share_link.share_url,
            expires_at=share_link.expires_at.isoformat() if share_link.expires_at else None,
            access_level=share_link.access_level,
            created_at=share_link.created_at.isoformat()
        )
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error creating share link: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/share/{share_token}")
async def access_shared_content(
    share_token: str,
    request: Request,
    password: Optional[str] = Query(None)
):
    """Access shared content via share token."""
    try:
        sharing_service = get_sharing_service()
        
        # Extract request info
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent")
        referrer = request.headers.get("referer")
        
        # Validate access
        is_valid, share_link, error_msg = await sharing_service.validate_access(
            share_token, password, ip_address, user_agent, referrer
        )
        
        if not is_valid:
            raise HTTPException(status_code=403, detail=error_msg)
        
        # Record access
        await sharing_service.record_access(
            share_link.share_id, "view", ip_address, user_agent, referrer
        )
        
        # Return shared content info (frontend will handle display)
        return {
            "share_type": share_link.share_type,
            "item_id": share_link.item_id,
            "access_level": share_link.access_level,
            "permissions": share_link.permissions,
            "custom_message": share_link.custom_message,
            "created_at": share_link.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error accessing shared content: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/share/{share_id}/analytics")
async def get_share_analytics(share_id: str):
    """Get analytics for a shared link."""
    try:
        sharing_service = get_sharing_service()
        analytics = await sharing_service.get_share_analytics(share_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Share not found")
        
        return {
            "view_count": analytics.view_count,
            "download_count": analytics.download_count,
            "unique_visitors": analytics.unique_visitors,
            "last_accessed": analytics.last_accessed.isoformat() if analytics.last_accessed else None,
            "referrer_stats": analytics.referrer_stats,
            "device_stats": analytics.device_stats,
            "recent_access_count": len([
                access for access in analytics.access_history
                if (datetime.now() - access['timestamp']).days < 7
            ])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error getting share analytics {share_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.put("/api/v1/share/{share_id}/revoke")
async def revoke_share_link(share_id: str):
    """Revoke a shared link."""
    try:
        sharing_service = get_sharing_service()
        success = await sharing_service.revoke_share_link(share_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Share not found")
        
        return {"message": f"Share link {share_id} revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error revoking share link {share_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.put("/api/v1/share/{share_id}/extend")
async def extend_share_expiration(
    share_id: str,
    additional_hours: int = Query(..., ge=1, le=8760)
):
    """Extend expiration of a shared link."""
    try:
        sharing_service = get_sharing_service()
        success = await sharing_service.extend_expiration(share_id, additional_hours)
        
        if not success:
            raise HTTPException(status_code=404, detail="Share not found")
        
        return {"message": f"Share link {share_id} extended by {additional_hours} hours"}
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error extending share expiration {share_id}: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/share/user/{creator_id}")
async def list_user_shares(
    creator_id: str,
    status: Optional[str] = Query(None)
):
    """List shares created by a user."""
    try:
        sharing_service = get_sharing_service()
        
        from sharing_service import ShareStatus
        share_status = None
        if status:
            try:
                share_status = ShareStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        shares = await sharing_service.list_user_shares(creator_id, share_status)
        
        return [
            {
                "share_id": share.share_id,
                "share_url": share.share_url,
                "share_type": share.share_type,
                "item_id": share.item_id,
                "access_level": share.access_level,
                "status": share.status,
                "created_at": share.created_at.isoformat(),
                "expires_at": share.expires_at.isoformat() if share.expires_at else None,
                "last_accessed": share.last_accessed.isoformat() if share.last_accessed else None
            }
            for share in shares
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error listing user shares: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

# Collaboration Endpoints
@app.post("/api/v1/share/{share_id}/invite")
async def create_collaboration_invite(
    share_id: str,
    request: CollaborationInviteRequest,
    invited_by: Optional[str] = Header(None, alias="X-User-ID")
):
    """Create a collaboration invitation."""
    try:
        sharing_service = get_sharing_service()
        
        invite = await sharing_service.create_collaboration_invite(
            share_id=share_id,
            email=request.email,
            access_level=request.access_level,
            invited_by=invited_by,
            expires_in_hours=request.expires_in_hours,
            personal_message=request.personal_message
        )
        
        return {
            "invite_id": invite.invite_id,
            "email": invite.email,
            "access_level": invite.access_level,
            "invited_at": invite.invited_at.isoformat(),
            "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
            "status": invite.status
        }
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error creating collaboration invite: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/collaboration/accept/{invite_id}")
async def accept_collaboration_invite(invite_id: str):
    """Accept a collaboration invitation."""
    try:
        sharing_service = get_sharing_service()
        success, share_link = await sharing_service.accept_collaboration_invite(invite_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Invitation not found or expired")
        
        return {
            "message": "Invitation accepted successfully",
            "share_url": share_link.share_url if share_link else None,
            "access_level": share_link.access_level if share_link else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error accepting collaboration invite: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

# Security and Analytics Endpoints
@app.get("/api/v1/sharing/security-report")
async def get_sharing_security_report():
    """Generate security report for sharing activities."""
    try:
        sharing_service = get_sharing_service()
        report = await sharing_service.get_security_report()
        return report
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error generating security report: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/sharing/cleanup")
async def cleanup_expired_shares():
    """Clean up expired shares and invitations."""
    try:
        sharing_service = get_sharing_service()
        await sharing_service.cleanup_expired_shares()
        
        export_manager = get_export_manager()
        await export_manager.cleanup_expired_exports()
        
        return {"message": "Cleanup completed successfully"}
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error during cleanup: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

# External API Integration Endpoints
@app.get("/api/v1/external/documents", response_model=List[DocumentInfo])
async def get_documents_api(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    file_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """External API: Get documents list for integration with external systems."""
    try:
        document_manager = get_document_manager()
        
        filter_params = DocumentFilter(
            file_type=file_type,
            status=status,
            limit=limit,
            offset=offset
        )
        
        documents = await document_manager.list_documents(filter_params)
        
        return [DocumentInfo(
            doc_id=doc.doc_id,
            title=doc.title,
            file_type=doc.file_type,
            upload_date=doc.upload_timestamp,
            chunk_count=doc.chunk_count,
            file_size=doc.file_size,
            status=doc.status,
            error_message=doc.error_message
        ) for doc in documents]
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error in external documents API: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.post("/api/v1/external/query")
async def external_query_api(
    request: QueryRequest,
    api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """External API: Query documents for integration with external systems."""
    try:
        # Basic API key validation (implement proper key management in production)
        if api_key != "external-api-key-placeholder":
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        rag_system = get_rag_system()
        response = await rag_system.query(
            request.question,
            max_chunks=request.max_chunks or 5
        )
        
        return QueryResponse(
            answer=response["answer"],
            sources=response["sources"],
            context_used=response["context_used"],
            context_tokens=response["context_tokens"],
            efficiency_ratio=response["efficiency_ratio"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error in external query API: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

@app.get("/api/v1/external/health")
async def external_health_api():
    """External API: Health check for integration monitoring."""
    try:
        rag_system = get_rag_system()
        document_count = rag_system.collection.count()
        
        # Check service health
        health_status = await health_monitor.get_system_health()
        
        return {
            "status": "healthy" if health_status.status == HealthStatus.HEALTHY else "degraded",
            "document_count": document_count,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "rag_system": health_status.components.get("rag_system", False),
                "chroma_db": health_status.components.get("chroma_db", False),
                "ollama": health_status.components.get("ollama", False)
            }
        }
        
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Error in external health API: {app_error.to_dict()}")
        raise HTTPException(status_code=500, detail=app_error.user_message)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info"
    )