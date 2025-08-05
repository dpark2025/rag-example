# API Reference Guide

## Overview

The Local RAG System provides a comprehensive REST API with full v1 endpoints for document management, intelligent querying, and system monitoring. All API endpoints are fully documented with interactive examples at http://localhost:8000/docs.

## Base URL

```
http://localhost:8000
```

## Authentication

The system runs locally and requires no authentication for development. For production deployments, configure authentication in your deployment environment.

## API Versioning

- **Current Version**: v1
- **Stable Endpoints**: All v1 endpoints are production-ready
- **Legacy Support**: v0 endpoints (non-versioned) maintained for backward compatibility

## Document Management API

### Upload Documents

#### Single Document Upload
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: [file_upload]
```

**Response:**
```json
{
  "id": "doc_123",
  "filename": "document.pdf",
  "size": 1024000,
  "status": "processing",
  "upload_time": "2024-01-01T10:00:00Z"
}
```

#### Bulk Document Upload
```http
POST /api/v1/documents/bulk-upload
Content-Type: multipart/form-data

files: [multiple_file_uploads]
```

**Response:**
```json
{
  "task_id": "bulk_456",
  "total_files": 5,
  "status": "processing",
  "progress": {
    "completed": 0,
    "failed": 0,
    "remaining": 5
  }
}
```

### Document Management

#### List Documents
```http
GET /api/v1/documents
```

**Query Parameters:**
- `limit` (optional): Maximum number of documents to return (default: 100)
- `offset` (optional): Number of documents to skip (default: 0)
- `status` (optional): Filter by status (`ready`, `processing`, `error`)
- `file_type` (optional): Filter by file type (`pdf`, `txt`, `md`)

**Response:**
```json
{
  "documents": [
    {
      "id": "doc_123",
      "title": "Technical Report",
      "filename": "report.pdf", 
      "file_type": "pdf",
      "size": 1024000,
      "chunk_count": 25,
      "status": "ready",
      "upload_time": "2024-01-01T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

#### Delete Document
```http
DELETE /api/v1/documents/{doc_id}
```

**Response:**
```json
{
  "success": true,
  "document_id": "doc_123",
  "chunks_deleted": 25,
  "message": "Document deleted successfully"
}
```

#### Bulk Delete Documents
```http
DELETE /api/v1/documents/bulk
Content-Type: application/json

{
  "document_ids": ["doc_123", "doc_456", "doc_789"]
}
```

**Response:**
```json
{
  "success": true,
  "deleted_count": 3,
  "failed_count": 0,
  "results": [
    {
      "document_id": "doc_123",
      "status": "deleted",
      "chunks_deleted": 25
    }
  ]
}
```

#### Document Status
```http
GET /api/v1/documents/{doc_id}/status
```

**Response:**
```json
{
  "document_id": "doc_123",
  "status": "ready",
  "processing_progress": 100,
  "error_message": null,
  "chunks_created": 25,
  "last_updated": "2024-01-01T10:05:00Z"
}
```

#### Storage Statistics
```http
GET /api/v1/documents/stats
```

**Response:**
```json
{
  "total_documents": 15,
  "total_chunks": 375,
  "storage_size_bytes": 15360000,
  "status_breakdown": {
    "ready": 12,
    "processing": 2,
    "error": 1
  },
  "file_type_breakdown": {
    "pdf": 8,
    "txt": 5,
    "md": 2
  }
}
```

## Query & Search API

### RAG Query
```http
POST /query
Content-Type: application/json

{
  "question": "What are the key findings in the technical reports?",
  "max_chunks": 5,
  "similarity_threshold": 0.7,
  "include_sources": true
}
```

**Response:**
```json
{
  "answer": "Based on the technical reports, the key findings include...",
  "sources": [
    {
      "document_id": "doc_123",
      "document_title": "Technical Report Q1",
      "chunk_id": "chunk_456",
      "similarity_score": 0.89,
      "content_preview": "The analysis revealed that...",
      "page_number": 5
    }
  ],
  "query_metadata": {
    "chunks_retrieved": 3,
    "processing_time_ms": 1250,
    "model_used": "llama3.2:8b",
    "total_tokens": 2048
  }
}
```

### Configuration Management

#### Get Settings
```http
GET /settings
```

**Response:**
```json
{
  "similarity_threshold": 0.7,
  "max_chunks": 5,
  "model_name": "llama3.2:8b",
  "chunking_strategy": "semantic",
  "chunk_size": 400,
  "chunk_overlap": 50
}
```

#### Update Settings
```http
POST /settings
Content-Type: application/json

{
  "similarity_threshold": 0.8,
  "max_chunks": 3
}
```

**Response:**
```json
{
  "success": true,
  "updated_settings": {
    "similarity_threshold": 0.8,
    "max_chunks": 3
  },
  "message": "Settings updated successfully"
}
```

## Upload Management API

### Upload Tasks

#### List Upload Tasks
```http
GET /api/v1/upload/tasks
```

**Response:**
```json
{
  "tasks": [
    {
      "task_id": "bulk_456",
      "type": "bulk_upload",
      "status": "completed",
      "total_files": 5,
      "completed_files": 5,
      "failed_files": 0,
      "created_at": "2024-01-01T10:00:00Z",
      "completed_at": "2024-01-01T10:02:30Z"
    }
  ]
}
```

#### Get Upload Task Status
```http
GET /api/v1/upload/tasks/{task_id}
```

**Response:**
```json
{
  "task_id": "bulk_456",
  "status": "processing",
  "progress": {
    "total_files": 5,
    "completed": 3,
    "failed": 0,
    "remaining": 2,
    "percentage": 60
  },
  "results": [
    {
      "filename": "doc1.pdf",
      "document_id": "doc_123",
      "status": "completed"
    },
    {
      "filename": "doc2.pdf", 
      "status": "processing"
    }
  ],
  "estimated_completion": "2024-01-01T10:03:00Z"
}
```

#### Clean Up Upload Tasks
```http
POST /api/v1/upload/cleanup
Content-Type: application/json

{
  "older_than_hours": 24,
  "status": "completed"
}
```

**Response:**
```json
{
  "success": true,
  "cleaned_tasks": 15,
  "message": "Cleanup completed successfully"
}
```

#### Upload Statistics
```http
GET /api/v1/upload/stats
```

**Response:**
```json
{
  "total_uploads": 125,
  "successful_uploads": 118,
  "failed_uploads": 7,
  "success_rate": 94.4,
  "average_processing_time_seconds": 45,
  "upload_trends": {
    "last_24h": 12,
    "last_7d": 89,
    "last_30d": 125
  }
}
```

## Health & Monitoring API

### System Health
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "services": {
    "rag_backend": {
      "status": "healthy",
      "response_time_ms": 25
    },
    "chromadb": {
      "status": "healthy", 
      "response_time_ms": 12,
      "collection_count": 1
    },
    "ollama": {
      "status": "healthy",
      "response_time_ms": 150,
      "model": "llama3.2:8b"
    }
  },
  "system_metrics": {
    "memory_usage_mb": 2048,
    "cpu_usage_percent": 25.5,
    "disk_usage_gb": 15.2
  }
}
```

### Error Statistics
```http
GET /health/errors
```

**Response:**
```json
{
  "error_summary": {
    "total_errors_24h": 3,
    "critical_errors": 0,
    "warning_errors": 2,
    "info_errors": 1
  },
  "recent_errors": [
    {
      "timestamp": "2024-01-01T09:30:00Z",
      "level": "warning",
      "category": "document_processing",
      "message": "PDF extraction timeout for large file",
      "document_id": "doc_789"
    }
  ],
  "error_trends": {
    "error_rate_percent": 0.2,
    "mttr_minutes": 5.5,
    "most_common_category": "upload_validation"
  }
}
```

### Performance Metrics
```http
GET /health/metrics
```

**Response:**
```json
{
  "performance_metrics": {
    "avg_response_time_ms": 125,
    "requests_per_minute": 45,
    "cache_hit_rate": 85.5,
    "query_success_rate": 98.2
  },
  "resource_usage": {
    "memory_usage_mb": 2048,
    "cpu_usage_percent": 25.5,
    "disk_io_rate_mbps": 5.2,
    "network_io_rate_mbps": 1.8
  },
  "database_metrics": {
    "total_documents": 125,
    "total_chunks": 3125, 
    "avg_chunks_per_document": 25,
    "index_size_mb": 512
  }
}
```

### Processing Status
```http
GET /processing/status
```

**Response:**
```json
{
  "queue_status": {
    "pending_documents": 2,
    "processing_documents": 1,
    "completed_today": 25,
    "failed_today": 1
  },
  "processing_metrics": {
    "avg_processing_time_seconds": 45,
    "current_queue_wait_time_seconds": 30,
    "throughput_docs_per_hour": 80
  },
  "worker_status": {
    "active_workers": 3,
    "idle_workers": 1,
    "total_capacity": 4
  }
}
```

## Error Handling

### Standard Error Format

All API endpoints return errors in a consistent format:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Document with ID 'doc_123' was not found",
    "details": {
      "document_id": "doc_123",
      "timestamp": "2024-01-01T10:00:00Z"
    },
    "suggestion": "Verify the document ID and try again"
  }
}
```

### HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate upload)
- `422 Unprocessable Entity` - Invalid file format or content
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

### Common Error Codes

- `INVALID_FILE_FORMAT` - Unsupported file type
- `FILE_TOO_LARGE` - File exceeds size limit
- `DOCUMENT_NOT_FOUND` - Document ID not found
- `PROCESSING_FAILED` - Document processing failed
- `OLLAMA_UNAVAILABLE` - LLM service unavailable
- `CHROMADB_ERROR` - Vector database error
- `RATE_LIMIT_EXCEEDED` - Too many requests

## Rate Limiting

- **Upload Endpoints**: 10 requests per minute per IP
- **Query Endpoints**: 60 requests per minute per IP  
- **Management Endpoints**: 100 requests per minute per IP
- **Health Endpoints**: 200 requests per minute per IP

## Usage Examples

### Complete Document Workflow

```bash
# 1. Upload document
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf"

# 2. Check processing status
curl "http://localhost:8000/api/v1/documents/doc_123/status"

# 3. Query the document
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main topic?",
    "max_chunks": 3,
    "include_sources": true
  }'

# 4. List all documents
curl "http://localhost:8000/api/v1/documents"

# 5. Delete document
curl -X DELETE "http://localhost:8000/api/v1/documents/doc_123"
```

### System Monitoring

```bash
# Check system health
curl "http://localhost:8000/health"

# Get performance metrics
curl "http://localhost:8000/health/metrics"

# Check error statistics
curl "http://localhost:8000/health/errors"
```

## Interactive Documentation

For detailed interactive API documentation with request/response examples and the ability to test endpoints directly:

**🔗 Visit: http://localhost:8000/docs**

The interactive documentation includes:
- Complete endpoint specifications
- Request/response schemas
- Authentication requirements
- Rate limiting information
- Real-time API testing interface
- Code generation in multiple languages

## SDK and Integration

### Python Integration

```python
import requests

class RAGClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def upload_document(self, file_path):
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/api/v1/documents/upload",
                files={"file": f}
            )
        return response.json()
    
    def query(self, question, max_chunks=5):
        response = requests.post(
            f"{self.base_url}/query",
            json={
                "question": question,
                "max_chunks": max_chunks,
                "include_sources": True
            }
        )
        return response.json()
    
    def get_health(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage
client = RAGClient()
health = client.get_health()
print(f"System status: {health['status']}")
```

### JavaScript Integration

```javascript
class RAGClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseUrl}/api/v1/documents/upload`, {
            method: 'POST',
            body: formData
        });
        
        return response.json();
    }
    
    async query(question, maxChunks = 5) {
        const response = await fetch(`${this.baseUrl}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                max_chunks: maxChunks,
                include_sources: true
            })
        });
        
        return response.json();
    }
}

// Usage
const client = new RAGClient();
const result = await client.query('What are the main topics?');
console.log(result.answer);
```

## Support

For additional support:
- **Interactive Docs**: http://localhost:8000/docs
- **Health Dashboard**: http://localhost:8000/health
- **System Monitoring**: http://localhost:3001 (Grafana)
- **GitHub Issues**: Create issues for bugs or feature requests
- **Documentation**: See `/docs` directory for technical guides