"""MCP Tools for Neo4j Code Graph Analysis."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from src.database import db

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """MCP Tool definition."""
    name: str
    description: str
    category: str
    query: str
    parameters: Optional[Dict[str, Any]] = None


class MCPToolRegistry:
    """Registry for MCP tools."""
    
    def __init__(self):
        """Initialize with predefined tools."""
        self.tools_file = Path(__file__).parent.parent / "tools.json"
        self.tools = self._load_all_tools()
    
    def _get_predefined_tools(self) -> List[MCPTool]:
        """Get predefined tools from business queries and CVE examples."""
        return [
            # Security & Risk Management Tools
            MCPTool(
                name="find_customer_facing_vulnerable_apis",
                description="Find customer-facing APIs that use vulnerable dependencies",
                category="Security",
                query="""
                MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency)
                MATCH (dep)<-[:DEPENDS_ON]-(i:Import)<-[:IMPORTS]-(f:File)
                MATCH (f)-[:DECLARES]->(m:Method {is_public: true})
                WHERE cve.cvss_score >= 7.0
                RETURN f.path as file_path, 
                       m.class_name + '.' + m.name as api_endpoint,
                       cve.cve_id as cve_id,
                       cve.cvss_score as severity,
                       dep.package as vulnerable_dependency
                ORDER BY cve.cvss_score DESC
                """
            ),
            
            MCPTool(
                name="dependency_license_audit",
                description="Audit all open-source dependencies for license compliance",
                category="Security",
                query="""
                MATCH (dep:ExternalDependency)
                OPTIONAL MATCH (dep)<-[:DEPENDS_ON]-(i:Import)<-[:IMPORTS]-(f:File)
                RETURN dep.package as package,
                       dep.version as version,
                       dep.license as license,
                       count(DISTINCT f) as usage_count,
                       collect(DISTINCT f.path)[0..3] as sample_usage
                ORDER BY usage_count DESC
                """
            ),
            
            # Architecture & Technical Debt Tools
            MCPTool(
                name="refactoring_priority_matrix",
                description="Find high-impact components for refactoring (20% that impact 80% of system)",
                category="Architecture",
                query="""
                MATCH (m:Method)
                WHERE m.pagerank_score IS NOT NULL AND m.estimated_lines > 20
                WITH m, (m.pagerank_score * m.estimated_lines) as impact_score
                MATCH (m)<-[:DECLARES]-(f:File)
                RETURN f.path as file_path,
                       m.class_name + '.' + m.name as method_name,
                       m.pagerank_score as system_importance,
                       m.estimated_lines as complexity,
                       impact_score,
                       'High ROI refactoring target' as recommendation
                ORDER BY impact_score DESC
                LIMIT 20
                """
            ),
            
            MCPTool(
                name="architectural_bottlenecks",
                description="Find methods with high PageRank scores indicating architectural importance",
                category="Architecture",
                query="""
                MATCH (m:Method)
                WHERE m.pagerank_score IS NOT NULL AND m.pagerank_score > 0.001
                MATCH (m)<-[:DECLARES]-(f:File)
                RETURN f.path as file_path,
                       m.class_name + '.' + m.name as method_name,
                       m.pagerank_score as importance,
                       m.estimated_lines as complexity
                ORDER BY m.pagerank_score DESC
                LIMIT 20
                """
            ),
            
            MCPTool(
                name="co_changed_files_analysis",
                description="Find files that are frequently changed together (high coupling)",
                category="Architecture",
                query="""
                MATCH (f1:File)-[:CHANGED_IN]->(commit:Commit)-[:CHANGED]->(f2:FileVer)-[:OF_FILE]->(f3:File)
                WHERE f1 <> f3
                WITH f1, f3, count(commit) as co_changes
                WHERE co_changes > 3
                RETURN f1.path as file1,
                       f3.path as file2,
                       co_changes as change_frequency,
                       'High coupling detected' as insight
                ORDER BY co_changes DESC
                LIMIT 25
                """
            ),
            
            # Code Quality & Complexity Tools
            MCPTool(
                name="complex_methods_analysis",
                description="Find methods with high cyclomatic complexity",
                category="Quality",
                query="""
                MATCH (m:Method)
                WHERE m.estimated_lines > 50 OR m.cyclomatic_complexity > 10
                MATCH (m)<-[:DECLARES]-(f:File)
                RETURN f.path as file_path,
                       m.class_name + '.' + m.name as method_name,
                       m.estimated_lines as lines_of_code,
                       m.cyclomatic_complexity as complexity,
                       'Consider refactoring' as recommendation
                ORDER BY m.cyclomatic_complexity DESC, m.estimated_lines DESC
                LIMIT 30
                """
            ),
            
            MCPTool(
                name="large_files_analysis",
                description="Find files with excessive lines of code",
                category="Quality",
                query="""
                MATCH (f:File)
                WHERE f.total_lines > 500
                RETURN f.path as file_path,
                       f.total_lines as lines_of_code,
                       f.method_count as method_count,
                       f.class_count as class_count,
                       'Consider splitting into smaller files' as recommendation
                ORDER BY f.total_lines DESC
                LIMIT 25
                """
            ),
            
            # Security & Vulnerability Tools
            MCPTool(
                name="vulnerable_dependencies_summary",
                description="Find all vulnerable dependencies and their usage",
                category="Security",
                query="""
                MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency)
                MATCH (dep)<-[:DEPENDS_ON]-(i:Import)<-[:IMPORTS]-(f:File)
                RETURN dep.package as package,
                       dep.version as version,
                       cve.cve_id as cve_id,
                       cve.cvss_score as severity,
                       count(DISTINCT f) as affected_files,
                       collect(DISTINCT f.path)[0..5] as sample_files
                ORDER BY cve.cvss_score DESC, affected_files DESC
                """
            ),
            
            MCPTool(
                name="cve_impact_analysis",
                description="Analyze the impact of CVEs on the codebase",
                category="Security",
                query="""
                MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency)
                MATCH (dep)<-[:DEPENDS_ON]-(i:Import)<-[:IMPORTS]-(f:File)
                WITH cve, dep, count(f) as file_count
                MATCH (f:File)-[:DEPENDS_ON]->(dep)
                MATCH (f)-[:DECLARES]->(m:Method)
                RETURN cve.cve_id as cve_id,
                       cve.cvss_score as severity,
                       dep.package as package,
                       file_count as affected_files,
                       count(m) as affected_methods,
                       'High impact vulnerability' as assessment
                ORDER BY cve.cvss_score DESC, file_count DESC
                """
            ),
            
            # Team & Development Tools
            MCPTool(
                name="developer_activity_summary",
                description="Analyze developer activity and contribution patterns",
                category="Team",
                query="""
                MATCH (dev:Developer)-[:AUTHORED]->(commit:Commit)
                WITH dev, count(commit) as total_commits
                MATCH (dev)-[:AUTHORED]->(commit:Commit)-[:CHANGED]->(fv:FileVer)-[:OF_FILE]->(f:File)
                WITH dev, total_commits, f, count(commit) as file_commits
                WITH dev, total_commits, collect({file: f.path, commits: file_commits}) as file_activity
                RETURN dev.name as developer,
                       total_commits as total_commits,
                       size(file_activity) as files_worked_on,
                       [activity in file_activity | activity.file + ' (' + toString(activity.commits) + ')'][0..5] as top_files
                ORDER BY total_commits DESC
                LIMIT 15
                """
            ),
            
            MCPTool(
                name="file_ownership_analysis",
                description="Analyze file ownership and developer distribution",
                category="Team",
                query="""
                MATCH (dev:Developer)-[:AUTHORED]->(commit:Commit)-[:CHANGED]->(fv:FileVer)-[:OF_FILE]->(f:File)
                WITH f, dev, count(commit) as commits_by_dev
                WITH f, collect({dev: dev.name, commits: commits_by_dev}) as dev_contributions
                WITH f, dev_contributions, 
                     [dev in dev_contributions | dev.commits] as commit_counts
                RETURN f.path as file_path,
                       f.total_lines as lines_of_code,
                       size(dev_contributions) as developer_count,
                       reduce(total = 0, count in commit_counts | total + count) as total_commits,
                       [dev in dev_contributions | dev.dev + ' (' + toString(dev.commits) + ')'] as contributors
                ORDER BY total_commits DESC
                LIMIT 25
                """
            )
        ]
    
    def _load_all_tools(self) -> List[MCPTool]:
        """Load all tools from JSON file or create with predefined tools if file doesn't exist."""
        if self.tools_file.exists():
            try:
                with open(self.tools_file, 'r') as f:
                    tools_data = json.load(f)
                    tools = [MCPTool(**tool_data) for tool_data in tools_data]
                logger.info(f"Loaded {len(tools)} tools from {self.tools_file}")
                return tools
            except Exception as e:
                logger.error(f"Error loading tools from {self.tools_file}: {e}")
                logger.info("Falling back to predefined tools")
        
        # If file doesn't exist or error, create with predefined tools
        predefined_tools = self._get_predefined_tools()
        self._save_all_tools(predefined_tools)
        logger.info(f"Created tools file with {len(predefined_tools)} predefined tools")
        return predefined_tools
    
    def _save_all_tools(self, tools: List[MCPTool] = None):
        """Save all tools to JSON file."""
        if tools is None:
            tools = self.tools
        
        try:
            tools_data = [asdict(tool) for tool in tools]
            with open(self.tools_file, 'w') as f:
                json.dump(tools_data, f, indent=2)
            logger.info(f"Saved {len(tools)} tools to {self.tools_file}")
        except Exception as e:
            logger.error(f"Error saving tools: {e}")
    
    def get_tools_by_category(self, category: str) -> List[MCPTool]:
        """Get tools by category."""
        return [tool for tool in self.tools if tool.category == category]
    
    def get_tool_by_name(self, name: str) -> Optional[MCPTool]:
        """Get tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
    
    def add_tool(self, name: str, description: str, category: str, query: str, parameters: Optional[Dict[str, Any]] = None) -> MCPTool:
        """Add a new custom tool to the registry."""
        # Check if tool already exists
        if self.get_tool_by_name(name):
            raise ValueError(f"Tool with name '{name}' already exists")
        
        # Create new tool
        new_tool = MCPTool(
            name=name,
            description=description,
            category=category,
            query=query,
            parameters=parameters
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
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
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
            metrics = getattr(db, 'last_metrics', None)
            return {
                "tool_name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "results": results,
                "result_count": len(results),
                "db_metrics": metrics
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
                "has_parameters": tool.parameters is not None
            }
            for tool in self.tools
        ]


# Global tool registry
tool_registry = MCPToolRegistry()
