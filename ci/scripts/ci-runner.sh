#!/bin/bash

# CI/CD Runner Script
# This script provides common CI operations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to install dependencies
install_deps() {
    log_info "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    log_success "Dependencies installed"
}

# Function to run tests
run_tests() {
    log_info "Running tests..."
    pytest tests/test_ci_cd.py tests/test_basic.py -v --cov=src --cov-report=term-missing
    log_success "Tests completed"
}

# Function to run linting
run_lint() {
    log_info "Running linting checks..."
    
    log_info "Checking code formatting with Black..."
    black --check --diff src/ tests/
    
    log_info "Checking import sorting with isort..."
    isort --check-only --diff src/ tests/
    
    log_info "Running flake8..."
    flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
    
    log_info "Running type checking with mypy..."
    mypy src/ --ignore-missing-imports --no-strict-optional
    
    log_success "Linting completed"
}

# Function to run security checks
run_security() {
    log_info "Running security checks..."
    
    log_info "Running Bandit security scan..."
    bandit -r src/ -f json -o bandit-report.json || true
    
    log_info "Checking for known vulnerabilities..."
    safety check --json --output safety-report.json || true
    
    log_success "Security checks completed"
}

# Function to format code
format_code() {
    log_info "Formatting code..."
    black src/ tests/
    isort src/ tests/
    log_success "Code formatting completed"
}

# Function to build package
build_package() {
    log_info "Building package..."
    python -m build
    log_success "Package build completed"
}

# Function to run full CI pipeline
run_full_ci() {
    log_info "Running full CI pipeline..."
    
    install_deps
    format_code
    run_lint
    run_tests
    run_security
    build_package
    
    log_success "Full CI pipeline completed successfully!"
}

# Function to show help
show_help() {
    echo "CI/CD Runner Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  install     Install dependencies"
    echo "  test        Run tests"
    echo "  lint        Run linting checks"
    echo "  security    Run security checks"
    echo "  format      Format code"
    echo "  build       Build package"
    echo "  full        Run full CI pipeline"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 test     # Run tests only"
    echo "  $0 full     # Run complete CI pipeline"
}

# Main script logic
case "${1:-help}" in
    install)
        install_deps
        ;;
    test)
        install_deps
        run_tests
        ;;
    lint)
        install_deps
        run_lint
        ;;
    security)
        install_deps
        run_security
        ;;
    format)
        install_deps
        format_code
        ;;
    build)
        install_deps
        build_package
        ;;
    full)
        run_full_ci
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
