"""
Authored by: AI/ML Engineer (jackson)
Date: 2025-08-05

Enhanced Semantic Search Engine

Advanced search capabilities with query understanding, expansion, and intelligent ranking.
Provides semantic search, query analytics, and intelligent result scoring for the RAG system.
"""

import os
import json
import time
import logging
from typing import List, Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import math
import asyncio
from functools import wraps

import numpy as np
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from rag_backend import get_rag_system
from document_manager import DocumentManager
from performance_cache import get_rag_query_cache
from error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

@dataclass
class QueryIntent:
    """Parsed query intent and metadata."""
    original_query: str
    normalized_query: str
    intent_type: str  # question, search, comparison, analysis, summary
    entities: List[str]
    keywords: List[str]
    semantic_concepts: List[str]
    complexity_score: float
    expanded_terms: List[str]
    filters: Dict[str, Any]
    confidence: float

@dataclass
class SearchResult:
    """Enhanced search result with relevance scoring."""
    doc_id: str
    content: str
    title: str
    source: str
    relevance_score: float
    semantic_score: float
    keyword_score: float
    freshness_score: float
    quality_score: float
    snippet: str
    highlights: List[str]
    metadata: Dict[str, Any]
    rank_position: int

@dataclass
class SearchAnalytics:
    """Search analytics and metrics."""
    query: str
    timestamp: datetime
    results_count: int
    response_time_ms: float
    user_clicked: List[int]  # clicked result positions
    user_satisfaction: Optional[float] = None
    session_id: Optional[str] = None

class QueryProcessor:
    """Advanced query processing and understanding."""
    
    def __init__(self):
        self.stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Intent classification patterns
        self.intent_patterns = {
            'question': [r'\b(what|who|where|when|why|how|which)\b', r'\?'],
            'comparison': [r'\b(vs|versus|compare|difference|between|better|worse)\b'],
            'analysis': [r'\b(analyze|analysis|explain|understand|insight)\b'],
            'summary': [r'\b(summary|summarize|overview|brief|main points)\b'],
            'search': [r'.*']  # default fallback
        }
        
        # Domain-specific synonyms for query expansion
        self.synonym_groups = {
            'technology': ['tech', 'technology', 'digital', 'software', 'system'],
            'business': ['business', 'company', 'organization', 'enterprise', 'firm'],
            'analysis': ['analysis', 'analyze', 'examine', 'study', 'evaluate'],
            'performance': ['performance', 'efficiency', 'speed', 'optimization'],
            'security': ['security', 'safety', 'protection', 'privacy', 'secure']
        }

    def process_query(self, query: str, context: Optional[Dict] = None) -> QueryIntent:
        """Process and understand user query intent."""
        try:
            # Normalize query
            normalized = self._normalize_query(query)
            
            # Extract intent
            intent_type = self._classify_intent(query)
            
            # Extract entities and keywords
            entities = self._extract_entities(normalized)
            keywords = self._extract_keywords(normalized)
            
            # Semantic concept extraction (simplified)
            semantic_concepts = self._extract_semantic_concepts(normalized)
            
            # Calculate complexity
            complexity = self._calculate_complexity(query, intent_type, keywords)
            
            # Query expansion
            expanded_terms = self._expand_query(keywords, semantic_concepts)
            
            # Extract filters from query
            filters = self._extract_filters(query, context or {})
            
            return QueryIntent(
                original_query=query,
                normalized_query=normalized,
                intent_type=intent_type,
                entities=entities,
                keywords=keywords,
                semantic_concepts=semantic_concepts,
                complexity_score=complexity,
                expanded_terms=expanded_terms,
                filters=filters,
                confidence=0.8  # Simplified confidence score
            )
            
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            # Return basic intent for fallback
            return QueryIntent(
                original_query=query,
                normalized_query=query.lower().strip(),
                intent_type='search',
                entities=[],
                keywords=query.lower().split(),
                semantic_concepts=[],
                complexity_score=0.5,
                expanded_terms=[],
                filters={},
                confidence=0.3
            )

    def _normalize_query(self, query: str) -> str:
        """Normalize query text."""
        # Basic normalization
        normalized = query.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Handle common contractions
        contractions = {
            "don't": "do not",
            "won't": "will not",
            "can't": "cannot",
            "what's": "what is",
            "how's": "how is"
        }
        
        for contraction, expansion in contractions.items():
            normalized = normalized.replace(contraction, expansion)
        
        return normalized

    def _classify_intent(self, query: str) -> str:
        """Classify query intent using pattern matching."""
        query_lower = query.lower()
        
        # Check patterns in order of specificity
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return intent
        
        return 'search'  # default

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query (simplified NER)."""
        # This is a simplified version - in production, use spaCy or similar
        entities = []
        
        # Look for capitalized words (potential proper nouns)
        words = query.split()
        for word in words:
            if word and word[0].isupper() and len(word) > 2:
                entities.append(word)
        
        return entities

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query."""
        words = query.split()
        keywords = []
        
        for word in words:
            # Remove punctuation and check length
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if len(clean_word) > 2 and clean_word not in self.stop_words:
                keywords.append(clean_word)
        
        return keywords

    def _extract_semantic_concepts(self, query: str) -> List[str]:
        """Extract semantic concepts from query."""
        concepts = []
        
        # Map keywords to semantic domains
        for concept, synonyms in self.synonym_groups.items():
            if any(synonym in query for synonym in synonyms):
                concepts.append(concept)
        
        return concepts

    def _calculate_complexity(self, query: str, intent_type: str, keywords: List[str]) -> float:
        """Calculate query complexity score (0-1)."""
        base_score = 0.3
        
        # Word count factor
        word_count = len(query.split())
        word_factor = min(word_count / 20.0, 0.3)
        
        # Intent complexity
        intent_weights = {
            'search': 0.2,
            'question': 0.4,
            'comparison': 0.7,
            'analysis': 0.8,
            'summary': 0.6
        }
        intent_factor = intent_weights.get(intent_type, 0.3)
        
        # Keyword diversity
        keyword_factor = min(len(set(keywords)) / 10.0, 0.2)
        
        return min(base_score + word_factor + intent_factor + keyword_factor, 1.0)

    def _expand_query(self, keywords: List[str], concepts: List[str]) -> List[str]:
        """Expand query with synonyms and related terms."""
        expanded = set(keywords)
        
        # Add synonyms for concepts
        for concept in concepts:
            if concept in self.synonym_groups:
                expanded.update(self.synonym_groups[concept])
        
        # Add common variations
        variations = []
        for keyword in keywords:
            # Add plural/singular forms (simplified)
            if keyword.endswith('s') and len(keyword) > 3:
                variations.append(keyword[:-1])
            else:
                variations.append(keyword + 's')
        
        expanded.update(variations)
        return list(expanded)

    def _extract_filters(self, query: str, context: Dict) -> Dict[str, Any]:
        """Extract filters from query and context."""
        filters = {}
        
        # Time-based filters
        time_patterns = {
            'recent': {'days': 30},
            'last week': {'days': 7},
            'today': {'days': 1},
            'this month': {'days': 30}
        }
        
        for pattern, time_filter in time_patterns.items():
            if pattern in query.lower():
                filters['time_range'] = time_filter
                break
        
        # File type filters
        file_types = ['pdf', 'doc', 'txt', 'html', 'markdown']
        for file_type in file_types:
            if file_type in query.lower():
                filters['file_type'] = file_type
                break
        
        return filters

class SemanticSearchEngine:
    """Enhanced semantic search engine with intelligent ranking."""
    
    def __init__(self, rag_system=None):
        self.rag_system = rag_system or get_rag_system()
        self.doc_manager = DocumentManager()
        self.query_processor = QueryProcessor()
        self.cache = get_rag_query_cache()
        
        # Initialize TF-IDF for keyword scoring
        self.tfidf_vectorizer = None
        self.document_texts = {}
        self._build_tfidf_index()
        
        # Search analytics storage
        self.analytics = []
        self.analytics_lock = asyncio.Lock()

    def _build_tfidf_index(self):
        """Build TF-IDF index for keyword-based scoring."""
        try:
            # Get all documents
            documents = self.doc_manager.list_documents()
            if not documents:
                logger.info("No documents found for TF-IDF indexing")
                return
            
            # Collect document texts
            texts = []
            doc_ids = []
            
            for doc in documents:
                doc_id = doc.get('doc_id')
                if doc_id:
                    # Get document chunks from ChromaDB
                    try:
                        results = self.rag_system.collection.get(
                            where={"doc_id": doc_id},
                            include=["documents"]
                        )
                        if results and results['documents']:
                            doc_text = ' '.join(results['documents'])
                            texts.append(doc_text)
                            doc_ids.append(doc_id)
                            self.document_texts[doc_id] = doc_text
                    except Exception as e:
                        logger.warning(f"Could not get text for document {doc_id}: {e}")
            
            if texts:
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=5000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
                self.doc_id_to_index = {doc_id: i for i, doc_id in enumerate(doc_ids)}
                logger.info(f"Built TF-IDF index for {len(texts)} documents")
            
        except Exception as e:
            logger.error(f"Error building TF-IDF index: {e}")

    async def search(self, query: str, max_results: int = 10, 
                    filters: Optional[Dict] = None,
                    user_context: Optional[Dict] = None) -> List[SearchResult]:
        """Enhanced semantic search with intelligent ranking."""
        start_time = time.time()
        
        try:
            # Process query
            query_intent = self.query_processor.process_query(query, user_context)
            
            # Check cache
            cache_key = self._generate_cache_key(query, max_results, filters)
            cached_results = await self._get_cached_results(cache_key)
            if cached_results:
                return cached_results
            
            # Perform multi-modal search
            results = await self._multi_modal_search(query_intent, max_results, filters)
            
            # Rank and score results
            ranked_results = self._rank_results(results, query_intent)
            
            # Cache results
            await self._cache_results(cache_key, ranked_results)
            
            # Record analytics
            response_time = (time.time() - start_time) * 1000
            await self._record_search_analytics(query, len(ranked_results), response_time)
            
            return ranked_results[:max_results]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def _multi_modal_search(self, query_intent: QueryIntent, 
                                max_results: int, filters: Optional[Dict]) -> List[Dict]:
        """Perform multi-modal search combining semantic and keyword approaches."""
        all_results = []
        
        # 1. Semantic search using existing RAG system
        semantic_results = await self._semantic_search(query_intent, max_results * 2)
        all_results.extend(semantic_results)
        
        # 2. Keyword search using TF-IDF
        if self.tfidf_vectorizer:
            keyword_results = await self._keyword_search(query_intent, max_results)
            all_results.extend(keyword_results)
        
        # 3. Apply filters
        if filters:
            all_results = self._apply_filters(all_results, filters)
        
        # Remove duplicates by doc_id
        seen_docs = set()
        unique_results = []
        for result in all_results:
            doc_id = result.get('doc_id')
            if doc_id and doc_id not in seen_docs:
                seen_docs.add(doc_id)
                unique_results.append(result)
        
        return unique_results

    async def _semantic_search(self, query_intent: QueryIntent, max_results: int) -> List[Dict]:
        """Perform semantic search using the existing RAG system."""
        try:
            # Use expanded query for better recall
            search_query = ' '.join([query_intent.original_query] + query_intent.expanded_terms[:3])
            
            # Get semantic results from RAG system
            docs = self.rag_system.adaptive_retrieval(search_query, max_chunks=max_results)
            
            results = []
            for doc in docs:
                result = {
                    'doc_id': doc.get('doc_id', ''),
                    'content': doc.get('content', ''),
                    'title': doc.get('title', ''),
                    'source': doc.get('source', ''),
                    'semantic_score': doc.get('score', 0.0),
                    'search_type': 'semantic',
                    'metadata': doc.get('metadata', {})
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    async def _keyword_search(self, query_intent: QueryIntent, max_results: int) -> List[Dict]:
        """Perform keyword-based search using TF-IDF."""
        try:
            if not self.tfidf_vectorizer:
                return []
            
            # Create query vector
            query_text = ' '.join(query_intent.keywords + query_intent.expanded_terms)
            query_vector = self.tfidf_vectorizer.transform([query_text])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Get top results
            top_indices = similarities.argsort()[-max_results:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum relevance threshold
                    doc_id = list(self.doc_id_to_index.keys())[
                        list(self.doc_id_to_index.values()).index(idx)
                    ]
                    
                    # Get document metadata
                    doc_info = self.doc_manager.get_document(doc_id)
                    if doc_info:
                        result = {
                            'doc_id': doc_id,
                            'content': self.document_texts.get(doc_id, ''),
                            'title': doc_info.title,
                            'source': doc_info.source,
                            'keyword_score': float(similarities[idx]),
                            'search_type': 'keyword',
                            'metadata': doc_info.to_dict()
                        }
                        results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []

    def _rank_results(self, results: List[Dict], query_intent: QueryIntent) -> List[SearchResult]:
        """Rank and score search results using multiple factors."""
        scored_results = []
        
        for i, result in enumerate(results):
            # Extract scores
            semantic_score = result.get('semantic_score', 0.0)
            keyword_score = result.get('keyword_score', 0.0)
            
            # Calculate additional scores
            freshness_score = self._calculate_freshness_score(result.get('metadata', {}))
            quality_score = self._calculate_quality_score(result)
            
            # Combine scores with weights
            weights = {
                'semantic': 0.4,
                'keyword': 0.3,
                'freshness': 0.1,
                'quality': 0.2
            }
            
            relevance_score = (
                semantic_score * weights['semantic'] +
                keyword_score * weights['keyword'] +
                freshness_score * weights['freshness'] +
                quality_score * weights['quality']
            )
            
            # Generate snippet and highlights
            snippet = self._generate_snippet(result.get('content', ''), query_intent)
            highlights = self._generate_highlights(result.get('content', ''), query_intent)
            
            search_result = SearchResult(
                doc_id=result.get('doc_id', ''),
                content=result.get('content', ''),
                title=result.get('title', ''),
                source=result.get('source', ''),
                relevance_score=relevance_score,
                semantic_score=semantic_score,
                keyword_score=keyword_score,
                freshness_score=freshness_score,
                quality_score=quality_score,
                snippet=snippet,
                highlights=highlights,
                metadata=result.get('metadata', {}),
                rank_position=i + 1
            )
            
            scored_results.append(search_result)
        
        # Sort by relevance score
        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Update rank positions
        for i, result in enumerate(scored_results):
            result.rank_position = i + 1
        
        return scored_results

    def _calculate_freshness_score(self, metadata: Dict) -> float:
        """Calculate freshness score based on document age."""
        try:
            upload_time = metadata.get('upload_timestamp')
            if not upload_time:
                return 0.5  # neutral score
            
            upload_date = datetime.fromisoformat(upload_time)
            days_old = (datetime.now() - upload_date).days
            
            # Exponential decay with half-life of 90 days
            freshness = math.exp(-days_old / 90.0)
            return min(freshness, 1.0)
            
        except Exception:
            return 0.5

    def _calculate_quality_score(self, result: Dict) -> float:
        """Calculate quality score based on document characteristics."""
        try:
            metadata = result.get('metadata', {})
            content = result.get('content', '')
            
            score = 0.5  # base score
            
            # Content length factor
            if len(content) > 100:
                score += 0.2
            if len(content) > 500:
                score += 0.1
            
            # Title quality
            title = result.get('title', '')
            if title and len(title) > 10:
                score += 0.1
            
            # PDF quality score
            pdf_quality = metadata.get('quality_score')
            if pdf_quality:
                score += pdf_quality * 0.2
            
            return min(score, 1.0)
            
        except Exception:
            return 0.5

    def _generate_snippet(self, content: str, query_intent: QueryIntent, max_length: int = 200) -> str:
        """Generate a relevant snippet from the content."""
        if not content:
            return ""
        
        # Find sentences containing query keywords
        sentences = content.split('. ')
        query_words = set(query_intent.keywords + query_intent.expanded_terms[:3])
        
        scored_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            sentence_words = set(sentence.lower().split())
            overlap = len(query_words.intersection(sentence_words))
            scored_sentences.append((overlap, sentence))
        
        # Sort by relevance and take best sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        
        snippet_parts = []
        current_length = 0
        
        for score, sentence in scored_sentences:
            if score > 0 and current_length + len(sentence) <= max_length:
                snippet_parts.append(sentence)
                current_length += len(sentence)
            
            if current_length >= max_length * 0.8:  # 80% of max length
                break
        
        if not snippet_parts:
            # Fallback to first part of content
            return content[:max_length] + "..." if len(content) > max_length else content
        
        snippet = '. '.join(snippet_parts)
        return snippet + "..." if len(content) > len(snippet) else snippet

    def _generate_highlights(self, content: str, query_intent: QueryIntent) -> List[str]:
        """Generate highlighted terms from the content."""
        highlights = []
        query_terms = query_intent.keywords + query_intent.expanded_terms[:5]
        
        for term in query_terms:
            # Find term occurrences (case-insensitive)
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            matches = pattern.finditer(content)
            
            for match in matches:
                start = max(0, match.start() - 30)
                end = min(len(content), match.end() + 30)
                highlight = content[start:end]
                
                # Bold the matched term
                highlight = pattern.sub(f"**{match.group()}**", highlight)
                highlights.append(highlight)
                
                if len(highlights) >= 3:  # Limit highlights
                    break
            
            if len(highlights) >= 3:
                break
        
        return highlights

    def _apply_filters(self, results: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to search results."""
        filtered_results = []
        
        for result in results:
            metadata = result.get('metadata', {})
            
            # Time range filter
            if 'time_range' in filters:
                upload_time = metadata.get('upload_timestamp')
                if upload_time:
                    try:
                        upload_date = datetime.fromisoformat(upload_time)
                        days_ago = (datetime.now() - upload_date).days
                        if days_ago > filters['time_range'].get('days', 365):
                            continue
                    except Exception:
                        pass
            
            # File type filter
            if 'file_type' in filters:
                doc_file_type = metadata.get('file_type', '').lower()
                if filters['file_type'].lower() not in doc_file_type:
                    continue
            
            filtered_results.append(result)
        
        return filtered_results

    def _generate_cache_key(self, query: str, max_results: int, filters: Optional[Dict]) -> str:
        """Generate cache key for search results."""
        key_data = {
            'query': query,
            'max_results': max_results,
            'filters': filters or {}
        }
        return f"search_{hash(str(key_data))}"

    async def _get_cached_results(self, cache_key: str) -> Optional[List[SearchResult]]:
        """Get cached search results."""
        try:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                # Convert dict back to SearchResult objects
                results = []
                for item in cached_data:
                    result = SearchResult(**item)
                    results.append(result)
                return results
        except Exception as e:
            logger.debug(f"Cache retrieval error: {e}")
        return None

    async def _cache_results(self, cache_key: str, results: List[SearchResult]):
        """Cache search results."""
        try:
            # Convert SearchResult objects to dicts for caching
            cache_data = [asdict(result) for result in results]
            self.cache.put(cache_key, cache_data, ttl=300)  # 5 minute TTL
        except Exception as e:
            logger.debug(f"Cache storage error: {e}")

    async def _record_search_analytics(self, query: str, results_count: int, response_time: float):
        """Record search analytics."""
        try:
            async with self.analytics_lock:
                analytics = SearchAnalytics(
                    query=query,
                    timestamp=datetime.now(),
                    results_count=results_count,
                    response_time_ms=response_time,
                    user_clicked=[]
                )
                self.analytics.append(analytics)
                
                # Keep only recent analytics (last 1000 searches)
                if len(self.analytics) > 1000:
                    self.analytics = self.analytics[-1000:]
                    
        except Exception as e:
            logger.debug(f"Analytics recording error: {e}")

    async def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on partial query."""
        try:
            suggestions = []
            
            # Get popular queries from analytics
            if hasattr(self, 'analytics') and self.analytics:
                query_counts = Counter()
                for analytic in self.analytics[-100:]:  # Recent analytics
                    query_counts[analytic.query] += 1
                
                # Find matching queries
                partial_lower = partial_query.lower()
                for query, count in query_counts.most_common():
                    if partial_lower in query.lower() and query != partial_query:
                        suggestions.append(query)
                        if len(suggestions) >= limit:
                            break
            
            # Add keyword-based suggestions
            if len(suggestions) < limit:
                # Simple keyword expansion
                common_terms = ['analysis', 'summary', 'overview', 'guide', 'tutorial']
                for term in common_terms:
                    if term.startswith(partial_query.lower()):
                        suggestions.append(f"{partial_query} {term}")
                        if len(suggestions) >= limit:
                            break
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Search suggestions error: {e}")
            return []

# Global instance
_search_engine_instance = None

def get_search_engine() -> SemanticSearchEngine:
    """Get global search engine instance."""
    global _search_engine_instance
    if _search_engine_instance is None:
        _search_engine_instance = SemanticSearchEngine()
    return _search_engine_instance