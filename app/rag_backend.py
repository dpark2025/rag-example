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
        logger.info(f"Initializing LLM client with URL: {base_url}")
    
    def chat(self, messages, model="llama3.2:3b", temperature=0.7, max_tokens=1000):
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
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
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
            "efficiency_ratio": len(docs) / max(total_context_tokens, 1) * 1000  # chunks per 1000 tokens
        }

# Global instance - initialized lazily
rag_system = None

def get_rag_system():
    """Get or create the global RAG system instance"""
    global rag_system
    if rag_system is None:
        rag_system = LocalRAGSystem()
    return rag_system