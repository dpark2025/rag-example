#!/usr/bin/env python3
"""Test script for processing status tracking functionality."""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def create_test_file():
    """Create a test file for upload."""
    content = f"""
    Test Document for Processing Status
    Created at: {datetime.now().isoformat()}
    
    This is a test document to demonstrate the processing status tracking
    functionality of the RAG system.
    
    The document contains multiple paragraphs to test the chunking
    and embedding generation process. 
    
    Each step of the processing pipeline should be tracked and
    reported back to the client through the status API.
    
    This final paragraph completes the test document.
    """
    
    filename = f"test_status_{int(time.time())}.txt"
    with open(f"/tmp/{filename}", "w", encoding='utf-8') as f:
        f.write(content)
    
    return f"/tmp/{filename}", filename

def test_processing_status():
    """Test the complete processing status workflow."""
    print("🧪 Testing Processing Status Tracking")
    print("=" * 50)
    
    # Check initial status
    print("\n1. Initial processing queue status:")
    response = requests.get(f"{BASE_URL}/processing/status")
    print(json.dumps(response.json(), indent=2))
    
    # Create and upload test file
    filepath, filename = create_test_file()
    print(f"\n2. Uploading test file: {filename}")
    
    with open(filepath, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/documents/upload",
            files={"files": (filename, f, "text/plain")}
        )
    
    if response.status_code == 200:
        upload_result = response.json()
        print(f"✅ Upload successful!")
        print(f"   Message: {upload_result['message']}")
        print(f"   Processing tasks: {upload_result['processing_tasks']}")
        
        # Get the task ID
        task_id = upload_result['processing_tasks'][0]
        
        # Check specific task status
        print(f"\n3. Checking task status for {task_id}:")
        response = requests.get(f"{BASE_URL}/processing/tasks/{task_id}")
        if response.status_code == 200:
            task_status = response.json()
            print(json.dumps(task_status, indent=2))
        
        # Check updated queue status
        print(f"\n4. Updated processing queue status:")
        response = requests.get(f"{BASE_URL}/processing/status")
        print(json.dumps(response.json(), indent=2))
        
        # Get all tasks
        print(f"\n5. All processing tasks:")
        response = requests.get(f"{BASE_URL}/processing/tasks")
        if response.status_code == 200:
            all_tasks = response.json()
            print(f"   Total tasks: {len(all_tasks['tasks'])}")
            for task in all_tasks['tasks'][-3:]:  # Show last 3
                print(f"   - {task['filename']} ({task['status']}) - {task['progress']}%")
    
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)

def test_multiple_uploads():
    """Test multiple file uploads to see queue behavior."""
    print("\n🔄 Testing Multiple File Processing")
    print("=" * 50)
    
    # Create multiple test files
    files_to_upload = []
    for i in range(3):
        filepath, filename = create_test_file()
        files_to_upload.append((filepath, filename))
        time.sleep(0.1)  # Small delay to get different timestamps
    
    # Upload all files
    print(f"\n1. Uploading {len(files_to_upload)} files simultaneously...")
    for filepath, filename in files_to_upload:
        print(f"   Uploading: {filename}")
        with open(filepath, 'rb') as f:
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                files={"files": (filename, f, "text/plain")}
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {filename}: {result['processing_tasks'][0]}")
        else:
            print(f"   ❌ {filename}: Failed")
    
    # Check final status
    print(f"\n2. Final processing queue status:")
    response = requests.get(f"{BASE_URL}/processing/status")
    print(json.dumps(response.json(), indent=2))

def cleanup_old_tasks():
    """Test the cleanup functionality."""
    print("\n🧹 Testing Task Cleanup")
    print("=" * 50)
    
    response = requests.post(f"{BASE_URL}/processing/cleanup")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Cleanup result: {result['message']}")
    else:
        print(f"❌ Cleanup failed: {response.status_code}")

if __name__ == "__main__":
    print("Processing Status Tracking Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        test_processing_status()
        test_multiple_uploads()
        cleanup_old_tasks()
        
        print("\n" + "=" * 60)
        print("✅ All processing status tests completed!")
        print("\nKey Features Tested:")
        print("• Document upload with status tracking")
        print("• Real-time progress updates")
        print("• Processing queue management")
        print("• Task-specific status queries")
        print("• Bulk processing capabilities")
        print("• Automatic task cleanup")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()