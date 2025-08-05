# Document Versioning System Guide

## Overview

The Document Versioning System provides comprehensive version control for documents in the RAG system. It offers:

- **Complete Version History**: Track all document changes with detailed metadata
- **Content Comparison**: Advanced diff analysis with similarity scoring
- **Safe Rollback Operations**: Rollback with safety checks and impact analysis
- **Conflict Detection**: Identify and resolve concurrent modification conflicts
- **Audit Trail**: Full audit trail with author tracking and change summaries
- **Data Integrity**: Comprehensive validation and integrity checks

## Architecture

The versioning system consists of several key components:

### Core Components

1. **DocumentVersioning** (`document_versioning.py`)
   - Main versioning service
   - Version creation, retrieval, and management
   - Diff analysis and comparison
   - Rollback operations with safety checks

2. **DocumentVersionValidator** (`versioning_validators.py`)
   - Comprehensive input validation
   - Security constraint checking
   - Data integrity validation
   - Safety checks for operations

3. **API Endpoints** (`main.py`)
   - RESTful API for version operations
   - Request/response models
   - Error handling and validation

### Storage Architecture

```
ChromaDB Collections:
├── documents (main document collection)
│   ├── Document chunks with embeddings
│   └── Current version metadata
└── document_versions (version collection)
    ├── Version content and metadata
    ├── Change tracking information
    └── Audit trail data
```

## API Reference

### Version Management

#### Create Document Version
```http
POST /api/v1/documents/{doc_id}/versions
Content-Type: application/json

{
  "content": "Updated document content...",
  "author": "user@example.com",
  "change_summary": "Added new section on API usage",
  "parent_version_id": "optional-parent-version-id"
}
```

#### Get Version History
```http
GET /api/v1/documents/{doc_id}/versions?limit=20&include_deleted=false
```

#### Get Current Version
```http
GET /api/v1/documents/{doc_id}/versions/current
```

#### Get Specific Version
```http
GET /api/v1/versions/{version_id}
```

#### Get Version Content
```http
GET /api/v1/versions/{version_id}/content
```

### Version Comparison

#### Compare Two Versions
```http
GET /api/v1/versions/{from_version_id}/compare/{to_version_id}
```

Response includes:
- Similarity score (0.0 to 1.0)
- Line changes (added, removed, modified)
- Unified diff format
- Structural change analysis

### Rollback Operations

#### Validate Rollback Safety
```http
GET /api/v1/documents/{doc_id}/rollback/{version_id}/safety-check
```

#### Perform Rollback
```http
POST /api/v1/documents/{doc_id}/rollback
Content-Type: application/json

{
  "target_version_id": "version-to-rollback-to",
  "author": "user@example.com",
  "force": false
}
```

### Conflict Management

#### Detect Conflicts
```http
POST /api/v1/documents/{doc_id}/detect-conflicts?new_content=...&base_version_id=...
```

#### Resolve Conflicts
```http
POST /api/v1/conflicts/{conflict_id}/resolve
Content-Type: application/json

{
  "resolution_strategy": "manual|auto_merge|force_overwrite|abort",
  "author": "user@example.com",
  "merged_content": "resolved content for manual strategy"
}
```

### Maintenance

#### Cleanup Old Versions
```http
POST /api/v1/documents/{doc_id}/versions/cleanup?keep_versions=50
```

#### Global Cleanup
```http
POST /api/v1/versions/cleanup?keep_versions=50
```

## Usage Examples

### Basic Version Creation

```python
import requests

# Create a new version
response = requests.post(
    "http://localhost:8000/api/v1/documents/doc123/versions",
    json={
        "content": "Updated document with new information",
        "author": "john.doe@example.com",
        "change_summary": "Added troubleshooting section"
    }
)

version = response.json()
print(f"Created version {version['version_number']}")
```

### Version Comparison

```python
# Compare two versions
response = requests.get(
    "http://localhost:8000/api/v1/versions/version1/compare/version2"
)

diff = response.json()
print(f"Similarity: {diff['similarity_score']:.2f}")
print(f"Changes: +{diff['lines_added']} -{diff['lines_removed']}")
```

### Safe Rollback

```python
# Check rollback safety first
safety_response = requests.get(
    "http://localhost:8000/api/v1/documents/doc123/rollback/old_version_id/safety-check"
)

safety = safety_response.json()
if safety['is_safe']:
    # Proceed with rollback
    rollback_response = requests.post(
        "http://localhost:8000/api/v1/documents/doc123/rollback",
        json={
            "target_version_id": "old_version_id",
            "author": "admin@example.com",
            "force": False
        }
    )
    
    result = rollback_response.json()
    if result['success']:
        print("Rollback successful!")
    else:
        print("Rollback failed")
else:
    print(f"Rollback not safe: {safety['blocking_issues']}")
```

## Data Models

### DocumentVersion

```python
{
  "version_id": "uuid-string",
  "doc_id": "document-identifier", 
  "version_number": 1,
  "title": "Document Title",
  "author": "user@example.com",
  "timestamp": "2025-08-05T10:30:00Z",
  "operation": "update|create|rollback|merge",
  "change_summary": "Description of changes",
  "status": "active|archived|deleted",
  "is_current": true,
  "lines_added": 10,
  "lines_removed": 5,
  "lines_modified": 3,
  "similarity_score": 0.85,
  "file_size": 1024
}
```

### VersionDiff

```python
{
  "from_version": "version-id-1",
  "to_version": "version-id-2", 
  "similarity_score": 0.85,
  "lines_added": 10,
  "lines_removed": 5,
  "lines_modified": 3,
  "total_changes": 18,
  "unified_diff": "--- Version 1\n+++ Version 2\n@@ -1,3 +1,4 @@...",
  "structural_changes": ["Line count changed from 100 to 110"]
}
```

### RollbackSafetyCheck

```python
{
  "is_safe": true,
  "risk_level": "low|medium|high|critical",
  "warnings": ["Rolling back 5 versions"],
  "blocking_issues": [],
  "affected_systems": ["document_content", "embeddings", "search_index"],
  "rollback_impact": {
    "content_changes": 25,
    "versions_rolled_back": 5,
    "critical_operations": 0
  }
}
```

## Configuration

### Version Limits

```python
# In document_versioning.py
self.max_versions_per_document = 50  # Maximum versions per document
self.auto_cleanup_threshold = 100    # Trigger automatic cleanup
self.max_diff_size = 10000          # Maximum diff size to store
```

### Validation Settings

```python
# In versioning_validators.py
self.max_content_size = 50 * 1024 * 1024  # 50MB maximum content
self.max_change_summary_length = 1000      # 1000 char summary limit
self.max_rollback_distance = 100           # Max versions to rollback
```

## Security Features

### Input Validation
- Content size limits (50MB default)
- SQL injection pattern detection
- Script injection pattern detection
- Author field validation
- Malicious content detection

### Data Integrity
- Content hash verification
- File size consistency checks
- Timestamp validation
- Version number validation
- Status validation

### Access Control
- Author tracking for all operations
- Operation audit trail
- Safety checks for destructive operations
- Validation of rollback operations

## Performance Optimization

### Caching Strategy
- Version metadata caching (5 minutes TTL)
- Document cache integration
- Intelligent cache invalidation

### Batch Operations
- Bulk version cleanup
- Batched database operations
- Parallel processing for large operations

### Storage Efficiency
- Content deduplication via hashing
- Compressed diff storage
- Automatic old version cleanup

## Error Handling

The system provides comprehensive error handling with:

### Error Categories
- **Validation Errors**: Invalid input parameters
- **Database Errors**: Storage and retrieval issues
- **Conflict Errors**: Version conflicts and resolution
- **Security Errors**: Malicious content or unauthorized access

### Recovery Actions
- **Retry**: Temporary failures, network issues
- **Validate**: Input validation failures
- **Escalate**: Critical system errors
- **None**: Permanent failures

### Error Response Format
```json
{
  "error_code": "VALIDATION_FAILED",
  "user_message": "Invalid version parameters provided",
  "recovery_action": "retry",
  "technical_message": "Content size exceeds maximum limit"
}
```

## Testing

### Automated Test Suite

Run the comprehensive test suite:

```bash
python tests/unit/test_document_versioning.py
```

The test suite covers:
- Version creation and retrieval
- Content comparison and diff analysis
- Rollback operations and safety checks
- Conflict detection
- Data integrity validation
- Error handling scenarios

### Manual Testing

1. **Basic Operations**
   ```bash
   # Create document
   curl -X POST http://localhost:8000/api/v1/documents/upload \
     -F "files=@test.txt"
   
   # Create version
   curl -X POST http://localhost:8000/api/v1/documents/DOC_ID/versions \
     -H "Content-Type: application/json" \
     -d '{"content":"Updated content","author":"test"}'
   ```

2. **Version History**
   ```bash
   curl http://localhost:8000/api/v1/documents/DOC_ID/versions
   ```

3. **Version Comparison**
   ```bash
   curl http://localhost:8000/api/v1/versions/VERSION1/compare/VERSION2
   ```

## Monitoring and Metrics

### Key Metrics to Monitor
- Version creation rate
- Storage usage per document
- Rollback operation frequency
- Validation error rates
- Cache hit rates

### Health Checks
- Version collection connectivity
- Data integrity validation
- Performance benchmarks
- Error rate monitoring

## Best Practices

### Version Management
1. **Meaningful Change Summaries**: Always provide descriptive change summaries
2. **Regular Cleanup**: Schedule periodic version cleanup to manage storage
3. **Safety First**: Always check rollback safety before performing rollbacks
4. **Author Tracking**: Use consistent author identifiers for audit trails

### Performance
1. **Batch Operations**: Use bulk operations for multiple documents
2. **Caching**: Leverage caching for frequently accessed versions
3. **Monitoring**: Monitor storage growth and performance metrics
4. **Cleanup**: Regular cleanup of old versions to maintain performance

### Security
1. **Input Validation**: Always validate input before processing
2. **Content Scanning**: Monitor for malicious content patterns
3. **Access Logging**: Log all version operations for security auditing
4. **Safe Defaults**: Use safe default settings and require explicit overrides

## Troubleshooting

### Common Issues

1. **Version Creation Fails**
   - Check document exists
   - Validate content size limits
   - Check author format
   - Review validation errors

2. **Rollback Not Working**
   - Verify target version exists
   - Check rollback safety validation
   - Review rollback distance limits
   - Check author permissions

3. **Poor Performance**
   - Check version count per document
   - Review cleanup settings
   - Monitor cache hit rates
   - Check database connectivity

4. **Storage Issues**
   - Monitor collection sizes
   - Run cleanup operations
   - Check storage quotas
   - Review retention policies

### Debug Commands

```bash
# Check version collection status
curl http://localhost:8000/health

# Get storage statistics
curl http://localhost:8000/api/v1/documents/stats

# Check specific document versions
curl http://localhost:8000/api/v1/documents/DOC_ID/versions

# Validate rollback safety
curl http://localhost:8000/api/v1/documents/DOC_ID/rollback/VERSION_ID/safety-check
```

## Integration Guide

### Reflex UI Integration

The versioning system integrates with the Reflex UI through:

1. **Version History Display**: Show document version timeline
2. **Diff Visualization**: Display content changes between versions
3. **Rollback Interface**: Provide safe rollback operations
4. **Conflict Resolution**: Interactive conflict resolution UI

### API Client Integration

```python
class VersioningClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_version(self, doc_id, content, author, summary=""):
        return self.session.post(
            f"{self.base_url}/api/v1/documents/{doc_id}/versions",
            json={
                "content": content,
                "author": author, 
                "change_summary": summary
            }
        )
    
    def get_version_history(self, doc_id, limit=None):
        params = {"limit": limit} if limit else {}
        return self.session.get(
            f"{self.base_url}/api/v1/documents/{doc_id}/versions",
            params=params
        )
    
    def compare_versions(self, from_id, to_id):
        return self.session.get(
            f"{self.base_url}/api/v1/versions/{from_id}/compare/{to_id}"
        )
    
    def rollback_document(self, doc_id, target_version_id, author, force=False):
        return self.session.post(
            f"{self.base_url}/api/v1/documents/{doc_id}/rollback",
            json={
                "target_version_id": target_version_id,
                "author": author,
                "force": force
            }
        )
```

This comprehensive versioning system provides enterprise-grade document version control with robust safety checks, comprehensive validation, and seamless integration with the existing RAG infrastructure.