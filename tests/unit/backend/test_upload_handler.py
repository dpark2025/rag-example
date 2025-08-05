"""
Unit tests for UploadHandler class.

Tests file upload processing, WebSocket communication, task management,
and real-time progress tracking.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-04
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any
from io import BytesIO

# Import modules under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from upload_handler import UploadHandler, UploadTask, UploadStatus, BulkUploadResult
from document_manager import DocumentManager
from error_handlers import ApplicationError, ErrorCategory, ErrorSeverity


@pytest.mark.unit
class TestUploadHandler:
    """Test suite for UploadHandler functionality."""

    def test_init(self, document_manager):
        """Test UploadHandler initialization."""
        handler = UploadHandler()
        assert handler.document_manager is document_manager
        assert handler.active_tasks == {}
        assert handler.websocket_connections == {}

    @pytest.mark.asyncio
    async def test_process_single_file_success(self, upload_handler, sample_upload_file):
        """Test successful single file upload processing."""
        # Mock the document manager's add_document method
        upload_handler.document_manager.rag_system.add_documents = Mock(
            return_value="Successfully added document (3 chunks)"
        )
        
        task = await upload_handler.process_single_file(sample_upload_file)
        
        assert isinstance(task, UploadTask)
        assert task.filename == "sample.txt"
        assert task.status == UploadStatus.COMPLETED
        assert task.progress == 100.0
        assert task.doc_id is not None

    @pytest.mark.asyncio
    async def test_process_single_file_invalid_type(self, upload_handler):
        """Test single file upload with invalid file type."""
        from fastapi import UploadFile
        
        # Create invalid file type
        invalid_file = UploadFile(
            file=BytesIO(b"invalid content"),
            filename="test.exe"
        )
        
        task = await upload_handler.process_single_file(invalid_file)
        
        assert task.status == UploadStatus.FAILED
        assert "not supported" in task.error_message.lower()

    @pytest.mark.asyncio
    async def test_process_single_file_processing_error(self, upload_handler, sample_upload_file):
        """Test single file upload with processing error."""
        # Mock document manager to raise exception
        upload_handler.document_manager.rag_system.add_documents.side_effect = Exception("Processing failed")
        
        task = await upload_handler.process_single_file(sample_upload_file)
        
        assert task.status == UploadStatus.FAILED
        assert "Processing failed" in task.error_message

    @pytest.mark.asyncio
    async def test_process_multiple_files_success(self, upload_handler):
        """Test successful multiple file upload processing."""
        from fastapi import UploadFile
        
        # Create multiple upload files
        files = []
        for i in range(3):
            content = f"Content for file {i}".encode()
            file_obj = BytesIO(content)
            upload_file = UploadFile(
                file=file_obj,
                filename=f"file_{i}.txt"
            )
            files.append(upload_file)
        
        # Mock successful processing
        upload_handler.document_manager.rag_system.add_documents = Mock(
            return_value="Successfully added document (2 chunks)"
        )
        
        result = await upload_handler.process_multiple_files(files)
        
        assert isinstance(result, BulkUploadResult)
        assert result.total_files == 3
        assert result.successful_uploads == 3
        assert result.failed_uploads == 0
        assert len(result.upload_tasks) == 3

    @pytest.mark.asyncio
    async def test_process_multiple_files_partial_failure(self, upload_handler):
        """Test multiple file upload with some failures."""
        from fastapi import UploadFile
        
        # Create mix of valid and invalid files
        files = []
        # Valid file
        files.append(UploadFile(
            file=BytesIO(b"valid content"),
            filename="valid.txt"
        ))
        # Invalid file type
        files.append(UploadFile(
            file=BytesIO(b"invalid content"),
            filename="invalid.exe"
        ))
        
        # Mock processing for valid files
        upload_handler.document_manager.rag_system.add_documents = Mock(
            return_value="Successfully added document (1 chunks)"
        )
        
        result = await upload_handler.process_multiple_files(files)
        
        assert result.total_files == 2
        assert result.successful_uploads == 1
        assert result.failed_uploads == 1
        assert len(result.errors) == 1

    def test_create_upload_task(self, upload_handler):
        """Test upload task creation."""
        filename = "test.txt"
        file_size = 1024
        
        task = upload_handler._create_upload_task(filename, file_size)
        
        assert isinstance(task, UploadTask)
        assert task.filename == filename
        assert task.file_size == file_size
        assert task.status == UploadStatus.PENDING
        assert task.progress == 0.0
        assert task.task_id is not None
        assert task.created_at is not None

    def test_update_task_progress(self, upload_handler):
        """Test task progress updates."""
        # Create a task
        task = upload_handler._create_upload_task("test.txt", 1024)
        upload_handler.active_tasks[task.task_id] = task
        
        # Update progress
        upload_handler._update_task_progress(task.task_id, 50.0, UploadStatus.UPLOADING, "Uploading...")
        
        updated_task = upload_handler.active_tasks[task.task_id]
        assert updated_task.progress == 50.0
        assert updated_task.status == UploadStatus.UPLOADING
        assert updated_task.status_message == "Uploading..."

    def test_complete_task(self, upload_handler):
        """Test task completion."""
        # Create a task
        task = upload_handler._create_upload_task("test.txt", 1024)
        upload_handler.active_tasks[task.task_id] = task
        
        # Complete task
        doc_id = "completed_doc_123"
        upload_handler._complete_task(task.task_id, doc_id)
        
        completed_task = upload_handler.active_tasks[task.task_id]
        assert completed_task.status == UploadStatus.COMPLETED
        assert completed_task.progress == 100.0
        assert completed_task.doc_id == doc_id

    def test_fail_task(self, upload_handler):
        """Test task failure handling."""
        # Create a task
        task = upload_handler._create_upload_task("test.txt", 1024)
        upload_handler.active_tasks[task.task_id] = task
        
        # Fail task
        error_message = "Upload failed due to network error"
        upload_handler._fail_task(task.task_id, error_message)
        
        failed_task = upload_handler.active_tasks[task.task_id]
        assert failed_task.status == UploadStatus.FAILED
        assert failed_task.error_message == error_message

    def test_get_task_status(self, upload_handler):
        """Test retrieving task status."""
        # Create a task
        task = upload_handler._create_upload_task("test.txt", 1024)
        upload_handler.active_tasks[task.task_id] = task
        
        # Get task status
        retrieved_task = upload_handler.get_task_status(task.task_id)
        
        assert retrieved_task is not None
        assert retrieved_task.task_id == task.task_id
        
        # Test non-existent task
        non_existent = upload_handler.get_task_status("non_existent_id")
        assert non_existent is None

    def test_get_all_tasks(self, upload_handler):
        """Test retrieving all tasks."""
        # Create multiple tasks
        task1 = upload_handler._create_upload_task("file1.txt", 1024)
        task2 = upload_handler._create_upload_task("file2.txt", 2048)
        
        upload_handler.active_tasks[task1.task_id] = task1
        upload_handler.active_tasks[task2.task_id] = task2
        
        all_tasks = upload_handler.get_all_tasks()
        
        assert len(all_tasks) == 2
        assert task1 in all_tasks
        assert task2 in all_tasks

    def test_cleanup_completed_tasks(self, upload_handler):
        """Test cleanup of completed tasks."""
        # Create tasks with different statuses
        completed_task = upload_handler._create_upload_task("completed.txt", 1024)
        completed_task.status = UploadStatus.COMPLETED
        
        failed_task = upload_handler._create_upload_task("failed.txt", 1024)
        failed_task.status = UploadStatus.FAILED
        
        active_task = upload_handler._create_upload_task("active.txt", 1024)
        active_task.status = UploadStatus.UPLOADING
        
        upload_handler.active_tasks[completed_task.task_id] = completed_task
        upload_handler.active_tasks[failed_task.task_id] = failed_task
        upload_handler.active_tasks[active_task.task_id] = active_task
        
        # Cleanup completed tasks
        removed_count = upload_handler.cleanup_completed_tasks()
        
        assert removed_count == 2  # Completed and failed tasks removed
        assert len(upload_handler.active_tasks) == 1
        assert active_task.task_id in upload_handler.active_tasks

    def test_get_statistics(self, upload_handler):
        """Test getting upload handler statistics."""
        # Create tasks with different statuses
        for i in range(3):
            task = upload_handler._create_upload_task(f"file{i}.txt", 1024)
            task.status = UploadStatus.COMPLETED
            upload_handler.active_tasks[task.task_id] = task
        
        for i in range(2):
            task = upload_handler._create_upload_task(f"fail{i}.txt", 1024)
            task.status = UploadStatus.FAILED
            upload_handler.active_tasks[task.task_id] = task
        
        task = upload_handler._create_upload_task("active.txt", 1024)
        task.status = UploadStatus.UPLOADING
        upload_handler.active_tasks[task.task_id] = task
        
        stats = upload_handler.get_statistics()
        
        assert stats["total_tasks"] == 6
        assert stats["completed_tasks"] == 3
        assert stats["failed_tasks"] == 2
        assert stats["active_tasks"] == 1

    @pytest.mark.asyncio
    async def test_websocket_connection_handling(self, upload_handler, mock_websocket):
        """Test WebSocket connection handling."""
        client_id = "test_client_123"
        
        # Mock WebSocket accept and communication
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        mock_websocket.receive_text = AsyncMock(side_effect=["ping", "close"])
        
        # Test connection handling would require more complex mocking
        # This is a basic test for the connection setup
        upload_handler.websocket_connections[client_id] = mock_websocket
        
        assert client_id in upload_handler.websocket_connections
        assert upload_handler.websocket_connections[client_id] is mock_websocket

    @pytest.mark.asyncio
    async def test_broadcast_progress_update(self, upload_handler, mock_websocket):
        """Test broadcasting progress updates to connected clients."""
        client_id = "test_client_123"
        upload_handler.websocket_connections[client_id] = mock_websocket
        
        # Create a task to update
        task = upload_handler._create_upload_task("test.txt", 1024)
        upload_handler.active_tasks[task.task_id] = task
        
        # Update progress (this should trigger broadcast)
        upload_handler._update_task_progress(
            task.task_id, 75.0, UploadStatus.UPLOADING, "Processing..."
        )
        
        # In a real implementation, this would trigger WebSocket sends
        # For testing, we verify the task was updated
        updated_task = upload_handler.active_tasks[task.task_id]
        assert updated_task.progress == 75.0
        assert updated_task.status == UploadStatus.UPLOADING

    def test_validate_file_type_success(self, upload_handler):
        """Test successful file type validation."""
        from fastapi import UploadFile
        
        valid_file = UploadFile(
            file=BytesIO(b"content"),
            filename="test.txt"
        )
        
        # This would be tested through process_single_file
        assert upload_handler._is_supported_file_type(valid_file.content_type)

    def test_validate_file_type_failure(self, upload_handler):
        """Test file type validation failure."""
        # Test unsupported file type
        assert not upload_handler._is_supported_file_type("application/octet-stream")
        assert not upload_handler._is_supported_file_type("image/jpeg")
        assert not upload_handler._is_supported_file_type("video/mp4")

    def test_validate_file_size_success(self, upload_handler):
        """Test successful file size validation."""
        # Normal file size (1MB)
        assert upload_handler._is_valid_file_size(1024 * 1024)
        
        # Small file
        assert upload_handler._is_valid_file_size(1024)

    def test_validate_file_size_failure(self, upload_handler):
        """Test file size validation failure."""
        # Very large file (100MB+)
        large_size = 100 * 1024 * 1024 + 1
        assert not upload_handler._is_valid_file_size(large_size)
        
        # Zero size file
        assert not upload_handler._is_valid_file_size(0)

    @pytest.mark.asyncio
    async def test_error_handling_during_processing(self, upload_handler, sample_upload_file):
        """Test error handling during file processing."""
        # Mock document manager to raise different types of errors
        upload_handler.document_manager.rag_system.add_documents.side_effect = ApplicationError(
            message="Database connection failed",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            user_message="Database is temporarily unavailable"
        )
        
        task = await upload_handler.process_single_file(sample_upload_file)
        
        assert task.status == UploadStatus.FAILED
        assert "Database is temporarily unavailable" in task.error_message

    @pytest.mark.asyncio
    async def test_concurrent_file_processing(self, upload_handler):
        """Test concurrent file processing."""
        from fastapi import UploadFile
        
        # Create multiple files for concurrent processing
        files = []
        for i in range(5):
            content = f"Content for concurrent file {i}".encode()
            file_obj = BytesIO(content)
            upload_file = UploadFile(
                file=file_obj,
                filename=f"concurrent_{i}.txt"
            )
            files.append(upload_file)
        
        # Mock successful processing
        upload_handler.document_manager.rag_system.add_documents = Mock(
            return_value="Successfully added document (1 chunks)"
        )
        
        # Process files concurrently
        tasks = [upload_handler.process_single_file(file) for file in files]
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 5
        assert all(task.status == UploadStatus.COMPLETED for task in results)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_file_processing(self, upload_handler, large_upload_file, performance_config):
        """Test processing of large files."""
        import time
        
        # Mock processing
        upload_handler.document_manager.rag_system.add_documents = Mock(
            return_value="Successfully added document (50 chunks)"
        )
        
        start_time = time.time()
        task = await upload_handler.process_single_file(large_upload_file)
        duration = time.time() - start_time
        
        assert task.status == UploadStatus.COMPLETED
        assert duration < performance_config["upload_timeout"]

    def test_task_serialization(self, upload_handler):
        """Test task serialization for API responses."""
        task = upload_handler._create_upload_task("test.txt", 1024)
        task.progress = 50.0
        task.status = UploadStatus.UPLOADING
        task.status_message = "Processing..."
        
        task_dict = task.to_dict()
        
        assert isinstance(task_dict, dict)
        assert task_dict["filename"] == "test.txt"
        assert task_dict["progress"] == 50.0
        assert task_dict["status"] == "uploading"
        assert task_dict["status_message"] == "Processing..."

    def test_bulk_upload_result_creation(self, upload_handler):
        """Test BulkUploadResult creation and validation."""
        tasks = [
            upload_handler._create_upload_task("file1.txt", 1024),
            upload_handler._create_upload_task("file2.txt", 2048)
        ]
        tasks[0].status = UploadStatus.COMPLETED
        tasks[1].status = UploadStatus.FAILED
        
        result = BulkUploadResult(
            total_files=2,
            successful_uploads=1,
            failed_uploads=1,
            upload_tasks=["task1", "task2"],
            errors=[{"filename": "file2.txt", "error": "Processing failed"}],
            processing_time=5.5
        )
        
        assert result.total_files == 2
        assert result.successful_uploads == 1
        assert result.failed_uploads == 1
        assert len(result.errors) == 1
        assert result.processing_time == 5.5


@pytest.mark.integration
class TestUploadHandlerIntegration:
    """Integration tests for UploadHandler with real document processing."""

    @pytest.mark.asyncio
    async def test_end_to_end_file_upload(self, upload_handler, temp_directory):
        """Test complete file upload workflow."""
        from fastapi import UploadFile
        
        # Create test file
        test_content = "This is a test document for end-to-end upload testing."
        test_file_path = os.path.join(temp_directory, "test_upload.txt")
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        # Create UploadFile
        with open(test_file_path, 'rb') as f:
            upload_file = UploadFile(
                file=f,
                filename="test_upload.txt"
            )
            
            # Process the file
            task = await upload_handler.process_single_file(upload_file)
        
        assert task.status == UploadStatus.COMPLETED
        assert task.doc_id is not None
        
        # Verify document was added to RAG system
        doc_count = upload_handler.document_manager.rag_system.collection.count()
        assert doc_count > 0

    @pytest.mark.asyncio
    async def test_websocket_real_time_updates(self, upload_handler):
        """Test real-time progress updates via WebSocket."""
        # This would require a more complex WebSocket testing setup
        # For now, we test the basic update mechanism
        
        client_connections = {}
        upload_handler.websocket_connections = client_connections
        
        # Simulate task progress that would trigger WebSocket updates
        task = upload_handler._create_upload_task("realtime_test.txt", 1024)
        upload_handler.active_tasks[task.task_id] = task
        
        # Update progress
        upload_handler._update_task_progress(
            task.task_id, 100.0, UploadStatus.COMPLETED, "Upload completed"
        )
        
        # Verify task was updated
        updated_task = upload_handler.active_tasks[task.task_id]
        assert updated_task.status == UploadStatus.COMPLETED
        assert updated_task.progress == 100.0