"""
Authored by: AI/ML Engineer (jackson)
Date: 2025-08-05

Faceted Search System

Advanced search filtering with dynamic facets, multi-dimensional filtering,
and intelligent filter suggestions for enhanced document discovery.
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

import numpy as np
from sklearn.preprocessing import StandardScaler

from .rag_backend import get_rag_system
from .document_manager import DocumentManager
from .search_engine import get_search_engine, SearchResult
from .document_analytics import get_analytics_engine
from .intelligent_tagging import get_tagging_system
from .performance_cache import get_rag_query_cache
from .error_handlers import handle_error, ApplicationError, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

class FilterType(Enum):
    """Types of search filters."""
    CATEGORICAL = "categorical"
    RANGE = "range"
    DATE_RANGE = "date_range"
    TEXT = "text"
    TAGS = "tags"
    BOOLEAN = "boolean"

@dataclass
class FilterOption:
    """Individual filter option with metadata."""
    value: str
    label: str
    count: int
    percentage: float
    selected: bool = False

@dataclass
class SearchFacet:
    """Search facet definition."""
    name: str
    display_name: str
    filter_type: FilterType
    options: List[FilterOption]
    allow_multiple: bool = True
    collapsed: bool = False
    sort_by: str = "count"  # count, alpha, relevance

@dataclass
class FilterCriteria:
    """Search filter criteria."""
    facet_name: str
    filter_type: FilterType
    values: List[str]
    operator: str = "OR"  # OR, AND, NOT
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

@dataclass
class FacetedSearchResult:
    """Complete faceted search result."""
    results: List[SearchResult]
    facets: List[SearchFacet]
    applied_filters: List[FilterCriteria]
    total_count: int
    filtered_count: int
    search_time_ms: float
    suggestions: List[str]

class FacetBuilder:
    """Builds dynamic facets from document collection."""
    
    def __init__(self):
        self.rag_system = get_rag_system()
        self.doc_manager = DocumentManager()
        self.analytics_engine = get_analytics_engine()
        self.tagging_system = get_tagging_system()
        
        # Facet configurations
        self.facet_configs = self._build_facet_configs()

    def _build_facet_configs(self) -> Dict[str, Dict[str, Any]]:
        """Build facet configuration definitions."""
        return {
            'file_type': {
                'display_name': 'File Type',
                'filter_type': FilterType.CATEGORICAL,
                'allow_multiple': True,
                'sort_by': 'count'
            },
            'document_type': {
                'display_name': 'Document Type',
                'filter_type': FilterType.CATEGORICAL,
                'allow_multiple': True,
                'sort_by': 'count'
            },
            'content_structure': {
                'display_name': 'Content Structure',
                'filter_type': FilterType.CATEGORICAL,
                'allow_multiple': True,
                'sort_by': 'count'
            },
            'tags': {
                'display_name': 'Tags',
                'filter_type': FilterType.TAGS,
                'allow_multiple': True,
                'sort_by': 'count'
            },
            'upload_date': {
                'display_name': 'Upload Date',
                'filter_type': FilterType.DATE_RANGE,
                'allow_multiple': False,
                'sort_by': 'alpha'
            },
            'file_size': {
                'display_name': 'File Size',
                'filter_type': FilterType.RANGE,
                'allow_multiple': False,
                'sort_by': 'alpha'
            },
            'word_count': {
                'display_name': 'Word Count',
                'filter_type': FilterType.RANGE,
                'allow_multiple': False,
                'sort_by': 'alpha'
            },
            'complexity': {
                'display_name': 'Complexity Level',
                'filter_type': FilterType.CATEGORICAL,
                'allow_multiple': True,
                'sort_by': 'alpha'
            },
            'quality': {
                'display_name': 'Quality Score',
                'filter_type': FilterType.RANGE,
                'allow_multiple': False,
                'sort_by': 'alpha'
            },
            'sentiment': {
                'display_name': 'Content Sentiment',
                'filter_type': FilterType.CATEGORICAL,
                'allow_multiple': True,
                'sort_by': 'alpha'
            },
            'language': {
                'display_name': 'Language',
                'filter_type': FilterType.CATEGORICAL,
                'allow_multiple': True,
                'sort_by': 'count'
            },
            'source': {
                'display_name': 'Source',
                'filter_type': FilterType.CATEGORICAL,
                'allow_multiple': True,
                'sort_by': 'count'
            }
        }

    async def build_facets(self, documents: Optional[List[Dict]] = None, 
                          search_query: Optional[str] = None) -> List[SearchFacet]:
        """Build dynamic facets from document collection."""
        try:
            # Get documents if not provided
            if documents is None:
                documents = self.doc_manager.list_documents()
            
            if not documents:
                return []
            
            facets = []
            
            # Get document analytics for advanced facets
            doc_insights = await self._get_document_insights(documents)
            
            # Build each facet
            for facet_name, config in self.facet_configs.items():
                facet = await self._build_single_facet(
                    facet_name, config, documents, doc_insights, search_query
                )
                if facet and facet.options:  # Only include facets with options
                    facets.append(facet)
            
            return facets
            
        except Exception as e:
            logger.error(f"Facet building error: {e}")
            return []

    async def _get_document_insights(self, documents: List[Dict]) -> Dict[str, Any]:
        """Get document insights for facet building."""
        insights = {}
        
        for doc in documents[:50]:  # Limit for performance
            doc_id = doc.get('doc_id')
            if doc_id:
                try:
                    insight = await self.analytics_engine.analyze_document(doc_id)
                    if insight:
                        insights[doc_id] = insight
                except Exception as e:
                    logger.debug(f"Could not get insight for {doc_id}: {e}")
        
        return insights

    async def _build_single_facet(self, facet_name: str, config: Dict[str, Any],
                                documents: List[Dict], doc_insights: Dict[str, Any],
                                search_query: Optional[str]) -> Optional[SearchFacet]:
        """Build a single facet from documents."""
        try:
            filter_type = config['filter_type']
            
            if filter_type == FilterType.CATEGORICAL:
                options = await self._build_categorical_facet(
                    facet_name, documents, doc_insights
                )
            elif filter_type == FilterType.RANGE:
                options = await self._build_range_facet(
                    facet_name, documents, doc_insights
                )
            elif filter_type == FilterType.DATE_RANGE:
                options = await self._build_date_range_facet(
                    facet_name, documents, doc_insights
                )
            elif filter_type == FilterType.TAGS:
                options = await self._build_tags_facet(
                    facet_name, documents, doc_insights
                )
            else:
                options = []
            
            if not options:
                return None
            
            # Sort options
            sort_by = config.get('sort_by', 'count')
            if sort_by == 'count':
                options.sort(key=lambda x: x.count, reverse=True)
            elif sort_by == 'alpha':
                options.sort(key=lambda x: x.label.lower())
            
            # Limit options for performance
            max_options = 20 if filter_type != FilterType.TAGS else 15
            options = options[:max_options]
            
            return SearchFacet(
                name=facet_name,
                display_name=config['display_name'],
                filter_type=filter_type,
                options=options,
                allow_multiple=config.get('allow_multiple', True),
                collapsed=len(options) > 10,  # Collapse large facets
                sort_by=sort_by
            )
        
        except Exception as e:
            logger.warning(f"Error building facet {facet_name}: {e}")
            return None

    async def _build_categorical_facet(self, facet_name: str, documents: List[Dict],
                                     doc_insights: Dict[str, Any]) -> List[FilterOption]:
        """Build categorical facet options."""
        value_counts = Counter()
        total_docs = len(documents)
        
        for doc in documents:
            value = None
            
            if facet_name == 'file_type':
                value = doc.get('file_type', 'unknown')
            elif facet_name == 'document_type':
                value = doc.get('document_type', 'plain_text')
            elif facet_name == 'content_structure':
                value = doc.get('content_structure', 'unstructured')
            elif facet_name == 'source':
                value = doc.get('source', 'unknown')
            elif facet_name == 'complexity':
                # Use insights to determine complexity level
                doc_id = doc.get('doc_id')
                if doc_id in doc_insights:
                    complexity_score = doc_insights[doc_id].complexity_score
                    if complexity_score > 0.7:
                        value = 'high'
                    elif complexity_score > 0.4:
                        value = 'medium'
                    else:
                        value = 'low'
            elif facet_name == 'sentiment':
                # Use insights to determine sentiment
                doc_id = doc.get('doc_id')
                if doc_id in doc_insights:
                    sentiment_score = doc_insights[doc_id].sentiment_score
                    if sentiment_score > 0.1:
                        value = 'positive'
                    elif sentiment_score < -0.1:
                        value = 'negative'
                    else:
                        value = 'neutral'
            elif facet_name == 'language':
                # Simple language detection (could be enhanced)
                value = 'english'  # Default for now
            
            if value:
                value_counts[value] += 1
        
        # Create filter options
        options = []
        for value, count in value_counts.items():
            percentage = (count / total_docs) * 100 if total_docs > 0 else 0
            
            options.append(FilterOption(
                value=value,
                label=value.replace('_', ' ').title(),
                count=count,
                percentage=percentage
            ))
        
        return options

    async def _build_range_facet(self, facet_name: str, documents: List[Dict],
                               doc_insights: Dict[str, Any]) -> List[FilterOption]:
        """Build range facet options."""
        values = []
        
        for doc in documents:
            value = None
            
            if facet_name == 'file_size':
                value = doc.get('file_size', 0)
            elif facet_name == 'word_count':
                doc_id = doc.get('doc_id')
                if doc_id in doc_insights:
                    value = doc_insights[doc_id].word_count
            elif facet_name == 'quality':
                doc_id = doc.get('doc_id')
                if doc_id in doc_insights:
                    quality_scores = list(doc_insights[doc_id].quality_metrics.values())
                    value = np.mean(quality_scores) if quality_scores else 0.5
            
            if value is not None:
                values.append(value)
        
        if not values:
            return []
        
        # Create range buckets
        min_val = min(values)
        max_val = max(values)
        
        if min_val == max_val:
            return []
        
        # Define range buckets based on facet type
        if facet_name == 'file_size':
            ranges = [
                (0, 1024, 'Small (< 1KB)'),
                (1024, 1024*1024, 'Medium (1KB - 1MB)'),
                (1024*1024, 1024*1024*10, 'Large (1MB - 10MB)'),
                (1024*1024*10, float('inf'), 'Very Large (> 10MB)')
            ]
        elif facet_name == 'word_count':
            ranges = [
                (0, 100, 'Very Short (< 100 words)'),
                (100, 500, 'Short (100-500 words)'),
                (500, 2000, 'Medium (500-2K words)'),
                (2000, 10000, 'Long (2K-10K words)'),
                (10000, float('inf'), 'Very Long (> 10K words)')
            ]
        elif facet_name == 'quality':
            ranges = [
                (0, 0.3, 'Low Quality'),
                (0.3, 0.6, 'Medium Quality'),
                (0.6, 0.8, 'High Quality'),
                (0.8, 1.0, 'Excellent Quality')
            ]
        else:
            # Generic ranges
            num_buckets = 5
            step = (max_val - min_val) / num_buckets
            ranges = []
            for i in range(num_buckets):
                range_min = min_val + i * step
                range_max = min_val + (i + 1) * step if i < num_buckets - 1 else max_val
                label = f"{range_min:.1f} - {range_max:.1f}"
                ranges.append((range_min, range_max, label))
        
        # Count values in each range
        options = []
        total_docs = len(values)
        
        for range_min, range_max, label in ranges:
            count = sum(1 for v in values if range_min <= v < range_max)
            if count > 0:
                percentage = (count / total_docs) * 100
                
                options.append(FilterOption(
                    value=f"{range_min}-{range_max}",
                    label=label,
                    count=count,
                    percentage=percentage
                ))
        
        return options

    async def _build_date_range_facet(self, facet_name: str, documents: List[Dict],
                                    doc_insights: Dict[str, Any]) -> List[FilterOption]:
        """Build date range facet options."""
        dates = []
        
        for doc in documents:
            if facet_name == 'upload_date':
                upload_time = doc.get('upload_timestamp')
                if upload_time:
                    try:
                        date = datetime.fromisoformat(upload_time)
                        dates.append(date)
                    except:
                        pass
        
        if not dates:
            return []
        
        # Define date ranges
        now = datetime.now()
        ranges = [
            (now - timedelta(days=1), now, 'Today'),
            (now - timedelta(days=7), now - timedelta(days=1), 'This Week'),
            (now - timedelta(days=30), now - timedelta(days=7), 'This Month'),
            (now - timedelta(days=90), now - timedelta(days=30), 'Last 3 Months'),
            (now - timedelta(days=365), now - timedelta(days=90), 'This Year'),
            (datetime.min, now - timedelta(days=365), 'Older')
        ]
        
        # Count dates in each range
        options = []
        total_docs = len(dates)
        
        for range_start, range_end, label in ranges:
            count = sum(1 for d in dates if range_start <= d < range_end)
            if count > 0:
                percentage = (count / total_docs) * 100
                
                options.append(FilterOption(
                    value=f"{range_start.isoformat()}-{range_end.isoformat()}",
                    label=label,
                    count=count,
                    percentage=percentage
                ))
        
        return options

    async def _build_tags_facet(self, facet_name: str, documents: List[Dict],
                              doc_insights: Dict[str, Any]) -> List[FilterOption]:
        """Build tags facet options."""
        try:
            # Get popular tags from tagging system
            popular_tags = await self.tagging_system.get_popular_tags(limit=30)
            
            if not popular_tags:
                return []
            
            options = []
            total_docs = len(documents)
            
            for tag_info in popular_tags:
                tag = tag_info['tag']
                count = tag_info['count']
                percentage = (count / total_docs) * 100 if total_docs > 0 else 0
                
                options.append(FilterOption(
                    value=tag,
                    label=tag.replace('_', ' ').title(),
                    count=count,
                    percentage=percentage
                ))
            
            return options
            
        except Exception as e:
            logger.warning(f"Error building tags facet: {e}")
            return []

class FilterEngine:
    """Applies filters to search results."""
    
    def __init__(self):
        self.rag_system = get_rag_system()
        self.doc_manager = DocumentManager()
        self.analytics_engine = get_analytics_engine()

    def apply_filters(self, documents: List[Dict], filters: List[FilterCriteria]) -> List[Dict]:
        """Apply filters to document list."""
        if not filters:
            return documents
        
        filtered_docs = documents.copy()
        
        for filter_criteria in filters:
            filtered_docs = self._apply_single_filter(filtered_docs, filter_criteria)
        
        return filtered_docs

    def _apply_single_filter(self, documents: List[Dict], 
                           filter_criteria: FilterCriteria) -> List[Dict]:
        """Apply a single filter to document list."""
        try:
            facet_name = filter_criteria.facet_name
            filter_type = filter_criteria.filter_type
            values = filter_criteria.values
            operator = filter_criteria.operator
            
            if not values:
                return documents
            
            filtered_docs = []
            
            for doc in documents:
                if self._document_matches_filter(doc, filter_criteria):
                    filtered_docs.append(doc)
            
            return filtered_docs
            
        except Exception as e:
            logger.error(f"Filter application error: {e}")
            return documents

    def _document_matches_filter(self, doc: Dict, filter_criteria: FilterCriteria) -> bool:
        """Check if a document matches the filter criteria."""
        try:
            facet_name = filter_criteria.facet_name
            filter_type = filter_criteria.filter_type
            values = filter_criteria.values
            operator = filter_criteria.operator
            
            # Get document value for the facet
            doc_value = self._get_document_facet_value(doc, facet_name, filter_type)
            
            if doc_value is None:
                return False
            
            # Check match based on filter type
            if filter_type == FilterType.CATEGORICAL or filter_type == FilterType.TAGS:
                matches = self._check_categorical_match(doc_value, values, operator)
            elif filter_type == FilterType.RANGE:
                matches = self._check_range_match(doc_value, filter_criteria)
            elif filter_type == FilterType.DATE_RANGE:
                matches = self._check_date_range_match(doc_value, filter_criteria)
            else:
                matches = False
            
            return matches
            
        except Exception as e:
            logger.debug(f"Document filter matching error: {e}")
            return False

    def _get_document_facet_value(self, doc: Dict, facet_name: str, 
                                filter_type: FilterType) -> Any:
        """Get the facet value for a document."""
        try:
            if facet_name == 'file_type':
                return doc.get('file_type')
            elif facet_name == 'document_type':
                return doc.get('document_type')
            elif facet_name == 'content_structure':
                return doc.get('content_structure')
            elif facet_name == 'source':
                return doc.get('source')
            elif facet_name == 'upload_date':
                upload_time = doc.get('upload_timestamp')
                if upload_time:
                    return datetime.fromisoformat(upload_time)
            elif facet_name == 'file_size':
                return doc.get('file_size')
            elif facet_name in ['word_count', 'complexity', 'quality', 'sentiment']:
                # These require document insights
                return self._get_insight_value(doc.get('doc_id'), facet_name)
            elif facet_name == 'tags':
                # Get document tags
                return self._get_document_tags(doc.get('doc_id'))
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting facet value for {facet_name}: {e}")
            return None

    def _get_insight_value(self, doc_id: str, facet_name: str) -> Any:
        """Get insight-based value for a document (with caching)."""
        # This would normally be cached or pre-computed
        # For now, return None to avoid performance issues
        return None

    def _get_document_tags(self, doc_id: str) -> List[str]:
        """Get tags for a document (with caching)."""
        # This would normally be cached or pre-computed
        # For now, return empty list to avoid performance issues
        return []

    def _check_categorical_match(self, doc_value: Any, filter_values: List[str], 
                               operator: str) -> bool:
        """Check categorical/tags match."""
        if isinstance(doc_value, list):
            # For tags or multi-value fields
            if operator == "OR":
                return any(tag in filter_values for tag in doc_value)
            elif operator == "AND":
                return all(tag in doc_value for tag in filter_values)
            elif operator == "NOT":
                return not any(tag in filter_values for tag in doc_value)
        else:
            # Single value
            if operator == "OR":
                return doc_value in filter_values
            elif operator == "NOT":
                return doc_value not in filter_values
        
        return False

    def _check_range_match(self, doc_value: float, filter_criteria: FilterCriteria) -> bool:
        """Check range match."""
        range_min = filter_criteria.range_min
        range_max = filter_criteria.range_max
        
        if range_min is not None and doc_value < range_min:
            return False
        if range_max is not None and doc_value > range_max:
            return False
        
        return True

    def _check_date_range_match(self, doc_value: datetime, 
                              filter_criteria: FilterCriteria) -> bool:
        """Check date range match."""
        date_from = filter_criteria.date_from
        date_to = filter_criteria.date_to
        
        if date_from is not None and doc_value < date_from:
            return False
        if date_to is not None and doc_value > date_to:
            return False
        
        return True

class FacetedSearchEngine:
    """Main faceted search engine combining search and filtering."""
    
    def __init__(self):
        self.search_engine = get_search_engine()
        self.facet_builder = FacetBuilder()
        self.filter_engine = FilterEngine()
        self.cache = get_rag_query_cache()

    async def search(self, query: str = "", filters: Optional[List[FilterCriteria]] = None,
                    max_results: int = 20, include_facets: bool = True) -> FacetedSearchResult:
        """Perform faceted search with filters."""
        start_time = time.time()
        
        try:
            # Get all documents first
            all_documents = self.facet_builder.doc_manager.list_documents()
            total_count = len(all_documents)
            
            # Apply filters to document list
            if filters:
                filtered_documents = self.filter_engine.apply_filters(all_documents, filters)
            else:
                filtered_documents = all_documents.copy()
                filters = []
            
            filtered_count = len(filtered_documents)
            
            # Perform search on filtered documents if query provided
            if query and query.strip():
                # Get document IDs for filtered documents
                filtered_doc_ids = {doc.get('doc_id') for doc in filtered_documents}
                
                # Perform search
                search_results = await self.search_engine.search(
                    query, max_results=max_results * 2  # Get more to account for filtering
                )
                
                # Filter search results to only include filtered documents
                final_results = []
                for result in search_results:
                    if result.doc_id in filtered_doc_ids:
                        final_results.append(result)
                        if len(final_results) >= max_results:
                            break
            else:
                # No query - convert filtered documents to search results
                final_results = await self._convert_documents_to_results(
                    filtered_documents[:max_results]
                )
            
            # Build facets based on all documents (not just results)
            facets = []
            if include_facets:
                facets = await self.facet_builder.build_facets(
                    documents=all_documents, search_query=query
                )
                # Update facet selection state based on applied filters
                facets = self._update_facet_selections(facets, filters)
            
            # Generate search suggestions
            suggestions = await self._generate_search_suggestions(query, filters)
            
            search_time = (time.time() - start_time) * 1000
            
            return FacetedSearchResult(
                results=final_results,
                facets=facets,
                applied_filters=filters,
                total_count=total_count,
                filtered_count=filtered_count,
                search_time_ms=search_time,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Faceted search error: {e}")
            return FacetedSearchResult(
                results=[],
                facets=[],
                applied_filters=filters or [],
                total_count=0,
                filtered_count=0,
                search_time_ms=0,
                suggestions=[]
            )

    async def _convert_documents_to_results(self, documents: List[Dict]) -> List[SearchResult]:
        """Convert document metadata to search results."""
        results = []
        
        for doc in documents:
            try:
                # Get document content for snippet
                doc_id = doc.get('doc_id')
                content = ""
                if doc_id:
                    db_results = self.facet_builder.rag_system.collection.get(
                        where={"doc_id": doc_id},
                        include=["documents"]
                    )
                    if db_results and db_results['documents']:
                        content = ' '.join(db_results['documents'][:2])  # First 2 chunks
                
                # Create search result
                result = SearchResult(
                    doc_id=doc_id or '',
                    content=content,
                    title=doc.get('title', ''),
                    source=doc.get('source', ''),
                    relevance_score=0.5,  # Neutral relevance for non-query results
                    semantic_score=0.0,
                    keyword_score=0.0,
                    freshness_score=0.5,
                    quality_score=0.5,
                    snippet=content[:200] + "..." if len(content) > 200 else content,
                    highlights=[],
                    metadata=doc,
                    rank_position=len(results) + 1
                )
                results.append(result)
                
            except Exception as e:
                logger.debug(f"Error converting document to result: {e}")
                continue
        
        return results

    def _update_facet_selections(self, facets: List[SearchFacet], 
                               filters: List[FilterCriteria]) -> List[SearchFacet]:
        """Update facet option selections based on applied filters."""
        filter_map = {f.facet_name: f.values for f in filters}
        
        for facet in facets:
            if facet.name in filter_map:
                filter_values = filter_map[facet.name]
                for option in facet.options:
                    option.selected = option.value in filter_values
        
        return facets

    async def _generate_search_suggestions(self, query: str, 
                                         filters: List[FilterCriteria]) -> List[str]:
        """Generate search suggestions based on query and filters."""
        try:
            suggestions = []
            
            # Query-based suggestions
            if query:
                query_suggestions = await self.search_engine.get_search_suggestions(query)
                suggestions.extend(query_suggestions)
            
            # Filter-based suggestions
            for filter_criteria in filters:
                if filter_criteria.filter_type == FilterType.TAGS:
                    # Suggest related tags
                    tag_suggestions = await self.facet_builder.tagging_system.get_tag_suggestions_for_query(
                        ' '.join(filter_criteria.values)
                    )
                    suggestions.extend(tag_suggestions[:3])
            
            # Remove duplicates and limit
            unique_suggestions = list(dict.fromkeys(suggestions))
            return unique_suggestions[:10]
            
        except Exception as e:
            logger.debug(f"Suggestion generation error: {e}")
            return []

    def parse_filter_from_string(self, filter_string: str) -> Optional[FilterCriteria]:
        """Parse filter criteria from string format."""
        try:
            # Expected format: "facet:type:values" or "facet:type:min-max" 
            parts = filter_string.split(':', 2)
            if len(parts) < 3:
                return None
            
            facet_name, type_str, value_str = parts
            
            # Map string to FilterType
            type_map = {
                'cat': FilterType.CATEGORICAL,
                'categorical': FilterType.CATEGORICAL,
                'range': FilterType.RANGE,
                'date': FilterType.DATE_RANGE,
                'tags': FilterType.TAGS,
                'bool': FilterType.BOOLEAN
            }
            
            filter_type = type_map.get(type_str.lower())
            if not filter_type:
                return None
            
            # Parse values based on type
            if filter_type in [FilterType.CATEGORICAL, FilterType.TAGS]:
                values = [v.strip() for v in value_str.split(',')]
                return FilterCriteria(
                    facet_name=facet_name,
                    filter_type=filter_type,
                    values=values
                )
            elif filter_type == FilterType.RANGE:
                if '-' in value_str:
                    min_str, max_str = value_str.split('-', 1)
                    return FilterCriteria(
                        facet_name=facet_name,
                        filter_type=filter_type,
                        values=[],
                        range_min=float(min_str) if min_str else None,
                        range_max=float(max_str) if max_str else None
                    )
            elif filter_type == FilterType.DATE_RANGE:
                if '-' in value_str:
                    from_str, to_str = value_str.split('-', 1)
                    return FilterCriteria(
                        facet_name=facet_name,
                        filter_type=filter_type,
                        values=[],
                        date_from=datetime.fromisoformat(from_str) if from_str else None,
                        date_to=datetime.fromisoformat(to_str) if to_str else None
                    )
            
            return None
            
        except Exception as e:
            logger.debug(f"Filter parsing error: {e}")
            return None

    async def get_facet_statistics(self) -> Dict[str, Any]:
        """Get statistics about facet usage and effectiveness."""
        try:
            # Get all documents
            documents = self.facet_builder.doc_manager.list_documents()
            
            # Build facets
            facets = await self.facet_builder.build_facets(documents)
            
            # Calculate statistics
            stats = {
                'total_documents': len(documents),
                'total_facets': len(facets),
                'facet_details': []
            }
            
            for facet in facets:
                facet_stats = {
                    'name': facet.name,
                    'display_name': facet.display_name,
                    'type': facet.filter_type.value,
                    'option_count': len(facet.options),
                    'top_options': [
                        {'value': opt.value, 'label': opt.label, 'count': opt.count}
                        for opt in facet.options[:5]
                    ]
                }
                stats['facet_details'].append(facet_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Facet statistics error: {e}")
            return {}

# Global instance
_faceted_search_engine_instance = None

def get_faceted_search_engine() -> FacetedSearchEngine:
    """Get global faceted search engine instance."""
    global _faceted_search_engine_instance
    if _faceted_search_engine_instance is None:
        _faceted_search_engine_instance = FacetedSearchEngine()
    return _faceted_search_engine_instance