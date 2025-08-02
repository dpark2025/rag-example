#!/usr/bin/env python3
"""
System integration tests for the Local RAG System
Tests API endpoints, document processing, and query functionality
"""

import requests
import json
import time
import sys
from typing import Dict, List

class RAGSystemTester:
    def __init__(self, base_url="http://localhost:8501", api_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_url = api_url
    
    def test_health_check(self) -> bool:
        """Test system health endpoints"""
        print("🏥 Testing health checks...")
        
        try:
            # Test Streamlit health
            response = requests.get(f"{self.base_url}/_stcore/health", timeout=10)
            streamlit_healthy = response.status_code == 200
            print(f"  Streamlit: {'✅' if streamlit_healthy else '❌'}")
            
            # Test Ollama health
            response = requests.get("http://localhost:11434/api/tags", timeout=10)
            ollama_healthy = response.status_code == 200
            print(f"  Ollama: {'✅' if ollama_healthy else '❌'}")
            
            return streamlit_healthy and ollama_healthy
            
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
                "content": "Docker containers provide a way to package applications with their dependencies. This ensures consistency across different environments.",
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
                result = response.json()
                print(f"  ✅ Uploaded {result.get('count', 0)} documents")
                return True
            else:
                print(f"  ❌ Upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"  ❌ Upload failed: {e}")
            return False
    
    def test_document_count(self) -> bool:
        """Test document count endpoint"""
        print("📊 Testing document count...")
        
        try:
            response = requests.get(f"{self.api_url}/documents/count", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                count = result.get('total_chunks', 0)
                print(f"  ✅ Found {count} document chunks")
                return count > 0
            else:
                print(f"  ❌ Count check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Count check failed: {e}")
            return False
    
    def test_query_functionality(self) -> bool:
        """Test RAG query functionality"""
        print("🔍 Testing query functionality...")
        
        test_queries = [
            "What is artificial intelligence?",
            "How do Docker containers work?",
            "What are the benefits of machine learning?"
        ]
        
        success_count = 0
        
        for query in test_queries:
            try:
                response = requests.post(
                    f"{self.api_url}/query",
                    json={"question": query, "max_chunks": 3},
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get('answer', '')
                    sources = result.get('sources', [])
                    
                    if answer and len(answer) > 50:  # Reasonable answer length
                        print(f"  ✅ Query: '{query[:30]}...' - Got answer ({len(sources)} sources)")
                        success_count += 1
                    else:
                        print(f"  ⚠️ Query: '{query[:30]}...' - Short answer")
                else:
                    print(f"  ❌ Query failed: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Query '{query[:30]}...' failed: {e}")
        
        success_rate = success_count / len(test_queries)
        print(f"  📈 Query success rate: {success_rate:.1%}")
        return success_rate >= 0.5  # At least 50% success rate
    
    def test_settings_management(self) -> bool:
        """Test settings get/update functionality"""
        print("⚙️ Testing settings management...")
        
        try:
            # Get current settings
            response = requests.get(f"{self.api_url}/settings", timeout=10)
            if response.status_code != 200:
                print(f"  ❌ Failed to get settings: {response.status_code}")
                return False
            
            original_settings = response.json()
            print(f"  📋 Current settings: threshold={original_settings.get('similarity_threshold', 'N/A')}")
            
            # Update settings
            new_threshold = 0.8
            response = requests.post(
                f"{self.api_url}/settings",
                json={"similarity_threshold": new_threshold},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"  ✅ Updated similarity threshold to {new_threshold}")
            else:
                print(f"  ❌ Failed to update settings: {response.status_code}")
                return False
            
            # Verify update
            response = requests.get(f"{self.api_url}/settings", timeout=10)
            if response.status_code == 200:
                updated_settings = response.json()
                if abs(updated_settings.get('similarity_threshold', 0) - new_threshold) < 0.01:
                    print(f"  ✅ Settings update verified")
                    return True
                else:
                    print(f"  ❌ Settings not updated correctly")
                    return False
            
        except Exception as e:
            print(f"  ❌ Settings test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all system tests"""
        print("🧪 Starting RAG System Integration Tests\n")
        
        tests = {
            "Health Check": self.test_health_check,
            "Document Upload": self.test_document_upload,
            "Document Count": self.test_document_count,
            "Query Functionality": self.test_query_functionality,
            "Settings Management": self.test_settings_management
        }
        
        results = {}
        
        for test_name, test_func in tests.items():
            print(f"\n{'-'*50}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test results summary"""
        print(f"\n{'='*50}")
        print("🧪 TEST RESULTS SUMMARY")
        print(f"{'='*50}")
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name:.<30} {status}")
        
        print(f"\n📊 Overall: {passed}/{total} tests passed ({passed/total:.1%})")
        
        if passed == total:
            print("🎉 All tests passed! System is ready to use.")
            return 0
        else:
            print("⚠️ Some tests failed. Check the logs above.")
            return 1

def main():
    """Main test runner"""
    tester = RAGSystemTester()
    
    # Wait for system to be ready
    print("⏳ Waiting for system to be ready...")
    time.sleep(5)
    
    results = tester.run_all_tests()
    exit_code = tester.print_summary(results)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()