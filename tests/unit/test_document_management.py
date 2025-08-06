"""
Unit tests for document management functionality.

Tests CRUD operations, bulk operations, filtering, and document lifecycle management.
Focuses on testing DocumentManager class with proper mocking of dependencies.

Authored by: QA/Test Engineer
Date: 2025-08-05
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from typing import List, Dict, Any

# Import modules under test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.document_manager import DocumentManager, DocumentMetadata, DocumentFilter
from app.rag_backend import LocalRAGSystem

@pytest.fixture
def document_manager_with_mock_rag():
    """Provide DocumentManager with mocked RAG system."""
    mock_rag = Mock(spec=LocalRAGSystem)
    mock_rag.add_documents.return_value = "Successfully added 1 documents (3 chunks)"
    mock_rag.collection = Mock()
    mock_rag.collection.count.return_value = 5
    
    manager = DocumentManager()
    manager.rag_system = mock_rag
    return manager


@pytest.fixture
def sample_documents_data():
    """Sample document data for testing."""
    return [
        {
            "title": "Financial Document",
            "content": "This is document 1 for bulk upload testing. Contains financial data.",
            "source": "doc1.txt",
            "file_type": "txt",
            "doc_id": "doc1"
        },
        {
            "title": "Technical Specifications", 
            "content": "This is document 2 for bulk upload testing. Contains technical specifications.",
            "source": "doc2.txt",
            "file_type": "txt",
            "doc_id": "doc2"
        },
        {
            "title": "Meeting Notes",
            "content": "This is document 3 for bulk upload testing. Contains meeting notes.",
            "source": "doc3.txt",
            "file_type": "txt", 
            "doc_id": "doc3"
        }
    ]


@pytest.mark.unit
class TestDocumentManager:
    """Unit tests for document manager functionality."""

    def test_document_manager_initialization(self):
        """Test DocumentManager can be initialized."""
        manager = DocumentManager()
        assert manager is not None
        
    def test_document_metadata_creation(self, sample_documents_data):
        """Test DocumentMetadata can be created with sample data."""
        document = sample_documents_data[0]
        
        metadata = DocumentMetadata(
            doc_id=document["doc_id"],
            title=document["title"],
            file_type=document["file_type"],
            file_size=len(document["content"]),
            upload_timestamp="2025-08-05T10:00:00Z",
            chunk_count=3,
            status="ready",
            last_modified="2025-08-05T10:00:00Z"
        )
        
        # Verify metadata creation
        assert metadata.doc_id == document["doc_id"]
        assert metadata.title == document["title"]
        assert metadata.file_type == document["file_type"]
        assert metadata.status == "ready"

    def test_document_filter_creation(self):
        """Test DocumentFilter can be created."""
        filter_obj = DocumentFilter(file_type="txt")
        assert filter_obj.file_type == "txt"
        
    def test_document_manager_has_expected_methods(self):
        """Test DocumentManager has expected async methods."""
        manager = DocumentManager()
        
        # Check that expected methods exist
        assert hasattr(manager, 'create_document')
        assert hasattr(manager, 'get_document')
        assert hasattr(manager, 'list_documents')
        assert hasattr(manager, 'update_document_metadata')
        
    def test_sample_documents_data_structure(self, sample_documents_data):
        """Test that sample documents have expected structure."""
        assert len(sample_documents_data) == 3
        
        for doc in sample_documents_data:
            assert "doc_id" in doc
            assert "title" in doc
            assert "content" in doc
            assert "file_type" in doc
            assert "source" in doc
@pytest.mark.unit
class TestDocumentListing:
    """Unit tests for document listing and filtering functionality."""

    def test_list_all_documents(self, document_manager_with_mock_rag):
        """Test listing all documents."""
        manager = document_manager_with_mock_rag
        
        # Mock ChromaDB response with multiple documents
        mock_query_result = {
            "ids": [["doc1", "doc2", "doc3"]],
            "metadatas": [[
                {"title": "Document 1", "file_type": "txt", "source": "doc1.txt"},
                {"title": "Document 2", "file_type": "pdf", "source": "doc2.pdf"},
                {"title": "Document 3", "file_type": "txt", "source": "doc3.txt"}
            ]],
            "documents": [["Content 1", "Content 2", "Content 3"]]
        }
        manager.rag_system.collection.get.return_value = mock_query_result
        
        documents = manager.list_documents()
        
        # Verify document listing
        assert len(documents) == 3
        assert documents[0]["doc_id"] == "doc1"
        assert documents[1]["file_type"] == "pdf"
        assert documents[2]["title"] == "Document 3"

    def test_filter_documents_by_type(self, document_manager_with_mock_rag):
        """Test filtering documents by file type."""
        manager = document_manager_with_mock_rag
        
        # Mock ChromaDB response with filtered results
        mock_query_result = {
            "ids": [["doc1", "doc3"]],
            "metadatas": [[
                {"title": "Document 1", "file_type": "txt", "source": "doc1.txt"},
                {"title": "Document 3", "file_type": "txt", "source": "doc3.txt"}
            ]],
            "documents": [["Content 1", "Content 3"]]
        }
        manager.rag_system.collection.get.return_value = mock_query_result
        
        filter_obj = DocumentFilter(file_type="txt")
        documents = manager.list_documents(filter_obj)
        
        # Verify filtering worked
        assert len(documents) == 2
        assert all(doc["file_type"] == "txt" for doc in documents)

    def test_pagination(self, document_manager_with_mock_rag):
        """Test document pagination."""
        manager = document_manager_with_mock_rag
        
        # Mock first page
        manager.rag_system.collection.get.return_value = {
            "ids": [["doc1", "doc2"]],
            "metadatas": [[
                {"title": "Document 1", "file_type": "txt", "source": "doc1.txt"},
                {"title": "Document 2", "file_type": "txt", "source": "doc2.txt"}
            ]],
            "documents": [["Content 1", "Content 2"]]
        }
        
        documents = manager.list_documents(limit=2, offset=0)
        
        # Verify pagination
        assert len(documents) <= 2
        manager.rag_system.collection.get.assert_called_once()


@pytest.mark.unit
class TestDocumentDeletion:
    """Unit tests for document deletion functionality."""

    def test_delete_single_document(self, document_manager_with_mock_rag):
        """Test deleting a single document."""
        manager = document_manager_with_mock_rag
        doc_id = "test_doc_1"
        
        # Mock ChromaDB delete operation
        manager.rag_system.collection.delete.return_value = None
        manager.rag_system.collection.get.return_value = {
            "ids": [[doc_id]],
            "metadatas": [[{"title": "Test Doc", "chunk_count": 3}]],
            "documents": [["Test content"]]
        }
        
        result = manager.delete_document(doc_id)
        
        # Verify deletion
        assert result["success"] is True
        assert result["deleted_chunks"] > 0
        manager.rag_system.collection.delete.assert_called_once()

    def test_delete_nonexistent_document(self, document_manager_with_mock_rag):
        """Test deleting a non-existent document."""
        manager = document_manager_with_mock_rag
        
        # Mock empty response
        manager.rag_system.collection.get.return_value = {
            "ids": [[]],
            "metadatas": [[]],
            "documents": [[]]
        }
        
        result = manager.delete_document("nonexistent_id")
        
        # Should handle gracefully
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_bulk_delete_documents(self, document_manager_with_mock_rag):
        """Test bulk document deletion."""
        manager = document_manager_with_mock_rag
        doc_ids = ["doc1", "doc2", "doc3"]
        
        # Mock successful bulk delete
        manager.rag_system.collection.delete.return_value = None
        manager.rag_system.collection.get.return_value = {
            "ids": [doc_ids],
            "metadatas": [[
                {"title": "Doc 1", "chunk_count": 2},
                {"title": "Doc 2", "chunk_count": 3},
                {"title": "Doc 3", "chunk_count": 1}
            ]],
            "documents": [["Content 1", "Content 2", "Content 3"]]
        }
        
        result = manager.delete_documents(doc_ids)
        
        # Verify bulk deletion
        assert result["success"] is True
        assert result["success_count"] == 3
        assert result["total_chunks_deleted"] == 6
        manager.rag_system.collection.delete.assert_called_once()

    def test_bulk_delete_with_failures(self, document_manager_with_mock_rag):
        """Test bulk deletion with some failures."""
        manager = document_manager_with_mock_rag
        doc_ids = ["doc1", "doc2", "nonexistent"]
        
        # Mock partial success
        manager.rag_system.collection.get.return_value = {
            "ids": [["doc1", "doc2"]],  # Only 2 found
            "metadatas": [[
                {"title": "Doc 1", "chunk_count": 2},
                {"title": "Doc 2", "chunk_count": 3}
            ]],
            "documents": [["Content 1", "Content 2"]]
        }
        manager.rag_system.collection.delete.return_value = None
        
        result = manager.delete_documents(doc_ids)
        
        # Should handle partial failures
        assert result["success"] is True  # Partial success still counts
        assert result["success_count"] == 2
        assert result["failed_count"] == 1


@pytest.mark.unit 
class TestDocumentStats:
    """Unit tests for document statistics functionality."""

    def test_get_storage_stats(self, document_manager_with_mock_rag):
        """Test getting storage statistics."""
        manager = document_manager_with_mock_rag
        
        # Mock collection stats
        manager.rag_system.collection.count.return_value = 10
        manager.rag_system.collection.get.return_value = {
            "ids": [["doc1", "doc2", "doc3"]],
            "metadatas": [[
                {"file_size": 1024, "chunk_count": 3},
                {"file_size": 2048, "chunk_count": 5},
                {"file_size": 512, "chunk_count": 2}
            ]],
            "documents": [["Content 1", "Content 2", "Content 3"]]
        }
        
        stats = manager.get_storage_stats()
        
        # Verify statistics
        assert stats["total_documents"] == 3
        assert stats["total_chunks"] == 10  # From collection.count()
        assert stats["total_size_bytes"] == 3584  # Sum of file sizes
        assert "storage_usage" in stats

    def test_get_document_count(self, document_manager_with_mock_rag):
        """Test getting document count."""
        manager = document_manager_with_mock_rag
        
        # Mock count response
        manager.rag_system.collection.count.return_value = 42
        
        count = manager.get_document_count()
        
        assert count == 42
        manager.rag_system.collection.count.assert_called_once()


@pytest.mark.integration
class TestDocumentManagementIntegration:
    """Integration tests for complete document management workflows."""

    def test_complete_document_lifecycle(self, document_manager_with_mock_rag, sample_documents_data):
        """Test complete document lifecycle: add, list, delete."""
        manager = document_manager_with_mock_rag
        
        # Add documents
        add_result = manager.add_documents(sample_documents_data)
        assert add_result["success"] is True
        
        # Mock document listing after addition
        manager.rag_system.collection.get.return_value = {
            "ids": [["doc1", "doc2", "doc3"]],
            "metadatas": [[
                {"title": "Financial Document", "file_type": "txt"},
                {"title": "Technical Specifications", "file_type": "txt"},
                {"title": "Meeting Notes", "file_type": "txt"}
            ]],
            "documents": [["Content 1", "Content 2", "Content 3"]]
        }
        
        # List documents
        documents = manager.list_documents()
        assert len(documents) == 3
        
        # Delete documents
        doc_ids = ["doc1", "doc2", "doc3"]
        delete_result = manager.delete_documents(doc_ids)
        assert delete_result["success"] is True