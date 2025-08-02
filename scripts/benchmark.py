#!/usr/bin/env python3
"""
Performance benchmarking for the Local RAG System
Tests token usage, response times, and retrieval accuracy
"""

import requests
import time
import json
import statistics
from typing import Dict, List, Tuple
import concurrent.futures

class RAGBenchmark:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.test_documents = [
            {
                "title": "Machine Learning Fundamentals",
                "content": """Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed. It involves algorithms that can identify patterns, make predictions, and improve their performance over time. There are three main types: supervised learning (using labeled data), unsupervised learning (finding patterns in unlabeled data), and reinforcement learning (learning through rewards and penalties). Popular applications include image recognition, natural language processing, recommendation systems, and autonomous vehicles.""",
                "source": "benchmark"
            },
            {
                "title": "Docker Container Technology",
                "content": """Docker is a containerization platform that packages applications and their dependencies into lightweight, portable containers. Unlike virtual machines, containers share the host OS kernel, making them more efficient in terms of resource usage. Docker containers ensure consistency across development, testing, and production environments. Key benefits include faster deployment, better resource utilization, easier scaling, and improved DevOps workflows. Docker uses images as blueprints for containers, and these images can be stored in registries like Docker Hub for easy sharing and distribution.""",
                "source": "benchmark"
            },
            {
                "title": "Cloud Computing Architecture",
                "content": """Cloud computing delivers computing services over the internet, including storage, processing power, and software applications. The main service models are Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS). Cloud deployment models include public, private, hybrid, and multi-cloud configurations. Benefits include cost efficiency, scalability, flexibility, and reduced IT maintenance. Major cloud providers include Amazon Web Services (AWS), Microsoft Azure, and Google Cloud Platform. Organizations can migrate workloads to the cloud using various strategies like lift-and-shift or cloud-native approaches.""",
                "source": "benchmark"
            },
            {
                "title": "Microservices Architecture",
                "content": """Microservices architecture is a design approach that structures applications as a collection of loosely coupled, independently deployable services. Each service focuses on a specific business function and communicates through well-defined APIs. This contrasts with monolithic architecture where all components are tightly integrated. Benefits include improved scalability, technology diversity, fault isolation, and faster development cycles. However, microservices also introduce complexity in areas like service discovery, distributed data management, and network communication. Container technologies like Docker and orchestration platforms like Kubernetes are commonly used to manage microservices deployments.""",
                "source": "benchmark"
            }
        ]
        
        self.test_queries = [
            "What is machine learning?",
            "How do Docker containers work?",
            "What are the benefits of cloud computing?",
            "Explain microservices architecture",
            "Compare containers and virtual machines",
            "What are the types of machine learning?",
            "How does cloud computing save costs?",
            "What challenges do microservices face?"
        ]
    
    def setup_test_data(self) -> bool:
        """Upload test documents for benchmarking"""
        print("📄 Setting up benchmark data...")
        
        try:
            response = requests.post(
                f"{self.api_url}/documents",
                json=self.test_documents,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Uploaded {result.get('count', 0)} test documents")
                return True
            else:
                print(f"  ❌ Failed to upload documents: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Setup failed: {e}")
            return False
    
    def measure_response_time(self, query: str, max_chunks: int = 3) -> Tuple[float, Dict]:
        """Measure response time for a single query"""
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/query",
                json={"question": query, "max_chunks": max_chunks},
                timeout=60
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                return response_time, result
            else:
                return response_time, {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            end_time = time.time()
            return end_time - start_time, {"error": str(e)}
    
    def benchmark_response_times(self) -> Dict:
        """Benchmark response times for all test queries"""
        print("⏱️ Benchmarking response times...")
        
        response_times = []
        successful_queries = 0
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"  Query {i}/{len(self.test_queries)}: {query[:30]}...")
            
            response_time, result = self.measure_response_time(query)
            response_times.append(response_time)
            
            if "error" not in result:
                successful_queries += 1
                print(f"    ✅ {response_time:.2f}s - {result.get('context_used', 0)} chunks, {result.get('context_tokens', 0)} tokens")
            else:
                print(f"    ❌ {response_time:.2f}s - {result.get('error', 'Unknown error')}")
        
        if response_times:
            stats = {
                "total_queries": len(self.test_queries),
                "successful_queries": successful_queries,
                "success_rate": successful_queries / len(self.test_queries),
                "avg_response_time": statistics.mean(response_times),
                "median_response_time": statistics.median(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "std_dev": statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
        else:
            stats = {"error": "No response times recorded"}
        
        return stats
    
    def benchmark_token_efficiency(self) -> Dict:
        """Benchmark token usage efficiency"""
        print("🔤 Benchmarking token efficiency...")
        
        token_metrics = []
        
        for query in self.test_queries[:4]:  # Sample subset for efficiency
            _, result = self.measure_response_time(query)
            
            if "error" not in result:
                token_metrics.append({
                    "context_tokens": result.get("context_tokens", 0),
                    "context_used": result.get("context_used", 0),
                    "efficiency_ratio": result.get("efficiency_ratio", 0)
                })
        
        if token_metrics:
            avg_tokens = statistics.mean([m["context_tokens"] for m in token_metrics])
            avg_chunks = statistics.mean([m["context_used"] for m in token_metrics])
            avg_efficiency = statistics.mean([m["efficiency_ratio"] for m in token_metrics])
            
            stats = {
                "avg_context_tokens": avg_tokens,
                "avg_chunks_used": avg_chunks,
                "avg_efficiency_ratio": avg_efficiency,
                "token_per_chunk": avg_tokens / avg_chunks if avg_chunks > 0 else 0
            }
        else:
            stats = {"error": "No token metrics collected"}
        
        return stats
    
    def benchmark_concurrent_queries(self, concurrent_users: int = 3) -> Dict:
        """Benchmark concurrent query performance"""
        print(f"👥 Benchmarking {concurrent_users} concurrent queries...")
        
        def execute_query(query_info):
            query_id, query = query_info
            start_time = time.time()
            response_time, result = self.measure_response_time(query)
            return {
                "query_id": query_id,
                "query": query[:50],
                "response_time": response_time,
                "success": "error" not in result,
                "start_time": start_time
            }
        
        # Prepare concurrent queries
        query_batch = [(i, self.test_queries[i % len(self.test_queries)]) 
                      for i in range(concurrent_users)]
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            results = list(executor.map(execute_query, query_batch))
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        successful_queries = sum(1 for r in results if r["success"])
        response_times = [r["response_time"] for r in results if r["success"]]
        
        if response_times:
            stats = {
                "concurrent_users": concurrent_users,
                "total_duration": total_duration,
                "successful_queries": successful_queries,
                "success_rate": successful_queries / len(results),
                "queries_per_second": len(results) / total_duration,
                "avg_response_time": statistics.mean(response_times),
                "max_response_time": max(response_times),
                "throughput": successful_queries / total_duration
            }
        else:
            stats = {"error": "No successful concurrent queries"}
        
        return stats
    
    def run_full_benchmark(self) -> Dict:
        """Run complete benchmark suite"""
        print("🏃 Starting RAG System Performance Benchmark\n")
        
        # Setup test data
        if not self.setup_test_data():
            return {"error": "Failed to setup test data"}
        
        time.sleep(2)  # Allow indexing to complete
        
        benchmark_results = {}
        
        # Response time benchmark
        print(f"\n{'-'*50}")
        benchmark_results["response_times"] = self.benchmark_response_times()
        
        # Token efficiency benchmark
        print(f"\n{'-'*50}")
        benchmark_results["token_efficiency"] = self.benchmark_token_efficiency()
        
        # Concurrent query benchmark
        print(f"\n{'-'*50}")
        benchmark_results["concurrent_performance"] = self.benchmark_concurrent_queries()
        
        return benchmark_results
    
    def print_benchmark_report(self, results: Dict):
        """Print formatted benchmark report"""
        print(f"\n{'='*60}")
        print("🚀 RAG SYSTEM PERFORMANCE REPORT")
        print(f"{'='*60}")
        
        # Response Times
        if "response_times" in results and "error" not in results["response_times"]:
            rt = results["response_times"]
            print(f"\n📊 RESPONSE TIME METRICS")
            print(f"  Success Rate: {rt['success_rate']:.1%}")
            print(f"  Average Time: {rt['avg_response_time']:.2f}s")
            print(f"  Median Time:  {rt['median_response_time']:.2f}s")
            print(f"  Range:        {rt['min_response_time']:.2f}s - {rt['max_response_time']:.2f}s")
            print(f"  Std Dev:      {rt['std_dev']:.2f}s")
        
        # Token Efficiency
        if "token_efficiency" in results and "error" not in results["token_efficiency"]:
            te = results["token_efficiency"]
            print(f"\n🔤 TOKEN EFFICIENCY METRICS")
            print(f"  Avg Context Tokens: {te['avg_context_tokens']:.0f}")
            print(f"  Avg Chunks Used:    {te['avg_chunks_used']:.1f}")
            print(f"  Tokens per Chunk:   {te['token_per_chunk']:.0f}")
            print(f"  Efficiency Ratio:   {te['avg_efficiency_ratio']:.3f}")
        
        # Concurrent Performance
        if "concurrent_performance" in results and "error" not in results["concurrent_performance"]:
            cp = results["concurrent_performance"]
            print(f"\n👥 CONCURRENT PERFORMANCE METRICS")
            print(f"  Concurrent Users:   {cp['concurrent_users']}")
            print(f"  Success Rate:       {cp['success_rate']:.1%}")
            print(f"  Throughput:         {cp['throughput']:.2f} queries/sec")
            print(f"  Avg Response Time:  {cp['avg_response_time']:.2f}s")
            print(f"  Max Response Time:  {cp['max_response_time']:.2f}s")
        
        # Performance Assessment
        print(f"\n🎯 PERFORMANCE ASSESSMENT")
        
        if "response_times" in results and "error" not in results["response_times"]:
            avg_time = results["response_times"]["avg_response_time"]
            if avg_time < 2.0:
                print("  Response Time: 🟢 Excellent (< 2s)")
            elif avg_time < 5.0:
                print("  Response Time: 🟡 Good (2-5s)")
            else:
                print("  Response Time: 🔴 Needs Improvement (> 5s)")
        
        if "token_efficiency" in results and "error" not in results["token_efficiency"]:
            efficiency = results["token_efficiency"]["avg_efficiency_ratio"]
            if efficiency > 2.0:
                print("  Token Efficiency: 🟢 Excellent")
            elif efficiency > 1.0:
                print("  Token Efficiency: 🟡 Good")
            else:
                print("  Token Efficiency: 🔴 Needs Improvement")
        
        print(f"\n{'='*60}")

def main():
    """Main benchmark runner"""
    benchmark = RAGBenchmark()
    
    print("⏳ Waiting for system to be ready...")
    time.sleep(5)
    
    results = benchmark.run_full_benchmark()
    benchmark.print_benchmark_report(results)

if __name__ == "__main__":
    main()