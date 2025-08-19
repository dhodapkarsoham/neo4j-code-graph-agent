"""API routes for the Code Graph Agent."""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from src.agent import agent
from src.tools import tool_registry

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/query")
async def query_endpoint(request: Request) -> JSONResponse:
    """Process a user query through the agent."""
    try:
        data = await request.json()
        user_query = data.get("query", "").strip()
        
        if not user_query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        logger.info(f"Processing query: {user_query}")
        
        # Process the query through the agent
        result = await agent.process_query(user_query)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.get("/tools")
async def get_tools() -> JSONResponse:
    """Get list of available tools."""
    try:
        tools = tool_registry.list_tools()
        return JSONResponse(content={"tools": tools})
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting tools: {str(e)}")

@router.post("/tools")
async def create_tool(request: Request) -> JSONResponse:
    """Create a new custom tool."""
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ["name", "description", "category", "query"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Create the tool
        tool_registry.create_tool(
            name=data["name"],
            description=data["description"],
            category=data["category"],
            query=data["query"],
            parameters=data.get("parameters")
        )
        
        return JSONResponse(content={"message": "Tool created successfully"})
        
    except Exception as e:
        logger.error(f"Error creating tool: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating tool: {str(e)}")

@router.delete("/tools/{tool_name}")
async def delete_tool(tool_name: str) -> JSONResponse:
    """Delete a custom tool."""
    try:
        tool_registry.delete_tool(tool_name)
        return JSONResponse(content={"message": f"Tool '{tool_name}' deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting tool: {str(e)}")

@router.post("/text2cypher")
async def text2cypher_direct(request: Request) -> JSONResponse:
    """Direct text2cypher endpoint for testing."""
    try:
        data = await request.json()
        question = data.get("question", "").strip()
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Get dynamic schema from tools module
        from src.tools import tool_registry
        schema_info = await tool_registry._get_database_schema_context()
        
        # Try to use LLM if available
        try:
            from src.llm import llm_client
            if llm_client.client:
                # Use LLM for better query generation
                result = await tool_registry.async_execute_tool("text2cypher", {"question": question})
            else:
                # Fallback to basic query generation
                result = tool_registry.execute_tool("text2cypher", {"question": question})
        except Exception as e:
            logger.warning(f"LLM not available, using fallback: {e}")
            result = tool_registry.execute_tool("text2cypher", {"question": question})
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error in text2cypher: {e}")
        raise HTTPException(status_code=500, detail=f"Error in text2cypher: {str(e)}")

@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(content={"status": "healthy", "service": "code-graph-agent"})
