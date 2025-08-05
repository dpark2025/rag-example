#!/usr/bin/env python3
"""
Document Management Testing Script
Tests CRUD operations, bulk operations, and filtering
"""

import requests
import json
import time
import tempfile
import os

class DocumentManagementTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: str, duration: float = 0):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.3f}s)")
        if not success or details:
            print(f"   {details}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "duration": duration
        })
    
    def test_bulk_upload(self):
        """Test bulk file upload"""
        try:
            start_time = time.time()
            
            # Create multiple test files
            test_files = [
                ("doc1.txt", "This is document 1 for bulk upload testing. Contains financial data."),
                ("doc2.txt", "This is document 2 for bulk upload testing. Contains technical specifications."),
                ("doc3.txt", "This is document 3 for bulk upload testing. Contains meeting notes.")
            ]
            
            files = []
            temp_files = []
            
            for filename, content in test_files:
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                temp_file.write(content)
                temp_file.close()
                temp_files.append(temp_file.name)
                files.append(('files', (filename, open(temp_file.name, 'rb'), 'text/plain')))
            
            response = requests.post(f"{self.base_url}/api/v1/documents/bulk-upload", files=files, timeout=30)
            duration = time.time() - start_time
            
            # Cleanup
            for f in files:
                f[1][1].close()
            for temp_file in temp_files:
                os.unlink(temp_file)
            
            if response.status_code == 200:
                data = response.json()
                success_count = data.get("successful_uploads", 0)
                self.log_result("Bulk Upload", success_count >= 3, 
                              f"Uploaded {success_count}/3 files", duration)
                return success_count >= 3
            else:
                self.log_result("Bulk Upload", False, 
                              f"HTTP {response.status_code}: {response.text}", duration)
                return False
                
        except Exception as e:
            self.log_result("Bulk Upload", False, f"Error: {e}", 0)
            return False
    
    def test_document_filtering(self):
        """Test document filtering capabilities"""
        try:
            start_time = time.time()
            
            # Test filtering by file type
            response = requests.get(f"{self.base_url}/api/v1/documents?file_type=txt&limit=10", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get("documents", [])
                
                # Check that all returned documents are txt files
                all_txt = all(doc.get("file_type") == "txt" for doc in documents)
                
                duration = time.time() - start_time
                self.log_result("Document Filtering", all_txt and len(documents) > 0, 
                              f"Found {len(documents)} txt files, all correct type: {all_txt}", duration)
                return all_txt and len(documents) > 0
            else:
                duration = time.time() - start_time
                self.log_result("Document Filtering", False, 
                              f"HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("Document Filtering", False, f"Error: {e}", 0)
            return False
    
    def test_document_deletion(self):
        """Test single document deletion"""
        try:
            start_time = time.time()
            
            # First, get a document to delete
            response = requests.get(f"{self.base_url}/api/v1/documents?limit=1", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Document Deletion", False, "Cannot get documents list", 0)
                return False
            
            data = response.json()
            documents = data.get("documents", [])
            
            if not documents:
                self.log_result("Document Deletion", False, "No documents to delete", 0)
                return False
            
            doc_id = documents[0]["doc_id"]
            
            # Delete the document
            delete_response = requests.delete(f"{self.base_url}/api/v1/documents/{doc_id}", timeout=10)
            duration = time.time() - start_time
            
            if delete_response.status_code == 200:
                delete_data = delete_response.json()
                chunks_deleted = delete_data.get("deleted_chunks", 0)
                
                self.log_result("Document Deletion", chunks_deleted > 0, 
                              f"Deleted doc {doc_id}, {chunks_deleted} chunks removed", duration)
                return chunks_deleted > 0
            else:
                self.log_result("Document Deletion", False, 
                              f"HTTP {delete_response.status_code}: {delete_response.text}", duration)
                return False
                
        except Exception as e:
            self.log_result("Document Deletion", False, f"Error: {e}", 0)
            return False
    
    def test_bulk_deletion(self):
        """Test bulk document deletion"""
        try:
            start_time = time.time()
            
            # Get multiple documents to delete
            response = requests.get(f"{self.base_url}/api/v1/documents?limit=3", timeout=10)
            
            if response.status_code != 200:
                self.log_result("Bulk Deletion", False, "Cannot get documents list", 0)
                return False
            
            data = response.json()
            documents = data.get("documents", [])
            
            if len(documents) < 2:
                self.log_result("Bulk Deletion", False, "Need at least 2 documents for bulk delete", 0)
                return False
            
            doc_ids = [doc["doc_id"] for doc in documents[:2]]
            
            # Bulk delete
            bulk_delete_payload = {"doc_ids": doc_ids}
            delete_response = requests.delete(f"{self.base_url}/api/v1/documents/bulk", 
                                            json=bulk_delete_payload, timeout=10)
            duration = time.time() - start_time
            
            if delete_response.status_code == 200:
                delete_data = delete_response.json()
                success_count = delete_data.get("success_count", 0)
                total_chunks = delete_data.get("total_chunks_deleted", 0)
                
                self.log_result("Bulk Deletion", success_count >= 2, 
                              f"Deleted {success_count} docs, {total_chunks} chunks", duration)
                return success_count >= 2
            else:
                self.log_result("Bulk Deletion", False, 
                              f"HTTP {delete_response.status_code}: {delete_response.text}", duration)
                return False
                
        except Exception as e:
            self.log_result("Bulk Deletion", False, f"Error: {e}", 0)
            return False
    
    def test_storage_stats(self):
        """Test storage statistics endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/v1/documents/stats", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ["total_documents", "total_chunks", "total_size_bytes"]
                has_all_fields = all(field in data for field in required_fields)
                
                if has_all_fields:
                    stats_summary = f"Docs: {data['total_documents']}, Chunks: {data['total_chunks']}, Size: {data['total_size_bytes']} bytes"
                    self.log_result("Storage Stats", True, stats_summary, duration)
                    return True
                else:
                    self.log_result("Storage Stats", False, 
                                  f"Missing fields in response: {required_fields}", duration)
                    return False
            else:
                self.log_result("Storage Stats", False, 
                              f"HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("Storage Stats", False, f"Error: {e}", 0)
            return False
    
    def test_pagination(self):
        """Test document listing pagination"""
        try:
            start_time = time.time()
            
            # Get first page
            response1 = requests.get(f"{self.base_url}/api/v1/documents?limit=5&offset=0", timeout=10)
            
            # Get second page
            response2 = requests.get(f"{self.base_url}/api/v1/documents?limit=5&offset=5", timeout=10)
            
            duration = time.time() - start_time
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                docs1 = data1.get("documents", [])
                docs2 = data2.get("documents", [])
                
                # Check that we got different documents
                ids1 = set(doc["doc_id"] for doc in docs1)
                ids2 = set(doc["doc_id"] for doc in docs2)
                
                no_overlap = len(ids1.intersection(ids2)) == 0
                
                self.log_result("Pagination", no_overlap and len(docs1) > 0, 
                              f"Page 1: {len(docs1)} docs, Page 2: {len(docs2)} docs, No overlap: {no_overlap}", 
                              duration)
                return no_overlap and len(docs1) > 0
            else:
                self.log_result("Pagination", False, 
                              f"HTTP errors: {response1.status_code}, {response2.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("Pagination", False, f"Error: {e}", 0)
            return False
    
    def run_all_tests(self):
        """Run all document management tests"""
        print("🗂️  Starting Document Management Testing\n")
        
        # Run tests
        self.test_bulk_upload()
        self.test_document_filtering()
        self.test_storage_stats()
        self.test_pagination()
        self.test_document_deletion()
        self.test_bulk_deletion()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print("📊 DOCUMENT MANAGEMENT TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.results if result["success"])
        total = len(self.results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            print("\n🎉 DOCUMENT MANAGEMENT: EXCELLENT")
        elif pass_rate >= 75:
            print("\n✅ DOCUMENT MANAGEMENT: GOOD")
        elif pass_rate >= 60:
            print("\n⚠️  DOCUMENT MANAGEMENT: NEEDS IMPROVEMENT")
        else:
            print("\n❌ DOCUMENT MANAGEMENT: CRITICAL ISSUES")

if __name__ == "__main__":
    tester = DocumentManagementTester()
    tester.run_all_tests()