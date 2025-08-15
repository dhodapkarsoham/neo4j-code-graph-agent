#!/usr/bin/env python3
"""
Test runner for Code Graph Agent.

This script provides an easy way to run all tests or specific test categories.
"""

import sys
import subprocess
import argparse
from pathlib import Path
import os

# Redirect standard error to null device to suppress error messages
sys.stderr = open(os.devnull, 'w')


def run_tests(test_pattern=None, verbose=False, coverage=False):
    """Run tests with the specified options."""
    cmd = ["python", "-m", "pytest"]
    
    if test_pattern:
        cmd.append(test_pattern)
    else:
        cmd.append("tests/")
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    print(f"Running tests with command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print(f"❌ Tests failed with exit code {e.returncode}")
        return False


def run_unit_tests(verbose=False):
    """Run unit tests only."""
    print("🧪 Running Unit Tests...")
    return run_tests("tests/test_*.py", verbose=verbose)


def run_integration_tests(verbose=False):
    """Run integration tests only."""
    print("🔗 Running Integration Tests...")
    return run_tests("tests/test_integration.py", verbose=verbose)


def run_component_tests(verbose=False):
    """Run component-specific tests."""
    print("🔧 Running Component Tests...")
    components = [
        "tests/test_config.py",
        "tests/test_tools.py", 
        "tests/test_llm.py",
        "tests/test_agent.py",
        "tests/test_database.py"
    ]
    
    success = True
    for component in components:
        print(f"\n📋 Testing {Path(component).stem}...")
        if not run_tests(component, verbose=verbose):
            success = False
    
    return success


def main():
    """Main function for test runner."""
    parser = argparse.ArgumentParser(description="Run Code Graph Agent tests")
    parser.add_argument(
        "--basic", 
        action="store_true", 
        help="Run basic smoke tests only (default)"
    )
    parser.add_argument(
        "--unit", 
        action="store_true", 
        help="Run unit tests only"
    )
    parser.add_argument(
        "--integration", 
        action="store_true", 
        help="Run integration tests only"
    )
    parser.add_argument(
        "--components", 
        action="store_true", 
        help="Run component tests only"
    )
    parser.add_argument(
        "--full", 
        action="store_true", 
        help="Run full test suite (may have issues)"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true", 
        help="Generate coverage report"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "pattern", 
        nargs="?", 
        help="Test pattern to run (e.g., 'test_config')"
    )
    
    args = parser.parse_args()
    
    print("🚀 Code Graph Agent Test Runner")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Error: 'tests' directory not found. Please run from the project root.")
        sys.exit(1)
    
    success = False
    
    if args.basic:
        print("🧪 Running Basic Smoke Tests...")
        success = run_tests("tests/test_basic.py", verbose=args.verbose, coverage=args.coverage)
    elif args.unit:
        success = run_unit_tests(verbose=args.verbose)
    elif args.integration:
        success = run_integration_tests(verbose=args.verbose)
    elif args.components:
        success = run_component_tests(verbose=args.verbose)
    elif args.full:
        print("🧪 Running Full Test Suite...")
        success = run_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.pattern:
        print(f"🔍 Running tests matching pattern: {args.pattern}")
        success = run_tests(f"tests/test_{args.pattern}.py", verbose=args.verbose, coverage=args.coverage)
    else:
        print("🧪 Running Basic Smoke Tests (default)...")
        success = run_tests("tests/test_basic.py", verbose=args.verbose, coverage=args.coverage)
    
    if success:
        print("\n🎉 Test execution completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test execution failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
