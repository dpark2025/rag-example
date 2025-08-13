#!/usr/bin/env python3
"""
Test configuration loading functionality.
"""

import sys
import os
sys.path.append('app')

from app.rag_backend import config

def test_configuration():
    """Test that configuration values are loaded correctly."""
    print("Testing Configuration Loading...")
    print("=" * 40)
    
    # Test LLM configuration
    llm_config = config.get('llm')
    print(f"LLM Model: {llm_config.get('model')}")
    print(f"Temperature: {llm_config.get('temperature')}")
    print(f"Max Tokens: {llm_config.get('max_tokens')}")
    print(f"Base URL: {llm_config.get('base_url')}")
    
    # Test RAG configuration
    rag_config = config.get('rag')
    print(f"\nRAG Similarity Threshold: {rag_config.get('similarity_threshold')}")
    print(f"Max Chunks: {rag_config.get('max_chunks')}")
    print(f"Chunk Size: {rag_config.get('chunk_size')}")
    print(f"Chunk Overlap: {rag_config.get('chunk_overlap')}")
    
    # Test Vector DB configuration
    vector_db_config = config.get('vector_db')
    print(f"\nVector DB Collection Name: {vector_db_config.get('collection_name')}")
    
    # Test API configuration
    api_config = config.get('api')
    print(f"\nAPI Host: {api_config.get('host')}")
    print(f"API Port: {api_config.get('port')}")
    
    print("\n✅ Configuration loading successful!")
    
    return True

if __name__ == "__main__":
    test_configuration()