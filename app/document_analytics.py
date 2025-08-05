"""
Authored by: AI/ML Engineer (jackson)
Date: 2025-08-05

Document Analytics Engine

Advanced document analysis, insights generation, and intelligent categorization system.
Provides content analytics, trend analysis, and automated document classification.
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
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from rag_backend import get_rag_system
from document_manager import DocumentManager
from performance_cache import get_document_cache
from error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

@dataclass
class DocumentInsight:
    """Document-level insights and analytics."""
    doc_id: str
    title: str
    content_summary: str
    key_topics: List[str]
    sentiment_score: float
    complexity_score: float
    readability_score: float
    word_count: int
    unique_concepts: List[str]
    related_documents: List[str]
    quality_metrics: Dict[str, float]
    generated_at: datetime

@dataclass
class CollectionInsights:
    """Collection-level analytics and trends."""
    total_documents: int
    total_words: int
    avg_document_length: float
    topic_distribution: Dict[str, int]
    content_types: Dict[str, int]
    upload_trends: Dict[str, int]
    quality_distribution: Dict[str, int]
    top_keywords: List[Tuple[str, int]]
    document_clusters: List[Dict[str, Any]]
    sentiment_analysis: Dict[str, float]
    generated_at: datetime

@dataclass
class ContentCategory:
    """Document categorization result.""" 
    category: str
    confidence: float
    keywords: List[str]
    reasoning: str

@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    metric: str
    time_period: str
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    change_rate: float
    data_points: List[Tuple[datetime, float]]

class TopicExtractor:
    """Advanced topic extraction using multiple approaches."""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        self.lda_model = None
        self.kmeans_model = None
        self.document_vectors = None

    def extract_topics(self, documents: List[str], num_topics: int = 5) -> Dict[str, Any]:
        """Extract topics using multiple approaches."""
        try:
            if not documents or len(documents) < 2:
                return {'topics': [], 'method': 'insufficient_data'}
            
            # TF-IDF analysis
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # LDA topic modeling
            lda_topics = self._extract_lda_topics(tfidf_matrix, feature_names, num_topics)
            
            # K-means clustering topics
            kmeans_topics = self._extract_kmeans_topics(tfidf_matrix, feature_names, num_topics)
            
            # Combine and rank topics
            combined_topics = self._combine_topic_results(lda_topics, kmeans_topics)
            
            return {
                'topics': combined_topics,
                'method': 'combined_lda_kmeans',
                'document_count': len(documents)
            }
        
        except Exception as e:
            logger.error(f"Topic extraction error: {e}")
            return {'topics': [], 'method': 'error', 'error': str(e)}

    def _extract_lda_topics(self, tfidf_matrix, feature_names: List[str], num_topics: int) -> List[Dict]:
        """Extract topics using Latent Dirichlet Allocation."""
        try:
            self.lda_model = LatentDirichletAllocation(
                n_components=num_topics,
                max_iter=100,
                learning_method='online',
                random_state=42
            )
            self.lda_model.fit(tfidf_matrix)
            
            topics = []
            for topic_idx, topic in enumerate(self.lda_model.components_):
                top_indices = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_indices]
                top_scores = [topic[i] for i in top_indices]
                
                topics.append({
                    'id': f'lda_topic_{topic_idx}',
                    'words': top_words,
                    'scores': top_scores,
                    'method': 'lda'
                })
            
            return topics
        
        except Exception as e:
            logger.warning(f"LDA topic extraction failed: {e}")
            return []

    def _extract_kmeans_topics(self, tfidf_matrix, feature_names: List[str], num_topics: int) -> List[Dict]:
        """Extract topics using K-means clustering."""
        try:
            self.kmeans_model = KMeans(n_clusters=num_topics, random_state=42, n_init=10)
            self.kmeans_model.fit(tfidf_matrix)
            
            topics = []
            for cluster_idx, centroid in enumerate(self.kmeans_model.cluster_centers_):
                top_indices = centroid.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_indices]
                top_scores = [centroid[i] for i in top_indices]
                
                topics.append({
                    'id': f'kmeans_cluster_{cluster_idx}',
                    'words': top_words,
                    'scores': top_scores,
                    'method': 'kmeans'
                })
            
            return topics
        
        except Exception as e:
            logger.warning(f"K-means topic extraction failed: {e}")
            return []

    def _combine_topic_results(self, lda_topics: List[Dict], kmeans_topics: List[Dict]) -> List[Dict]:
        """Combine and rank topics from different methods."""
        all_topics = lda_topics + kmeans_topics
        
        # Score topics by uniqueness and coherence
        scored_topics = []
        seen_words = set()
        
        for topic in all_topics:
            words = topic['words'][:5]  # Top 5 words
            
            # Calculate uniqueness (how many new words)
            new_words = set(words) - seen_words
            uniqueness = len(new_words) / len(words) if words else 0
            
            # Calculate coherence (average score of top words)
            coherence = np.mean(topic['scores'][:5]) if topic['scores'] else 0
            
            # Combined score
            combined_score = uniqueness * 0.6 + coherence * 0.4
            
            scored_topics.append({
                'words': words,
                'score': combined_score,
                'method': topic['method'],
                'uniqueness': uniqueness,
                'coherence': coherence
            })
            
            seen_words.update(new_words)
        
        # Sort by score and return top topics
        scored_topics.sort(key=lambda x: x['score'], reverse=True)
        return scored_topics[:10]  # Return top 10 topics

class ContentAnalyzer:
    """Advanced content analysis and metrics calculation."""
    
    def __init__(self):
        self.sentiment_words = self._load_sentiment_lexicon()

    def _load_sentiment_lexicon(self) -> Dict[str, float]:
        """Load or create a simple sentiment lexicon."""
        # Simplified sentiment lexicon (in production, use VADER or TextBlob)
        positive_words = {
            'good': 1.0, 'great': 1.5, 'excellent': 2.0, 'amazing': 1.8, 'wonderful': 1.5,
            'fantastic': 1.8, 'perfect': 2.0, 'outstanding': 1.8, 'superb': 1.6, 'brilliant': 1.7,
            'success': 1.2, 'achieve': 1.0, 'improve': 1.1, 'benefit': 1.0, 'advantage': 1.0
        }
        
        negative_words = {
            'bad': -1.0, 'terrible': -1.8, 'awful': -1.6, 'horrible': -1.7, 'poor': -1.2,
            'fail': -1.5, 'failure': -1.6, 'problem': -1.0, 'issue': -0.8, 'error': -1.0,
            'difficult': -0.8, 'challenge': -0.6, 'risk': -0.9, 'threat': -1.2
        }
        
        return {**positive_words, **negative_words}

    def analyze_content(self, text: str, title: str = "") -> Dict[str, Any]:
        """Comprehensive content analysis."""
        if not text:
            return self._empty_analysis()
        
        try:
            analysis = {
                'word_count': len(text.split()),
                'character_count': len(text),
                'sentence_count': len(re.split(r'[.!?]+', text)),
                'paragraph_count': len(text.split('\n\n')),
                'sentiment_score': self._calculate_sentiment(text),
                'complexity_score': self._calculate_complexity(text),
                'readability_score': self._calculate_readability(text),
                'key_phrases': self._extract_key_phrases(text),
                'entities': self._extract_entities(text),
                'statistics': self._calculate_text_statistics(text)
            }
            
            return analysis
        
        except Exception as e:
            logger.error(f"Content analysis error: {e}")
            return self._empty_analysis()

    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure."""
        return {
            'word_count': 0,
            'character_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
            'sentiment_score': 0.0,
            'complexity_score': 0.0,
            'readability_score': 0.0,
            'key_phrases': [],
            'entities': [],
            'statistics': {}
        }

    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score (-1 to 1)."""
        words = re.findall(r'\b\w+\b', text.lower())
        sentiment_scores = []
        
        for word in words:
            if word in self.sentiment_words:
                sentiment_scores.append(self.sentiment_words[word])
        
        if not sentiment_scores:
            return 0.0
        
        # Normalize to -1 to 1 range
        avg_sentiment = np.mean(sentiment_scores)
        return max(-1.0, min(1.0, avg_sentiment / 2.0))

    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score (0-1)."""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        if not words or not sentences:
            return 0.0
        
        # Average words per sentence
        avg_words_per_sentence = len(words) / len(sentences)
        
        # Average syllables per word (approximated)
        total_syllables = sum(self._count_syllables(word) for word in words)
        avg_syllables_per_word = total_syllables / len(words)
        
        # Flesch-Kincaid complexity (simplified)
        complexity = (avg_words_per_sentence * 0.39) + (avg_syllables_per_word * 11.8) - 15.59
        
        # Normalize to 0-1 scale
        return max(0.0, min(1.0, complexity / 100.0))

    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (0-1, higher is more readable)."""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        if not words or not sentences:
            return 0.5
        
        # Flesch Reading Ease Score (simplified)
        avg_sentence_length = len(words) / len(sentences)
        
        # Count complex words (>2 syllables)
        complex_words = sum(1 for word in words if self._count_syllables(word) > 2)
        complex_word_ratio = complex_words / len(words)
        
        # Flesch formula
        readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * complex_word_ratio)
        
        # Normalize to 0-1 scale (100 = very easy, 0 = very difficult)
        return max(0.0, min(1.0, readability / 100.0))

    def _count_syllables(self, word: str) -> int:
        """Approximate syllable count."""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        # Adjust for silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)

    def _extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """Extract key phrases from text."""
        # Simple n-gram extraction
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did'
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Generate bigrams and trigrams
        phrases = []
        
        # Bigrams
        for i in range(len(filtered_words) - 1):
            phrase = f"{filtered_words[i]} {filtered_words[i+1]}"
            phrases.append(phrase)
        
        # Trigrams
        for i in range(len(filtered_words) - 2):
            phrase = f"{filtered_words[i]} {filtered_words[i+1]} {filtered_words[i+2]}"
            phrases.append(phrase)
        
        # Count and return most frequent
        phrase_counts = Counter(phrases)
        return [phrase for phrase, count in phrase_counts.most_common(max_phrases)]

    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities (simplified)."""
        # Look for capitalized words (potential proper nouns)
        entities = []
        words = text.split()
        
        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            if (clean_word and clean_word[0].isupper() and 
                len(clean_word) > 2 and clean_word.isalpha()):
                entities.append(clean_word)
        
        # Return unique entities
        return list(set(entities))

    def _calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """Calculate detailed text statistics."""
        words = text.split()
        chars = list(text)
        
        return {
            'avg_word_length': np.mean([len(word) for word in words]) if words else 0,
            'unique_words': len(set(words)),
            'lexical_diversity': len(set(words)) / len(words) if words else 0,
            'uppercase_ratio': sum(1 for c in chars if c.isupper()) / len(chars) if chars else 0,
            'punctuation_ratio': sum(1 for c in chars if not c.isalnum() and not c.isspace()) / len(chars) if chars else 0
        }

class DocumentCategorizer:
    """Intelligent document categorization system."""
    
    def __init__(self):
        self.categories = {
            'technical': {
                'keywords': ['api', 'code', 'software', 'programming', 'development', 'system',
                           'function', 'method', 'class', 'algorithm', 'database', 'server'],
                'patterns': [r'\b(def|class|function|method)\b', r'\b\w+\(\)', r'[A-Z][a-z]*[A-Z]']
            },
            'business': {
                'keywords': ['business', 'market', 'customer', 'revenue', 'profit', 'strategy',
                           'management', 'operations', 'sales', 'marketing', 'finance'],
                'patterns': [r'\$\d+', r'\d+%', r'\b(ROI|KPI|revenue|profit)\b']
            },
            'research': {
                'keywords': ['study', 'research', 'analysis', 'methodology', 'hypothesis',
                           'experiment', 'data', 'results', 'conclusion', 'findings'],
                'patterns': [r'\b(Figure|Table|Chart)\s+\d+', r'\b(et al|ibid|ref)\b']
            },
            'documentation': {
                'keywords': ['guide', 'manual', 'tutorial', 'instruction', 'how to', 'setup',
                           'configuration', 'installation', 'usage', 'example'],
                'patterns': [r'\b(step|chapter|section)\s+\d+', r'^\s*\d+\.', r'^\s*[*-]']
            },
            'legal': {
                'keywords': ['contract', 'agreement', 'terms', 'conditions', 'policy',
                           'compliance', 'regulation', 'law', 'legal', 'rights'],
                'patterns': [r'\b(section|clause|article)\s+\d+', r'\b(shall|whereas|hereby)\b']
            }
        }

    def categorize_document(self, content: str, title: str = "", metadata: Dict = None) -> List[ContentCategory]:
        """Categorize document into multiple categories with confidence scores."""
        if not content:
            return []
        
        categories = []
        content_lower = content.lower()
        title_lower = title.lower() if title else ""
        
        for category, rules in self.categories.items():
            confidence = self._calculate_category_confidence(
                content_lower, title_lower, rules, metadata or {}
            )
            
            if confidence > 0.1:  # Minimum confidence threshold
                keywords_found = self._find_matching_keywords(content_lower, rules['keywords'])
                reasoning = self._generate_categorization_reasoning(
                    category, confidence, keywords_found
                )
                
                categories.append(ContentCategory(
                    category=category,
                    confidence=confidence,
                    keywords=keywords_found,
                    reasoning=reasoning
                ))
        
        # Sort by confidence
        categories.sort(key=lambda x: x.confidence, reverse=True)
        return categories

    def _calculate_category_confidence(self, content: str, title: str, 
                                     rules: Dict, metadata: Dict) -> float:
        """Calculate confidence score for a category."""
        score = 0.0
        
        # Keyword matching in content
        keyword_matches = sum(1 for keyword in rules['keywords'] if keyword in content)
        keyword_score = keyword_matches / len(rules['keywords'])
        score += keyword_score * 0.4
        
        # Keyword matching in title (higher weight)
        title_matches = sum(1 for keyword in rules['keywords'] if keyword in title)
        title_score = title_matches / len(rules['keywords'])
        score += title_score * 0.3
        
        # Pattern matching
        pattern_matches = 0
        for pattern in rules['patterns']:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                pattern_matches += 1
        pattern_score = pattern_matches / len(rules['patterns'])
        score += pattern_score * 0.2
        
        # File type bonus
        file_type = metadata.get('file_type', '').lower()
        if file_type:
            type_bonus = self._get_file_type_bonus(file_type, rules)
            score += type_bonus * 0.1
        
        return min(score, 1.0)

    def _find_matching_keywords(self, content: str, keywords: List[str]) -> List[str]:
        """Find keywords that match in the content."""
        return [keyword for keyword in keywords if keyword in content]

    def _generate_categorization_reasoning(self, category: str, confidence: float, 
                                         keywords: List[str]) -> str:
        """Generate human-readable reasoning for categorization."""
        if confidence > 0.7:
            strength = "strong"
        elif confidence > 0.4:
            strength = "moderate"
        else:
            strength = "weak"
        
        keyword_text = ", ".join(keywords[:5]) if keywords else "pattern matching"
        
        return f"{strength.capitalize()} {category} classification based on: {keyword_text}"

    def _get_file_type_bonus(self, file_type: str, rules: Dict) -> float:
        """Get bonus score based on file type relevance."""
        type_bonuses = {
            'technical': {'py': 0.8, 'js': 0.8, 'java': 0.8, 'cpp': 0.8, 'json': 0.6, 'yaml': 0.6},
            'business': {'xlsx': 0.7, 'csv': 0.5, 'ppt': 0.6},
            'research': {'pdf': 0.5, 'tex': 0.8},
            'documentation': {'md': 0.7, 'rst': 0.7, 'txt': 0.4},
            'legal': {'pdf': 0.6, 'doc': 0.5}
        }
        
        category = rules.get('category', '')
        return type_bonuses.get(category, {}).get(file_type, 0.0)

class DocumentAnalyticsEngine:
    """Main document analytics engine."""
    
    def __init__(self):
        self.rag_system = get_rag_system()
        self.doc_manager = DocumentManager()
        self.topic_extractor = TopicExtractor()
        self.content_analyzer = ContentAnalyzer()
        self.categorizer = DocumentCategorizer()
        self.cache = get_document_cache()
        
        # Analytics storage
        self.document_insights = {}
        self.collection_insights = None
        self.last_analysis_time = None

    async def analyze_document(self, doc_id: str, force_refresh: bool = False) -> Optional[DocumentInsight]:
        """Analyze a single document and generate insights."""
        try:
            # Check cache
            cache_key = f"doc_analysis_{doc_id}"
            if not force_refresh:
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    return DocumentInsight(**cached_result)
            
            # Get document data
            doc_metadata = self.doc_manager.get_document(doc_id)
            if not doc_metadata:
                return None
            
            # Get document content from ChromaDB
            results = self.rag_system.collection.get(
                where={"doc_id": doc_id},
                include=["documents", "metadatas"]
            )
            
            if not results or not results['documents']:
                return None
            
            content = ' '.join(results['documents'])
            
            # Analyze content
            content_analysis = self.content_analyzer.analyze_content(content, doc_metadata.title)
            
            # Categorize document
            categories = self.categorizer.categorize_document(
                content, doc_metadata.title, doc_metadata.to_dict()
            )
            
            # Extract topics (for this document)
            topics_result = self.topic_extractor.extract_topics([content], num_topics=3)
            key_topics = [topic['words'][:3] for topic in topics_result['topics'][:3]]
            key_topics = [' '.join(words) for words in key_topics]
            
            # Find related documents
            related_docs = await self._find_related_documents(doc_id, content)
            
            # Generate summary
            summary = self._generate_summary(content, content_analysis)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(
                content_analysis, doc_metadata.to_dict()
            )
            
            # Create insight object
            insight = DocumentInsight(
                doc_id=doc_id,
                title=doc_metadata.title,
                content_summary=summary,
                key_topics=key_topics,
                sentiment_score=content_analysis['sentiment_score'],
                complexity_score=content_analysis['complexity_score'],
                readability_score=content_analysis['readability_score'],
                word_count=content_analysis['word_count'],
                unique_concepts=content_analysis['key_phrases'][:10],
                related_documents=related_docs,
                quality_metrics=quality_metrics,
                generated_at=datetime.now()
            )
            
            # Cache result
            self.cache.put(cache_key, asdict(insight), ttl=3600)  # 1 hour TTL
            
            return insight
        
        except Exception as e:
            logger.error(f"Document analysis error for {doc_id}: {e}")
            return None

    async def analyze_collection(self, force_refresh: bool = False) -> Optional[CollectionInsights]:
        """Analyze the entire document collection."""
        try:
            # Check if recent analysis exists
            if (not force_refresh and self.collection_insights and 
                self.last_analysis_time and 
                (datetime.now() - self.last_analysis_time).seconds < 1800):  # 30 minutes
                return self.collection_insights
            
            # Get all documents
            documents = self.doc_manager.list_documents()
            if not documents:
                return None
            
            # Collect all document content and metadata
            all_content = []
            all_metadata = []
            doc_analyses = []
            
            for doc in documents:
                doc_id = doc.get('doc_id')
                if doc_id:
                    # Analyze individual document
                    doc_insight = await self.analyze_document(doc_id)
                    if doc_insight:
                        doc_analyses.append(doc_insight)
                        
                        # Get content for collection analysis
                        results = self.rag_system.collection.get(
                            where={"doc_id": doc_id},
                            include=["documents"]
                        )
                        if results and results['documents']:
                            content = ' '.join(results['documents'])
                            all_content.append(content)
                            all_metadata.append(doc)
            
            if not all_content:
                return None
            
            # Extract collection-level topics
            topics_result = self.topic_extractor.extract_topics(all_content, num_topics=10)
            
            # Calculate collection metrics
            total_words = sum(analysis.word_count for analysis in doc_analyses)
            avg_doc_length = total_words / len(doc_analyses) if doc_analyses else 0
            
            # Topic distribution
            topic_distribution = {}
            for analysis in doc_analyses:
                for topic in analysis.key_topics:
                    topic_distribution[topic] = topic_distribution.get(topic, 0) + 1
            
            # Content type distribution
            content_types = {}
            for doc in all_metadata:
                file_type = doc.get('file_type', 'unknown')
                content_types[file_type] = content_types.get(file_type, 0) + 1
            
            # Upload trends (by month)
            upload_trends = {}
            for doc in all_metadata:
                upload_time = doc.get('upload_timestamp')
                if upload_time:
                    try:
                        date = datetime.fromisoformat(upload_time)
                        month_key = date.strftime('%Y-%m')
                        upload_trends[month_key] = upload_trends.get(month_key, 0) + 1
                    except:
                        pass
            
            # Quality distribution
            quality_distribution = {'high': 0, 'medium': 0, 'low': 0}
            for analysis in doc_analyses:
                avg_quality = np.mean(list(analysis.quality_metrics.values()))
                if avg_quality > 0.7:
                    quality_distribution['high'] += 1
                elif avg_quality > 0.4:
                    quality_distribution['medium'] += 1
                else:
                    quality_distribution['low'] += 1
            
            # Top keywords across collection
            all_keywords = []
            for analysis in doc_analyses:
                all_keywords.extend(analysis.unique_concepts)
            top_keywords = Counter(all_keywords).most_common(20)
            
            # Document clustering
            document_clusters = self._cluster_documents(doc_analyses)
            
            # Sentiment analysis
            sentiment_scores = [analysis.sentiment_score for analysis in doc_analyses]
            sentiment_analysis = {
                'average': np.mean(sentiment_scores) if sentiment_scores else 0,
                'positive_docs': sum(1 for s in sentiment_scores if s > 0.1),
                'negative_docs': sum(1 for s in sentiment_scores if s < -0.1),
                'neutral_docs': sum(1 for s in sentiment_scores if -0.1 <= s <= 0.1)
            }
            
            # Create collection insights
            insights = CollectionInsights(
                total_documents=len(documents),
                total_words=total_words,
                avg_document_length=avg_doc_length,
                topic_distribution=topic_distribution,
                content_types=content_types,
                upload_trends=upload_trends,
                quality_distribution=quality_distribution,
                top_keywords=top_keywords,
                document_clusters=document_clusters,
                sentiment_analysis=sentiment_analysis,
                generated_at=datetime.now()
            )
            
            self.collection_insights = insights
            self.last_analysis_time = datetime.now()
            
            return insights
        
        except Exception as e:
            logger.error(f"Collection analysis error: {e}")
            return None

    async def _find_related_documents(self, doc_id: str, content: str, max_related: int = 5) -> List[str]:
        """Find documents related to the given document."""
        try:
            # Use RAG system to find similar documents
            query = content[:500]  # Use first part of content as query
            similar_docs = self.rag_system.adaptive_retrieval(query, max_chunks=max_related * 2)
            
            # Filter out the current document and extract unique doc_ids
            related_ids = []
            seen_ids = {doc_id}
            
            for doc in similar_docs:
                related_id = doc.get('doc_id')
                if related_id and related_id not in seen_ids:
                    related_ids.append(related_id)
                    seen_ids.add(related_id)
                    
                    if len(related_ids) >= max_related:
                        break
            
            return related_ids
        
        except Exception as e:
            logger.warning(f"Error finding related documents: {e}")
            return []

    def _generate_summary(self, content: str, analysis: Dict, max_length: int = 200) -> str:
        """Generate a summary of the document content."""
        if not content:
            return "No content available"
        
        # Simple extractive summarization
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) <= 2:
            return content[:max_length]
        
        # Score sentences by keyword frequency
        keywords = analysis.get('key_phrases', [])[:5]
        scored_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # Score based on keyword presence
            score = sum(1 for keyword in keywords if keyword.lower() in sentence.lower())
            # Bonus for position (earlier sentences often more important)
            position_bonus = (len(sentences) - sentences.index(sentence)) / len(sentences)
            total_score = score + position_bonus * 0.5
            
            scored_sentences.append((total_score, sentence))
        
        # Sort by score and take top sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        
        summary_parts = []
        current_length = 0
        
        for score, sentence in scored_sentences:
            if current_length + len(sentence) <= max_length:
                summary_parts.append(sentence)
                current_length += len(sentence)
            else:
                break
        
        summary = '. '.join(summary_parts)
        return summary + "..." if len(content) > len(summary) else summary

    def _calculate_quality_metrics(self, analysis: Dict, metadata: Dict) -> Dict[str, float]:
        """Calculate quality metrics for a document."""
        metrics = {}
        
        # Content completeness
        word_count = analysis.get('word_count', 0)
        metrics['completeness'] = min(word_count / 1000.0, 1.0)  # Normalize to 1000 words
        
        # Readability
        metrics['readability'] = analysis.get('readability_score', 0.5)
        
        # Structure quality (based on paragraph count vs content length)
        para_count = analysis.get('paragraph_count', 1)
        structure_score = min(para_count / max(word_count / 200, 1), 1.0)
        metrics['structure'] = structure_score
        
        # Lexical diversity
        lexical_diversity = analysis.get('statistics', {}).get('lexical_diversity', 0.5)
        metrics['vocabulary'] = lexical_diversity
        
        # PDF extraction quality (if applicable)
        pdf_quality = metadata.get('quality_score')
        if pdf_quality is not None:
            metrics['extraction_quality'] = pdf_quality
        
        return metrics

    def _cluster_documents(self, doc_analyses: List[DocumentInsight], num_clusters: int = 5) -> List[Dict[str, Any]]:
        """Cluster documents by similarity."""
        try:
            if len(doc_analyses) < 2:
                return []
            
            # Create feature vectors from key topics and concepts
            feature_texts = []
            for analysis in doc_analyses:
                text = ' '.join(analysis.key_topics + analysis.unique_concepts[:5])
                feature_texts.append(text)
            
            # Vectorize
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            vectors = vectorizer.fit_transform(feature_texts)
            
            # Cluster
            actual_clusters = min(num_clusters, len(doc_analyses) // 2)
            if actual_clusters < 2:
                return []
            
            kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(vectors)
            
            # Group documents by cluster
            clusters = []
            for cluster_id in range(actual_clusters):
                cluster_docs = []
                cluster_topics = []
                
                for i, label in enumerate(cluster_labels):
                    if label == cluster_id:
                        analysis = doc_analyses[i]
                        cluster_docs.append({
                            'doc_id': analysis.doc_id,
                            'title': analysis.title
                        })
                        cluster_topics.extend(analysis.key_topics)
                
                # Find most common topics in cluster
                topic_counts = Counter(cluster_topics)
                top_topics = [topic for topic, count in topic_counts.most_common(3)]
                
                clusters.append({
                    'id': cluster_id,
                    'documents': cluster_docs,
                    'topics': top_topics,
                    'size': len(cluster_docs)
                })
            
            return clusters
        
        except Exception as e:
            logger.warning(f"Document clustering error: {e}")
            return []

    async def get_trending_topics(self, time_period: str = 'week') -> List[Dict[str, Any]]:
        """Get trending topics over a time period."""
        try:
            # Define time range
            now = datetime.now()
            if time_period == 'day':
                start_date = now - timedelta(days=1)
            elif time_period == 'week':
                start_date = now - timedelta(weeks=1)
            elif time_period == 'month':
                start_date = now - timedelta(days=30)
            else:
                start_date = now - timedelta(weeks=1)  # default
            
            # Get documents from time period
            all_docs = self.doc_manager.list_documents()
            recent_docs = []
            
            for doc in all_docs:
                upload_time = doc.get('upload_timestamp')
                if upload_time:
                    try:
                        upload_date = datetime.fromisoformat(upload_time)
                        if upload_date >= start_date:
                            recent_docs.append(doc)
                    except:
                        pass
            
            if not recent_docs:
                return []
            
            # Analyze topics in recent documents
            recent_content = []
            for doc in recent_docs:
                doc_id = doc.get('doc_id')
                if doc_id:
                    results = self.rag_system.collection.get(
                        where={"doc_id": doc_id},
                        include=["documents"]
                    )
                    if results and results['documents']:
                        content = ' '.join(results['documents'])
                        recent_content.append(content)
            
            if not recent_content:
                return []
            
            # Extract topics
            topics_result = self.topic_extractor.extract_topics(recent_content, num_topics=10)
            
            # Format for output
            trending_topics = []
            for i, topic in enumerate(topics_result['topics']):
                trending_topics.append({
                    'rank': i + 1,
                    'topic': ' '.join(topic['words'][:3]),
                    'keywords': topic['words'][:5],
                    'score': topic['score'],
                    'document_count': len(recent_docs)
                })
            
            return trending_topics
        
        except Exception as e:
            logger.error(f"Trending topics error: {e}")
            return []

# Global instance
_analytics_engine_instance = None

def get_analytics_engine() -> DocumentAnalyticsEngine:
    """Get global analytics engine instance."""
    global _analytics_engine_instance
    if _analytics_engine_instance is None:
        _analytics_engine_instance = DocumentAnalyticsEngine()
    return _analytics_engine_instance