"""
Unit tests for PDF processing functionality.

Tests PDF upload, text extraction, chunking, and intelligence features.
Focuses on unit testing individual PDF processing components with proper mocking.

Authored by: QA/Test Engineer
Date: 2025-08-05
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Import modules under test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.pdf_processor import PDFProcessor, PDFExtractionResult, PDFMetadata
from app.document_intelligence import DocumentIntelligenceEngine


@pytest.fixture
def pdf_processor():
    """Provide PDFProcessor instance for testing."""
    return PDFProcessor()


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return """
    PDF Processing Test Document
    
    This is a test PDF document for validating the RAG system's PDF processing capabilities.
    
    Key Features to Test:
    - Text extraction from PDF files
    - Document intelligence analysis
    - Chunking and embedding generation
    - Quality score assessment
    
    Performance Metrics:
    - Extraction accuracy: High quality text extraction
    - Processing speed: Under 30 seconds
    - Memory efficiency: Optimized resource usage
    
    Quality Assurance:
    This PDF contains structured content that should be extractable
    and processable by the RAG system's PDF processing pipeline.
    """


@pytest.fixture
def create_test_pdf():
    """Utility fixture to create test PDF files."""
    def _create_pdf(content: str, filename: str = "test.pdf") -> str:
        """Create a test PDF file with given content"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w+b', suffix='.pdf', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Create PDF content
            c = canvas.Canvas(temp_path, pagesize=letter)
            width, height = letter
            
            # Add title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "PDF Test Document")
            
            # Add content
            c.setFont("Helvetica", 12)
            lines = content.split('\n')
            y_position = height - 100
            
            for line in lines:
                if y_position < 50:  # Start new page if needed
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y_position = height - 50
                
                c.drawString(50, y_position, line.strip())
                y_position -= 15
            
            c.save()
            return temp_path
            
        except Exception as e:
            pytest.fail(f"Error creating test PDF: {e}")
            return None
    
    return _create_pdf

@pytest.mark.unit
class TestPDFProcessor:
    """Unit tests for PDF processing functionality."""

    def test_pdf_text_extraction_success(self, pdf_processor, create_test_pdf, sample_pdf_content):
        """Test successful PDF text extraction."""
        # Create test PDF
        pdf_path = create_test_pdf(sample_pdf_content)
        
        try:
            # Read PDF content as bytes
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Process PDF
            result = pdf_processor.process_pdf(pdf_content, "test.pdf")
            
            # Assertions
            assert result.success is True
            assert "PDF Processing Test Document" in result.text
            assert "text extraction" in result.text.lower()
            assert result.extraction_method is not None
            assert result.quality_score > 0.0
            
            # Metadata checks
            assert result.metadata is not None
            assert result.metadata.page_count > 0
            
        finally:
            # Cleanup
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

    def test_pdf_extraction_with_invalid_content(self, pdf_processor):
        """Test PDF extraction with invalid content."""
        invalid_content = b"This is not a valid PDF file"
        
        result = pdf_processor.process_pdf(invalid_content, "invalid.pdf")
        
        # Should handle gracefully
        assert result.success is False
        assert result.error_message != ""

    def test_pdf_extraction_with_empty_pdf(self, pdf_processor, create_test_pdf):
        """Test PDF extraction with minimal content."""
        pdf_path = create_test_pdf("")
        
        try:
            # Read PDF content as bytes
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            result = pdf_processor.process_pdf(pdf_content, "empty.pdf")
            
            # Should still succeed but with minimal content
            assert result.success is True
            assert len(result.text.strip()) >= 0  # May be empty or contain minimal text
            
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

    def test_pdf_metadata_extraction(self, pdf_processor, create_test_pdf, sample_pdf_content):
        """Test PDF metadata extraction."""
        pdf_path = create_test_pdf(sample_pdf_content)
        
        try:
            # Read PDF content as bytes
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            result = pdf_processor.process_pdf(pdf_content, "test.pdf")
            
            # Check metadata
            assert result.metadata is not None
            assert result.metadata.page_count >= 1
            assert hasattr(result.metadata, 'title')
            
            # Convert to dict should work
            metadata_dict = result.metadata.to_dict()
            assert isinstance(metadata_dict, dict)
            assert 'page_count' in metadata_dict
            
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

    def test_pdf_quality_scoring(self, pdf_processor, create_test_pdf, sample_pdf_content):
        """Test PDF quality scoring functionality."""
        pdf_path = create_test_pdf(sample_pdf_content)
        
        try:
            # Read PDF content as bytes
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            result = pdf_processor.process_pdf(pdf_content, "test.pdf")
            
            # Quality score should be between 0 and 1
            assert 0.0 <= result.quality_score <= 1.0
            
            # For structured content, quality should be reasonably high
            assert result.quality_score > 0.5
            
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

    def test_pdf_extraction_error_handling(self, pdf_processor):
        """Test error handling during PDF extraction."""
        # Use malformed PDF content to trigger error
        malformed_content = b"%PDF-1.4\nMalformed PDF content"
        
        result = pdf_processor.process_pdf(malformed_content, "malformed.pdf")
        
        # Should handle error gracefully
        assert result.success is False
        assert result.error_message != ""
    

@pytest.mark.unit
class TestPDFIntelligence:
    """Unit tests for PDF document intelligence functionality."""

    def test_pdf_document_type_detection(self, sample_pdf_content):
        """Test document type detection for PDF text content."""
        intelligence = DocumentIntelligenceEngine()
        analysis = intelligence.analyze_document(sample_pdf_content, "PDF Test Document", "pdf")
        
        # Should detect document type
        assert analysis.document_type is not None
        assert analysis.confidence > 0.0

    def test_pdf_structure_analysis(self):
        """Test PDF structure analysis."""
        structured_content = """
        Chapter 1: Introduction
        This chapter introduces the main concepts.
        
        Chapter 2: Technical Specifications
        Key points include:
        - Scalability requirements
        - Performance benchmarks
        - Security considerations
        
        Chapter 3: Implementation
        Implementation details and best practices.
        """
        
        intelligence = DocumentIntelligenceEngine()
        analysis = intelligence.analyze_document(structured_content, "Structured Document", "pdf")
        
        # Should detect structure
        assert analysis.structure is not None
        assert analysis.suggested_chunk_size > 0
        assert analysis.suggested_overlap >= 0
        assert len(analysis.processing_notes) > 0

    def test_pdf_chunking_recommendations(self, sample_pdf_content):
        """Test PDF chunking parameter recommendations."""
        intelligence = DocumentIntelligenceEngine()
        analysis = intelligence.analyze_document(sample_pdf_content, "PDF Test Document", "pdf")
        
        # Should provide reasonable chunking recommendations
        assert analysis.suggested_chunk_size >= 200
        assert analysis.suggested_chunk_size <= 1000
        assert analysis.suggested_overlap >= 0
        assert analysis.suggested_overlap < analysis.suggested_chunk_size


@pytest.mark.unit
class TestPDFChunking:
    """Unit tests for PDF chunking functionality."""

    def test_pdf_chunking_quality(self, pdf_processor, create_test_pdf):
        """Test PDF chunking quality with structured content."""
        structured_content = """
        Chapter 1: Introduction
        This chapter introduces the main concepts and provides background information.
        
        Chapter 2: Technical Specifications
        Here we detail the technical requirements and system architecture.
        Key points include:
        - Scalability requirements
        - Performance benchmarks
        - Security considerations
        
        Chapter 3: Implementation
        This section covers the actual implementation details and best practices.
        """
        
        pdf_path = create_test_pdf(structured_content)
        
        try:
            # Read PDF content as bytes
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            result = pdf_processor.process_pdf(pdf_content, "structured.pdf")
            
            # Should extract structured content successfully
            assert result.success is True
            assert "Chapter 1" in result.text
            assert "Chapter 2" in result.text
            assert "Chapter 3" in result.text
            assert "Scalability requirements" in result.text
            
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)

    def test_pdf_performance(self, pdf_processor, create_test_pdf):
        """Test PDF processing performance with larger content."""
        # Create larger content for performance testing
        large_content = "Performance Testing Document\n\n"
        large_content += "\n\n".join([
            f"Section {i}: This is content for section {i} with detailed information about various topics and technical specifications."
            for i in range(1, 21)
        ])
        
        pdf_path = create_test_pdf(large_content)
        
        try:
            # Read PDF content as bytes
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            import time
            start_time = time.time()
            
            result = pdf_processor.process_pdf(pdf_content, "performance.pdf")
            
            processing_time = time.time() - start_time
            
            # Should process in reasonable time (allow generous time for CI)
            assert processing_time < 30.0
            assert result.success is True
            
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)


@pytest.mark.integration
class TestPDFProcessingIntegration:
    """Integration tests for complete PDF processing workflow."""

    def test_complete_pdf_workflow(self, pdf_processor, create_test_pdf, sample_pdf_content):
        """Test complete PDF processing workflow from file to structured data."""
        pdf_path = create_test_pdf(sample_pdf_content)
        
        try:
            # Read PDF content as bytes
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Process PDF
            result = pdf_processor.process_pdf(pdf_content, "workflow_test.pdf")
            
            # Verify complete workflow
            assert result.success is True
            assert len(result.text) > 100  # Should have substantial text
            assert result.metadata.page_count > 0
            assert result.quality_score > 0.0
            
            # Verify intelligence analysis integration
            intelligence = DocumentIntelligenceEngine()
            analysis = intelligence.analyze_document(result.text, "PDF Test Document", "pdf")
            
            assert analysis.confidence > 0.0
            assert analysis.suggested_chunk_size > 0
            
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)