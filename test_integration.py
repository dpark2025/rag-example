#!/usr/bin/env python3
"""
Integration Testing Script
Tests API endpoints, WebSocket connections, and system integration
"""

import requests
import json
import time
import asyncio
import websockets
import threading

class IntegrationTester:
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
    
    def test_all_api_endpoints(self):
        """Test all documented API endpoints"""
        try:
            start_time = time.time()
            
            # Get endpoint information
            info_response = requests.get(f"{self.base_url}/info", timeout=10)
            
            if info_response.status_code != 200:
                self.log_result("API Endpoints", False, "Cannot get API info", 0)
                return False
            
            info_data = info_response.json()
            endpoints = info_data.get("endpoints", {})
            
            tested_endpoints = 0
            working_endpoints = 0
            
            # Test health endpoint
            if "health" in endpoints:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                tested_endpoints += 1
                if response.status_code == 200:
                    working_endpoints += 1
            
            # Test settings endpoints
            if "settings" in endpoints:
                # GET settings
                response = requests.get(f"{self.base_url}/settings", timeout=5)
                tested_endpoints += 1
                if response.status_code == 200:
                    working_endpoints += 1
                
                # POST settings (update)
                response = requests.post(f"{self.base_url}/settings", 
                                       json={"similarity_threshold": 0.5}, timeout=5)
                tested_endpoints += 1
                if response.status_code == 200:
                    working_endpoints += 1
            
            # Test document endpoints
            if "documents" in endpoints:
                # List documents
                response = requests.get(f"{self.base_url}/api/v1/documents?limit=1", timeout=10)
                tested_endpoints += 1
                if response.status_code == 200:
                    working_endpoints += 1
                
                # Get stats
                response = requests.get(f"{self.base_url}/api/v1/documents/stats", timeout=10)
                tested_endpoints += 1
                if response.status_code == 200:
                    working_endpoints += 1
            
            duration = time.time() - start_time
            success_rate = working_endpoints / tested_endpoints if tested_endpoints > 0 else 0
            
            self.log_result("API Endpoints", success_rate >= 0.8, 
                          f"{working_endpoints}/{tested_endpoints} endpoints working ({success_rate:.1%})", 
                          duration)
            return success_rate >= 0.8
            
        except Exception as e:
            self.log_result("API Endpoints", False, f"Error: {e}", 0)
            return False
    
    def test_websocket_connection(self):
        """Test WebSocket connection for real-time updates"""
        try:
            start_time = time.time()
            
            # WebSocket endpoint: /api/v1/documents/ws/{client_id}
            ws_url = f"ws://localhost:8000/api/v1/documents/ws/test-client"
            
            async def test_websocket():
                try:
                    async with websockets.connect(ws_url, timeout=10) as websocket:
                        # Send a test message or wait for connection confirmation
                        await asyncio.sleep(1)  # Give it time to establish
                        return True
                except Exception as e:
                    print(f"   WebSocket connection failed: {e}")
                    return False
            
            # Run the async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            connected = loop.run_until_complete(test_websocket())
            loop.close()
            
            duration = time.time() - start_time
            
            self.log_result("WebSocket Connection", connected, 
                          f"WebSocket connection established: {connected}", 
                          duration)
            return connected
            
        except Exception as e:
            self.log_result("WebSocket Connection", False, f"Error: {e}", 0)
            return False
    
    def test_health_monitoring(self):
        """Test health monitoring system"""
        try:
            start_time = time.time()
            
            # Test health endpoint
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Check required health data structure
                required_fields = ["status", "components", "document_count"]
                has_required = all(field in health_data for field in required_fields)
                
                # Check monitoring details
                monitoring = health_data.get("monitoring", {})
                monitoring_enabled = monitoring.get("enabled", False)
                
                # Test metrics endpoint
                metrics_response = requests.get(f"{self.base_url}/health/metrics", timeout=10)
                metrics_available = metrics_response.status_code == 200
                
                duration = time.time() - start_time
                
                health_system_working = has_required and monitoring_enabled and metrics_available
                
                self.log_result("Health Monitoring", health_system_working, 
                              f"Health data complete: {has_required}, Monitoring: {monitoring_enabled}, Metrics: {metrics_available}", 
                              duration)
                return health_system_working
            else:
                duration = time.time() - start_time
                self.log_result("Health Monitoring", False, 
                              f"Health endpoint failed: HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("Health Monitoring", False, f"Error: {e}", 0)
            return False
    
    def test_error_statistics(self):
        """Test error statistics and tracking"""
        try:
            start_time = time.time()
            
            # Test error statistics endpoint
            response = requests.get(f"{self.base_url}/health/errors", timeout=10)
            
            if response.status_code == 200:
                error_data = response.json()
                
                # Check error statistics structure
                success = error_data.get("success", False)
                statistics = error_data.get("statistics", {})
                
                has_stats = "total" in statistics and "by_category" in statistics
                
                duration = time.time() - start_time
                
                self.log_result("Error Statistics", success and has_stats, 
                              f"Error tracking available: {success}, Stats structure: {has_stats}", 
                              duration)
                return success and has_stats
            else:
                duration = time.time() - start_time
                self.log_result("Error Statistics", False, 
                              f"Error stats endpoint failed: HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("Error Statistics", False, f"Error: {e}", 0)
            return False
    
    def test_upload_task_tracking(self):
        """Test upload task tracking system"""
        try:
            start_time = time.time()
            
            # Test upload tasks endpoint
            response = requests.get(f"{self.base_url}/api/v1/upload/tasks", timeout=10)
            
            if response.status_code == 200:
                tasks_data = response.json()
                
                # Check tasks structure
                has_tasks = "tasks" in tasks_data and "total_tasks" in tasks_data
                
                # Test upload statistics
                stats_response = requests.get(f"{self.base_url}/api/v1/upload/stats", timeout=10)
                stats_available = stats_response.status_code == 200
                
                duration = time.time() - start_time
                
                tracking_working = has_tasks and stats_available
                
                self.log_result("Upload Task Tracking", tracking_working, 
                              f"Tasks endpoint working: {has_tasks}, Stats available: {stats_available}", 
                              duration)
                return tracking_working
            else:
                duration = time.time() - start_time
                self.log_result("Upload Task Tracking", False, 
                              f"Upload tasks endpoint failed: HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("Upload Task Tracking", False, f"Error: {e}", 0)
            return False
    
    def test_cors_and_headers(self):
        """Test CORS configuration and security headers"""
        try:
            start_time = time.time()
            
            # Test CORS headers
            response = requests.get(f"{self.base_url}/health", 
                                  headers={'Origin': 'http://localhost:3000'}, 
                                  timeout=5)
            
            if response.status_code == 200:
                # Check CORS headers
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                cors_methods = response.headers.get('Access-Control-Allow-Methods')
                
                # For development, permissive CORS is acceptable
                cors_configured = cors_origin is not None
                
                # Check for basic security headers (optional but good)
                security_headers = {
                    'X-Content-Type-Options': response.headers.get('X-Content-Type-Options'),
                    'X-Frame-Options': response.headers.get('X-Frame-Options'),
                }
                
                duration = time.time() - start_time
                
                self.log_result("CORS and Headers", cors_configured, 
                              f"CORS configured: {cors_configured}, Origin: {cors_origin}", 
                              duration)
                return cors_configured
            else:
                duration = time.time() - start_time
                self.log_result("CORS and Headers", False, 
                              f"Request failed: HTTP {response.status_code}", duration)
                return False
                
        except Exception as e:
            self.log_result("CORS and Headers", False, f"Error: {e}", 0)
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🔗 Starting Integration Testing\n")
        
        # Check if websockets is available
        try:
            import websockets
        except ImportError:
            print("Installing websockets for WebSocket testing...")
            import subprocess
            subprocess.check_call(["pip", "install", "websockets"])
            import websockets
        
        # Run integration tests
        self.test_all_api_endpoints()
        self.test_health_monitoring()
        self.test_error_statistics()
        self.test_upload_task_tracking()
        self.test_cors_and_headers()
        self.test_websocket_connection()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print("📊 INTEGRATION TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for result in self.results if result["success"])
        total = len(self.results)
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Run: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            print("\n🎉 INTEGRATION: EXCELLENT")
        elif pass_rate >= 75:
            print("\n✅ INTEGRATION: GOOD")
        elif pass_rate >= 60:
            print("\n⚠️  INTEGRATION: NEEDS IMPROVEMENT")
        else:
            print("\n❌ INTEGRATION: CRITICAL ISSUES")

if __name__ == "__main__":
    tester = IntegrationTester()
    tester.run_all_tests()