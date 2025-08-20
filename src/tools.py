"""Code Analysis Tools for Neo4j Code Graph Analysis."""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta

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
        
        # Add built-in text2cypher tools to the registry
        self._add_builtin_text2cypher_tools()

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
    
    def _add_builtin_text2cypher_tools(self) -> None:
        """Add built-in text2cypher tools to the registry."""
        # Add text2cypher tool if not already present
        if not self.get_tool_by_name("text2cypher"):
            text2cypher_tool = CodeTool(
                name="text2cypher",
                description="ENHANCED: Advanced natural language to Cypher with multi-step validation, error correction, and robust workflow. Includes guardrails, syntax validation, and automatic error correction. Perfect for specific questions about dependencies, files, classes, methods, developers, CVEs, and relationships.",
                category="Query",
                query="",  # This tool doesn't use a static query
                parameters={"question": "string"},
                is_prebuilt=True,
            )
            self.tools.append(text2cypher_tool)
            logger.info("Added built-in enhanced text2cypher tool to registry")
        


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
        # For text2cypher, prefer async_execute_tool when possible
        if tool_name == "text2cypher":
            import asyncio
            try:
                # Try to get current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we cannot use run_until_complete
                    # Return error message suggesting async usage
                    return {
                        "tool_name": "text2cypher",
                        "description": "text2cypher requires async execution",
                        "category": "Query",
                        "results": [],
                        "result_count": 0,
                        "error": "text2cypher must be called using async_execute_tool from async context",
                        "user_question": parameters.get("question", "") if parameters else "",
                    }
                else:
                    return loop.run_until_complete(self._execute_text2cypher_tool(parameters or {}))
            except RuntimeError:
                # No event loop, create one
                return asyncio.run(self._execute_text2cypher_tool(parameters or {}))
        
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

    async def async_execute_tool(
        self, tool_name: str, parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a tool asynchronously and return results."""
                # Special handling for text2cypher tools
        if tool_name == "text2cypher":
            return await self._execute_text2cypher_tool(parameters or {})
        
        # For regular tools, execute synchronously
        return self.execute_tool(tool_name, parameters)

    async def _execute_text2cypher_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute enhanced text2cypher tool using LangGraph workflow."""
        from src.text2cypher import text2cypher
        
        user_question = parameters.get("question", "")
        if not user_question:
            raise ValueError("Parameter 'question' is required for text2cypher tool")
        
        try:
            # Use the enhanced LangGraph workflow
            result = await text2cypher(user_question)
            
            return {
                "tool_name": "text2cypher",
                "description": f"Enhanced Cypher generation with validation for: {user_question}",
                "category": "Query",
                "results": result.get("answer", "No results generated"),
                "result_count": 1,  # Enhanced version returns a single answer
                "generated_query": result.get("generated_query", result.get("cypher_statement", "")),
                "explanation": result.get("explanation", ""),
                "user_question": user_question,
                "steps": result.get("steps", []),
                "enhanced": True,
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced text2cypher tool: {e}")
            return {
                "tool_name": "text2cypher",
                "description": f"Failed to process question: {user_question}",
                "category": "Query",
                "results": [],
                "result_count": 0,
                "error": str(e),
                "user_question": user_question,
                "enhanced": True,
            }



    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        tools_list = [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "has_parameters": tool.parameters is not None,
                "is_prebuilt": tool.is_prebuilt,
            }
            for tool in self.tools
        ]
        
        # Add text2cypher tool
        tools_list.append({
            "name": "text2cypher",
            "description": "ENHANCED: Advanced natural language to Cypher with multi-step validation, error correction, and robust workflow. Includes guardrails, syntax validation, and automatic error correction. Perfect for specific questions about dependencies, files, classes, methods, developers, CVEs, and relationships.",
            "category": "Query",
            "has_parameters": True,
            "is_prebuilt": True,
        })
        

        
        return tools_list


# Global tool registry
tool_registry = ToolRegistry()


@dataclass
class SchemaCache:
    """Schema cache entry with TTL."""
    schema: str
    created_at: datetime
    ttl_seconds: int = 300  # 5 minutes default
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def time_until_expiry(self) -> float:
        """Get seconds until cache expires."""
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return (expiry_time - datetime.now()).total_seconds()

class SchemaCacheManager:
    """Manages lazy loading and caching of database schema."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: Optional[SchemaCache] = None
        self._loading_lock = asyncio.Lock()
        self._last_load_attempt: Optional[datetime] = None
        self._load_attempt_interval = 60  # Don't retry loading more than once per minute
    
    async def get_schema(self) -> str:
        """Get schema with lazy loading and caching."""
        # Check if we have a valid cache
        if self._cache and not self._cache.is_expired():
            logger.debug(f"Using cached schema (expires in {self._cache.time_until_expiry():.1f}s)")
            return self._cache.schema
        
        # Check if we should attempt to load (rate limiting)
        if self._last_load_attempt:
            time_since_last = (datetime.now() - self._last_load_attempt).total_seconds()
            if time_since_last < self._load_attempt_interval:
                if self._cache:
                    logger.warning(f"Using expired cache due to rate limiting (last attempt {time_since_last:.1f}s ago)")
                    return self._cache.schema
                else:
                    # Reset the last load attempt to allow retry
                    self._last_load_attempt = None
        
        # Load schema with lock to prevent concurrent loads
        async with self._loading_lock:
            # Double-check cache after acquiring lock
            if self._cache and not self._cache.is_expired():
                return self._cache.schema
            
            logger.info("Loading database schema (lazy load)")
            self._last_load_attempt = datetime.now()
            
            try:
                schema = await self._fetch_schema_from_database()
                self._cache = SchemaCache(
                    schema=schema,
                    created_at=datetime.now(),
                    ttl_seconds=self.ttl_seconds
                )
                logger.info(f"Schema loaded successfully (cached for {self.ttl_seconds}s)")
                return schema
                
            except Exception as e:
                logger.error(f"Failed to load schema: {e}")
                if self._cache:
                    logger.warning("Using expired cache due to load failure")
                    return self._cache.schema
                else:
                    raise Exception(f"Failed to load schema and no cache available: {e}")
    
    async def _fetch_schema_from_database(self) -> str:
        """Fetch schema from database with optimized queries."""
        from src.database import db
        
        schema_context = "DATABASE SCHEMA:\n\n"
        
        # Get node labels (single query)
        schema_context += "NODE LABELS:\n"
        try:
            labels_result = db.execute_query("CALL db.labels() YIELD label RETURN label ORDER BY label")
            for row in labels_result:
                schema_context += f"- {row['label']}\n"
        except Exception as e:
            logger.warning(f"Could not fetch node labels: {e}")
            schema_context += "- Error fetching node labels\n"
        
        schema_context += "\n"
        
        # Get relationship types (single query)
        schema_context += "RELATIONSHIP TYPES:\n"
        try:
            rels_result = db.execute_query("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")
            for row in rels_result:
                schema_context += f"- {row['relationshipType']}\n"
        except Exception as e:
            logger.warning(f"Could not fetch relationship types: {e}")
            schema_context += "- Error fetching relationship types\n"
        
        schema_context += "\n"
        
        # Get relationship patterns (optimized - single query with aggregation)
        schema_context += "RELATIONSHIP PATTERNS:\n"
        try:
            # Use a more efficient query to get relationship patterns
            pattern_query = """
            CALL db.relationshipTypes() YIELD relationshipType
            MATCH ()-[r]->() 
            WHERE type(r) = relationshipType
            RETURN relationshipType, 
                   labels(startNode(r)) as startLabels, 
                   labels(endNode(r)) as endLabels
            LIMIT 1
            """
            patterns_result = db.execute_query(pattern_query)
            for row in patterns_result:
                rel_type = row['relationshipType']
                start_labels = row['startLabels']
                end_labels = row['endLabels']
                schema_context += f"- ({start_labels}) -[:{rel_type}]-> ({end_labels})\n"
        except Exception as e:
            logger.warning(f"Could not fetch relationship patterns: {e}")
            schema_context += "- Error fetching relationship patterns\n"
        
        schema_context += "\n"
        
        # Get node properties (simplified approach)
        schema_context += "NODE PROPERTIES:\n"
        try:
            # Get properties for each label individually to avoid complex queries
            labels_result = db.execute_query("CALL db.labels() YIELD label")
            for row in labels_result:
                label_name = row['label']
                try:
                    # Simple query to get properties for this label
                    props = db.execute_query(f"MATCH (n:{label_name}) RETURN keys(n) as properties LIMIT 1")
                    if props and props[0]['properties']:
                        schema_context += f"{label_name}:\n"
                        properties = props[0]['properties']
                        for prop in sorted(properties):
                            schema_context += f"  - {prop}\n"
                except Exception as e:
                    schema_context += f"{label_name}: Error getting properties\n"
        except Exception as e:
            logger.warning(f"Could not fetch node properties: {e}")
            schema_context += "- Error fetching node properties\n"
        
        # Add common query patterns and examples
        schema_context += "\nCOMMON QUERY PATTERNS:\n"
        schema_context += "1. Security Analysis: CVE-AFFECTS->ExternalDependency<-DEPENDS_ON-Import<-IMPORTS-File\n"
        schema_context += "2. Code Complexity: Method.estimated_lines, File.total_lines\n"
        schema_context += "3. Developer Activity: Developer-AUTHORED->Commit-CHANGED->FileVer-OF_FILE->File\n"
        schema_context += "4. Architecture Analysis: Method.pagerank_score, betweenness_score\n"
        schema_context += "5. Method Calls: Method-CALLS->Method\n"
        schema_context += "6. Class Hierarchy: Class-EXTENDS/IMPLEMENTS->Class/Interface\n"
        schema_context += "7. Class-Method Relationship: Class-CONTAINS_METHOD->Method\n"
        schema_context += "8. File-Class-Method: File-DEFINES->Class-CONTAINS_METHOD->Method\n"
        
        schema_context += "\nEXAMPLE QUERIES:\n"
        schema_context += "- Find vulnerable files: MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency)<-[:DEPENDS_ON]-(imp:Import)<-[:IMPORTS]-(f:File) WHERE cve.cvss_score >= 7.0 RETURN f.path, cve.id LIMIT 50\n"
        schema_context += "- CVEs affecting specific dependency: MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency) WHERE dep.name = 'dependency.name' AND cve.cvss_score >= 7.0 RETURN cve.id, cve.description, cve.cvss_score LIMIT 50\n"
        schema_context += "- High severity CVEs for dependency: MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency) WHERE dep.name = 'apoc.create.Create' AND cve.cvss_score >= 7.0 RETURN cve.id, cve.description, cve.cvss_score LIMIT 50\n"
        schema_context += "- Complex methods: MATCH (m:Method)<-[:DECLARES]-(f:File) WHERE m.estimated_lines > 50 RETURN f.path, m.name, m.estimated_lines LIMIT 50\n"
        schema_context += "- Developer activity: MATCH (dev:Developer)-[:AUTHORED]->(c:Commit) RETURN dev.name, count(c) as commits ORDER BY commits DESC LIMIT 50\n"
        schema_context += "- Methods in class: MATCH (c:Class {name: 'ClassName'})-[:CONTAINS_METHOD]->(m:Method) RETURN m.name, m.line LIMIT 50\n"
        schema_context += "- Methods in file: MATCH (f:File)-[:DECLARES]->(m:Method) WHERE f.path CONTAINS 'path/to/file' RETURN m.name, m.line LIMIT 50\n"
        
        return schema_context
    
    def invalidate_cache(self):
        """Invalidate the current cache."""
        self._cache = None
        logger.info("Schema cache invalidated")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status for debugging."""
        if not self._cache:
            return {"status": "no_cache", "message": "No schema cached"}
        
        return {
            "status": "expired" if self._cache.is_expired() else "valid",
            "created_at": self._cache.created_at.isoformat(),
            "ttl_seconds": self._cache.ttl_seconds,
            "time_until_expiry": self._cache.time_until_expiry(),
            "schema_length": len(self._cache.schema)
        }
    
    async def preload_schema(self):
        """Preload schema on startup for better performance."""
        logger.info("Preloading database schema for better performance...")
        try:
            await self.get_schema()
            logger.info("Schema preloaded successfully")
        except Exception as e:
            logger.warning(f"Failed to preload schema: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        status = self.get_cache_status()
        return {
            **status,
            "cache_hit_rate": "N/A",  # Could be implemented with counters
            "load_attempts": "N/A",   # Could be implemented with counters
            "last_load_attempt": self._last_load_attempt.isoformat() if self._last_load_attempt else None
        }

# Global schema cache manager
schema_cache_manager = SchemaCacheManager(ttl_seconds=300)  # 5 minutes TTL
