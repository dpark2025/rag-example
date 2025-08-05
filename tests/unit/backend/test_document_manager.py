"""
Unit tests for DocumentManager class.

Tests document management operations including CRUD operations,
filtering, bulk operations, and error handling.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-04
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import List, Dict, Any

# Import modules under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from document_manager import DocumentManager, DocumentMetadata, DocumentFilter, BulkOperationResult
from rag_backend import LocalRAGSystem
from error_handlers import ApplicationError, ErrorCategory, ErrorSeverity


@pytest.mark.unit
class TestDocumentManager:
    """Test suite for DocumentManager functionality."""

    def test_init(self):
        """Test DocumentManager initialization."""
        manager = DocumentManager()
        assert manager.rag_system is not None
        assert manager is not None
        assert hasattr(manager, '_lock')
        assert hasattr(manager, '_executor')

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, document_manager):
        """Test listing documents when database is empty."""
        document_filter = DocumentFilter()
        documents, total_count = await document_manager.list_documents(document_filter)
        
        assert documents == []
        assert total_count == 0

    @pytest.mark.asyncio
    async def test_list_documents_with_data(self, document_manager, rag_system_with_documents):
        """Test listing documents with populated database."""
        # Override the manager to use populated system
        document_manager.rag_system = rag_system_with_documents
        
        document_filter = DocumentFilter()
        documents, total_count = await document_manager.list_documents(document_filter)
        
        assert len(documents) == 3  # Based on sample_documents fixture
        assert total_count == 3
        assert all(isinstance(doc, DocumentMetadata) for doc in documents)

    @pytest.mark.asyncio
    async def test_list_documents_with_file_type_filter(self, document_manager, rag_system_with_documents):
        """Test listing documents with file type filtering."""
        document_manager.rag_system = rag_system_with_documents
        
        document_filter = DocumentFilter(file_type="txt")
        documents, total_count = await document_manager.list_documents(document_filter)
        
        assert all(doc.file_type == "txt" for doc in documents)

    @pytest.mark.asyncio
    async def test_list_documents_with_title_filter(self, document_manager, rag_system_with_documents):
        """Test listing documents with title filtering."""
        document_manager.rag_system = rag_system_with_documents
        
        document_filter = DocumentFilter(title_contains="AI")
        documents, total_count = await document_manager.list_documents(document_filter)
        
        # Should find "AI Overview" document
        assert len(documents) >= 1
        assert any("AI" in doc.title for doc in documents)

    @pytest.mark.asyncio
    async def test_list_documents_with_limit_offset(self, document_manager, rag_system_with_documents):
        """Test listing documents with pagination."""
        document_manager.rag_system = rag_system_with_documents
        
        # Test limit
        document_filter = DocumentFilter(limit=2)
        documents, total_count = await document_manager.list_documents(document_filter)
        
        assert len(documents) <= 2
        assert total_count == 3  # Total should still be 3

        # Test offset
        document_filter = DocumentFilter(limit=2, offset=1)
        documents, total_count = await document_manager.list_documents(document_filter)
        
        assert len(documents) <= 2

    @pytest.mark.asyncio
    async def test_get_document_existing(self, document_manager, rag_system_with_documents):
        """Test retrieving an existing document."""
        document_manager.rag_system = rag_system_with_documents
        
        doc_metadata = await document_manager.get_document("test_doc_1")
        
        assert doc_metadata is not None
        assert doc_metadata.doc_id == "test_doc_1"
        assert doc_metadata.title == "AI Overview"

    @pytest.mark.asyncio
    async def test_get_document_nonexistent(self, document_manager):
        """Test retrieving a non-existent document."""
        doc_metadata = await document_manager.get_document("nonexistent_doc")
        assert doc_metadata is None

    @pytest.mark.asyncio
    async def test_delete_document_success(self, document_manager, rag_system_with_documents):
        """Test successful document deletion."""
        document_manager.rag_system = rag_system_with_documents
        
        # Verify document exists first
        doc_metadata = await document_manager.get_document("test_doc_1")
        assert doc_metadata is not None
        
        # Delete the document
        success, chunks_deleted = await document_manager.delete_document("test_doc_1")
        
        assert success is True
        assert chunks_deleted > 0
        
        # Verify document is deleted
        doc_metadata = await document_manager.get_document("test_doc_1")
        assert doc_metadata is None

    @pytest.mark.asyncio
    async def test_delete_document_nonexistent(self, document_manager):
        """Test deleting a non-existent document."""
        success, chunks_deleted = await document_manager.delete_document("nonexistent_doc")
        
        assert success is False
        assert chunks_deleted == 0

    @pytest.mark.asyncio
    async def test_bulk_delete_documents_success(self, document_manager, rag_system_with_documents):
        """Test successful bulk document deletion."""
        document_manager.rag_system = rag_system_with_documents
        
        doc_ids = ["test_doc_1", "test_doc_2"]
        result = await document_manager.bulk_delete_documents(doc_ids)
        
        assert isinstance(result, BulkOperationResult)
        assert result.success_count == 2
        assert result.error_count == 0
        assert result.total_chunks_affected > 0
        assert result.processing_time > 0

    @pytest.mark.asyncio
    async def test_bulk_delete_documents_partial_failure(self, document_manager, rag_system_with_documents):
        """Test bulk deletion with some non-existent documents."""
        document_manager.rag_system = rag_system_with_documents
        
        doc_ids = ["test_doc_1", "nonexistent_doc", "test_doc_2"]
        result = await document_manager.bulk_delete_documents(doc_ids)
        
        assert isinstance(result, BulkOperationResult)
        assert result.success_count == 2
        assert result.error_count == 1
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_bulk_delete_documents_empty_list(self, document_manager):
        """Test bulk deletion with empty document list."""
        result = await document_manager.bulk_delete_documents([])
        
        assert result.success_count == 0
        assert result.error_count == 0
        assert result.total_chunks_affected == 0

    @pytest.mark.asyncio
    async def test_get_storage_stats_empty(self, document_manager):
        """Test storage statistics with empty database."""
        stats = await document_manager.get_storage_stats()
        
        assert stats["total_documents"] == 0
        assert stats["total_chunks"] == 0
        assert stats["total_size_bytes"] == 0
        assert stats["avg_chunks_per_document"] == 0.0
        assert stats["file_type_distribution"] == {}

    @pytest.mark.asyncio
    async def test_get_storage_stats_with_data(self, document_manager, rag_system_with_documents):
        """Test storage statistics with populated database."""
        document_manager.rag_system = rag_system_with_documents
        
        stats = await document_manager.get_storage_stats()
        
        assert stats["total_documents"] > 0
        assert stats["total_chunks"] > 0
        assert stats["total_size_bytes"] > 0
        assert stats["avg_chunks_per_document"] > 0
        assert isinstance(stats["file_type_distribution"], dict)

    @pytest.mark.asyncio
    async def test_error_handling_database_error(self, document_manager):
        """Test error handling when database operations fail."""
        # Mock the RAG system to raise an exception
        document_manager.rag_system.collection.get.side_effect = Exception("Database error")
        
        with pytest.raises(ApplicationError) as exc_info:
            await document_manager.get_document("test_doc")
        
        error = exc_info.value
        assert error.category == ErrorCategory.DATABASE
        assert "Database error" in error.message

    @pytest.mark.asyncio
    async def test_performance_large_document_list(self, document_manager, performance_config):
        """Test performance with large number of documents."""
        # This would need a populated database with many documents
        # For now, we'll test the basic timing
        import time
        
        start_time = time.time()
        document_filter = DocumentFilter(limit=100)
        documents, total_count = await document_manager.list_documents(document_filter)
        duration = time.time() - start_time
        
        # Should complete within reasonable time
        assert duration < 1.0  # 1 second threshold

    def test_document_filter_validation(self):
        """Test DocumentFilter validation logic."""
        # Valid filter
        filter1 = DocumentFilter(
            file_type="txt",
            status="ready", 
            title_contains="test",
            limit=50,
            offset=0
        )
        assert filter1.file_type == "txt"
        assert filter1.limit == 50

        # Test default values
        filter2 = DocumentFilter()
        assert filter2.file_type is None
        assert filter2.limit is None
        assert filter2.offset == 0

    def test_document_metadata_creation(self):
        """Test DocumentMetadata object creation and validation."""
        metadata = DocumentMetadata(
            doc_id="test_123",
            title="Test Document",
            file_type="txt",
            file_size=1024,
            upload_timestamp="2025-08-04T10:00:00Z",
            chunk_count=5,
            status="ready"
        )
        
        assert metadata.doc_id == "test_123"
        assert metadata.title == "Test Document"
        assert metadata.file_type == "txt"
        assert metadata.file_size == 1024
        assert metadata.chunk_count == 5
        assert metadata.status == "ready"

    def test_bulk_operation_result_creation(self):
        """Test BulkOperationResult object creation."""
        result = BulkOperationResult(
            success_count=3,
            error_count=1,
            total_chunks_affected=15,
            processing_time=2.5,
            errors=[{"doc_id": "test", "error": "Not found"}]
        )
        
        assert result.success_count == 3
        assert result.error_count == 1
        assert result.total_chunks_affected == 15
        assert result.processing_time == 2.5
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, document_manager, rag_system_with_documents):
        """Test concurrent document manager operations."""
        document_manager.rag_system = rag_system_with_documents
        
        # Run multiple operations concurrently
        tasks = [
            document_manager.get_document("test_doc_1"),
            document_manager.get_document("test_doc_2"),
            document_manager.get_document("test_doc_3"),
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All operations should complete successfully
        assert len(results) == 3
        assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_memory_usage_during_operations(self, document_manager, rag_system_with_documents):
        """Test memory usage during document operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        document_manager.rag_system = rag_system_with_documents
        
        # Perform multiple operations
        for i in range(10):
            await document_manager.list_documents(DocumentFilter())
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_edge_case_empty_doc_id(self, document_manager):
        """Test edge case with empty document ID."""
        doc_metadata = await document_manager.get_document("")
        assert doc_metadata is None

    @pytest.mark.asyncio
    async def test_edge_case_very_long_doc_id(self, document_manager):
        """Test edge case with very long document ID."""
        long_doc_id = "a" * 1000  # 1000 character doc ID
        doc_metadata = await document_manager.get_document(long_doc_id)
        assert doc_metadata is None

    @pytest.mark.asyncio
    async def test_edge_case_special_characters_in_doc_id(self, document_manager):
        """Test edge case with special characters in document ID."""
        special_doc_id = "test@#$%^&*()_+-=[]{}|;':\",./<>?"
        doc_metadata = await document_manager.get_document(special_doc_id)
        assert doc_metadata is None


@pytest.mark.integration
class TestDocumentManagerIntegration:
    """Integration tests for DocumentManager with real ChromaDB."""

    @pytest.mark.asyncio
    async def test_full_document_lifecycle(self, document_manager, sample_documents):
        """Test complete document lifecycle: add, list, get, delete."""
        # Add documents to the system
        document_manager.rag_system.add_documents(sample_documents)
        
        # List documents
        document_filter = DocumentFilter()
        documents, total_count = await document_manager.list_documents(document_filter)
        assert len(documents) == 3
        
        # Get specific document
        doc = await document_manager.get_document("test_doc_1")
        assert doc is not None
        assert doc.title == "AI Overview"
        
        # Delete document
        success, chunks_deleted = await document_manager.delete_document("test_doc_1")
        assert success is True
        assert chunks_deleted > 0
        
        # Verify deletion
        doc = await document_manager.get_document("test_doc_1")
        assert doc is None
        
        # List remaining documents
        documents, total_count = await document_manager.list_documents(document_filter)
        assert len(documents) == 2

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_bulk_operations_performance(self, document_manager, rag_system_with_documents):
        """Test performance of bulk operations."""
        import time
        
        document_manager.rag_system = rag_system_with_documents
        
        # Measure bulk delete performance
        start_time = time.time()
        doc_ids = ["test_doc_1", "test_doc_2", "test_doc_3"]
        result = await document_manager.bulk_delete_documents(doc_ids)
        duration = time.time() - start_time
        
        assert result.success_count == 3
        assert duration < 5.0  # Should complete within 5 seconds