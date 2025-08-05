"""
Unit tests for DocumentState class.

Tests state management, async operations, WebSocket handling,
and UI state synchronization for document management.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-04
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List, Dict, Any

# Import modules under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'app', 'reflex_app', 'rag_reflex_app'))

from state.document_state import DocumentState, DocumentInfo, UploadStatus, UploadProgress
import reflex as rx


@pytest.mark.unit
class TestDocumentState:
    """Test suite for DocumentState functionality."""

    def test_init(self):
        """Test DocumentState initialization."""
        state = DocumentState()
        
        assert state.documents == []
        assert state.is_loading_documents is False
        assert state.upload_progress == {}
        assert state.is_upload_modal_open is False
        assert state.selected_documents == []
        assert state.search_query == ""
        assert state.filter_type == "all"
        assert state.sort_by == "newest"

    def test_toggle_upload_modal(self):
        """Test upload modal toggle functionality."""
        state = DocumentState()
        
        # Initially closed
        assert state.show_upload_modal is False
        
        # Toggle open
        state.toggle_upload_modal()
        assert state.show_upload_modal is True
        
        # Toggle closed
        state.toggle_upload_modal()
        assert state.show_upload_modal is False
        assert state.upload_status == ""
        assert state.websocket_client_id != ""  # Should generate new ID

    def test_clear_completed_uploads(self):
        """Test clearing completed upload progress items."""
        state = DocumentState()
        
        # Add various upload progress items
        state.upload_progress = {
            "task1": UploadProgress(
                task_id="task1",
                filename="file1.txt",
                status="completed"
            ),
            "task2": UploadProgress(
                task_id="task2",
                filename="file2.txt",
                status="error"
            ),
            "task3": UploadProgress(
                task_id="task3",
                filename="file3.txt",
                status="uploading"
            )
        }
        
        state.clear_completed_uploads()
        
        # Only active uploads should remain
        assert len(state.upload_progress) == 1
        assert "task3" in state.upload_progress

    @pytest.mark.asyncio
    async def test_load_documents_empty(self):
        """Test loading documents when database is empty."""
        state = DocumentState()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"documents": [], "total_count": 0}
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            await state.load_documents()
            
            assert state.documents == []
            assert state.is_loading_documents is False

    @pytest.mark.asyncio
    async def test_load_documents_with_data(self):
        """Test loading documents with populated database."""
        state = DocumentState()
        
        mock_documents = [
            {
                "doc_id": "doc1",
                "title": "Document 1",
                "file_type": "txt",
                "upload_date": "2025-08-04T10:00:00Z",
                "chunk_count": 3,
                "file_size": 1024,
                "status": "ready"
            },
            {
                "doc_id": "doc2",
                "title": "Document 2",
                "file_type": "pdf",
                "upload_date": "2025-08-04T11:00:00Z",
                "chunk_count": 5,
                "file_size": 2048,
                "status": "processing"
            }
        ]
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"documents": mock_documents}
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            await state.load_documents()
            
            assert len(state.documents) == 2
            assert state.documents[0].doc_id == "doc1"
            assert state.documents[1].doc_id == "doc2"
            assert state.is_loading_documents is False

    @pytest.mark.asyncio
    async def test_load_documents_with_filters(self):
        """Test loading documents with filtering parameters."""
        state = DocumentState()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"documents": []}
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            await state.load_documents(
                file_type="txt",
                status="ready",
                title_contains="test",
                limit=10,
                offset=0
            )
            
            # Verify the API was called with correct parameters
            call_args = mock_client.return_value.__aenter__.return_value.get.call_args
            params = call_args[1]["params"]
            
            assert params["file_type"] == "txt"
            assert params["status"] == "ready"
            assert params["title_contains"] == "test"
            assert params["limit"] == 10
            assert params["offset"] == 0

    @pytest.mark.asyncio
    async def test_load_documents_api_error(self):
        """Test loading documents when API returns error."""
        state = DocumentState()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 500
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            await state.load_documents()
            
            assert state.show_error is True
            assert "Failed to load documents" in state.error_message
            assert state.is_loading_documents is False

    @pytest.mark.asyncio
    async def test_handle_file_upload_single_file(self):
        """Test handling single file upload."""        
        with patch('httpx.AsyncClient') as mock_client, \
             patch.object(DocumentState, 'load_documents', new_callable=AsyncMock):
            state = DocumentState()
            
            # Mock UploadFile
            mock_file = Mock()
            mock_file.filename = "test.txt"
            mock_file.content_type = "text/plain"
            mock_file.read = AsyncMock(return_value=b"Test content")
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "task_id": "task123",
                "doc_id": "doc123",
                "status": "completed"
            }
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            await state.handle_file_upload([mock_file])
            
            assert "task123" in state.upload_progress
            assert state.upload_progress["task123"].filename == "test.txt"
            assert state.upload_progress["task123"].status == "completed"

    @pytest.mark.asyncio
    async def test_handle_file_upload_multiple_files(self):
        """Test handling multiple file upload."""
        with patch('httpx.AsyncClient') as mock_client, \
             patch.object(DocumentState, 'load_documents', new_callable=AsyncMock):
            state = DocumentState()
            
            # Mock multiple files
            mock_files = []
            for i in range(3):
                mock_file = Mock()
                mock_file.filename = f"test{i}.txt"
                mock_file.content_type = "text/plain"
                mock_file.read = AsyncMock(return_value=f"Test content {i}".encode())
                mock_files.append(mock_file)
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "upload_tasks": ["task1", "task2", "task3"],
                "errors": []
            }
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            await state.handle_file_upload(mock_files)
            
            # Should have progress tracking for all tasks
            assert len(state.upload_progress) == 3

    @pytest.mark.asyncio
    async def test_handle_file_upload_error(self):
        """Test handling file upload with errors."""
        state = DocumentState()
        
        mock_file = Mock()
        mock_file.filename = "error.txt"
        mock_file.read = AsyncMock(side_effect=Exception("Read error"))
        
        await state.handle_file_upload([mock_file])
        
        # Should have error in upload progress
        assert "error.txt" in state.upload_progress
        assert state.upload_progress["error.txt"].status == "failed"
        assert "Read error" in state.upload_progress["error.txt"].error_message

    def test_toggle_document_selection(self):
        """Test document selection toggle."""
        state = DocumentState()
        
        doc_id = "doc123"
        
        # Initially not selected
        assert doc_id not in state.selected_documents
        
        # Toggle selection on
        state.toggle_document_selection(doc_id)
        assert doc_id in state.selected_documents
        
        # Toggle selection off
        state.toggle_document_selection(doc_id)
        assert doc_id not in state.selected_documents

    def test_is_document_selected(self):
        """Test checking if document is selected."""
        state = DocumentState()
        
        doc_id = "doc123"
        state.selected_documents = [doc_id]
        
        assert state.is_document_selected(doc_id) is True
        assert state.is_document_selected("other_doc") is False

    def test_select_all_documents(self):
        """Test selecting all visible documents."""
        state = DocumentState()
        
        # Mock some documents
        state.documents = [
            DocumentInfo(doc_id="doc1", title="Doc 1", file_type="txt", upload_date="2025-08-04", chunk_count=1, file_size=100),
            DocumentInfo(doc_id="doc2", title="Doc 2", file_type="txt", upload_date="2025-08-04", chunk_count=1, file_size=100),
            DocumentInfo(doc_id="doc3", title="Doc 3", file_type="pdf", upload_date="2025-08-04", chunk_count=1, file_size=100)
        ]
        
        state.select_all_documents()
        
        assert len(state.selected_documents) == 3
        assert "doc1" in state.selected_documents
        assert "doc2" in state.selected_documents
        assert "doc3" in state.selected_documents

    def test_clear_selection(self):
        """Test clearing document selection."""
        state = DocumentState()
        
        state.selected_documents = ["doc1", "doc2", "doc3"]
        state.clear_selection()
        
        assert state.selected_documents == []

    def test_toggle_select_all(self):
        """Test toggle select all functionality."""
        state = DocumentState()
        
        # Mock documents
        state.documents = [
            DocumentInfo(doc_id="doc1", title="Doc 1", file_type="txt", upload_date="2025-08-04", chunk_count=1, file_size=100)
        ]
        
        # Toggle all on
        state.toggle_select_all(True)
        assert len(state.selected_documents) == 1
        
        # Toggle all off
        state.toggle_select_all(False)
        assert len(state.selected_documents) == 0

    @pytest.mark.asyncio
    async def test_delete_selected_documents_success(self):
        """Test successful deletion of selected documents."""
        with patch('httpx.AsyncClient') as mock_client:
            state = DocumentState()
            state.selected_documents = ["doc1", "doc2"]
            
            # Mock both DELETE and GET requests (GET is for load_documents)
            delete_response = Mock()
            delete_response.status_code = 200
            delete_response.json.return_value = {
                "success_count": 2,
                "error_count": 0,
                "errors": []
            }
            
            get_response = Mock()
            get_response.status_code = 200
            get_response.json.return_value = {"documents": []}
            
            mock_client.return_value.__aenter__.return_value.delete.return_value = delete_response
            mock_client.return_value.__aenter__.return_value.get.return_value = get_response
            
            await state.delete_selected_documents()
            
            assert state.selected_documents == []
            assert state.is_deleting is False

    @pytest.mark.asyncio
    async def test_delete_selected_documents_partial_failure(self):
        """Test deletion with some failures."""
        with patch('httpx.AsyncClient') as mock_client:
            state = DocumentState()
            state.selected_documents = ["doc1", "doc2"]
            
            # Mock both DELETE and GET requests (GET is for load_documents)
            delete_response = Mock()
            delete_response.status_code = 200
            delete_response.json.return_value = {
                "success_count": 1,
                "error_count": 1,
                "errors": [{"doc_id": "doc2", "error": "Not found"}]
            }
            
            get_response = Mock()
            get_response.status_code = 200
            get_response.json.return_value = {"documents": []}
            
            mock_client.return_value.__aenter__.return_value.delete.return_value = delete_response
            mock_client.return_value.__aenter__.return_value.get.return_value = get_response
            
            await state.delete_selected_documents()
            
            assert state.show_error is True
            assert "Some deletions failed" in state.error_message

    @pytest.mark.asyncio
    async def test_delete_single_document_success(self):
        """Test successful single document deletion."""        
        with patch('httpx.AsyncClient') as mock_client:
            state = DocumentState()
            
            # Mock both DELETE and GET requests (GET is for load_documents)
            delete_response = Mock()
            delete_response.status_code = 200
            
            get_response = Mock()
            get_response.status_code = 200
            get_response.json.return_value = {"documents": []}
            
            mock_client.return_value.__aenter__.return_value.delete.return_value = delete_response
            mock_client.return_value.__aenter__.return_value.get.return_value = get_response
            
            await state.delete_single_document("doc123")

    @pytest.mark.asyncio
    async def test_delete_single_document_failure(self):
        """Test single document deletion failure."""
        state = DocumentState()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            
            mock_client.return_value.__aenter__.return_value.delete.return_value = mock_response
            
            await state.delete_single_document("nonexistent")
            
            assert state.show_error is True
            assert "Failed to delete document" in state.error_message

    def test_set_search_query(self):
        """Test setting search query."""
        state = DocumentState()
        
        query = "test search"
        state.set_search_query(query)
        
        assert state.search_query == query

    def test_set_filter_type(self):
        """Test setting filter type."""
        state = DocumentState()
        
        filter_type = "pdf"
        state.set_filter_type(filter_type)
        
        assert state.filter_type == filter_type

    def test_set_sort_by(self):
        """Test setting sort method."""
        state = DocumentState()
        
        sort_by = "name"
        state.set_sort_by(sort_by)
        
        assert state.sort_by == sort_by

    def test_get_filtered_documents_no_filters(self):
        """Test getting filtered documents without filters."""
        state = DocumentState()
        
        # Mock documents
        state.documents = [
            DocumentInfo(doc_id="doc1", title="Document A", file_type="txt", upload_date="2025-08-04T10:00:00Z", chunk_count=1, file_size=100),
            DocumentInfo(doc_id="doc2", title="Document B", file_type="pdf", upload_date="2025-08-04T11:00:00Z", chunk_count=1, file_size=100)
        ]
        
        filtered = state.get_filtered_documents
        
        assert len(filtered) == 2

    def test_get_filtered_documents_with_type_filter(self):
        """Test getting filtered documents with type filter."""
        state = DocumentState()
        
        state.documents = [
            DocumentInfo(doc_id="doc1", title="Document A", file_type="txt", upload_date="2025-08-04", chunk_count=1, file_size=100),
            DocumentInfo(doc_id="doc2", title="Document B", file_type="pdf", upload_date="2025-08-04", chunk_count=1, file_size=100)
        ]
        
        state.filter_type = "txt"
        filtered = state.get_filtered_documents
        
        assert len(filtered) == 1
        assert filtered[0].file_type == "txt"

    def test_get_filtered_documents_with_search(self):
        """Test getting filtered documents with search query."""
        state = DocumentState()
        
        state.documents = [
            DocumentInfo(doc_id="doc1", title="AI Document", file_type="txt", upload_date="2025-08-04", chunk_count=1, file_size=100),
            DocumentInfo(doc_id="doc2", title="ML Guide", file_type="txt", upload_date="2025-08-04", chunk_count=1, file_size=100)
        ]
        
        state.search_query = "AI"
        filtered = state.get_filtered_documents
        
        assert len(filtered) == 1
        assert "AI" in filtered[0].title

    def test_get_filtered_documents_with_sorting(self):
        """Test getting filtered documents with sorting."""
        state = DocumentState()
        
        state.documents = [
            DocumentInfo(doc_id="doc1", title="B Document", file_type="txt", upload_date="2025-08-04", chunk_count=1, file_size=200),
            DocumentInfo(doc_id="doc2", title="A Document", file_type="txt", upload_date="2025-08-04", chunk_count=1, file_size=100)
        ]
        
        # Test name sorting
        state.sort_by = "name"
        filtered = state.get_filtered_documents
        
        assert filtered[0].title == "A Document"
        assert filtered[1].title == "B Document"
        
        # Test size sorting
        state.sort_by = "size"
        filtered = state.get_filtered_documents
        
        assert filtered[0].file_size == 200  # Largest first
        assert filtered[1].file_size == 100

    def test_selected_count(self):
        """Test selected document count."""
        state = DocumentState()
        
        state.selected_documents = ["doc1", "doc2", "doc3"]
        
        assert state.selected_count == 3

    def test_total_documents(self):
        """Test total document count."""
        state = DocumentState()
        
        state.documents = [
            DocumentInfo(doc_id="doc1", title="Doc 1", file_type="txt", upload_date="2025-08-04", chunk_count=1, file_size=100),
            DocumentInfo(doc_id="doc2", title="Doc 2", file_type="txt", upload_date="2025-08-04", chunk_count=1, file_size=100)
        ]
        
        assert state.total_documents == 2

    def test_uploading_files(self):
        """Test getting list of uploading files."""
        state = DocumentState()
        
        state.upload_progress = {
            "task1": UploadProgress(task_id="task1", filename="file1.txt", status="uploading"),
            "task2": UploadProgress(task_id="task2", filename="file2.txt", status="completed")
        }
        
        uploading = state.uploading_files
        
        assert len(uploading) == 2

    def test_show_error_message(self):
        """Test showing error message."""
        state = DocumentState()
        
        error_msg = "Test error message"
        state.show_error_message(error_msg)
        
        assert state.error_message == error_msg
        assert state.show_error is True

    def test_clear_error(self):
        """Test clearing error message."""
        state = DocumentState()
        
        # Set error first
        state.error_message = "Test error"
        state.show_error = True
        
        state.clear_error()
        
        assert state.error_message == ""
        assert state.show_error is False

    def test_format_file_size(self):
        """Test file size formatting."""
        state = DocumentState()
        
        # Test bytes
        assert state.format_file_size(512) == "512 B"
        
        # Test KB
        assert state.format_file_size(1536) == "1.5 KB"  # 1.5 * 1024
        
        # Test MB
        assert state.format_file_size(2097152) == "2.0 MB"  # 2 * 1024 * 1024

    def test_format_upload_date(self):
        """Test upload date formatting."""
        state = DocumentState()
        
        # Test valid ISO date
        iso_date = "2025-08-04T10:30:45Z"
        formatted = state.format_upload_date(iso_date)
        
        assert "2025-08-04" in formatted
        assert "10:30" in formatted
        
        # Test invalid date
        invalid_date = "invalid-date"
        formatted = state.format_upload_date(invalid_date)
        
        assert formatted == invalid_date  # Should return as-is

    def test_handle_websocket_message_ping(self):
        """Test handling WebSocket ping messages."""
        state = DocumentState()
        
        ping_message = json.dumps({
            "type": "ping",
            "timestamp": "2025-08-04T10:00:00Z"
        })
        
        state.handle_websocket_message(ping_message)
        
        assert state.last_update_timestamp == "2025-08-04T10:00:00Z"

    def test_handle_websocket_message_upload_progress(self):
        """Test handling WebSocket upload progress messages."""
        state = DocumentState()
        
        progress_message = json.dumps({
            "type": "progress",
            "task_id": "task123",
            "filename": "test.txt",
            "progress": 75.0,
            "status": "uploading",
            "message": "Processing...",
            "timestamp": "2025-08-04T10:00:00Z"
        })
        
        state.handle_websocket_message(progress_message)
        
        assert "task123" in state.upload_progress
        progress = state.upload_progress["task123"]
        assert progress.filename == "test.txt"
        assert progress.progress == 75.0
        assert progress.status == "uploading"

    def test_handle_websocket_message_malformed(self):
        """Test handling malformed WebSocket messages."""
        state = DocumentState()
        
        # Should not raise exception
        state.handle_websocket_message("invalid json")
        state.handle_websocket_message("")
        state.handle_websocket_message("null")

    def test_websocket_url_generation(self):
        """Test WebSocket URL generation."""
        state = DocumentState()
        
        # Without client ID
        assert state.websocket_url == ""
        
        # With client ID
        state.websocket_client_id = "client123"
        expected_url = "ws://localhost:8000/api/v1/documents/ws/client123"
        assert state.websocket_url == expected_url

    def test_upload_stats_summary(self):
        """Test upload statistics summary."""
        state = DocumentState()
        
        # No uploads
        assert state.upload_stats_summary == "No active uploads"
        
        # With various upload statuses
        state.upload_progress = {
            "task1": UploadProgress(task_id="task1", filename="file1.txt", status="completed"),
            "task2": UploadProgress(task_id="task2", filename="file2.txt", status="failed"),
            "task3": UploadProgress(task_id="task3", filename="file3.txt", status="uploading")
        }
        
        summary = state.upload_stats_summary
        assert "1 uploading" in summary
        assert "1 completed" in summary
        assert "1 failed" in summary

    def test_enable_disable_real_time_updates(self):
        """Test enabling and disabling real-time updates."""
        state = DocumentState()
        
        # Enable
        state.enable_real_time_updates()
        assert state.real_time_updates_enabled is True
        assert state.websocket_client_id != ""
        
        # Disable
        state.disable_real_time_updates()
        assert state.real_time_updates_enabled is False
        assert state.websocket_connected is False

    @pytest.mark.asyncio
    async def test_refresh_documents(self):
        """Test refreshing documents with current filters."""
        with patch.object(DocumentState, 'load_documents', new_callable=AsyncMock):
            state = DocumentState()
            
            state.filter_type = "txt"
            state.search_query = "test"
            
            # Test that the method executes without error
            await state.refresh_documents()

    @pytest.mark.asyncio
    async def test_get_document_status(self):
        """Test getting document processing status."""
        state = DocumentState()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "doc_id": "doc123",
                "status": "processing",
                "processing_progress": 50.0
            }
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await state.get_document_status("doc123")
            
            assert result is not None
            assert result["doc_id"] == "doc123"
            assert result["status"] == "processing"

    @pytest.mark.asyncio
    async def test_get_storage_statistics(self):
        """Test getting storage statistics."""
        state = DocumentState()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "total_documents": 10,
                "total_chunks": 50,
                "total_size_bytes": 1048576,
                "storage_efficiency": 0.85
            }
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await state.get_storage_statistics()
            
            assert result is not None
            assert result["total_documents"] == 10
            assert result["total_chunks"] == 50


@pytest.mark.unit
class TestDocumentInfoModel:
    """Test DocumentInfo data model."""

    def test_document_info_creation(self):
        """Test DocumentInfo object creation."""
        doc = DocumentInfo(
            doc_id="test123",
            title="Test Document",
            file_type="txt",
            upload_date="2025-08-04T10:00:00Z",
            chunk_count=5,
            file_size=1024,
            status="ready",
            error_message=""
        )
        
        assert doc.doc_id == "test123"
        assert doc.title == "Test Document"
        assert doc.file_type == "txt"
        assert doc.chunk_count == 5
        assert doc.file_size == 1024
        assert doc.status == "ready"

    def test_document_info_defaults(self):
        """Test DocumentInfo with default values."""
        doc = DocumentInfo(
            doc_id="test123",
            title="Test Document",
            file_type="txt",
            upload_date="2025-08-04T10:00:00Z",
            chunk_count=5,
            file_size=1024
        )
        
        assert doc.status == "ready"
        assert doc.error_message == ""


@pytest.mark.unit
class TestUploadProgressModel:
    """Test UploadProgress data model."""

    def test_upload_progress_creation(self):
        """Test UploadProgress object creation."""
        progress = UploadProgress(
            task_id="task123",
            filename="test.txt",
            progress=75.0,
            status="uploading",
            message="Processing document...",
            doc_id="doc123",
            timestamp="2025-08-04T10:00:00Z"
        )
        
        assert progress.task_id == "task123"
        assert progress.filename == "test.txt"
        assert progress.progress == 75.0
        assert progress.status == "uploading"
        assert progress.doc_id == "doc123"

    def test_upload_progress_defaults(self):
        """Test UploadProgress with default values."""
        progress = UploadProgress(
            task_id="task123",
            filename="test.txt"
        )
        
        assert progress.progress == 0.0
        assert progress.status == "pending"
        assert progress.message == ""
        assert progress.error_message == ""
        assert progress.doc_id is None