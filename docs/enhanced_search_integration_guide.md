# Enhanced Search & Analytics Integration Guide

This guide covers the integration of the new intelligent search and analytics system into the existing RAG application.

## System Overview

The enhanced search system consists of 6 key components:

1. **Semantic Search Engine** (`search_engine.py`) - Advanced semantic search with query understanding
2. **Document Analytics** (`document_analytics.py`) - Content analysis and insights generation  
3. **Intelligent Tagging** (`intelligent_tagging.py`) - ML-based document categorization
4. **Faceted Search** (`faceted_search.py`) - Dynamic filtering and multi-dimensional search
5. **Search Analytics** (`search_analytics.py`) - User behavior tracking and search optimization
6. **Relevance Ranking** (`relevance_ranking.py`) - ML-powered result ranking with user feedback

## Quick Start Integration

### 1. Install Dependencies

```bash
# Install enhanced search dependencies
pip install -r app/enhanced_search_requirements.txt

# For full NLP support (optional)
python -m spacy download en_core_web_sm
```

### 2. Update Main Application

Add the enhanced search routes to your main FastAPI application:

```python
# In app/main.py
from enhanced_search_api import add_enhanced_search_routes

# Add this after creating your FastAPI app
add_enhanced_search_routes(app)
```

### 3. Basic Usage Examples

#### Enhanced Search with Facets
```python
from search_engine import get_search_engine
from faceted_search import get_faceted_search_engine

# Basic semantic search
search_engine = get_search_engine()
results = await search_engine.search("machine learning algorithms", max_results=10)

# Faceted search with filters
faceted_engine = get_faceted_search_engine()
search_result = await faceted_engine.search(
    query="python tutorial",
    filters=[],
    include_facets=True,
    max_results=20
)
```

#### Document Analytics
```python
from document_analytics import get_analytics_engine

analytics = get_analytics_engine()

# Analyze single document
doc_insight = await analytics.analyze_document("doc_id_123")

# Get collection-wide analytics
collection_insights = await analytics.analyze_collection()

# Get trending topics
trending = await analytics.get_trending_topics("week")
```

#### Intelligent Tagging
```python
from intelligent_tagging import get_tagging_system

tagging = get_tagging_system()

# Tag a document
doc_tags = await tagging.tag_document("doc_id_123")

# Get popular tags
popular_tags = await tagging.get_popular_tags(limit=20)

# Get tag suggestions for search
suggestions = await tagging.get_tag_suggestions_for_query("machine learning")
```

## API Endpoints

The enhanced search system adds the following REST API endpoints:

### Enhanced Search
- `POST /api/v1/search/enhanced` - Advanced semantic search with facets
- `GET /api/v1/search/suggestions` - Search query suggestions
- `GET /api/v1/search/facets/statistics` - Facet usage statistics

### Document Analytics
- `POST /api/v1/analytics/document` - Analyze specific document
- `GET /api/v1/analytics/collection` - Collection-wide analytics
- `GET /api/v1/analytics/trending-topics` - Get trending topics

### Intelligent Tagging
- `POST /api/v1/tags/document` - Tag a document
- `GET /api/v1/tags/popular` - Get popular tags
- `GET /api/v1/tags/suggestions` - Get tag suggestions
- `GET /api/v1/tags/trends` - Get tag trends

### Search Analytics & User Behavior
- `POST /api/v1/search/track-analytics` - Track user interactions
- `GET /api/v1/search/analytics/dashboard` - Analytics dashboard
- `GET /api/v1/behavior/user/{user_id}` - User behavior profile
- `GET /api/v1/behavior/queries/improvement` - Query improvement suggestions

## Frontend Integration

### Enhanced Search UI Component

```javascript
// Example React component for enhanced search
import React, { useState, useEffect } from 'react';

const EnhancedSearch = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [facets, setFacets] = useState([]);
    const [selectedFilters, setSelectedFilters] = useState([]);

    const handleSearch = async () => {
        try {
            const response = await fetch('/api/v1/search/enhanced', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    filters: selectedFilters,
                    include_facets: true,
                    max_results: 20,
                    session_id: 'user_session_123'
                })
            });
            
            const data = await response.json();
            setResults(data.results);
            setFacets(data.facets);
            
            // Track search analytics
            await fetch('/api/v1/search/track-analytics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    event_type: 'search_query',
                    session_id: 'user_session_123',
                    query,
                    metadata: { results_count: data.results.length }
                })
            });
            
        } catch (error) {
            console.error('Search error:', error);
        }
    };

    const handleResultClick = async (result, position) => {
        // Track click analytics
        await fetch('/api/v1/search/track-analytics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                event_type: 'result_click',
                session_id: 'user_session_123',
                document_id: result.doc_id,
                position_clicked: position
            })
        });
        
        // Handle result click (e.g., navigate to document)
        window.open(`/documents/${result.doc_id}`, '_blank');
    };

    return (
        <div className="enhanced-search">
            <div className="search-input">
                <input 
                    type="text" 
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search documents..."
                />
                <button onClick={handleSearch}>Search</button>
            </div>
            
            <div className="search-content">
                <div className="facets">
                    {facets.map(facet => (
                        <FacetComponent 
                            key={facet.name} 
                            facet={facet}
                            onFilterChange={setSelectedFilters}
                        />
                    ))}
                </div>
                
                <div className="results">
                    {results.map((result, index) => (
                        <ResultComponent 
                            key={result.doc_id}
                            result={result}
                            position={index + 1}
                            onClick={() => handleResultClick(result, index + 1)}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
};
```

### Analytics Dashboard Component

```javascript
const AnalyticsDashboard = () => {
    const [analytics, setAnalytics] = useState(null);

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const response = await fetch('/api/v1/search/analytics/dashboard?days=7');
                const data = await response.json();
                setAnalytics(data);
            } catch (error) {
                console.error('Analytics error:', error);
            }
        };

        fetchAnalytics();
    }, []);

    if (!analytics) return <div>Loading analytics...</div>;

    return (
        <div className="analytics-dashboard">
            <div className="overview">
                <h2>Search Analytics Overview</h2>
                <div className="metrics">
                    <div className="metric">
                        <span className="label">Total Searches</span>
                        <span className="value">{analytics.overview.total_searches}</span>
                    </div>
                    <div className="metric">
                        <span className="label">Click-through Rate</span>
                        <span className="value">{analytics.overview.click_through_rate}%</span>
                    </div>
                    <div className="metric">
                        <span className="label">Unique Sessions</span>
                        <span className="value">{analytics.overview.unique_sessions}</span>
                    </div>
                </div>
            </div>
            
            <div className="top-queries">
                <h3>Top Queries</h3>
                <ul>
                    {analytics.top_queries.map(query => (
                        <li key={query.query}>
                            <span className="query">{query.query}</span>
                            <span className="frequency">({query.frequency} searches)</span>
                            <span className="success-rate">{query.success_rate}% success</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};
```

## Configuration Options

### Environment Variables

```bash
# Enhanced search configuration
ENHANCED_SEARCH_ENABLED=true
SEARCH_ANALYTICS_ENABLED=true
ML_RANKING_ENABLED=true
FACETED_SEARCH_ENABLED=true

# ML Model settings
RANKING_MODEL_PATH=/app/models/ranking_model.pkl
TAGGING_CONFIDENCE_THRESHOLD=0.3
ANALYTICS_RETENTION_DAYS=90

# Performance settings
SEARCH_CACHE_TTL=300
ANALYTICS_BATCH_SIZE=100
FACET_MAX_OPTIONS=20
```

### Component Configuration

```python
# Configuration for enhanced search components
ENHANCED_SEARCH_CONFIG = {
    'search_engine': {
        'max_results_default': 10,
        'similarity_threshold': 0.7,
        'query_expansion_enabled': True,
        'semantic_cache_ttl': 300
    },
    'document_analytics': {
        'batch_analysis_enabled': True,
        'insight_cache_ttl': 3600,
        'topic_extraction_enabled': True,
        'sentiment_analysis_enabled': True
    },
    'intelligent_tagging': {
        'auto_tagging_enabled': True,
        'min_confidence_threshold': 0.3,
        'max_tags_per_document': 15,
        'hierarchical_tagging': True
    },
    'faceted_search': {
        'dynamic_facets_enabled': True,
        'max_facet_options': 20,
        'facet_cache_ttl': 1800,
        'advanced_filtering': True
    },
    'search_analytics': {
        'user_tracking_enabled': True,
        'session_timeout_minutes': 30,
        'behavior_analysis_enabled': True,
        'retention_days': 90
    },
    'relevance_ranking': {
        'ml_ranking_enabled': True,
        'personalization_enabled': True,
        'feedback_learning_enabled': True,
        'model_retrain_threshold': 100
    }
}
```

## Performance Considerations

### Caching Strategy
- **Search Results**: 5-minute TTL for search result caching
- **Document Analytics**: 1-hour TTL for document insights
- **Facet Data**: 30-minute TTL for facet calculations
- **User Profiles**: 24-hour TTL for user behavior profiles

### Async Processing
- Document analytics run asynchronously where possible
- Bulk tagging operations use background processing
- Analytics data aggregation happens in background tasks
- ML model training runs as scheduled batch jobs

### Resource Management
- Connection pooling for database access
- Memory limits for large document processing
- Rate limiting for API endpoints
- Circuit breakers for external service calls

## Monitoring & Observability

### Key Metrics to Monitor
- Search response times (<200ms target)
- Search success rates (>80% target)
- Analytics processing latency
- ML model accuracy scores
- Cache hit rates
- API endpoint error rates

### Health Check Endpoints
```python
@app.get("/health/search")
async def search_health_check():
    return {
        'search_engine': 'healthy',
        'analytics_engine': 'healthy',
        'tagging_system': 'healthy',
        'faceted_search': 'healthy',
        'ml_ranking': 'healthy',
        'timestamp': datetime.now().isoformat()
    }
```

## Troubleshooting

### Common Issues

1. **Slow Search Performance**
   - Check if embeddings are cached
   - Verify database connection pooling
   - Review facet calculation efficiency

2. **ML Model Not Loading**
   - Verify model file permissions
   - Check if scikit-learn version matches
   - Ensure sufficient memory for model loading

3. **Analytics Data Missing**
   - Verify event tracking is enabled
   - Check session ID consistency
   - Review cache configuration

4. **Tagging Accuracy Issues**
   - Adjust confidence thresholds
   - Review taxonomy definitions
   - Check for content preprocessing issues

### Debug Mode
Enable debug logging for detailed troubleshooting:

```python
import logging
logging.getLogger('search_engine').setLevel(logging.DEBUG)
logging.getLogger('document_analytics').setLevel(logging.DEBUG)
logging.getLogger('intelligent_tagging').setLevel(logging.DEBUG)
```

## Production Deployment

### Recommended Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Load Balancer  │◄──►│   FastAPI App    │◄──►│   PostgreSQL    │
│  (nginx)        │    │  Enhanced Search │    │   (Analytics)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │                        ▼                        │
         │              ┌─────────────────┐                │
         │              │   Redis Cache   │                │
         │              │   (Search)      │                │
         │              └─────────────────┘                │
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                        ┌─────────────────┐
                        │   ChromaDB      │
                        │   (Vectors)     │
                        └─────────────────┘
```

### Scaling Considerations
- Horizontal scaling of FastAPI instances
- Read replicas for analytics queries
- Dedicated cache cluster for search results
- Async processing queues for heavy operations
- CDN for static assets and cached responses

## Next Steps

1. **Deploy Basic Integration**: Start with semantic search and basic analytics
2. **Add User Tracking**: Implement session tracking and basic analytics
3. **Enable ML Features**: Activate tagging and relevance ranking
4. **Build Dashboard UI**: Create analytics and insights interfaces
5. **Optimize Performance**: Tune caching and async processing
6. **Scale & Monitor**: Set up production monitoring and scaling

For detailed API documentation, see the interactive docs at `/docs` when running the application with enhanced search enabled.