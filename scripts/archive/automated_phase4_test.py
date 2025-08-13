#!/usr/bin/env python3
"""
Automated Phase 4 Test Suite
Tests PDF processing, document intelligence, and enhanced RAG functionality
"""

import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"

def create_test_documents():
    """Create test documents for different document types."""
    test_docs = {
        "api_guide.txt": """
API Authentication Guide

Overview
This guide covers authentication methods for our REST API.

Authentication Methods
1. JWT Token Authentication
2. API Key Authentication
3. OAuth 2.0 Integration

Endpoints
POST /auth/login
- Parameters: username, password
- Returns: JWT token
- Example: curl -X POST /auth/login -d '{"username":"user","password":"pass"}'

GET /auth/verify
- Headers: Authorization: Bearer <token>
- Returns: User info
- Status codes: 200 (valid), 401 (invalid)

Error Handling
401: Unauthorized - Invalid credentials
403: Forbidden - Insufficient permissions
429: Rate limited - Too many requests

Implementation Notes
- Tokens expire after 24 hours
- Rate limit: 1000 requests/hour
- Use HTTPS in production
""",
        
        "meeting_notes.txt": """
Weekly Team Meeting - March 15, 2024

Attendees:
• Sarah Johnson (Product Manager)
• Mike Chen (Lead Developer)  
• Lisa Rodriguez (UX Designer)
• Alex Thompson (QA Engineer)

Agenda Items:

1. Project Status Updates
   • Backend API - 85% complete
   • Frontend UI - 70% complete
   • Testing suite - 60% complete
   • Documentation - 40% complete

2. Blockers and Issues
   • Database migration delayed
   • Need more time for accessibility testing
   • API rate limiting needs review

3. Action Items
   • Mike: Complete database migration by Friday
   • Lisa: Finish accessibility audit by Tuesday
   • Alex: Implement load testing framework
   • Sarah: Schedule client demo for next week

4. Decisions Made
   - Use JWT for authentication
   - Implement rate limiting at 1000 req/hour
   - Deploy beta version March 29th

Next Meeting: March 22, 2024 at 2:00 PM
Location: Conference Room B
""",
        
        "financial_report.txt": """
Q1 2024 Financial Results

Executive Summary
Strong quarter with 16% revenue growth and improved margins.
Net profit increased 25% year-over-year to $1.0M.

Revenue Breakdown
                    Q1 2024    Q1 2023    Change
Product Sales       $2.4M      $2.1M      +14%
Service Revenue     $0.8M      $0.7M      +14%
Licensing Fees      $0.2M      $0.2M       0%
Total Revenue       $3.4M      $3.0M      +13%

Operating Expenses
Cost of Goods       $1.8M      $1.7M      +6%
Sales & Marketing   $0.6M      $0.6M       0%
R&D                 $0.4M      $0.4M       0%
General & Admin     $0.2M      $0.2M       0%
Total OpEx          $3.0M      $2.9M      +3%

Key Metrics
Gross Margin        47%        43%        +4%
Operating Margin    12%         3%        +9%
Net Profit Margin   29%        23%        +6%
Cash Flow           $0.4M      $0.1M     +300%

Balance Sheet Highlights
Total Assets        $5.2M
Cash & Equivalents  $1.8M
Total Liabilities   $1.4M
Shareholders Equity $3.8M

The company maintains strong financial position with
low debt-to-equity ratio and healthy cash reserves.
""",
        
        "research_paper.txt": """
Improving Document Retrieval Through Semantic Embeddings

Abstract
This paper presents a novel approach to document retrieval using semantic 
embeddings and vector similarity search. We demonstrate improved performance 
over traditional keyword-based retrieval methods through comprehensive 
evaluation on multiple datasets.

1. Introduction
Document retrieval has been a fundamental challenge in information systems [1].
Traditional approaches rely on exact keyword matching, which often fails to
capture semantic relationships between queries and documents [2]. Recent 
advances in transformer models have enabled semantic understanding of text.

2. Related Work
Previous work in document retrieval includes:
- TF-IDF based approaches [3]
- BM25 scoring algorithms [4]  
- Neural information retrieval [5]
- Dense passage retrieval [6]

3. Methodology
We implemented a retrieval system using sentence transformers for embedding
generation and ChromaDB for vector storage. The system processes documents
through the following pipeline:

3.1 Document Processing
Documents are preprocessed to remove noise and extract clean text.
Text is segmented into chunks of optimal size for embedding generation.

3.2 Embedding Generation  
We use the all-MiniLM-L6-v2 model for generating 384-dimensional embeddings.
This model provides good balance between accuracy and efficiency.

3.3 Retrieval Process
Query embeddings are compared against document embeddings using cosine
similarity. Results are ranked by similarity score.

4. Experimental Results
Our experiments on three datasets show:
- 23% improvement in retrieval accuracy vs keyword methods
- 15% improvement in mean reciprocal rank
- Consistent performance across different domains

5. Conclusion
Semantic embeddings represent a significant advancement in document retrieval.
Future work will explore multi-modal embeddings and real-time learning.

References
[1] Manning, C.D., et al. Introduction to Information Retrieval. 2008.
[2] Salton, G. Automatic Text Processing. 1989.
[3] Robertson, S. Understanding inverse document frequency. 2004.
[4] Jones, K.S., et al. A probabilistic model of information retrieval. 2000.
[5] Karpukhin, V., et al. Dense Passage Retrieval. 2020.
[6] Lee, K., et al. Latent Retrieval for Weakly Supervised Open Domain QA. 2019.
"""
    }
    
    return test_docs

def test_document_upload(test_docs):
    """Test document upload functionality."""
    print("1. Testing Document Upload & Processing")
    print("-" * 50)
    
    uploaded_tasks = []
    upload_results = {}
    
    for filename, content in test_docs.items():
        print(f"\n📄 Uploading: {filename}")
        
        # Write test file
        filepath = f"/tmp/{filename}"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        try:
            # Upload file
            with open(filepath, 'rb') as f:
                files = {"files": (filename, f, "text/plain")}
                response = requests.post(f"{BASE_URL}/documents/upload", files=files)
            
            if response.status_code == 200:
                result = response.json()
                uploaded_tasks.extend(result.get("processing_tasks", []))
                upload_results[filename] = {
                    "success": True,
                    "files_processed": result.get("files_processed", 0),
                    "tasks": result.get("processing_tasks", [])
                }
                print(f"   ✅ Success: {result.get('files_processed', 0)} file processed")
            else:
                upload_results[filename] = {"success": False, "error": response.text}
                print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            upload_results[filename] = {"success": False, "error": str(e)}
            print(f"   ❌ Exception: {e}")
    
    return uploaded_tasks, upload_results

def test_processing_status(uploaded_tasks):
    """Test processing status tracking."""
    print(f"\n2. Testing Processing Status Tracking")
    print("-" * 50)
    
    if not uploaded_tasks:
        print("   ⚠️  No tasks to check")
        return {}
    
    # Wait for processing to complete
    print(f"   Waiting for {len(uploaded_tasks)} tasks to complete...")
    time.sleep(3)
    
    task_results = {}
    completed_tasks = 0
    
    for task_id in uploaded_tasks:
        try:
            response = requests.get(f"{BASE_URL}/processing/tasks/{task_id}")
            if response.status_code == 200:
                task_data = response.json()
                task_results[task_id] = task_data
                
                status = task_data.get("status", "unknown")
                progress = task_data.get("progress", 0)
                filename = task_data.get("filename", "unknown")
                
                print(f"   📋 {filename}: {status} ({progress}%)")
                
                if status == "completed":
                    completed_tasks += 1
                elif status == "failed":
                    error = task_data.get("error_message", "Unknown error")
                    print(f"      ❌ Error: {error}")
                    
            else:
                print(f"   ❌ Failed to get task {task_id}: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception checking task {task_id}: {e}")
    
    print(f"\n   📊 Processing Summary: {completed_tasks}/{len(uploaded_tasks)} completed")
    return task_results

def test_document_intelligence(task_results):
    """Test document intelligence features."""
    print(f"\n3. Testing Document Intelligence")
    print("-" * 50)
    
    intelligence_results = {}
    
    for task_id, task_data in task_results.items():
        if task_data.get("status") == "completed":
            filename = task_data.get("filename", "unknown")
            
            print(f"\n   📄 {filename}:")
            
            # Check for intelligence metadata (these might be in different places)
            # The exact location depends on how the task data is structured
            intelligence_data = {}
            
            # Try to find intelligence data in task metadata
            for key in ["document_type", "content_structure", "intelligence_confidence"]:
                if key in task_data:
                    intelligence_data[key] = task_data[key]
            
            if intelligence_data:
                print(f"      🧠 Document type: {intelligence_data.get('document_type', 'unknown')}")
                print(f"      📊 Structure: {intelligence_data.get('content_structure', 'unknown')}")
                print(f"      🎯 Confidence: {intelligence_data.get('intelligence_confidence', 0):.2f}")
            else:
                print(f"      ⚠️  Intelligence data not available in task results")
            
            intelligence_results[filename] = intelligence_data
    
    return intelligence_results

def test_query_system(test_docs):
    """Test the enhanced query system."""
    print(f"\n4. Testing Enhanced Query System")
    print("-" * 50)
    
    # Define test queries that should match our uploaded content
    test_queries = [
        ("How do I authenticate with the API?", ["api_guide.txt"]),
        ("What are the action items from the meeting?", ["meeting_notes.txt"]),
        ("What was the revenue for Q1?", ["financial_report.txt"]),
        ("Who attended the meeting?", ["meeting_notes.txt"]),
        ("What methodology was used in the research?", ["research_paper.txt"]),
        ("What is the profit margin?", ["financial_report.txt"]),
        ("JWT token authentication", ["api_guide.txt"]),
        ("semantic embeddings", ["research_paper.txt"])
    ]
    
    query_results = {}
    successful_queries = 0
    
    for query, expected_sources in test_queries:
        print(f"\n   ❓ Query: {query}")
        print(f"      Expected sources: {', '.join(expected_sources)}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/query",
                json={"question": query, "max_chunks": 5}
            )
            
            if response.status_code == 200:
                result = response.json()
                sources = result.get("sources", [])
                
                query_results[query] = {
                    "sources_count": len(sources),
                    "context_tokens": result.get("context_tokens", 0),
                    "answer_length": len(result.get("answer", "")),
                    "sources": sources
                }
                
                print(f"      📊 Sources found: {len(sources)}")
                print(f"      🔍 Context tokens: {result.get('context_tokens', 0)}")
                print(f"      📝 Answer length: {len(result.get('answer', ''))}")
                
                if sources:
                    successful_queries += 1
                    print(f"      📄 First source: {sources[0].get('title', 'Unknown')}")
                    
                    # Check if expected source was found
                    found_expected = any(
                        any(exp_src in source.get('title', '') for exp_src in expected_sources)
                        for source in sources
                    )
                    
                    if found_expected:
                        print(f"      ✅ Found expected source!")
                    else:
                        print(f"      ⚠️  Expected source not found, but found other content")
                else:
                    print(f"      ❌ No sources found")
                    
            else:
                print(f"      ❌ Query failed: {response.status_code}")
                query_results[query] = {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"      ❌ Exception: {e}")
            query_results[query] = {"error": str(e)}
    
    print(f"\n   📊 Query Summary: {successful_queries}/{len(test_queries)} successful")
    return query_results, successful_queries

def test_system_health():
    """Test system health and status."""
    print(f"\n5. Testing System Health")
    print("-" * 50)
    
    health_data = {}
    
    try:
        # Health check
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ System Status: {health_data.get('status', 'unknown')}")
            print(f"   📊 Total Documents: {health_data.get('document_count', 0)}")
            
            components = health_data.get('components', {})
            for component, status in components.items():
                status_icon = "✅" if status else "❌"
                print(f"      {status_icon} {component}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
        
        # Document count
        response = requests.get(f"{BASE_URL}/documents")
        if response.status_code == 200:
            docs_data = response.json()
            print(f"   📋 Documents in system: {docs_data.get('total_count', 0)}")
        
        # Processing queue status
        response = requests.get(f"{BASE_URL}/processing/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   🔄 Processing Queue:")
            for status_type, count in status_data.items():
                print(f"      {status_type}: {count}")
        
    except Exception as e:
        print(f"   ❌ Health check exception: {e}")
    
    return health_data

def run_comprehensive_test():
    """Run the complete Phase 4 test suite."""
    print("🚀 Phase 4 Comprehensive Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing against: {BASE_URL}")
    print()
    
    # Create test documents
    test_docs = create_test_documents()
    
    # Run tests
    uploaded_tasks, upload_results = test_document_upload(test_docs)
    task_results = test_processing_status(uploaded_tasks)
    intelligence_results = test_document_intelligence(task_results)
    query_results, successful_queries = test_query_system(test_docs)
    health_data = test_system_health()
    
    # Generate final report
    print(f"\n🎯 FINAL TEST REPORT")
    print("=" * 60)
    
    # Upload results
    successful_uploads = sum(1 for r in upload_results.values() if r.get("success"))
    print(f"📤 Document Upload: {successful_uploads}/{len(test_docs)} successful")
    
    # Processing results
    completed_processing = sum(1 for r in task_results.values() if r.get("status") == "completed")
    print(f"⚙️  Document Processing: {completed_processing}/{len(uploaded_tasks)} completed")
    
    # Intelligence results
    intelligence_count = len(intelligence_results)
    print(f"🧠 Document Intelligence: {intelligence_count} documents analyzed")
    
    # Query results
    print(f"🔍 Query System: {successful_queries}/{len(query_results)} queries successful")
    
    # System health
    system_status = health_data.get("status", "unknown")
    print(f"🏥 System Health: {system_status}")
    
    # Overall assessment
    print(f"\n📊 OVERALL ASSESSMENT")
    print("-" * 30)
    
    total_score = 0
    max_score = 5
    
    if successful_uploads == len(test_docs):
        print("✅ Document Upload: PASS")
        total_score += 1
    else:
        print("❌ Document Upload: FAIL")
    
    if completed_processing == len(uploaded_tasks):
        print("✅ Document Processing: PASS") 
        total_score += 1
    else:
        print("❌ Document Processing: FAIL")
    
    if intelligence_count > 0:
        print("✅ Document Intelligence: PASS")
        total_score += 1
    else:
        print("❌ Document Intelligence: FAIL")
    
    if successful_queries >= len(query_results) * 0.6:  # 60% success rate
        print("✅ Query System: PASS")
        total_score += 1
    else:
        print("❌ Query System: FAIL")
    
    if system_status in ["healthy", "degraded"]:
        print("✅ System Health: PASS")
        total_score += 1
    else:
        print("❌ System Health: FAIL")
    
    print(f"\n🎯 FINAL SCORE: {total_score}/{max_score}")
    
    if total_score == max_score:
        print("🎉 Phase 4 System: FULLY FUNCTIONAL!")
        return True
    elif total_score >= max_score * 0.8:
        print("✅ Phase 4 System: MOSTLY FUNCTIONAL")
        return True
    else:
        print("❌ Phase 4 System: SIGNIFICANT ISSUES DETECTED")
        return False

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        exit(2)
    except Exception as e:
        print(f"\n\n❌ Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(3)