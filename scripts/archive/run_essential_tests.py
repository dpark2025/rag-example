#!/usr/bin/env python3
"""
Essential tests runner for RAG system.

Runs a simplified test suite focusing on core functionality validation.
Much faster and more reliable than the comprehensive test suite.

Authored by: Claude
Date: 2025-08-05
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def clean_test_environment():
    """Clean up any existing test data before running tests."""
    print("🧹 Cleaning test environment...")
    
    # Remove ChromaDB data
    chroma_path = Path("./data/chroma_db")
    if chroma_path.exists():
        import shutil
        shutil.rmtree(chroma_path)
        print("  ✓ Cleaned ChromaDB data")
    
    # Remove test documents
    docs_path = Path("./data/documents")
    if docs_path.exists():
        import shutil
        shutil.rmtree(docs_path)
        print("  ✓ Cleaned document data")


def check_dependencies():
    """Check if required services are running."""
    print("\n🔍 Checking dependencies...")
    
    # Check Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=2)
        if response.status_code == 200:
            print("  ✓ Ollama is running")
        else:
            print("  ⚠️  Ollama may not be properly configured")
    except:
        print("  ⚠️  Ollama is not running (some tests may fail)")
    
    # Check ChromaDB
    try:
        import chromadb
        print("  ✓ ChromaDB is available")
    except ImportError:
        print("  ❌ ChromaDB is not installed")
        return False
    
    return True


def run_essential_tests():
    """Run the essential functionality tests."""
    print("\n🧪 Running essential functionality tests...\n")
    
    start_time = time.time()
    
    # Run pytest with essential tests only
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_essential_functionality.py",
        "-v",                    # Verbose output
        "--tb=short",           # Short traceback
        "--disable-warnings",   # Disable warnings for cleaner output
        "-s"                    # Show print statements
    ]
    
    try:
        result = subprocess.run(cmd, cwd=Path.cwd())
        duration = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"Test execution completed in {duration:.2f} seconds")
        print(f"{'='*60}")
        
        if result.returncode == 0:
            print("\n✅ All essential tests passed!")
            return True
        else:
            print("\n❌ Some tests failed. Please check the output above.")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return False


def main():
    """Main execution function."""
    print("RAG System Essential Tests")
    print("=" * 60)
    
    # Clean environment
    clean_test_environment()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing required dependencies. Please install them first.")
        sys.exit(1)
    
    # Run tests
    success = run_essential_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()