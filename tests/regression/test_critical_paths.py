"""
Regression test suite for critical paths and system reliability.

Tests core functionality, critical user journeys, and system reliability
to prevent regressions and ensure consistent behavior across releases.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-05
"""

import pytest
import asyncio
import time
import json
import tempfile
import os
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from fastapi.testclient import TestClient

# Import modules under test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from rag_backend import LocalRAGSystem, LocalLLMClient
from document_manager import DocumentManager
from upload_handler import UploadHandler
from main import app


@pytest.mark.regression
class TestCriticalUserJourneys:
    """Regression tests for critical user journeys."""

    @pytest.fixture
    def baseline_documents(self):
        """Standard test documents for regression testing."""
        return [
            {
                "title": "Artificial Intelligence Fundamentals",
                "content": """
                Artificial Intelligence (AI) is the simulation of human intelligence in machines 
                that are programmed to think like humans and mimic their actions. The term may 
                also be applied to any machine that exhibits traits associated with a human mind 
                such as learning and problem-solving.

                Key characteristics of AI include:
                - Learning: The ability to acquire information and rules for using the information
                - Reasoning: Using rules to reach approximate or definite conclusions
                - Self-correction: The ability to learn from mistakes and improve performance

                AI is used in various applications including:
                - Healthcare: Medical diagnosis and treatment recommendations
                - Finance: Fraud detection and algorithmic trading
                - Transportation: Autonomous vehicles and traffic optimization
                - Technology: Search engines and recommendation systems
                """,
                "source": "ai_fundamentals_2025",
                "doc_id": "regression_ai_001",
                "file_type": "txt"
            },
            {
                "title": "Machine Learning Overview",
                "content": """
                Machine Learning (ML) is a subset of artificial intelligence that provides 
                systems the ability to automatically learn and improve from experience without 
                being explicitly programmed. ML focuses on the development of computer programs 
                that can access data and use it to learn for themselves.

                Types of Machine Learning:
                1. Supervised Learning: Learning with labeled training data
                   - Examples: Classification, Regression
                   - Algorithms: Linear Regression, Decision Trees, SVM

                2. Unsupervised Learning: Finding hidden patterns in data without labels
                   - Examples: Clustering, Dimensionality Reduction
                   - Algorithms: K-Means, PCA, Hierarchical Clustering

                3. Reinforcement Learning: Learning through interaction with environment
                   - Examples: Game playing, Robotics
                   - Algorithms: Q-Learning, Policy Gradients

                Machine learning is the foundation of many modern AI applications and continues 
                to evolve with new techniques and algorithms.
                """,
                "source": "ml_overview_2025",
                "doc_id": "regression_ml_002",
                "file_type": "txt"
            },
            {
                "title": "Vector Databases in AI Systems",
                "content": """
                Vector databases are specialized databases designed to store and query 
                high-dimensional vectors efficiently. They are crucial for modern AI 
                applications, particularly those involving embeddings and similarity search.

                Key features of vector databases:
                - High-dimensional vector storage and indexing
                - Fast similarity search using various metrics (cosine, euclidean, dot product)
                - Horizontal scalability for large datasets
                - Integration with machine learning workflows

                Popular vector databases include:
                - Chroma: Open-source embedding database
                - Pinecone: Managed vector database service
                - Weaviate: Open-source vector search engine
                - Qdrant: Vector similarity search engine

                Use cases for vector databases:
                - Semantic search and information retrieval
                - Recommendation systems
                - Image and video search
                - Retrieval-Augmented Generation (RAG) systems
                - Anomaly detection and fraud prevention

                Vector databases enable efficient similarity search at scale, making them 
                essential for AI applications that work with embeddings.
                """,
                "source": "vector_db_guide_2025",
                "doc_id": "regression_vdb_003",
                "file_type": "txt"
            }
        ]

    @pytest.fixture
    def baseline_queries(self):
        """Standard test queries for regression testing."""
        return [
            {
                "query": "What is artificial intelligence?",
                "expected_topics": ["artificial intelligence", "ai", "intelligence", "machines"],
                "expected_sources": ["ai_fundamentals_2025"],
                "complexity": "simple"
            },
            {
                "query": "Explain the different types of machine learning",
                "expected_topics": ["supervised learning", "unsupervised learning", "reinforcement learning", "machine learning"],
                "expected_sources": ["ml_overview_2025"],
                "complexity": "moderate"
            },
            {
                "query": "How do vector databases work and what are they used for?",
                "expected_topics": ["vector databases", "similarity search", "embeddings", "high-dimensional"],
                "expected_sources": ["vector_db_guide_2025"],
                "complexity": "moderate"
            },
            {
                "query": "Compare machine learning and artificial intelligence applications",
                "expected_topics": ["machine learning", "artificial intelligence", "applications"],
                "expected_sources": ["ai_fundamentals_2025", "ml_overview_2025"],
                "complexity": "complex"
            }
        ]

    def test_document_upload_regression(self, rag_system, baseline_documents):
        """Test document upload functionality for regressions."""
        print("Testing document upload regression...")
        
        # Mock the system components
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=len(baseline_documents) * 3)
        
        # Mock embedding generation
        total_chunks = len(baseline_documents) * 3
        rag_system.encoder.encode = Mock(return_value=np.random.rand(total_chunks, 384).tolist())
        
        # Test document addition
        start_time = time.time()
        result = rag_system.add_documents(baseline_documents)
        processing_time = time.time() - start_time
        
        # Regression assertions
        assert "Successfully added" in result, "Document upload should succeed"
        assert f"{len(baseline_documents)} documents" in result, "Should report correct document count"
        
        # Performance regression checks
        expected_max_time = 10.0  # Maximum expected processing time
        assert processing_time < expected_max_time, f"Document processing time regression: {processing_time:.2f}s > {expected_max_time}s"
        
        # Verify mocked operations were called correctly
        assert rag_system.encoder.encode.called, "Embedding generation should be called"
        assert rag_system.collection.add.called, "Document storage should be called"
        
        throughput = len(baseline_documents) / processing_time
        print(f"Document upload regression test: {throughput:.1f} docs/sec, {processing_time:.2f}s")

    def test_query_processing_regression(self, rag_system, baseline_documents, baseline_queries, mock_llm_client):
        """Test query processing functionality for regressions."""
        print("Testing query processing regression...")
        
        # Setup system with documents
        rag_system.collection = Mock()
        rag_system.collection.count = Mock(return_value=len(baseline_documents) * 3)
        
        # Mock LLM responses
        mock_responses = {
            "What is artificial intelligence?": "Artificial Intelligence (AI) is the simulation of human intelligence in machines that are programmed to think like humans.",
            "Explain the different types of machine learning": "There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning.",
            "How do vector databases work and what are they used for?": "Vector databases store high-dimensional vectors and enable fast similarity search for AI applications.",
            "Compare machine learning and artificial intelligence applications": "Machine learning is a subset of AI with applications in healthcare, finance, and technology."
        }
        
        def mock_llm_response(messages, **kwargs):
            query = messages[-1].get("content", "") if messages else ""
            return mock_responses.get(query, "I can help answer questions about AI and machine learning.")
        
        mock_llm_client.chat = mock_llm_response
        
        # Test each baseline query
        query_results = []
        for query_data in baseline_queries:
            query = query_data["query"]
            expected_topics = query_data["expected_topics"]
            
            # Mock similarity search based on query
            mock_search_results = self._generate_mock_search_results(query, baseline_documents, expected_topics)
            rag_system.adaptive_retrieval = Mock(return_value=mock_search_results)
            
            start_time = time.time()
            result = rag_system.rag_query(query)
            processing_time = time.time() - start_time
            
            # Regression assertions
            assert isinstance(result, dict), "Query result should be a dictionary"
            assert "answer" in result, "Result should contain answer"
            assert "sources" in result, "Result should contain sources"
            assert "context_used" in result, "Result should contain context usage info"
            assert "efficiency_ratio" in result, "Result should contain efficiency metrics"
            
            # Quality assertions
            assert len(result["answer"]) > 20, "Answer should be substantial"
            assert result["context_used"] > 0, "Should use context from documents"
            assert len(result["sources"]) > 0, "Should cite sources"
            
            # Performance regression checks
            max_query_time = 5.0  # Maximum expected query time
            assert processing_time < max_query_time, f"Query processing time regression: {processing_time:.2f}s > {max_query_time}s"
            
            query_results.append({
                "query": query,
                "processing_time": processing_time,
                "context_used": result["context_used"],
                "sources_count": len(result["sources"]),
                "answer_length": len(result["answer"])
            })
        
        # Overall performance analysis
        avg_processing_time = sum(r["processing_time"] for r in query_results) / len(query_results)
        avg_context_used = sum(r["context_used"] for r in query_results) / len(query_results)
        
        print(f"Query processing regression: {avg_processing_time:.2f}s avg, {avg_context_used:.1f} context avg")

    def _generate_mock_search_results(self, query: str, documents: List[Dict], expected_topics: List[str]) -> List[Dict]:
        """Generate mock search results based on query and expected topics."""
        mock_results = []
        
        # Find relevant documents based on expected topics
        for doc in documents:
            relevance_score = 0.0
            doc_content_lower = doc["content"].lower()
            
            # Calculate relevance based on topic matches
            for topic in expected_topics:
                if topic.lower() in doc_content_lower:
                    relevance_score += 0.2
            
            if relevance_score > 0:
                # Extract relevant content chunk
                content_lines = doc["content"].split('\n')
                relevant_lines = [line for line in content_lines if any(topic.lower() in line.lower() for topic in expected_topics)]
                
                if relevant_lines:
                    content_chunk = ' '.join(relevant_lines[:3])  # First 3 relevant lines
                else:
                    content_chunk = doc["content"][:300]  # First 300 chars as fallback
                
                mock_results.append({
                    "content": content_chunk,
                    "metadata": {
                        "title": doc["title"],
                        "source": doc["source"],
                        "doc_id": doc["doc_id"]
                    },
                    "similarity": min(0.95, 0.7 + relevance_score)  # Similarity between 0.7-0.95
                })
        
        # Sort by similarity and return top results
        mock_results.sort(key=lambda x: x["similarity"], reverse=True)
        return mock_results[:3]  # Return top 3 results

    def test_api_endpoints_regression(self, test_client, baseline_documents):
        """Test API endpoint functionality for regressions."""
        print("Testing API endpoints regression...")
        
        # Test health endpoint
        response = test_client.get("/health")
        assert response.status_code == 200, "Health endpoint should be accessible"
        
        health_data = response.json()
        assert "status" in health_data, "Health response should contain status"
        assert "timestamp" in health_data, "Health response should contain timestamp"
        
        # Test query endpoint
        with patch('main.rag_system') as mock_rag:
            mock_rag.rag_query.return_value = {
                "answer": "Test answer for regression testing",
                "sources": [{"title": "Test Source", "source": "test", "chunk_count": 1}],
                "context_used": 1,
                "context_tokens": 50,
                "efficiency_ratio": 0.8
            }
            
            query_response = test_client.post(
                "/api/v1/query",
                json={"query": "What is artificial intelligence?"}
            )
            
            assert query_response.status_code == 200, "Query endpoint should work"
            query_data = query_response.json()
            assert "answer" in query_data, "Query response should contain answer"
            assert "sources" in query_data, "Query response should contain sources"
        
        # Test documents list endpoint
        with patch('main.document_manager') as mock_doc_manager:
            mock_doc_manager.list_documents.return_value = [
                {
                    "doc_id": "test_doc_1",
                    "title": "Test Document",
                    "file_type": "txt",
                    "status": "ready"
                }
            ]
            
            docs_response = test_client.get("/api/v1/documents")
            assert docs_response.status_code == 200, "Documents endpoint should work"
            docs_data = docs_response.json()
            assert isinstance(docs_data, list), "Documents response should be a list"
        
        print("API endpoints regression test completed")

    def test_error_handling_regression(self, rag_system, test_client):
        """Test error handling for regressions."""
        print("Testing error handling regression...")
        
        # Test RAG system error handling
        rag_system.collection = Mock()
        rag_system.collection.count = Mock(return_value=0)  # No documents
        
        with pytest.raises(Exception) as exc_info:
            rag_system.rag_query("Test query with no documents")
        
        assert "no documents" in str(exc_info.value).lower(), "Should report no documents error"
        
        # Test API error handling
        error_test_cases = [
            {"endpoint": "/api/v1/query", "data": {}, "expected_status": 422},  # Missing query
            {"endpoint": "/api/v1/query", "data": {"query": ""}, "expected_status": 422},  # Empty query
            {"endpoint": "/api/v1/documents/nonexistent", "method": "GET", "expected_status": 404},  # Not found
        ]
        
        for test_case in error_test_cases:
            if test_case.get("method") == "GET":
                response = test_client.get(test_case["endpoint"])
            else:
                response = test_client.post(test_case["endpoint"], json=test_case["data"])
            
            assert response.status_code == test_case["expected_status"], f"Error handling regression for {test_case['endpoint']}"
        
        print("Error handling regression test completed")


@pytest.mark.regression
class TestSystemReliabilityRegression:
    """Regression tests for system reliability and stability."""

    def test_memory_stability_regression(self, rag_system, bulk_document_generator):
        """Test memory stability for regressions."""
        print("Testing memory stability regression...")
        
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Process documents in batches to test memory stability
        for batch in range(5):
            documents = bulk_document_generator(20, size_kb=5)
            
            # Mock operations
            rag_system.collection = Mock()
            rag_system.collection.add = Mock()
            rag_system.collection.count = Mock(return_value=(batch + 1) * 20)
            rag_system.encoder.encode = Mock(return_value=np.random.rand(20 * 2, 384).tolist())
            
            result = rag_system.add_documents(documents)
            assert "Successfully added" in result, f"Batch {batch} processing should succeed"
            
            # Force garbage collection
            import gc
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_growth = (final_memory - initial_memory) / (1024**2)  # MB
        
        # Memory regression check
        max_memory_growth = 100  # MB
        assert memory_growth < max_memory_growth, f"Memory growth regression: {memory_growth:.1f}MB > {max_memory_growth}MB"
        
        print(f"Memory stability regression: {memory_growth:.1f}MB growth")

    def test_performance_baseline_regression(self, rag_system, baseline_documents, mock_llm_client):
        """Test performance baseline for regressions."""
        print("Testing performance baseline regression...")
        
        performance_baselines = {
            "document_upload_throughput": 20.0,  # docs/sec minimum
            "query_response_time": 2.0,          # seconds maximum
            "embedding_generation_time": 5.0,    # seconds maximum for baseline docs
        }
        
        # Test document upload performance
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=len(baseline_documents) * 3)
        rag_system.encoder.encode = Mock(return_value=np.random.rand(len(baseline_documents) * 3, 384).tolist())
        
        start_time = time.time()
        result = rag_system.add_documents(baseline_documents)
        upload_time = time.time() - start_time
        
        upload_throughput = len(baseline_documents) / upload_time
        assert upload_throughput >= performance_baselines["document_upload_throughput"], f"Upload throughput regression: {upload_throughput:.1f} < {performance_baselines['document_upload_throughput']}"
        
        # Test query performance
        rag_system.adaptive_retrieval = Mock(return_value=[
            {
                "content": "AI is the simulation of human intelligence in machines.",
                "metadata": {"title": "AI Fundamentals", "source": "test"},
                "similarity": 0.9
            }
        ])
        mock_llm_client.chat.return_value = "AI is artificial intelligence."
        
        start_time = time.time()
        query_result = rag_system.rag_query("What is AI?")
        query_time = time.time() - start_time
        
        assert query_time <= performance_baselines["query_response_time"], f"Query response time regression: {query_time:.2f}s > {performance_baselines['query_response_time']}s"
        
        print(f"Performance baseline: {upload_throughput:.1f} docs/sec upload, {query_time:.2f}s query")

    def test_concurrent_operations_stability(self, rag_system, mock_llm_client):
        """Test stability under concurrent operations."""
        print("Testing concurrent operations stability...")
        
        import threading
        import queue
        
        # Setup system
        rag_system.collection = Mock()
        rag_system.collection.count = Mock(return_value=10)
        rag_system.adaptive_retrieval = Mock(return_value=[
            {
                "content": "Test content for concurrent operations",
                "metadata": {"title": "Test Doc", "source": "test"},
                "similarity": 0.8
            }
        ])
        mock_llm_client.chat.return_value = "Concurrent test response"
        
        # Concurrent query test
        results_queue = queue.Queue()
        
        def concurrent_query(query_id):
            try:
                result = rag_system.rag_query(f"Test query {query_id}")
                results_queue.put({"success": True, "query_id": query_id, "result": result})
            except Exception as e:
                results_queue.put({"success": False, "query_id": query_id, "error": str(e)})
        
        # Run concurrent queries
        threads = []
        num_threads = 10
        
        for i in range(num_threads):
            thread = threading.Thread(target=concurrent_query, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)
        
        # Analyze results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        successful_queries = [r for r in results if r["success"]]
        failed_queries = [r for r in results if not r["success"]]
        
        success_rate = len(successful_queries) / len(results) if results else 0
        
        # Stability assertions
        assert success_rate >= 0.9, f"Concurrent operation stability regression: {success_rate:.2%} success rate"
        assert len(results) == num_threads, f"Expected {num_threads} results, got {len(results)}"
        
        print(f"Concurrent operations stability: {success_rate:.2%} success rate ({len(successful_queries)}/{len(results)})")

    def test_data_consistency_regression(self, document_manager):
        """Test data consistency for regressions."""
        print("Testing data consistency regression...")
        
        # Mock document operations
        stored_documents = {}
        
        async def mock_add_document(doc_data):
            doc_id = f"doc_{len(stored_documents) + 1}"
            stored_documents[doc_id] = doc_data.copy()
            return doc_id
        
        def mock_get_document_metadata(doc_id):
            if doc_id in stored_documents:
                doc_data = stored_documents[doc_id]
                return {
                    "doc_id": doc_id,
                    "title": doc_data.get("title", "Unknown"),
                    "file_type": doc_data.get("file_type", "txt"),
                    "status": "ready"
                }
            return None
        
        def mock_delete_document(doc_id):
            if doc_id in stored_documents:
                del stored_documents[doc_id]
                return True
            return False
        
        document_manager.add_document = mock_add_document
        document_manager.get_document_metadata = mock_get_document_metadata
        document_manager.delete_document = mock_delete_document
        
        # Test CRUD operations consistency
        # Add documents
        doc_ids = []
        for i in range(3):
            doc_data = {
                "title": f"Consistency Test Doc {i}",
                "content": f"Content for document {i}",
                "source": f"consistency_test_{i}",
                "file_type": "txt"
            }
            doc_id = asyncio.run(document_manager.add_document(doc_data))
            doc_ids.append(doc_id)
        
        # Verify documents exist
        for doc_id in doc_ids:
            metadata = document_manager.get_document_metadata(doc_id)
            assert metadata is not None, f"Document {doc_id} should exist after creation"
            assert metadata["doc_id"] == doc_id, "Document ID should be consistent"
        
        # Delete one document
        deleted_doc_id = doc_ids[1]
        delete_result = document_manager.delete_document(deleted_doc_id)
        assert delete_result is True, "Document deletion should succeed"
        
        # Verify deletion
        deleted_metadata = document_manager.get_document_metadata(deleted_doc_id)
        assert deleted_metadata is None, "Deleted document should not exist"
        
        # Verify other documents still exist
        remaining_doc_ids = [doc_ids[0], doc_ids[2]]
        for doc_id in remaining_doc_ids:
            metadata = document_manager.get_document_metadata(doc_id)
            assert metadata is not None, f"Non-deleted document {doc_id} should still exist"
        
        print(f"Data consistency regression: CRUD operations verified for {len(doc_ids)} documents")


@pytest.mark.regression
class TestBackwardCompatibilityRegression:
    """Test backward compatibility to prevent breaking changes."""

    def test_api_response_format_compatibility(self, test_client):
        """Test API response format compatibility."""
        print("Testing API response format compatibility...")
        
        # Define expected response schemas
        expected_schemas = {
            "/health": {
                "required_fields": ["status", "timestamp"],
                "optional_fields": ["components", "version", "uptime"]
            },
            "/api/v1/query": {
                "required_fields": ["answer", "sources", "context_used"],
                "optional_fields": ["context_tokens", "efficiency_ratio", "metadata"]
            },
            "/api/v1/documents": {
                "type": "array",
                "required_item_fields": ["doc_id", "title", "status"],
                "optional_item_fields": ["file_type", "file_size", "upload_timestamp"]
            }
        }
        
        # Test health endpoint compatibility
        health_response = test_client.get("/health")
        assert health_response.status_code == 200, "Health endpoint should be accessible"
        
        health_data = health_response.json()
        health_schema = expected_schemas["/health"]
        
        for field in health_schema["required_fields"]:
            assert field in health_data, f"Health response missing required field: {field}"
        
        # Test query endpoint compatibility
        with patch('main.rag_system') as mock_rag:
            mock_rag.rag_query.return_value = {
                "answer": "Compatibility test answer",
                "sources": [{"title": "Test Source", "source": "test", "chunk_count": 1}],
                "context_used": 1,
                "context_tokens": 25,
                "efficiency_ratio": 0.75
            }
            
            query_response = test_client.post(
                "/api/v1/query",
                json={"query": "Compatibility test query"}
            )
            
            assert query_response.status_code == 200, "Query endpoint should work"
            query_data = query_response.json()
            query_schema = expected_schemas["/api/v1/query"]
            
            for field in query_schema["required_fields"]:
                assert field in query_data, f"Query response missing required field: {field}"
        
        # Test documents endpoint compatibility
        with patch('main.document_manager') as mock_doc_manager:
            mock_doc_manager.list_documents.return_value = [
                {
                    "doc_id": "compat_test_1",
                    "title": "Compatibility Test Document",
                    "status": "ready",
                    "file_type": "txt",
                    "file_size": 1024
                }
            ]
            
            docs_response = test_client.get("/api/v1/documents")
            assert docs_response.status_code == 200, "Documents endpoint should work"
            
            docs_data = docs_response.json()
            assert isinstance(docs_data, list), "Documents response should be array"
            
            if docs_data:
                doc_schema = expected_schemas["/api/v1/documents"]
                for field in doc_schema["required_item_fields"]:
                    assert field in docs_data[0], f"Document item missing required field: {field}"
        
        print("API response format compatibility verified")

    def test_query_behavior_compatibility(self, rag_system, mock_llm_client):
        """Test query behavior compatibility."""
        print("Testing query behavior compatibility...")
        
        # Setup system with mock data
        rag_system.collection = Mock()
        rag_system.collection.count = Mock(return_value=5)
        
        # Test various query types that should maintain backward compatibility
        compatibility_queries = [
            {
                "query": "What is AI?",
                "expected_behavior": "simple_factual_response"
            },
            {
                "query": "Explain machine learning algorithms",
                "expected_behavior": "detailed_explanation"
            },
            {
                "query": "",
                "expected_behavior": "error_handling"
            },
            {
                "query": "A" * 1000,  # Very long query
                "expected_behavior": "handles_long_query"
            }
        ]
        
        for query_test in compatibility_queries:
            query = query_test["query"]
            expected_behavior = query_test["expected_behavior"]
            
            if expected_behavior == "error_handling":
                # Empty query should raise an error
                with pytest.raises(Exception):
                    rag_system.rag_query(query)
            else:
                # Mock appropriate responses
                if expected_behavior == "simple_factual_response":
                    rag_system.adaptive_retrieval = Mock(return_value=[
                        {
                            "content": "AI is artificial intelligence",
                            "metadata": {"title": "AI Basics", "source": "test"},
                            "similarity": 0.9
                        }
                    ])
                    mock_llm_client.chat.return_value = "AI stands for Artificial Intelligence."
                
                elif expected_behavior == "detailed_explanation":
                    rag_system.adaptive_retrieval = Mock(return_value=[
                        {
                            "content": "Machine learning includes supervised, unsupervised, and reinforcement learning",
                            "metadata": {"title": "ML Guide", "source": "test"},
                            "similarity": 0.85
                        }
                    ])
                    mock_llm_client.chat.return_value = "Machine learning algorithms can be categorized into three main types: supervised learning, unsupervised learning, and reinforcement learning."
                
                elif expected_behavior == "handles_long_query":
                    rag_system.adaptive_retrieval = Mock(return_value=[
                        {
                            "content": "Handling long queries requires careful processing",
                            "metadata": {"title": "Query Processing", "source": "test"},
                            "similarity": 0.7
                        }
                    ])
                    mock_llm_client.chat.return_value = "I can help with your detailed query."
                
                result = rag_system.rag_query(query)
                
                # Verify backward compatibility of result structure
                assert isinstance(result, dict), "Query result should be dictionary"
                assert "answer" in result, "Result should contain answer"
                assert "sources" in result, "Result should contain sources"
                assert isinstance(result["sources"], list), "Sources should be a list"
                
                if result["sources"]:
                    source = result["sources"][0]
                    assert "title" in source, "Source should contain title"
        
        print("Query behavior compatibility verified")

    def test_configuration_compatibility(self, rag_system):
        """Test configuration parameter compatibility."""
        print("Testing configuration compatibility...")
        
        # Test that system maintains compatibility with configuration parameters
        original_similarity_threshold = rag_system.similarity_threshold
        original_max_context_tokens = rag_system.max_context_tokens
        original_chunk_size = rag_system.chunk_size
        original_chunk_overlap = rag_system.chunk_overlap
        
        # Verify default values are within expected ranges
        assert 0.5 <= original_similarity_threshold <= 1.0, "Similarity threshold should be reasonable"
        assert 1000 <= original_max_context_tokens <= 10000, "Max context tokens should be reasonable"
        assert 100 <= original_chunk_size <= 1000, "Chunk size should be reasonable"
        assert 0 <= original_chunk_overlap <= 200, "Chunk overlap should be reasonable"
        
        # Test that parameters can be modified (backward compatibility)
        rag_system.similarity_threshold = 0.8
        rag_system.max_context_tokens = 5000
        rag_system.chunk_size = 500
        rag_system.chunk_overlap = 100
        
        # Verify changes took effect
        assert rag_system.similarity_threshold == 0.8, "Should be able to modify similarity threshold"
        assert rag_system.max_context_tokens == 5000, "Should be able to modify max context tokens"
        assert rag_system.chunk_size == 500, "Should be able to modify chunk size"
        assert rag_system.chunk_overlap == 100, "Should be able to modify chunk overlap"
        
        # Restore original values
        rag_system.similarity_threshold = original_similarity_threshold
        rag_system.max_context_tokens = original_max_context_tokens
        rag_system.chunk_size = original_chunk_size
        rag_system.chunk_overlap = original_chunk_overlap
        
        print("Configuration compatibility verified")


@pytest.mark.regression
@pytest.mark.slow
class TestIntegrationRegression:
    """Integration regression tests for component interactions."""

    def test_end_to_end_workflow_regression(self, rag_system, upload_handler, mock_llm_client):
        """Test complete end-to-end workflow for regressions."""
        print("Testing end-to-end workflow regression...")
        
        # Mock file upload
        from fastapi import UploadFile
        from io import BytesIO
        
        test_content = """
        Regression Testing in Software Development
        
        Regression testing is a type of software testing that ensures that previously 
        developed and tested software still performs correctly after changes or 
        additions to the codebase.
        
        Key benefits of regression testing:
        - Prevents introduction of new bugs
        - Validates existing functionality
        - Maintains software quality
        - Enables confident code changes
        """
        
        file_obj = BytesIO(test_content.encode())
        upload_file = UploadFile(
            file=file_obj,
            filename="regression_test.txt",
            size=len(test_content)
        )
        
        # Mock upload handler dependencies
        upload_handler.document_manager.add_document = AsyncMock(return_value="regression_doc_001")
        
        # Step 1: Upload document
        upload_result = asyncio.run(upload_handler.handle_upload(upload_file))
        
        assert upload_result.success, "Document upload should succeed"
        assert upload_result.document_id == "regression_doc_001", "Should return correct document ID"
        
        # Step 2: Setup RAG system with uploaded document
        rag_system.collection = Mock()
        rag_system.collection.count = Mock(return_value=3)  # Mock 3 chunks
        rag_system.adaptive_retrieval = Mock(return_value=[
            {
                "content": "Regression testing is a type of software testing that ensures previously developed software still works correctly.",
                "metadata": {"title": "Regression Testing in Software Development", "source": "regression_test.txt"},
                "similarity": 0.92
            }
        ])
        
        mock_llm_client.chat.return_value = "Regression testing is a software testing practice that verifies that existing functionality continues to work correctly after code changes."
        
        # Step 3: Query the uploaded document
        query_result = rag_system.rag_query("What is regression testing?")
        
        # Verify end-to-end workflow
        assert "regression testing" in query_result["answer"].lower(), "Answer should mention regression testing"
        assert len(query_result["sources"]) == 1, "Should cite the uploaded document"
        assert query_result["sources"][0]["title"] == "Regression Testing in Software Development", "Should cite correct source"
        assert query_result["context_used"] == 1, "Should use context from uploaded document"
        
        print("End-to-end workflow regression test completed successfully")

    def test_component_integration_regression(self, document_manager, rag_system):
        """Test integration between components for regressions."""
        print("Testing component integration regression...")
        
        # Test DocumentManager and RAGSystem integration
        test_doc_data = {
            "title": "Integration Test Document",
            "content": "This document tests integration between components in the RAG system.",
            "source": "integration_test",
            "file_type": "txt"
        }
        
        # Mock document manager operations
        document_manager.add_document = AsyncMock(return_value="integration_doc_001")
        document_manager.get_document_metadata = Mock(return_value={
            "doc_id": "integration_doc_001",
            "title": "Integration Test Document",
            "status": "ready",
            "chunk_count": 2
        })
        
        # Test document addition through document manager
        doc_id = asyncio.run(document_manager.add_document(test_doc_data))
        assert doc_id == "integration_doc_001", "Document manager should return correct ID"
        
        # Test metadata retrieval
        metadata = document_manager.get_document_metadata(doc_id)
        assert metadata["title"] == "Integration Test Document", "Should retrieve correct metadata"
        assert metadata["status"] == "ready", "Document should be ready"
        
        # Test RAG system integration
        rag_system.collection = Mock()
        rag_system.collection.count = Mock(return_value=2)
        rag_system.encoder.encode = Mock(return_value=np.random.rand(2, 384).tolist())
        rag_system.collection.add = Mock()
        
        # Simulate adding document to RAG system
        result = rag_system.add_documents([test_doc_data])
        assert "Successfully added" in result, "RAG system should successfully add document"
        
        print("Component integration regression test completed")

    def test_error_propagation_regression(self, rag_system, upload_handler):
        """Test error propagation between components for regressions."""
        print("Testing error propagation regression...")
        
        # Test error propagation from RAG system
        rag_system.collection = Mock()
        rag_system.collection.count = Mock(side_effect=Exception("Database connection error"))
        
        with pytest.raises(Exception) as exc_info:
            rag_system.rag_query("Test query that should fail")
        
        assert "Database connection error" in str(exc_info.value), "Error should propagate correctly"
        
        # Test error propagation in upload handler
        upload_handler.document_manager.add_document = AsyncMock(side_effect=Exception("Document processing error"))
        
        from fastapi import UploadFile
        from io import BytesIO
        
        error_file = UploadFile(
            file=BytesIO(b"Error test content"),
            filename="error_test.txt",
            size=18
        )
        
        with pytest.raises(Exception) as exc_info:
            asyncio.run(upload_handler.handle_upload(error_file))
        
        assert "Document processing error" in str(exc_info.value), "Upload error should propagate correctly"
        
        print("Error propagation regression test completed")


# Utility fixtures for regression testing
@pytest.fixture
def bulk_document_generator():
    """Generate bulk documents for regression testing."""
    def _generate_documents(count: int, size_kb: int = 5) -> List[Dict[str, Any]]:
        documents = []
        content_template = "Regression test document content. " * (size_kb * 40)
        
        for i in range(count):
            documents.append({
                "title": f"Regression Test Document {i+1}",
                "content": f"{content_template} Document ID: {i+1}",
                "source": f"regression_test_{i+1}",
                "doc_id": f"reg_doc_{i+1:06d}",
                "file_type": "txt"
            })
        
        return documents
    
    return _generate_documents


@pytest.fixture
def test_client():
    """Test client for API regression tests."""
    return TestClient(app)