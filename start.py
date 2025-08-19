#!/usr/bin/env python3
"""Start script for the Code Graph Agent."""

import uvicorn
from src.app import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
