#!/usr/bin/env python3
"""
MCP Code Graph Agent - Startup Script

This script provides a simple way to start the MCP Code Graph Agent
with proper environment setup and error handling.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_environment_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Error: .env file not found")
        print("Please copy env.example to .env and configure your settings")
        sys.exit(1)
    print("✅ Environment file found")

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        import neo4j
        import openai
        import langgraph
        print("✅ All dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

def main():
    """Main startup function."""
    print("🚀 Starting MCP Code Graph Agent...")
    print("=" * 50)
    
    # Pre-flight checks
    check_python_version()
    check_environment_file()
    check_dependencies()
    
    print("\n🔧 Starting the application...")
    print("📊 Web UI will be available at: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the application
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
