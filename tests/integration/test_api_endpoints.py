"""
Integration tests for FastAPI endpoints.

Tests API functionality, request/response handling, error scenarios,
and integration with backend services.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-04
"""

import pytest
import json
import asyncio
from typing import Dict, Any, List
from io import BytesIO
from fastapi.testclient import TestClient
import httpx

# Import modules under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from main import app


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health check and monitoring endpoints."""

    def test_health_check_basic(self, test_client):
        """Test basic health check endpoint."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "components" in data
        assert "document_count" in data
        assert isinstance(data["document_count"], int)

    def test_health_check_detailed(self, test_client):
        """Test detailed health check information."""
        response = test_client.get("/health")
        data = response.json()
        
        # Should include health details
        assert "health_details" in data
        assert "error_statistics" in data
        assert "monitoring" in data
        
        # Components should be boolean status
        components = data["components"]
        assert isinstance(components, dict)

    def test_api_info_endpoint(self, test_client):
        """Test API information endpoint."""
        response = test_client.get("/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "Local RAG System API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert "quick_test" in data

    def test_root_redirect(self, test_client):
        """Test root endpoint redirects to docs."""
        response = test_client.get("/", allow_redirects=False)
        
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"


@pytest.mark.integration
class TestDocumentEndpoints:
    """Test document management API endpoints."""

    def test_list_documents_empty(self, test_client):
        """Test listing documents when database is empty."""
        response = test_client.get("/api/v1/documents")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["documents"] == []
        assert data["total_count"] == 0

    def test_upload_single_file_success(self, test_client, sample_text_content):
        """Test successful single file upload."""
        file_content = sample_text_content.encode()
        files = {"file": ("test.txt", file_content, "text/plain")}
        
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "task_id" in data
        assert "doc_id" in data

    def test_upload_invalid_file_type(self, test_client):
        """Test upload with invalid file type."""
        file_content = b"Invalid binary content"
        files = {"file": ("test.exe", file_content, "application/octet-stream")}
        
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        # Should either reject or mark as failed
        data = response.json()
        assert data["success"] is False or "error" in data

    def test_upload_empty_file(self, test_client):
        """Test upload with empty file."""
        files = {"file": ("empty.txt", b"", "text/plain")}
        
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        # Should handle empty files gracefully
        assert response.status_code in [200, 400]

    def test_bulk_upload_success(self, test_client):
        """Test successful bulk file upload."""
        files = [
            ("files", ("file1.txt", b"Content of file 1", "text/plain")),
            ("files", ("file2.txt", b"Content of file 2", "text/plain")),
            ("files", ("file3.txt", b"Content of file 3", "text/plain"))
        ]
        
        response = test_client.post("/api/v1/documents/bulk-upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_files"] == 3
        assert data["successful_uploads"] >= 0
        assert data["failed_uploads"] >= 0

    def test_bulk_upload_mixed_file_types(self, test_client):
        """Test bulk upload with mixed valid and invalid file types."""
        files = [
            ("files", ("valid.txt", b"Valid text content", "text/plain")),
            ("files", ("invalid.exe", b"Invalid binary", "application/octet-stream"))
        ]
        
        response = test_client.post("/api/v1/documents/bulk-upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_files"] == 2
        assert data["successful_uploads"] == 1
        assert data["failed_uploads"] == 1
        assert len(data["errors"]) == 1

    def test_list_documents_after_upload(self, test_client):
        """Test listing documents after uploading some files."""
        # First upload a document
        file_content = b"Test document content for listing"
        files = {"file": ("list_test.txt", file_content, "text/plain")}
        
        upload_response = test_client.post("/api/v1/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        # Then list documents
        list_response = test_client.get("/api/v1/documents")
        
        assert list_response.status_code == 200
        data = list_response.json()
        
        assert data["total_count"] >= 1
        assert len(data["documents"]) >= 1
        
        # Check document structure
        doc = data["documents"][0]
        assert "doc_id" in doc
        assert "title" in doc
        assert "file_type" in doc
        assert "upload_date" in doc
        assert "chunk_count" in doc
        assert "file_size" in doc

    def test_list_documents_with_filters(self, test_client):
        """Test document listing with query parameters."""
        # Test with file type filter
        response = test_client.get("/api/v1/documents?file_type=txt")
        assert response.status_code == 200
        
        # Test with title search
        response = test_client.get("/api/v1/documents?title_contains=test")
        assert response.status_code == 200
        
        # Test with pagination
        response = test_client.get("/api/v1/documents?limit=5&offset=0")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["documents"]) <= 5

    def test_get_document_status(self, test_client):
        """Test getting document processing status."""
        # Upload a document first
        file_content = b"Test document for status check"
        files = {"file": ("status_test.txt", file_content, "text/plain")}
        
        upload_response = test_client.post("/api/v1/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        upload_data = upload_response.json()
        if "task_id" in upload_data:
            task_id = upload_data["task_id"]
        elif "doc_id" in upload_data:
            task_id = upload_data["doc_id"]
        else:
            pytest.skip("No task_id or doc_id in upload response")
        
        # Check status
        status_response = test_client.get(f"/api/v1/documents/{task_id}/status")
        
        assert status_response.status_code in [200, 404]  # 404 if task already completed
        
        if status_response.status_code == 200:
            data = status_response.json()
            assert "status" in data
            assert "processing_progress" in data

    def test_delete_document_success(self, test_client):
        """Test successful document deletion."""
        # First upload a document
        file_content = b"Document to be deleted"
        files = {"file": ("delete_test.txt", file_content, "text/plain")}
        
        upload_response = test_client.post("/api/v1/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        upload_data = upload_response.json()
        doc_id = upload_data.get("doc_id")
        
        if not doc_id:
            pytest.skip("No doc_id in upload response")
        
        # Delete the document
        delete_response = test_client.delete(f"/api/v1/documents/{doc_id}")
        
        assert delete_response.status_code == 200
        data = delete_response.json()
        
        assert "message" in data
        assert "deleted_chunks" in data
        assert data["deleted_chunks"] >= 0

    def test_delete_nonexistent_document(self, test_client):
        """Test deleting a non-existent document."""
        response = test_client.delete("/api/v1/documents/nonexistent_doc_id")
        
        assert response.status_code == 404

    def test_bulk_delete_documents(self, test_client):
        """Test bulk document deletion."""
        # Upload multiple documents first
        doc_ids = []
        for i in range(3):
            file_content = f"Document {i} for bulk deletion".encode()
            files = {"file": (f"bulk_delete_{i}.txt", file_content, "text/plain")}
            
            upload_response = test_client.post("/api/v1/documents/upload", files=files)
            if upload_response.status_code == 200:
                upload_data = upload_response.json()
                if "doc_id" in upload_data:
                    doc_ids.append(upload_data["doc_id"])
        
        if not doc_ids:
            pytest.skip("No documents uploaded for bulk delete test")
        
        # Bulk delete
        delete_data = {"doc_ids": doc_ids}
        response = test_client.delete("/api/v1/documents/bulk", json=delete_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success_count" in data
        assert "error_count" in data
        assert data["success_count"] >= 0

    def test_get_storage_stats(self, test_client):
        """Test getting storage statistics."""
        response = test_client.get("/api/v1/documents/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_documents" in data
        assert "total_chunks" in data
        assert "total_size_bytes" in data
        assert "avg_chunks_per_document" in data
        assert "file_type_distribution" in data
        assert "storage_efficiency" in data


@pytest.mark.integration
class TestQueryEndpoints:
    """Test RAG query processing endpoints."""

    def test_query_empty_database(self, test_client):
        """Test query when no documents are in database."""
        query_data = {"question": "What is artificial intelligence?"}
        
        response = test_client.post("/query", json=query_data)
        
        # Should handle gracefully with appropriate message
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "no documents" in data["answer"].lower()

    def test_query_with_documents(self, test_client, sample_text_content):
        """Test query processing with documents in database."""
        # First upload a document
        file_content = sample_text_content.encode()
        files = {"file": ("query_test.txt", file_content, "text/plain")}
        
        upload_response = test_client.post("/api/v1/documents/upload", files=files)
        assert upload_response.status_code == 200
        
        # Wait a moment for processing
        import time
        time.sleep(1)
        
        # Now query
        query_data = {"question": "What is artificial intelligence?"}
        response = test_client.post("/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "context_used" in data
        assert "context_tokens" in data
        assert "efficiency_ratio" in data

    def test_query_with_max_chunks(self, test_client):
        """Test query with max_chunks parameter."""
        query_data = {
            "question": "Test query with limit",
            "max_chunks": 2
        }
        
        response = test_client.post("/query", json=query_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should respect max_chunks limit
        assert len(data["sources"]) <= 2

    def test_query_invalid_request(self, test_client):
        """Test query with invalid request data."""
        # Missing question
        response = test_client.post("/query", json={})
        
        assert response.status_code == 422  # Validation error

    def test_query_very_long_question(self, test_client):
        """Test query with very long question."""
        long_question = "What is " + "very " * 1000 + "long question?"
        query_data = {"question": long_question}
        
        response = test_client.post("/query", json=query_data)
        
        # Should handle gracefully
        assert response.status_code == 200

    def test_query_special_characters(self, test_client):
        """Test query with special characters."""
        special_question = "What about @#$%^&*() symbols?"
        query_data = {"question": special_question}
        
        response = test_client.post("/query", json=query_data)
        
        assert response.status_code == 200


@pytest.mark.integration
class TestUploadTaskEndpoints:
    """Test upload task management endpoints."""

    def test_get_upload_tasks_empty(self, test_client):
        """Test getting upload tasks when none exist."""
        response = test_client.get("/api/v1/upload/tasks")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tasks" in data
        assert "total_tasks" in data
        assert isinstance(data["tasks"], list)

    def test_get_upload_task_nonexistent(self, test_client):
        """Test getting non-existent upload task."""
        response = test_client.get("/api/v1/upload/tasks/nonexistent_task_id")
        
        assert response.status_code == 404

    def test_cleanup_upload_tasks(self, test_client):
        """Test cleanup of old upload tasks."""
        response = test_client.post("/api/v1/upload/cleanup")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "removed_count" in data

    def test_get_upload_stats(self, test_client):
        """Test getting upload handler statistics."""
        response = test_client.get("/api/v1/upload/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return statistics dictionary
        assert isinstance(data, dict)


@pytest.mark.integration
class TestSettingsEndpoints:
    """Test configuration and settings endpoints."""

    def test_get_settings(self, test_client):
        """Test getting current RAG settings."""
        response = test_client.get("/settings")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "similarity_threshold" in data
        assert "max_context_tokens" in data
        assert "chunk_size" in data
        assert "chunk_overlap" in data

    def test_update_settings_partial(self, test_client):
        """Test updating settings with partial data."""
        update_data = {"similarity_threshold": 0.8}
        
        response = test_client.post("/settings", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Settings updated successfully"

    def test_update_settings_full(self, test_client):
        """Test updating all settings."""
        update_data = {
            "similarity_threshold": 0.75,
            "max_context_tokens": 3000,
            "chunk_size": 300,
            "chunk_overlap": 40
        }
        
        response = test_client.post("/settings", json=update_data)
        
        assert response.status_code == 200

    def test_update_settings_invalid_values(self, test_client):
        """Test updating settings with invalid values."""
        # Negative values should be handled gracefully
        update_data = {"similarity_threshold": -0.5}
        
        response = test_client.post("/settings", json=update_data)
        
        # Should either reject or clamp values
        assert response.status_code in [200, 400]


@pytest.mark.integration
class TestErrorHandling:
    """Test API error handling and edge cases."""

    def test_malformed_json_request(self, test_client):
        """Test handling of malformed JSON requests."""
        response = test_client.post(
            "/query",
            data="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

    def test_missing_content_type(self, test_client):
        """Test handling of requests with missing content type."""
        response = test_client.post("/query", data='{"question": "test"}')
        
        # FastAPI should handle this gracefully
        assert response.status_code in [200, 422]

    def test_very_large_file_upload(self, test_client):
        """Test handling of very large file uploads."""
        # Create a 10MB file (may be rejected based on limits)
        large_content = b"x" * (10 * 1024 * 1024)
        files = {"file": ("large.txt", large_content, "text/plain")}
        
        response = test_client.post("/api/v1/documents/upload", files=files)
        
        # Should either process or reject gracefully
        assert response.status_code in [200, 413]  # 413 = Request Entity Too Large

    def test_concurrent_requests(self, test_client):
        """Test handling of concurrent API requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = test_client.get("/health")
            results.append(response.status_code)
        
        # Make 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 10

    def test_invalid_endpoints(self, test_client):
        """Test access to invalid API endpoints."""
        invalid_endpoints = [
            "/api/v1/invalid",
            "/documents/nonexistent",
            "/api/v2/documents",  # Version that doesn't exist
        ]
        
        for endpoint in invalid_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 404

    def test_method_not_allowed(self, test_client):
        """Test using wrong HTTP methods."""
        # Try POST on GET endpoint
        response = test_client.post("/health")
        assert response.status_code == 405
        
        # Try GET on POST endpoint
        response = test_client.get("/query")
        assert response.status_code == 405


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Integration tests for API performance."""

    def test_health_check_performance(self, test_client, performance_config):
        """Test health check endpoint performance."""
        import time
        
        start_time = time.time()
        response = test_client.get("/health")
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < performance_config["api_response_timeout"]

    def test_document_list_performance(self, test_client, performance_config):
        """Test document listing performance."""
        import time
        
        start_time = time.time()
        response = test_client.get("/api/v1/documents")
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < performance_config["api_response_timeout"]

    def test_upload_performance(self, test_client, performance_config):
        """Test file upload performance."""
        import time
        
        # 1KB file should upload quickly
        file_content = b"x" * 1024
        files = {"file": ("perf_test.txt", file_content, "text/plain")}
        
        start_time = time.time()
        response = test_client.post("/api/v1/documents/upload", files=files)
        duration = time.time() - start_time
        
        assert response.status_code == 200
        # Small file should upload within timeout
        assert duration < performance_config["upload_timeout"]

    def test_query_performance(self, test_client, performance_config):
        """Test query processing performance."""
        import time
        
        query_data = {"question": "Performance test query"}
        
        start_time = time.time()
        response = test_client.post("/query", json=query_data)
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < performance_config["api_response_timeout"] * 10  # Queries can be slower


@pytest.mark.integration
@pytest.mark.asyncio
class TestAsyncIntegration:
    """Integration tests using async HTTP client."""

    async def test_async_health_check(self, async_client):
        """Test health check using async client."""
        response = await async_client.get("http://localhost:8000/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    async def test_async_document_operations(self, async_client):
        """Test document operations using async client."""
        # Upload document
        file_content = b"Async test document content"
        files = {"file": ("async_test.txt", file_content, "text/plain")}
        
        upload_response = await async_client.post(
            "http://localhost:8000/api/v1/documents/upload",
            files=files
        )
        
        assert upload_response.status_code == 200
        
        # List documents
        list_response = await async_client.get("http://localhost:8000/api/v1/documents")
        assert list_response.status_code == 200

    async def test_concurrent_async_requests(self, async_client):
        """Test concurrent async requests."""
        # Make multiple concurrent health checks
        tasks = [
            async_client.get("http://localhost:8000/health")
            for _ in range(5)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(response.status_code == 200 for response in responses)
        assert len(responses) == 5