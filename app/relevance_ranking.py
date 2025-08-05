"""
Authored by: AI/ML Engineer (jackson)
Date: 2025-08-05

Advanced Relevance Ranking System

ML-powered search result ranking with learning from user feedback,
personalization, and multi-factor relevance scoring optimization.
"""

import os
import json
import time
import logging
from typing import List, Dict, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
import math
import asyncio
from enum import Enum
import pickle

import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import ndcg_score, mean_squared_error
from sklearn.model_selection import train_test_split

from search_engine import SearchResult, get_search_engine
from search_analytics import get_search_analytics_engine, EventType
from document_analytics import get_analytics_engine
from intelligent_tagging import get_tagging_system
from performance_cache import get_rag_query_cache
from error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

@dataclass
class RankingFeatures:
    """Features used for relevance ranking."""
    # Content relevance
    semantic_similarity: float
    keyword_match_score: float
    title_match_score: float
    content_quality: float
    
    # Document characteristics
    document_age_days: float
    document_length: int
    document_type_score: float
    authority_score: float
    
    # User interaction
    historical_ctr: float  # Click-through rate
    avg_dwell_time: float
    bookmark_rate: float
    share_rate: float
    
    # Query-document matching
    query_document_topic_alignment: float
    intent_match_score: float
    complexity_match: float
    
    # Personalization
    user_preference_score: float
    similar_user_engagement: float
    content_type_affinity: float
    
    # Context
    recency_boost: float
    trending_score: float
    collection_popularity: float

@dataclass
class RankingFeedback:
    """User feedback for ranking model training."""
    query: str
    document_id: str
    position: int
    clicked: bool
    dwell_time_seconds: float
    satisfaction_score: Optional[float]  # 1-5 scale
    user_id: Optional[str]
    session_id: str
    timestamp: datetime

@dataclass
class PersonalizationProfile:
    """User personalization profile for ranking."""
    user_id: str
    content_type_preferences: Dict[str, float]
    topic_preferences: Dict[str, float]
    complexity_preference: float  # 0-1, higher = prefers complex content
    recency_preference: float  # 0-1, higher = prefers recent content
    authority_preference: float  # 0-1, higher = prefers authoritative sources
    avg_session_length: float
    search_expertise: float  # 0-1, higher = expert searcher
    created_at: datetime
    updated_at: datetime

class FeatureExtractor:
    """Extracts features for relevance ranking."""
    
    def __init__(self):
        self.analytics_engine = get_analytics_engine()
        self.tagging_system = get_tagging_system()
        self.search_analytics = get_search_analytics_engine()
        self.cache = get_rag_query_cache()
        
        # Feature caches
        self.document_features_cache = {}
        self.user_features_cache = {}

    async def extract_features(self, query: str, search_results: List[SearchResult],
                             user_id: Optional[str] = None) -> List[RankingFeatures]:
        """Extract ranking features for search results."""
        try:
            features_list = []
            
            # Get query features
            query_features = await self._extract_query_features(query)
            
            # Get user features
            user_features = await self._extract_user_features(user_id) if user_id else {}
            
            # Process each result
            for result in search_results:
                features = await self._extract_result_features(
                    query, result, query_features, user_features
                )
                features_list.append(features)
            
            return features_list
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return []

    async def _extract_query_features(self, query: str) -> Dict[str, Any]:
        """Extract features from the query."""
        return {
            'query_length': len(query.split()),
            'query_complexity': self._calculate_query_complexity(query),
            'query_intent': self._classify_query_intent(query),
            'query_specificity': self._calculate_query_specificity(query)
        }

    async def _extract_user_features(self, user_id: str) -> Dict[str, Any]:
        """Extract user-specific features."""
        if user_id in self.user_features_cache:
            return self.user_features_cache[user_id]
        
        try:
            # Get user behavior profile
            behavior_profile = await self.search_analytics.behavior_analyzer.analyze_user_behavior(user_id)
            
            if behavior_profile:
                features = {
                    'user_expertise': self._map_expertise_to_score(behavior_profile.expertise_level),
                    'avg_session_duration': behavior_profile.avg_session_duration,
                    'content_preferences': behavior_profile.favorite_content_types,
                    'search_patterns': behavior_profile.search_patterns
                }
            else:
                features = {
                    'user_expertise': 0.5,  # neutral
                    'avg_session_duration': 300.0,  # 5 minutes default
                    'content_preferences': [],
                    'search_patterns': []
                }
            
            self.user_features_cache[user_id] = features
            return features
            
        except Exception as e:
            logger.debug(f"User feature extraction error: {e}")
            return {}

    async def _extract_result_features(self, query: str, result: SearchResult,
                                     query_features: Dict[str, Any],
                                     user_features: Dict[str, Any]) -> RankingFeatures:
        """Extract features for a specific search result."""
        try:
            # Content relevance features
            semantic_similarity = result.semantic_score
            keyword_match_score = result.keyword_score
            title_match_score = self._calculate_title_match(query, result.title)
            content_quality = await self._get_content_quality(result.doc_id)
            
            # Document characteristics
            doc_age_days = self._calculate_document_age(result.metadata)
            doc_length = len(result.content.split()) if result.content else 0
            doc_type_score = self._calculate_document_type_score(result.metadata)
            authority_score = self._calculate_authority_score(result.source, result.metadata)
            
            # User interaction features
            interaction_features = await self._get_interaction_features(result.doc_id)
            
            # Query-document matching
            topic_alignment = await self._calculate_topic_alignment(query, result.doc_id)
            intent_match = self._calculate_intent_match(query_features, result)
            complexity_match = self._calculate_complexity_match(query_features, result.metadata)
            
            # Personalization features
            personalization_features = self._calculate_personalization_features(
                result, user_features
            )
            
            # Context features
            recency_boost = self._calculate_recency_boost(result.metadata)
            trending_score = await self._calculate_trending_score(result.doc_id)
            popularity_score = await self._calculate_popularity_score(result.doc_id)
            
            return RankingFeatures(
                semantic_similarity=semantic_similarity,
                keyword_match_score=keyword_match_score,
                title_match_score=title_match_score,
                content_quality=content_quality,
                document_age_days=doc_age_days,
                document_length=doc_length,
                document_type_score=doc_type_score,
                authority_score=authority_score,
                historical_ctr=interaction_features.get('ctr', 0.0),
                avg_dwell_time=interaction_features.get('dwell_time', 0.0),
                bookmark_rate=interaction_features.get('bookmark_rate', 0.0),
                share_rate=interaction_features.get('share_rate', 0.0),
                query_document_topic_alignment=topic_alignment,
                intent_match_score=intent_match,
                complexity_match=complexity_match,
                user_preference_score=personalization_features.get('preference_score', 0.5),
                similar_user_engagement=personalization_features.get('similar_engagement', 0.5),
                content_type_affinity=personalization_features.get('type_affinity', 0.5),
                recency_boost=recency_boost,
                trending_score=trending_score,
                collection_popularity=popularity_score
            )
            
        except Exception as e:
            logger.warning(f"Result feature extraction error: {e}")
            # Return default features
            return RankingFeatures(
                semantic_similarity=result.semantic_score,
                keyword_match_score=result.keyword_score,
                title_match_score=0.5,
                content_quality=0.5,
                document_age_days=30.0,
                document_length=500,
                document_type_score=0.5,
                authority_score=0.5,
                historical_ctr=0.0,
                avg_dwell_time=0.0,
                bookmark_rate=0.0,
                share_rate=0.0,
                query_document_topic_alignment=0.5,
                intent_match_score=0.5,
                complexity_match=0.5,
                user_preference_score=0.5,
                similar_user_engagement=0.5,
                content_type_affinity=0.5,
                recency_boost=0.5,
                trending_score=0.5,
                collection_popularity=0.5
            )

    def _calculate_query_complexity(self, query: str) -> float:
        """Calculate query complexity score."""
        # Simple heuristics
        word_count = len(query.split())
        has_operators = any(op in query.lower() for op in ['and', 'or', 'not', '"'])
        has_filters = ':' in query or '[' in query
        
        complexity = word_count / 20.0  # Normalize by 20 words
        if has_operators:
            complexity += 0.3
        if has_filters:
            complexity += 0.2
        
        return min(complexity, 1.0)

    def _classify_query_intent(self, query: str) -> str:
        """Classify query intent."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['what', 'how', 'why', 'where', 'when']):
            return 'question'
        elif any(word in query_lower for word in ['compare', 'vs', 'difference']):
            return 'comparison'
        elif any(word in query_lower for word in ['tutorial', 'guide', 'how to']):
            return 'learning'
        else:
            return 'informational'

    def _calculate_query_specificity(self, query: str) -> float:
        """Calculate how specific the query is."""
        words = query.split()
        
        # More words generally mean more specific
        specificity = min(len(words) / 10.0, 1.0)
        
        # Quoted phrases indicate specificity
        if '"' in query:
            specificity += 0.2
        
        # Technical terms indicate specificity
        technical_indicators = ['api', 'function', 'method', 'class', 'algorithm']
        if any(term in query.lower() for term in technical_indicators):
            specificity += 0.1
        
        return min(specificity, 1.0)

    def _map_expertise_to_score(self, expertise_level: str) -> float:
        """Map expertise level to numeric score."""
        mapping = {
            'novice': 0.2,
            'intermediate': 0.5,
            'expert': 0.8
        }
        return mapping.get(expertise_level, 0.5)

    def _calculate_title_match(self, query: str, title: str) -> float:
        """Calculate how well the query matches the title."""
        if not query or not title:
            return 0.0
        
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        
        intersection = query_words.intersection(title_words)
        union = query_words.union(title_words)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)

    async def _get_content_quality(self, doc_id: str) -> float:
        """Get content quality score for document."""
        try:
            doc_insight = await self.analytics_engine.analyze_document(doc_id)
            if doc_insight and doc_insight.quality_metrics:
                return np.mean(list(doc_insight.quality_metrics.values()))
            return 0.5
        except Exception:
            return 0.5

    def _calculate_document_age(self, metadata: Dict[str, Any]) -> float:
        """Calculate document age in days."""
        try:
            upload_time = metadata.get('upload_timestamp')
            if upload_time:
                upload_date = datetime.fromisoformat(upload_time)
                return (datetime.now() - upload_date).days
            return 30.0  # Default
        except Exception:
            return 30.0

    def _calculate_document_type_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate document type relevance score."""
        doc_type = metadata.get('document_type', 'plain_text')
        
        # Score different document types
        type_scores = {
            'technical': 0.9,
            'documentation': 0.8,
            'tutorial': 0.7,
            'plain_text': 0.5,
            'presentation': 0.6,
            'spreadsheet': 0.4
        }
        
        return type_scores.get(doc_type, 0.5)

    def _calculate_authority_score(self, source: str, metadata: Dict[str, Any]) -> float:
        """Calculate document authority score."""
        # Simple authority scoring based on source
        if 'official' in source.lower() or 'docs' in source.lower():
            return 0.9
        elif 'wiki' in source.lower():
            return 0.7
        elif source.startswith('http'):
            return 0.6
        else:
            return 0.5

    async def _get_interaction_features(self, doc_id: str) -> Dict[str, float]:
        """Get user interaction features for document."""
        try:
            # This would analyze historical click data
            # For now, return placeholder values
            return {
                'ctr': 0.1,  # 10% CTR
                'dwell_time': 120.0,  # 2 minutes average
                'bookmark_rate': 0.05,
                'share_rate': 0.02
            }
        except Exception:
            return {'ctr': 0.0, 'dwell_time': 0.0, 'bookmark_rate': 0.0, 'share_rate': 0.0}

    async def _calculate_topic_alignment(self, query: str, doc_id: str) -> float:
        """Calculate topic alignment between query and document."""
        try:
            # Get document tags
            doc_tags = await self.tagging_system.tag_document(doc_id)
            if not doc_tags:
                return 0.5
            
            # Get query-based tag suggestions
            query_tags = await self.tagging_system.get_tag_suggestions_for_query(query)
            
            # Calculate overlap
            doc_tag_names = {tag.name for tag in doc_tags.tags}
            query_tag_set = set(query_tags)
            
            if not doc_tag_names or not query_tag_set:
                return 0.5
            
            intersection = doc_tag_names.intersection(query_tag_set)
            union = doc_tag_names.union(query_tag_set)
            
            return len(intersection) / len(union) if union else 0.5
            
        except Exception:
            return 0.5

    def _calculate_intent_match(self, query_features: Dict[str, Any], result: SearchResult) -> float:
        """Calculate how well the result matches query intent."""
        query_intent = query_features.get('query_intent', 'informational')
        
        # Simple intent matching based on metadata
        doc_type = result.metadata.get('document_type', 'plain_text')
        
        intent_type_alignment = {
            'question': {'documentation': 0.9, 'tutorial': 0.7, 'plain_text': 0.6},
            'comparison': {'technical': 0.8, 'documentation': 0.9, 'plain_text': 0.7},
            'learning': {'tutorial': 0.9, 'documentation': 0.8, 'plain_text': 0.6},
            'informational': {'plain_text': 0.8, 'documentation': 0.7, 'technical': 0.6}
        }
        
        alignment = intent_type_alignment.get(query_intent, {})
        return alignment.get(doc_type, 0.5)

    def _calculate_complexity_match(self, query_features: Dict[str, Any], metadata: Dict[str, Any]) -> float:
        """Calculate complexity alignment between query and document."""
        query_complexity = query_features.get('query_complexity', 0.5)
        
        # Estimate document complexity from metadata
        doc_complexity = 0.5  # Default
        
        # Adjust based on document type
        doc_type = metadata.get('document_type', 'plain_text')
        if doc_type == 'technical':
            doc_complexity = 0.8
        elif doc_type == 'tutorial':
            doc_complexity = 0.3
        elif doc_type == 'documentation':
            doc_complexity = 0.6
        
        # Calculate match (prefer similar complexity levels)
        complexity_diff = abs(query_complexity - doc_complexity)
        return 1.0 - complexity_diff

    def _calculate_personalization_features(self, result: SearchResult, 
                                          user_features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate personalization features."""
        if not user_features:
            return {'preference_score': 0.5, 'similar_engagement': 0.5, 'type_affinity': 0.5}
        
        # Content type affinity
        doc_type = result.metadata.get('document_type', 'plain_text')
        user_preferences = user_features.get('content_preferences', [])
        type_affinity = 0.8 if doc_type in user_preferences else 0.4
        
        return {
            'preference_score': 0.5,  # Placeholder
            'similar_engagement': 0.5,  # Placeholder
            'type_affinity': type_affinity
        }

    def _calculate_recency_boost(self, metadata: Dict[str, Any]) -> float:
        """Calculate recency boost factor."""
        try:
            upload_time = metadata.get('upload_timestamp')
            if upload_time:
                upload_date = datetime.fromisoformat(upload_time)
                days_old = (datetime.now() - upload_date).days
                
                # Exponential decay with half-life of 30 days
                return math.exp(-days_old / 30.0)
            return 0.5
        except Exception:
            return 0.5

    async def _calculate_trending_score(self, doc_id: str) -> float:
        """Calculate trending score for document."""
        # This would analyze recent interaction trends
        # For now, return placeholder
        return 0.5

    async def _calculate_popularity_score(self, doc_id: str) -> float:
        """Calculate popularity score in collection."""
        # This would analyze overall document popularity
        # For now, return placeholder
        return 0.5

class RankingModel:
    """ML model for learning-to-rank."""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.model_version = "1.0"
        
        # Training data storage
        self.training_data = []
        self.feedback_data = []

    def train(self, features_list: List[List[RankingFeatures]], 
             relevance_scores: List[List[float]]) -> Dict[str, Any]:
        """Train the ranking model."""
        try:
            if not features_list or not relevance_scores:
                return {'status': 'error', 'message': 'No training data provided'}
            
            # Convert features to numpy arrays
            X = []
            y = []
            
            for features_group, scores_group in zip(features_list, relevance_scores):
                for features, score in zip(features_group, scores_group):
                    feature_vector = self._features_to_vector(features)
                    X.append(feature_vector)
                    y.append(score)
            
            if not X:
                return {'status': 'error', 'message': 'No valid training samples'}
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            y_pred = self.model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            
            self.is_trained = True
            
            return {
                'status': 'success',
                'train_score': train_score,
                'test_score': test_score,
                'mse': mse,
                'n_samples': len(X),
                'n_features': X.shape[1]
            }
            
        except Exception as e:
            logger.error(f"Model training error: {e}")
            return {'status': 'error', 'message': str(e)}

    def predict(self, features_list: List[RankingFeatures]) -> List[float]:
        """Predict relevance scores."""
        try:
            if not self.is_trained or not self.model:
                # Return original scores if model not trained
                return [0.5] * len(features_list)
            
            # Convert to feature vectors
            X = np.array([self._features_to_vector(features) for features in features_list])
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Predict
            predictions = self.model.predict(X_scaled)
            
            # Ensure scores are in [0, 1] range
            predictions = np.clip(predictions, 0.0, 1.0)
            
            return predictions.tolist()
            
        except Exception as e:
            logger.error(f"Model prediction error: {e}")
            return [0.5] * len(features_list)

    def _features_to_vector(self, features: RankingFeatures) -> List[float]:
        """Convert RankingFeatures to feature vector."""
        return [
            features.semantic_similarity,
            features.keyword_match_score,
            features.title_match_score,
            features.content_quality,
            features.document_age_days / 365.0,  # Normalize to years
            min(features.document_length / 5000.0, 1.0),  # Normalize, cap at 5000 words
            features.document_type_score,
            features.authority_score,
            features.historical_ctr,
            features.avg_dwell_time / 600.0,  # Normalize to 10 minutes
            features.bookmark_rate,
            features.share_rate,
            features.query_document_topic_alignment,
            features.intent_match_score,
            features.complexity_match,
            features.user_preference_score,
            features.similar_user_engagement,
            features.content_type_affinity,
            features.recency_boost,
            features.trending_score,
            features.collection_popularity
        ]

    def add_feedback(self, feedback: RankingFeedback):
        """Add user feedback for model improvement."""
        self.feedback_data.append(feedback)

    def save(self, file_path: str):
        """Save trained model."""
        try:
            if self.is_trained and self.model:
                model_data = {
                    'model': self.model,
                    'scaler': self.scaler,
                    'feature_names': self.feature_names,
                    'model_version': self.model_version,
                    'is_trained': self.is_trained
                }
                
                with open(file_path, 'wb') as f:
                    pickle.dump(model_data, f)
                
                logger.info(f"Model saved to {file_path}")
                
        except Exception as e:
            logger.error(f"Model save error: {e}")

    def load(self, file_path: str) -> bool:
        """Load trained model."""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.model = model_data['model']
                self.scaler = model_data['scaler']
                self.feature_names = model_data.get('feature_names', [])
                self.model_version = model_data.get('model_version', '1.0')
                self.is_trained = model_data.get('is_trained', False)
                
                logger.info(f"Model loaded from {file_path}")
                return True
                
        except Exception as e:
            logger.error(f"Model load error: {e}")
        
        return False

class RelevanceRankingEngine:
    """Main relevance ranking engine."""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.ranking_model = RankingModel()
        self.search_engine = get_search_engine()
        self.cache = get_rag_query_cache()
        
        # Load pre-trained model if available
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'ranking_model.pkl')
        if os.path.exists(model_path):
            self.ranking_model.load(model_path)

    async def rank_results(self, query: str, search_results: List[SearchResult],
                          user_id: Optional[str] = None) -> List[SearchResult]:
        """Rank search results using ML model."""
        try:
            if not search_results:
                return []
            
            # Extract features
            features_list = await self.feature_extractor.extract_features(
                query, search_results, user_id
            )
            
            if not features_list:
                return search_results  # Return original order if feature extraction fails
            
            # Predict relevance scores
            relevance_scores = self.ranking_model.predict(features_list)
            
            # Combine with original scores using weighted average
            final_scores = []
            for i, (result, ml_score) in enumerate(zip(search_results, relevance_scores)):
                # Weight: 70% ML score, 30% original relevance score
                combined_score = 0.7 * ml_score + 0.3 * result.relevance_score
                final_scores.append((combined_score, i, result))
            
            # Sort by combined score
            final_scores.sort(key=lambda x: x[0], reverse=True)
            
            # Update results with new scores and positions
            ranked_results = []
            for rank, (score, original_idx, result) in enumerate(final_scores):
                # Create new result with updated ranking
                updated_result = SearchResult(
                    doc_id=result.doc_id,
                    content=result.content,
                    title=result.title,
                    source=result.source,
                    relevance_score=score,
                    semantic_score=result.semantic_score,
                    keyword_score=result.keyword_score,
                    freshness_score=result.freshness_score,
                    quality_score=result.quality_score,
                    snippet=result.snippet,
                    highlights=result.highlights,
                    metadata=result.metadata,
                    rank_position=rank + 1
                )
                ranked_results.append(updated_result)
            
            return ranked_results
            
        except Exception as e:
            logger.error(f"Result ranking error: {e}")
            return search_results  # Return original results on error

    async def add_user_feedback(self, query: str, document_id: str, position: int,
                              clicked: bool, dwell_time_seconds: float = 0.0,
                              satisfaction_score: Optional[float] = None,
                              user_id: Optional[str] = None,
                              session_id: str = "") -> str:
        """Add user feedback for model training."""
        try:
            feedback = RankingFeedback(
                query=query,
                document_id=document_id,
                position=position,
                clicked=clicked,
                dwell_time_seconds=dwell_time_seconds,
                satisfaction_score=satisfaction_score,
                user_id=user_id,
                session_id=session_id,
                timestamp=datetime.now()
            )
            
            self.ranking_model.add_feedback(feedback)
            
            # Cache feedback for batch training
            cache_key = f"ranking_feedback_{datetime.now().date().isoformat()}"
            cached_feedback = self.cache.get(cache_key) or []
            cached_feedback.append(asdict(feedback))
            self.cache.put(cache_key, cached_feedback, ttl=86400)  # 24 hours
            
            return "feedback_recorded"
            
        except Exception as e:
            logger.error(f"Feedback recording error: {e}")
            return "error"

    async def retrain_model(self, min_feedback_samples: int = 100) -> Dict[str, Any]:
        """Retrain ranking model with accumulated feedback."""
        try:
            # Collect feedback from cache
            all_feedback = []
            for days_back in range(30):  # Last 30 days
                date = (datetime.now() - timedelta(days=days_back)).date()
                cache_key = f"ranking_feedback_{date.isoformat()}"
                daily_feedback = self.cache.get(cache_key) or []
                all_feedback.extend(daily_feedback)
            
            if len(all_feedback) < min_feedback_samples:
                return {
                    'status': 'insufficient_data',
                    'message': f'Need at least {min_feedback_samples} feedback samples, got {len(all_feedback)}'
                }
            
            # Prepare training data
            training_features = []
            training_labels = []
            
            # Group feedback by query
            query_groups = defaultdict(list)
            for feedback_dict in all_feedback:
                query_groups[feedback_dict['query']].append(feedback_dict)
            
            # Process each query group
            for query, feedback_list in query_groups.items():
                if len(feedback_list) < 2:  # Need at least 2 results per query
                    continue
                
                # Generate synthetic search results for feature extraction
                # In a real implementation, this would use the actual search results from when the feedback was generated
                search_results = await self._reconstruct_search_results(query, feedback_list)
                
                if search_results:
                    features = await self.feature_extractor.extract_features(query, search_results)
                    
                    # Create relevance labels from feedback
                    labels = []
                    for feedback_dict in feedback_list:
                        # Convert feedback to relevance score
                        score = 0.0
                        if feedback_dict['clicked']:
                            score += 0.5
                        if feedback_dict['dwell_time_seconds'] > 30:
                            score += 0.3
                        if feedback_dict.get('satisfaction_score'):
                            score += feedback_dict['satisfaction_score'] / 5.0 * 0.2
                        
                        labels.append(min(score, 1.0))
                    
                    if len(features) == len(labels):
                        training_features.append(features)
                        training_labels.append(labels)
            
            if not training_features:
                return {
                    'status': 'no_training_data',
                    'message': 'Could not prepare training data from feedback'
                }
            
            # Train model
            training_result = self.ranking_model.train(training_features, training_labels)
            
            # Save model if training was successful
            if training_result.get('status') == 'success':
                model_dir = os.path.join(os.path.dirname(__file__), 'models')
                os.makedirs(model_dir, exist_ok=True)
                model_path = os.path.join(model_dir, 'ranking_model.pkl')
                self.ranking_model.save(model_path)
            
            return training_result
            
        except Exception as e:
            logger.error(f"Model retraining error: {e}")
            return {'status': 'error', 'message': str(e)}

    async def _reconstruct_search_results(self, query: str, feedback_list: List[Dict]) -> List[SearchResult]:
        """Reconstruct search results from feedback for training."""
        # This is a simplified reconstruction
        # In a real implementation, you'd store the original search results
        try:
            # Perform a fresh search to get similar results
            current_results = await self.search_engine.search(query, max_results=20)
            
            # Filter to only documents that have feedback
            feedback_doc_ids = {f['document_id'] for f in feedback_list}
            filtered_results = [r for r in current_results if r.doc_id in feedback_doc_ids]
            
            return filtered_results
            
        except Exception as e:
            logger.debug(f"Result reconstruction error: {e}")
            return []

    async def get_ranking_analytics(self) -> Dict[str, Any]:
        """Get analytics about ranking performance."""
        try:
            return {
                'model_trained': self.ranking_model.is_trained,
                'model_version': self.ranking_model.model_version,
                'feedback_samples': len(self.ranking_model.feedback_data),
                'feature_count': len(self.ranking_model._features_to_vector(
                    RankingFeatures(
                        semantic_similarity=0.0, keyword_match_score=0.0, title_match_score=0.0,
                        content_quality=0.0, document_age_days=0.0, document_length=0,
                        document_type_score=0.0, authority_score=0.0, historical_ctr=0.0,
                        avg_dwell_time=0.0, bookmark_rate=0.0, share_rate=0.0,
                        query_document_topic_alignment=0.0, intent_match_score=0.0,
                        complexity_match=0.0, user_preference_score=0.0,
                        similar_user_engagement=0.0, content_type_affinity=0.0,
                        recency_boost=0.0, trending_score=0.0, collection_popularity=0.0
                    )
                )),
                'cache_status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Ranking analytics error: {e}")
            return {}

# Global instance
_relevance_ranking_engine_instance = None

def get_relevance_ranking_engine() -> RelevanceRankingEngine:
    """Get global relevance ranking engine instance."""
    global _relevance_ranking_engine_instance
    if _relevance_ranking_engine_instance is None:
        _relevance_ranking_engine_instance = RelevanceRankingEngine()
    return _relevance_ranking_engine_instance