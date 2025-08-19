#!/usr/bin/env python3
"""
Development server start script for Code Graph Agent
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.web_ui:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info"
    )
