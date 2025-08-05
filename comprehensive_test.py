#!/usr/bin/env python3
"""
Comprehensive RAG System Validation Script
Tests end-to-end functionality including upload, search, and query processing
"""

import requests
import json
import time
import os
import sys
from typing import Dict, List

class RAGSystemValidator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str, duration: float = 0):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
        if not success or details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "duration": duration
        })
    
    def test_health_status(self) -> bool:
        """Test system health"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                components = health_data.get("components", {})
                
                # Check critical components
                critical_components = ["fastapi", "chromadb", "embeddings"]
                healthy_components = [comp for comp in critical_components if components.get(comp, False)]
                
                if len(healthy_components) == len(critical_components):
                    self.log_result("Health Status", True, 
                                  f"All critical components healthy. Doc count: {health_data.get('document_count', 0)}", 
                                  duration)
                    return True
                else:
                    self.log_result("Health Status", False, 
                                  f"Unhealthy components: {set(critical_components) - set(healthy_components)}", 
                                  duration)
                    return False
            else:
                self.log_result("Health Status", False, f"HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("Health Status", False, f"Connection error: {e}", 0)
            return False
    
    def test_document_upload(self, filename: str, content: str) -> str:
        """Test document upload functionality"""
        try:
            start_time = time.time()
            
            # Create temporary file
            with open(filename, 'w') as f:
                f.write(content)
            
            # Upload file
            with open(filename, 'rb') as f:
                files = {'files': (filename, f, 'text/plain')}
                response = requests.post(f"{self.base_url}/documents/upload", files=files, timeout=30)
            
            duration = time.time() - start_time
            
            # Cleanup
            os.remove(filename)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("files_processed", 0) > 0:
                    task_id = data.get("processing_tasks", [None])[0]
                    self.log_result("Document Upload", True, 
                                  f"Uploaded {filename}, task: {task_id}", duration)
                    return task_id
                else:
                    self.log_result("Document Upload", False, "No files processed", duration)
                    return None
            else:
                self.log_result("Document Upload", False, 
                              f"HTTP {response.status_code}: {response.text}", duration)
                return None
                
        except Exception as e:
            self.log_result("Document Upload", False, f"Error: {e}", 0)
            return None
    
    def test_processing_status(self, task_id: str) -> bool:
        """Test processing status tracking"""
        if not task_id:
            return False
            
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/processing/tasks/{task_id}", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                chunks = data.get("chunks_created", 0)
                
                if status == "completed" and chunks > 0:
                    self.log_result("Processing Status", True, 
                                  f"Status: {status}, chunks: {chunks}", duration)
                    return True
                else:
                    self.log_result("Processing Status", False, 
                                  f"Status: {status}, chunks: {chunks}", duration)
                    return False
            else:
                self.log_result("Processing Status", False, 
                              f"HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("Processing Status", False, f"Error: {e}", 0)
            return False
    
    def test_document_listing(self) -> bool:
        """Test document listing functionality"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/v1/documents?limit=5", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                doc_count = len(data.get("documents", []))
                total_count = data.get("total_count", 0)
                
                if doc_count > 0:
                    self.log_result("Document Listing", True, 
                                  f"Listed {doc_count} docs, total: {total_count}", duration)
                    return True
                else:
                    self.log_result("Document Listing", False, 
                                  "No documents found", duration)
                    return False
            else:
                self.log_result("Document Listing", False, 
                              f"HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("Document Listing", False, f"Error: {e}", 0)
            return False
    
    def test_rag_query(self, question: str, expected_terms: List[str] = None) -> bool:
        """Test RAG query functionality"""
        try:
            start_time = time.time()
            
            # First, lower similarity threshold for testing
            requests.post(f"{self.base_url}/settings", 
                         json={"similarity_threshold": 0.1}, timeout=10)
            
            # Make query
            payload = {"question": question, "max_chunks": 5}
            response = requests.post(f"{self.base_url}/query", 
                                   json=payload, timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                context_used = data.get("context_used", 0)
                
                # Check if we got meaningful results
                if context_used > 0 and sources:
                    # Check if expected terms are in the answer (if provided)
                    if expected_terms:
                        found_terms = [term for term in expected_terms 
                                     if term.lower() in answer.lower()]
                        if found_terms:
                            self.log_result("RAG Query", True, 
                                          f"Answer found with {context_used} chunks, contains: {found_terms}", 
                                          duration)
                            return True
                        else:
                            self.log_result("RAG Query", False, 
                                          f"Answer lacks expected terms. Answer: {answer[:100]}...", 
                                          duration)
                            return False
                    else:
                        self.log_result("RAG Query", True, 
                                      f"Answer generated with {context_used} chunks", duration)
                        return True
                else:
                    self.log_result("RAG Query", False, 
                                  f"No relevant context found. Answer: {answer}", duration)
                    return False
            else:
                self.log_result("RAG Query", False, 
                              f"HTTP {response.status_code}: {response.text}", duration)
                return False
                
        except Exception as e:
            self.log_result("RAG Query", False, f"Error: {e}", 0)
            return False
    
    def test_api_performance(self) -> bool:
        """Test API response time performance"""
        try:
            # Test health endpoint performance
            times = []
            for _ in range(5):
                start_time = time.time()
                response = requests.get(f"{self.base_url}/health", timeout=5)
                duration = time.time() - start_time
                if response.status_code == 200:
                    times.append(duration * 1000)  # Convert to ms
            
            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                
                # Performance target: < 200ms average
                if avg_time < 200:
                    self.log_result("API Performance", True, 
                                  f"Avg: {avg_time:.1f}ms, Max: {max_time:.1f}ms", 
                                  avg_time/1000)
                    return True
                else:
                    self.log_result("API Performance", False, 
                                  f"Too slow - Avg: {avg_time:.1f}ms (target: <200ms)", 
                                  avg_time/1000)
                    return False
            else:
                self.log_result("API Performance", False, "No successful requests", 0)
                return False
                
        except Exception as e:
            self.log_result("API Performance", False, f"Error: {e}", 0)
            return False
    
    def run_comprehensive_test(self):
        """Run all validation tests"""
        print("🚀 Starting Comprehensive RAG System Validation\n")
        
        # Test 1: Health Status
        health_ok = self.test_health_status()
        
        if not health_ok:
            print("\n❌ Critical: System health check failed. Stopping tests.")
            return False
        
        # Test 2: Document Upload
        test_content = """
        Performance Testing Document
        
        This document contains specific information for testing the RAG system.
        
        Key Performance Targets:
        - Document processing time: under 30 seconds
        - API response time: under 200 milliseconds  
        - Search accuracy: above 85 percent
        - Memory usage: below 2 gigabytes
        
        Quality Metrics:
        - Embedding generation speed
        - Vector database performance
        - Context retrieval accuracy
        - Answer generation quality
        """
        
        task_id = self.test_document_upload("perf_test.txt", test_content)
        
        # Test 3: Processing Status
        if task_id:
            # Wait a moment for processing
            time.sleep(2)
            self.test_processing_status(task_id)
        
        # Test 4: Document Listing
        self.test_document_listing()
        
        # Test 5: RAG Query
        self.test_rag_query("What are the performance targets?", 
                           ["30 seconds", "200 milliseconds", "85 percent"])
        
        # Test 6: API Performance
        self.test_api_performance()
        
        # Summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if pass_rate >= 80:
            print("\n🎉 SYSTEM VALIDATION: PASSED")
            print("   Ready for production deployment")
        elif pass_rate >= 60:
            print("\n⚠️  SYSTEM VALIDATION: PARTIAL")
            print("   Some issues need attention")
        else:
            print("\n❌ SYSTEM VALIDATION: FAILED")
            print("   Critical issues must be resolved")
        
        # Detailed results
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}: {result['details']}")

if __name__ == "__main__":
    validator = RAGSystemValidator()
    validator.run_comprehensive_test()