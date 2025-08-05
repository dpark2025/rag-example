import os
import requests
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging
from datetime import datetime
import time
import random
from functools import wraps
import asyncio

# Performance optimizations
from .performance_cache import get_rag_query_cache, get_embedding_cache, get_document_cache
from .connection_pool import get_pool_manager
from .performance_monitor import get_performance_monitor, record_rag_query_time, record_cache_hit_rate, record_memory_usage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retry and circuit breaker utilities
def retry_with_exponential_backoff(max_retries=3, base_delay=1, max_delay=30, backoff_factor=2):
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (backoff_factor ** attempt) + random.uniform(0, 1), max_delay)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
            
            raise last_exception
        return wrapper
    return decorator

class CircuitBreaker:
    """Simple circuit breaker implementation for external service calls."""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def can_attempt(self):
        """Check if we can attempt the operation."""
        if self.state == 'CLOSED':
            return True
        elif self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record a successful operation."""
        self.failure_count = 0
        self.state = 'CLOSED'
        logger.info("Circuit breaker reset to CLOSED state")
    
    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
        
        if self.state == 'HALF_OPEN':
            self.state = 'OPEN'
            logger.warning("Circuit breaker returned to OPEN state after failure in HALF_OPEN")

class LocalLLMClient:
    def __init__(self, base_url=None):
        # Auto-detect if running in container vs local
        if base_url is None:
            import os
            
            # Check for environment variable first (for container configs)
            ollama_host = os.environ.get('OLLAMA_HOST')
            if ollama_host:
                base_url = f"http://{ollama_host}"
            elif os.path.exists('/.dockerenv') or os.environ.get('container'):
                # Running in container - try different host access methods in order
                import socket
                connection_attempts = [
                    ('host.containers.internal', 11434, "http://host.containers.internal:11434"),
                    ('10.0.2.2', 11434, "http://10.0.2.2:11434"),
                    ('172.17.0.1', 11434, "http://172.17.0.1:11434"),  # Common Docker bridge IP
                    ('localhost', 11434, "http://localhost:11434")
                ]
                
                base_url = "http://localhost:11434"  # fallback
                for host, port, url in connection_attempts:
                    try:
                        socket.create_connection((host, port), timeout=3)
                        base_url = url
                        logger.info(f"Successfully connected to Ollama at {host}:{port}")
                        break
                    except Exception as e:
                        logger.debug(f"Failed to connect to {host}:{port} - {e}")
                        continue
                        
                if base_url == "http://localhost:11434":
                    logger.warning("Could not connect to Ollama on any known host addresses")
            else:
                # Running locally - use localhost
                base_url = "http://localhost:11434"
        
        self.base_url = base_url
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        self.last_successful_health_check = None
        
        # Initialize connection pool for HTTP requests
        self.pool_manager = get_pool_manager()
        self.http_pool = self.pool_manager.create_ollama_pool(
            name="ollama_main",
            base_url=base_url,
            min_connections=2,
            max_connections=6
        )
        
        logger.info(f"Initializing LLM client with URL: {base_url} (with connection pooling)")
    
    def chat(self, messages, model="llama3.2:3b", temperature=0.7, max_tokens=1000):
        """Chat with local Ollama LLM with circuit breaker and retry logic."""
        # Check circuit breaker first
        if not self.circuit_breaker.can_attempt():
            logger.warning("Circuit breaker is OPEN, skipping LLM call")
            return "Sorry, the language model is temporarily unavailable. Please try again later."
        
        try:
            return self._chat_with_retry(messages, model, temperature, max_tokens)
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"LLM chat failed after retries: {e}")
            return "Sorry, the language model is not available right now."
    
    @retry_with_exponential_backoff(max_retries=2, base_delay=1, max_delay=10)
    def _chat_with_retry(self, messages, model, temperature, max_tokens):
        """Internal chat method with retry logic and connection pooling."""
        # Get pooled connection
        pooled_conn = self.http_pool.get_connection()
        if not pooled_conn:
            raise Exception("Failed to get HTTP connection from pool")
        
        try:
            session = pooled_conn.connection
            
            response = session.post(
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
                timeout=(5.0, 120.0)  # (connect, read) timeout
            )
            
            if response.status_code == 200:
                self.circuit_breaker.record_success()
                result = response.json()["message"]["content"]
                logger.debug(f"LLM response received: {len(result)} characters")
                
                # Return connection to pool
                self.http_pool.return_connection(pooled_conn, error_occurred=False)
                return result
            else:
                error_msg = f"LLM API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                self.http_pool.return_connection(pooled_conn, error_occurred=True)
                raise Exception(error_msg)
                
        except Exception as e:
            # Return connection to pool with error flag
            self.http_pool.return_connection(pooled_conn, error_occurred=True)
            raise
    
    def health_check(self, use_cache=True, cache_ttl=30):
        """Check if Ollama is running with caching to avoid excessive requests."""
        # Use cached result if available and recent
        if use_cache and self.last_successful_health_check:
            if time.time() - self.last_successful_health_check < cache_ttl:
                return True
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            is_healthy = response.status_code == 200
            
            if is_healthy:
                self.last_successful_health_check = time.time()
                # Reset circuit breaker on successful health check
                if self.circuit_breaker.state != 'CLOSED':
                    self.circuit_breaker.record_success()
                logger.debug("Ollama health check passed")
            else:
                logger.warning(f"Ollama health check failed: HTTP {response.status_code}")
            
            return is_healthy
            
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    def get_connection_info(self):
        """Get connection status information for debugging."""
        return {
            "base_url": self.base_url,
            "circuit_breaker_state": self.circuit_breaker.state,
            "failure_count": self.circuit_breaker.failure_count,
            "last_successful_health_check": self.last_successful_health_check,
            "health_status": self.health_check(use_cache=False)
        }

class LocalRAGSystem:
    def __init__(self, llm_client=None, data_path="./data"):
        self.data_path = data_path
        
        # Initialize local embedding model
        logger.info("Loading embedding model...")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB with connection pooling
        chroma_path = os.path.join(data_path, "chroma_db")
        os.makedirs(chroma_path, exist_ok=True)
        
        # Get connection pool manager and create ChromaDB pool
        self.pool_manager = get_pool_manager()
        self.chroma_pool = self.pool_manager.create_chromadb_pool(
            name="chromadb_main",
            chroma_path=chroma_path,
            min_connections=1,
            max_connections=3
        )
        
        # Get primary connection for collection access
        # Note: ChromaDB collections are accessed through the client
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
        
        # Initialize caching systems
        self.rag_cache = get_rag_query_cache()
        self.embedding_cache = get_embedding_cache()
        self.document_cache = get_document_cache()
        
        # Initialize performance monitoring
        self.performance_monitor = get_performance_monitor()
        
        # RAG efficiency settings
        self.max_context_tokens = 2000  # Adjust based on your LLM
        self.similarity_threshold = 0.6  # Minimum relevance score (lowered for better recall)
        self.chunk_size = 400  # Optimal chunk size for most LLMs
        self.chunk_overlap = 50  # Overlap between chunks
        
        logger.info(f"RAG system initialized with {self.collection.count()} documents (with caching and pooling)")
    
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
    
    def _clean_metadata(self, metadata: dict) -> dict:
        """Clean metadata to ensure ChromaDB compatibility."""
        cleaned = {}
        for key, value in metadata.items():
            if value is None:
                continue  # Skip None values
            elif isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                cleaned[key] = ", ".join(str(item) for item in value if item is not None)
            else:
                # Convert other types to strings
                cleaned[key] = str(value)
        return cleaned
    
    def custom_chunking(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Custom chunking with specified parameters (in tokens/words)"""
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        # Ensure valid step size
        step_size = max(1, chunk_size - chunk_overlap)
        
        for i in range(0, len(words), step_size):
            chunk_words = words[i:i + chunk_size]
            if chunk_words:  # Only add non-empty chunks
                chunks.append(' '.join(chunk_words))
        
        return chunks
    
    def add_documents(self, documents: List[Dict[str, str]], chunk_size: int = None, chunk_overlap: int = None):
        """Add documents with smart chunking and optional custom parameters"""
        if not documents:
            return "No documents provided"
        
        try:
            all_chunks = []
            current_count = self.collection.count()
            doc_id = current_count
            
            for doc in documents:
                # Use provided doc_id if available, otherwise use incrementing counter
                current_doc_id = doc.get("doc_id", str(doc_id))
                
                # Use custom chunking parameters if provided, otherwise use smart chunking
                if chunk_size is not None and chunk_overlap is not None:
                    chunks = self.custom_chunking(doc['content'], chunk_size, chunk_overlap)
                else:
                    chunks = self.smart_chunking(doc['content'])
                
                for i, chunk in enumerate(chunks):
                    embedding = self.encoder.encode(chunk).tolist()
                    
                    all_chunks.append({
                        "id": f"doc_{current_doc_id}_chunk_{i}",
                        "embedding": embedding,
                        "text": chunk,
                        "metadata": self._clean_metadata({
                            "title": doc["title"],
                            "source": doc.get("source", "unknown"),
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "doc_id": str(current_doc_id),
                            "content_preview": chunk[:150] + "..." if len(chunk) > 150 else chunk,
                            "file_type": doc.get("file_type", "txt"),
                            "upload_timestamp": doc.get("upload_timestamp", 
                                datetime.now().isoformat()),
                            "original_filename": doc.get("original_filename", doc["title"]),
                            "file_size": len(doc.get("content", "")),
                            # Document intelligence metadata
                            "document_type": doc.get("document_type", "plain_text"),
                            "content_structure": doc.get("content_structure", "unstructured"),
                            "intelligence_confidence": doc.get("intelligence_confidence", 0.5),
                            "suggested_chunk_size": doc.get("suggested_chunk_size", 400),
                            "suggested_overlap": doc.get("suggested_overlap", 50),
                            "processing_notes": "; ".join(doc.get("processing_notes", [])) if doc.get("processing_notes") else "",
                            # PDF-specific metadata (if available)
                            "extraction_method": doc.get("extraction_method"),
                            "quality_score": doc.get("quality_score"),
                            "page_count": doc.get("page_count")
                        })
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
    
    def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text."""
        cache_key = self.embedding_cache._generate_key("embed", text)
        return self.embedding_cache.get(cache_key)
    
    def _cache_embedding(self, text: str, embedding: List[float], ttl: float = 1800.0):
        """Cache embedding for text."""
        cache_key = self.embedding_cache._generate_key("embed", text)
        self.embedding_cache.set(cache_key, embedding, ttl)
    
    def _generate_embedding_with_cache(self, text: str) -> List[float]:
        """Generate embedding with caching and performance monitoring."""
        # Try cache first
        cached_embedding = self._get_cached_embedding(text)
        if cached_embedding is not None:
            logger.debug(f"Using cached embedding for text: '{text[:50]}...'")
            return cached_embedding
        
        # Generate new embedding with timing
        with self.performance_monitor.timer("embedding_generation"):
            start_time = time.time()
            embedding = self.encoder.encode(text).tolist()
            embedding_time = (time.time() - start_time) * 1000
        
        # Cache the result
        self._cache_embedding(text, embedding)
        
        logger.debug(f"Generated new embedding in {embedding_time:.1f}ms for text: '{text[:50]}...'")
        return embedding
    
    @retry_with_exponential_backoff(max_retries=2, base_delay=0.5, max_delay=5)
    def adaptive_retrieval(self, query: str, max_chunks: int = 5) -> List[Dict]:
        """Efficient retrieval with relevance filtering and token management"""
        if not query or not query.strip():
            logger.warning("Empty query provided to adaptive_retrieval")
            return []
            
        try:
            logger.debug(f"Starting adaptive retrieval for query: '{query[:50]}...' (max_chunks={max_chunks})")
            
            # Generate query embedding with caching
            query_embedding = self._generate_embedding_with_cache(query)
            logger.debug(f"Generated query embedding with {len(query_embedding)} dimensions")
            
            # Check document count
            doc_count = self.collection.count()
            if doc_count == 0:
                logger.warning("No documents in ChromaDB collection")
                return []
            
            # Retrieve more candidates than needed for filtering
            candidate_count = min(max_chunks * 3, doc_count)
            logger.debug(f"Querying ChromaDB for {candidate_count} candidates from {doc_count} total documents")
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=candidate_count,
                include=["metadatas", "documents", "distances"]
            )
            
            if not results['ids'] or not results['ids'][0]:
                logger.warning("ChromaDB query returned no results")
                return []
            
            logger.debug(f"ChromaDB returned {len(results['ids'][0])} results")
            
            # Filter by similarity threshold and manage tokens
            filtered_docs = []
            total_tokens = 0
            filtered_count = 0
            token_limited_count = 0
            
            for i in range(len(results['ids'][0])):
                similarity_score = 1 - results['distances'][0][i]
                
                # Only include chunks above similarity threshold
                if similarity_score < self.similarity_threshold:
                    filtered_count += 1
                    continue
                
                chunk_text = results['documents'][0][i]
                chunk_tokens = len(chunk_text.split()) * 1.3  # Rough token estimate
                
                # Check if adding this chunk would exceed context limit
                if total_tokens + chunk_tokens > self.max_context_tokens:
                    token_limited_count += 1
                    logger.debug(f"Token limit reached: {total_tokens:.1f} + {chunk_tokens:.1f} > {self.max_context_tokens}")
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
                    logger.debug(f"Max chunks limit reached: {max_chunks}")
                    break
            
            # Sort by relevance score (highest first)
            filtered_docs.sort(key=lambda x: x['score'], reverse=True)
            
            # Enhanced logging
            retrieval_stats = {
                "candidates_searched": len(results['ids'][0]),
                "filtered_by_similarity": filtered_count,
                "filtered_by_tokens": token_limited_count,
                "final_count": len(filtered_docs),
                "total_tokens": int(total_tokens),
                "similarity_threshold": self.similarity_threshold,
                "max_context_tokens": self.max_context_tokens
            }
            
            logger.info(f"Retrieved {len(filtered_docs)} chunks ({total_tokens:.0f} tokens) for query - Stats: {retrieval_stats}")
            
            if len(filtered_docs) == 0:
                logger.warning(f"No documents passed similarity threshold of {self.similarity_threshold}. "
                             f"Consider lowering threshold or checking document quality.")
            
            return filtered_docs
        
        except Exception as e:
            logger.error(f"Error in adaptive retrieval for query '{query[:50]}...': {e}", exc_info=True)
            raise  # Re-raise to trigger retry mechanism
    
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
    
    async def rag_query_async(self, question: str, max_chunks: int = None) -> Dict:
        """Async RAG query with caching and request coalescing."""
        if not question or not question.strip():
            logger.warning("Empty question provided to rag_query")
            return {
                "answer": "Please provide a question to search for.",
                "sources": [],
                "context_used": 0,
                "context_tokens": 0,
                "efficiency_ratio": 0.0,
                "error": "Empty query",
                "cache_hit": False
            }
        
        # Create cache key based on question and parameters
        cache_key = self.rag_cache._generate_key("rag_query", {
            "question": question,
            "max_chunks": max_chunks,
            "similarity_threshold": self.similarity_threshold
        })
        
        # Try to get cached result with request coalescing
        async def compute_rag_result():
            return self._compute_rag_query(question, max_chunks)
        
        start_time = time.time()
        logger.info(f"Starting RAG query: '{question[:100]}...' (max_chunks={max_chunks})")
        
        # Get result with caching and coalescing
        result = await self.rag_cache.get_or_compute(
            key=cache_key,
            compute_func=compute_rag_result,
            ttl=300.0,  # 5 minutes
            use_coalescing=True
        )
        
        # Add cache metadata and record performance metrics
        query_time = time.time() - start_time
        result["query_time"] = round(query_time, 3)
        cache_hit = result.get("cache_hit", True)  # Default to True if from cache
        result["cache_hit"] = cache_hit
        
        # Record performance metrics
        record_rag_query_time(query_time * 1000, cache_hit)  # Convert to milliseconds
        
        # Update cache hit rates
        for cache_name, cache in [("rag", self.rag_cache), ("embedding", self.embedding_cache)]:
            cache_stats = cache.get_stats()
            if cache_stats.get("hit_rate", 0) > 0:
                record_cache_hit_rate(cache_stats["hit_rate"], cache_name)
        
        logger.info(f"RAG query completed in {query_time:.3f}s: "
                   f"cache_hit={cache_hit}")
        
        return result
    
    def _compute_rag_query(self, question: str, max_chunks: int = None) -> Dict:
        """Compute RAG query result (non-cached)."""
        start_time = time.time()
        
        try:
            # Adaptive chunk selection based on query complexity
            if max_chunks is None:
                query_words = len(question.split())
                if query_words < 10:
                    max_chunks = 2  # Simple query
                elif any(word in question.lower() for word in ['compare', 'difference', 'versus', 'analyze']):
                    max_chunks = 5  # Complex comparison query
                else:
                    max_chunks = 3  # Default
                
                logger.debug(f"Auto-selected max_chunks={max_chunks} based on query complexity ({query_words} words)")
            
            # Retrieve with efficiency optimizations
            try:
                docs = self.adaptive_retrieval(question, max_chunks=max_chunks)
            except Exception as e:
                logger.error(f"Document retrieval failed: {e}")
                return {
                    "answer": "I'm sorry, I encountered an error while searching for relevant documents. Please try again.",
                    "sources": [],
                    "context_used": 0,
                    "context_tokens": 0,
                    "efficiency_ratio": 0.0,
                    "error": f"Retrieval error: {str(e)}",
                    "cache_hit": False
                }
            
            # Check if we found any documents
            if not docs:
                logger.warning(f"No relevant documents found for query: '{question[:50]}...'")
                fallback_answer = ("I couldn't find any relevant documents to answer your question. "
                                 "This might be because:\n"
                                 "1. No documents match your query well enough\n"
                                 "2. The similarity threshold is too high\n"
                                 "3. The documents don't contain relevant information")
                
                return {
                    "answer": fallback_answer,
                    "sources": [],
                    "context_used": 0,
                    "context_tokens": 0,
                    "efficiency_ratio": 0.0,
                    "cache_hit": False,
                    "query_stats": {
                        "similarity_threshold": self.similarity_threshold,
                        "total_documents": self.collection.count()
                    }
                }
            
            # Generate answer with error handling
            try:
                answer = self.generate_answer(question, docs)
            except Exception as e:
                logger.error(f"Answer generation failed: {e}")
                # Provide fallback response with retrieved context
                context_preview = " | ".join([doc['content'][:100] + "..." for doc in docs[:2]])
                answer = (f"I found relevant information but encountered an error generating a response. "
                         f"Here's what I found: {context_preview}")
            
            # Calculate efficiency metrics
            total_context_tokens = sum(len(doc['content'].split()) * 1.3 for doc in docs)
            query_time = time.time() - start_time
            
            result = {
                "answer": answer,
                "sources": [{"title": doc["title"], "score": f"{doc['score']:.2f}"} for doc in docs],
                "context_used": len(docs),
                "context_tokens": int(total_context_tokens),
                "efficiency_ratio": len(docs) / max(total_context_tokens, 1) * 1000,  # chunks per 1000 tokens
                "query_time": round(query_time, 3),
                "cache_hit": False
            }
            
            logger.info(f"RAG query computed in {query_time:.3f}s: {len(docs)} docs, {int(total_context_tokens)} tokens")
            return result
            
        except Exception as e:
            query_time = time.time() - start_time
            logger.error(f"RAG query failed after {query_time:.3f}s: {e}", exc_info=True)
            
            return {
                "answer": "I'm sorry, I encountered an unexpected error while processing your question. Please try again.",
                "sources": [],
                "context_used": 0,
                "context_tokens": 0,
                "efficiency_ratio": 0.0,
                "error": f"Pipeline error: {str(e)}",
                "query_time": round(query_time, 3),
                "cache_hit": False
            }
    
    def rag_query(self, question: str, max_chunks: int = None) -> Dict:
        """Synchronous wrapper for RAG query (backwards compatibility)."""
        import asyncio
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run async query
        if loop.is_running():
            # If loop is already running, use run_in_executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(self.rag_query_async(question, max_chunks))
                )
                return future.result()
        else:
            return loop.run_until_complete(self.rag_query_async(question, max_chunks))
    
    def get_system_diagnostics(self) -> Dict:
        """Get comprehensive system diagnostics including performance metrics."""
        try:
            doc_count = self.collection.count()
            sample_docs = self.collection.get(limit=3, include=['metadatas', 'documents'])
            
            # Get performance metrics
            cache_stats = {
                "rag_cache": self.rag_cache.get_stats(),
                "embedding_cache": self.embedding_cache.get_stats(),
                "document_cache": self.document_cache.get_stats()
            }
            
            pool_stats = self.pool_manager.get_all_stats()
            
            # Get monitoring dashboard data
            dashboard_data = self.performance_monitor.get_dashboard_data(duration_seconds=300)
            
            return {
                "status": "healthy",
                "document_count": doc_count,
                "embedding_model": str(self.encoder),
                "rag_settings": {
                    "similarity_threshold": self.similarity_threshold,
                    "max_context_tokens": self.max_context_tokens,
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap
                },
                "llm_connection": self.llm_client.get_connection_info(),
                "performance_metrics": {
                    "cache_stats": cache_stats,
                    "connection_pool_stats": pool_stats,
                    "monitoring_dashboard": dashboard_data,
                    "total_cache_hit_rate": sum(
                        stats.get("hit_rate", 0) for stats in cache_stats.values()
                    ) / len(cache_stats) if cache_stats else 0,
                    "performance_report": self.performance_monitor.get_performance_report()
                },
                "sample_documents": [
                    {
                        "id": sample_docs.get('ids', [])[i] if i < len(sample_docs.get('ids', [])) else None,
                        "title": sample_docs.get('metadatas', [])[i].get('title', 'Unknown') if i < len(sample_docs.get('metadatas', [])) else None,
                        "content_preview": sample_docs.get('documents', [])[i][:100] + "..." if i < len(sample_docs.get('documents', [])) else None
                    }
                    for i in range(min(3, len(sample_docs.get('ids', []))))
                ],
                "chroma_config": {
                    "path": self.data_path,
                    "collection_name": self.collection.name if hasattr(self.collection, 'name') else 'documents'
                }
            }
        except Exception as e:
            logger.error(f"Error getting system diagnostics: {e}")
            return {
                "status": "error",
                "error": str(e),
                "llm_connection": self.llm_client.get_connection_info() if hasattr(self, 'llm_client') else None
            }

# Global instance - initialized lazily
rag_system = None

def get_rag_system():
    """Get or create the global RAG system instance"""
    global rag_system
    if rag_system is None:
        rag_system = LocalRAGSystem()
    return rag_system