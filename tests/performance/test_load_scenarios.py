"""
Comprehensive performance testing with load scenarios and concurrent user testing.

Tests system behavior under high load, concurrent users, resource exhaustion,
and stress conditions to ensure reliability and performance targets.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-05
"""

import pytest
import asyncio
import time
import threading
import psutil
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
import httpx
from fastapi.testclient import TestClient

# Import modules under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from rag_backend import LocalRAGSystem
from document_manager import DocumentManager
from upload_handler import UploadHandler
from main import app


@pytest.mark.performance
class TestLoadScenarios:
    """Load testing scenarios for RAG system components."""

    @pytest.fixture
    def performance_metrics(self):
        """Utility to collect and analyze performance metrics."""
        class PerformanceMetrics:
            def __init__(self):
                self.response_times = []
                self.throughput_data = []
                self.error_rates = []
                self.memory_usage = []
                self.cpu_usage = []
                
            def record_response_time(self, duration: float):
                self.response_times.append(duration)
                
            def record_throughput(self, operations_per_second: float):
                self.throughput_data.append(operations_per_second)
                
            def record_error_rate(self, error_rate: float):
                self.error_rates.append(error_rate)
                
            def record_system_metrics(self):
                process = psutil.Process()
                self.memory_usage.append(process.memory_info().rss / (1024**2))  # MB
                self.cpu_usage.append(process.cpu_percent())
                
            def get_summary(self) -> Dict[str, Any]:
                return {
                    'response_times': {
                        'mean': statistics.mean(self.response_times) if self.response_times else 0,
                        'median': statistics.median(self.response_times) if self.response_times else 0,
                        'p95': np.percentile(self.response_times, 95) if self.response_times else 0,
                        'p99': np.percentile(self.response_times, 99) if self.response_times else 0,
                        'max': max(self.response_times) if self.response_times else 0
                    },
                    'throughput': {
                        'mean': statistics.mean(self.throughput_data) if self.throughput_data else 0,
                        'max': max(self.throughput_data) if self.throughput_data else 0
                    },
                    'error_rate': {
                        'mean': statistics.mean(self.error_rates) if self.error_rates else 0,
                        'max': max(self.error_rates) if self.error_rates else 0
                    },
                    'memory_usage': {
                        'mean': statistics.mean(self.memory_usage) if self.memory_usage else 0,
                        'max': max(self.memory_usage) if self.memory_usage else 0
                    },
                    'cpu_usage': {
                        'mean': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                        'max': max(self.cpu_usage) if self.cpu_usage else 0
                    }
                }
        
        return PerformanceMetrics()

    @pytest.mark.slow
    def test_concurrent_rag_queries(self, rag_system_with_documents, performance_metrics):
        """Test RAG query performance with concurrent users."""
        query_sets = [
            "What is artificial intelligence?",
            "How do machine learning algorithms work?",
            "What are vector databases used for?",
            "Explain natural language processing",
            "What is document retrieval?"
        ]
        
        concurrent_users = 20
        queries_per_user = 5
        total_queries = concurrent_users * queries_per_user
        
        def execute_queries(user_id: int) -> List[Tuple[float, bool]]:
            """Execute queries for a single user."""
            results = []
            for i in range(queries_per_user):
                query = query_sets[i % len(query_sets)]
                
                start_time = time.time()
                try:
                    result = rag_system_with_documents.rag_query(query)
                    duration = time.time() - start_time
                    success = result and 'answer' in result
                    results.append((duration, success))
                except Exception:
                    duration = time.time() - start_time
                    results.append((duration, False))
                    
            return results
        
        # Execute concurrent queries
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(execute_queries, user_id) for user_id in range(concurrent_users)]
            
            all_results = []
            for future in as_completed(futures):
                user_results = future.result()
                all_results.extend(user_results)
        
        total_duration = time.time() - start_time
        
        # Analyze results
        response_times = [r[0] for r in all_results]
        successes = [r[1] for r in all_results]
        
        success_rate = sum(successes) / len(successes)
        throughput = total_queries / total_duration
        
        # Performance assertions
        assert success_rate >= 0.95  # 95% success rate
        assert statistics.mean(response_times) < 2.0  # Mean response time < 2s
        assert np.percentile(response_times, 95) < 5.0  # 95th percentile < 5s
        assert throughput >= 5.0  # At least 5 queries/second
        
        # Record metrics
        for rt in response_times:
            performance_metrics.record_response_time(rt)
        performance_metrics.record_throughput(throughput)
        performance_metrics.record_error_rate(1 - success_rate)
        
        print(f"Concurrent query test: {success_rate:.2%} success rate, {throughput:.1f} q/s")

    @pytest.mark.slow
    def test_document_upload_load(self, upload_handler, performance_metrics):
        """Test document upload performance under load."""
        from fastapi import UploadFile
        from io import BytesIO
        
        concurrent_uploads = 10
        files_per_batch = 5
        
        def create_test_file(size_kb: int, file_id: str) -> UploadFile:
            content = f"Test content for file {file_id}. " * (size_kb * 10)
            content_bytes = content.encode()[:size_kb * 1024]
            
            file_obj = BytesIO(content_bytes)
            return UploadFile(
                file=file_obj,
                filename=f"load_test_{file_id}.txt",
                size=len(content_bytes)
            )
        
        async def upload_batch(batch_id: int) -> List[Tuple[float, bool]]:
            """Upload a batch of files."""
            results = []
            
            for file_id in range(files_per_batch):
                test_file = create_test_file(10, f"{batch_id}_{file_id}")
                
                # Mock document manager
                upload_handler.document_manager.add_document = AsyncMock(
                    return_value=f"doc_{batch_id}_{file_id}"
                )
                
                start_time = time.time()
                try:
                    result = await upload_handler.handle_upload(test_file)
                    duration = time.time() - start_time
                    success = result.success
                    results.append((duration, success))
                except Exception:
                    duration = time.time() - start_time
                    results.append((duration, False))
                    
            return results
        
        async def run_load_test():
            # Execute concurrent uploads
            tasks = [upload_batch(batch_id) for batch_id in range(concurrent_uploads)]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_results = []
            for batch_result in batch_results:
                if not isinstance(batch_result, Exception):
                    all_results.extend(batch_result)
            
            return all_results
        
        # Run the load test
        start_time = time.time()
        all_results = asyncio.run(run_load_test())
        total_duration = time.time() - start_time
        
        # Analyze results
        upload_times = [r[0] for r in all_results]
        successes = [r[1] for r in all_results]
        
        success_rate = sum(successes) / len(successes)
        throughput = len(all_results) / total_duration
        
        # Performance assertions
        assert success_rate >= 0.90  # 90% success rate for uploads
        assert statistics.mean(upload_times) < 5.0  # Mean upload time < 5s
        assert throughput >= 2.0  # At least 2 uploads/second
        
        print(f"Upload load test: {success_rate:.2%} success rate, {throughput:.1f} uploads/s")

    @pytest.mark.slow
    def test_memory_usage_under_load(self, rag_system, performance_metrics):
        """Test memory usage patterns under sustained load."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Simulate sustained load with document operations
        for cycle in range(10):
            # Add documents
            documents = []
            for i in range(20):
                documents.append({
                    "title": f"Load Test Doc {cycle}_{i}",
                    "content": f"This is load test content for cycle {cycle}, document {i}. " * 100,
                    "source": f"load_test_{cycle}_{i}",
                    "doc_id": f"load_doc_{cycle}_{i}"
                })
            
            # Mock heavy operations
            rag_system.collection = Mock()
            rag_system.collection.add = Mock()
            rag_system.collection.count = Mock(return_value=20 * (cycle + 1))
            rag_system.encoder.encode = Mock(return_value=np.random.rand(20, 384).tolist())
            
            start_time = time.time()
            result = rag_system.add_documents(documents)
            duration = time.time() - start_time
            
            # Record metrics
            current_memory = process.memory_info().rss
            memory_mb = (current_memory - initial_memory) / (1024 ** 2)
            
            performance_metrics.record_system_metrics()
            performance_metrics.record_response_time(duration)
            
            # Memory should not grow excessively
            assert memory_mb < 500  # Less than 500MB memory growth
            
            # Performance should remain consistent
            assert duration < 10.0  # Should complete within 10 seconds
            
            # Simulate some cleanup
            if cycle % 3 == 0:
                import gc
                gc.collect()
        
        final_memory = process.memory_info().rss
        total_memory_growth = (final_memory - initial_memory) / (1024 ** 2)
        
        # Final memory assertion
        assert total_memory_growth < 300  # Less than 300MB total growth
        
        print(f"Memory load test: {total_memory_growth:.1f}MB total growth")

    def test_cpu_usage_under_load(self, rag_system, performance_metrics):
        """Test CPU usage patterns under computational load."""
        process = psutil.Process()
        
        # Generate computationally intensive workload
        large_documents = []
        for i in range(10):
            # Create large documents with complex content
            content = f"Complex document {i} with extensive content. " * 1000
            large_documents.append({
                "title": f"CPU Load Test Doc {i}",
                "content": content,
                "source": f"cpu_test_{i}",
                "doc_id": f"cpu_doc_{i}"
            })
        
        # Mock expensive operations with realistic delays
        def mock_generate_embeddings(texts):
            # Simulate CPU-intensive embedding generation
            time.sleep(0.1 * len(texts))  # 100ms per text
            return np.random.rand(len(texts), 384).tolist()
        
        rag_system.encoder.encode = mock_generate_embeddings
        rag_system.collection = Mock()
        rag_system.collection.add = Mock()
        rag_system.collection.count = Mock(return_value=len(large_documents) * 3)
        
        cpu_measurements = []
        
        def monitor_cpu():
            """Monitor CPU usage in background."""
            while not getattr(monitor_cpu, 'stop', False):
                cpu_percent = process.cpu_percent(interval=0.1)
                cpu_measurements.append(cpu_percent)
                time.sleep(0.1)
        
        # Start CPU monitoring
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        try:
            start_time = time.time()
            result = rag_system.add_documents(large_documents)
            duration = time.time() - start_time
            
            # Stop monitoring
            monitor_cpu.stop = True
            monitor_thread.join(timeout=1.0)
            
            # Analyze CPU usage
            if cpu_measurements:
                avg_cpu = statistics.mean(cpu_measurements)
                max_cpu = max(cpu_measurements)
                
                # CPU usage assertions
                assert avg_cpu < 80.0  # Average CPU < 80%
                assert max_cpu < 95.0  # Peak CPU < 95%
                
                performance_metrics.record_system_metrics()
                
                print(f"CPU load test: {avg_cpu:.1f}% avg, {max_cpu:.1f}% max CPU usage")
            
            # Performance assertions
            assert duration < 30.0  # Should complete within 30 seconds
            assert "Successfully added" in result
            
        finally:
            monitor_cpu.stop = True
            if monitor_thread.is_alive():
                monitor_thread.join(timeout=1.0)

    @pytest.mark.slow
    def test_concurrent_mixed_operations(self, rag_system, upload_handler, performance_metrics):
        """Test system performance with mixed concurrent operations."""
        from fastapi import UploadFile
        from io import BytesIO
        
        def create_upload_file(content: str, filename: str) -> UploadFile:
            content_bytes = content.encode()
            file_obj = BytesIO(content_bytes)
            return UploadFile(
                file=file_obj,
                filename=filename,
                size=len(content_bytes)
            )
        
        async def upload_operation(op_id: int) -> Tuple[str, float, bool]:
            """Perform upload operation."""
            test_file = create_upload_file(f"Mixed test content {op_id}", f"mixed_{op_id}.txt")
            upload_handler.document_manager.add_document = AsyncMock(return_value=f"doc_{op_id}")
            
            start_time = time.time()
            try:
                result = await upload_handler.handle_upload(test_file)
                duration = time.time() - start_time
                return ("upload", duration, result.success)
            except Exception:
                duration = time.time() - start_time
                return ("upload", duration, False)
        
        def query_operation(op_id: int) -> Tuple[str, float, bool]:
            """Perform query operation."""
            queries = [
                "What is artificial intelligence?",
                "Explain machine learning",
                "How do vector databases work?",
                "What is natural language processing?",
                "Describe document retrieval"
            ]
            query = queries[op_id % len(queries)]
            
            start_time = time.time()
            try:
                result = rag_system.rag_query(query)
                duration = time.time() - start_time
                return ("query", duration, bool(result and 'answer' in result))
            except Exception:
                duration = time.time() - start_time
                return ("query", duration, False)
        
        def document_add_operation(op_id: int) -> Tuple[str, float, bool]:
            """Perform document addition operation."""
            documents = [{
                "title": f"Mixed Operation Doc {op_id}",
                "content": f"Content for mixed operation {op_id}. " * 50,
                "source": f"mixed_op_{op_id}",
                "doc_id": f"mixed_doc_{op_id}"
            }]
            
            # Mock heavy operations
            rag_system.collection = Mock()
            rag_system.collection.add = Mock()
            rag_system.collection.count = Mock(return_value=1)
            rag_system.encoder.encode = Mock(return_value=np.random.rand(1, 384).tolist())
            
            start_time = time.time()
            try:
                result = rag_system.add_documents(documents)
                duration = time.time() - start_time
                return ("add_doc", duration, "Successfully added" in result)
            except Exception:
                duration = time.time() - start_time
                return ("add_doc", duration, False)
        
        async def run_mixed_operations():
            """Run mixed operations concurrently."""
            tasks = []
            
            # Create mixed workload
            for i in range(30):
                if i % 3 == 0:
                    # Upload operation (async)
                    tasks.append(asyncio.create_task(upload_operation(i)))
                elif i % 3 == 1:
                    # Query operation (sync, run in executor)
                    loop = asyncio.get_event_loop()
                    tasks.append(loop.run_in_executor(None, query_operation, i))
                else:
                    # Document add operation (sync, run in executor)
                    loop = asyncio.get_event_loop()
                    tasks.append(loop.run_in_executor(None, document_add_operation, i))
            
            # Wait for all operations to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if not isinstance(r, Exception)]
        
        # Execute mixed operations
        start_time = time.time()
        results = asyncio.run(run_mixed_operations())
        total_duration = time.time() - start_time
        
        # Analyze results by operation type
        operation_stats = {}
        for op_type, duration, success in results:
            if op_type not in operation_stats:
                operation_stats[op_type] = {'durations': [], 'successes': []}
            operation_stats[op_type]['durations'].append(duration)
            operation_stats[op_type]['successes'].append(success)
        
        # Verify performance for each operation type
        for op_type, stats in operation_stats.items():
            durations = stats['durations']
            successes = stats['successes']
            
            success_rate = sum(successes) / len(successes)
            avg_duration = statistics.mean(durations)
            
            # Performance assertions per operation type
            assert success_rate >= 0.85  # 85% success rate minimum
            
            if op_type == "upload":
                assert avg_duration < 3.0  # Uploads should be fast
            elif op_type == "query":
                assert avg_duration < 2.0  # Queries should be fast
            elif op_type == "add_doc":
                assert avg_duration < 5.0  # Document additions can be slower
            
            print(f"{op_type}: {success_rate:.2%} success rate, {avg_duration:.2f}s avg duration")
        
        # Overall throughput
        total_ops = len(results)
        throughput = total_ops / total_duration
        
        assert throughput >= 5.0  # At least 5 operations/second
        print(f"Mixed operations: {throughput:.1f} ops/s total throughput")


@pytest.mark.performance
class TestStressScenarios:
    """Stress testing scenarios for system limits."""

    @pytest.mark.slow
    def test_database_connection_stress(self, rag_system):
        """Test database connection handling under stress."""
        connection_attempts = 100
        successful_connections = 0
        connection_times = []
        
        for i in range(connection_attempts):
            start_time = time.time()
            
            try:
                # Simulate database operation
                rag_system.collection = Mock()
                rag_system.collection.add = Mock()
                rag_system.collection.query = Mock(return_value={
                    "ids": [["test_id"]],
                    "distances": [[0.1]],
                    "metadatas": [[{"title": "Test"}]],
                    "documents": [["Test content"]]
                })
                
                # Perform a query operation
                result = rag_system.adaptive_retrieval("test query")
                
                duration = time.time() - start_time
                connection_times.append(duration)
                successful_connections += 1
                
            except Exception as e:
                print(f"Connection attempt {i} failed: {e}")
        
        success_rate = successful_connections / connection_attempts
        avg_connection_time = statistics.mean(connection_times) if connection_times else 0
        
        # Stress test assertions
        assert success_rate >= 0.95  # 95% success rate under stress
        assert avg_connection_time < 1.0  # Average connection time < 1s
        
        print(f"DB stress test: {success_rate:.2%} success rate, {avg_connection_time:.2f}s avg time")

    @pytest.mark.slow
    def test_memory_pressure_stress(self, rag_system):
        """Test system behavior under extreme memory pressure."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create memory pressure by processing many large documents
        large_documents = []
        for i in range(50):
            # Create very large documents
            content = f"Large document {i} with extensive content. " * 2000  # ~100KB each
            large_documents.append({
                "title": f"Memory Stress Doc {i}",
                "content": content,
                "source": f"memory_stress_{i}",
                "doc_id": f"memory_doc_{i}",
                "file_type": "txt"
            })
        
        # Process documents in batches to create sustained memory pressure
        batch_size = 10
        successful_batches = 0
        
        for batch_start in range(0, len(large_documents), batch_size):
            batch = large_documents[batch_start:batch_start + batch_size]
            
            try:
                # Mock operations to avoid actual memory allocation
                rag_system.collection = Mock()
                rag_system.collection.add = Mock()
                rag_system.collection.count = Mock(return_value=len(batch) * 3)
                
                # Simulate memory-intensive embedding generation
                rag_system.encoder.encode = Mock(return_value=np.random.rand(len(batch) * 3, 384).tolist())
                
                result = rag_system.add_documents(batch)
                
                current_memory = process.memory_info().rss
                memory_mb = (current_memory - initial_memory) / (1024 ** 2)
                
                # Check memory doesn't grow too much
                if memory_mb < 1000:  # Less than 1GB growth
                    successful_batches += 1
                
                # Force garbage collection to simulate memory management
                import gc
                gc.collect()
                
            except MemoryError:
                print(f"Memory error at batch {batch_start // batch_size}")
                break
            except Exception as e:
                print(f"Error processing batch {batch_start // batch_size}: {e}")
        
        success_rate = successful_batches / (len(large_documents) // batch_size)
        
        # Memory stress assertions
        assert success_rate >= 0.80  # 80% success rate under memory pressure
        
        final_memory = process.memory_info().rss
        total_memory_growth = (final_memory - initial_memory) / (1024 ** 2)
        
        print(f"Memory stress test: {success_rate:.2%} success rate, {total_memory_growth:.1f}MB growth")

    @pytest.mark.slow  
    def test_concurrent_user_simulation(self, rag_system_with_documents):
        """Simulate realistic concurrent user behavior."""
        
        def simulate_user_session(user_id: int, session_duration: int = 60) -> Dict[str, Any]:
            """Simulate a single user session."""
            session_start = time.time()
            operations = []
            
            user_queries = [
                f"User {user_id}: What is artificial intelligence?",
                f"User {user_id}: How does machine learning work?",
                f"User {user_id}: Explain vector databases",
                f"User {user_id}: What is natural language processing?",
                f"User {user_id}: How do I implement RAG systems?"
            ]
            
            while time.time() - session_start < session_duration:
                query = user_queries[len(operations) % len(user_queries)]
                
                op_start = time.time()
                try:
                    result = rag_system_with_documents.rag_query(query)
                    op_duration = time.time() - op_start
                    
                    operations.append({
                        'type': 'query',
                        'duration': op_duration,
                        'success': bool(result and 'answer' in result),
                        'timestamp': op_start
                    })
                    
                except Exception as e:
                    op_duration = time.time() - op_start
                    operations.append({
                        'type': 'query',
                        'duration': op_duration,
                        'success': False,
                        'error': str(e),
                        'timestamp': op_start
                    })
                
                # Simulate user think time (1-5 seconds between queries)
                think_time = np.random.uniform(1.0, 5.0)
                time.sleep(think_time)
            
            return {
                'user_id': user_id,
                'session_duration': time.time() - session_start,
                'operations': operations
            }
        
        # Simulate multiple concurrent users
        concurrent_users = 15
        session_duration = 30  # 30 seconds per session
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(simulate_user_session, user_id, session_duration)
                for user_id in range(concurrent_users)
            ]
            
            user_sessions = [future.result() for future in as_completed(futures)]
        
        total_test_duration = time.time() - start_time
        
        # Analyze session results
        all_operations = []
        for session in user_sessions:
            all_operations.extend(session['operations'])
        
        successful_ops = [op for op in all_operations if op['success']]
        failed_ops = [op for op in all_operations if not op['success']]
        
        success_rate = len(successful_ops) / len(all_operations) if all_operations else 0
        avg_response_time = statistics.mean([op['duration'] for op in successful_ops]) if successful_ops else 0
        total_throughput = len(all_operations) / total_test_duration
        
        # User simulation assertions
        assert success_rate >= 0.90  # 90% success rate for user operations
        assert avg_response_time < 3.0  # Average response time < 3s
        assert total_throughput >= 2.0  # At least 2 operations/second total
        
        # Analyze concurrent load patterns
        time_windows = {}
        for op in all_operations:
            window = int(op['timestamp'] - start_time) // 5  # 5-second windows
            if window not in time_windows:
                time_windows[window] = []
            time_windows[window].append(op)
        
        max_concurrent_ops = max(len(ops) for ops in time_windows.values()) if time_windows else 0
        
        print(f"User simulation: {concurrent_users} users, {success_rate:.2%} success rate")
        print(f"Throughput: {total_throughput:.1f} ops/s, Max concurrent: {max_concurrent_ops} ops/5s")
        print(f"Avg response time: {avg_response_time:.2f}s")
        
        return {
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'throughput': total_throughput,
            'max_concurrent_ops': max_concurrent_ops,
            'user_sessions': user_sessions
        }