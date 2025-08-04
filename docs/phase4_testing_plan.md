# Phase 4 Testing Plan: PDF Processing & Document Intelligence

This document provides a comprehensive testing plan for Phase 4 features including PDF processing, document intelligence, and enhanced RAG capabilities.

## Overview

Phase 4 introduces several major enhancements:
- **PDF Processing Engine**: Multi-library PDF text extraction
- **Document Intelligence**: Automatic document type detection and analysis
- **Enhanced Metadata**: Comprehensive document feature extraction
- **Intelligent Chunking**: Document-type-specific optimization strategies
- **Quality Scoring**: Content quality assessment algorithms

## Prerequisites

### System Requirements
- Python 3.10+
- All dependencies from `requirements.txt` installed
- Ollama running locally (optional for basic functionality)
- ~8GB RAM recommended for full testing

### Setup
```bash
# Install dependencies
cd app
pip install -r requirements.txt

# Start the RAG backend
python main.py

# Optional: Start Reflex UI (in separate terminal)
cd reflex_app
reflex run
```

## Test Categories

### 1. PDF Processing Tests

#### 1.1 Basic PDF Upload
**Objective**: Verify PDF files can be uploaded and processed

**Test Steps**:
1. Create a simple PDF file (or use any existing PDF)
2. Upload via API: `POST /documents/upload` with `Content-Type: application/pdf`
3. Check processing status: `GET /processing/tasks/{task_id}`
4. Verify document appears in list: `GET /documents`

**Expected Results**:
- Upload returns 200 status
- Processing completes successfully (status: "completed")
- Document appears in document list with `file_type: "pdf"`
- Metadata includes PDF-specific fields (page_count, extraction_method, quality_score)

**Test Script**: Use `scripts/test_pdf_processing.py`

#### 1.2 PDF Text Extraction
**Objective**: Verify text is correctly extracted from PDFs

**Test Data**: Create PDFs with different characteristics:
- Simple text-only PDF
- PDF with tables
- PDF with images
- Complex layout PDF
- Scanned PDF (OCR not implemented, should gracefully fail)

**Test Steps**:
1. Upload each PDF type
2. Query for content that should exist in the PDFs
3. Verify extraction quality scores

**Expected Results**:
- Text-only PDFs: High quality scores (>0.7)
- Complex PDFs: Moderate quality scores (>0.4)
- Extraction method fallback works (tries PyMuPDF → pdfplumber → PyPDF2)

#### 1.3 PDF Metadata Extraction
**Objective**: Verify PDF metadata is correctly extracted

**Test Steps**:
1. Upload PDFs with known metadata (title, author, creation date)
2. Check document metadata via `GET /documents/{doc_id}`
3. Verify metadata fields are populated

**Expected Results**:
- PDF metadata correctly extracted and stored
- Fallback to filename when metadata unavailable

### 2. Document Intelligence Tests

#### 2.1 Document Type Classification
**Objective**: Test automatic document type detection

**Test Documents** (create these files):

```
technical_manual.txt:
"""
API Documentation - Authentication Service

Overview
This guide covers authentication methods for our REST API.

Endpoints
POST /auth/login - User authentication
GET /auth/verify - Token verification

Parameters
- username (string): User login name
- password (string): User password

Error Codes
401: Unauthorized
403: Forbidden
"""

research_paper.txt:
"""
Improving Document Retrieval Through Semantic Embeddings

Abstract
This paper presents a novel approach to document retrieval using semantic embeddings.

1. Introduction
Document retrieval has been a fundamental challenge [1]. Traditional keyword-based 
methods often fail to capture semantic relationships [2].

2. Methodology
We implemented a system using sentence transformers for embedding generation.

References
[1] Manning, C.D. Introduction to Information Retrieval. 2008.
[2] Salton, G. Automatic Text Processing. 1989.
"""

meeting_notes.txt:
"""
Weekly Team Meeting - March 15, 2024

Attendees:
• Sarah Johnson (Product Manager)
• Mike Chen (Lead Developer)
• Lisa Rodriguez (UX Designer)

Action Items:
• Mike: Complete API documentation by Friday
• Lisa: Finalize UI mockups by Tuesday
• Sarah: Schedule client demo next week

Next Meeting: March 22, 2024
"""

financial_report.txt:
"""
Q1 2024 Financial Results

Revenue Breakdown
Product Sales    $2.4M    (+15% YoY)
Services         $0.8M    (+20% YoY)
Total Revenue    $3.2M    (+16% YoY)

Operating Expenses
R&D              $1.2M
Marketing        $0.6M
Operations       $0.4M
Total OpEx       $2.2M

Net Profit: $1.0M (31% margin)
"""
```

**Test Steps**:
1. Upload each document type
2. Check processing task details for document intelligence results
3. Verify document type classification

**Expected Results**:
- `technical_manual.txt` → `document_type: "code_documentation"`
- `research_paper.txt` → `document_type: "research_paper"`
- `meeting_notes.txt` → `document_type: "meeting_notes"`
- `financial_report.txt` → `document_type: "financial_report"`

#### 2.2 Content Structure Analysis
**Objective**: Test document structure detection

**Test Steps**:
1. Upload documents with different structures (hierarchical, list-heavy, tabular)
2. Check `content_structure` field in processing results
3. Verify appropriate chunking parameters are suggested

**Expected Results**:
- Documents with headings → `"hierarchical"`
- Documents with many bullet points → `"list_heavy"`
- Documents with tables → `"tabular"`
- Plain text → `"linear"`

#### 2.3 Intelligent Chunking
**Objective**: Verify document-type-specific chunking strategies

**Test Steps**:
1. Upload documents of different types
2. Check `suggested_chunk_size` and `suggested_overlap` values
3. Query documents to verify chunking quality

**Expected Results**:
- Technical docs: Larger chunks (500-600 tokens)
- Legal docs: Very large chunks (800+ tokens)
- News articles: Smaller chunks (300 tokens)
- Meeting notes: Small-medium chunks (250 tokens)

### 3. Enhanced Query System Tests

#### 3.1 Basic Query Functionality
**Objective**: Verify query system works with new features

**Test Steps**:
1. Upload test documents
2. Query for specific information that exists in documents
3. Verify sources are returned with proper metadata

**Test Queries**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I authenticate with the API?", "max_chunks": 3}'
```

**Expected Results**:
- Relevant sources returned
- Context tokens calculated correctly
- Document intelligence metadata included in source metadata

#### 3.2 Semantic Search Quality
**Objective**: Test semantic search with different document types

**Test Steps**:
1. Upload documents from different domains
2. Test queries with:
   - Exact keyword matches
   - Semantic similarity (synonyms)
   - Cross-document information

**Expected Results**:
- High-quality matches for exact terms
- Reasonable matches for semantic queries
- Proper ranking by relevance

#### 3.3 Similarity Threshold Testing
**Objective**: Verify similarity threshold is properly calibrated

**Test Steps**:
1. Upload a known test document
2. Query with various similarity levels
3. Test edge cases (very specific vs. very general queries)

**Expected Results**:
- Default threshold (0.6) returns relevant results
- Very specific queries find exact matches
- General queries return broader but relevant content

### 4. Processing Status & Monitoring Tests

#### 4.1 Processing Status Tracking
**Objective**: Test real-time processing status updates

**Test Steps**:
1. Upload a document
2. Immediately check processing status: `GET /processing/tasks/{task_id}`
3. Monitor progress updates
4. Verify completion status

**Expected Results**:
- Status progresses through: pending → in_progress → completed
- Progress percentage increases appropriately
- Final status includes processing notes and intelligence results

#### 4.2 Error Handling
**Objective**: Test system behavior with problematic inputs

**Test Cases**:
- Upload invalid PDF files
- Upload extremely large files
- Upload files with unsupported formats
- Network interruptions during processing

**Expected Results**:
- Graceful error handling
- Appropriate error messages
- Failed tasks marked as "failed" with error details
- System remains stable

### 5. Integration Tests

#### 5.1 End-to-End Workflow
**Objective**: Test complete document processing pipeline

**Test Steps**:
1. Upload multiple document types simultaneously
2. Monitor processing queue
3. Query across all uploaded documents
4. Verify cross-document search works

**Expected Results**:
- All documents processed successfully
- Queue management works correctly
- Cross-document queries return relevant results from multiple sources

#### 5.2 Performance Testing
**Objective**: Test system performance under load

**Test Steps**:
1. Upload 10+ documents of various types
2. Execute multiple concurrent queries
3. Monitor response times and resource usage

**Expected Results**:
- Upload processing completes within reasonable time (< 2 min per document)
- Query response time < 5 seconds
- System remains responsive under load

### 6. API Endpoint Tests

#### 6.1 New Endpoint Functionality
**Test all enhanced endpoints**:

```bash
# Health check with document intelligence
GET /health

# Enhanced document upload
POST /documents/upload (supports PDF + intelligence analysis)

# Processing status endpoints
GET /processing/status
GET /processing/tasks
GET /processing/tasks/{doc_id}
POST /processing/cleanup

# Enhanced document listing (with intelligence metadata)
GET /documents

# Query with intelligence-enhanced results
POST /query
```

#### 6.2 Backward Compatibility
**Objective**: Ensure existing functionality still works

**Test Steps**:
1. Test all Phase 3 functionality
2. Verify existing API contracts unchanged
3. Check that old documents still query correctly

**Expected Results**:
- All existing functionality preserved
- No breaking changes to API responses
- Legacy documents work with new query system

## Automated Testing

### Quick Test Script
Create and run this comprehensive test:

```python
#!/usr/bin/env python3
"""Automated Phase 4 test suite"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def run_phase4_tests():
    print("🚀 Phase 4 Automated Test Suite")
    print("=" * 50)
    
    # Test 1: Upload different document types
    test_docs = {
        "api_guide.txt": "API Authentication Guide\n\nPOST /auth/login\nReturns JWT token",
        "meeting.txt": "Meeting Notes\n\nAttendees:\n• John Doe\n• Jane Smith\n\nAction Items:\n• Deploy by Friday",
        "report.txt": "Financial Report\n\nRevenue: $1M\nProfit: $200K\nMargin: 20%"
    }
    
    uploaded_tasks = []
    
    for filename, content in test_docs.items():
        with open(f"/tmp/{filename}", "w") as f:
            f.write(content)
        
        with open(f"/tmp/{filename}", "rb") as f:
            files = {"files": (filename, f, "text/plain")}
            response = requests.post(f"{BASE_URL}/documents/upload", files=files)
        
        if response.status_code == 200:
            result = response.json()
            uploaded_tasks.extend(result.get("processing_tasks", []))
            print(f"✅ Uploaded {filename}")
        else:
            print(f"❌ Failed to upload {filename}")
    
    # Test 2: Check processing completion
    time.sleep(2)  # Allow processing time
    
    completed_tasks = 0
    for task_id in uploaded_tasks:
        response = requests.get(f"{BASE_URL}/processing/tasks/{task_id}")
        if response.status_code == 200:
            task = response.json()
            if task["status"] == "completed":
                completed_tasks += 1
    
    print(f"📊 Processing: {completed_tasks}/{len(uploaded_tasks)} completed")
    
    # Test 3: Query system
    test_queries = [
        "How do I authenticate?",
        "What are the action items?",
        "What is the profit margin?"
    ]
    
    successful_queries = 0
    for query in test_queries:
        response = requests.post(f"{BASE_URL}/query", json={"question": query})
        if response.status_code == 200:
            result = response.json()
            if result.get("sources"):
                successful_queries += 1
                print(f"✅ Query '{query}' found {len(result['sources'])} sources")
            else:
                print(f"❌ Query '{query}' found no sources")
    
    # Test 4: System health
    response = requests.get(f"{BASE_URL}/health")
    system_healthy = response.status_code == 200
    
    print(f"\n📊 Test Results:")
    print(f"   Documents uploaded: {len(uploaded_tasks)}/3")
    print(f"   Processing completed: {completed_tasks}/{len(uploaded_tasks)}")
    print(f"   Successful queries: {successful_queries}/{len(test_queries)}")
    print(f"   System health: {'✅' if system_healthy else '❌'}")
    
    if completed_tasks == len(uploaded_tasks) and successful_queries > 0:
        print(f"\n🎉 Phase 4 System: FULLY FUNCTIONAL!")
    else:
        print(f"\n⚠️  Phase 4 System: Issues detected")

if __name__ == "__main__":
    run_phase4_tests()
```

Save as `scripts/automated_phase4_test.py` and run with:
```bash
python scripts/automated_phase4_test.py
```

## Expected Test Outcomes

### Success Criteria
- **Document Upload**: 100% success rate for supported formats
- **PDF Processing**: >90% success rate with quality scores >0.4
- **Document Intelligence**: >80% correct document type classification
- **Query System**: >70% of semantic queries return relevant results
- **Processing Speed**: <2 minutes per document, <5 seconds per query
- **System Stability**: No crashes or memory leaks during testing

### Known Limitations
- **OCR**: Scanned PDFs require OCR (not implemented)
- **Complex Tables**: May not preserve table structure perfectly
- **Large Files**: Files >50MB may have performance issues
- **Semantic Matching**: Some queries may not find semantically similar content

## Troubleshooting Common Issues

### PDF Processing Fails
1. Check file is valid PDF
2. Verify PDF libraries installed (`pip install PyPDF2 pdfplumber pymupdf`)
3. Check server logs for extraction errors

### Document Intelligence Not Working
1. Verify `document_intelligence.py` imported correctly
2. Check processing task logs for intelligence analysis errors
3. Ensure feature analysis completed successfully

### Queries Return No Results
1. Check similarity threshold (default: 0.6)
2. Verify documents were processed and stored
3. Test with very specific keyword queries first
4. Check Ollama is running for LLM responses (optional)

### Performance Issues
1. Monitor memory usage during bulk uploads
2. Check ChromaDB storage space
3. Restart services if memory leaks suspected
4. Consider processing documents in smaller batches

## Conclusion

This testing plan ensures comprehensive validation of all Phase 4 features. Regular execution of these tests will help maintain system quality and catch regressions early in development.

For automated testing in CI/CD pipelines, focus on the API endpoint tests and the automated test script. Manual testing is recommended for UI features and complex document scenarios.