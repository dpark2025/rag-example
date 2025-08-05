#!/usr/bin/env python3
"""
Test script for Document Versioning System

Tests comprehensive document version control including:
- Version creation and retrieval
- Document diff and comparison
- Rollback operations with safety checks  
- Conflict detection and resolution
- Version cleanup and maintenance

Run this script to validate the versioning system implementation.
"""

import asyncio
import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

class VersioningTestSuite:
    """Comprehensive test suite for document versioning system."""
    
    def __init__(self):
        self.session = requests.Session()
        self.test_doc_id = None
        self.version_ids = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def check_service_health(self) -> bool:
        """Check if the RAG service is running."""
        try:
            response = self.session.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                self.log("✅ RAG service is healthy")
                return True
            else:
                self.log(f"❌ RAG service returned status {response.status_code}", "ERROR")
                return False
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Cannot connect to RAG service: {e}", "ERROR")
            return False
    
    def create_test_document(self) -> Optional[str]:
        """Create a test document for versioning tests."""
        try:
            # Upload a test document
            test_content = """# Test Document for Versioning

This is a test document created for testing the document versioning system. 
It contains multiple sections and will be modified to test version tracking.

## Section 1: Introduction
This section introduces the document and explains its purpose.

## Section 2: Content
This section contains the main content that will be modified during testing.

## Section 3: Conclusion
This section provides conclusions and next steps.
"""
            
            files = {
                'files': ('test_versioning.txt', test_content, 'text/plain')
            }
            
            response = self.session.post(f"{API_V1}/documents/upload", files=files)
            
            if response.status_code == 200:
                data = response.json()
                # Extract doc_id from processing tasks
                if data.get('processing_tasks'):
                    self.test_doc_id = data['processing_tasks'][0]
                    self.log(f"✅ Created test document with ID: {self.test_doc_id}")
                    return self.test_doc_id
                else:
                    self.log("❌ No processing tasks returned from document upload", "ERROR")
                    return None
            else:
                self.log(f"❌ Failed to create test document: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Error creating test document: {e}", "ERROR")
            return None
    
    def wait_for_document_processing(self, doc_id: str, timeout: int = 30) -> bool:
        """Wait for document processing to complete."""
        import time
        
        self.log(f"⏳ Waiting for document {doc_id} to be processed...")
        
        for _ in range(timeout):
            try:
                response = self.session.get(f"{API_V1}/documents/{doc_id}/status")
                if response.status_code == 200:
                    status_data = response.json()
                    if status_data.get('status') == 'ready':
                        self.log(f"✅ Document {doc_id} processing completed")
                        return True
                    elif status_data.get('status') in ['failed', 'error']:
                        self.log(f"❌ Document processing failed: {status_data.get('error_message', 'Unknown error')}", "ERROR")
                        return False
                
                time.sleep(1)
                
            except Exception as e:
                self.log(f"⚠️ Error checking document status: {e}", "WARN")
                time.sleep(1)
        
        self.log(f"❌ Document processing timed out after {timeout} seconds", "ERROR")
        return False
    
    def test_version_creation(self) -> bool:
        """Test creating document versions."""
        self.log("🧪 Testing version creation...")
        
        try:
            # Create Version 1 - Initial content
            version1_content = """# Test Document for Versioning - Version 1

This is the first version of our test document.

## Section 1: Introduction
This section introduces the document and explains its purpose in version 1.

## Section 2: Content  
This section contains the main content. Initial version content goes here.

## Section 3: Conclusion
This section provides conclusions for version 1.
"""
            
            version1_data = {
                "content": version1_content,
                "author": "test_user",
                "change_summary": "Initial version creation"
            }
            
            response = self.session.post(
                f"{API_V1}/documents/{self.test_doc_id}/versions",
                json=version1_data
            )
            
            if response.status_code == 200:
                version1 = response.json()
                self.version_ids.append(version1['version_id'])
                self.log(f"✅ Created version 1: {version1['version_id']}")
            else:
                self.log(f"❌ Failed to create version 1: {response.status_code} - {response.text}", "ERROR")
                return False
            
            # Create Version 2 - Modified content
            version2_content = """# Test Document for Versioning - Version 2

This is the second version with significant changes.

## Section 1: Introduction
This section introduces the document and explains its purpose in version 2.
We've added more details and context here.

## Section 2: Content
This section contains the main content. Version 2 has enhanced content with additional details.
We've also added new subsections and expanded explanations.

### Section 2.1: New Subsection
This is a new subsection added in version 2.

## Section 3: Conclusion
This section provides updated conclusions for version 2 with new insights.

## Section 4: Appendix
This is a completely new section added in version 2.
"""
            
            version2_data = {
                "content": version2_content,
                "author": "test_user",
                "change_summary": "Added new sections and enhanced content",
                "parent_version_id": version1['version_id']
            }
            
            response = self.session.post(
                f"{API_V1}/documents/{self.test_doc_id}/versions",
                json=version2_data
            )
            
            if response.status_code == 200:
                version2 = response.json()
                self.version_ids.append(version2['version_id'])
                self.log(f"✅ Created version 2: {version2['version_id']}")
                return True
            else:
                self.log(f"❌ Failed to create version 2: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in version creation test: {e}", "ERROR")
            return False
    
    def test_version_history(self) -> bool:
        """Test retrieving version history."""
        self.log("🧪 Testing version history retrieval...")
        
        try:
            response = self.session.get(f"{API_V1}/documents/{self.test_doc_id}/versions")
            
            if response.status_code == 200:
                history = response.json()
                versions = history.get('versions', [])
                
                self.log(f"✅ Retrieved {len(versions)} versions")
                
                # Validate version data
                for version in versions:
                    self.log(f"  📋 Version {version['version_number']}: {version['change_summary']}")
                    self.log(f"     Author: {version['author']}, Changes: +{version['lines_added']} -{version['lines_removed']}")
                
                return len(versions) >= 2
            else:
                self.log(f"❌ Failed to get version history: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in version history test: {e}", "ERROR")
            return False
    
    def test_version_comparison(self) -> bool:
        """Test version comparison and diff functionality."""
        self.log("🧪 Testing version comparison...")
        
        if len(self.version_ids) < 2:
            self.log("❌ Need at least 2 versions for comparison test", "ERROR")
            return False
        
        try:
            from_version = self.version_ids[0]
            to_version = self.version_ids[1]
            
            response = self.session.get(f"{API_V1}/versions/{from_version}/compare/{to_version}")
            
            if response.status_code == 200:
                diff = response.json()
                
                self.log(f"✅ Version comparison completed")
                self.log(f"  📊 Similarity: {diff['similarity_score']:.2f}")
                self.log(f"  📈 Changes: +{diff['lines_added']} -{diff['lines_removed']} ~{diff['lines_modified']}")
                self.log(f"  📋 Total changes: {diff['total_changes']}")
                
                if diff.get('structural_changes'):
                    self.log(f"  🔄 Structural changes: {', '.join(diff['structural_changes'])}")
                
                return True
            else:
                self.log(f"❌ Failed to compare versions: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in version comparison test: {e}", "ERROR")
            return False
    
    def test_rollback_safety_check(self) -> bool:
        """Test rollback safety validation."""
        self.log("🧪 Testing rollback safety check...")
        
        if len(self.version_ids) < 2:
            self.log("❌ Need at least 2 versions for rollback test", "ERROR")
            return False
        
        try:
            target_version = self.version_ids[0]  # Rollback to first version
            
            response = self.session.get(
                f"{API_V1}/documents/{self.test_doc_id}/rollback/{target_version}/safety-check"
            )
            
            if response.status_code == 200:
                safety = response.json()
                
                self.log(f"✅ Rollback safety check completed")
                self.log(f"  🛡️ Is safe: {safety['is_safe']}")
                self.log(f"  ⚠️ Risk level: {safety['risk_level']}")
                
                if safety.get('warnings'):
                    for warning in safety['warnings']:
                        self.log(f"  ⚠️ Warning: {warning}")
                
                if safety.get('blocking_issues'):
                    for issue in safety['blocking_issues']:
                        self.log(f"  🚫 Blocking issue: {issue}")
                
                return True
            else:
                self.log(f"❌ Failed to check rollback safety: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in rollback safety test: {e}", "ERROR")
            return False
    
    def test_rollback_operation(self) -> bool:
        """Test document rollback functionality."""
        self.log("🧪 Testing rollback operation...")
        
        if len(self.version_ids) < 2:
            self.log("❌ Need at least 2 versions for rollback test", "ERROR")
            return False
        
        try:
            target_version = self.version_ids[0]  # Rollback to first version
            
            rollback_data = {
                "target_version_id": target_version,
                "author": "test_user",
                "force": False
            }
            
            response = self.session.post(
                f"{API_V1}/documents/{self.test_doc_id}/rollback",
                json=rollback_data
            )
            
            if response.status_code == 200:
                rollback_result = response.json()
                
                self.log(f"✅ Rollback operation completed")
                self.log(f"  ✅ Success: {rollback_result['success']}")
                
                if rollback_result.get('warnings'):
                    for warning in rollback_result['warnings']:
                        self.log(f"  ⚠️ Warning: {warning}")
                
                if rollback_result.get('new_version'):
                    new_version = rollback_result['new_version']
                    self.version_ids.append(new_version['version_id'])
                    self.log(f"  📋 New rollback version: {new_version['version_id']}")
                
                return rollback_result['success']
            else:
                self.log(f"❌ Failed to rollback document: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in rollback test: {e}", "ERROR")
            return False
    
    def test_current_version(self) -> bool:
        """Test getting current document version."""
        self.log("🧪 Testing current version retrieval...")
        
        try:
            response = self.session.get(f"{API_V1}/documents/{self.test_doc_id}/versions/current")
            
            if response.status_code == 200:
                current = response.json()
                
                self.log(f"✅ Retrieved current version")
                self.log(f"  📋 Version: {current['version_number']}")
                self.log(f"  👤 Author: {current['author']}")
                self.log(f"  📝 Summary: {current['change_summary']}")
                self.log(f"  🏷️ Operation: {current['operation']}")
                
                return True
            else:
                self.log(f"❌ Failed to get current version: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in current version test: {e}", "ERROR")
            return False
    
    def test_version_content_retrieval(self) -> bool:
        """Test retrieving version content."""
        self.log("🧪 Testing version content retrieval...")
        
        if not self.version_ids:
            self.log("❌ No versions available for content test", "ERROR")
            return False
        
        try:
            version_id = self.version_ids[0]
            response = self.session.get(f"{API_V1}/versions/{version_id}/content")
            
            if response.status_code == 200:
                content_data = response.json()
                
                self.log(f"✅ Retrieved version content")
                self.log(f"  📄 Content size: {content_data['file_size']} bytes")
                self.log(f"  🔒 Content hash: {content_data['content_hash'][:16]}...")
                
                return True
            else:
                self.log(f"❌ Failed to get version content: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in version content test: {e}", "ERROR")
            return False
    
    def test_conflict_detection(self) -> bool:
        """Test version conflict detection."""
        self.log("🧪 Testing conflict detection...")
        
        if not self.version_ids:
            self.log("❌ No versions available for conflict test", "ERROR")
            return False
        
        try:
            base_version = self.version_ids[0]
            
            # Simulate conflicting content
            conflicting_content = """# Test Document - Conflicting Changes

This content has conflicting changes that overlap with recent modifications.

## Section 1: Modified Introduction
This section has been changed differently than recent versions.

## Section 2: Conflicting Content
This section contains changes that conflict with the current version.
"""
            
            params = {
                "new_content": conflicting_content,
                "base_version_id": base_version
            }
            
            response = self.session.post(
                f"{API_V1}/documents/{self.test_doc_id}/detect-conflicts",
                params=params
            )
            
            if response.status_code == 200:
                conflict_data = response.json()
                
                self.log(f"✅ Conflict detection completed")
                self.log(f"  🔍 Has conflicts: {conflict_data.get('has_conflicts', False)}")
                
                if conflict_data.get('has_conflicts'):
                    conflict = conflict_data.get('conflict', {})
                    self.log(f"  ⚠️ Conflict type: {conflict.get('conflict_type')}")
                    self.log(f"  📍 Conflict areas: {len(conflict.get('conflict_areas', []))}")
                else:
                    self.log(f"  ✅ No conflicts detected")
                
                return True
            else:
                self.log(f"❌ Failed to detect conflicts: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in conflict detection test: {e}", "ERROR")
            return False
    
    def cleanup_test_document(self) -> bool:
        """Clean up test document."""
        self.log("🧹 Cleaning up test document...")
        
        if not self.test_doc_id:
            return True
        
        try:
            response = self.session.delete(f"{API_V1}/documents/{self.test_doc_id}")
            
            if response.status_code == 200:
                self.log(f"✅ Test document cleaned up")
                return True
            else:
                self.log(f"⚠️ Failed to clean up test document: {response.status_code}", "WARN")
                return False
                
        except Exception as e:
            self.log(f"⚠️ Error cleaning up test document: {e}", "WARN")
            return False
    
    def run_all_tests(self) -> bool:
        """Run the complete test suite."""
        self.log("🚀 Starting Document Versioning Test Suite")
        
        # Check service health
        if not self.check_service_health():
            return False
        
        # Create test document
        if not self.create_test_document():
            return False
        
        # Wait for document processing
        if not self.wait_for_document_processing(self.test_doc_id):
            return False
        
        # Run all tests
        tests = [
            ("Version Creation", self.test_version_creation),
            ("Version History", self.test_version_history),
            ("Version Comparison", self.test_version_comparison),
            ("Current Version", self.test_current_version),
            ("Version Content", self.test_version_content_retrieval),
            ("Rollback Safety Check", self.test_rollback_safety_check),
            ("Rollback Operation", self.test_rollback_operation),
            ("Conflict Detection", self.test_conflict_detection)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n--- Running {test_name} Test ---")
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} test PASSED")
                else:
                    failed += 1
                    self.log(f"❌ {test_name} test FAILED", "ERROR")
            except Exception as e:
                failed += 1
                self.log(f"❌ {test_name} test ERROR: {e}", "ERROR")
        
        # Cleanup
        self.cleanup_test_document()
        
        # Summary
        self.log(f"\n📊 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            self.log("🎉 All tests passed! Document versioning system is working correctly.")
            return True
        else:
            self.log(f"❌ {failed} tests failed. Please check the implementation.", "ERROR")
            return False

def main():
    """Main test runner."""
    test_suite = VersioningTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()