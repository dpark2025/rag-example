"""
Comprehensive edge case tests for file upload functionality.

Tests large files, corrupt files, empty files, concurrent uploads,
memory pressure scenarios, and error recovery.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-05
"""

import pytest
import asyncio
import os
import tempfile
import time
import psutil
from io import BytesIO
from unittest.mock import Mock, patch, AsyncMock
from fastapi import UploadFile
from typing import List, Dict, Any

# Import modules under test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from upload_handler import UploadHandler, UploadTask, UploadStatus
from document_manager import DocumentManager
from error_handlers import ApplicationError, ErrorCategory, ErrorSeverity


@pytest.mark.unit
class TestFileUploadEdgeCases:
    """Edge case testing for file upload functionality."""

    @pytest.fixture
    def create_upload_file(self):
        """Utility to create UploadFile instances."""
        def _create_file(filename: str, content: bytes, content_type: str = "text/plain"):
            file_obj = BytesIO(content)
            return UploadFile(
                file=file_obj,
                filename=filename,
                size=len(content)
            )
        return _create_file

    @pytest.fixture
    def create_large_file(self, create_upload_file):
        """Create large file for testing."""
        def _create_large_file(size_mb: int):
            # Generate content of specified size
            chunk_size = 1024 * 1024  # 1MB chunks
            content = b"Large file test content. " * (chunk_size // 26)  # Fill 1MB
            
            if size_mb > 1:
                content = content * size_mb
            else:
                content = content[:size_mb * chunk_size]
                
            return create_upload_file(f"large_file_{size_mb}mb.txt", content)
        return _create_large_file

    @pytest.fixture
    def create_corrupt_file(self, create_upload_file):
        """Create corrupt/malformed files for testing."""
        def _create_corrupt_file(file_type: str):
            if file_type == "pdf":
                # Invalid PDF header
                content = b"Not a real PDF file, just invalid content"
                return create_upload_file("corrupt.pdf", content, "application/pdf")
            elif file_type == "binary":
                # Random binary data
                content = bytes(range(256)) * 100  # Binary garbage
                return create_upload_file("corrupt.bin", content, "application/octet-stream")
            elif file_type == "truncated":
                # Truncated file (incomplete)
                content = b"This file appears to be cut off in the midd"
                return create_upload_file("truncated.txt", content)
            elif file_type == "null_bytes":
                # File with null bytes
                content = b"Valid content\x00\x00\x00with null bytes\x00"
                return create_upload_file("null_bytes.txt", content)
            else:
                raise ValueError(f"Unknown corrupt file type: {file_type}")
        return _create_corrupt_file

    @pytest.mark.asyncio
    async def test_empty_file_upload(self, upload_handler, create_upload_file):
        """Test uploading completely empty file."""
        empty_file = create_upload_file("empty.txt", b"")
        
        with pytest.raises(ApplicationError) as exc_info:
            await upload_handler.handle_upload(empty_file)
        
        assert exc_info.value.category == ErrorCategory.VALIDATION
        assert "empty" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_whitespace_only_file(self, upload_handler, create_upload_file):
        """Test uploading file with only whitespace."""
        whitespace_file = create_upload_file("whitespace.txt", b"   \n\t  \n  ")
        
        with pytest.raises(ApplicationError) as exc_info:
            await upload_handler.handle_upload(whitespace_file)
        
        assert exc_info.value.category == ErrorCategory.VALIDATION
        assert "empty" in exc_info.value.message.lower() or "no content" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_file_upload_10mb(self, upload_handler, create_large_file):
        """Test uploading 10MB file."""
        large_file = create_large_file(10)
        
        start_time = time.time()
        
        # Mock document manager to avoid actual processing
        upload_handler.document_manager.add_document = AsyncMock(return_value="doc_123")
        
        result = await upload_handler.handle_upload(large_file)
        
        duration = time.time() - start_time
        
        assert result.success
        assert result.document_id == "doc_123"
        # Should complete within reasonable time (30 seconds for 10MB)
        assert duration < 30.0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_file_upload_100mb(self, upload_handler, create_large_file, performance_config):
        """Test uploading 100MB file (at configured limit)."""
        large_file = create_large_file(100)
        
        start_time = time.time()
        
        # Mock to avoid actual processing
        upload_handler.document_manager.add_document = AsyncMock(return_value="doc_large")
        
        result = await upload_handler.handle_upload(large_file)
        
        duration = time.time() - start_time
        
        assert result.success
        # Should complete within timeout limit
        assert duration < performance_config["upload_timeout"]

    @pytest.mark.asyncio
    async def test_oversized_file_rejection(self, upload_handler, create_large_file):
        """Test rejection of files exceeding size limit."""
        # Create file larger than typical limit (assume 200MB limit)
        oversized_file = create_large_file(200)
        
        with pytest.raises(ApplicationError) as exc_info:
            await upload_handler.handle_upload(oversized_file)
        
        assert exc_info.value.category == ErrorCategory.VALIDATION
        assert "size" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_corrupt_pdf_file(self, upload_handler, create_corrupt_file):
        """Test handling of corrupt PDF file."""
        corrupt_pdf = create_corrupt_file("pdf")
        
        with pytest.raises(ApplicationError) as exc_info:
            await upload_handler.handle_upload(corrupt_pdf)
        
        assert exc_info.value.category in [ErrorCategory.PROCESSING, ErrorCategory.VALIDATION]
        assert "pdf" in exc_info.value.message.lower() or "format" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_binary_garbage_file(self, upload_handler, create_corrupt_file):
        """Test handling of binary garbage file."""
        binary_file = create_corrupt_file("binary")
        
        with pytest.raises(ApplicationError) as exc_info:
            await upload_handler.handle_upload(binary_file)
        
        assert exc_info.value.category in [ErrorCategory.PROCESSING, ErrorCategory.VALIDATION]

    @pytest.mark.asyncio
    async def test_truncated_file(self, upload_handler, create_corrupt_file):
        """Test handling of truncated/incomplete file."""
        truncated_file = create_corrupt_file("truncated")
        
        # This might succeed but with warnings, or fail gracefully
        try:
            result = await upload_handler.handle_upload(truncated_file)
            # If it succeeds, check for warnings
            assert result.success
            if hasattr(result, 'warnings'):
                assert len(result.warnings) > 0
        except ApplicationError as e:
            # If it fails, should be graceful failure
            assert e.category in [ErrorCategory.PROCESSING, ErrorCategory.VALIDATION]

    @pytest.mark.asyncio
    async def test_null_bytes_file(self, upload_handler, create_corrupt_file):
        """Test handling of file with null bytes."""
        null_bytes_file = create_corrupt_file("null_bytes")
        
        # Should either clean the content or reject gracefully
        try:
            result = await upload_handler.handle_upload(null_bytes_file)
            assert result.success
        except ApplicationError as e:
            assert e.category in [ErrorCategory.PROCESSING, ErrorCategory.VALIDATION]

    @pytest.mark.asyncio
    async def test_special_character_filename(self, upload_handler, create_upload_file):
        """Test files with special characters in filename."""
        special_names = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.with.dots.txt",
            "file@email.com.txt",
            "file#hash.txt",
            "file%percent.txt",
            "файл.txt",  # Cyrillic
            "文件.txt",   # Chinese
            "ファイル.txt" # Japanese
        ]
        
        for filename in special_names:
            special_file = create_upload_file(filename, b"Test content for special filename")
            
            # Mock document manager
            upload_handler.document_manager.add_document = AsyncMock(return_value="doc_special")
            
            result = await upload_handler.handle_upload(special_file)
            assert result.success, f"Failed to upload file with name: {filename}"

    @pytest.mark.asyncio
    async def test_duplicate_filename_handling(self, upload_handler, create_upload_file):
        """Test handling of duplicate filenames."""
        file1 = create_upload_file("duplicate.txt", b"First file content")
        file2 = create_upload_file("duplicate.txt", b"Second file content")
        
        # Mock document manager to track calls
        upload_handler.document_manager.add_document = AsyncMock(side_effect=["doc_1", "doc_2"])
        
        result1 = await upload_handler.handle_upload(file1)
        result2 = await upload_handler.handle_upload(file2)
        
        assert result1.success
        assert result2.success
        assert result1.document_id != result2.document_id

    @pytest.mark.asyncio
    async def test_concurrent_uploads(self, upload_handler, create_upload_file):
        """Test concurrent file uploads."""
        files = []
        for i in range(5):
            files.append(create_upload_file(f"concurrent_{i}.txt", f"Content {i}".encode()))
        
        # Mock document manager
        upload_handler.document_manager.add_document = AsyncMock(side_effect=[f"doc_{i}" for i in range(5)])
        
        # Upload all files concurrently
        tasks = [upload_handler.handle_upload(file) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Upload {i} failed: {result}"
            assert result.success
            assert result.document_id == f"doc_{i}"

    @pytest.mark.asyncio
    async def test_memory_pressure_during_upload(self, upload_handler, create_large_file):
        """Test upload behavior under memory pressure."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create multiple large files
        large_files = [create_large_file(5) for _ in range(3)]
        
        # Mock document manager
        upload_handler.document_manager.add_document = AsyncMock(side_effect=["doc_1", "doc_2", "doc_3"])
        
        for i, file in enumerate(large_files):
            result = await upload_handler.handle_upload(file)
            assert result.success
            
            current_memory = process.memory_info().rss
            memory_increase = current_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB per file)
            assert memory_increase < 100 * 1024 * 1024 * (i + 1)

    @pytest.mark.asyncio
    async def test_upload_timeout_handling(self, upload_handler, create_upload_file):
        """Test upload timeout scenarios."""
        test_file = create_upload_file("timeout_test.txt", b"Test content")
        
        # Mock document manager to simulate slow processing
        async def slow_add_document(*args, **kwargs):
            await asyncio.sleep(2.0)  # Simulate slow processing
            return "doc_slow"
        
        upload_handler.document_manager.add_document = slow_add_document
        
        # Set short timeout for test
        original_timeout = getattr(upload_handler, 'timeout', None)
        upload_handler.timeout = 1.0
        
        try:
            with pytest.raises(ApplicationError) as exc_info:
                await upload_handler.handle_upload(test_file)
            
            assert exc_info.value.category == ErrorCategory.TIMEOUT
        finally:
            # Restore original timeout
            if original_timeout:
                upload_handler.timeout = original_timeout

    @pytest.mark.asyncio
    async def test_disk_space_full_simulation(self, upload_handler, create_upload_file, tmp_path):
        """Test behavior when disk space is full."""
        test_file = create_upload_file("disk_full_test.txt", b"Test content")
        
        # Mock document manager to simulate disk full error
        upload_handler.document_manager.add_document = AsyncMock(
            side_effect=OSError("No space left on device")
        )
        
        with pytest.raises(ApplicationError) as exc_info:
            await upload_handler.handle_upload(test_file)
        
        assert exc_info.value.category == ErrorCategory.SYSTEM
        assert "space" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_interrupted_upload_recovery(self, upload_handler, create_upload_file):
        """Test recovery from interrupted uploads."""
        test_file = create_upload_file("interrupted.txt", b"Test content for interrupted upload")
        
        # Mock document manager to fail first time, succeed second time
        call_count = 0
        async def mock_add_document(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Connection interrupted")
            return "doc_recovered"
        
        upload_handler.document_manager.add_document = mock_add_document
        
        # First attempt should fail
        with pytest.raises(ApplicationError):
            await upload_handler.handle_upload(test_file)
        
        # Reset file pointer for retry
        test_file.file.seek(0)
        
        # Second attempt should succeed
        result = await upload_handler.handle_upload(test_file)
        assert result.success
        assert result.document_id == "doc_recovered"

    @pytest.mark.asyncio
    async def test_malformed_content_type(self, upload_handler):
        """Test handling of files with incorrect content type."""
        # Create PDF content but claim it's text
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF"
        
        file_obj = BytesIO(pdf_content)
        mistyped_file = UploadFile(
            file=file_obj,
            filename="fake.txt",
            size=len(pdf_content)
        )
        
        # Should either detect correct type or handle gracefully
        try:
            # Mock document manager
            upload_handler.document_manager.add_document = AsyncMock(return_value="doc_mistyped")
            
            result = await upload_handler.handle_upload(mistyped_file)
            assert result.success
        except ApplicationError as e:
            assert e.category in [ErrorCategory.PROCESSING, ErrorCategory.VALIDATION]

    @pytest.mark.asyncio
    async def test_upload_with_network_instability(self, upload_handler, create_upload_file):
        """Test upload resilience to network instability."""
        test_file = create_upload_file("network_test.txt", b"Network instability test content")
        
        # Mock intermittent network failures
        attempt_count = 0
        async def unstable_add_document(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count <= 2:
                # Fail first two attempts with different network errors
                if attempt_count == 1:
                    raise ConnectionError("Connection refused")
                else:
                    raise TimeoutError("Request timed out")
            
            return "doc_network_stable"
        
        upload_handler.document_manager.add_document = unstable_add_document
        
        # Should eventually succeed with retry logic
        with patch.object(upload_handler, 'max_retries', 3):
            result = await upload_handler.handle_upload(test_file)
            assert result.success
            assert result.document_id == "doc_network_stable"


@pytest.mark.integration
class TestFileUploadIntegrationEdgeCases:
    """Integration tests for file upload edge cases."""

    @pytest.mark.asyncio
    async def test_end_to_end_large_file_processing(self, upload_handler, create_large_file):
        """Test complete large file processing pipeline."""
        large_file = create_large_file(10)
        
        # Use real document manager but mock heavy operations
        with patch.object(upload_handler.document_manager.rag_system.encoder, 'encode') as mock_embed:
            mock_embed.return_value = [[0.1] * 384] * 20  # Mock embeddings
            
            with patch.object(upload_handler.document_manager.rag_system.collection, 'add') as mock_add:
                mock_add.return_value = None
                
                result = await upload_handler.handle_upload(large_file)
                
                assert result.success
                assert mock_embed.called
                assert mock_add.called

    @pytest.mark.asyncio
    async def test_concurrent_upload_resource_contention(self, upload_handler, create_upload_file):
        """Test resource contention during concurrent uploads."""
        # Create multiple files that would compete for resources
        files = [create_upload_file(f"contention_{i}.txt", f"Content {i}" * 1000) for i in range(10)]
        
        # Mock document manager with realistic delays
        async def realistic_add_document(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return f"doc_{hash(args[0]) % 1000}"
        
        upload_handler.document_manager.add_document = realistic_add_document
        
        start_time = time.time()
        
        # Upload with controlled concurrency
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent uploads
        
        async def controlled_upload(file):
            async with semaphore:
                return await upload_handler.handle_upload(file)
        
        tasks = [controlled_upload(file) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        # All should succeed
        successful_uploads = [r for r in results if not isinstance(r, Exception) and r.success]
        assert len(successful_uploads) == 10
        
        # Should complete within reasonable time with controlled concurrency
        assert duration < 5.0

    @pytest.mark.slow
    def test_upload_memory_leak_detection(self, upload_handler, create_upload_file):
        """Test for memory leaks during repeated uploads."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Perform many uploads to detect leaks
        for i in range(50):
            test_file = create_upload_file(f"leak_test_{i}.txt", f"Content {i}" * 100)
            
            # Mock to avoid actual storage
            upload_handler.document_manager.add_document = AsyncMock(return_value=f"doc_{i}")
            
            # Run upload in event loop
            result = asyncio.run(upload_handler.handle_upload(test_file))
            assert result.success
            
            # Check memory every 10 uploads
            if i % 10 == 0:
                current_memory = process.memory_info().rss
                memory_increase = current_memory - initial_memory
                
                # Memory increase should be linear, not exponential (no major leaks)
                expected_max_increase = 20 * 1024 * 1024 * ((i // 10) + 1)  # 20MB per batch
                assert memory_increase < expected_max_increase
        
        # Final memory check
        final_memory = process.memory_info().rss
        total_increase = final_memory - initial_memory
        
        # Total increase should be reasonable (less than 200MB for 50 uploads)
        assert total_increase < 200 * 1024 * 1024


@pytest.mark.performance
class TestFileUploadPerformanceEdgeCases:
    """Performance edge case tests for file uploads."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_upload_throughput_measurement(self, upload_handler, create_upload_file, performance_config):
        """Measure upload throughput under various conditions."""
        file_sizes = [1, 5, 10, 50]  # MB
        results = {}
        
        for size_mb in file_sizes:
            large_file = create_upload_file(f"throughput_{size_mb}mb.txt", b"x" * (size_mb * 1024 * 1024))
            
            # Mock processing
            upload_handler.document_manager.add_document = AsyncMock(return_value=f"doc_{size_mb}")
            
            start_time = time.time()
            result = await upload_handler.handle_upload(large_file)
            duration = time.time() - start_time
            
            assert result.success
            
            throughput_mbps = size_mb / duration
            results[size_mb] = {
                'duration': duration,
                'throughput_mbps': throughput_mbps
            }
            
            # Basic performance assertions
            assert duration < performance_config["upload_timeout"]
            assert throughput_mbps > 1.0  # At least 1 MB/s
        
        # Log performance results for analysis
        print(f"Upload Performance Results: {results}")

    @pytest.mark.asyncio 
    async def test_upload_latency_under_load(self, upload_handler, create_upload_file):
        """Test upload latency when system is under load."""
        # Create background load
        background_tasks = []
        
        async def background_work():
            """Simulate background system load."""
            for _ in range(1000):
                await asyncio.sleep(0.001)
                # Simulate CPU work
                sum(range(1000))
        
        # Start background load
        for _ in range(5):
            background_tasks.append(asyncio.create_task(background_work()))
        
        try:
            # Test upload latency under load
            test_file = create_upload_file("latency_test.txt", b"Latency test content" * 100)
            upload_handler.document_manager.add_document = AsyncMock(return_value="doc_latency")
            
            start_time = time.time()
            result = await upload_handler.handle_upload(test_file)
            latency = time.time() - start_time
            
            assert result.success
            # Latency should still be reasonable under load
            assert latency < 2.0
            
        finally:
            # Cleanup background tasks
            for task in background_tasks:
                task.cancel()
            
            await asyncio.gather(*background_tasks, return_exceptions=True)

    @pytest.mark.asyncio
    async def test_upload_queue_saturation(self, upload_handler, create_upload_file):
        """Test behavior when upload queue becomes saturated."""
        # Create many upload requests simultaneously
        files = [create_upload_file(f"queue_test_{i}.txt", f"Queue test {i}".encode()) for i in range(20)]
        
        # Mock with realistic processing time
        async def slow_processing(*args, **kwargs):
            await asyncio.sleep(0.2)  # 200ms processing time
            return f"doc_{hash(str(args)) % 1000}"
        
        upload_handler.document_manager.add_document = slow_processing
        
        start_time = time.time()
        
        # Launch all uploads simultaneously
        tasks = [upload_handler.handle_upload(file) for file in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        # Check results
        successful_uploads = [r for r in results if not isinstance(r, Exception) and r.success]
        failed_uploads = [r for r in results if isinstance(r, Exception) or not r.success]
        
        # Most should succeed, some might fail due to resource limits
        assert len(successful_uploads) >= 15  # At least 75% success rate
        
        if failed_uploads:
            # Failed uploads should be due to resource exhaustion, not bugs
            for failure in failed_uploads:
                if isinstance(failure, ApplicationError):
                    assert failure.category in [ErrorCategory.SYSTEM, ErrorCategory.TIMEOUT]
        
        print(f"Queue saturation test: {len(successful_uploads)}/{len(files)} succeeded in {duration:.2f}s")