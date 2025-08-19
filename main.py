#!/usr/bin/env python3
"""
Code Graph Agent - Main Entry Point
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Main application entry point."""
    print("🚀 Starting Code Graph Agent...")
    print("=" * 50)
    
    # Check environment setup
    try:
        from src.config import settings
        print("✅ Environment setup complete")
    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        sys.exit(1)
    
    print("🔧 Starting the application...")
    print("📊 Web UI will be available at: http://localhost:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        import uvicorn
        
        # Start the app using import string for reload functionality
        uvicorn.run(
            "src.web_ui:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["src"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
