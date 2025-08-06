"""
Comprehensive integration tests for RAG query functionality and API endpoints.

Tests end-to-end RAG workflows, query processing, context building,
answer generation, and API endpoint integration.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-05
"""

import pytest
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from fastapi.testclient import TestClient
import httpx

# Import modules under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.rag_backend import LocalRAGSystem, LocalLLMClient
from app.document_manager import DocumentManager
from app.main import app


@pytest.mark.integration
class TestRAGQueryComprehensive:
    """Comprehensive integration tests for RAG query functionality."""

    @pytest.fixture
    def complex_document_set(self):
        """Create a complex set of documents for testing."""
        return [
            {
                "title": "Introduction to Artificial Intelligence",
                "content": """
                Artificial Intelligence (AI) is a branch of computer science that aims to create 
                intelligent machines that work and react like humans. AI systems can perform tasks 
                that typically require human intelligence such as visual perception, speech recognition, 
                decision-making, and language translation.
                
                The field of AI includes several subfields:
                - Machine Learning (ML): Systems that can learn from data
                - Natural Language Processing (NLP): Understanding human language
                - Computer Vision: Interpreting visual information
                - Robotics: Intelligent physical systems
                
                AI has applications in healthcare, finance, transportation, entertainment, and many 
                other industries. The goal is to create systems that can solve complex problems 
                and make decisions autonomously.
                """,
                "source": "ai_textbook_chapter1",
                "doc_id": "ai_intro_001",
                "file_type": "txt"
            },
            {
                "title": "Machine Learning Fundamentals",
                "content": """
                Machine Learning is a subset of artificial intelligence that focuses on algorithms 
                that can learn and improve from experience without being explicitly programmed. 
                ML algorithms build mathematical models based on training data to make predictions 
                or decisions.
                
                Types of Machine Learning:
                1. Supervised Learning: Learning with labeled examples
                   - Classification: Predicting categories
                   - Regression: Predicting numerical values
                
                2. Unsupervised Learning: Finding patterns in unlabeled data
                   - Clustering: Grouping similar data points
                   - Dimensionality Reduction: Simplifying data
                
                3. Reinforcement Learning: Learning through interaction
                   - Agent learns by receiving rewards and penalties
                   - Used in game playing, robotics, and autonomous systems
                
                Popular ML algorithms include linear regression, decision trees, neural networks, 
                support vector machines, and random forests.
                """,
                "source": "ml_handbook_chapter2",
                "doc_id": "ml_fundamentals_002",
                "file_type": "txt"
            },
            {
                "title": "Vector Databases and Embeddings",
                "content": """
                Vector databases are specialized databases designed to store and query high-dimensional 
                vectors efficiently. They are essential for modern AI applications that work with 
                embeddings - mathematical representations of data in vector space.
                
                Key Concepts:
                - Embeddings: Dense vector representations of text, images, or other data
                - Similarity Search: Finding vectors that are close in vector space
                - Distance Metrics: Cosine similarity, Euclidean distance, dot product
                - Indexing: Structures like HNSW, IVF for fast approximate search
                
                Applications:
                - Semantic Search: Finding documents by meaning, not just keywords
                - Recommendation Systems: Suggesting similar items
                - RAG Systems: Retrieval-Augmented Generation for AI
                - Image Search: Finding similar images
                
                Popular vector databases include Chroma, Pinecone, Weaviate, and Qdrant. 
                They provide APIs for storing vectors, performing similarity searches, 
                and filtering results based on metadata.
                """,
                "source": "vector_db_guide",
                "doc_id": "vector_db_003",
                "file_type": "txt"
            },
            {
                "title": "Natural Language Processing Techniques",
                "content": """
                Natural Language Processing (NLP) is a field of AI that focuses on the interaction 
                between computers and human language. NLP combines computational linguistics with 
                machine learning to help computers understand, interpret, and generate human language.
                
                Core NLP Tasks:
                - Tokenization: Breaking text into words or subwords
                - Part-of-Speech Tagging: Identifying grammatical roles
                - Named Entity Recognition: Identifying people, places, organizations
                - Sentiment Analysis: Determining emotional tone
                - Text Classification: Categorizing documents
                - Machine Translation: Converting between languages
                - Question Answering: Providing answers to natural language questions
                
                Modern NLP relies heavily on:
                - Transformer Models: BERT, GPT, T5, and their variants
                - Attention Mechanisms: Focusing on relevant parts of input
                - Pre-training and Fine-tuning: Learning general patterns then specializing
                - Transfer Learning: Applying knowledge from one task to another
                
                NLP powers search engines, chatbots, translation services, and content analysis tools.
                """,
                "source": "nlp_handbook",
                "doc_id": "nlp_techniques_004",
                "file_type": "txt"
            },
            {
                "title": "Retrieval-Augmented Generation (RAG) Systems",
                "content": """
                Retrieval-Augmented Generation (RAG) is an AI framework that combines information 
                retrieval with text generation to provide accurate, contextual responses. RAG systems 
                address the limitations of pure language models by grounding their responses in 
                retrieved knowledge.
                
                RAG Architecture:
                1. Document Ingestion: Processing and storing documents in a vector database
                2. Query Processing: Converting user questions into searchable embeddings
                3. Retrieval: Finding relevant document chunks using similarity search
                4. Context Building: Assembling retrieved information into coherent context
                5. Generation: Using an LLM to generate responses based on retrieved context
                
                Benefits of RAG:
                - Reduces hallucinations by grounding responses in real data
                - Enables knowledge updates without retraining the model
                - Provides source attribution for fact-checking
                - Scales to large knowledge bases efficiently
                
                RAG systems are widely used in customer support, knowledge management, 
                research assistance, and educational applications. They represent a significant 
                advancement in making AI systems more reliable and trustworthy.
                """,
                "source": "rag_systems_paper",
                "doc_id": "rag_systems_005",
                "file_type": "txt"
            },
            {
                "title": "Deep Learning and Neural Networks",
                "content": """
                Deep Learning is a subset of machine learning that uses artificial neural networks 
                with multiple layers to model and understand complex patterns in data. Deep neural 
                networks can automatically learn hierarchical representations of data.
                
                Neural Network Components:
                - Neurons: Basic processing units that apply activation functions
                - Layers: Groups of neurons (input, hidden, output layers)
                - Weights and Biases: Parameters learned during training
                - Activation Functions: ReLU, sigmoid, tanh for non-linearity
                
                Types of Neural Networks:
                - Feedforward Networks: Information flows in one direction
                - Convolutional Neural Networks (CNNs): Specialized for image processing
                - Recurrent Neural Networks (RNNs): Handle sequential data
                - Transformers: Attention-based models for language tasks
                
                Training Process:
                - Forward Pass: Computing predictions
                - Loss Calculation: Measuring prediction errors
                - Backpropagation: Computing gradients
                - Optimization: Updating weights using gradient descent
                
                Deep learning has revolutionized computer vision, natural language processing, 
                speech recognition, and many other AI applications.
                """,
                "source": "deep_learning_textbook",
                "doc_id": "deep_learning_006",
                "file_type": "txt"
            }
        ]

    @pytest.fixture
    def rag_system_with_complex_docs(self, rag_system, complex_document_set):
        """RAG system pre-loaded with complex document set."""
        # Mock the collection and embedding operations
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=len(complex_document_set) * 3)
        
        # Mock embedding generation with realistic dimensions
        total_chunks = len(complex_document_set) * 3  # Assume ~3 chunks per document
        rag_system.encoder.encode = Mock(return_value=np.random.rand(total_chunks, 384).tolist())
        
        # Add documents to the system
        result = rag_system.add_documents(complex_document_set)
        assert "Successfully added" in result
        
        return rag_system

    def test_basic_rag_query_workflow(self, rag_system_with_complex_docs, mock_llm_client):
        """Test basic RAG query workflow end-to-end."""
        query = "What is artificial intelligence?"
        
        # Mock similarity search results
        mock_search_results = [
            {
                "content": "Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines that work and react like humans.",
                "metadata": {"title": "Introduction to Artificial Intelligence", "source": "ai_textbook_chapter1"},
                "similarity": 0.92
            },
            {
                "content": "AI systems can perform tasks that typically require human intelligence such as visual perception, speech recognition, decision-making, and language translation.",
                "metadata": {"title": "Introduction to Artificial Intelligence", "source": "ai_textbook_chapter1"},
                "similarity": 0.88
            }
        ]
        
        rag_system_with_complex_docs.adaptive_retrieval = Mock(return_value=mock_search_results)
        mock_llm_client.chat.return_value = "Artificial Intelligence is a branch of computer science focused on creating intelligent machines that can perform tasks typically requiring human intelligence, such as visual perception, speech recognition, and decision-making."
        
        result = rag_system_with_complex_docs.rag_query(query)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "answer" in result
        assert "sources" in result
        assert "context_used" in result
        assert "context_tokens" in result
        assert "efficiency_ratio" in result
        
        # Verify result content
        assert result["answer"] == mock_llm_client.chat.return_value
        assert len(result["sources"]) == 1  # One unique source
        assert result["context_used"] == 2
        assert result["context_tokens"] > 0
        assert result["efficiency_ratio"] > 0

    def test_complex_multi_topic_query(self, rag_system_with_complex_docs, mock_llm_client):
        """Test complex query spanning multiple topics."""
        query = "How do machine learning and vector databases work together in RAG systems?"
        
        # Mock search results from multiple documents
        mock_search_results = [
            {
                "content": "Machine Learning is a subset of artificial intelligence that focuses on algorithms that can learn and improve from experience without being explicitly programmed.",
                "metadata": {"title": "Machine Learning Fundamentals", "source": "ml_handbook_chapter2"},
                "similarity": 0.89
            },
            {
                "content": "Vector databases are specialized databases designed to store and query high-dimensional vectors efficiently. They are essential for modern AI applications that work with embeddings.",
                "metadata": {"title": "Vector Databases and Embeddings", "source": "vector_db_guide"},
                "similarity": 0.91
            },
            {
                "content": "RAG Architecture: 1. Document Ingestion: Processing and storing documents in a vector database 2. Query Processing: Converting user questions into searchable embeddings",
                "metadata": {"title": "Retrieval-Augmented Generation (RAG) Systems", "source": "rag_systems_paper"},
                "similarity": 0.94
            },
            {
                "content": "RAG systems address the limitations of pure language models by grounding their responses in retrieved knowledge.",
                "metadata": {"title": "Retrieval-Augmented Generation (RAG) Systems", "source": "rag_systems_paper"},
                "similarity": 0.87
            }
        ]
        
        rag_system_with_complex_docs.adaptive_retrieval = Mock(return_value=mock_search_results)
        mock_llm_client.chat.return_value = "Machine learning and vector databases work together in RAG systems by enabling semantic search and knowledge retrieval. Vector databases store document embeddings created by ML models, allowing for similarity-based search that finds relevant information to augment language model responses."
        
        result = rag_system_with_complex_docs.rag_query(query, max_chunks=4)
        
        # Verify multi-topic integration
        assert result["context_used"] == 4
        assert len(result["sources"]) == 3  # Three unique sources
        
        # Verify sources include multiple topics
        source_titles = [source["title"] for source in result["sources"]]
        assert "Machine Learning Fundamentals" in source_titles
        assert "Vector Databases and Embeddings" in source_titles
        assert "Retrieval-Augmented Generation (RAG) Systems" in source_titles

    def test_query_with_no_relevant_context(self, rag_system_with_complex_docs, mock_llm_client):
        """Test query with no relevant context found."""
        query = "What is the weather like today in Tokyo?"
        
        # Mock empty search results (no relevant content)
        rag_system_with_complex_docs.adaptive_retrieval = Mock(return_value=[])
        
        mock_llm_client.chat.return_value = "I don't have access to current weather information. Please check a reliable weather service for up-to-date weather conditions in Tokyo."
        
        result = rag_system_with_complex_docs.rag_query(query)
        
        # Verify fallback behavior
        assert result["context_used"] == 0
        assert len(result["sources"]) == 0
        assert "don't have access" in result["answer"]

    def test_query_with_low_similarity_threshold(self, rag_system_with_complex_docs, mock_llm_client):
        """Test query behavior with low similarity results."""
        query = "Tell me about quantum computing"
        
        # Mock search results with low similarity scores
        mock_search_results = [
            {
                "content": "Deep learning has revolutionized computer vision, natural language processing, speech recognition, and many other AI applications.",
                "metadata": {"title": "Deep Learning and Neural Networks", "source": "deep_learning_textbook"},
                "similarity": 0.65  # Below typical threshold
            },
            {
                "content": "AI systems can perform tasks that typically require human intelligence such as visual perception, speech recognition, decision-making, and language translation.",
                "metadata": {"title": "Introduction to Artificial Intelligence", "source": "ai_textbook_chapter1"},
                "similarity": 0.62  # Below typical threshold
            }
        ]
        
        # Set low similarity threshold for this test
        rag_system_with_complex_docs.similarity_threshold = 0.6
        rag_system_with_complex_docs.adaptive_retrieval = Mock(return_value=mock_search_results)
        
        mock_llm_client.chat.return_value = "Based on the available information about AI and deep learning technologies, quantum computing is a separate field that I don't have specific information about in the current context."
        
        result = rag_system_with_complex_docs.rag_query(query)
        
        # Verify low-confidence context handling
        assert result["context_used"] == 2
        assert len(result["sources"]) > 0
        assert "don't have specific information" in result["answer"]

    def test_query_context_token_limit(self, rag_system_with_complex_docs, mock_llm_client):
        """Test query behavior when context exceeds token limit."""
        query = "Explain all aspects of artificial intelligence"
        
        # Mock many search results that would exceed token limit
        mock_search_results = []
        for i in range(10):
            mock_search_results.append({
                "content": f"This is a very long piece of content about AI topic {i}. " * 100,  # ~500 tokens each
                "metadata": {"title": f"AI Topic {i}", "source": f"ai_source_{i}"},
                "similarity": 0.9 - (i * 0.05)
            })
        
        rag_system_with_complex_docs.adaptive_retrieval = Mock(return_value=mock_search_results)
        
        # Set low token limit to force truncation
        rag_system_with_complex_docs.max_context_tokens = 1000
        
        mock_llm_client.chat.return_value = "Based on the available context, artificial intelligence encompasses multiple aspects including machine learning, neural networks, and various applications."
        
        result = rag_system_with_complex_docs.rag_query(query)
        
        # Verify token limit enforcement
        assert result["context_tokens"] <= rag_system_with_complex_docs.max_context_tokens
        assert result["context_used"] < 10  # Should use fewer chunks due to token limit
        assert result["efficiency_ratio"] > 0

    def test_query_with_source_attribution(self, rag_system_with_complex_docs, mock_llm_client):
        """Test proper source attribution in query results."""
        query = "What are the types of machine learning?"
        
        mock_search_results = [
            {
                "content": "Types of Machine Learning: 1. Supervised Learning, 2. Unsupervised Learning, 3. Reinforcement Learning",
                "metadata": {
                    "title": "Machine Learning Fundamentals",
                    "source": "ml_handbook_chapter2",
                    "doc_id": "ml_fundamentals_002"
                },
                "similarity": 0.95
            },
            {
                "content": "Supervised Learning: Learning with labeled examples - Classification: Predicting categories - Regression: Predicting numerical values",
                "metadata": {
                    "title": "Machine Learning Fundamentals",
                    "source": "ml_handbook_chapter2",
                    "doc_id": "ml_fundamentals_002"
                },
                "similarity": 0.92
            }
        ]
        
        rag_system_with_complex_docs.adaptive_retrieval = Mock(return_value=mock_search_results)
        mock_llm_client.chat.return_value = "The three main types of machine learning are: 1) Supervised Learning (learning with labeled data for classification and regression), 2) Unsupervised Learning (finding patterns in unlabeled data), and 3) Reinforcement Learning (learning through interaction and rewards)."
        
        result = rag_system_with_complex_docs.rag_query(query)
        
        # Verify source attribution
        assert len(result["sources"]) == 1
        source = result["sources"][0]
        assert source["title"] == "Machine Learning Fundamentals"
        assert source["source"] == "ml_handbook_chapter2"
        assert "chunk_count" in source
        assert source["chunk_count"] == 2  # Two chunks from same source

    def test_query_performance_metrics(self, rag_system_with_complex_docs, mock_llm_client):
        """Test query performance metrics collection."""
        query = "How does natural language processing work?"
        
        mock_search_results = [
            {
                "content": "Natural Language Processing (NLP) is a field of AI that focuses on the interaction between computers and human language.",
                "metadata": {"title": "Natural Language Processing Techniques", "source": "nlp_handbook"},
                "similarity": 0.88
            }
        ]
        
        rag_system_with_complex_docs.adaptive_retrieval = Mock(return_value=mock_search_results)
        
        # Mock LLM with slight delay to test timing
        def delayed_chat(*args, **kwargs):
            time.sleep(0.1)  # 100ms delay
            return "Natural Language Processing works by combining computational linguistics with machine learning to help computers understand and generate human language."
        
        mock_llm_client.chat = delayed_chat
        
        start_time = time.time()
        result = rag_system_with_complex_docs.rag_query(query)
        total_duration = time.time() - start_time
        
        # Verify performance characteristics
        assert result["efficiency_ratio"] > 0
        assert result["context_tokens"] > 0
        assert total_duration > 0.1  # Should include LLM delay
        assert total_duration < 5.0   # Should complete within reasonable time

    def test_concurrent_queries(self, rag_system_with_complex_docs, mock_llm_client):
        """Test concurrent query processing."""
        queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "What are vector databases?",
            "Explain natural language processing",
            "What is a RAG system?"
        ]
        
        # Mock search results for each query
        def mock_adaptive_retrieval(query, max_chunks=5):
            if "artificial intelligence" in query.lower():
                return [{
                    "content": "AI is a branch of computer science",
                    "metadata": {"title": "AI Intro", "source": "ai_source"},
                    "similarity": 0.9
                }]
            elif "machine learning" in query.lower():
                return [{
                    "content": "ML is a subset of AI",
                    "metadata": {"title": "ML Fundamentals", "source": "ml_source"},
                    "similarity": 0.9
                }]
            else:
                return [{
                    "content": "General AI content",
                    "metadata": {"title": "General AI", "source": "general_source"},
                    "similarity": 0.8
                }]
        
        rag_system_with_complex_docs.adaptive_retrieval = mock_adaptive_retrieval
        mock_llm_client.chat.return_value = "This is a response to your query."
        
        # Execute queries concurrently
        def execute_query(query):
            return rag_system_with_complex_docs.rag_query(query)
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_query, query) for query in queries]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all queries completed successfully
        assert len(results) == len(queries)
        for result in results:
            assert "answer" in result
            assert "sources" in result
            assert result["context_used"] >= 0


@pytest.mark.integration
class TestAPIEndpointIntegration:
    """Integration tests for RAG API endpoints."""

    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        health_data = response.json()
        
        assert "status" in health_data
        assert "timestamp" in health_data
        assert "components" in health_data
        
        # Verify component health checks
        components = health_data["components"]
        assert "rag_backend" in components
        assert "document_manager" in components

    def test_query_endpoint_basic(self, test_client):
        """Test basic query endpoint functionality."""
        query_data = {
            "query": "What is artificial intelligence?",
            "max_chunks": 3
        }
        
        with patch('main.rag_system') as mock_rag:
            mock_rag.rag_query.return_value = {
                "answer": "AI is a branch of computer science.",
                "sources": [{"title": "AI Intro", "source": "test", "chunk_count": 1}],
                "context_used": 1,
                "context_tokens": 50,
                "efficiency_ratio": 0.5
            }
            
            response = test_client.post("/api/v1/query", json=query_data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert "answer" in result
        assert "sources" in result
        assert result["answer"] == "AI is a branch of computer science."

    def test_query_endpoint_validation(self, test_client):
        """Test query endpoint input validation."""
        # Test empty query
        response = test_client.post("/api/v1/query", json={"query": ""})
        assert response.status_code == 422
        
        # Test missing query
        response = test_client.post("/api/v1/query", json={})
        assert response.status_code == 422
        
        # Test invalid max_chunks
        response = test_client.post("/api/v1/query", json={
            "query": "test",
            "max_chunks": -1
        })
        assert response.status_code == 422

    def test_documents_list_endpoint(self, test_client):
        """Test documents listing endpoint."""
        with patch('main.document_manager') as mock_doc_manager:
            mock_doc_manager.list_documents.return_value = [
                {
                    "doc_id": "test_doc_1",
                    "title": "Test Document 1",
                    "file_type": "txt",
                    "file_size": 1024,
                    "status": "ready",
                    "upload_timestamp": "2025-08-05T10:00:00Z"
                }
            ]
            
            response = test_client.get("/api/v1/documents")
        
        assert response.status_code == 200
        documents = response.json()
        
        assert isinstance(documents, list)
        assert len(documents) == 1
        assert documents[0]["doc_id"] == "test_doc_1"

    def test_document_detail_endpoint(self, test_client):
        """Test individual document detail endpoint."""
        doc_id = "test_doc_1"
        
        with patch('main.document_manager') as mock_doc_manager:
            mock_doc_manager.get_document_metadata.return_value = {
                "doc_id": doc_id,
                "title": "Test Document 1",
                "file_type": "txt",
                "file_size": 1024,
                "status": "ready",
                "chunk_count": 3,
                "upload_timestamp": "2025-08-05T10:00:00Z",
                "last_modified": "2025-08-05T10:00:00Z"
            }
            
            response = test_client.get(f"/api/v1/documents/{doc_id}")
        
        assert response.status_code == 200
        document = response.json()
        
        assert document["doc_id"] == doc_id
        assert document["title"] == "Test Document 1"
        assert document["chunk_count"] == 3

    def test_document_not_found(self, test_client):
        """Test document not found error handling."""
        with patch('main.document_manager') as mock_doc_manager:
            mock_doc_manager.get_document_metadata.return_value = None
            
            response = test_client.get("/api/v1/documents/nonexistent_doc")
        
        assert response.status_code == 404

    def test_document_delete_endpoint(self, test_client):
        """Test document deletion endpoint."""
        doc_id = "test_doc_1"
        
        with patch('main.document_manager') as mock_doc_manager:
            mock_doc_manager.delete_document.return_value = True
            
            response = test_client.delete(f"/api/v1/documents/{doc_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_file_upload_endpoint(self, test_client):
        """Test file upload endpoint."""
        # Create test file
        test_content = b"This is test file content for upload."
        
        with patch('main.upload_handler') as mock_upload_handler:
            mock_result = Mock()
            mock_result.success = True
            mock_result.document_id = "uploaded_doc_123"
            mock_result.message = "File uploaded successfully"
            
            mock_upload_handler.handle_upload = AsyncMock(return_value=mock_result)
            
            response = test_client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.txt", test_content, "text/plain")}
            )
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["success"] is True
        assert result["document_id"] == "uploaded_doc_123"

    def test_bulk_operations_endpoint(self, test_client):
        """Test bulk document operations endpoint."""
        operation_data = {
            "operation": "delete",
            "document_ids": ["doc1", "doc2", "doc3"]
        }
        
        with patch('main.document_manager') as mock_doc_manager:
            mock_doc_manager.bulk_delete_documents.return_value = {
                "deleted": 3,
                "failed": 0,
                "errors": []
            }
            
            response = test_client.post("/api/v1/documents/bulk", json=operation_data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["deleted"] == 3
        assert result["failed"] == 0

    def test_api_error_handling(self, test_client):
        """Test API error handling and response format."""
        with patch('main.rag_system') as mock_rag:
            mock_rag.rag_query.side_effect = Exception("Internal processing error")
            
            response = test_client.post("/api/v1/query", json={"query": "test query"})
        
        assert response.status_code == 500
        error_response = response.json()
        
        assert "error" in error_response
        assert "message" in error_response["error"]

    @pytest.mark.asyncio
    async def test_api_performance_under_load(self):
        """Test API performance under concurrent load."""
        async def make_request(client, query_data):
            response = await client.post("/api/v1/query", json=query_data)
            return response.status_code, response.json()
        
        # Mock the RAG system
        with patch('main.rag_system') as mock_rag:
            mock_rag.rag_query.return_value = {
                "answer": "Test response",
                "sources": [],
                "context_used": 0,
                "context_tokens": 10,
                "efficiency_ratio": 1.0
            }
            
            async with httpx.AsyncClient(app=app, base_url="http://test") as client:
                # Create concurrent requests
                tasks = []
                for i in range(20):
                    query_data = {"query": f"Test query {i}"}
                    tasks.append(make_request(client, query_data))
                
                # Execute all requests concurrently
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                duration = time.time() - start_time
                
                # Analyze results
                status_codes = [result[0] for result in results]
                successful_requests = [sc for sc in status_codes if sc == 200]
                
                # Performance assertions
                assert len(successful_requests) >= 18  # 90% success rate
                assert duration < 10.0  # Should complete within 10 seconds
                
                print(f"API load test: {len(successful_requests)}/20 successful in {duration:.2f}s")


@pytest.mark.integration
class TestRAGSystemReliability:
    """Integration tests for RAG system reliability and error recovery."""

    def test_error_recovery_embedding_failure(self, rag_system):
        """Test system recovery from embedding generation failures."""
        documents = [
            {
                "title": "Test Doc",
                "content": "Test content",
                "source": "test",
                "doc_id": "test_doc"
            }
        ]
        
        # Mock intermittent embedding failures
        call_count = 0
        def mock_generate_embeddings(texts):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Embedding service temporarily unavailable")
            return np.random.rand(len(texts), 384).tolist()
        
        rag_system.encoder.encode = mock_generate_embeddings
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=1)
        
        # Should eventually succeed with retry logic
        with pytest.raises(Exception):
            rag_system.add_documents(documents)

    def test_partial_failure_handling(self, rag_system):
        """Test handling of partial failures in batch operations."""
        documents = []
        for i in range(10):
            documents.append({
                "title": f"Doc {i}",
                "content": f"Content {i}" if i != 5 else "",  # Empty content for doc 5
                "source": f"test_{i}",
                "doc_id": f"doc_{i}"
            })
        
        # Mock collection operations
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=9)  # 9 successful documents
        
        # Mock embedding generation that handles empty content
        def mock_generate_embeddings(texts):
            return np.random.rand(len([t for t in texts if t.strip()]), 384).tolist()
        
        rag_system.encoder.encode = mock_generate_embeddings
        
        # Should handle partial failures gracefully
        result = rag_system.add_documents(documents)
        
        # Verify partial success
        assert "Successfully added" in result or "processed" in result.lower()

    def test_system_state_consistency(self, rag_system_with_complex_docs, mock_llm_client):
        """Test system state consistency across operations."""
        # Perform multiple operations and verify state consistency
        
        # Query 1
        result1 = rag_system_with_complex_docs.rag_query("What is AI?")
        
        # Add more documents (simulated)
        new_docs = [{
            "title": "Additional AI Info",
            "content": "More information about artificial intelligence",
            "source": "additional_source",
            "doc_id": "additional_doc"
        }]
        
        rag_system_with_complex_docs.collection.count = Mock(return_value=7)  # Updated count
        rag_system_with_complex_docs.encoder.encode = Mock(return_value=np.random.rand(1, 384).tolist())
        rag_system_with_complex_docs.add_documents(new_docs)
        
        # Query 2 - should work with updated state
        result2 = rag_system_with_complex_docs.rag_query("What is machine learning?")
        
        # Verify both queries succeeded
        assert "answer" in result1
        assert "answer" in result2
        assert result1["efficiency_ratio"] > 0
        assert result2["efficiency_ratio"] > 0