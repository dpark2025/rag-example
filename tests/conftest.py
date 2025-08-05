"""
Global pytest configuration and fixtures for RAG System testing.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-04
"""

import pytest
import tempfile
import shutil
import os
import asyncio
from typing import Dict, Any, List, AsyncGenerator
from unittest.mock import Mock, AsyncMock
import chromadb
from chromadb.config import Settings
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import application components for testing
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.rag_backend import LocalRAGSystem, LocalLLMClient
from app.document_manager import DocumentManager, DocumentMetadata, DocumentFilter
from app.upload_handler import UploadHandler, UploadTask, UploadStatus
from app.error_handlers import ApplicationError, ErrorCategory, ErrorSeverity


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_data_directory():
    """Provide path to test data directory."""
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'documents')


# ChromaDB and Database Fixtures

@pytest.fixture
def clean_chromadb():
    """Provide clean in-memory ChromaDB instance for each test."""
    client = chromadb.Client(Settings(
        persist_directory=":memory:",
        is_persistent=False,
        allow_reset=True
    ))
    yield client
    try:
        client.reset()
    except Exception:
        pass  # Memory client cleanup is automatic


@pytest.fixture
def mock_llm_client():
    """Provide mock LLM client for testing."""
    mock_client = Mock(spec=LocalLLMClient)
    mock_client.chat.return_value = "Test response from LLM."
    mock_client.health_check.return_value = True
    mock_client.base_url = "http://localhost:11434"
    return mock_client


@pytest.fixture
def rag_system(clean_chromadb, temp_directory, mock_llm_client):
    """Provide RAG system with clean database and mock LLM."""
    system = LocalRAGSystem(
        llm_client=mock_llm_client,
        data_path=temp_directory
    )
    system.chroma_client = clean_chromadb
    system.collection = clean_chromadb.get_or_create_collection("rag_documents")
    return system


@pytest.fixture
def document_manager(rag_system):
    """Provide document manager instance with clean database."""
    manager = DocumentManager()
    # Override the RAG system to use the clean test instance
    manager.rag_system = rag_system
    return manager


@pytest.fixture
def upload_handler():
    """Provide upload handler instance."""
    return UploadHandler()


# Test Data Fixtures

@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return """
    This is a sample document for testing the RAG system.
    It contains multiple paragraphs with various information.
    
    The document discusses artificial intelligence and machine learning.
    These technologies are transforming how we process information.
    
    Key topics include:
    - Natural language processing
    - Document retrieval systems
    - Embedding technologies
    - Vector databases
    
    This content should be sufficient for testing chunking,
    embedding generation, and retrieval functionality.
    """


@pytest.fixture
def sample_documents(sample_text_content):
    """Sample documents for testing."""
    return [
        {
            "title": "AI Overview",
            "content": sample_text_content,
            "source": "test_document_1",
            "file_type": "txt",
            "doc_id": "test_doc_1"
        },
        {
            "title": "Machine Learning Basics",
            "content": "Machine learning is a subset of AI that focuses on algorithms.",
            "source": "test_document_2", 
            "file_type": "txt",
            "doc_id": "test_doc_2"
        },
        {
            "title": "Vector Databases",
            "content": "Vector databases store high-dimensional vectors for similarity search.",
            "source": "test_document_3",
            "file_type": "txt", 
            "doc_id": "test_doc_3"
        }
    ]


@pytest.fixture
def rag_system_with_documents(temp_directory, mock_llm_client, sample_documents):
    """RAG system pre-loaded with test documents - separate instance."""
    # Create a separate ChromaDB client for this fixture
    test_client = chromadb.Client(Settings(
        persist_directory=":memory:",
        is_persistent=False,
        allow_reset=True
    ))
    
    system = LocalRAGSystem(
        llm_client=mock_llm_client,
        data_path=temp_directory
    )
    system.chroma_client = test_client
    system.collection = test_client.get_or_create_collection("rag_documents_with_data")
    system.add_documents(sample_documents)
    
    yield system
    
    # Cleanup
    try:
        test_client.reset()
    except Exception:
        pass


@pytest.fixture
def sample_upload_file():
    """Create a sample upload file for testing."""
    from fastapi import UploadFile
    from io import BytesIO
    
    content = b"Sample file content for upload testing."
    file_obj = BytesIO(content)
    
    upload_file = UploadFile(
        file=file_obj,
        filename="sample.txt",
        size=len(content)
    )
    return upload_file


@pytest.fixture
def large_upload_file():
    """Create a large upload file for performance testing."""
    from fastapi import UploadFile
    from io import BytesIO
    
    # Generate 1MB of test content
    content = b"This is test content. " * 50000  # ~1MB
    file_obj = BytesIO(content)
    
    upload_file = UploadFile(
        file=file_obj,
        filename="large_file.txt",
        size=len(content)
    )
    return upload_file


# HTTP Client Fixtures

@pytest.fixture
async def async_client():
    """Provide async HTTP client for API testing."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
def fastapi_app():
    """Provide FastAPI app instance for testing."""
    from main import app
    return app


@pytest.fixture
def test_client(fastapi_app):
    """Provide FastAPI test client."""
    return TestClient(fastapi_app)


# Mock Service Fixtures

@pytest.fixture
def mock_pdf_processor():
    """Mock PDF processor for testing."""
    mock_processor = Mock()
    mock_processor.process_pdf.return_value = Mock(
        success=True,
        text="Extracted PDF text content",
        metadata=Mock(
            page_count=3,
            title="Test PDF",
            to_dict=lambda: {"page_count": 3, "title": "Test PDF"}
        ),
        extraction_method="text_extraction",
        quality_score=0.95,
        error_message=""
    )
    return mock_processor


@pytest.fixture
def mock_document_intelligence():
    """Mock document intelligence service."""
    mock_intelligence = Mock()
    mock_intelligence.analyze_document.return_value = Mock(
        document_type=Mock(value="plain_text"),
        structure=Mock(value="unstructured"),
        confidence=0.85,
        suggested_chunk_size=400,
        suggested_overlap=50,
        processing_notes=["Document analyzed successfully"],
        features=Mock(__dict__={"has_headers": False, "has_lists": True})
    )
    return mock_intelligence


# Error Testing Fixtures

@pytest.fixture
def sample_application_error():
    """Sample application error for testing error handling."""
    return ApplicationError(
        message="Test error occurred",
        category=ErrorCategory.PROCESSING,
        severity=ErrorSeverity.MEDIUM,
        user_message="A test error occurred. Please try again.",
        recovery_action="retry"
    )


# Performance Testing Fixtures

@pytest.fixture
def performance_config():
    """Configuration for performance testing."""
    return {
        "upload_timeout": 30.0,
        "api_response_timeout": 0.2,
        "max_file_size": 100 * 1024 * 1024,  # 100MB
        "concurrent_uploads": 5,
        "memory_limit_mb": 512
    }


# WebSocket Testing Fixtures

@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing real-time features."""
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


# Database State Fixtures

@pytest.fixture
def document_metadata_samples():
    """Sample document metadata for database testing."""
    return [
        DocumentMetadata(
            doc_id="meta_doc_1",
            title="Sample Document 1",
            file_type="txt",
            file_size=1024,
            upload_timestamp="2025-08-04T10:00:00Z",
            chunk_count=3,
            status="ready",
            last_modified="2025-08-04T10:00:00Z"
        ),
        DocumentMetadata(
            doc_id="meta_doc_2", 
            title="Sample Document 2",
            file_type="pdf",
            file_size=2048,
            upload_timestamp="2025-08-04T11:00:00Z",
            chunk_count=5,
            status="processing",
            last_modified="2025-08-04T11:00:00Z"
        )
    ]


# Utility Functions for Tests

@pytest.fixture
def create_test_file():
    """Utility function to create test files."""
    def _create_file(filename: str, content: str, temp_dir: str):
        filepath = os.path.join(temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    return _create_file


@pytest.fixture
def assert_performance():
    """Utility for asserting performance requirements."""
    def _assert_performance(duration: float, max_duration: float, operation: str):
        assert duration <= max_duration, (
            f"{operation} took {duration:.2f}s, exceeding limit of {max_duration}s"
        )
    return _assert_performance


# Cleanup Fixtures

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatic cleanup after each test."""
    yield
    # Cleanup any remaining test data
    import gc
    gc.collect()


# Markers for test categorization

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interaction"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests for complete workflows"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and load tests"
    )
    config.addinivalue_line(
        "markers", "accessibility: Accessibility compliance tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests that take >10 seconds"
    )


# Skip conditions for CI/CD

@pytest.fixture
def skip_if_no_ollama():
    """Skip test if Ollama is not available."""
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            pytest.skip("Ollama not available")
    except Exception:
        pytest.skip("Ollama not available")


@pytest.fixture
def skip_if_no_chromadb():
    """Skip test if ChromaDB is not available."""
    try:
        import chromadb
        client = chromadb.Client()
        client.heartbeat()
    except Exception:
        pytest.skip("ChromaDB not available")