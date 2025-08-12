"""Tests for MCP tools registry."""

import pytest
import json
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from src.mcp_tools import MCPTool, MCPToolRegistry


class TestMCPTool:
    """Test cases for MCPTool class."""

    def test_mcp_tool_creation(self):
        """Test MCPTool creation with all parameters."""
        tool = MCPTool(
            name="test_tool",
            description="Test tool description",
            category="Test",
            query="MATCH (n) RETURN n",
            parameters={"param1": "value1"}
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "Test tool description"
        assert tool.category == "Test"
        assert tool.query == "MATCH (n) RETURN n"
        assert tool.parameters == {"param1": "value1"}

    def test_mcp_tool_creation_without_parameters(self):
        """Test MCPTool creation without optional parameters."""
        tool = MCPTool(
            name="test_tool",
            description="Test tool description",
            category="Test",
            query="MATCH (n) RETURN n"
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "Test tool description"
        assert tool.category == "Test"
        assert tool.query == "MATCH (n) RETURN n"
        assert tool.parameters is None


class TestMCPToolRegistry:
    """Test cases for MCPToolRegistry class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.tools_file = Path(self.temp_dir) / "tools.json"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.mcp_tools.MCPToolRegistry._load_all_tools')
    def test_registry_initialization(self, mock_load_tools):
        """Test MCPToolRegistry initialization."""
        mock_tools = [
            MCPTool(name="tool1", description="Tool 1", category="Test", query="MATCH (n) RETURN n"),
            MCPTool(name="tool2", description="Tool 2", category="Test", query="MATCH (m) RETURN m")
        ]
        mock_load_tools.return_value = mock_tools
        
        with patch.object(MCPToolRegistry, 'tools_file', self.tools_file):
            registry = MCPToolRegistry()
            
            assert len(registry.tools) == 2
            assert registry.tools[0].name == "tool1"
            assert registry.tools[1].name == "tool2"

    def test_get_tools_by_category(self):
        """Test getting tools by category."""
        registry = MCPToolRegistry()
        registry.tools = [
            MCPTool(name="security_tool", description="Security tool", category="Security", query="MATCH (n) RETURN n"),
            MCPTool(name="quality_tool", description="Quality tool", category="Quality", query="MATCH (m) RETURN m"),
            MCPTool(name="custom_tool", description="Custom tool", category="Custom", query="MATCH (o) RETURN o")
        ]
        
        security_tools = registry.get_tools_by_category("Security")
        assert len(security_tools) == 1
        assert security_tools[0].name == "security_tool"
        
        custom_tools = registry.get_tools_by_category("Custom")
        assert len(custom_tools) == 1
        assert custom_tools[0].name == "custom_tool"

    def test_get_tool_by_name(self):
        """Test getting tool by name."""
        registry = MCPToolRegistry()
        registry.tools = [
            MCPTool(name="tool1", description="Tool 1", category="Test", query="MATCH (n) RETURN n"),
            MCPTool(name="tool2", description="Tool 2", category="Test", query="MATCH (m) RETURN m")
        ]
        
        tool = registry.get_tool_by_name("tool1")
        assert tool is not None
        assert tool.name == "tool1"
        assert tool.description == "Tool 1"
        
        # Test non-existent tool
        tool = registry.get_tool_by_name("non_existent")
        assert tool is None

    def test_add_tool_success(self):
        """Test successfully adding a new tool."""
        registry = MCPToolRegistry()
        registry.tools = []
        
        with patch.object(registry, '_save_all_tools') as mock_save:
            new_tool = registry.add_tool(
                name="new_tool",
                description="New tool description",
                category="Custom",
                query="MATCH (n) RETURN n"
            )
            
            assert new_tool.name == "new_tool"
            assert new_tool.description == "New tool description"
            assert new_tool.category == "Custom"
            assert len(registry.tools) == 1
            assert registry.tools[0].name == "new_tool"
            mock_save.assert_called_once()

    def test_add_tool_duplicate_name(self):
        """Test adding tool with duplicate name raises error."""
        registry = MCPToolRegistry()
        registry.tools = [
            MCPTool(name="existing_tool", description="Existing tool", category="Test", query="MATCH (n) RETURN n")
        ]
        
        with pytest.raises(ValueError, match="Tool with name 'existing_tool' already exists"):
            registry.add_tool(
                name="existing_tool",
                description="New tool description",
                category="Custom",
                query="MATCH (n) RETURN n"
            )

    def test_remove_tool_success(self):
        """Test successfully removing a custom tool."""
        registry = MCPToolRegistry()
        registry.tools = [
            MCPTool(name="custom_tool", description="Custom tool", category="Custom", query="MATCH (n) RETURN n"),
            MCPTool(name="predefined_tool", description="Predefined tool", category="Security", query="MATCH (m) RETURN m")
        ]
        
        with patch.object(registry, '_save_all_tools') as mock_save:
            result = registry.remove_tool("custom_tool")
            
            assert result is True
            assert len(registry.tools) == 1
            assert registry.tools[0].name == "predefined_tool"
            mock_save.assert_called_once()

    def test_remove_tool_not_found(self):
        """Test removing non-existent tool returns False."""
        registry = MCPToolRegistry()
        registry.tools = [
            MCPTool(name="custom_tool", description="Custom tool", category="Custom", query="MATCH (n) RETURN n")
        ]
        
        result = registry.remove_tool("non_existent")
        assert result is False
        assert len(registry.tools) == 1  # Tool list unchanged

    def test_remove_predefined_tool_fails(self):
        """Test that removing predefined tools fails."""
        registry = MCPToolRegistry()
        registry.tools = [
            MCPTool(name="predefined_tool", description="Predefined tool", category="Security", query="MATCH (n) RETURN n")
        ]
        
        result = registry.remove_tool("predefined_tool")
        assert result is False
        assert len(registry.tools) == 1  # Tool list unchanged

    def test_list_tools(self):
        """Test listing all tools."""
        registry = MCPToolRegistry()
        registry.tools = [
            MCPTool(name="tool1", description="Tool 1", category="Test", query="MATCH (n) RETURN n"),
            MCPTool(name="tool2", description="Tool 2", category="Test", query="MATCH (m) RETURN m", parameters={"param": "value"})
        ]
        
        tools_list = registry.list_tools()
        
        assert len(tools_list) == 2
        assert tools_list[0]["name"] == "tool1"
        assert tools_list[0]["description"] == "Tool 1"
        assert tools_list[0]["category"] == "Test"
        assert tools_list[0]["has_parameters"] is False
        
        assert tools_list[1]["name"] == "tool2"
        assert tools_list[1]["has_parameters"] is True

    def test_load_all_tools_from_file(self):
        """Test loading tools from JSON file."""
        tools_data = [
            {
                "name": "tool1",
                "description": "Tool 1",
                "category": "Test",
                "query": "MATCH (n) RETURN n",
                "parameters": None
            },
            {
                "name": "tool2",
                "description": "Tool 2",
                "category": "Custom",
                "query": "MATCH (m) RETURN m",
                "parameters": {"param": "value"}
            }
        ]
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(tools_data))):
                with patch.object(MCPToolRegistry, 'tools_file', self.tools_file):
                    registry = MCPToolRegistry()
                    
                    assert len(registry.tools) == 2
                    assert registry.tools[0].name == "tool1"
                    assert registry.tools[1].name == "tool2"
                    assert registry.tools[1].parameters == {"param": "value"}

    def test_load_all_tools_file_not_exists(self):
        """Test loading tools when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.object(MCPToolRegistry, 'tools_file', self.tools_file):
                with patch.object(MCPToolRegistry, '_get_predefined_tools') as mock_predefined:
                    mock_predefined.return_value = [
                        MCPTool(name="predefined", description="Predefined", category="Test", query="MATCH (n) RETURN n")
                    ]
                    
                    with patch.object(MCPToolRegistry, '_save_all_tools') as mock_save:
                        registry = MCPToolRegistry()
                        
                        assert len(registry.tools) == 1
                        assert registry.tools[0].name == "predefined"
                        mock_save.assert_called_once()

    def test_save_all_tools(self):
        """Test saving tools to JSON file."""
        registry = MCPToolRegistry()
        registry.tools = [
            MCPTool(name="tool1", description="Tool 1", category="Test", query="MATCH (n) RETURN n"),
            MCPTool(name="tool2", description="Tool 2", category="Custom", query="MATCH (m) RETURN m")
        ]
        
        with patch.object(registry, 'tools_file', self.tools_file):
            with patch('builtins.open', mock_open()) as mock_file:
                registry._save_all_tools()
                
                mock_file.assert_called_once_with(self.tools_file, 'w')
                # Verify that json.dump was called with the correct data
                mock_file().write.assert_called()

    @patch('src.mcp_tools.db')
    def test_execute_tool_success(self, mock_db):
        """Test successful tool execution."""
        registry = MCPToolRegistry()
        registry.tools = [
            MCPTool(name="test_tool", description="Test tool", category="Test", query="MATCH (n) RETURN n")
        ]
        
        mock_results = [{"node": "data"}]
        mock_db.execute_query.return_value = mock_results
        
        result = registry.execute_tool("test_tool")
        
        assert result["tool_name"] == "test_tool"
        assert result["description"] == "Test tool"
        assert result["category"] == "Test"
        assert result["results"] == mock_results
        assert result["result_count"] == 1
        mock_db.execute_query.assert_called_once_with("MATCH (n) RETURN n", {})

    def test_execute_tool_not_found(self):
        """Test executing non-existent tool raises error."""
        registry = MCPToolRegistry()
        registry.tools = []
        
        with pytest.raises(ValueError, match="Tool 'non_existent' not found"):
            registry.execute_tool("non_existent")


if __name__ == "__main__":
    pytest.main([__file__])
