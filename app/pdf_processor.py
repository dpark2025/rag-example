"""
PDF Processing Engine for RAG System
Supports multiple PDF processing libraries for robust text extraction
"""

import logging
import fitz  # PyMuPDF
import pdfplumber
import PyPDF2
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class ExtractionMethod(Enum):
    PYMUPDF = "pymupdf"
    PDFPLUMBER = "pdfplumber"
    PYPDF2 = "pypdf2"
    AUTO = "auto"


@dataclass
class PDFMetadata:
    """PDF metadata information."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    page_count: int = 0
    file_size: int = 0
    has_images: bool = False
    has_tables: bool = False
    language: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'title': self.title,
            'author': self.author,
            'subject': self.subject,
            'creator': self.creator,
            'producer': self.producer,
            'creation_date': self.creation_date.isoformat() if self.creation_date else None,
            'modification_date': self.modification_date.isoformat() if self.modification_date else None,
            'page_count': self.page_count,
            'file_size': self.file_size,
            'has_images': self.has_images,
            'has_tables': self.has_tables,
            'language': self.language
        }


@dataclass
class PDFPage:
    """Represents a single PDF page with extracted content."""
    page_number: int
    text: str
    word_count: int
    char_count: int
    has_images: bool = False
    has_tables: bool = False
    extraction_quality: float = 0.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'page_number': self.page_number,
            'text': self.text,
            'word_count': self.word_count,
            'char_count': self.char_count,
            'has_images': self.has_images,
            'has_tables': self.has_tables,
            'extraction_quality': self.extraction_quality
        }


@dataclass
class PDFExtractionResult:
    """Complete PDF extraction result."""
    success: bool
    text: str
    metadata: PDFMetadata
    pages: List[PDFPage]
    extraction_method: ExtractionMethod
    processing_time: float
    quality_score: float
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'success': self.success,
            'text': self.text,
            'metadata': self.metadata.to_dict(),
            'pages': [page.to_dict() for page in self.pages],
            'extraction_method': self.extraction_method.value,
            'processing_time': self.processing_time,
            'quality_score': self.quality_score,
            'error_message': self.error_message
        }


class PDFProcessor:
    """
    Advanced PDF processing engine with multiple extraction strategies.
    
    Features:
    - Multiple extraction libraries (PyMuPDF, pdfplumber, PyPDF2)
    - Automatic fallback between methods
    - Metadata extraction
    - Quality assessment
    - Table and image detection
    """
    
    def __init__(self):
        self.extraction_methods = [
            ExtractionMethod.PYMUPDF,
            ExtractionMethod.PDFPLUMBER,
            ExtractionMethod.PYPDF2
        ]
    
    def process_pdf(self, pdf_content: bytes, filename: str = "unknown.pdf", 
                   method: ExtractionMethod = ExtractionMethod.AUTO) -> PDFExtractionResult:
        """
        Process PDF content and extract text, metadata, and structure.
        
        Args:
            pdf_content: PDF file content as bytes
            filename: Original filename for reference
            method: Extraction method to use
            
        Returns:
            PDFExtractionResult with all extracted information
        """
        start_time = datetime.now()
        
        if method == ExtractionMethod.AUTO:
            # Try methods in order of preference
            for extraction_method in self.extraction_methods:
                try:
                    result = self._extract_with_method(pdf_content, filename, extraction_method)
                    if result.success and result.quality_score > 0.3:
                        processing_time = (datetime.now() - start_time).total_seconds()
                        result.processing_time = processing_time
                        return result
                except Exception as e:
                    logger.warning(f"Extraction method {extraction_method.value} failed: {e}")
                    continue
            
            # If all methods failed, return error result
            return PDFExtractionResult(
                success=False,
                text="",
                metadata=PDFMetadata(),
                pages=[],
                extraction_method=ExtractionMethod.AUTO,
                processing_time=(datetime.now() - start_time).total_seconds(),
                quality_score=0.0,
                error_message="All extraction methods failed"
            )
        else:
            result = self._extract_with_method(pdf_content, filename, method)
            result.processing_time = (datetime.now() - start_time).total_seconds()
            return result
    
    def _extract_with_method(self, pdf_content: bytes, filename: str, 
                           method: ExtractionMethod) -> PDFExtractionResult:
        """Extract PDF content using specified method."""
        try:
            if method == ExtractionMethod.PYMUPDF:
                return self._extract_with_pymupdf(pdf_content, filename)
            elif method == ExtractionMethod.PDFPLUMBER:
                return self._extract_with_pdfplumber(pdf_content, filename)
            elif method == ExtractionMethod.PYPDF2:
                return self._extract_with_pypdf2(pdf_content, filename)
            else:
                raise ValueError(f"Unsupported extraction method: {method}")
                
        except Exception as e:
            logger.error(f"PDF extraction failed with {method.value}: {e}")
            return PDFExtractionResult(
                success=False,
                text="",
                metadata=PDFMetadata(file_size=len(pdf_content)),
                pages=[],
                extraction_method=method,
                processing_time=0.0,
                quality_score=0.0,
                error_message=str(e)
            )
    
    def _extract_with_pymupdf(self, pdf_content: bytes, filename: str) -> PDFExtractionResult:
        """Extract using PyMuPDF (fitz) - best for complex layouts."""
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        
        # Extract metadata
        metadata = self._extract_pymupdf_metadata(doc, len(pdf_content))
        
        # Extract text from all pages
        pages = []
        full_text = ""
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            
            # Quality assessment
            quality = self._assess_text_quality(page_text)
            
            # Detect images and tables
            has_images = len(page.get_images()) > 0
            has_tables = self._detect_tables_pymupdf(page)
            
            pdf_page = PDFPage(
                page_number=page_num + 1,
                text=page_text,
                word_count=len(page_text.split()),
                char_count=len(page_text),
                has_images=has_images,
                has_tables=has_tables,
                extraction_quality=quality
            )
            
            pages.append(pdf_page)
            full_text += page_text + "\n\n"
        
        doc.close()
        
        # Overall quality assessment
        overall_quality = sum(p.extraction_quality for p in pages) / len(pages) if pages else 0.0
        
        return PDFExtractionResult(
            success=True,
            text=full_text.strip(),
            metadata=metadata,
            pages=pages,
            extraction_method=ExtractionMethod.PYMUPDF,
            processing_time=0.0,  # Will be set by caller
            quality_score=overall_quality
        )
    
    def _extract_with_pdfplumber(self, pdf_content: bytes, filename: str) -> PDFExtractionResult:
        """Extract using pdfplumber - best for tables and structured content."""
        import io
        
        pdf_file = io.BytesIO(pdf_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            # Extract metadata
            metadata = self._extract_pdfplumber_metadata(pdf, len(pdf_content))
            
            # Extract text from all pages
            pages = []
            full_text = ""
            
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                
                # Quality assessment
                quality = self._assess_text_quality(page_text)
                
                # Detect tables and images
                tables = page.extract_tables()
                has_tables = len(tables) > 0
                has_images = len(page.images) > 0
                
                pdf_page = PDFPage(
                    page_number=page_num + 1,
                    text=page_text,
                    word_count=len(page_text.split()),
                    char_count=len(page_text),
                    has_images=has_images,
                    has_tables=has_tables,
                    extraction_quality=quality
                )
                
                pages.append(pdf_page)
                full_text += page_text + "\n\n"
        
        # Overall quality assessment
        overall_quality = sum(p.extraction_quality for p in pages) / len(pages) if pages else 0.0
        
        return PDFExtractionResult(
            success=True,
            text=full_text.strip(),
            metadata=metadata,
            pages=pages,
            extraction_method=ExtractionMethod.PDFPLUMBER,
            processing_time=0.0,  # Will be set by caller
            quality_score=overall_quality
        )
    
    def _extract_with_pypdf2(self, pdf_content: bytes, filename: str) -> PDFExtractionResult:
        """Extract using PyPDF2 - fallback method."""
        import io
        
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract metadata
        metadata = self._extract_pypdf2_metadata(pdf_reader, len(pdf_content))
        
        # Extract text from all pages
        pages = []
        full_text = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                
                # Quality assessment
                quality = self._assess_text_quality(page_text)
                
                pdf_page = PDFPage(
                    page_number=page_num + 1,
                    text=page_text,
                    word_count=len(page_text.split()),
                    char_count=len(page_text),
                    has_images=False,  # PyPDF2 doesn't easily detect images
                    has_tables=False,  # PyPDF2 doesn't easily detect tables
                    extraction_quality=quality
                )
                
                pages.append(pdf_page)
                full_text += page_text + "\n\n"
                
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                continue
        
        # Overall quality assessment
        overall_quality = sum(p.extraction_quality for p in pages) / len(pages) if pages else 0.0
        
        return PDFExtractionResult(
            success=True,
            text=full_text.strip(),
            metadata=metadata,
            pages=pages,
            extraction_method=ExtractionMethod.PYPDF2,
            processing_time=0.0,  # Will be set by caller
            quality_score=overall_quality
        )
    
    def _extract_pymupdf_metadata(self, doc, file_size: int) -> PDFMetadata:
        """Extract metadata using PyMuPDF."""
        metadata_dict = doc.metadata
        
        return PDFMetadata(
            title=metadata_dict.get('title'),
            author=metadata_dict.get('author'),
            subject=metadata_dict.get('subject'),
            creator=metadata_dict.get('creator'),
            producer=metadata_dict.get('producer'),
            creation_date=self._parse_pdf_date(metadata_dict.get('creationDate')),
            modification_date=self._parse_pdf_date(metadata_dict.get('modDate')),
            page_count=doc.page_count,
            file_size=file_size,
            has_images=any(doc.load_page(i).get_images() for i in range(min(3, doc.page_count))),
            has_tables=False  # Would need more complex detection
        )
    
    def _extract_pdfplumber_metadata(self, pdf, file_size: int) -> PDFMetadata:
        """Extract metadata using pdfplumber."""
        metadata = pdf.metadata or {}
        
        return PDFMetadata(
            title=metadata.get('Title'),
            author=metadata.get('Author'),
            subject=metadata.get('Subject'),
            creator=metadata.get('Creator'),
            producer=metadata.get('Producer'),
            creation_date=self._parse_pdf_date(metadata.get('CreationDate')),
            modification_date=self._parse_pdf_date(metadata.get('ModDate')),
            page_count=len(pdf.pages),
            file_size=file_size,
            has_images=any(len(page.images) > 0 for page in pdf.pages[:3]),
            has_tables=any(len(page.extract_tables()) > 0 for page in pdf.pages[:3])
        )
    
    def _extract_pypdf2_metadata(self, pdf_reader, file_size: int) -> PDFMetadata:
        """Extract metadata using PyPDF2."""
        metadata = pdf_reader.metadata or {}
        
        return PDFMetadata(
            title=metadata.get('/Title'),
            author=metadata.get('/Author'),
            subject=metadata.get('/Subject'),
            creator=metadata.get('/Creator'),
            producer=metadata.get('/Producer'),
            creation_date=self._parse_pdf_date(metadata.get('/CreationDate')),
            modification_date=self._parse_pdf_date(metadata.get('/ModDate')),
            page_count=len(pdf_reader.pages),
            file_size=file_size
        )
    
    def _parse_pdf_date(self, date_str: str) -> Optional[datetime]:
        """Parse PDF date string to datetime."""
        if not date_str:
            return None
            
        try:
            # PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
            if date_str.startswith('D:'):
                date_str = date_str[2:]
            
            # Extract just the basic date part (YYYYMMDDHHMMSS)
            date_part = re.match(r'(\d{14})', date_str)
            if date_part:
                return datetime.strptime(date_part.group(1), '%Y%m%d%H%M%S')
            
            # Try simpler format
            date_part = re.match(r'(\d{8})', date_str)
            if date_part:
                return datetime.strptime(date_part.group(1), '%Y%m%d')
                
        except Exception as e:
            logger.warning(f"Failed to parse PDF date '{date_str}': {e}")
        
        return None
    
    def _assess_text_quality(self, text: str) -> float:
        """
        Assess the quality of extracted text.
        
        Returns a score from 0.0 to 1.0 where:
        - 1.0 = Perfect extraction
        - 0.5-0.9 = Good extraction with minor issues
        - 0.1-0.4 = Poor extraction with major issues
        - 0.0 = No usable text
        """
        if not text or len(text.strip()) == 0:
            return 0.0
        
        # Basic metrics
        char_count = len(text)
        word_count = len(text.split())
        line_count = len([line for line in text.split('\n') if line.strip()])
        
        if word_count == 0:
            return 0.0
        
        # Quality indicators
        quality_score = 0.5  # Base score
        
        # Average word length (good text has reasonable word lengths)
        avg_word_length = char_count / word_count
        if 3 <= avg_word_length <= 8:
            quality_score += 0.2
        elif avg_word_length < 2:
            quality_score -= 0.3  # Likely extraction artifacts
        
        # Ratio of letters to total characters
        letter_count = sum(1 for c in text if c.isalpha())
        letter_ratio = letter_count / char_count if char_count > 0 else 0
        if letter_ratio > 0.6:
            quality_score += 0.2
        elif letter_ratio < 0.3:
            quality_score -= 0.3
        
        # Check for extraction artifacts
        artifact_patterns = [
            r'[^\w\s]{10,}',  # Long sequences of special characters
            r'\s{5,}',        # Long sequences of spaces
            r'(.)\1{10,}',    # Repeated characters
        ]
        
        for pattern in artifact_patterns:
            if re.search(pattern, text):
                quality_score -= 0.1
        
        # Reasonable line length distribution
        line_lengths = [len(line.strip()) for line in text.split('\n') if line.strip()]
        if line_lengths:
            avg_line_length = sum(line_lengths) / len(line_lengths)
            if 20 <= avg_line_length <= 200:
                quality_score += 0.1
        
        return max(0.0, min(1.0, quality_score))
    
    def _detect_tables_pymupdf(self, page) -> bool:
        """Detect tables in a PyMuPDF page (basic heuristic)."""
        try:
            # Look for table-like structures
            text = page.get_text()
            
            # Simple heuristics for table detection
            lines = text.split('\n')
            
            # Check for lines with multiple whitespace-separated columns
            potential_table_lines = 0
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Count significant whitespace gaps (potential column separators)
                parts = [part for part in re.split(r'\s{2,}', line) if part.strip()]
                if len(parts) >= 3:  # At least 3 columns
                    potential_table_lines += 1
            
            # If more than 20% of non-empty lines look like table rows
            non_empty_lines = len([line for line in lines if line.strip()])
            if non_empty_lines > 0:
                table_ratio = potential_table_lines / non_empty_lines
                return table_ratio > 0.2
            
        except Exception as e:
            logger.warning(f"Error detecting tables: {e}")
        
        return False


# Global PDF processor instance
pdf_processor = PDFProcessor()