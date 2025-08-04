"""
Document Intelligence Engine for RAG System
Provides enhanced document type detection and content analysis
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Enhanced document type classification."""
    PLAIN_TEXT = "plain_text"
    TECHNICAL_MANUAL = "technical_manual"
    RESEARCH_PAPER = "research_paper"
    LEGAL_DOCUMENT = "legal_document"
    FINANCIAL_REPORT = "financial_report"
    NEWS_ARTICLE = "news_article"
    EMAIL = "email"
    CODE_DOCUMENTATION = "code_documentation"
    MEETING_NOTES = "meeting_notes"
    PRESENTATION = "presentation"
    UNKNOWN = "unknown"


class ContentStructure(Enum):
    """Document structural patterns."""
    HIERARCHICAL = "hierarchical"       # Clear heading structure
    LINEAR = "linear"                   # Sequential paragraphs
    TABULAR = "tabular"                 # Table-heavy content
    LIST_HEAVY = "list_heavy"          # Many lists and bullets
    MIXED = "mixed"                     # Multiple structures
    UNSTRUCTURED = "unstructured"      # No clear structure


@dataclass
class DocumentFeatures:
    """Document content features for classification."""
    # Length metrics
    char_count: int = 0
    word_count: int = 0
    line_count: int = 0
    paragraph_count: int = 0
    
    # Structure metrics
    heading_count: int = 0
    list_count: int = 0
    table_indicators: int = 0
    code_blocks: int = 0
    
    # Content patterns
    has_citations: bool = False
    has_legal_terms: bool = False
    has_financial_terms: bool = False
    has_technical_terms: bool = False
    has_email_patterns: bool = False
    has_date_patterns: bool = False
    
    # Language patterns
    avg_sentence_length: float = 0.0
    avg_word_length: float = 0.0
    punctuation_density: float = 0.0
    capitalization_ratio: float = 0.0
    
    # Quality indicators
    readability_score: float = 0.0
    structure_score: float = 0.0
    completeness_score: float = 0.0


@dataclass
class DocumentIntelligenceResult:
    """Result of document intelligence analysis."""
    document_type: DocumentType
    structure: ContentStructure
    features: DocumentFeatures
    confidence: float
    suggested_chunk_size: int
    suggested_overlap: int
    processing_notes: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'document_type': self.document_type.value,
            'structure': self.structure.value,
            'features': {
                'char_count': self.features.char_count,
                'word_count': self.features.word_count,
                'line_count': self.features.line_count,
                'paragraph_count': self.features.paragraph_count,
                'heading_count': self.features.heading_count,
                'list_count': self.features.list_count,
                'table_indicators': self.features.table_indicators,
                'code_blocks': self.features.code_blocks,
                'has_citations': self.features.has_citations,
                'has_legal_terms': self.features.has_legal_terms,
                'has_financial_terms': self.features.has_financial_terms,
                'has_technical_terms': self.features.has_technical_terms,
                'has_email_patterns': self.features.has_email_patterns,
                'has_date_patterns': self.features.has_date_patterns,
                'avg_sentence_length': self.features.avg_sentence_length,
                'avg_word_length': self.features.avg_word_length,
                'punctuation_density': self.features.punctuation_density,
                'capitalization_ratio': self.features.capitalization_ratio,
                'readability_score': self.features.readability_score,
                'structure_score': self.features.structure_score,
                'completeness_score': self.features.completeness_score
            },
            'confidence': self.confidence,
            'suggested_chunk_size': self.suggested_chunk_size,
            'suggested_overlap': self.suggested_overlap,
            'processing_notes': self.processing_notes
        }


class DocumentIntelligenceEngine:
    """
    Advanced document analysis engine for intelligent content processing.
    
    Features:
    - Document type classification
    - Content structure analysis
    - Optimal chunking strategy recommendation
    - Quality assessment and completeness scoring
    """
    
    def __init__(self):
        self.technical_terms = {
            'api', 'database', 'server', 'client', 'algorithm', 'function',
            'method', 'class', 'object', 'variable', 'parameter', 'return',
            'exception', 'error', 'debug', 'test', 'unit', 'integration',
            'deployment', 'configuration', 'authentication', 'authorization'
        }
        
        self.legal_terms = {
            'whereas', 'therefore', 'herein', 'thereof', 'hereby', 'pursuant',
            'agreement', 'contract', 'clause', 'provision', 'party', 'parties',
            'jurisdiction', 'liability', 'damages', 'breach', 'compliance',
            'regulation', 'statute', 'law', 'legal', 'court', 'judgment'
        }
        
        self.financial_terms = {
            'revenue', 'profit', 'loss', 'assets', 'liabilities', 'equity',
            'cash', 'flow', 'balance', 'sheet', 'income', 'statement',
            'financial', 'accounting', 'audit', 'investment', 'return',
            'risk', 'portfolio', 'market', 'stock', 'bond', 'dividend'
        }
    
    def analyze_document(self, content: str, title: str = "", 
                        file_type: str = "txt") -> DocumentIntelligenceResult:
        """
        Perform comprehensive document analysis.
        
        Args:
            content: Document text content
            title: Document title/filename
            file_type: File type (txt, pdf, etc.)
            
        Returns:
            DocumentIntelligenceResult with analysis results
        """
        try:
            # Extract basic features
            features = self._extract_features(content)
            
            # Classify document type
            doc_type, type_confidence = self._classify_document_type(content, title, features)
            
            # Analyze structure
            structure = self._analyze_structure(content, features)
            
            # Calculate optimal chunking parameters
            chunk_size, overlap = self._calculate_chunking_params(doc_type, structure, features)
            
            # Generate processing notes
            notes = self._generate_processing_notes(doc_type, structure, features)
            
            # Overall confidence score
            confidence = self._calculate_confidence(type_confidence, features)
            
            return DocumentIntelligenceResult(
                document_type=doc_type,
                structure=structure,
                features=features,
                confidence=confidence,
                suggested_chunk_size=chunk_size,
                suggested_overlap=overlap,
                processing_notes=notes
            )
            
        except Exception as e:
            logger.error(f"Document intelligence analysis failed: {e}")
            # Return default analysis
            return self._default_analysis(content)
    
    def _extract_features(self, content: str) -> DocumentFeatures:
        """Extract comprehensive document features."""
        features = DocumentFeatures()
        
        if not content:
            return features
        
        # Basic metrics
        features.char_count = len(content)
        words = content.split()
        features.word_count = len(words)
        lines = content.split('\n')
        features.line_count = len(lines)
        
        # Paragraph detection (double newlines or significant line breaks)
        paragraphs = re.split(r'\n\s*\n', content.strip())
        features.paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # Structure detection
        features.heading_count = len(re.findall(r'^#+\s+.*$|^.+\n[=-]+\s*$', content, re.MULTILINE))
        features.list_count = len(re.findall(r'^\s*[-*+•]\s+.*$|^\s*\d+\.\s+.*$', content, re.MULTILINE))
        features.table_indicators = len(re.findall(r'\|.*\|', content)) + len(re.findall(r'\t.*\t', content))
        features.code_blocks = len(re.findall(r'```.*?```|`.*?`', content, re.DOTALL))
        
        # Content pattern detection
        features.has_citations = bool(re.search(r'\[[0-9]+\]|\([^)]*\d{4}[^)]*\)', content))
        features.has_legal_terms = self._contains_terms(content.lower(), self.legal_terms)
        features.has_financial_terms = self._contains_terms(content.lower(), self.financial_terms)
        features.has_technical_terms = self._contains_terms(content.lower(), self.technical_terms)
        features.has_email_patterns = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content))
        features.has_date_patterns = bool(re.search(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b', content))
        
        # Language analysis
        if words:
            features.avg_word_length = sum(len(word.strip('.,!?;:')) for word in words) / len(words)
        
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            sentence_lengths = [len(s.split()) for s in sentences]
            features.avg_sentence_length = statistics.mean(sentence_lengths)
        
        # Punctuation and capitalization
        punct_chars = sum(1 for c in content if c in '.,!?;:')
        features.punctuation_density = punct_chars / features.char_count if features.char_count > 0 else 0
        
        cap_chars = sum(1 for c in content if c.isupper())
        alpha_chars = sum(1 for c in content if c.isalpha())
        features.capitalization_ratio = cap_chars / alpha_chars if alpha_chars > 0 else 0
        
        # Quality scores
        features.readability_score = self._calculate_readability(features)
        features.structure_score = self._calculate_structure_score(features)
        features.completeness_score = self._calculate_completeness(content, features)
        
        return features
    
    def _contains_terms(self, text: str, terms: set) -> bool:
        """Check if text contains any of the specified terms."""
        words = set(re.findall(r'\b\w+\b', text.lower()))
        return len(words.intersection(terms)) >= 2  # At least 2 matching terms
    
    def _classify_document_type(self, content: str, title: str, 
                               features: DocumentFeatures) -> Tuple[DocumentType, float]:
        """Classify document type with confidence score."""
        scores = {}
        
        # Technical documentation patterns
        tech_score = 0.0
        if features.has_technical_terms:
            tech_score += 0.4
        if features.code_blocks > 0:
            tech_score += 0.3
        if re.search(r'\b(API|SDK|documentation|manual|guide)\b', title, re.IGNORECASE):
            tech_score += 0.3
        scores[DocumentType.CODE_DOCUMENTATION] = tech_score
        
        # Research paper patterns
        research_score = 0.0
        if features.has_citations:
            research_score += 0.4
        if re.search(r'\b(abstract|introduction|methodology|results|conclusion)\b', content, re.IGNORECASE):
            research_score += 0.3
        if features.heading_count >= 3:
            research_score += 0.2
        if re.search(r'\b(paper|study|research|analysis)\b', title, re.IGNORECASE):
            research_score += 0.1
        scores[DocumentType.RESEARCH_PAPER] = research_score
        
        # Legal document patterns  
        legal_score = 0.0
        if features.has_legal_terms:
            legal_score += 0.5
        if re.search(r'\b(agreement|contract|terms|conditions|legal|law)\b', title, re.IGNORECASE):
            legal_score += 0.3
        if features.avg_sentence_length > 25:  # Legal docs tend to have long sentences
            legal_score += 0.2
        scores[DocumentType.LEGAL_DOCUMENT] = legal_score
        
        # Financial report patterns
        financial_score = 0.0
        if features.has_financial_terms:
            financial_score += 0.4
        if features.table_indicators > 5:  # Financial reports often have tables
            financial_score += 0.3
        if re.search(r'\b(financial|report|quarterly|annual|earnings)\b', title, re.IGNORECASE):
            financial_score += 0.3
        scores[DocumentType.FINANCIAL_REPORT] = financial_score
        
        # Email patterns
        email_score = 0.0
        if features.has_email_patterns:
            email_score += 0.3
        if re.search(r'\b(from|to|subject|sent|received):', content, re.IGNORECASE):
            email_score += 0.4
        if re.search(r'\b(email|message|mail)\b', title, re.IGNORECASE):
            email_score += 0.3
        scores[DocumentType.EMAIL] = email_score
        
        # News article patterns
        news_score = 0.0
        if features.has_date_patterns:
            news_score += 0.2
        if re.search(r'\b(news|article|report|breaking|update)\b', title, re.IGNORECASE):
            news_score += 0.3
        if 15 <= features.avg_sentence_length <= 25:  # News articles have moderate sentence length
            news_score += 0.3
        if features.paragraph_count >= 5:
            news_score += 0.2
        scores[DocumentType.NEWS_ARTICLE] = news_score
        
        # Meeting notes patterns
        meeting_score = 0.0
        if features.list_count > features.paragraph_count / 2:  # Lots of bullet points
            meeting_score += 0.4
        if re.search(r'\b(meeting|notes|agenda|action items|attendees)\b', content, re.IGNORECASE):
            meeting_score += 0.4
        if re.search(r'\b(meeting|notes|minutes)\b', title, re.IGNORECASE):
            meeting_score += 0.2
        scores[DocumentType.MEETING_NOTES] = meeting_score
        
        # Get best classification
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] >= 0.3:  # Minimum confidence threshold
                return best_type[0], best_type[1]
        
        # Default to plain text
        return DocumentType.PLAIN_TEXT, 0.5
    
    def _analyze_structure(self, content: str, features: DocumentFeatures) -> ContentStructure:
        """Analyze document structure patterns."""
        if features.heading_count >= 3 and features.paragraph_count >= features.heading_count:
            return ContentStructure.HIERARCHICAL
        elif features.table_indicators > features.paragraph_count:
            return ContentStructure.TABULAR
        elif features.list_count > features.paragraph_count / 2:
            return ContentStructure.LIST_HEAVY
        elif features.paragraph_count >= 3:
            return ContentStructure.LINEAR
        elif features.heading_count > 0 or features.list_count > 0 or features.table_indicators > 0:
            return ContentStructure.MIXED
        else:
            return ContentStructure.UNSTRUCTURED
    
    def _calculate_chunking_params(self, doc_type: DocumentType, 
                                 structure: ContentStructure,
                                 features: DocumentFeatures) -> Tuple[int, int]:
        """Calculate optimal chunking parameters based on document analysis."""
        base_chunk_size = 400
        base_overlap = 50
        
        # Adjust based on document type
        type_adjustments = {
            DocumentType.TECHNICAL_MANUAL: (600, 75),    # Larger chunks for technical content
            DocumentType.RESEARCH_PAPER: (500, 75),     # Larger chunks for academic content
            DocumentType.LEGAL_DOCUMENT: (800, 100),    # Large chunks for legal context
            DocumentType.FINANCIAL_REPORT: (600, 50),   # Large chunks, less overlap for tables
            DocumentType.NEWS_ARTICLE: (300, 50),       # Smaller chunks for news
            DocumentType.EMAIL: (200, 25),              # Small chunks for emails
            DocumentType.CODE_DOCUMENTATION: (500, 75), # Medium-large for code context
            DocumentType.MEETING_NOTES: (250, 40),      # Small-medium for notes
            DocumentType.PRESENTATION: (300, 60),       # Medium chunks with good overlap
        }
        
        if doc_type in type_adjustments:
            base_chunk_size, base_overlap = type_adjustments[doc_type]
        
        # Adjust based on structure
        if structure == ContentStructure.HIERARCHICAL:
            base_chunk_size = int(base_chunk_size * 1.2)  # Larger chunks for structured content
        elif structure == ContentStructure.TABULAR:
            base_chunk_size = int(base_chunk_size * 1.5)  # Much larger for tables
            base_overlap = int(base_overlap * 0.5)        # Less overlap for tabular data
        elif structure == ContentStructure.LIST_HEAVY:
            base_chunk_size = int(base_chunk_size * 0.8)  # Smaller chunks for lists
        elif structure == ContentStructure.UNSTRUCTURED:
            base_overlap = int(base_overlap * 1.5)        # More overlap for unstructured
        
        # Adjust based on content length
        if features.word_count < 500:
            base_chunk_size = min(base_chunk_size, features.word_count // 2)
        
        return max(100, base_chunk_size), max(10, base_overlap)
    
    def _calculate_readability(self, features: DocumentFeatures) -> float:
        """Calculate readability score (0.0-1.0, higher is more readable)."""
        score = 0.5  # Base score
        
        # Optimal sentence length (15-20 words)
        if 10 <= features.avg_sentence_length <= 25:
            score += 0.2
        elif features.avg_sentence_length > 30:
            score -= 0.2
        
        # Optimal word length (4-6 characters)
        if 3 <= features.avg_word_length <= 7:
            score += 0.1
        elif features.avg_word_length > 10:
            score -= 0.1
        
        # Reasonable punctuation density
        if 0.02 <= features.punctuation_density <= 0.08:
            score += 0.1
        
        # Structure helps readability
        if features.paragraph_count > 1:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_structure_score(self, features: DocumentFeatures) -> float:
        """Calculate structure quality score (0.0-1.0)."""
        score = 0.0
        
        # Presence of structural elements
        if features.heading_count > 0:
            score += 0.3
        if features.paragraph_count > 1:
            score += 0.2
        if features.list_count > 0:
            score += 0.2
        
        # Balance of elements
        if features.paragraph_count > 0:
            structure_ratio = (features.heading_count + features.list_count) / features.paragraph_count
            if 0.1 <= structure_ratio <= 0.5:  # Good balance
                score += 0.3
        
        return min(1.0, score)
    
    def _calculate_completeness(self, content: str, features: DocumentFeatures) -> float:
        """Calculate content completeness score (0.0-1.0)."""
        score = 0.5  # Base score
        
        # Sufficient length
        if features.word_count >= 100:
            score += 0.2
        elif features.word_count < 50:
            score -= 0.3
        
        # Complete sentences
        incomplete_sentences = len(re.findall(r'\b\w+\s*$', content))
        if incomplete_sentences == 0:
            score += 0.2
        
        # Proper punctuation
        if features.punctuation_density > 0.01:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _generate_processing_notes(self, doc_type: DocumentType, 
                                 structure: ContentStructure,
                                 features: DocumentFeatures) -> List[str]:
        """Generate processing recommendations."""
        notes = []
        
        # Document type specific notes
        if doc_type == DocumentType.TECHNICAL_MANUAL:
            notes.append("Technical content detected - using larger chunks for better context")
        elif doc_type == DocumentType.LEGAL_DOCUMENT:
            notes.append("Legal document detected - preserving longer passages for legal context")
        elif doc_type == DocumentType.FINANCIAL_REPORT:
            notes.append("Financial content detected - optimized for tabular data processing")
        
        # Structure specific notes
        if structure == ContentStructure.HIERARCHICAL:
            notes.append("Hierarchical structure detected - chunk boundaries aligned with sections")
        elif structure == ContentStructure.TABULAR:
            notes.append("Table-heavy content - using larger chunks to preserve table context")
        elif structure == ContentStructure.LIST_HEAVY:
            notes.append("List-heavy content - optimized chunk size for bullet points")
        
        # Quality notes
        if features.readability_score < 0.3:
            notes.append("Low readability detected - may need additional preprocessing")
        if features.completeness_score < 0.4:
            notes.append("Content may be incomplete or fragmented")
        if features.structure_score > 0.8:
            notes.append("Well-structured document - optimal for semantic chunking")
        
        return notes
    
    def _calculate_confidence(self, type_confidence: float, features: DocumentFeatures) -> float:
        """Calculate overall analysis confidence."""
        confidence = type_confidence * 0.6  # Type classification weight
        
        # Add confidence based on feature quality
        if features.word_count >= 100:
            confidence += 0.1
        if features.structure_score > 0.5:
            confidence += 0.1
        if features.completeness_score > 0.6:
            confidence += 0.1
        if features.readability_score > 0.5:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _default_analysis(self, content: str) -> DocumentIntelligenceResult:
        """Return default analysis when main analysis fails."""
        features = DocumentFeatures()
        features.char_count = len(content) if content else 0
        features.word_count = len(content.split()) if content else 0
        
        return DocumentIntelligenceResult(
            document_type=DocumentType.PLAIN_TEXT,
            structure=ContentStructure.UNSTRUCTURED,
            features=features,
            confidence=0.3,
            suggested_chunk_size=400,
            suggested_overlap=50,
            processing_notes=["Default analysis - original processing failed"]
        )


# Global document intelligence engine
document_intelligence = DocumentIntelligenceEngine()