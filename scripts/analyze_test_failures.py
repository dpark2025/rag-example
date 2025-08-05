#!/usr/bin/env python3
"""
Analyze test failures to categorize error types
"""
import subprocess
import re

def analyze_category(category, max_failures=20):
    """Analyze failures in a specific test category"""
    cmd = ['python', '-m', 'pytest', '-m', category, '--tb=line', f'--maxfail={max_failures}', '-q']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    errors = result.stdout + result.stderr
    
    # Count error types
    api_signature = len(re.findall(r'takes 1 positional argument but 2 were given', errors))
    upload_file_api = len(re.findall(r'UploadFile.*unexpected keyword argument', errors))
    missing_attributes = len(re.findall(r'object has no attribute', errors))
    service_connection = len(re.findall(r'ConnectionError|ConnectTimeout|Connection refused|Failed to connect', errors))
    
    total_failures = errors.count('FAILED')
    
    return {
        'category': category,
        'total_failures': total_failures,
        'api_signature': api_signature,
        'upload_file_api': upload_file_api, 
        'missing_attributes': missing_attributes,
        'service_connection': service_connection,
        'sample_output': errors[:500] if errors else "No output"
    }

def main():
    categories = ['unit', 'integration', 'performance', 'security', 'stress']
    
    print("=" * 80)
    print("TEST FAILURE ANALYSIS")
    print("=" * 80)
    
    total_service_errors = 0
    total_failures = 0
    
    for category in categories:
        try:
            print(f"\n🔍 Analyzing {category} tests...")
            result = analyze_category(category, 10)  # Small sample
            
            print(f"   Total failures: {result['total_failures']}")
            print(f"   API signature errors: {result['api_signature']}")
            print(f"   UploadFile API errors: {result['upload_file_api']}")
            print(f"   Missing attribute errors: {result['missing_attributes']}")
            print(f"   Service connection errors: {result['service_connection']}")
            
            total_service_errors += result['service_connection']
            total_failures += result['total_failures']
            
        except subprocess.TimeoutExpired:
            print(f"   ❌ {category} tests timed out")
        except Exception as e:
            print(f"   ❌ {category} tests failed to analyze: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Service connection errors (Category 3): {total_service_errors}")
    print(f"Total sampled failures: {total_failures}")
    print(f"Percentage due to service issues: {(total_service_errors/max(total_failures,1))*100:.1f}%")
    
    # Check service status
    print(f"\n🔍 Service Status Check:")
    try:
        import requests
        r = requests.get('http://localhost:11434/api/tags', timeout=2)
        print(f"   Ollama (localhost:11434): ✅ Running (status {r.status_code})")
    except:
        print(f"   Ollama (localhost:11434): ❌ Not accessible")
    
    try:
        import chromadb
        client = chromadb.Client()
        client.heartbeat()
        print(f"   ChromaDB: ✅ Running")
    except:
        print(f"   ChromaDB: ❌ Not accessible")

if __name__ == "__main__":
    main()