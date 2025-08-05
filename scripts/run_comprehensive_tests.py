#!/usr/bin/env python3
"""
Comprehensive test execution script for RAG system.

Runs all test categories with appropriate configurations and generates
detailed reports for quality assurance and system validation.

Authored by: QA/Test Engineer (Darren Fong)
Date: 2025-08-05
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse


class TestRunner:
    """Comprehensive test runner for RAG system."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.test_results = {}
        self.start_time = time.time()
        
    def run_test_category(self, category: str, description: str, markers: List[str], 
                         additional_args: List[str] = None) -> Dict[str, Any]:
        """Run a specific test category."""
        print(f"\n{'='*60}")
        print(f"Running {description}")
        print(f"{'='*60}")
        
        # Build pytest command
        cmd = ["python", "-m", "pytest"]
        
        # Add markers
        if markers:
            marker_expr = " or ".join(markers)
            cmd.extend(["-m", marker_expr])
        
        # Add additional arguments
        if additional_args:
            cmd.extend(additional_args)
        
        # Common arguments
        cmd.extend([
            "--tb=short",
            "--verbose",
            f"--junit-xml=test-results-{category}.xml",
            f"--html=test-report-{category}.html",
            "--self-contained-html"
        ])
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            duration = time.time() - start_time
            
            return {
                "category": category,
                "description": description,
                "duration": duration,
                "return_code": result.returncode,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                "category": category,
                "description": description,
                "duration": duration,
                "return_code": -1,
                "success": False,
                "error": "Test execution timed out",
                "command": " ".join(cmd)
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "category": category,
                "description": description,
                "duration": duration,
                "return_code": -1,
                "success": False,
                "error": str(e),
                "command": " ".join(cmd)
            }

    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests."""
        return self.run_test_category(
            "unit",
            "Unit Tests - Individual Component Testing",
            ["unit"],
            ["--cov=app", "--cov-report=term-missing"]
        )

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        return self.run_test_category(
            "integration",
            "Integration Tests - Component Interaction Testing",
            ["integration"],
            ["--maxfail=3"]
        )

    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests."""
        return self.run_test_category(
            "performance",
            "Performance Tests - Load and Concurrent User Testing",
            ["performance"],
            ["--maxfail=2", "--timeout=600"]
        )

    def run_accessibility_tests(self) -> Dict[str, Any]:
        """Run accessibility tests."""
        return self.run_test_category(
            "accessibility",
            "Accessibility Tests - WCAG Compliance and UI Accessibility",
            ["accessibility"],
            ["--maxfail=2"]
        )

    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests."""
        return self.run_test_category(
            "security",
            "Security Tests - Vulnerability and Rate Limiting Testing",
            ["security"],
            ["--maxfail=3"]
        )

    def run_stress_tests(self) -> Dict[str, Any]:
        """Run stress tests."""
        return self.run_test_category(
            "stress",
            "Stress Tests - Resource Exhaustion and Memory Leak Detection",
            ["stress"],
            ["--maxfail=1", "--timeout=900"]
        )

    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests."""
        return self.run_test_category(
            "e2e",
            "End-to-End Tests - Complete User Journey Testing",
            ["e2e"],
            ["--maxfail=2", "--timeout=600"]
        )

    def run_regression_tests(self) -> Dict[str, Any]:
        """Run regression tests."""
        return self.run_test_category(
            "regression",
            "Regression Tests - Critical Path and System Reliability",
            ["regression"],
            ["--maxfail=2"]
        )

    def run_comprehensive_suite(self, categories: List[str] = None) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        if categories is None:
            categories = [
                "unit", "integration", "performance", "accessibility", 
                "security", "stress", "e2e", "regression"
            ]
        
        print(f"Starting comprehensive test suite execution...")
        print(f"Test categories: {', '.join(categories)}")
        print(f"Project root: {self.project_root}")
        
        # Test category runners
        runners = {
            "unit": self.run_unit_tests,
            "integration": self.run_integration_tests,
            "performance": self.run_performance_tests,
            "accessibility": self.run_accessibility_tests,
            "security": self.run_security_tests,
            "stress": self.run_stress_tests,
            "e2e": self.run_e2e_tests,
            "regression": self.run_regression_tests
        }
        
        results = {}
        
        for category in categories:
            if category in runners:
                print(f"\n[{time.strftime('%H:%M:%S')}] Starting {category} tests...")
                result = runners[category]()
                results[category] = result
                
                if result["success"]:
                    print(f"✅ {category.upper()} tests completed successfully in {result['duration']:.1f}s")
                else:
                    print(f"❌ {category.upper()} tests failed after {result['duration']:.1f}s")
                    if "error" in result:
                        print(f"   Error: {result['error']}")
            else:
                print(f"⚠️  Unknown test category: {category}")
        
        total_duration = time.time() - self.start_time
        
        # Generate summary
        summary = self.generate_summary(results, total_duration)
        
        return {
            "summary": summary,
            "results": results,
            "total_duration": total_duration
        }

    def generate_summary(self, results: Dict[str, Any], total_duration: float) -> Dict[str, Any]:
        """Generate test execution summary."""
        successful_categories = [cat for cat, result in results.items() if result["success"]]
        failed_categories = [cat for cat, result in results.items() if not result["success"]]
        
        total_tests = len(results)
        success_rate = len(successful_categories) / total_tests if total_tests > 0 else 0
        
        summary = {
            "total_categories": total_tests,
            "successful_categories": len(successful_categories),
            "failed_categories": len(failed_categories),
            "success_rate": success_rate,
            "total_duration": total_duration,
            "successful": successful_categories,
            "failed": failed_categories
        }
        
        return summary

    def generate_report(self, results: Dict[str, Any], output_file: str = "comprehensive_test_report.json"):
        """Generate comprehensive test report."""
        report = {
            "test_execution": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "project_root": str(self.project_root),
                "execution_summary": results["summary"],
                "total_duration": results["total_duration"]
            },
            "category_results": {}
        }
        
        for category, result in results["results"].items():
            report["category_results"][category] = {
                "description": result["description"],
                "duration": result["duration"],
                "success": result["success"],
                "return_code": result["return_code"],
                "command": result["command"]
            }
            
            if "error" in result:
                report["category_results"][category]["error"] = result["error"]
        
        # Save report
        output_path = self.project_root / output_file
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Comprehensive test report saved to: {output_path}")
        
        return report

    def print_summary(self, results: Dict[str, Any]):
        """Print execution summary."""
        summary = results["summary"]
        
        print(f"\n{'='*60}")
        print("COMPREHENSIVE TEST EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Total test categories: {summary['total_categories']}")
        print(f"Successful categories: {summary['successful_categories']}")
        print(f"Failed categories: {summary['failed_categories']}")
        print(f"Success rate: {summary['success_rate']:.1%}")
        print(f"Total execution time: {summary['total_duration']:.1f} seconds")
        
        if summary["successful"]:
            print(f"\n✅ Successful categories: {', '.join(summary['successful'])}")
        
        if summary["failed"]:
            print(f"\n❌ Failed categories: {', '.join(summary['failed'])}")
        
        print(f"\n{'='*60}")
        
        # Performance insights
        category_times = {cat: result["duration"] for cat, result in results["results"].items()}
        slowest_category = max(category_times.items(), key=lambda x: x[1])
        fastest_category = min(category_times.items(), key=lambda x: x[1])
        
        print("PERFORMANCE INSIGHTS")
        print(f"{'='*60}")
        print(f"Slowest category: {slowest_category[0]} ({slowest_category[1]:.1f}s)")
        print(f"Fastest category: {fastest_category[0]} ({fastest_category[1]:.1f}s)")
        
        avg_duration = sum(category_times.values()) / len(category_times)
        print(f"Average category duration: {avg_duration:.1f}s")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Run comprehensive RAG system tests")
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["unit", "integration", "performance", "accessibility", "security", "stress", "e2e", "regression"],
        help="Test categories to run (default: all)"
    )
    parser.add_argument(
        "--output",
        default="comprehensive_test_report.json",
        help="Output file for test report"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(args.project_root)
    
    try:
        # Run tests
        results = runner.run_comprehensive_suite(args.categories)
        
        # Print summary
        runner.print_summary(results)
        
        # Generate report
        runner.generate_report(results, args.output)
        
        # Exit with appropriate code
        if results["summary"]["success_rate"] == 1.0:
            print("\n🎉 All test categories passed successfully!")
            sys.exit(0)
        else:
            print(f"\n⚠️  {results['summary']['failed_categories']} test categories failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test execution failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()