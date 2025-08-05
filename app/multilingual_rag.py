"""
Authored by: Harry Lewis (louie)
Date: 2025-01-08

Multilingual RAG System for Language-Aware Query Processing
Extends the existing RAG system with comprehensive multilingual support
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer
import chromadb
from datetime import datetime
import asyncio
import numpy as np
from functools import lru_cache

# Import our multilingual components
from .language_detection import get_language_detector, LanguageDetectionResult
from .i18n_manager import get_i18n_manager, I18nManager
from .rag_backend import get_rag_system, LocalRAGSystem

logger = logging.getLogger(__name__)

@dataclass
class MultilingualQuery:
    """Structure for multilingual query processing."""
    original_text: str
    detected_language: str
    confidence: float
    translated_text: Optional[str] = None
    target_language: Optional[str] = None
    language_alternatives: List[Tuple[str, float]] = None

@dataclass
class MultilingualDocument:
    """Structure for multilingual document metadata."""
    doc_id: str
    title: str
    content: str
    detected_language: str
    language_confidence: float
    alternative_languages: List[Tuple[str, float]]
    translation_available: List[str] = None  # Available translation languages
    content_hash: str = ""
    processing_notes: List[str] = None

@dataclass
class MultilingualSearchResult:
    """Enhanced search result with language information."""
    doc_id: str
    content: str
    similarity_score: float
    language: str
    language_confidence: float
    translation_used: bool = False
    original_language: Optional[str] = None
    chunk_metadata: Dict[str, Any] = None

@dataclass
class MultilingualRAGResponse:
    """Enhanced RAG response with multilingual context."""
    answer: str
    answer_language: str
    query_language: str
    sources: List[MultilingualSearchResult]
    context_used: int
    context_tokens: int
    efficiency_ratio: float
    translation_performed: bool = False
    language_mixing_detected: bool = False
    confidence_score: float = 1.0

class MultilingualEmbeddingManager:
    """
    Manages multilingual embeddings with language-specific optimizations.
    """
    
    def __init__(self):
        self.models = {}
        self.default_model = "all-MiniLM-L6-v2"  # Multilingual model
        self.language_specific_models = {
            # Language-specific models for better performance
            "zh": "distiluse-base-multilingual-cased",  # Better for Chinese
            "ja": "distiluse-base-multilingual-cased",  # Better for Japanese
            "ko": "distiluse-base-multilingual-cased",  # Better for Korean
            "ar": "distiluse-base-multilingual-cased",  # Better for Arabic
            "hi": "distiluse-base-multilingual-cased",  # Better for Hindi
        }
        self._load_default_model()
    
    def _load_default_model(self):
        """Load the default multilingual model."""
        try:
            self.models[self.default_model] = SentenceTransformer(self.default_model)
            logger.info(f"Loaded default multilingual model: {self.default_model}")
        except Exception as e:
            logger.error(f"Failed to load default model {self.default_model}: {e}")
            raise
    
    def get_model_for_language(self, language: str) -> SentenceTransformer:
        """Get the best embedding model for a specific language."""
        model_name = self.language_specific_models.get(language, self.default_model)
        
        if model_name not in self.models:
            try:
                self.models[model_name] = SentenceTransformer(model_name)
                logger.info(f"Loaded language-specific model {model_name} for {language}")
            except Exception as e:
                logger.warning(f"Failed to load model {model_name} for {language}, using default: {e}")
                model_name = self.default_model
        
        return self.models[model_name]
    
    @lru_cache(maxsize=1000)
    def encode_text(self, text: str, language: str) -> np.ndarray:
        """Encode text using the appropriate model for the language."""
        model = self.get_model_for_language(language)
        return model.encode(text)
    
    def encode_batch(self, texts: List[str], languages: List[str]) -> List[np.ndarray]:
        """Encode multiple texts with their respective language models."""
        # Group texts by language for efficient batch processing
        language_groups = {}
        for i, (text, lang) in enumerate(zip(texts, languages)):
            if lang not in language_groups:
                language_groups[lang] = []
            language_groups[lang].append((i, text))
        
        # Process each language group
        results = [None] * len(texts)
        for lang, text_pairs in language_groups.items():
            model = self.get_model_for_language(lang)
            indices, texts_for_lang = zip(*text_pairs)
            embeddings = model.encode(list(texts_for_lang))
            
            for idx, embedding in zip(indices, embeddings):
                results[idx] = embedding
        
        return results

class MultilingualRAGSystem:
    """
    Enhanced RAG system with comprehensive multilingual support.
    
    Features:
    - Automatic language detection for queries and documents
    - Language-aware embedding generation
    - Cross-language search capabilities
    - Translation integration
    - Language-specific retrieval strategies
    - Multilingual response generation
    """
    
    def __init__(self, base_rag_system: Optional[LocalRAGSystem] = None):
        self.base_rag = base_rag_system or get_rag_system()
        self.language_detector = get_language_detector()
        self.i18n_manager = get_i18n_manager()
        self.embedding_manager = MultilingualEmbeddingManager()
        
        # Configuration
        self.enable_cross_language_search = True
        self.enable_translation = True
        self.confidence_threshold = 0.3
        self.max_translation_cache = 1000
        
        # Language-specific search strategies
        self.language_search_strategies = {
            "zh": {"chunk_size": 300, "overlap": 30},  # Smaller chunks for Chinese
            "ja": {"chunk_size": 300, "overlap": 30},  # Smaller chunks for Japanese
            "ko": {"chunk_size": 300, "overlap": 30},  # Smaller chunks for Korean
            "ar": {"chunk_size": 400, "overlap": 50},  # Different overlap for Arabic
            "hi": {"chunk_size": 400, "overlap": 50},  # Different overlap for Hindi
        }
        
        logger.info("Multilingual RAG system initialized")
    
    async def process_multilingual_document(self, document: Dict[str, Any]) -> MultilingualDocument:
        """
        Process a document with multilingual analysis.
        
        Args:
            document: Document dictionary with content and metadata
            
        Returns:
            MultilingualDocument with language analysis
        """
        content = document.get("content", "")
        title = document.get("title", "")
        doc_id = document.get("doc_id", "")
        
        # Detect document language
        detection_result = self.language_detector.detect_language(content)
        
        # Create multilingual document metadata
        multilingual_doc = MultilingualDocument(
            doc_id=doc_id,
            title=title,
            content=content,
            detected_language=detection_result.language,
            language_confidence=detection_result.confidence,
            alternative_languages=detection_result.alternatives,
            translation_available=[],
            processing_notes=[]
        )
        
        # Add language metadata to document for storage
        document["detected_language"] = detection_result.language
        document["language_confidence"] = detection_result.confidence
        document["language_alternatives"] = detection_result.alternatives
        document["mixed_languages"] = detection_result.mixed_languages
        document["text_quality"] = detection_result.text_quality
        
        # Apply language-specific processing if needed
        if detection_result.language in self.language_search_strategies:
            strategy = self.language_search_strategies[detection_result.language]
            document["suggested_chunk_size"] = strategy["chunk_size"]
            document["suggested_overlap"] = strategy["overlap"]
            multilingual_doc.processing_notes.append(
                f"Applied {detection_result.language}-specific chunking strategy"
            )
        
        return multilingual_doc
    
    async def multilingual_query(self, query: str, target_language: Optional[str] = None,
                                max_chunks: Optional[int] = None,
                                enable_cross_language: bool = True) -> MultilingualRAGResponse:
        """
        Perform multilingual RAG query with language-aware processing.
        
        Args:
            query: User query in any supported language
            target_language: Preferred response language (auto-detect if None)
            max_chunks: Maximum chunks to retrieve
            enable_cross_language: Whether to search across different languages
            
        Returns:
            MultilingualRAGResponse with enhanced multilingual information
        """
        # Detect query language
        query_detection = self.language_detector.detect_language(query)
        query_language = query_detection.language
        
        # Determine target language for response
        response_language = target_language or query_language
        if response_language == "unknown":
            response_language = self.i18n_manager.default_language
        
        logger.info(f"Processing multilingual query in {query_language}, responding in {response_language}")
        
        # Create multilingual query object
        multilingual_query = MultilingualQuery(
            original_text=query,
            detected_language=query_language,
            confidence=query_detection.confidence,
            target_language=response_language,
            language_alternatives=query_detection.alternatives
        )
        
        # Perform multilingual search
        search_results = await self._multilingual_search(
            multilingual_query, max_chunks, enable_cross_language
        )
        
        # Generate multilingual response
        response = await self._generate_multilingual_response(
            multilingual_query, search_results
        )
        
        return response
    
    async def _multilingual_search(self, query: MultilingualQuery, max_chunks: Optional[int],
                                 enable_cross_language: bool) -> List[MultilingualSearchResult]:
        """Perform multilingual document search."""
        try:
            # Use language-aware embedding for query
            query_embedding = self.embedding_manager.encode_text(
                query.original_text, query.detected_language
            )
            
            # Perform vector search using the base RAG system
            # We'll modify the search to be language-aware
            collection = self.base_rag.collection
            
            # Build search filters
            where_clause = {}
            if not enable_cross_language and query.detected_language != "unknown":
                # Restrict to same language documents
                where_clause["detected_language"] = query.detected_language
            
            # Perform search
            search_results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=max_chunks or 5,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert to multilingual search results
            multilingual_results = []
            
            if search_results.get("documents") and search_results["documents"][0]:
                documents = search_results["documents"][0]
                metadatas = search_results["metadatas"][0] if search_results.get("metadatas") else []
                distances = search_results["distances"][0] if search_results.get("distances") else []
                
                for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                    # Convert distance to similarity score
                    similarity_score = 1.0 - distance
                    
                    doc_language = metadata.get("detected_language", "unknown")
                    doc_confidence = metadata.get("language_confidence", 0.0)
                    
                    result = MultilingualSearchResult(
                        doc_id=metadata.get("doc_id", f"doc_{i}"),
                        content=doc,
                        similarity_score=similarity_score,
                        language=doc_language,
                        language_confidence=doc_confidence,
                        translation_used=False,
                        original_language=doc_language,
                        chunk_metadata=metadata
                    )
                    
                    multilingual_results.append(result)
            
            logger.info(f"Found {len(multilingual_results)} multilingual search results")
            return multilingual_results
            
        except Exception as e:
            logger.error(f"Error in multilingual search: {e}")
            return []
    
    async def _generate_multilingual_response(self, query: MultilingualQuery,
                                            search_results: List[MultilingualSearchResult]) -> MultilingualRAGResponse:
        """Generate multilingual response from search results."""
        try:
            if not search_results:
                # No results found - return appropriate message
                no_results_message = self.i18n_manager.get_message(
                    "no_results_found",
                    language=query.target_language,
                    namespace="chat"
                )
                
                return MultilingualRAGResponse(
                    answer=no_results_message,
                    answer_language=query.target_language or "en",
                    query_language=query.detected_language,
                    sources=[],
                    context_used=0,
                    context_tokens=0,
                    efficiency_ratio=0.0,
                    confidence_score=0.0
                )
            
            # Build context for LLM
            context_pieces = []
            total_tokens = 0
            language_mixing_detected = False
            
            for result in search_results:
                # Check for language mixing
                if result.language != query.detected_language and query.detected_language != "unknown":
                    language_mixing_detected = True
                
                # Add source information with language context
                source_info = f"[Source: {result.doc_id}, Language: {result.language}]\n{result.content}"
                context_pieces.append(source_info)
                total_tokens += len(result.content.split())
            
            context = "\n\n".join(context_pieces)
            
            # Prepare prompt with multilingual awareness
            system_prompt = self._build_multilingual_system_prompt(
                query.detected_language, query.target_language
            )
            
            # Generate response using base RAG system's LLM
            try:
                llm_response = await self._call_llm_with_context(
                    system_prompt, query.original_text, context
                )
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                error_message = self.i18n_manager.get_message(
                    "generation_error",
                    language=query.target_language,
                    namespace="errors"
                )
                llm_response = error_message
            
            # Calculate efficiency metrics
            efficiency_ratio = min(len(search_results) / max(total_tokens / 100, 1), 1.0)
            
            # Assess response confidence
            confidence_score = self._calculate_response_confidence(
                query, search_results, language_mixing_detected
            )
            
            return MultilingualRAGResponse(
                answer=llm_response,
                answer_language=query.target_language or query.detected_language,
                query_language=query.detected_language,
                sources=search_results,
                context_used=len(search_results),
                context_tokens=total_tokens,
                efficiency_ratio=efficiency_ratio,
                translation_performed=False,  # TODO: Implement translation
                language_mixing_detected=language_mixing_detected,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Error generating multilingual response: {e}")
            error_message = self.i18n_manager.get_message(
                "response_generation_error",
                language=query.target_language or "en",
                namespace="errors"
            )
            
            return MultilingualRAGResponse(
                answer=error_message,
                answer_language=query.target_language or "en",
                query_language=query.detected_language,
                sources=[],
                context_used=0,
                context_tokens=0,
                efficiency_ratio=0.0,
                confidence_score=0.0
            )
    
    def _build_multilingual_system_prompt(self, query_language: str, response_language: str) -> str:
        """Build system prompt with multilingual instructions."""
        base_prompt = """You are a helpful multilingual AI assistant with access to a knowledge base. """
        
        if query_language != "unknown":
            base_prompt += f"The user's query is in {query_language}. "
        
        if response_language and response_language != query_language:
            base_prompt += f"Please respond in {response_language}. "
        elif query_language != "unknown":
            base_prompt += f"Please respond in the same language as the query ({query_language}). "
        
        base_prompt += """
Use the provided context to answer the user's question accurately and comprehensively.
If the context contains information in different languages, synthesize the information appropriately.
If you cannot find relevant information in the context, say so clearly.
Always cite your sources when possible.
"""
        return base_prompt
    
    async def _call_llm_with_context(self, system_prompt: str, query: str, context: str) -> str:
        """Call the LLM with multilingual context."""
        try:
            # Use the base RAG system's LLM client
            full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nUser Question: {query}\n\nAnswer:"
            
            # Call the Ollama client
            response = await asyncio.to_thread(
                self.base_rag.llm_client.generate_response,
                full_prompt
            )
            
            return response
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
    def _calculate_response_confidence(self, query: MultilingualQuery,
                                     search_results: List[MultilingualSearchResult],
                                     language_mixing: bool) -> float:
        """Calculate confidence score for the response."""
        if not search_results:
            return 0.0
        
        # Base confidence from query language detection
        base_confidence = query.confidence
        
        # Average similarity score from search results
        avg_similarity = sum(result.similarity_score for result in search_results) / len(search_results)
        
        # Language mixing penalty
        language_penalty = 0.9 if language_mixing else 1.0
        
        # Combine factors
        confidence = (base_confidence * 0.3 + avg_similarity * 0.7) * language_penalty
        
        return min(confidence, 1.0)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return [lang.code for lang in self.i18n_manager.get_supported_languages()]
    
    def get_language_statistics(self) -> Dict[str, Any]:
        """Get multilingual system statistics."""
        try:
            # Get language distribution from stored documents
            collection = self.base_rag.collection
            all_docs = collection.get(include=["metadatas"])
            
            language_counts = {}
            total_docs = 0
            
            if all_docs.get("metadatas"):
                for metadata in all_docs["metadatas"]:
                    lang = metadata.get("detected_language", "unknown")
                    language_counts[lang] = language_counts.get(lang, 0) + 1
                    total_docs += 1
            
            return {
                "total_documents": total_docs,
                "language_distribution": language_counts,
                "supported_languages": len(self.get_supported_languages()),
                "embedding_models_loaded": len(self.embedding_manager.models),
                "cross_language_search_enabled": self.enable_cross_language_search,
                "translation_enabled": self.enable_translation
            }
            
        except Exception as e:
            logger.error(f"Error getting language statistics: {e}")
            return {"error": str(e)}
    
    def set_language_preferences(self, **preferences):
        """Set language-specific preferences."""
        if "confidence_threshold" in preferences:
            self.confidence_threshold = preferences["confidence_threshold"]
        
        if "enable_cross_language_search" in preferences:
            self.enable_cross_language_search = preferences["enable_cross_language_search"]
        
        if "enable_translation" in preferences:
            self.enable_translation = preferences["enable_translation"]
        
        logger.info(f"Updated language preferences: {preferences}")

# Global instance
_multilingual_rag_system = None

def get_multilingual_rag_system() -> MultilingualRAGSystem:
    """Get the global multilingual RAG system instance."""
    global _multilingual_rag_system
    if _multilingual_rag_system is None:
        _multilingual_rag_system = MultilingualRAGSystem()
    return _multilingual_rag_system

async def multilingual_query(query: str, target_language: Optional[str] = None,
                            max_chunks: Optional[int] = None) -> MultilingualRAGResponse:
    """Shorthand function for multilingual RAG queries."""
    system = get_multilingual_rag_system()
    return await system.multilingual_query(query, target_language, max_chunks)

if __name__ == "__main__":
    # Demo usage
    import asyncio
    
    async def demo():
        system = MultilingualRAGSystem()
        
        # Test multilingual query
        test_queries = [
            "What is artificial intelligence?",
            "¿Qué es la inteligencia artificial?",
            "Qu'est-ce que l'intelligence artificielle?",
            "Was ist künstliche Intelligenz?",
            "人工智能是什么？"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            result = await system.multilingual_query(query)
            print(f"Detected language: {result.query_language}")
            print(f"Response language: {result.answer_language}")
            print(f"Confidence: {result.confidence_score:.3f}")
            print("---")
    
    asyncio.run(demo())