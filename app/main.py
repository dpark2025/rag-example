"""
Main FastAPI application for the Local RAG System
Provides REST API endpoints for the RAG functionality
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import logging
from rag_backend import rag_system

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
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health"""
    try:
        # Check LLM
        llm_healthy = rag_system.llm_client.health_check()
        
        # Check vector database
        doc_count = rag_system.collection.count()
        
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
        doc_dicts = [doc.dict() for doc in documents]
        result = rag_system.add_documents(doc_dicts)
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
        
        result = rag_system.add_documents(documents)
        return {"message": result, "files_processed": len(files)}
    
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base"""
    try:
        result = rag_system.rag_query(request.question, max_chunks=request.max_chunks)
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/count")
async def get_document_count():
    """Get total number of document chunks"""
    try:
        count = rag_system.collection.count()
        return {"total_chunks": count}
    except Exception as e:
        logger.error(f"Error getting document count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents")
async def clear_documents():
    """Clear all documents from the knowledge base"""
    try:
        rag_system.collection.delete(where={})
        return {"message": "All documents cleared"}
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings")
async def get_settings():
    """Get current RAG system settings"""
    return {
        "similarity_threshold": rag_system.similarity_threshold,
        "max_context_tokens": rag_system.max_context_tokens,
        "chunk_size": rag_system.chunk_size,
        "chunk_overlap": rag_system.chunk_overlap
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
        if similarity_threshold is not None:
            rag_system.similarity_threshold = similarity_threshold
        if max_context_tokens is not None:
            rag_system.max_context_tokens = max_context_tokens
        if chunk_size is not None:
            rag_system.chunk_size = chunk_size
        if chunk_overlap is not None:
            rag_system.chunk_overlap = chunk_overlap
        
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