"""
Main FastAPI application for the Local RAG System
Provides REST API endpoints for the RAG functionality
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import logging
from datetime import datetime
import hashlib
from rag_backend import get_rag_system
from document_processing_tracker import processing_tracker, ProcessingStatus
from pdf_processor import pdf_processor, ExtractionMethod
from document_intelligence import document_intelligence, DocumentType

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
                "add": {"method": "POST", "path": "/documents", "description": "Add documents to knowledge base"},
                "upload": {"method": "POST", "path": "/documents/upload", "description": "Upload text files"},
                "count": {"method": "GET", "path": "/documents/count", "description": "Get document count"},
                "clear": {"method": "DELETE", "path": "/documents", "description": "Clear all documents"}
            },
            "settings": {
                "get": {"method": "GET", "path": "/settings", "description": "Get RAG settings"},
                "update": {"method": "POST", "path": "/settings", "description": "Update RAG settings"}
            }
        },
        "quick_test": "curl http://localhost:8000/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health"""
    try:
        rag_sys = get_rag_system()
        
        # Check LLM
        llm_healthy = rag_sys.llm_client.health_check()
        
        # Check vector database
        doc_count = rag_sys.collection.count()
        
        return HealthResponse(
            status="healthy" if llm_healthy else "degraded",
            components={
                "embedding_model": True,  # Always available locally
                "vector_database": True,  # ChromaDB always available
                "llm": llm_healthy
            },
            document_count=doc_count
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/documents")
async def add_documents(documents: List[Document]):
    """Add documents to the knowledge base"""
    try:
        rag_sys = get_rag_system()
        doc_dicts = [doc.dict() for doc in documents]
        result = rag_sys.add_documents(doc_dicts)
        return {"message": result, "count": len(documents)}
    except Exception as e:
        logger.error(f"Error adding documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
                processing_tracker.fail_task(task.doc_id, str(e))
                logger.error(f"Error processing document {doc['title']}: {e}")
        
        return {
            "message": f"Successfully uploaded {len(processed_docs)} of {len(files)} files",
            "files_processed": len(processed_docs),
            "processing_tasks": [task.doc_id for task in processing_tasks]
        }
    
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base"""
    try:
        rag_sys = get_rag_system()
        result = rag_sys.rag_query(request.question, max_chunks=request.max_chunks)
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info"
    )