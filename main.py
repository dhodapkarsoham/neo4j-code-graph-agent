#!/usr/bin/env python3
"""
Code Graph Agent - Main Application Entry Point

This is the main entry point for the Code Graph Agent application.
It provides a simple way to start the FastAPI server with proper
environment setup and error handling.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_environment():
    """Check environment setup."""
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Error: .env file not found")
        print("Please copy env.example to .env and configure your settings")
        sys.exit(1)
    
    print("✅ Environment setup complete")

def main():
    """Main application entry point."""
    print("🚀 Starting Code Graph Agent...")
    print("=" * 50)
    
    # Check environment
    check_environment()
    
    print("\n🔧 Starting the application...")
    print("📊 Web UI will be available at: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Import and start the app
        from src.app import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
