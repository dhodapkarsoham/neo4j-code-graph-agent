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
    is_prebuilt: bool = False


class ToolRegistry:
    """Registry for Code Analysis tools."""

    def __init__(self) -> None:
        """Initialize tool registry and load tools from JSON file."""
        self.tools_file = Path(__file__).parent.parent / "tools.json"
        self.tools = self._load_all_tools()

    def _create_empty_tools_file(self) -> None:
        """Create an empty tools.json file with basic structure."""
        empty_tools: List[CodeTool] = []
        self._save_all_tools(empty_tools)
        logger.info(f"Created empty tools file at {self.tools_file}")

    def _load_all_tools(self) -> List[CodeTool]:
        """Load all tools from JSON file. Create empty file if it doesn't exist."""
        if self.tools_file.exists():
            try:
                with open(self.tools_file, "r") as f:
                    tools_data = json.load(f)
                    tools = []
                    for tool_data in tools_data:
                        # Mark tools as pre-built if they don't have the is_prebuilt flag
                        # (for backward compatibility with existing tools.json)
                        if "is_prebuilt" not in tool_data:
                            # Only mark non-Custom tools as pre-built
                            # Custom category tools should be user-created and deletable
                            is_prebuilt = tool_data.get("category") != "Custom"
                            tool_data["is_prebuilt"] = is_prebuilt
                            logger.info(f"Tool {tool_data.get('name')} (category: {tool_data.get('category')}) marked as is_prebuilt: {is_prebuilt}")
                        tools.append(CodeTool(**tool_data))
                logger.info(f"Loaded {len(tools)} tools from {self.tools_file}")
                return tools
            except Exception as e:
                logger.error(f"Error loading tools from {self.tools_file}: {e}")
                logger.warning("Creating new empty tools file due to corruption")

        # If file doesn't exist or is corrupted, create empty tools file
        self._create_empty_tools_file()
        return []

    def _save_all_tools(self, tools: List[CodeTool] = None) -> None:
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
        # Validate inputs
        if not name or not name.strip():
            raise ValueError("Tool name cannot be empty")
        
        if not description or not description.strip():
            raise ValueError("Tool description cannot be empty")
        
        if not query or not query.strip():
            raise ValueError("Tool query cannot be empty")
        
        # Normalize name (remove extra spaces, convert to lowercase for comparison)
        normalized_name = name.strip()
        
        # Check if tool already exists (case-insensitive)
        existing_tool = self.get_tool_by_name(normalized_name)
        if existing_tool:
            raise ValueError(f"Tool with name '{normalized_name}' already exists")

        # Validate category
        valid_categories = ["Security", "Architecture", "Team", "Quality", "Custom"]
        if category not in valid_categories:
            raise ValueError(f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}")

        # Create new tool (user-created, not pre-built)
        new_tool = CodeTool(
            name=normalized_name,
            description=description.strip(),
            category=category,
            query=query.strip(),
            parameters=parameters,
            is_prebuilt=False,
        )

        # Add to tools list
        self.tools.append(new_tool)

        # Save all tools to file
        self._save_all_tools()

        logger.info(f"Added new tool: {normalized_name} ({category})")
        return new_tool

    def remove_tool(self, name: str) -> bool:
        """Remove a custom tool from the registry."""
        for i, tool in enumerate(self.tools):
            if tool.name == name:
                # Check if this is a pre-built tool
                if tool.is_prebuilt:
                    logger.warning(f"Cannot delete pre-built tool: {name}")
                    return False
                
                # Allow deletion of any user-created tool (regardless of category)
                removed_tool = self.tools.pop(i)
                # Save all tools to file after removal
                self._save_all_tools()
                logger.info(f"Removed user-created tool: {name} (category: {tool.category})")
                return True
        
        logger.warning(f"Tool not found for deletion: {name}")
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
                "is_prebuilt": tool.is_prebuilt,
            }
            for tool in self.tools
        ]


# Global tool registry
tool_registry = ToolRegistry()
