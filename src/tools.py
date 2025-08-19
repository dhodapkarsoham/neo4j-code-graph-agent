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
        # Special handling for text2cypher tool
        if tool_name == "text2cypher":
            return await self._execute_text2cypher_tool(parameters or {})
        
        # For regular tools, execute synchronously
        return self.execute_tool(tool_name, parameters)

    async def _execute_text2cypher_tool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute text2cypher tool to generate and run Cypher queries from natural language."""
        from src.llm import llm_client
        
        user_question = parameters.get("question", "")
        if not user_question:
            raise ValueError("Parameter 'question' is required for text2cypher tool")
        
        try:
            # Generate Cypher query using LLM
            cypher_result = await self._generate_cypher_from_text(user_question)
            generated_query = cypher_result["query"]
            explanation = cypher_result["explanation"]
            
            # Execute the generated query
            results = db.execute_query(generated_query)
            metrics = getattr(db, "last_metrics", None)
            
            return {
                "tool_name": "text2cypher",
                "description": f"Generated and executed Cypher query for: {user_question}",
                "category": "Query",
                "results": results,
                "result_count": len(results),
                "db_metrics": metrics,
                "generated_query": generated_query,
                "explanation": explanation,
                "user_question": user_question,
            }
            
        except Exception as e:
            logger.error(f"Error in text2cypher tool: {e}")
            return {
                "tool_name": "text2cypher",
                "description": f"Failed to process question: {user_question}",
                "category": "Query",
                "results": [],
                "result_count": 0,
                "error": str(e),
                "user_question": user_question,
            }

    async def _generate_cypher_from_text(self, user_question: str) -> Dict[str, str]:
        """Generate a Cypher query from natural language question."""
        from src.llm import llm_client
        
        if not llm_client.is_configured():
            raise RuntimeError("LLM client not configured - cannot generate Cypher queries")
        
        # Define the database schema information
        schema_info = self._get_database_schema_context()
        
        system_prompt = f"""You are an expert Neo4j Cypher query generator for a code analysis graph database.

DATABASE SCHEMA:
{schema_info}

TASK: Convert the user's natural language question into a valid Cypher query.

GUIDELINES:
1. Use ONLY the node labels, properties, and relationships shown in the schema above
2. Always include LIMIT clauses (typically 25-50) to prevent huge result sets
3. Use DISTINCT to avoid duplicate results
4. Use proper Cypher syntax with correct WHERE clauses and aggregations
5. For complex questions, break them down into logical graph patterns
6. Include relevant properties in the RETURN clause
7. Use OPTIONAL MATCH when relationships might not exist
8. Order results by relevant criteria (e.g., severity, count, importance)

EXAMPLE PATTERNS:
- Finding vulnerabilities: MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency)<-[:DEPENDS_ON]-(f:File)
- Developer activity: MATCH (dev:Developer)-[:AUTHORED]->(commit:Commit)
- Complex methods: MATCH (m:Method) WHERE m.estimated_lines > 50
- File dependencies: MATCH (f:File)-[:DEPENDS_ON]->(dep:ExternalDependency)

RESPONSE FORMAT (JSON):
{{
    "query": "MATCH ... RETURN ... LIMIT 25",
    "explanation": "This query finds X by doing Y, filtering by Z, and returns the results ordered by importance."
}}

Be precise with property names and relationship directions. Always test your understanding against the schema provided."""

        try:
            import json
            
            # Generate response using await (we're now in async context)
            response = await llm_client.generate_response(
                messages=[{"role": "user", "content": f"Question: {user_question}"}],
                system_prompt=system_prompt,
                temperature=0.1,  # Low temperature for consistent query generation
                max_tokens=1000,
            )
            
            # Parse JSON response
            try:
                # Clean up the response
                cleaned_response = response.strip()
                if cleaned_response.startswith("```"):
                    # Remove code blocks
                    import re
                    cleaned_response = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned_response)
                    cleaned_response = re.sub(r"```$", "", cleaned_response).strip()
                
                # Extract JSON if mixed with other text
                if not cleaned_response.startswith("{"):
                    start = cleaned_response.find("{")
                    end = cleaned_response.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        cleaned_response = cleaned_response[start : end + 1]
                
                result = json.loads(cleaned_response)
                
                # Validate required fields
                if "query" not in result:
                    raise ValueError("Generated response missing 'query' field")
                
                return {
                    "query": result["query"],
                    "explanation": result.get("explanation", "Generated Cypher query from natural language"),
                }
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}")
                logger.warning(f"Raw response: {response[:200]}...")
                
                # Fallback: try to extract Cypher query from text
                cypher_query = self._extract_cypher_from_text(response)
                if cypher_query:
                    return {
                        "query": cypher_query,
                        "explanation": "Extracted Cypher query from LLM response (JSON parsing failed)",
                    }
                else:
                    raise ValueError("Could not extract valid Cypher query from LLM response")
                    
        except Exception as e:
            logger.error(f"Error generating Cypher query: {e}")
            raise
    
    def _extract_cypher_from_text(self, text: str) -> Optional[str]:
        """Extract Cypher query from text response as fallback."""
        import re
        
        # Look for MATCH statements
        match_patterns = [
            r"(MATCH\s+.*?(?=\n\n|\n$|$))",  # MATCH until double newline or end
            r"```(?:cypher)?\s*(MATCH.*?)```",  # Code blocks with MATCH
            r"(MATCH.*?LIMIT\s+\d+)",  # MATCH ... LIMIT pattern
        ]
        
        for pattern in match_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                query = matches[0].strip()
                # Basic validation
                if "MATCH" in query.upper() and "RETURN" in query.upper():
                    return query
        
        return None
    
    def _get_database_schema_context(self) -> str:
        """Get database schema context for LLM prompt by querying the database."""
        try:
            from src.database import db
            
            schema_context = "DATABASE SCHEMA:\n\n"
            
            # Get node labels
            schema_context += "NODE LABELS:\n"
            try:
                labels_result = db.execute_query("CALL db.labels() YIELD label RETURN label ORDER BY label")
                for row in labels_result:
                    schema_context += f"- {row['label']}\n"
            except Exception as e:
                logger.warning(f"Could not fetch node labels: {e}")
                schema_context += "- Error fetching node labels\n"
            
            schema_context += "\n"
            
            # Get relationship types
            schema_context += "RELATIONSHIP TYPES:\n"
            try:
                rels_result = db.execute_query("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")
                for row in rels_result:
                    schema_context += f"- {row['relationshipType']}\n"
            except Exception as e:
                logger.warning(f"Could not fetch relationship types: {e}")
                schema_context += "- Error fetching relationship types\n"
            
            schema_context += "\n"
            
            # Get sample relationships for each type
            schema_context += "RELATIONSHIP PATTERNS:\n"
            try:
                rels_result = db.execute_query("CALL db.relationshipTypes() YIELD relationshipType")
                for row in rels_result:
                    rel_type = row['relationshipType']
                    try:
                        sample = db.execute_query(f"MATCH ()-[r:{rel_type}]->() RETURN type(r), startNode(r), endNode(r) LIMIT 1")
                        if sample:
                            start_labels = list(sample[0]['startNode(r)'].labels)
                            end_labels = list(sample[0]['endNode(r)'].labels)
                            schema_context += f"- ({start_labels}) -[:{rel_type}]-> ({end_labels})\n"
                    except Exception as e:
                        schema_context += f"- {rel_type}: Error getting pattern\n"
            except Exception as e:
                logger.warning(f"Could not fetch relationship patterns: {e}")
                schema_context += "- Error fetching relationship patterns\n"
            
            schema_context += "\n"
            
            # Get properties for each node type
            schema_context += "NODE PROPERTIES:\n"
            try:
                labels_result = db.execute_query("CALL db.labels() YIELD label")
                for row in labels_result:
                    label = row['label']
                    try:
                        props = db.execute_query(f"MATCH (n:{label}) RETURN keys(n) as properties LIMIT 1")
                        if props:
                            properties = props[0]['properties']
                            schema_context += f"{label}:\n"
                            for prop in sorted(properties):
                                schema_context += f"  - {prop}\n"
                    except Exception as e:
                        schema_context += f"{label}: Error getting properties\n"
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
            schema_context += "- Find vulnerable files: MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency)<-[:DEPENDS_ON]-(imp:Import)<-[:IMPORTS]-(f:File) WHERE cve.cvss_score >= 7.0 RETURN f.path, cve.id\n"
            schema_context += "- Complex methods: MATCH (m:Method)<-[:DECLARES]-(f:File) WHERE m.estimated_lines > 50 RETURN f.path, m.name, m.estimated_lines\n"
            schema_context += "- Developer activity: MATCH (dev:Developer)-[:AUTHORED]->(c:Commit) RETURN dev.name, count(c) as commits ORDER BY commits DESC\n"
            schema_context += "- Methods in class: MATCH (c:Class {name: 'ClassName'})-[:CONTAINS_METHOD]->(m:Method) RETURN m.name, m.line\n"
            schema_context += "- Methods in file: MATCH (f:File)-[:DECLARES]->(m:Method) WHERE f.path CONTAINS 'path/to/file' RETURN m.name, m.line\n"
            
            return schema_context
            
        except Exception as e:
            logger.error(f"Error getting database schema context: {e}")
            raise Exception(f"Failed to get database schema: {e}. Please ensure the database is accessible and contains the required schema.")

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
            "description": "Generate and execute Cypher queries from natural language questions",
            "category": "Query",
            "has_parameters": True,
            "is_prebuilt": True,
        })
        
        return tools_list


# Global tool registry
tool_registry = ToolRegistry()
