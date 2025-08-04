"""
Main FastAPI application for the Local RAG System
Provides REST API endpoints for the RAG functionality
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import logging
from datetime import datetime
import hashlib
import asyncio
from rag_backend import get_rag_system
from document_processing_tracker import processing_tracker, ProcessingStatus
from pdf_processor import pdf_processor, ExtractionMethod
from document_intelligence import document_intelligence, DocumentType
from error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity, RecoveryAction, get_error_stats
from health_monitor import health_monitor, HealthStatus
from document_manager import get_document_manager, DocumentFilter, BulkOperationResult
from upload_handler import get_upload_handler, BulkUploadResult, UploadStatus

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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info"
    )