# Export and Sharing Features Guide

This guide covers the comprehensive export and sharing capabilities implemented in the RAG system, providing secure document export, link sharing, and collaboration features.

## Overview

The system now includes enterprise-grade export and sharing features:

- **Document Export**: PDF, Markdown, HTML, JSON, and Text formats
- **Chat Export**: Full conversation export with formatting and sources
- **Bulk Operations**: ZIP-compressed multi-document exports
- **Secure Sharing**: Password-protected links with expiration
- **Access Control**: Granular permissions and IP restrictions
- **Collaboration**: Team sharing with role-based access
- **Analytics**: Detailed usage tracking and security monitoring
- **External APIs**: Integration endpoints for external systems

## Export Features

### Supported Export Formats

| Format | Description | Use Cases |
|--------|-------------|-----------|
| **PDF** | Professional documents with formatting | Reports, presentations, archival |
| **Markdown** | Structured text with markup | Documentation, GitHub integration |
| **HTML** | Web-ready format with styling | Web publishing, email sharing |
| **JSON** | Structured data format | API integration, data processing |
| **Text** | Plain text format | Simple sharing, legacy systems |

### Export Types

#### Document Export
- Single document export in any supported format
- Includes metadata, processing information, and source attribution
- Customizable formatting options and page layouts

#### Chat Conversation Export
- Complete conversation history with timestamps
- Source document references and citations
- Formatted for readability and professional presentation

#### Bulk Export
- Multiple documents in a single ZIP archive
- Mixed format support (different formats per document)
- Progress tracking for large operations

### Export Options

```python
ExportOptions(
    format=ExportFormat.PDF,
    include_metadata=True,      # Document information
    include_sources=True,       # Source citations
    include_timestamps=True,    # Creation/modification dates
    include_metrics=False,      # Performance metrics
    page_size="letter",         # letter, a4, legal
    font_size=11,              # Font size for PDF
    margins={"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
    watermark=None,            # Optional watermark text
    password_protect=False,    # PDF password protection
    password=None              # Password for protected PDFs
)
```

## Sharing Features

### Share Types

- **Document Sharing**: Share individual documents
- **Conversation Sharing**: Share chat conversations
- **Export Sharing**: Share exported files
- **Collection Sharing**: Share document collections

### Access Levels

| Level | Permissions |
|-------|-------------|
| **View** | Read-only access |
| **Download** | View + download files |
| **Edit** | View + download + modify content |
| **Admin** | Full access + share management |

### Security Features

#### Password Protection
- Optional password requirement for access
- SHA-256 password hashing
- Failed attempt tracking

#### IP Restrictions
- Whitelist specific IP addresses
- Block malicious IPs automatically
- Geographic access controls

#### Domain Restrictions
- Limit access from specific domains
- Referrer-based validation
- Corporate network restrictions

#### Expiration Management
- Configurable expiration times (1 hour to 1 year)
- Automatic cleanup of expired links
- Expiration extension capabilities

### Analytics and Monitoring

#### Access Analytics
- View and download counts
- Unique visitor tracking
- Access history with timestamps
- Device and browser statistics
- Geographic access patterns
- Referrer analysis

#### Security Monitoring
- Failed access attempts
- Suspicious activity detection
- IP blocking and unblocking
- Security report generation

## API Endpoints

### Export Endpoints

#### Export Document
```http
POST /api/v1/export/document/{doc_id}
Content-Type: application/json

{
  "format": "pdf",
  "options": {
    "include_metadata": true,
    "include_sources": true,
    "page_size": "letter",
    "font_size": 11
  }
}
```

#### Export Chat Conversation
```http
POST /api/v1/export/chat
Content-Type: application/json

{
  "conversation_data": [
    {
      "role": "user",
      "content": "What is the main topic?",
      "timestamp": "2025-08-05T10:30:00Z",
      "message_id": "msg_1"
    },
    {
      "role": "assistant",
      "content": "The main topic is...",
      "timestamp": "2025-08-05T10:30:15Z",
      "message_id": "msg_2",
      "sources": [...]
    }
  ],
  "format": "pdf",
  "options": {
    "include_metadata": true,
    "include_sources": true
  }
}
```

#### Bulk Export
```http
POST /api/v1/export/bulk
Content-Type: application/json

{
  "export_requests": [
    {
      "export_type": "document",
      "format": "pdf",
      "item_ids": ["doc1", "doc2"],
      "options": {"include_metadata": true}
    },
    {
      "export_type": "document", 
      "format": "markdown",
      "item_ids": ["doc3", "doc4"],
      "options": {"include_metadata": true}
    }
  ]
}
```

#### Download Export
```http
GET /api/v1/export/{export_id}/download
```

### Sharing Endpoints

#### Create Share Link
```http
POST /api/v1/share
Content-Type: application/json
X-User-ID: user123

{
  "share_type": "document",
  "item_id": "doc_123",
  "access_level": "view",
  "expires_in_hours": 168,
  "password": "optional_password",
  "custom_message": "Check out this document!"
}
```

#### Access Shared Content
```http
GET /share/{share_token}?password=optional_password
```

#### Get Share Analytics
```http
GET /api/v1/share/{share_id}/analytics
```

#### Revoke Share Link
```http
PUT /api/v1/share/{share_id}/revoke
```

#### Extend Share Expiration
```http
PUT /api/v1/share/{share_id}/extend?additional_hours=24
```

### Collaboration Endpoints

#### Create Collaboration Invite
```http
POST /api/v1/share/{share_id}/invite
Content-Type: application/json
X-User-ID: inviter123

{
  "email": "collaborator@example.com",
  "access_level": "edit",
  "expires_in_hours": 168,
  "personal_message": "Join me in editing this document!"
}
```

#### Accept Collaboration Invite
```http
POST /api/v1/collaboration/accept/{invite_id}
```

### External API Integration

#### External Documents API
```http
GET /api/v1/external/documents?limit=50&offset=0&file_type=pdf
```

#### External Query API
```http
POST /api/v1/external/query
Content-Type: application/json
X-API-Key: your-api-key

{
  "question": "What is the main topic?",
  "max_chunks": 5
}
```

#### External Health API
```http
GET /api/v1/external/health
```

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio

async def export_and_share_document():
    async with httpx.AsyncClient() as client:
        # Export document as PDF
        export_response = await client.post(
            "http://localhost:8000/api/v1/export/document/doc_123",
            json={
                "format": "pdf",
                "options": {
                    "include_metadata": True,
                    "include_sources": True,
                    "page_size": "letter"
                }
            }
        )
        export_result = export_response.json()
        
        if export_result["success"]:
            print(f"Export created: {export_result['filename']}")
            
            # Create share link for the export
            share_response = await client.post(
                "http://localhost:8000/api/v1/share",
                json={
                    "share_type": "export_file",
                    "item_id": export_result["export_id"],
                    "access_level": "download",
                    "expires_in_hours": 24,
                    "password": "secure123"
                },
                headers={"X-User-ID": "user123"}
            )
            share_result = share_response.json()
            
            print(f"Share link created: {share_result['share_url']}")
            print(f"Expires: {share_result['expires_at']}")

# Run the example
asyncio.run(export_and_share_document())
```

### JavaScript/Frontend Example

```javascript
// Export document and create share link
async function exportAndShare(docId) {
    try {
        // Export document
        const exportResponse = await fetch(`/api/v1/export/document/${docId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                format: 'pdf',
                options: {
                    include_metadata: true,
                    include_sources: true,
                    page_size: 'letter'
                }
            })
        });
        
        const exportResult = await exportResponse.json();
        
        if (exportResult.success) {
            console.log('Export created:', exportResult.filename);
            
            // Create share link
            const shareResponse = await fetch('/api/v1/share', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': 'user123'
                },
                body: JSON.stringify({
                    share_type: 'export_file',
                    item_id: exportResult.export_id,
                    access_level: 'download',
                    expires_in_hours: 24
                })
            });
            
            const shareResult = await shareResponse.json();
            console.log('Share link:', shareResult.share_url);
            
            // Copy to clipboard
            navigator.clipboard.writeText(shareResult.share_url);
            alert('Share link copied to clipboard!');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
```

## Configuration

### Environment Variables

```bash
# Export settings
EXPORT_DIR=exports
TEMP_EXPORT_DIR=temp_exports
MAX_EXPORT_SIZE=100MB

# Sharing settings
SHARING_DATA_DIR=sharing_data
BASE_SHARE_URL=http://localhost:8000
MAX_SHARE_EXPIRATION_HOURS=8760  # 1 year

# Security settings
ENABLE_IP_RESTRICTIONS=true
ENABLE_PASSWORD_PROTECTION=true
MAX_FAILED_ATTEMPTS=10
BLOCK_SUSPICIOUS_IPS=true
```

### Performance Tuning

```python
# Export manager settings
export_manager = ExportManager(
    export_dir="exports",
    temp_dir="temp_exports"
)

# Sharing service settings
sharing_service = SharingService(
    data_dir="sharing_data",
    base_url="http://localhost:8000"
)
```

## Security Considerations

### Best Practices

1. **Password Policies**: Enforce strong passwords for protected shares
2. **Expiration Management**: Use reasonable expiration times
3. **IP Restrictions**: Limit access to trusted networks when possible
4. **Monitoring**: Regularly review access logs and security reports
5. **Cleanup**: Implement regular cleanup of expired shares and exports

### Security Features

- SHA-256 password hashing
- IP-based access controls
- Rate limiting on access attempts
- Automatic blocking of suspicious activity
- Comprehensive audit logging
- Secure token generation
- HTTPS enforcement (in production)

## Monitoring and Maintenance

### Regular Tasks

1. **Cleanup Expired Items**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/sharing/cleanup
   ```

2. **Generate Security Reports**:
   ```bash
   curl http://localhost:8000/api/v1/sharing/security-report
   ```

3. **Monitor Storage Usage**:
   - Check export directory sizes
   - Clean up old export files
   - Monitor sharing data growth

### Error Handling

The system includes comprehensive error handling:
- Export failures with detailed error messages
- Access validation with clear rejection reasons
- Automatic retry mechanisms for transient failures
- Graceful degradation when services are unavailable

## Integration Examples

### Webhook Integration

Set up webhooks to notify external systems of sharing events:

```python
# Custom webhook handler
async def handle_share_created(share_id, share_url, creator_id):
    webhook_url = "https://your-system.com/webhooks/share-created"
    
    payload = {
        "event": "share_created",
        "share_id": share_id,
        "share_url": share_url,
        "creator_id": creator_id,
        "timestamp": datetime.now().isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload)
```

### Enterprise SSO Integration

Integrate with enterprise authentication systems:

```python
# Custom authentication handler
async def validate_enterprise_user(share_token, user_token):
    # Validate with enterprise SSO
    sso_response = await validate_with_sso(user_token)
    
    if sso_response.valid:
        # Allow access based on enterprise permissions
        return True, sso_response.user_info
    
    return False, None
```

This comprehensive export and sharing system provides enterprise-grade capabilities while maintaining the local-first, privacy-preserving design of the RAG system.