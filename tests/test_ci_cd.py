"""Simple tests to ensure CI/CD pipeline works."""

import pytest


def test_ci_cd_basic():
    """Basic test to ensure CI/CD pipeline works."""
    assert True


def test_imports():
    """Test that all main modules can be imported."""
    try:
        from src.config import settings
        from src.database import db
        from src.tools import ToolRegistry

        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")


def test_config_loading():
    """Test basic configuration loading."""
    from src.config import settings

    assert settings is not None
    assert hasattr(settings, "neo4j_uri")
    assert hasattr(settings, "port")
    assert hasattr(settings, "debug")


def test_tool_registry_creation():
    """Test tool registry can be created."""
    from src.tools import ToolRegistry

    registry = ToolRegistry()
    assert registry is not None
    assert hasattr(registry, "tools")
    assert hasattr(registry, "list_tools")


def test_tool_registry_list_tools():
    """Test tool registry can list tools."""
    from src.tools import ToolRegistry

    registry = ToolRegistry()
    tools = registry.list_tools()

    assert isinstance(tools, list)
    assert len(tools) > 0

    # Check first tool has expected structure
    if tools:
        tool = tools[0]
        assert "name" in tool
        assert "description" in tool
        assert "category" in tool
