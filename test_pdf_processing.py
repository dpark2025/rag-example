#!/usr/bin/env python3
"""
PDF Processing Validation Script
Tests PDF upload, text extraction, and intelligence features
"""

import requests
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import tempfile
import os

class PDFProcessingTester:
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
    
    def create_test_pdf(self, content: str, filename: str) -> str:
        """Create a test PDF file with given content"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w+b', suffix='.pdf', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Create PDF content
            c = canvas.Canvas(temp_path, pagesize=letter)
            width, height = letter
            
            # Add title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "PDF Test Document")
            
            # Add content
            c.setFont("Helvetica", 12)
            lines = content.split('\n')
            y_position = height - 100
            
            for line in lines:
                if y_position < 50:  # Start new page if needed
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y_position = height - 50
                
                c.drawString(50, y_position, line.strip())
                y_position -= 15
            
            c.save()
            return temp_path
            
        except Exception as e:
            print(f"Error creating PDF: {e}")
            return None
    
    def test_pdf_upload_and_extraction(self):
        """Test PDF upload and text extraction"""
        try:
            start_time = time.time()
            
            # Create test PDF
            pdf_content = """
            PDF Processing Test Document
            
            This is a test PDF document for validating the RAG system's PDF processing capabilities.
            
            Key Features to Test:
            - Text extraction from PDF files
            - Document intelligence analysis
            - Chunking and embedding generation
            - Quality score assessment
            
            Performance Metrics:
            - Extraction accuracy: High quality text extraction
            - Processing speed: Under 30 seconds
            - Memory efficiency: Optimized resource usage
            
            Quality Assurance:
            This PDF contains structured content that should be extractable
            and processable by the RAG system's PDF processing pipeline.
            """
            
            pdf_path = self.create_test_pdf(pdf_content, "test_pdf_processing.pdf")
            
            if not pdf_path:
                self.log_result("PDF Upload & Extraction", False, "Could not create test PDF", 0)
                return False
            
            try:
                # Upload PDF
                with open(pdf_path, 'rb') as f:
                    files = {'file': ('test_pdf.pdf', f, 'application/pdf')}
                    response = requests.post(f"{self.base_url}/api/v1/documents/upload", 
                                           files=files, timeout=60)
                
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    task_id = data.get("task_id")
                    
                    if success:
                        # Wait for processing and check status
                        time.sleep(3)
                        status_response = requests.get(f"{self.base_url}/api/v1/documents/{task_id}/status", 
                                                     timeout=10)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            processing_status = status_data.get("status")
                            
                            self.log_result("PDF Upload & Extraction", 
                                          processing_status == "ready", 
                                          f"PDF processed, status: {processing_status}", 
                                          duration)
                            return processing_status == "ready"
                        else:
                            self.log_result("PDF Upload & Extraction", False, 
                                          "Could not check processing status", duration)
                            return False
                    else:
                        error_msg = data.get("message", "Unknown error")
                        self.log_result("PDF Upload & Extraction", False, 
                                      f"Upload failed: {error_msg}", duration)
                        return False
                else:
                    self.log_result("PDF Upload & Extraction", False, 
                                  f"HTTP {response.status_code}: {response.text}", duration)
                    return False
                    
            finally:
                # Cleanup
                os.unlink(pdf_path)
                
        except Exception as e:
            self.log_result("PDF Upload & Extraction", False, f"Error: {e}", 0)
            return False
    
    def test_pdf_intelligence_analysis(self):
        """Test document intelligence features for PDFs"""
        try:
            start_time = time.time()
            
            # Get recent documents to find a PDF
            response = requests.get(f"{self.base_url}/api/v1/documents?file_type=pdf&limit=1", timeout=10)
            
            if response.status_code != 200:
                self.log_result("PDF Intelligence Analysis", False, 
                              "Cannot retrieve PDF documents", time.time() - start_time)
                return False
            
            data = response.json()
            documents = data.get("documents", [])
            
            if not documents:
                self.log_result("PDF Intelligence Analysis", False, 
                              "No PDF documents found for analysis", time.time() - start_time)
                return False
            
            pdf_doc = documents[0]
            doc_id = pdf_doc["doc_id"]
            
            # Check document status for intelligence data
            status_response = requests.get(f"{self.base_url}/api/v1/documents/{doc_id}/status", timeout=10)
            duration = time.time() - start_time
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                # PDF intelligence features should be available
                has_intelligence = any(key in str(status_data) for key in 
                                     ["intelligence", "document_type", "quality_score"])
                
                self.log_result("PDF Intelligence Analysis", has_intelligence, 
                              f"Intelligence data available: {has_intelligence}", duration)
                return has_intelligence
            else:
                self.log_result("PDF Intelligence Analysis", False, 
                              f"HTTP {status_response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("PDF Intelligence Analysis", False, f"Error: {e}", 0)
            return False
    
    def test_pdf_chunking_quality(self):
        """Test PDF chunking and processing quality"""
        try:
            start_time = time.time()
            
            # Create a multi-page PDF with structured content
            structured_content = """
            Chapter 1: Introduction
            This chapter introduces the main concepts and provides background information.
            
            Chapter 2: Technical Specifications
            Here we detail the technical requirements and system architecture.
            Key points include:
            - Scalability requirements
            - Performance benchmarks
            - Security considerations
            
            Chapter 3: Implementation
            This section covers the actual implementation details and best practices.
            """
            
            pdf_path = self.create_test_pdf(structured_content, "structured_test.pdf")
            
            if not pdf_path:
                self.log_result("PDF Chunking Quality", False, "Could not create structured PDF", 0)
                return False
            
            try:
                # Upload structured PDF
                with open(pdf_path, 'rb') as f:
                    files = {'file': ('structured_test.pdf', f, 'application/pdf')}
                    response = requests.post(f"{self.base_url}/api/v1/documents/upload", 
                                           files=files, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    task_id = data.get("task_id")
                    
                    # Wait for processing
                    time.sleep(3)
                    
                    # Check final document in listing
                    docs_response = requests.get(f"{self.base_url}/api/v1/documents?limit=1", timeout=10)
                    
                    if docs_response.status_code == 200:
                        docs_data = docs_response.json()
                        documents = docs_data.get("documents", [])
                        
                        if documents:
                            doc = documents[0]
                            chunk_count = doc.get("chunk_count", 0)
                            
                            duration = time.time() - start_time
                            
                            # Good chunking should create multiple chunks for structured content
                            quality_chunking = chunk_count >= 3
                            
                            self.log_result("PDF Chunking Quality", quality_chunking, 
                                          f"Generated {chunk_count} chunks from structured PDF", 
                                          duration)
                            return quality_chunking
                        else:
                            duration = time.time() - start_time
                            self.log_result("PDF Chunking Quality", False, 
                                          "Document not found after processing", duration)
                            return False
                    else:
                        duration = time.time() - start_time
                        self.log_result("PDF Chunking Quality", False, 
                                      "Could not retrieve processed document", duration)
                        return False
                else:
                    duration = time.time() - start_time
                    self.log_result("PDF Chunking Quality", False, 
                                  f"Upload failed: HTTP {response.status_code}", duration)
                    return False
                    
            finally:
                os.unlink(pdf_path)
                
        except Exception as e:
            self.log_result("PDF Chunking Quality", False, f"Error: {e}", 0)
            return False
    
    def test_pdf_processing_performance(self):
        """Test PDF processing performance"""
        try:
            start_time = time.time()
            
            # Create a larger PDF for performance testing
            large_content = """
            Performance Testing Document
            
            This is a larger PDF document designed to test processing performance.
            """ + "\n\n".join([f"Section {i}: This is content for section {i} with detailed information about various topics and technical specifications that need to be processed efficiently." for i in range(1, 21)])
            
            pdf_path = self.create_test_pdf(large_content, "performance_test.pdf")
            
            if not pdf_path:
                self.log_result("PDF Processing Performance", False, "Could not create performance test PDF", 0)
                return False
            
            try:
                processing_start = time.time()
                
                # Upload large PDF
                with open(pdf_path, 'rb') as f:
                    files = {'file': ('performance_test.pdf', f, 'application/pdf')}
                    response = requests.post(f"{self.base_url}/api/v1/documents/upload", 
                                           files=files, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    task_id = data.get("task_id")
                    
                    # Monitor processing time
                    max_wait = 30  # 30 second target
                    processing_complete = False
                    
                    while time.time() - processing_start < max_wait:
                        time.sleep(1)
                        status_response = requests.get(f"{self.base_url}/api/v1/documents/{task_id}/status", 
                                                     timeout=5)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get("status") == "ready":
                                processing_complete = True
                                break
                    
                    processing_time = time.time() - processing_start
                    duration = time.time() - start_time
                    
                    # Performance target: < 30 seconds
                    meets_performance = processing_complete and processing_time < 30
                    
                    self.log_result("PDF Processing Performance", meets_performance, 
                                  f"Processing time: {processing_time:.2f}s (target: <30s), Complete: {processing_complete}", 
                                  duration)
                    return meets_performance
                else:
                    duration = time.time() - start_time
                    self.log_result("PDF Processing Performance", False, 
                                  f"Upload failed: HTTP {response.status_code}", duration)
                    return False
                    
            finally:
                os.unlink(pdf_path)
                
        except Exception as e:
            self.log_result("PDF Processing Performance", False, f"Error: {e}", 0)
            return False
    
    def run_all_tests(self):
        """Run all PDF processing tests"""
        print("📄 Starting PDF Processing Validation\n")
        
        # Check if reportlab is available
        try:
            import reportlab
        except ImportError:
            print("❌ ReportLab not available. Installing...")
            import subprocess
            subprocess.check_call(["pip", "install", "reportlab"])
            print("✅ ReportLab installed")
        
        # Run tests
        self.test_pdf_upload_and_extraction()
        self.test_pdf_processing_performance()
        self.test_pdf_chunking_quality()
        # Note: Intelligence analysis test may need actual PDFs to be meaningful
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print("📊 PDF PROCESSING TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.results if result["success"])
        total = len(self.results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            print("\n🎉 PDF PROCESSING: EXCELLENT")
        elif pass_rate >= 75:
            print("\n✅ PDF PROCESSING: GOOD")
        elif pass_rate >= 60:
            print("\n⚠️  PDF PROCESSING: NEEDS IMPROVEMENT")
        else:
            print("\n❌ PDF PROCESSING: CRITICAL ISSUES")

if __name__ == "__main__":
    tester = PDFProcessingTester()
    tester.run_all_tests()