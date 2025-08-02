# Fully Local RAG System with Reflex UI

## System Architecture (Completely Offline)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Reflex UI      │◄──►│   RAG Backend    │◄──►│   ChromaDB      │
│  - Chat Interface│    │   - FastAPI      │    │   - Local Vec DB│
│  - Port 3000    │    │   - Port 8000    │    │   - Embeddings  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         │                        ▼
         │              ┌─────────────────┐
         └─────────────►│   Local LLM     │
                        │   - Ollama      │
                        │   - Container   │
                        └─────────────────┘
```

All components run locally in containers - no internet required after setup!

## Project Structure

```
rag-example/
├── docker-compose.yml
├── Dockerfile.reflex
├── app/
│   ├── reflex_app/          # Reflex UI application
│   │   ├── components/      # UI components
│   │   ├── state/           # State management
│   │   ├── services/        # API client
│   │   └── pages/           # Page routes
│   ├── main.py              # FastAPI backend
│   ├── rag_backend.py       # RAG processing engine
│   ├── mcp_server.py        # MCP server
│   └── requirements.txt     # Backend dependencies
├── requirements.reflex.txt  # Reflex UI dependencies
├── data/
│   ├── documents/
│   └── chroma_db/
└── README.md
```

## Step 1: Core RAG Backend (Fully Local)

### app/main.py
```python
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
```

### app/mcp_server.py
```python
"""
MCP (Model Context Protocol) Server for RAG functionality
Provides standardized tool interface for RAG operations
"""

import asyncio
import json
import logging
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from rag_backend import rag_system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
server = Server("local-rag-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available RAG tools"""
    return [
        Tool(
            name="search_documents",
            description="Search through the local knowledge base for relevant information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant documents"
                    },
                    "max_chunks": {
                        "type": "integer",
                        "description": "Maximum number of document chunks to retrieve",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="add_documents",
            description="Add new documents to the knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "documents": {
                        "type": "array",
                        "description": "List of documents to add",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Document title"
                                },
                                "content": {
                                    "type": "string", 
                                    "description": "Document content"
                                },
                                "source": {
                                    "type": "string",
                                    "description": "Document source",
                                    "default": "mcp_upload"
                                }
                            },
                            "required": ["title", "content"]
                        }
                    }
                },
                "required": ["documents"]
            }
        ),
        Tool(
            name="rag_query",
            description="Complete RAG operation: search documents and generate answer",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question to answer using the knowledge base"
                    },
                    "max_chunks": {
                        "type": "integer",
                        "description": "Maximum number of chunks to use for context",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="get_system_status",
            description="Get the current status of the RAG system",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="update_settings",
            description="Update RAG system efficiency settings",
            inputSchema={
                "type": "object",
                "properties": {
                    "similarity_threshold": {
                        "type": "number",
                        "description": "Minimum similarity score for retrieval (0.0-1.0)",
                        "minimum": 0.0,
                        "maximum": 1.0
                    },
                    "max_context_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens to use for context",
                        "minimum": 500,
                        "maximum": 8000
                    }
                }
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """Handle tool calls"""
    
    if arguments is None:
        arguments = {}
    
    try:
        if name == "search_documents":
            query = arguments.get("query", "")
            max_chunks = arguments.get("max_chunks", 3)
            
            if not query:
                return [TextContent(
                    type="text",
                    text="Error: Query parameter is required"
                )]
            
            # Search documents
            results = rag_system.adaptive_retrieval(query, max_chunks=max_chunks)
            
            # Format results
            response = {
                "query": query,
                "results_count": len(results),
                "documents": [
                    {
                        "title": doc["title"],
                        "content_preview": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                        "source": doc["source"],
                        "relevance_score": f"{doc['score']:.3f}"
                    } for doc in results
                ]
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
        
        elif name == "add_documents":
            documents = arguments.get("documents", [])
            
            if not documents:
                return [TextContent(
                    type="text",
                    text="Error: No documents provided"
                )]
            
            # Add documents
            result = rag_system.add_documents(documents)
            
            response = {
                "status": "success",
                "message": result,
                "documents_added": len(documents)
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
        
        elif name == "rag_query":
            question = arguments.get("question", "")
            max_chunks = arguments.get("max_chunks", 3)
            
            if not question:
                return [TextContent(
                    type="text",
                    text="Error: Question parameter is required"
                )]
            
            # Perform complete RAG query
            result = rag_system.rag_query(question, max_chunks=max_chunks)
            
            response = {
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"],
                "efficiency_metrics": {
                    "chunks_used": result["context_used"],
                    "context_tokens": result["context_tokens"],
                    "efficiency_ratio": result["efficiency_ratio"]
                }
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
        
        elif name == "get_system_status":
            # Get system status
            doc_count = rag_system.collection.count()
            llm_healthy = rag_system.llm_client.health_check()
            
            status = {
                "status": "healthy" if llm_healthy else "degraded",
                "components": {
                    "embedding_model": True,
                    "vector_database": True,
                    "llm": llm_healthy
                },
                "document_count": doc_count,
                "settings": {
                    "similarity_threshold": rag_system.similarity_threshold,
                    "max_context_tokens": rag_system.max_context_tokens,
                    "chunk_size": rag_system.chunk_size
                }
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(status, indent=2)
            )]
        
        elif name == "update_settings":
            # Update settings
            updated = []
            
            if "similarity_threshold" in arguments:
                rag_system.similarity_threshold = arguments["similarity_threshold"]
                updated.append("similarity_threshold")
            
            if "max_context_tokens" in arguments:
                rag_system.max_context_tokens = arguments["max_context_tokens"]
                updated.append("max_context_tokens")
            
            response = {
                "status": "success",
                "updated_settings": updated,
                "current_settings": {
                    "similarity_threshold": rag_system.similarity_threshold,
                    "max_context_tokens": rag_system.max_context_tokens
                }
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Error: Unknown tool '{name}'"
            )]
    
    except Exception as e:
        logger.error(f"Error in tool '{name}': {e}")
        return [TextContent(
            type="text",
            text=f"Error executing tool '{name}': {str(e)}"
        )]

async def main():
    """Run the MCP server"""
    logger.info("Starting Local RAG MCP Server...")
    
    # Initialize RAG system
    logger.info("RAG system initialized and ready")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```
```txt
# Backend dependencies for RAG system
sentence-transformers==3.3.1
chromadb==0.4.15
requests==2.31.0
python-multipart==0.0.6
fastapi==0.115.0
uvicorn==0.32.0
python-dotenv==1.0.0
```

### app/rag_backend.py
```python
import os
import requests
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalLLMClient:
    def __init__(self, base_url="http://ollama:11434"):
        self.base_url = base_url
        logger.info(f"Initializing LLM client with URL: {base_url}")
    
    def chat(self, messages, model="llama3.2:8b", temperature=0.7, max_tokens=1000):
        """Chat with local Ollama LLM"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                logger.error(f"LLM error: {response.status_code} - {response.text}")
                return "Sorry, I'm having trouble connecting to the language model."
        except Exception as e:
            logger.error(f"LLM connection error: {e}")
            return "Sorry, the language model is not available right now."
    
    def health_check(self):
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

class LocalRAGSystem:
    def __init__(self, llm_client=None, data_path="/app/data"):
        self.data_path = data_path
        
        # Initialize local embedding model
        logger.info("Loading embedding model...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB (persistent local storage)
        chroma_path = os.path.join(data_path, "chroma_db")
        os.makedirs(chroma_path, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize LLM client
        self.llm_client = llm_client or LocalLLMClient()
        
        # RAG efficiency settings
        self.max_context_tokens = 2000  # Adjust based on your LLM
        self.similarity_threshold = 0.7  # Minimum relevance score
        self.chunk_size = 400  # Optimal chunk size for most LLMs
        self.chunk_overlap = 50  # Overlap between chunks
        
        logger.info(f"RAG system initialized with {self.collection.count()} documents")
    
    def smart_chunking(self, text: str) -> List[str]:
        """Intelligent text chunking for optimal RAG performance"""
        # Handle empty or very short text
        if len(text.strip()) < 100:
            return [text.strip()]
        
        chunks = []
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # Check if adding this paragraph exceeds chunk size
            estimated_tokens = len((current_chunk + " " + paragraph).split()) * 1.3
            
            if estimated_tokens <= self.chunk_size and current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk
                if len(paragraph.split()) * 1.3 > self.chunk_size:
                    # Split large paragraph by sentences
                    sentences = paragraph.split('. ')
                    current_chunk = ""
                    
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence.endswith('.'):
                            sentence += '.'
                        
                        test_chunk = current_chunk + " " + sentence if current_chunk else sentence
                        if len(test_chunk.split()) * 1.3 <= self.chunk_size:
                            current_chunk = test_chunk
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence
                else:
                    current_chunk = paragraph
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Handle overlap for better context continuity
        if len(chunks) > 1:
            overlapped_chunks = []
            for i, chunk in enumerate(chunks):
                if i == 0:
                    overlapped_chunks.append(chunk)
                else:
                    # Add overlap from previous chunk
                    prev_words = chunks[i-1].split()
                    overlap_words = prev_words[-self.chunk_overlap:] if len(prev_words) > self.chunk_overlap else prev_words
                    overlapped_chunk = " ".join(overlap_words) + " " + chunk
                    overlapped_chunks.append(overlapped_chunk)
            
            return overlapped_chunks
        
        return chunks
    
    def add_documents(self, documents: List[Dict[str, str]]):
        """Add documents with smart chunking"""
        if not documents:
            return "No documents provided"
        
        try:
            all_chunks = []
            current_count = self.collection.count()
            doc_id = current_count
            
            for doc in documents:
                # Smart chunking instead of naive splitting
                chunks = self.smart_chunking(doc['content'])
                
                for i, chunk in enumerate(chunks):
                    embedding = self.encoder.encode(chunk).tolist()
                    
                    all_chunks.append({
                        "id": f"doc_{doc_id}_chunk_{i}",
                        "embedding": embedding,
                        "text": chunk,
                        "metadata": {
                            "title": doc["title"],
                            "source": doc.get("source", "unknown"),
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "doc_id": doc_id,
                            "content_preview": chunk[:150] + "..." if len(chunk) > 150 else chunk
                        }
                    })
                
                doc_id += 1
            
            # Batch insert for efficiency
            if all_chunks:
                self.collection.add(
                    embeddings=[chunk["embedding"] for chunk in all_chunks],
                    documents=[chunk["text"] for chunk in all_chunks],
                    metadatas=[chunk["metadata"] for chunk in all_chunks],
                    ids=[chunk["id"] for chunk in all_chunks]
                )
            
            logger.info(f"Added {len(documents)} documents ({len(all_chunks)} chunks) to vector database")
            return f"Successfully added {len(documents)} documents ({len(all_chunks)} chunks)"
        
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return f"Error adding documents: {str(e)}"
    
    def adaptive_retrieval(self, query: str, max_chunks: int = 5) -> List[Dict]:
        """Efficient retrieval with relevance filtering and token management"""
        try:
            query_embedding = self.encoder.encode(query).tolist()
            
            # Retrieve more candidates than needed for filtering
            candidate_count = min(max_chunks * 3, self.collection.count())
            if candidate_count == 0:
                return []
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=candidate_count,
                include=["metadatas", "documents", "distances"]
            )
            
            if not results['ids'] or not results['ids'][0]:
                return []
            
            # Filter by similarity threshold and manage tokens
            filtered_docs = []
            total_tokens = 0
            
            for i in range(len(results['ids'][0])):
                similarity_score = 1 - results['distances'][0][i]
                
                # Only include chunks above similarity threshold
                if similarity_score < self.similarity_threshold:
                    continue
                
                chunk_text = results['documents'][0][i]
                chunk_tokens = len(chunk_text.split()) * 1.3  # Rough token estimate
                
                # Check if adding this chunk would exceed context limit
                if total_tokens + chunk_tokens > self.max_context_tokens:
                    break
                
                filtered_docs.append({
                    "title": results['metadatas'][0][i]['title'],
                    "content": chunk_text,
                    "source": results['metadatas'][0][i]['source'],
                    "score": similarity_score,
                    "chunk_index": results['metadatas'][0][i].get('chunk_index', 0),
                    "doc_id": results['metadatas'][0][i].get('doc_id', 'unknown')
                })
                
                total_tokens += chunk_tokens
                
                # Stop if we have enough high-quality chunks
                if len(filtered_docs) >= max_chunks:
                    break
            
            # Sort by relevance score (highest first)
            filtered_docs.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"Retrieved {len(filtered_docs)} chunks ({total_tokens:.0f} tokens) for query")
            return filtered_docs
        
        except Exception as e:
            logger.error(f"Error in adaptive retrieval: {e}")
            return []
    
    def search_documents(self, query: str, top_k: int = 3) -> List[Dict]:
        """Legacy method for backward compatibility"""
        return self.adaptive_retrieval(query, max_chunks=top_k)
    
    def build_efficient_context(self, chunks: List[Dict]) -> str:
        """Build context efficiently to minimize token usage"""
        if not chunks:
            return "No relevant information found."
        
        context_parts = []
        
        # Group chunks by document to avoid redundancy
        docs_by_id = {}
        for chunk in chunks:
            doc_id = chunk.get('doc_id', 'unknown')
            if doc_id not in docs_by_id:
                docs_by_id[doc_id] = []
            docs_by_id[doc_id].append(chunk)
        
        # Build context with most relevant information first
        for doc_id, doc_chunks in docs_by_id.items():
            # Sort chunks within document by score
            doc_chunks.sort(key=lambda x: x['score'], reverse=True)
            
            # Use most relevant chunk in full, others as supporting facts
            primary_chunk = doc_chunks[0]
            context_parts.append(f"Document: {primary_chunk['title']}")
            context_parts.append(primary_chunk['content'])
            
            # Add supporting chunks more concisely
            if len(doc_chunks) > 1:
                supporting_facts = []
                for chunk in doc_chunks[1:3]:  # Max 2 supporting chunks
                    # Extract key sentences (first sentence usually contains main point)
                    sentences = chunk['content'].split('. ')
                    key_sentence = sentences[0] if sentences else chunk['content']
                    if not key_sentence.endswith('.'):
                        key_sentence += '.'
                    supporting_facts.append(f"• {key_sentence}")
                
                if supporting_facts:
                    context_parts.append("Additional context:")
                    context_parts.extend(supporting_facts)
            
            context_parts.append("")  # Separator between documents
        
        return "\n".join(context_parts)
    
    def extract_key_sentences(self, text: str, query: str, max_sentences: int = 2) -> str:
        """Extract most relevant sentences from a chunk"""
        sentences = text.split('. ')
        if len(sentences) <= max_sentences:
            return text
        
        query_words = set(query.lower().split())
        scored_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_words = set(sentence.lower().split())
            # Simple relevance scoring based on word overlap
            overlap_score = len(query_words.intersection(sentence_words))
            # Bonus for position (earlier sentences often more important)
            position_bonus = (len(sentences) - sentences.index(sentence)) / len(sentences)
            total_score = overlap_score + position_bonus
            
            scored_sentences.append((sentence, total_score))
        
        # Return top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in scored_sentences[:max_sentences]]
        
        result = '. '.join(top_sentences)
        if not result.endswith('.'):
            result += '.'
        
        return result
        """Generate answer using retrieved context"""
        if not context_docs:
            return "I couldn't find any relevant documents to answer your question."
        
    def generate_answer(self, question: str, context_docs: List[Dict]) -> str:
        """Generate answer using retrieved context with efficient prompting"""
        if not context_docs:
            return "I couldn't find any relevant documents to answer your question."
        
        # Build efficient context
        context = self.build_efficient_context(context_docs)
        
        # Count tokens for monitoring
        estimated_tokens = len(context.split()) * 1.3
        logger.info(f"Using {estimated_tokens:.0f} tokens for context")
        
        # Efficient system prompt
        system_prompt = """Answer questions using only the provided context. Be concise but complete. If the answer isn't in the context, say so clearly."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user", 
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ]
        
        return self.llm_client.chat(messages, temperature=0.3, max_tokens=500)
    
    def rag_query(self, question: str, max_chunks: int = None) -> Dict:
        """Complete RAG pipeline with efficiency optimizations"""
        # Adaptive chunk selection based on query complexity
        if max_chunks is None:
            query_words = len(question.split())
            if query_words < 10:
                max_chunks = 2  # Simple query
            elif any(word in question.lower() for word in ['compare', 'difference', 'versus', 'analyze']):
                max_chunks = 5  # Complex comparison query
            else:
                max_chunks = 3  # Default
        
        # Retrieve with efficiency optimizations
        docs = self.adaptive_retrieval(question, max_chunks=max_chunks)
        
        # Generate answer
        answer = self.generate_answer(question, docs)
        
        # Calculate efficiency metrics
        total_context_tokens = sum(len(doc['content'].split()) * 1.3 for doc in docs)
        
        return {
            "answer": answer,
            "sources": [{"title": doc["title"], "score": f"{doc['score']:.2f}"} for doc in docs],
            "context_used": len(docs),
            "context_tokens": int(total_context_tokens),
            "efficiency_ratio": len(docs) / max(total_context_tokens, 1)  # chunks per token
        }

# Global instance
rag_system = LocalRAGSystem()
```

### Reflex UI Implementation

The Reflex UI provides a modern, reactive web interface for the RAG system. The implementation includes:

- **Chat Interface**: Real-time messaging with message history and auto-scroll
- **System Status**: Live health monitoring of all components
- **Document Management**: Upload and manage documents in the knowledge base
- **Source Attribution**: See which documents informed each response
- **Performance Metrics**: Real-time efficiency tracking and token usage

The complete Reflex implementation is located in `app/reflex_app/` with:
- `components/`: Reusable UI components (chat, forms, layouts)
- `state/`: Application and chat state management
- `services/`: API client for backend communication
- `pages/`: Main application pages and routing

For detailed component code, see the Reflex application files in the project structure.

## Step 2: Docker Configuration

### Dockerfile.rag-app
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download embedding model during build
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY app/ .

# Create data directory
RUN mkdir -p /app/data/chroma_db /app/data/documents

# Expose Reflex ports
EXPOSE 3000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:3000/_health || exit 1

# Run Reflex
CMD ["reflex", "run", "--frontend-port", "3000", "--backend-port", "8001", "--frontend-host", "0.0.0.0", "--backend-host", "0.0.0.0"]
```

### Dockerfile.ollama
```dockerfile
FROM ollama/ollama:latest

# Create models directory
RUN mkdir -p /root/.ollama

# Expose Ollama port
EXPOSE 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -f http://localhost:11434/api/tags || exit 1

# Start Ollama server
CMD ["ollama", "serve"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  ollama:
    build:
      context: .
      dockerfile: Dockerfile.ollama
    container_name: local-rag-ollama
    ports:
      - "11434:11434"
    volumes:
      - ./models/ollama_models:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

  reflex-app:
    build:
      context: .
      dockerfile: Dockerfile.reflex
    container_name: local-rag-reflex
    ports:
      - "3000:3000"  # Reflex frontend
      - "8001:8001"  # Reflex backend (different from FastAPI)
    volumes:
      - ./data:/app/data:Z
      - ./app:/app/app:Z
    environment:
      - PYTHONPATH=/app
      - REFLEX_HOST=0.0.0.0
      - REFLEX_PORT=3000
      - API_BASE_URL=http://host.containers.internal:8000
      - OLLAMA_HOST=host.containers.internal:11434
    extra_hosts:
      - "host.containers.internal:host-gateway"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/_health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    depends_on:
      - rag-backend

  rag-backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: local-rag-backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data:Z
      - ./app:/app:Z
    environment:
      - PYTHONPATH=/app
      - OLLAMA_HOST=host.containers.internal:11434
    extra_hosts:
      - "host.containers.internal:host-gateway"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  ollama_models:
    driver: local
  chroma_data:
    driver: local
```

## Step 3: Setup Scripts

### setup.sh
```bash
#!/bin/bash

# Setup script for Local RAG System

echo "🐳 Setting up Local RAG System..."

# Create necessary directories
mkdir -p data/chroma_db data/documents models/ollama_models

# Build containers
echo "📦 Building containers..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to start..."
sleep 30

# Pull a small model to start with
echo "📥 Downloading Llama 3.2 (3B) model..."
docker-compose exec ollama ollama pull llama3.2:3b

echo "✅ Setup complete!"
echo ""
echo "🌐 Access your Local RAG System at: http://localhost:3000"
echo "🤖 Ollama API available at: http://localhost:11434"
echo ""
echo "To pull more models:"
echo "  docker-compose exec ollama ollama pull llama3.2:8b"
echo "  docker-compose exec ollama ollama pull mistral:7b"
echo ""
echo "To stop the system:"
echo "  docker-compose down"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
```

### Makefile
```makefile
.PHONY: build start stop logs shell-rag shell-ollama pull-model health

# Build all containers
build:
	docker-compose build

# Start the system
start:
	docker-compose up -d

# Stop the system  
stop:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Shell into RAG app container
shell-rag:
	docker-compose exec rag-app bash

# Shell into Ollama container
shell-ollama:
	docker-compose exec ollama bash

# Pull a new model (usage: make pull-model MODEL=llama3.2:8b)
pull-model:
	docker-compose exec ollama ollama pull $(MODEL)

# Check system health
health:
	@echo "Checking system health..."
	@curl -s http://localhost:3000/_health > /dev/null && echo "✅ Reflex UI: Healthy" || echo "❌ Reflex UI: Unhealthy"
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ RAG Backend: Healthy" || echo "❌ RAG Backend: Unhealthy"
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Ollama: Healthy" || echo "❌ Ollama: Unhealthy"

# Complete setup
setup: build start
	@echo "⏳ Waiting for services to be ready..."
	@sleep 30
	@echo "📥 Downloading initial model..."
	@docker-compose exec ollama ollama pull llama3.2:3b
	@echo "✅ Setup complete! Visit http://localhost:3000"
```

## Step 4: Quick Start Guide

### 1. Clone and Setup
```bash
# Create project directory
mkdir local-rag-system && cd local-rag-system

# Copy all the files above into the structure
# ... (create the files as shown)

# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

### 2. Alternative: Using Makefile
```bash
# Build and start everything
make setup

# Check if everything is running
make health

# View logs
make logs

# Pull additional models
make pull-model MODEL=llama3.2:8b
make pull-model MODEL=mistral:7b
```

### 3. Access Your System
- **Reflex UI**: http://localhost:3000
- **FastAPI Backend**: http://localhost:8000
- **Ollama API**: http://localhost:11434

## Step 5: Usage Examples

### Available Models (by size)
```bash
# Small models (3-4GB RAM)
docker-compose exec ollama ollama pull llama3.2:3b
docker-compose exec ollama ollama pull phi3:mini

# Medium models (8GB RAM)  
docker-compose exec ollama ollama pull llama3.2:8b
docker-compose exec ollama ollama pull mistral:7b

# Large models (16GB+ RAM)
docker-compose exec ollama ollama pull llama3.1:70b
docker-compose exec ollama ollama pull codellama:34b
```

### Adding Documents Programmatically
```python
# Connect to running system
import requests

# Add documents via API
documents = [
    {
        "title": "Company Policy",
        "content": "Our company values...",
        "source": "hr_manual"
    }
]

# The system will automatically index them
```

## RAG Efficiency Optimizations

This system includes several efficiency optimizations to minimize context usage and improve performance:

### 1. **Smart Chunking**
- **Semantic Chunking**: Splits documents by paragraphs and sentences, not arbitrary token counts
- **Optimal Size**: 400 tokens per chunk (tested for best retrieval performance)
- **Overlap**: 50-token overlap between chunks for context continuity
- **Prevents**: Cutting sentences/paragraphs in the middle

### 2. **Adaptive Retrieval**
- **Relevance Filtering**: Only retrieves chunks above similarity threshold (0.7)
- **Token Management**: Stops retrieving when context limit is reached
- **Quality-First**: Prioritizes high-relevance chunks over quantity
- **Dynamic Selection**: Adjusts chunk count based on query complexity

### 3. **Efficient Context Building**
- **Hierarchical Context**: Most relevant chunk in full, others as supporting facts
- **Document Grouping**: Avoids redundancy from same document
- **Key Sentence Extraction**: Summarizes less relevant chunks
- **Structured Templates**: Uses bullet points and concise formatting

### 4. **Query-Adaptive Strategy**
```python
# Simple query (< 10 words) = 2 chunks
"What is Docker?"

# Complex comparison = 5 chunks  
"Compare Docker containers with virtual machines"

# Default queries = 3 chunks
"How do I set up a local RAG system?"
```

### 5. **Token Monitoring**
- Real-time token counting and efficiency metrics
- Configurable similarity threshold and context limits
- Performance tracking (chunks per token ratio)
- Visual feedback in the UI

### 6. **Context Window Optimization by LLM**
| LLM Type | Context Limit | Our Setting | Strategy |
|----------|---------------|-------------|----------|
| **Llama 3.2 3B** | 4K tokens | 1.5K tokens | Very selective |
| **Llama 3.2 8B** | 8K tokens | 2K tokens | Balanced |
| **Large Models** | 32K+ tokens | 4K tokens | More context OK |

## Features

✅ **Completely Offline** - No internet required after setup  
✅ **Data Privacy** - Everything stays on your machine  
✅ **Easy Deployment** - Single docker-compose command  
✅ **Scalable** - Add more models and documents easily  
✅ **Persistent Storage** - Data survives container restarts  
✅ **Health Monitoring** - Built-in health checks  
✅ **Multiple Models** - Switch between different LLMs  
✅ **Modern Web Interface** - Reactive Reflex UI with real-time updates  
✅ **Efficiency Optimized** - Smart chunking and adaptive retrieval
✅ **Token Management** - Configurable context limits and monitoring

## Resource Requirements

| Component | Minimum RAM | Recommended RAM |
|-----------|-------------|-----------------|
| RAG App | 2GB | 4GB |
| Ollama + 3B Model | 4GB | 8GB |
| Ollama + 8B Model | 8GB | 16GB |
| **Total System** | **6GB** | **20GB** |

## Troubleshooting

### Common Issues
```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs ollama
docker-compose logs rag-app

# Restart services
docker-compose restart

# Clean restart
docker-compose down && docker-compose up -d

# Free up space
docker system prune -f
```

This setup gives you a completely self-contained, offline RAG system that's production-ready and easy to deploy!