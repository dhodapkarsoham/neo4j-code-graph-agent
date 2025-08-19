"""Main FastAPI application for the Code Graph Agent."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from src.routes import api, websocket
from src.tools import schema_cache_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Code Graph Agent",
    description="An intelligent agent for analyzing code graphs using Neo4j",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Include API routes
app.include_router(api.router, prefix="/api", tags=["api"])

# WebSocket endpoint
app.add_websocket_route("/ws", websocket.websocket_endpoint)

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting Code Graph Agent...")
    
    # Preload schema cache
    try:
        await schema_cache_manager.preload_schema()
        logger.info("Schema cache preloaded successfully")
    except Exception as e:
        logger.warning(f"Failed to preload schema cache: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Code Graph Agent...")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    from src.components.main_page import get_main_page_html
    return HTMLResponse(content=get_main_page_html())

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "code-graph-agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
