#!/usr/bin/env python3
"""
Performance optimization test script for the RAG system.

Tests caching, connection pooling, and performance monitoring functionality.
"""

import asyncio
import time
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_caching_system():
    """Test the caching system performance."""
    logger.info("Testing caching system...")
    
    from performance_cache import PerformanceCache, CacheStrategy
    
    # Create test cache
    cache = PerformanceCache(
        max_size=100,
        default_ttl=10.0,
        strategy=CacheStrategy.LRU
    )
    
    # Test basic operations
    cache.set("test_key", "test_value")
    assert cache.get("test_key") == "test_value"
    
    # Test TTL expiration
    cache.set("expire_key", "expire_value", ttl=0.1)
    time.sleep(0.2)
    assert cache.get("expire_key") is None
    
    # Test performance with many operations
    start_time = time.time()
    for i in range(1000):
        cache.set(f"key_{i}", f"value_{i}")
    
    for i in range(1000):
        cache.get(f"key_{i}")
    
    cache_time = time.time() - start_time
    
    stats = cache.get_stats()
    logger.info(f"Cache performance test: {cache_time:.3f}s for 2000 operations")
    logger.info(f"Cache stats: hit_rate={stats['hit_rate']:.1f}%, size={stats['cache_size']}")
    
    cache.shutdown()
    return True

def test_connection_pooling():
    """Test connection pooling performance."""
    logger.info("Testing connection pooling...")
    
    from connection_pool import ConnectionPool
    
    def create_mock_connection():
        return {"id": int(time.time() * 1000000), "created": time.time()}
    
    # Create connection pool
    pool = ConnectionPool(
        name="test_pool",
        connection_factory=create_mock_connection,
        min_connections=2,
        max_connections=5
    )
    
    # Test connection acquisition
    connections = []
    start_time = time.time()
    
    for i in range(10):
        conn = pool.get_connection()
        if conn:
            connections.append(conn)
            pool.return_connection(conn)
    
    pool_time = time.time() - start_time
    stats = pool.get_stats()
    
    logger.info(f"Connection pool test: {pool_time:.3f}s for 10 operations")
    logger.info(f"Pool stats: total={stats['total_connections']}, utilization={stats['pool_utilization']:.1f}%")
    
    pool.shutdown()
    return True

async def test_async_caching():
    """Test async caching with request coalescing."""
    logger.info("Testing async caching with request coalescing...")
    
    from performance_cache import PerformanceCache, CacheStrategy
    
    cache = PerformanceCache(
        max_size=50,
        default_ttl=30.0,
        strategy=CacheStrategy.LRU
    )
    
    call_count = 0
    
    async def expensive_computation():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)  # Simulate expensive operation
        return f"result_{call_count}"
    
    # Test request coalescing - multiple requests for same key
    start_time = time.time()
    
    tasks = []
    for i in range(5):
        task = cache.get_or_compute(
            key="expensive_key",
            compute_func=expensive_computation,
            use_coalescing=True
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    coalescing_time = time.time() - start_time
    
    # All results should be the same (from single computation)
    assert all(result == results[0] for result in results)
    assert call_count == 1  # Should only be called once due to coalescing
    
    logger.info(f"Request coalescing test: {coalescing_time:.3f}s for 5 concurrent requests")
    logger.info(f"Computation called {call_count} times (should be 1)")
    
    cache.shutdown()
    return True

def test_performance_monitoring():
    """Test performance monitoring system."""
    logger.info("Testing performance monitoring...")
    
    from performance_monitor import PerformanceMonitor, AlertRule, AlertLevel
    
    monitor = PerformanceMonitor(retention_seconds=60)
    
    # Record some test metrics
    for i in range(10):
        monitor.record_timer("test_operation", 50.0 + i * 10)  # 50-140ms
        monitor.record_gauge("memory_usage", 100.0 + i * 5)   # 100-145MB
        monitor.record_counter("requests_total", 1)
    
    # Get metric summary
    timer_summary = monitor.get_metric_summary("test_operation", duration_seconds=60)
    gauge_summary = monitor.get_metric_summary("memory_usage", duration_seconds=60)
    
    logger.info(f"Timer metrics - mean: {timer_summary.get('mean', 0):.1f}ms, "
               f"p95: {timer_summary.get('p95', 0):.1f}ms")
    logger.info(f"Gauge metrics - latest: {gauge_summary.get('latest_value', 0):.1f}MB")
    
    # Test alerting
    alert_triggered = False
    
    def alert_callback(alert_event):
        nonlocal alert_triggered
        alert_triggered = True
        logger.info(f"Alert triggered: {alert_event.message}")
    
    monitor.add_alert_callback(alert_callback)
    
    # Add alert rule and trigger it
    rule = AlertRule(
        name="test_alert",
        metric_name="memory_usage",
        threshold=120.0,
        comparison=">",
        level=AlertLevel.WARNING,
        duration_seconds=1.0
    )
    monitor.add_alert_rule(rule)
    
    # Wait for alert check
    time.sleep(2.0)
    
    # Get dashboard data
    dashboard = monitor.get_dashboard_data()
    logger.info(f"Dashboard metrics: {len(dashboard.get('metrics', {}))} metric types")
    logger.info(f"Active alerts: {dashboard['alerts']['active_count']}")
    
    monitor.shutdown()
    return True

def benchmark_rag_query_performance():
    """Benchmark RAG query performance with and without optimizations."""
    logger.info("Benchmarking RAG query performance...")
    
    try:
        from rag_backend import LocalRAGSystem
        
        # Initialize RAG system
        rag_system = LocalRAGSystem()
        
        # Add a test document
        test_docs = [{
            "title": "Performance Test Document",
            "content": "This is a test document for performance benchmarking. " * 50,
            "source": "performance_test"
        }]
        
        rag_system.add_documents(test_docs)
        
        # Test queries
        test_queries = [
            "What is this document about?",
            "Tell me about performance testing",
            "What information is available?",
            "Explain the content",
            "What is this document about?"  # Repeat for cache test
        ]
        
        # Run benchmark
        query_times = []
        cache_hits = 0
        
        for i, query in enumerate(test_queries):
            start_time = time.time()
            
            # Use async query if available
            if hasattr(rag_system, 'rag_query_async'):
                import asyncio
                result = asyncio.run(rag_system.rag_query_async(query))
            else:
                result = rag_system.rag_query(query)
            
            query_time = time.time() - start_time
            query_times.append(query_time)
            
            if result.get('cache_hit', False):
                cache_hits += 1
            
            logger.info(f"Query {i+1}: {query_time:.3f}s, cache_hit={result.get('cache_hit', False)}")
        
        # Calculate statistics
        avg_time = sum(query_times) / len(query_times)
        min_time = min(query_times)
        max_time = max(query_times)
        
        logger.info(f"\nPerformance Benchmark Results:")
        logger.info(f"Average query time: {avg_time:.3f}s")
        logger.info(f"Min query time: {min_time:.3f}s")
        logger.info(f"Max query time: {max_time:.3f}s")
        logger.info(f"Cache hits: {cache_hits}/{len(test_queries)}")
        
        # Get system diagnostics
        diagnostics = rag_system.get_system_diagnostics()
        perf_metrics = diagnostics.get('performance_metrics', {})
        
        logger.info(f"\nSystem Performance Metrics:")
        if 'cache_stats' in perf_metrics:
            for cache_name, stats in perf_metrics['cache_stats'].items():
                logger.info(f"{cache_name}: hit_rate={stats.get('hit_rate', 0):.1f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"RAG benchmark failed: {e}")
        return False

def test_concurrent_performance():
    """Test performance under concurrent load."""
    logger.info("Testing concurrent performance...")
    
    from performance_cache import get_rag_query_cache
    from performance_monitor import get_performance_monitor
    
    cache = get_rag_query_cache()
    monitor = get_performance_monitor()
    
    def simulate_work(worker_id: int) -> dict:
        """Simulate concurrent work."""
        start_time = time.time()
        
        # Simulate cache operations
        for i in range(10):
            key = f"worker_{worker_id}_key_{i}"
            cache.set(key, f"value_{i}")
            value = cache.get(key)
            
            # Record metrics
            monitor.record_timer(f"worker_operation", (time.time() - start_time) * 1000)
        
        work_time = time.time() - start_time
        return {"worker_id": worker_id, "time": work_time}
    
    # Run concurrent workers
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(simulate_work, i) for i in range(5)]
        results = [future.result() for future in as_completed(futures)]
    
    total_time = time.time() - start_time
    
    # Analyze results
    worker_times = [r["time"] for r in results]
    avg_worker_time = sum(worker_times) / len(worker_times)
    
    logger.info(f"Concurrent test completed in {total_time:.3f}s")
    logger.info(f"Average worker time: {avg_worker_time:.3f}s")
    logger.info(f"Efficiency: {avg_worker_time/total_time:.2f}")
    
    # Get cache stats
    cache_stats = cache.get_stats()
    logger.info(f"Cache performance: hit_rate={cache_stats.get('hit_rate', 0):.1f}%")
    
    return True

async def main():
    """Run all performance tests."""
    logger.info("Starting performance optimization tests...")
    
    tests = [
        ("Caching System", test_caching_system),
        ("Connection Pooling", test_connection_pooling),
        ("Async Caching", test_async_caching),
        ("Performance Monitoring", test_performance_monitoring),
        ("Concurrent Performance", test_concurrent_performance),
        ("RAG Query Benchmark", benchmark_rag_query_performance),
    ]
    
    results = {}
    total_start_time = time.time()
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            test_start_time = time.time()
            
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            test_time = time.time() - test_start_time
            results[test_name] = {"success": result, "time": test_time}
            
            logger.info(f"{test_name}: {'PASSED' if result else 'FAILED'} ({test_time:.3f}s)")
            
        except Exception as e:
            test_time = time.time() - test_start_time
            results[test_name] = {"success": False, "time": test_time, "error": str(e)}
            logger.error(f"{test_name}: FAILED with error: {e}")
    
    total_time = time.time() - total_start_time
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"PERFORMANCE TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    logger.info(f"Tests passed: {passed}/{total}")
    logger.info(f"Total time: {total_time:.3f}s")
    
    for test_name, result in results.items():
        status = "PASSED" if result["success"] else "FAILED"
        time_str = f"{result['time']:.3f}s"
        error_str = f" - {result.get('error', '')}" if not result["success"] else ""
        logger.info(f"  {test_name}: {status} ({time_str}){error_str}")
    
    if passed == total:
        logger.info("\n🎉 All performance optimization tests passed!")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} tests failed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)