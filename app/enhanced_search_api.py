"""
Authored by: AI/ML Engineer (jackson)
Date: 2025-08-05

Enhanced Search API Endpoints

FastAPI endpoints for advanced search, analytics, tagging, and faceted search capabilities.
Integrates all intelligent search components into a cohesive API.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException, Query, Body, Depends
from fastapi.responses import JSONResponse

from .search_engine import get_search_engine, SearchResult, QueryIntent
from .document_analytics import get_analytics_engine, DocumentInsight, CollectionInsights
from .intelligent_tagging import get_tagging_system, DocumentTags, Tag, TagSuggestion
from .faceted_search import get_faceted_search_engine, FilterCriteria, FilterType, FacetedSearchResult
from .search_analytics import (
    get_search_analytics_engine, 
    EventType, 
    UserEvent, 
    SearchSession,
    QueryAnalysis,
    UserBehaviorProfile
)
from .error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses

class EnhancedSearchRequest(BaseModel):
    """Enhanced search request with advanced options."""
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    filters: Optional[List[str]] = Field(default=None, description="List of filter strings")
    include_facets: bool = Field(default=True, description="Include facets in response")
    include_analytics: bool = Field(default=False, description="Include search analytics")
    session_id: Optional[str] = Field(default=None, description="User session ID")
    user_id: Optional[str] = Field(default=None, description="User ID for tracking")

class FilterRequest(BaseModel):
    """Filter application request."""
    facet_name: str
    filter_type: str  # categorical, range, date_range, tags
    values: List[str] = Field(default_factory=list)
    operator: str = Field(default="OR", description="Filter operator: OR, AND, NOT")
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class SearchAnalyticsRequest(BaseModel):
    """Search analytics request."""
    event_type: str
    session_id: str
    user_id: Optional[str] = None
    query: Optional[str] = None
    document_id: Optional[str] = None
    position_clicked: Optional[int] = None
    filters_applied: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentAnalysisRequest(BaseModel):
    """Document analysis request."""
    doc_id: str
    force_refresh: bool = Field(default=False)
    include_tags: bool = Field(default=True)
    include_insights: bool = Field(default=True)

class TaggingRequest(BaseModel):
    """Document tagging request."""
    doc_id: str
    force_refresh: bool = Field(default=False)
    min_confidence: float = Field(default=0.3, ge=0.0, le=1.0)
    max_tags: int = Field(default=15, ge=1, le=50)

# Response models

class EnhancedSearchResponse(BaseModel):
    """Enhanced search response."""
    query: str
    results: List[Dict[str, Any]]
    facets: List[Dict[str, Any]]
    total_count: int
    filtered_count: int
    search_time_ms: float
    suggestions: List[str]
    analytics: Optional[Dict[str, Any]] = None

class DocumentAnalysisResponse(BaseModel):
    """Document analysis response."""
    doc_id: str
    insights: Optional[Dict[str, Any]]
    tags: Optional[Dict[str, Any]]
    analysis_time_ms: float
    cached: bool

class SearchAnalyticsDashboardResponse(BaseModel):
    """Search analytics dashboard response."""
    overview: Dict[str, Any]
    top_queries: List[Dict[str, Any]]
    search_trends: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    behavior_insights: Dict[str, Any]
    generated_at: datetime

# Initialize engines
search_engine = get_search_engine()
analytics_engine = get_analytics_engine()
tagging_system = get_tagging_system()
faceted_search_engine = get_faceted_search_engine()
search_analytics_engine = get_search_analytics_engine()

def create_enhanced_search_router():
    """Create FastAPI router with enhanced search endpoints."""
    from fastapi import APIRouter
    router = APIRouter(prefix="/api/v1/search", tags=["Enhanced Search"])

    @router.post("/enhanced", response_model=EnhancedSearchResponse)
    async def enhanced_search(request: EnhancedSearchRequest):
        """
        Perform enhanced semantic search with faceted filtering.
        
        Features:
        - Semantic search with query understanding
        - Dynamic faceted filtering
        - Search analytics tracking
        - Intelligent result ranking
        """
        try:
            start_time = datetime.now()
            
            # Track search query
            if request.session_id:
                await search_analytics_engine.track_search_query(
                    query=request.query,
                    session_id=request.session_id,
                    user_id=request.user_id
                )
            
            # Parse filters
            filters = []
            if request.filters:
                for filter_str in request.filters:
                    parsed_filter = faceted_search_engine.parse_filter_from_string(filter_str)
                    if parsed_filter:
                        filters.append(parsed_filter)
            
            # Perform faceted search
            search_result = await faceted_search_engine.search(
                query=request.query,
                filters=filters,
                max_results=request.max_results,
                include_facets=request.include_facets
            )
            
            # Convert results to dict format
            results_dict = []
            for i, result in enumerate(search_result.results):
                result_dict = {
                    'doc_id': result.doc_id,
                    'title': result.title,
                    'snippet': result.snippet,
                    'relevance_score': result.relevance_score,
                    'semantic_score': result.semantic_score,
                    'keyword_score': result.keyword_score,
                    'source': result.source,
                    'highlights': result.highlights,
                    'metadata': result.metadata,
                    'rank_position': i + 1
                }
                results_dict.append(result_dict)
            
            # Convert facets to dict format
            facets_dict = []
            for facet in search_result.facets:
                facet_dict = {
                    'name': facet.name,
                    'display_name': facet.display_name,
                    'type': facet.filter_type.value,
                    'allow_multiple': facet.allow_multiple,
                    'collapsed': facet.collapsed,
                    'options': [
                        {
                            'value': opt.value,
                            'label': opt.label,
                            'count': opt.count,
                            'percentage': opt.percentage,
                            'selected': opt.selected
                        }
                        for opt in facet.options
                    ]
                }
                facets_dict.append(facet_dict)
            
            # Include analytics if requested
            analytics_data = None
            if request.include_analytics:
                analytics_data = {
                    'query_intent': 'informational',  # Would be classified by query processor
                    'search_complexity': len(request.query.split()) / 10.0,
                    'filter_count': len(filters)
                }
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return EnhancedSearchResponse(
                query=request.query,
                results=results_dict,
                facets=facets_dict,
                total_count=search_result.total_count,
                filtered_count=search_result.filtered_count,
                search_time_ms=response_time,
                suggestions=search_result.suggestions,
                analytics=analytics_data
            )
            
        except Exception as e:
            logger.error(f"Enhanced search error: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    @router.post("/track-analytics")
    async def track_search_analytics(request: SearchAnalyticsRequest):
        """Track search analytics events."""
        try:
            event_type_map = {
                'search_query': EventType.SEARCH_QUERY,
                'result_click': EventType.SEARCH_RESULT_CLICK,
                'filter_applied': EventType.FILTER_APPLIED,
                'filter_removed': EventType.FILTER_REMOVED,
                'search_refinement': EventType.SEARCH_REFINEMENT
            }
            
            event_type = event_type_map.get(request.event_type)
            if not event_type:
                raise HTTPException(status_code=400, detail="Invalid event type")
            
            event_id = await search_analytics_engine.event_collector.track_event(
                event_type=event_type,
                session_id=request.session_id,
                user_id=request.user_id,
                query=request.query,
                document_id=request.document_id,
                position_clicked=request.position_clicked,
                filters_applied=request.filters_applied,
                metadata=request.metadata
            )
            
            return {"event_id": event_id, "status": "tracked"}
            
        except Exception as e:
            logger.error(f"Analytics tracking error: {e}")
            raise HTTPException(status_code=500, detail=f"Tracking failed: {str(e)}")

    @router.get("/analytics/dashboard", response_model=SearchAnalyticsDashboardResponse)
    async def get_search_analytics_dashboard(
        days: int = Query(default=7, ge=1, le=365, description="Number of days to analyze")
    ):
        """Get comprehensive search analytics dashboard."""
        try:
            time_period = timedelta(days=days)
            dashboard_data = await search_analytics_engine.get_search_analytics_dashboard(time_period)
            
            return SearchAnalyticsDashboardResponse(
                overview=dashboard_data.get('overview', {}),
                top_queries=dashboard_data.get('top_queries', []),
                search_trends=dashboard_data.get('search_trends', []),
                performance_metrics=dashboard_data.get('performance_metrics', {}),
                behavior_insights=dashboard_data.get('behavior_insights', {}),
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Analytics dashboard error: {e}")
            raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

    @router.get("/suggestions")
    async def get_search_suggestions(
        query: str = Query(..., description="Partial query for suggestions"),
        limit: int = Query(default=5, ge=1, le=20, description="Maximum suggestions")
    ):
        """Get search suggestions for partial query."""
        try:
            suggestions = await search_engine.get_search_suggestions(query, limit)
            return {"query": query, "suggestions": suggestions}
            
        except Exception as e:
            logger.error(f"Search suggestions error: {e}")
            raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")

    @router.get("/facets/statistics")
    async def get_facet_statistics():
        """Get facet usage statistics."""
        try:
            stats = await faceted_search_engine.get_facet_statistics()
            return stats
            
        except Exception as e:
            logger.error(f"Facet statistics error: {e}")
            raise HTTPException(status_code=500, detail=f"Statistics failed: {str(e)}")

    return router

def create_document_analytics_router():
    """Create FastAPI router with document analytics endpoints."""
    from fastapi import APIRouter
    router = APIRouter(prefix="/api/v1/analytics", tags=["Document Analytics"])

    @router.post("/document", response_model=DocumentAnalysisResponse)
    async def analyze_document(request: DocumentAnalysisRequest):
        """
        Perform comprehensive document analysis.
        
        Features:
        - Content analytics and insights
        - Automatic categorization
        - Quality metrics
        - Related document detection
        """
        try:
            start_time = datetime.now()
            cached = False
            
            # Get document insights
            insights = None
            if request.include_insights:
                insights = await analytics_engine.analyze_document(
                    request.doc_id, 
                    force_refresh=request.force_refresh
                )
                cached = not request.force_refresh and insights is not None
            
            # Get document tags
            tags = None
            if request.include_tags:
                doc_tags = await tagging_system.tag_document(
                    request.doc_id,
                    force_refresh=request.force_refresh
                )
                if doc_tags:
                    tags = {
                        'tags': [
                            {
                                'name': tag.name,
                                'category': tag.category,
                                'confidence': tag.confidence,
                                'source': tag.source,
                                'context': tag.context
                            }
                            for tag in doc_tags.tags
                        ],
                        'suggested_tags': [
                            {
                                'tag': suggestion.tag,
                                'confidence': suggestion.confidence,
                                'reasoning': suggestion.reasoning,
                                'auto_apply': suggestion.auto_apply
                            }
                            for suggestion in doc_tags.suggested_tags
                        ],
                        'hierarchy': doc_tags.hierarchy,
                        'semantic_clusters': doc_tags.semantic_clusters
                    }
            
            analysis_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Convert insights to dict
            insights_dict = None
            if insights:
                insights_dict = {
                    'content_summary': insights.content_summary,
                    'key_topics': insights.key_topics,
                    'sentiment_score': insights.sentiment_score,
                    'complexity_score': insights.complexity_score,
                    'readability_score': insights.readability_score,
                    'word_count': insights.word_count,
                    'unique_concepts': insights.unique_concepts,
                    'related_documents': insights.related_documents,
                    'quality_metrics': insights.quality_metrics
                }
            
            return DocumentAnalysisResponse(
                doc_id=request.doc_id,
                insights=insights_dict,
                tags=tags,
                analysis_time_ms=analysis_time,
                cached=cached
            )
            
        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    @router.get("/collection")
    async def get_collection_analytics(
        force_refresh: bool = Query(default=False, description="Force refresh of analytics")
    ):
        """Get collection-wide analytics and insights."""
        try:
            collection_insights = await analytics_engine.analyze_collection(force_refresh)
            
            if not collection_insights:
                return {"message": "No analytics available", "total_documents": 0}
            
            return {
                'total_documents': collection_insights.total_documents,
                'total_words': collection_insights.total_words,
                'avg_document_length': collection_insights.avg_document_length,
                'topic_distribution': collection_insights.topic_distribution,
                'content_types': collection_insights.content_types,
                'upload_trends': collection_insights.upload_trends,
                'quality_distribution': collection_insights.quality_distribution,
                'top_keywords': [{'keyword': kw, 'count': count} 
                               for kw, count in collection_insights.top_keywords],
                'document_clusters': collection_insights.document_clusters,
                'sentiment_analysis': collection_insights.sentiment_analysis,
                'generated_at': collection_insights.generated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Collection analytics error: {e}")
            raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")

    @router.get("/trending-topics")
    async def get_trending_topics(
        time_period: str = Query(default="week", description="Time period: day, week, month")
    ):
        """Get trending topics over a time period."""
        try:
            trending_topics = await analytics_engine.get_trending_topics(time_period)
            return {"time_period": time_period, "trending_topics": trending_topics}
            
        except Exception as e:
            logger.error(f"Trending topics error: {e}")
            raise HTTPException(status_code=500, detail=f"Trending topics failed: {str(e)}")

    return router

def create_tagging_router():
    """Create FastAPI router with intelligent tagging endpoints."""
    from fastapi import APIRouter
    router = APIRouter(prefix="/api/v1/tags", tags=["Intelligent Tagging"])

    @router.post("/document")
    async def tag_document(request: TaggingRequest):
        """
        Apply intelligent tagging to a document.
        
        Features:
        - ML-based semantic tagging
        - Rule-based pattern matching
        - Hierarchical tag organization
        - Confidence scoring
        """
        try:
            doc_tags = await tagging_system.tag_document(
                request.doc_id,
                force_refresh=request.force_refresh
            )
            
            if not doc_tags:
                raise HTTPException(status_code=404, detail="Document not found or could not be tagged")
            
            return {
                'doc_id': doc_tags.doc_id,
                'tags': [
                    {
                        'name': tag.name,
                        'category': tag.category,
                        'confidence': tag.confidence,
                        'source': tag.source,
                        'context': tag.context,
                        'related_terms': tag.related_terms
                    }
                    for tag in doc_tags.tags
                    if tag.confidence >= request.min_confidence
                ][:request.max_tags],
                'suggested_tags': [
                    {
                        'tag': suggestion.tag,
                        'confidence': suggestion.confidence,
                        'reasoning': suggestion.reasoning,
                        'similar_tags': suggestion.similar_tags,
                        'auto_apply': suggestion.auto_apply
                    }
                    for suggestion in doc_tags.suggested_tags
                    if suggestion.confidence >= request.min_confidence
                ][:request.max_tags],
                'hierarchy': doc_tags.hierarchy,
                'semantic_clusters': doc_tags.semantic_clusters,
                'model_version': doc_tags.model_version,
                'generated_at': doc_tags.generated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Document tagging error: {e}")
            raise HTTPException(status_code=500, detail=f"Tagging failed: {str(e)}")

    @router.get("/popular")
    async def get_popular_tags(
        limit: int = Query(default=20, ge=1, le=100, description="Maximum tags to return")
    ):
        """Get most popular tags across the collection."""
        try:
            popular_tags = await tagging_system.get_popular_tags(limit)
            return {"popular_tags": popular_tags}
            
        except Exception as e:
            logger.error(f"Popular tags error: {e}")
            raise HTTPException(status_code=500, detail=f"Popular tags failed: {str(e)}")

    @router.get("/suggestions")
    async def get_tag_suggestions(
        query: str = Query(..., description="Query to get tag suggestions for"),
        limit: int = Query(default=10, ge=1, le=50, description="Maximum suggestions")
    ):
        """Get tag suggestions for a query."""
        try:
            suggestions = await tagging_system.get_tag_suggestions_for_query(query)
            return {"query": query, "tag_suggestions": suggestions[:limit]}
            
        except Exception as e:
            logger.error(f"Tag suggestions error: {e}")
            raise HTTPException(status_code=500, detail=f"Tag suggestions failed: {str(e)}")

    @router.get("/trends")
    async def get_tag_trends(
        time_period: str = Query(default="month", description="Time period for trends")
    ):
        """Get trending tags over a time period."""
        try:
            trends = await tagging_system.get_tag_trends(time_period)
            return {"time_period": time_period, "tag_trends": trends}
            
        except Exception as e:
            logger.error(f"Tag trends error: {e}")
            raise HTTPException(status_code=500, detail=f"Tag trends failed: {str(e)}")

    return router

def create_user_behavior_router():
    """Create FastAPI router with user behavior analytics endpoints."""
    from fastapi import APIRouter
    router = APIRouter(prefix="/api/v1/behavior", tags=["User Behavior Analytics"])

    @router.get("/user/{user_id}")
    async def get_user_behavior_profile(user_id: str):
        """Get behavior profile for a specific user."""
        try:
            profile = await search_analytics_engine.behavior_analyzer.analyze_user_behavior(user_id)
            
            if not profile:
                raise HTTPException(status_code=404, detail="User behavior data not found")
            
            return {
                'user_id': profile.user_id,
                'total_sessions': profile.total_sessions,
                'avg_session_duration': profile.avg_session_duration,
                'favorite_content_types': profile.favorite_content_types,
                'search_patterns': profile.search_patterns,
                'expertise_level': profile.expertise_level,
                'preferred_filters': profile.preferred_filters,
                'peak_usage_hours': profile.peak_usage_hours
            }
            
        except Exception as e:
            logger.error(f"User behavior analysis error: {e}")
            raise HTTPException(status_code=500, detail=f"Behavior analysis failed: {str(e)}")

    @router.get("/sessions/active")
    async def get_active_sessions():
        """Get currently active user sessions."""
        try:
            active_sessions = await search_analytics_engine.event_collector.get_active_sessions()
            
            return {
                'active_sessions': [
                    {
                        'session_id': session.session_id,
                        'user_id': session.user_id,
                        'start_time': session.start_time.isoformat(),
                        'total_queries': session.total_queries,
                        'total_clicks': session.total_clicks,
                        'documents_viewed': len(session.documents_viewed),
                        'goal_achieved': session.goal_achieved
                    }
                    for session in active_sessions
                ]
            }
            
        except Exception as e:
            logger.error(f"Active sessions error: {e}")
            raise HTTPException(status_code=500, detail=f"Active sessions failed: {str(e)}")

    @router.get("/queries/improvement")
    async def get_query_improvement_suggestions(
        limit: int = Query(default=10, ge=1, le=50, description="Maximum suggestions")
    ):
        """Get queries that need improvement based on analytics."""
        try:
            suggestions = await search_analytics_engine.get_query_suggestions_for_improvement(limit)
            return {"improvement_suggestions": suggestions}
            
        except Exception as e:
            logger.error(f"Query improvement suggestions error: {e}")
            raise HTTPException(status_code=500, detail=f"Improvement suggestions failed: {str(e)}")

    return router

# Utility functions for integration

def add_enhanced_search_routes(app: FastAPI):
    """Add all enhanced search routes to FastAPI app."""
    try:
        # Add routers
        app.include_router(create_enhanced_search_router())
        app.include_router(create_document_analytics_router())
        app.include_router(create_tagging_router())
        app.include_router(create_user_behavior_router())
        
        logger.info("Enhanced search routes added successfully")
        
    except Exception as e:
        logger.error(f"Error adding enhanced search routes: {e}")
        raise

def get_enhanced_search_status():
    """Get status of enhanced search components."""
    try:
        return {
            'search_engine': 'operational',
            'analytics_engine': 'operational',
            'tagging_system': 'operational',
            'faceted_search': 'operational',
            'search_analytics': 'operational',
            'components_loaded': True,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }