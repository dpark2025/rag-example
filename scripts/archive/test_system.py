#!/usr/bin/env python3
"""
System integration tests for the Local RAG System with Reflex UI
Tests API endpoints, document processing, and query functionality
"""

import requests
import json
import time
import sys
from typing import Dict, List

class RAGSystemTester:
    def __init__(self, ui_url="http://localhost:3000", api_url="http://localhost:8000"):
        self.ui_url = ui_url
        self.api_url = api_url
    
    def test_health_check(self) -> bool:
        """Test system health endpoints"""
        print("🏥 Testing health checks...")
        
        try:
            # Test FastAPI health
            response = requests.get(f"{self.api_url}/health", timeout=10)
            api_healthy = response.status_code == 200
            api_data = response.json() if api_healthy else {}
            print(f"  FastAPI Backend: {'✅' if api_healthy else '❌'}")
            
            # Check individual components from API health
            if api_healthy:
                llm_healthy = api_data.get("llm", {}).get("healthy", False)
                vector_db_healthy = api_data.get("vector_db", {}).get("healthy", False)
                embeddings_healthy = api_data.get("embeddings", {}).get("healthy", False)
                
                print(f"  - LLM (Ollama): {'✅' if llm_healthy else '❌'}")
                print(f"  - Vector DB: {'✅' if vector_db_healthy else '❌'}")
                print(f"  - Embeddings: {'✅' if embeddings_healthy else '❌'}")
            
            # Test Reflex UI (basic check)
            try:
                ui_response = requests.get(f"{self.ui_url}", timeout=10)
                ui_healthy = ui_response.status_code == 200
                print(f"  Reflex UI: {'✅' if ui_healthy else '❌'}")
            except:
                ui_healthy = False
                print(f"  Reflex UI: ❌ (not running)")
            
            # Test direct Ollama connection
            try:
                ollama_response = requests.get("http://localhost:11434/api/tags", timeout=10)
                ollama_direct = ollama_response.status_code == 200
                print(f"  Ollama Direct: {'✅' if ollama_direct else '❌'}")
            except:
                ollama_direct = False
                print(f"  Ollama Direct: ❌")
            
            return api_healthy and llm_healthy
            
        except Exception as e:
            print(f"  ❌ Health check failed: {e}")
            return False
    
    def test_document_upload(self) -> bool:
        """Test document upload functionality"""
        print("📄 Testing document upload...")
        
        test_documents = [
            {
                "title": "Test Document 1",
                "content": "This is a test document about artificial intelligence and machine learning. It covers various aspects of AI development.",
                "source": "test"
            },
            {
                "title": "Test Document 2",
                "content": "This document discusses natural language processing and its applications in modern software systems.",
                "source": "test"
            }
        ]
        
        try:
            response = requests.post(
                f"{self.api_url}/documents",
                json=test_documents,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"  ✅ Documents uploaded successfully")
                return True
            else:
                print(f"  ❌ Upload failed: {response.status_code}")
                print(f"     {response.text}")
                return False
                
        except Exception as e:
            print(f"  ❌ Document upload failed: {e}")
            return False
    
    def test_query_functionality(self) -> bool:
        """Test RAG query functionality"""
        print("🔍 Testing query functionality...")
        
        test_queries = [
            "What is artificial intelligence?",
            "Tell me about natural language processing",
            "How are AI and machine learning related?"
        ]
        
        success_count = 0
        
        for query in test_queries:
            try:
                print(f"\n  Testing query: '{query}'")
                
                response = requests.post(
                    f"{self.api_url}/query",
                    json={
                        "question": query,
                        "max_chunks": 3,
                        "similarity_threshold": 0.7
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check response structure
                    has_answer = "answer" in data
                    has_sources = "sources" in data
                    has_metrics = "metrics" in data
                    
                    if has_answer and data["answer"]:
                        print(f"    ✅ Got answer: {data['answer'][:100]}...")
                        if has_sources and data["sources"]:
                            print(f"    ✅ Sources provided: {len(data['sources'])} chunks")
                        if has_metrics:
                            print(f"    ✅ Metrics: {data['metrics']}")
                        success_count += 1
                    else:
                        print(f"    ❌ No answer received")
                else:
                    print(f"    ❌ Query failed: {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Query error: {e}")
        
        print(f"\n  Summary: {success_count}/{len(test_queries)} queries successful")
        return success_count == len(test_queries)
    
    def test_stats_endpoint(self) -> bool:
        """Test system statistics endpoint"""
        print("📊 Testing statistics endpoint...")
        
        try:
            response = requests.get(f"{self.api_url}/stats", timeout=10)
            
            if response.status_code == 200:
                stats = response.json()
                print(f"  ✅ Stats retrieved:")
                print(f"     Documents: {stats.get('total_documents', 0)}")
                print(f"     Chunks: {stats.get('total_chunks', 0)}")
                print(f"     Embeddings: {stats.get('embedding_model', 'unknown')}")
                return True
            else:
                print(f"  ❌ Stats failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Stats error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all system tests"""
        print("🚀 Starting RAG System Integration Tests")
        print("=" * 50)
        
        # Check if services are reachable
        print("\n🔌 Checking service connectivity...")
        print(f"  UI URL: {self.ui_url}")
        print(f"  API URL: {self.api_url}")
        
        results = {
            "health": self.test_health_check(),
            "upload": False,
            "query": False,
            "stats": False
        }
        
        # Only run other tests if health check passes
        if results["health"]:
            time.sleep(2)  # Give system time to stabilize
            results["upload"] = self.test_document_upload()
            
            if results["upload"]:
                time.sleep(2)  # Wait for documents to be processed
                results["query"] = self.test_query_functionality()
                results["stats"] = self.test_stats_endpoint()
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 Test Summary:")
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r)
        
        for test, passed in results.items():
            print(f"  {test.capitalize()}: {'✅ PASSED' if passed else '❌ FAILED'}")
        
        print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! The RAG system is working correctly.")
            return 0
        else:
            print("\n❌ Some tests failed. Please check the logs above.")
            return 1


if __name__ == "__main__":
    # Allow custom URLs via command line arguments
    ui_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    tester = RAGSystemTester(ui_url, api_url)
    sys.exit(tester.run_all_tests())