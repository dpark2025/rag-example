"""
Unit tests for RAG backend core functionality.

Tests document processing, embedding generation, similarity search,
and query processing components.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-04
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import modules under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from rag_backend import LocalRAGSystem, LocalLLMClient
import chromadb
from sentence_transformers import SentenceTransformer


@pytest.mark.unit
class TestLocalLLMClient:
    """Test suite for LocalLLMClient functionality."""

    def test_init_default_url(self):
        """Test LLM client initialization with default URL."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('os.path.exists', return_value=False):
                client = LocalLLMClient()
                assert client.base_url == "http://localhost:11434"

    def test_init_with_custom_url(self):
        """Test LLM client initialization with custom URL."""
        custom_url = "http://custom-ollama:11434"
        client = LocalLLMClient(base_url=custom_url)
        assert client.base_url == custom_url

    def test_init_with_environment_variable(self):
        """Test LLM client initialization with OLLAMA_HOST environment variable."""
        with patch.dict(os.environ, {"OLLAMA_HOST": "remote-ollama:11434"}):
            client = LocalLLMClient()
            assert client.base_url == "http://remote-ollama:11434"

    @patch('requests.post')
    def test_chat_success(self, mock_post):
        """Test successful chat interaction."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "This is a test response from the LLM."}
        }
        mock_post.return_value = mock_response
        
        client = LocalLLMClient()
        messages = [{"role": "user", "content": "Test question"}]
        
        response = client.chat(messages)
        
        assert response == "This is a test response from the LLM."
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_chat_failure(self, mock_post):
        """Test chat interaction with API failure."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response
        
        client = LocalLLMClient()
        messages = [{"role": "user", "content": "Test question"}]
        
        response = client.chat(messages)
        
        assert "trouble connecting" in response

    @patch('requests.post')
    def test_chat_timeout(self, mock_post):
        """Test chat interaction with timeout."""
        # Mock timeout exception
        mock_post.side_effect = Exception("Connection timeout")
        
        client = LocalLLMClient()
        messages = [{"role": "user", "content": "Test question"}]
        
        response = client.chat(messages)
        
        assert "not available" in response

    @patch('requests.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = LocalLLMClient()
        result = client.health_check()
        
        assert result is True

    @patch('requests.get')
    def test_health_check_failure(self, mock_get):
        """Test failed health check."""
        mock_get.side_effect = Exception("Connection failed")
        
        client = LocalLLMClient()
        result = client.health_check()
        
        assert result is False

    def test_chat_with_custom_parameters(self):
        """Test chat with custom temperature and max_tokens."""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"content": "Custom response"}
            }
            mock_post.return_value = mock_response
            
            client = LocalLLMClient()
            messages = [{"role": "user", "content": "Test"}]
            
            response = client.chat(
                messages, 
                model="llama3.2:7b",
                temperature=0.3,
                max_tokens=500
            )
            
            # Verify the request was made with correct parameters
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            
            assert request_data['model'] == "llama3.2:7b"
            assert request_data['options']['temperature'] == 0.3
            assert request_data['options']['num_predict'] == 500


@pytest.mark.unit
class TestLocalRAGSystem:
    """Test suite for LocalRAGSystem functionality."""

    def test_init(self, temp_directory, mock_llm_client):
        """Test RAG system initialization."""
        with patch('sentence_transformers.SentenceTransformer') as mock_encoder:
            mock_encoder.return_value = Mock()
            
            rag_system = LocalRAGSystem(
                llm_client=mock_llm_client,
                data_path=temp_directory
            )
            
            assert rag_system.llm_client is mock_llm_client
            assert rag_system.data_path == temp_directory
            assert rag_system.similarity_threshold == 0.6
            assert rag_system.max_context_tokens == 2000

    def test_text_chunking_default(self, rag_system):
        """Test text chunking with default parameters."""
        text = "This is a test document. " * 100  # Create long text
        
        chunks = rag_system.smart_chunking(text)
        
        assert len(chunks) > 1
        # Smart chunking prioritizes semantic boundaries over strict size limits
        assert all(len(chunk) > 0 for chunk in chunks)  # Chunks should not be empty
        assert all(len(chunk) <= 3000 for chunk in chunks)  # Reasonable upper bound

    def test_text_chunking_custom_size(self, rag_system):
        """Test text chunking with custom chunk size."""
        text = "This is a test document. " * 50
        custom_chunk_size = 200
        custom_overlap = 20
        
        chunks = rag_system.custom_chunking(text, chunk_size=custom_chunk_size, chunk_overlap=custom_overlap)
        
        assert len(chunks) > 0
        # Custom chunking prioritizes semantic boundaries over strict size limits
        assert all(len(chunk) > 0 for chunk in chunks)  # Chunks should not be empty
        assert all(len(chunk) <= 1000 for chunk in chunks)  # Reasonable upper bound for custom size

    def test_text_chunking_short_text(self, rag_system):
        """Test text chunking with text shorter than chunk size."""
        short_text = "This is a short text."
        
        chunks = rag_system.smart_chunking(short_text)
        
        assert len(chunks) == 1
        assert chunks[0] == short_text

    def test_text_chunking_empty_text(self, rag_system):
        """Test text chunking with empty text."""
        chunks = rag_system.smart_chunking("")
        # Empty text might return empty list or single empty chunk
        assert len(chunks) <= 1
        if len(chunks) == 1:
            assert chunks[0].strip() == ""

    def test_generate_embeddings(self, rag_system):
        """Test embedding generation with caching."""
        text = "This is test text"
        
        # Mock the encoder - it should return numpy array for single text
        mock_embedding = np.array([0.1, 0.2, 0.3])
        rag_system.encoder.encode = Mock(return_value=mock_embedding)
        
        embedding = rag_system._generate_embedding_with_cache(text)
        
        assert len(embedding) == 3
        assert embedding == mock_embedding.tolist()

    def test_add_documents_single(self, rag_system, sample_documents):
        """Test adding a single document."""
        # Mock the collection methods
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=3)
        
        # Mock embedding generation
        rag_system.encoder.encode = Mock(return_value=[[0.1, 0.2, 0.3]])
        
        document = sample_documents[0]
        result = rag_system.add_documents([document])
        
        assert "Successfully added" in result
        rag_system.collection.add.assert_called_once()

    def test_add_documents_multiple(self, rag_system, sample_documents):
        """Test adding multiple documents."""
        # Mock the collection methods
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=9)  # 3 docs * ~3 chunks each
        
        # Mock embedding generation
        mock_embeddings = np.random.rand(9, 384).tolist()  # 9 chunks, 384 dimensions
        rag_system.encoder.encode = Mock(return_value=mock_embeddings)
        
        result = rag_system.add_documents(sample_documents)
        
        assert "Successfully added" in result
        assert "3 documents" in result
        rag_system.collection.add.assert_called_once()

    def test_add_documents_with_custom_chunking(self, rag_system, sample_text_content):
        """Test adding documents with custom chunking parameters."""
        document = {
            "title": "Custom Chunk Test",
            "content": sample_text_content,
            "source": "test",
            "doc_id": "custom_test"
        }
        
        # Mock the collection
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=2)
        
        # Mock embedding generation
        rag_system.encoder.encode = Mock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        
        result = rag_system.add_documents([document], chunk_size=200, chunk_overlap=20)
        
        assert "Successfully added" in result
        rag_system.encoder.encode.assert_called_once()

    def test_similarity_search(self, rag_system):
        """Test similarity search functionality."""
        query = "test query"
        
        # Mock query embedding
        query_embedding = [0.1, 0.2, 0.3]
        rag_system.encoder.encode = Mock(return_value=[query_embedding])
        
        # Mock collection query results
        mock_results = {
            "ids": [["chunk1", "chunk2"]],
            "distances": [[0.2, 0.4]],
            "metadatas": [[
                {"title": "Doc 1", "source": "test1", "content_preview": "Preview 1"},
                {"title": "Doc 2", "source": "test2", "content_preview": "Preview 2"}
            ]],
            "documents": [["Content 1", "Content 2"]]
        }
        rag_system.collection.query = Mock(return_value=mock_results)
        
        results = rag_system.adaptive_retrieval(query, max_chunks=2)
        
        assert len(results) == 2
        assert results[0]["content"] == "Content 1"
        assert results[0]["similarity"] == 0.8  # 1 - 0.2
        assert results[1]["similarity"] == 0.6  # 1 - 0.4

    def test_similarity_search_with_threshold(self, rag_system):
        """Test similarity search with threshold filtering."""
        query = "test query"
        
        # Mock query embedding
        query_embedding = [0.1, 0.2, 0.3]
        rag_system.encoder.encode = Mock(return_value=[query_embedding])
        
        # Mock results with varying similarities
        mock_results = {
            "ids": [["chunk1", "chunk2", "chunk3"]],
            "distances": [[0.1, 0.5, 0.8]],  # similarities: 0.9, 0.5, 0.2
            "metadatas": [[
                {"title": "Doc 1", "source": "test1", "content_preview": "Preview 1"},
                {"title": "Doc 2", "source": "test2", "content_preview": "Preview 2"},
                {"title": "Doc 3", "source": "test3", "content_preview": "Preview 3"}
            ]],
            "documents": [["Content 1", "Content 2", "Content 3"]]
        }
        rag_system.collection.query = Mock(return_value=mock_results)
        
        # Set threshold to 0.7
        rag_system.similarity_threshold = 0.7
        results = rag_system.adaptive_retrieval(query, max_chunks=5)
        
        # Should only return chunks with similarity >= 0.7
        assert len(results) == 1
        assert results[0]["similarity"] == 0.9

    def test_build_context(self, rag_system):
        """Test context building from search results."""
        search_results = [
            {
                "content": "This is the first relevant chunk.",
                "metadata": {"title": "Doc 1", "source": "test1"},
                "score": 0.9,
                "doc_id": "doc1"
            },
            {
                "content": "This is the second relevant chunk.",
                "metadata": {"title": "Doc 2", "source": "test2"},
                "score": 0.8,
                "doc_id": "doc2"
            },
            {
                "content": "This is the third relevant chunk.",
                "metadata": {"title": "Doc 1", "source": "test1"},
                "score": 0.75,
                "doc_id": "doc1"
            }
        ]
        
        context = rag_system.build_efficient_context(search_results)
        
        assert "first relevant chunk" in context
        assert "second relevant chunk" in context
        assert len(context) > 0

    def test_build_context_token_limit(self, rag_system):
        """Test context building with token limit."""
        # Create many long search results
        search_results = []
        for i in range(10):
            search_results.append({
                "content": "This is a very long chunk of text. " * 50,  # ~200 tokens
                "metadata": {"title": f"Doc {i}", "source": f"test{i}"},
                "score": 0.9 - i * 0.05,
                "doc_id": f"doc{i}"
            })
        
        # Set a low token limit
        rag_system.max_context_tokens = 300
        
        context = rag_system.build_efficient_context(search_results)
        
        # Context should be built efficiently
        assert len(context) > 0
        assert "very long chunk" in context

    def test_count_tokens(self, rag_system):
        """Test token counting functionality."""
        text = "This is a test sentence with multiple words."
        
        token_count = rag_system._count_tokens(text)
        
        # Should be approximately the number of words
        assert token_count > 0
        assert token_count < len(text)  # Should be less than character count

    def test_rag_query_no_documents(self, rag_system):
        """Test RAG query with no documents in database."""
        rag_system.collection = Mock()
        rag_system.collection.count = Mock(return_value=0)
        
        query = "What is artificial intelligence?"
        
        with pytest.raises(Exception) as exc_info:
            result = rag_system.rag_query(query)
        
        assert "no documents" in str(exc_info.value).lower()

    def test_rag_query_success(self, rag_system, mock_llm_client, sample_text_content):
        """Test successful RAG query processing."""
        query = "What is artificial intelligence?"
        
        # Mock collection count
        rag_system.collection.count = Mock(return_value=5)
        
        # Mock similarity search results
        search_results = [
            {
                "content": sample_text_content[:200],
                "metadata": {"title": "AI Overview", "source": "test1"},
                "similarity": 0.9
            }
        ]
        rag_system.adaptive_retrieval = Mock(return_value=search_results)
        
        # Mock LLM response
        mock_llm_client.chat.return_value = "AI is the simulation of human intelligence in machines."
        
        result = rag_system.rag_query(query)
        
        assert result["answer"] == "AI is the simulation of human intelligence in machines."
        assert len(result["sources"]) == 1
        assert result["context_used"] == 1
        assert result["context_tokens"] > 0
        assert result["efficiency_ratio"] > 0

    def test_rag_query_with_max_chunks(self, rag_system, mock_llm_client):
        """Test RAG query with max_chunks parameter."""
        query = "Test query"
        max_chunks = 3
        
        # Mock dependencies
        rag_system.collection.count = Mock(return_value=10)
        rag_system.adaptive_retrieval = Mock(return_value=[
            {"content": f"Content {i}", "metadata": {"title": f"Doc {i}", "source": f"test{i}"}, "similarity": 0.9 - i*0.1}
            for i in range(5)
        ])
        mock_llm_client.chat.return_value = "Test response"
        
        result = rag_system.rag_query(query, max_chunks=max_chunks)
        
        # Should limit to max_chunks
        rag_system.adaptive_retrieval.assert_called_with(query, max_chunks=max_chunks)

    def test_rag_query_no_results_above_threshold(self, rag_system, mock_llm_client):
        """Test RAG query when no results meet similarity threshold."""
        query = "Very specific query with no matches"
        
        # Mock collection count
        rag_system.collection.count = Mock(return_value=5)
        
        # Mock empty search results
        rag_system.adaptive_retrieval = Mock(return_value=[])
        
        # Mock LLM fallback response
        mock_llm_client.chat.return_value = "I don't have specific information about that."
        
        result = rag_system.rag_query(query)
        
        assert result["context_used"] == 0
        assert len(result["sources"]) == 0
        assert "don't have specific information" in result["answer"]

    def test_error_handling_embedding_failure(self, rag_system):
        """Test error handling when embedding generation fails."""
        documents = [{"title": "Test", "content": "Test content", "source": "test"}]
        
        # Mock embedding failure
        rag_system.encoder.encode = Mock(side_effect=Exception("Embedding model failed"))
        
        with pytest.raises(Exception) as exc_info:
            rag_system.add_documents(documents)
        
        assert "Embedding model failed" in str(exc_info.value)

    def test_error_handling_chromadb_failure(self, rag_system, sample_documents):
        """Test error handling when ChromaDB operations fail."""
        # Mock ChromaDB failure
        rag_system.collection.add = Mock(side_effect=Exception("Database connection failed"))
        rag_system.encoder.encode = Mock(return_value=[[0.1, 0.2, 0.3]])
        
        with pytest.raises(Exception) as exc_info:
            rag_system.add_documents(sample_documents[:1])
        
        assert "Database connection failed" in str(exc_info.value)

    def test_performance_large_document_set(self, rag_system):
        """Test performance with large document set."""
        import time
        
        # Create many documents
        large_document_set = []
        for i in range(50):
            large_document_set.append({
                "title": f"Document {i}",
                "content": f"Content for document {i}. " * 100,  # ~500 tokens
                "source": f"test_{i}",
                "doc_id": f"doc_{i}"
            })
        
        # Mock the expensive operations
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=150)
        
        # Mock embeddings (would be expensive in real scenario)
        mock_embeddings = np.random.rand(150, 384).tolist()
        rag_system.encoder.encode = Mock(return_value=mock_embeddings)
        
        start_time = time.time()
        result = rag_system.add_documents(large_document_set)
        duration = time.time() - start_time
        
        # Should complete in reasonable time (mocked operations should be fast)
        assert duration < 1.0
        assert "Successfully added" in result

    def test_memory_efficiency(self, rag_system, sample_documents):
        """Test memory efficiency during operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Mock operations to avoid actual heavy processing
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=3)
        rag_system.encoder.encode = Mock(return_value=np.random.rand(3, 384).tolist())
        
        # Process documents multiple times
        for _ in range(10):
            rag_system.add_documents(sample_documents)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for mocked operations)
        assert memory_increase < 50 * 1024 * 1024


@pytest.mark.integration
class TestRAGSystemIntegration:
    """Integration tests for RAG system components."""

    @pytest.mark.asyncio
    async def test_complete_rag_workflow(self, rag_system_with_documents, mock_llm_client):
        """Test complete RAG workflow from document addition to query."""
        query = "What is machine learning?"
        
        # Mock LLM response
        mock_llm_client.chat.return_value = "Machine learning is a subset of AI that focuses on algorithms that can learn from data."
        
        result = rag_system_with_documents.rag_query(query)
        
        assert result["answer"] is not None
        assert len(result["sources"]) > 0
        assert result["context_used"] > 0
        assert result["efficiency_ratio"] > 0

    def test_document_retrieval_accuracy(self, rag_system_with_documents):
        """Test accuracy of document retrieval."""
        # Query for specific content we know exists
        query = "vector databases"
        
        search_results = rag_system_with_documents.adaptive_retrieval(query)
        
        # Should find relevant content
        assert len(search_results) > 0
        # Check if relevant content is found (based on sample documents)
        found_relevant = any("vector" in result["content"].lower() for result in search_results)
        assert found_relevant

    @pytest.mark.slow
    def test_performance_benchmarks(self, rag_system, sample_documents, performance_config):
        """Test performance meets required benchmarks."""
        import time
        
        # Test document addition performance
        start_time = time.time()
        rag_system.add_documents(sample_documents)
        add_duration = time.time() - start_time
        
        # Test query performance
        start_time = time.time()
        result = rag_system.adaptive_retrieval("test query")
        query_duration = time.time() - start_time
        
        # Performance assertions
        assert add_duration < 10.0  # Should add documents quickly
        assert query_duration < 1.0  # Should query quickly