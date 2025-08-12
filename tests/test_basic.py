"""Basic smoke tests to verify the system is working."""

import pytest
from pathlib import Path
import sys

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all main modules can be imported."""
    try:
        from src.config import settings
        from src.mcp_tools import MCPToolRegistry
        from src.database import db
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")


def test_config_loading():
    """Test basic configuration loading."""
    from src.config import settings
    
    assert settings is not None
    assert hasattr(settings, 'neo4j_uri')
    assert hasattr(settings, 'port')
    assert hasattr(settings, 'debug')


def test_tool_registry_creation():
    """Test tool registry can be created."""
    from src.mcp_tools import MCPToolRegistry
    
    registry = MCPToolRegistry()
    assert registry is not None
    assert hasattr(registry, 'tools')
    assert hasattr(registry, 'list_tools')


def test_tool_registry_list_tools():
    """Test tool registry can list tools."""
    from src.mcp_tools import MCPToolRegistry
    
    registry = MCPToolRegistry()
    tools = registry.list_tools()
    
    assert isinstance(tools, list)
    assert len(tools) > 0
    
    # Check first tool has expected structure
    if tools:
        tool = tools[0]
        assert 'name' in tool
        assert 'description' in tool
        assert 'category' in tool


def test_azure_openai_client_creation():
    """Test Azure OpenAI client can be created."""
    from src.llm import AzureOpenAIClient
    
    client = AzureOpenAIClient()
    assert client is not None
    assert hasattr(client, 'client')
    assert hasattr(client, 'is_configured')


def test_agent_creation():
    """Test agent can be created."""
    from src.agent import CodeGraphAgent
    
    agent = CodeGraphAgent()
    assert agent is not None
    assert hasattr(agent, 'workflow')
    assert hasattr(agent, 'process_query')


def test_basic_functionality():
    """Test basic system functionality."""
    from src.config import settings
    from src.mcp_tools import MCPToolRegistry
    from src.llm import AzureOpenAIClient
    from src.agent import CodeGraphAgent
    
    # Test configuration
    assert settings.port == 8000
    
    # Test tool registry
    registry = MCPToolRegistry()
    tools = registry.list_tools()
    assert len(tools) >= 10  # Should have at least 10 predefined tools
    
    # Test LLM client
    llm_client = AzureOpenAIClient()
    is_configured = llm_client.is_configured()
    assert isinstance(is_configured, bool)
    
    # Test agent
    agent = CodeGraphAgent()
    assert agent.workflow is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
