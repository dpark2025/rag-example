"""
Authored by: AI/ML Engineer (jackson)
Date: 2025-08-05

Search Analytics & User Behavior Tracking

Comprehensive analytics system for search behavior, user interactions,
and search performance optimization with ML-driven insights.
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
import hashlib
import uuid

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from performance_cache import get_rag_query_cache
from error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of user interaction events."""
    SEARCH_QUERY = "search_query"
    SEARCH_RESULT_CLICK = "search_result_click"
    SEARCH_REFINEMENT = "search_refinement"
    FILTER_APPLIED = "filter_applied"
    FILTER_REMOVED = "filter_removed"
    DOCUMENT_VIEW = "document_view"
    DOCUMENT_DOWNLOAD = "document_download"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SEARCH_ABANDONED = "search_abandoned"
    PAGINATION = "pagination"
    SORT_CHANGED = "sort_changed"

@dataclass
class UserEvent:
    """Individual user interaction event."""
    event_id: str
    event_type: EventType
    timestamp: datetime
    session_id: str
    user_id: Optional[str]
    query: Optional[str]
    document_id: Optional[str]
    position_clicked: Optional[int]
    filters_applied: List[str]
    search_results_count: Optional[int]
    response_time_ms: Optional[float]
    metadata: Dict[str, Any]

@dataclass
class SearchSession:
    """User search session."""
    session_id: str
    user_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    total_queries: int
    successful_queries: int  # queries that led to clicks
    total_clicks: int
    documents_viewed: Set[str]
    query_refinements: int
    filters_used: List[str]
    session_duration_seconds: Optional[float]
    goal_achieved: bool  # heuristic based on user behavior

@dataclass
class QueryAnalysis:
    """Analysis of a search query."""
    query: str
    frequency: int
    success_rate: float  # % of queries that led to clicks
    avg_response_time_ms: float
    avg_results_count: float
    top_clicked_positions: List[int]
    related_queries: List[str]
    user_intent: str  # classified intent
    difficulty_score: float  # how hard it is to satisfy

@dataclass
class SearchTrend:
    """Search trend analysis."""
    metric: str
    time_period: str
    data_points: List[Tuple[datetime, float]]
    trend_direction: str  # increasing, decreasing, stable
    change_rate: float
    significance: float

@dataclass
class UserBehaviorProfile:
    """User behavior analysis profile."""
    user_id: str
    total_sessions: int
    avg_session_duration: float
    favorite_content_types: List[str]
    search_patterns: List[str]
    expertise_level: str  # novice, intermediate, expert
    preferred_filters: List[str]
    peak_usage_hours: List[int]

class EventCollector:
    """Collects and stores user interaction events."""
    
    def __init__(self):
        self.events = []
        self.sessions = {}
        self.event_lock = asyncio.Lock()
        self.cache = get_rag_query_cache()
        
        # Event storage limits
        self.max_events_in_memory = 10000
        self.max_session_age_hours = 24

    async def track_event(self, event_type: EventType, session_id: str,
                         user_id: Optional[str] = None, **kwargs) -> str:
        """Track a user interaction event."""
        try:
            event_id = str(uuid.uuid4())
            
            event = UserEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.now(),
                session_id=session_id,
                user_id=user_id,
                query=kwargs.get('query'),
                document_id=kwargs.get('document_id'),
                position_clicked=kwargs.get('position_clicked'),
                filters_applied=kwargs.get('filters_applied', []),
                search_results_count=kwargs.get('search_results_count'),
                response_time_ms=kwargs.get('response_time_ms'),
                metadata=kwargs.get('metadata', {})
            )
            
            async with self.event_lock:
                self.events.append(event)
                
                # Update session
                self._update_session(event)
                
                # Cleanup old events
                if len(self.events) > self.max_events_in_memory:
                    self._cleanup_old_events()
            
            # Cache recent events for quick access
            self._cache_event(event)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Event tracking error: {e}")
            return ""

    def _update_session(self, event: UserEvent):
        """Update session data with new event."""
        session_id = event.session_id
        
        if session_id not in self.sessions:
            self.sessions[session_id] = SearchSession(
                session_id=session_id,
                user_id=event.user_id,
                start_time=event.timestamp,
                end_time=None,
                total_queries=0,
                successful_queries=0,
                total_clicks=0,
                documents_viewed=set(),
                query_refinements=0,
                filters_used=[],
                session_duration_seconds=None,
                goal_achieved=False
            )
        
        session = self.sessions[session_id]
        session.end_time = event.timestamp
        
        # Update session metrics based on event type
        if event.event_type == EventType.SEARCH_QUERY:
            session.total_queries += 1
        elif event.event_type == EventType.SEARCH_RESULT_CLICK:
            session.total_clicks += 1
            if event.document_id:
                session.documents_viewed.add(event.document_id)
        elif event.event_type == EventType.SEARCH_REFINEMENT:
            session.query_refinements += 1
        elif event.event_type in [EventType.FILTER_APPLIED, EventType.FILTER_REMOVED]:
            if event.filters_applied:
                session.filters_used.extend(event.filters_applied)
        
        # Calculate session duration
        if session.start_time and session.end_time:
            duration = (session.end_time - session.start_time).total_seconds()
            session.session_duration_seconds = duration
        
        # Heuristic for goal achievement
        session.goal_achieved = (
            session.total_clicks > 0 and 
            len(session.documents_viewed) > 0 and
            session.total_queries <= session.total_clicks * 3  # reasonable query-to-click ratio
        )

    def _cleanup_old_events(self):
        """Remove old events from memory."""
        cutoff_time = datetime.now() - timedelta(hours=self.max_session_age_hours)
        
        # Remove old events
        self.events = [e for e in self.events if e.timestamp > cutoff_time]
        
        # Remove old sessions
        old_sessions = [sid for sid, session in self.sessions.items() 
                       if session.end_time and session.end_time < cutoff_time]
        for sid in old_sessions:
            del self.sessions[sid]

    def _cache_event(self, event: UserEvent):
        """Cache event for quick retrieval."""
        try:
            cache_key = f"event_{event.event_id}"
            self.cache.put(cache_key, asdict(event), ttl=3600)  # 1 hour TTL
        except Exception as e:
            logger.debug(f"Event caching error: {e}")

    async def get_events(self, session_id: Optional[str] = None,
                        event_type: Optional[EventType] = None,
                        time_range: Optional[Tuple[datetime, datetime]] = None,
                        limit: int = 1000) -> List[UserEvent]:
        """Get events with optional filtering."""
        try:
            async with self.event_lock:
                filtered_events = self.events.copy()
            
            # Apply filters
            if session_id:
                filtered_events = [e for e in filtered_events if e.session_id == session_id]
            
            if event_type:
                filtered_events = [e for e in filtered_events if e.event_type == event_type]
            
            if time_range:
                start_time, end_time = time_range
                filtered_events = [e for e in filtered_events 
                                 if start_time <= e.timestamp <= end_time]
            
            # Sort by timestamp (newest first) and limit
            filtered_events.sort(key=lambda x: x.timestamp, reverse=True)
            return filtered_events[:limit]
            
        except Exception as e:
            logger.error(f"Event retrieval error: {e}")
            return []

    async def get_session(self, session_id: str) -> Optional[SearchSession]:
        """Get session data."""
        return self.sessions.get(session_id)

    async def get_active_sessions(self) -> List[SearchSession]:
        """Get currently active sessions."""
        cutoff_time = datetime.now() - timedelta(minutes=30)  # 30 minutes of inactivity
        
        active_sessions = []
        for session in self.sessions.values():
            if session.end_time and session.end_time > cutoff_time:
                active_sessions.append(session)
        
        return active_sessions

class QueryAnalyzer:
    """Analyzes search queries and patterns."""
    
    def __init__(self, event_collector: EventCollector):
        self.event_collector = event_collector
        self.query_cache = {}

    async def analyze_query_performance(self, time_period: timedelta = timedelta(days=7)) -> List[QueryAnalysis]:
        """Analyze query performance over a time period."""
        try:
            # Get query events
            end_time = datetime.now()
            start_time = end_time - time_period
            
            query_events = await self.event_collector.get_events(
                event_type=EventType.SEARCH_QUERY,
                time_range=(start_time, end_time)
            )
            
            if not query_events:
                return []
            
            # Group by query
            query_groups = defaultdict(list)
            for event in query_events:
                if event.query:
                    normalized_query = event.query.lower().strip()
                    query_groups[normalized_query].append(event)
            
            # Analyze each query
            analyses = []
            for query, events in query_groups.items():
                analysis = await self._analyze_single_query(query, events)
                if analysis:
                    analyses.append(analysis)
            
            # Sort by frequency
            analyses.sort(key=lambda x: x.frequency, reverse=True)
            return analyses[:50]  # Top 50 queries
            
        except Exception as e:
            logger.error(f"Query analysis error: {e}")
            return []

    async def _analyze_single_query(self, query: str, events: List[UserEvent]) -> Optional[QueryAnalysis]:
        """Analyze a single query's performance."""
        try:
            if not events:
                return None
            
            frequency = len(events)
            
            # Calculate success rate (queries that led to clicks)
            successful_sessions = set()
            total_sessions = set()
            
            for event in events:
                total_sessions.add(event.session_id)
                
                # Check if this session had clicks after the query
                click_events = await self.event_collector.get_events(
                    session_id=event.session_id,
                    event_type=EventType.SEARCH_RESULT_CLICK
                )
                
                # Look for clicks within 5 minutes of the query
                for click_event in click_events:
                    if (click_event.timestamp - event.timestamp).total_seconds() <= 300:
                        successful_sessions.add(event.session_id)
                        break
            
            success_rate = len(successful_sessions) / len(total_sessions) if total_sessions else 0
            
            # Calculate average response time
            response_times = [e.response_time_ms for e in events if e.response_time_ms]
            avg_response_time = np.mean(response_times) if response_times else 0
            
            # Calculate average results count
            results_counts = [e.search_results_count for e in events if e.search_results_count]
            avg_results_count = np.mean(results_counts) if results_counts else 0
            
            # Find top clicked positions
            click_positions = await self._get_click_positions_for_query(query, events)
            
            # Find related queries
            related_queries = await self._find_related_queries(query)
            
            # Classify user intent
            user_intent = self._classify_query_intent(query)
            
            # Calculate difficulty score
            difficulty_score = self._calculate_query_difficulty(
                success_rate, avg_response_time, avg_results_count
            )
            
            return QueryAnalysis(
                query=query,
                frequency=frequency,
                success_rate=success_rate,
                avg_response_time_ms=avg_response_time,
                avg_results_count=avg_results_count,
                top_clicked_positions=click_positions,
                related_queries=related_queries,
                user_intent=user_intent,
                difficulty_score=difficulty_score
            )
            
        except Exception as e:
            logger.warning(f"Single query analysis error: {e}")
            return None

    async def _get_click_positions_for_query(self, query: str, query_events: List[UserEvent]) -> List[int]:
        """Get clicked positions for a query."""
        try:
            click_positions = []
            
            for query_event in query_events:
                # Get clicks in the same session within 5 minutes
                click_events = await self.event_collector.get_events(
                    session_id=query_event.session_id,
                    event_type=EventType.SEARCH_RESULT_CLICK
                )
                
                for click_event in click_events:
                    time_diff = (click_event.timestamp - query_event.timestamp).total_seconds()
                    if 0 <= time_diff <= 300:  # Within 5 minutes after query
                        if click_event.position_clicked:
                            click_positions.append(click_event.position_clicked)
            
            # Return top clicked positions
            position_counts = Counter(click_positions)
            return [pos for pos, count in position_counts.most_common(5)]
            
        except Exception as e:
            logger.debug(f"Click position analysis error: {e}")
            return []

    async def _find_related_queries(self, query: str, max_related: int = 5) -> List[str]:
        """Find queries related to the given query."""
        try:
            # Get all recent queries
            recent_events = await self.event_collector.get_events(
                event_type=EventType.SEARCH_QUERY,
                time_range=(datetime.now() - timedelta(days=30), datetime.now()),
                limit=1000
            )
            
            query_words = set(query.lower().split())
            related_queries = []
            
            for event in recent_events:
                if event.query and event.query.lower() != query.lower():
                    other_words = set(event.query.lower().split())
                    
                    # Calculate word overlap
                    overlap = len(query_words.intersection(other_words))
                    if overlap > 0:
                        similarity = overlap / len(query_words.union(other_words))
                        if similarity > 0.3:  # 30% similarity threshold
                            related_queries.append((event.query, similarity))
            
            # Sort by similarity and return top queries
            related_queries.sort(key=lambda x: x[1], reverse=True)
            return [q for q, sim in related_queries[:max_related]]
            
        except Exception as e:
            logger.debug(f"Related query finding error: {e}")
            return []

    def _classify_query_intent(self, query: str) -> str:
        """Classify query intent using simple heuristics."""
        query_lower = query.lower()
        
        # Question words
        if any(word in query_lower for word in ['what', 'how', 'why', 'where', 'when', 'who']):
            return 'question'
        
        # Comparison words
        if any(word in query_lower for word in ['vs', 'versus', 'compare', 'difference', 'better']):
            return 'comparison'
        
        # Analysis/explanation words
        if any(word in query_lower for word in ['explain', 'analyze', 'understand', 'learn']):
            return 'learning'
        
        # Tutorial/guide words
        if any(word in query_lower for word in ['tutorial', 'guide', 'how to', 'steps']):
            return 'tutorial'
        
        # Problem solving
        if any(word in query_lower for word in ['error', 'problem', 'issue', 'fix', 'troubleshoot']):
            return 'troubleshooting'
        
        return 'informational'

    def _calculate_query_difficulty(self, success_rate: float, response_time: float, 
                                  results_count: float) -> float:
        """Calculate query difficulty score (0-1, higher = more difficult)."""
        difficulty = 0.0
        
        # Low success rate indicates difficulty
        difficulty += (1.0 - success_rate) * 0.4
        
        # High response time might indicate complex processing
        if response_time > 1000:  # > 1 second
            difficulty += 0.2
        
        # Very few or too many results indicate difficulty
        if results_count < 3:
            difficulty += 0.2
        elif results_count > 50:
            difficulty += 0.1
        
        return min(difficulty, 1.0)

class UserBehaviorAnalyzer:
    """Analyzes user behavior patterns."""
    
    def __init__(self, event_collector: EventCollector):
        self.event_collector = event_collector

    async def analyze_user_behavior(self, user_id: str) -> Optional[UserBehaviorProfile]:
        """Analyze behavior for a specific user."""
        try:
            # Get user events
            user_events = [e for e in await self.event_collector.get_events(limit=10000) 
                          if e.user_id == user_id]
            
            if not user_events:
                return None
            
            # Get user sessions
            user_sessions = [s for s in self.event_collector.sessions.values() 
                           if s.user_id == user_id]
            
            if not user_sessions:
                return None
            
            # Calculate metrics
            total_sessions = len(user_sessions)
            
            # Average session duration
            durations = [s.session_duration_seconds for s in user_sessions 
                        if s.session_duration_seconds]
            avg_session_duration = np.mean(durations) if durations else 0
            
            # Favorite content types (based on clicked documents)
            content_types = self._analyze_content_preferences(user_events)
            
            # Search patterns
            search_patterns = self._identify_search_patterns(user_events)
            
            # Expertise level
            expertise_level = self._assess_expertise_level(user_events, user_sessions)
            
            # Preferred filters
            preferred_filters = self._analyze_filter_preferences(user_events)
            
            # Peak usage hours
            peak_hours = self._analyze_usage_timing(user_events)
            
            return UserBehaviorProfile(
                user_id=user_id,
                total_sessions=total_sessions,
                avg_session_duration=avg_session_duration,
                favorite_content_types=content_types,
                search_patterns=search_patterns,
                expertise_level=expertise_level,
                preferred_filters=preferred_filters,
                peak_usage_hours=peak_hours
            )
            
        except Exception as e:
            logger.error(f"User behavior analysis error: {e}")
            return None

    def _analyze_content_preferences(self, events: List[UserEvent]) -> List[str]:
        """Analyze user's content type preferences."""
        content_types = []
        
        # This would analyze clicked documents' types
        # For now, return placeholder data
        return ['technical', 'documentation']

    def _identify_search_patterns(self, events: List[UserEvent]) -> List[str]:
        """Identify user's search patterns."""
        patterns = []
        
        # Analyze query complexity
        query_events = [e for e in events if e.event_type == EventType.SEARCH_QUERY and e.query]
        if query_events:
            avg_query_length = np.mean([len(e.query.split()) for e in query_events])
            if avg_query_length > 5:
                patterns.append('detailed_queries')
            else:
                patterns.append('simple_queries')
        
        # Analyze refinement behavior
        refinement_events = [e for e in events if e.event_type == EventType.SEARCH_REFINEMENT]
        if len(refinement_events) > len(query_events) * 0.3:
            patterns.append('frequent_refiner')
        
        # Analyze filter usage
        filter_events = [e for e in events if e.event_type == EventType.FILTER_APPLIED]
        if len(filter_events) > len(query_events) * 0.5:
            patterns.append('filter_heavy_user')
        
        return patterns

    def _assess_expertise_level(self, events: List[UserEvent], sessions: List[SearchSession]) -> str:
        """Assess user's expertise level."""
        if not sessions:
            return 'novice'
        
        # Calculate metrics
        avg_queries_per_session = np.mean([s.total_queries for s in sessions])
        success_rate = np.mean([s.total_clicks / max(s.total_queries, 1) for s in sessions])
        avg_session_duration = np.mean([s.session_duration_seconds or 0 for s in sessions])
        
        # Expertise heuristics
        if (avg_queries_per_session <= 3 and success_rate > 0.7 and 
            avg_session_duration < 300):  # Less than 5 minutes
            return 'expert'
        elif (avg_queries_per_session <= 5 and success_rate > 0.5):
            return 'intermediate'
        else:
            return 'novice'

    def _analyze_filter_preferences(self, events: List[UserEvent]) -> List[str]:
        """Analyze user's filter preferences."""
        filter_events = [e for e in events if e.event_type == EventType.FILTER_APPLIED]
        all_filters = []
        
        for event in filter_events:
            all_filters.extend(event.filters_applied)
        
        # Return most used filters
        filter_counts = Counter(all_filters)
        return [f for f, count in filter_counts.most_common(5)]

    def _analyze_usage_timing(self, events: List[UserEvent]) -> List[int]:
        """Analyze user's peak usage hours."""
        hours = [e.timestamp.hour for e in events]
        hour_counts = Counter(hours)
        
        # Return top 3 hours
        return [h for h, count in hour_counts.most_common(3)]

class SearchAnalyticsEngine:
    """Main search analytics engine."""
    
    def __init__(self):
        self.event_collector = EventCollector()
        self.query_analyzer = QueryAnalyzer(self.event_collector)
        self.behavior_analyzer = UserBehaviorAnalyzer(self.event_collector)
        self.cache = get_rag_query_cache()

    async def track_search_query(self, query: str, session_id: str, user_id: Optional[str] = None,
                               response_time_ms: Optional[float] = None,
                               results_count: Optional[int] = None) -> str:
        """Track a search query event."""
        return await self.event_collector.track_event(
            EventType.SEARCH_QUERY,
            session_id=session_id,
            user_id=user_id,
            query=query,
            response_time_ms=response_time_ms,
            search_results_count=results_count
        )

    async def track_result_click(self, session_id: str, document_id: str, position: int,
                               user_id: Optional[str] = None) -> str:
        """Track a search result click event."""
        return await self.event_collector.track_event(
            EventType.SEARCH_RESULT_CLICK,
            session_id=session_id,
            user_id=user_id,
            document_id=document_id,
            position_clicked=position
        )

    async def track_filter_applied(self, session_id: str, filters: List[str],
                                 user_id: Optional[str] = None) -> str:
        """Track filter application event."""
        return await self.event_collector.track_event(
            EventType.FILTER_APPLIED,
            session_id=session_id,
            user_id=user_id,
            filters_applied=filters
        )

    async def get_search_analytics_dashboard(self, time_period: timedelta = timedelta(days=7)) -> Dict[str, Any]:
        """Get comprehensive search analytics dashboard data."""
        try:
            end_time = datetime.now()
            start_time = end_time - time_period
            
            # Get events for the time period
            all_events = await self.event_collector.get_events(
                time_range=(start_time, end_time),
                limit=10000
            )
            
            # Basic metrics
            total_searches = len([e for e in all_events if e.event_type == EventType.SEARCH_QUERY])
            total_clicks = len([e for e in all_events if e.event_type == EventType.SEARCH_RESULT_CLICK])
            unique_sessions = len(set(e.session_id for e in all_events))
            
            # Calculate CTR (Click-Through Rate)
            ctr = (total_clicks / total_searches * 100) if total_searches > 0 else 0
            
            # Query analysis
            top_queries = await self.query_analyzer.analyze_query_performance(time_period)
            
            # Search trends
            search_trends = await self._calculate_search_trends(all_events, time_period)
            
            # Performance metrics
            performance_metrics = self._calculate_performance_metrics(all_events)
            
            # User behavior insights
            behavior_insights = await self._get_behavior_insights(all_events)
            
            return {
                'overview': {
                    'total_searches': total_searches,
                    'total_clicks': total_clicks,
                    'unique_sessions': unique_sessions,
                    'click_through_rate': round(ctr, 2),
                    'avg_session_duration': behavior_insights.get('avg_session_duration', 0),
                    'time_period': f"{time_period.days} days"
                },
                'top_queries': [
                    {
                        'query': q.query,
                        'frequency': q.frequency,
                        'success_rate': round(q.success_rate * 100, 1),
                        'avg_response_time': round(q.avg_response_time_ms, 0),
                        'user_intent': q.user_intent,
                        'difficulty': round(q.difficulty_score * 100, 1)
                    }
                    for q in top_queries[:10]
                ],
                'search_trends': search_trends,
                'performance_metrics': performance_metrics,
                'behavior_insights': behavior_insights
            }
            
        except Exception as e:
            logger.error(f"Analytics dashboard error: {e}")
            return {}

    async def _calculate_search_trends(self, events: List[UserEvent], 
                                     time_period: timedelta) -> List[Dict[str, Any]]:
        """Calculate search trends over time."""
        try:
            # Group events by day
            daily_searches = defaultdict(int)
            daily_clicks = defaultdict(int)
            
            for event in events:
                day_key = event.timestamp.date().isoformat()
                
                if event.event_type == EventType.SEARCH_QUERY:
                    daily_searches[day_key] += 1
                elif event.event_type == EventType.SEARCH_RESULT_CLICK:
                    daily_clicks[day_key] += 1
            
            # Create trend data
            trends = []
            
            # Search volume trend
            search_data = [(datetime.fromisoformat(day), count) 
                          for day, count in sorted(daily_searches.items())]
            if len(search_data) > 1:
                trends.append({
                    'metric': 'search_volume',
                    'data_points': search_data,
                    'trend_direction': self._calculate_trend_direction(search_data)
                })
            
            # Click volume trend
            click_data = [(datetime.fromisoformat(day), count)
                         for day, count in sorted(daily_clicks.items())]
            if len(click_data) > 1:
                trends.append({
                    'metric': 'click_volume',
                    'data_points': click_data,
                    'trend_direction': self._calculate_trend_direction(click_data)
                })
            
            return trends
            
        except Exception as e:
            logger.warning(f"Trend calculation error: {e}")
            return []

    def _calculate_trend_direction(self, data_points: List[Tuple[datetime, float]]) -> str:
        """Calculate trend direction from data points."""
        if len(data_points) < 2:
            return 'stable'
        
        values = [point[1] for point in data_points]
        
        # Simple linear trend
        first_half_avg = np.mean(values[:len(values)//2])
        second_half_avg = np.mean(values[len(values)//2:])
        
        change_rate = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0
        
        if change_rate > 0.1:
            return 'increasing'
        elif change_rate < -0.1:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_performance_metrics(self, events: List[UserEvent]) -> Dict[str, Any]:
        """Calculate search performance metrics."""
        query_events = [e for e in events if e.event_type == EventType.SEARCH_QUERY]
        
        if not query_events:
            return {}
        
        # Response times
        response_times = [e.response_time_ms for e in query_events if e.response_time_ms]
        
        # Results counts
        result_counts = [e.search_results_count for e in query_events if e.search_results_count]
        
        return {
            'avg_response_time_ms': round(np.mean(response_times), 2) if response_times else 0,
            'median_response_time_ms': round(np.median(response_times), 2) if response_times else 0,
            'p95_response_time_ms': round(np.percentile(response_times, 95), 2) if response_times else 0,
            'avg_results_count': round(np.mean(result_counts), 1) if result_counts else 0,
            'zero_results_rate': round(
                sum(1 for count in result_counts if count == 0) / len(result_counts) * 100, 1
            ) if result_counts else 0
        }

    async def _get_behavior_insights(self, events: List[UserEvent]) -> Dict[str, Any]:
        """Get user behavior insights."""
        sessions = list(self.event_collector.sessions.values())
        
        if not sessions:
            return {}
        
        # Session metrics
        session_durations = [s.session_duration_seconds for s in sessions 
                           if s.session_duration_seconds]
        
        # Query patterns
        query_events = [e for e in events if e.event_type == EventType.SEARCH_QUERY and e.query]
        query_lengths = [len(e.query.split()) for e in query_events]
        
        return {
            'total_sessions': len(sessions),
            'avg_session_duration': round(np.mean(session_durations), 1) if session_durations else 0,
            'avg_queries_per_session': round(np.mean([s.total_queries for s in sessions]), 1),
            'session_success_rate': round(
                sum(1 for s in sessions if s.goal_achieved) / len(sessions) * 100, 1
            ),
            'avg_query_length': round(np.mean(query_lengths), 1) if query_lengths else 0,
            'refinement_rate': round(
                sum(s.query_refinements for s in sessions) / sum(s.total_queries for s in sessions) * 100, 1
            ) if sessions else 0
        }

    async def get_query_suggestions_for_improvement(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get queries that need improvement based on analytics."""
        try:
            query_analyses = await self.query_analyzer.analyze_query_performance()
            
            # Sort by difficulty score and low success rate
            problem_queries = [
                q for q in query_analyses 
                if q.success_rate < 0.3 or q.difficulty_score > 0.7
            ]
            
            problem_queries.sort(
                key=lambda x: (x.difficulty_score * 2 + (1 - x.success_rate)) * x.frequency,
                reverse=True
            )
            
            return [
                {
                    'query': q.query,
                    'frequency': q.frequency,
                    'success_rate': round(q.success_rate * 100, 1),
                    'difficulty_score': round(q.difficulty_score * 100, 1),
                    'avg_response_time_ms': round(q.avg_response_time_ms, 0),
                    'improvement_priority': 'high' if q.difficulty_score > 0.8 else 'medium'
                }
                for q in problem_queries[:limit]
            ]
            
        except Exception as e:
            logger.error(f"Query improvement suggestions error: {e}")
            return []

# Global instance
_search_analytics_engine_instance = None

def get_search_analytics_engine() -> SearchAnalyticsEngine:
    """Get global search analytics engine instance."""
    global _search_analytics_engine_instance
    if _search_analytics_engine_instance is None:
        _search_analytics_engine_instance = SearchAnalyticsEngine()
    return _search_analytics_engine_instance