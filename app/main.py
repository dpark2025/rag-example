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
from rag_backend import get_rag_system

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
    """Upload text files and add to knowledge base"""
    try:
        documents = []
        for file in files:
            if file.content_type != "text/plain":
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a text file")
            
            content = await file.read()
            documents.append({
                "title": file.filename,
                "content": content.decode('utf-8'),
                "source": "file_upload"
            })
        
        rag_sys = get_rag_system()
        result = rag_sys.add_documents(documents)
        return {"message": result, "files_processed": len(files)}
    
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