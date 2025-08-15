"""Code Analysis Tools for Neo4j Code Graph Analysis."""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.database import db

logger = logging.getLogger(__name__)


@dataclass
class CodeTool:
    """Code Analysis Tool definition."""

    name: str
    description: str
    category: str
    query: str
    parameters: Optional[Dict[str, Any]] = None


class ToolRegistry:
    """Registry for Code Analysis tools."""

    def __init__(self):
        """Initialize tool registry and load tools from JSON file."""
        self.tools_file = Path(__file__).parent.parent / "tools.json"
        self.tools = self._load_all_tools()

    def _create_empty_tools_file(self):
        """Create an empty tools.json file with basic structure."""
        empty_tools = []
        self._save_all_tools(empty_tools)
        logger.info(f"Created empty tools file at {self.tools_file}")

    def _load_all_tools(self) -> List[CodeTool]:
        """Load all tools from JSON file. Create empty file if it doesn't exist."""
        if self.tools_file.exists():
            try:
                with open(self.tools_file, "r") as f:
                    tools_data = json.load(f)
                    tools = [CodeTool(**tool_data) for tool_data in tools_data]
                logger.info(f"Loaded {len(tools)} tools from {self.tools_file}")
                return tools
            except Exception as e:
                logger.error(f"Error loading tools from {self.tools_file}: {e}")
                logger.warning("Creating new empty tools file due to corruption")

        # If file doesn't exist or is corrupted, create empty tools file
        self._create_empty_tools_file()
        return []

    def _save_all_tools(self, tools: List[CodeTool] = None):
        """Save all tools to JSON file."""
        if tools is None:
            tools = self.tools

        try:
            tools_data = [asdict(tool) for tool in tools]
            with open(self.tools_file, "w") as f:
                json.dump(tools_data, f, indent=2)
            logger.info(f"Saved {len(tools)} tools to {self.tools_file}")
        except Exception as e:
            logger.error(f"Error saving tools: {e}")

    def get_tools_by_category(self, category: str) -> List[CodeTool]:
        """Get tools by category."""
        return [tool for tool in self.tools if tool.category == category]

    def get_tool_by_name(self, name: str) -> Optional[CodeTool]:
        """Get tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def add_tool(
        self,
        name: str,
        description: str,
        category: str,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> CodeTool:
        """Add a new custom tool to the registry."""
        # Check if tool already exists
        if self.get_tool_by_name(name):
            raise ValueError(f"Tool with name '{name}' already exists")

        # Create new tool
        new_tool = CodeTool(
            name=name,
            description=description,
            category=category,
            query=query,
            parameters=parameters,
        )

        # Add to tools list
        self.tools.append(new_tool)

        # Save all tools to file
        self._save_all_tools()

        logger.info(f"Added new tool: {name} ({category})")
        return new_tool

    def remove_tool(self, name: str) -> bool:
        """Remove a custom tool from the registry."""
        for i, tool in enumerate(self.tools):
            if tool.name == name and tool.category == "Custom":
                removed_tool = self.tools.pop(i)
                # Save all tools to file after removal
                self._save_all_tools()
                logger.info(f"Removed custom tool: {name}")
                return True
        return False

    def execute_tool(
        self, tool_name: str, parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a tool and return results."""
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        # Merge tool parameters with provided parameters
        query_params = tool.parameters or {}
        if parameters:
            query_params.update(parameters)

        try:
            results = db.execute_query(tool.query, query_params)
            metrics = getattr(db, "last_metrics", None)
            return {
                "tool_name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "results": results,
                "result_count": len(results),
                "db_metrics": metrics,
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            raise

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "has_parameters": tool.parameters is not None,
            }
            for tool in self.tools
        ]


# Global tool registry
tool_registry = ToolRegistry()
