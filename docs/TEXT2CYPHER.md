# Text2Cypher: Natural Language to Cypher Query Generation

## Overview

The Text2Cypher capability allows users to ask questions in natural language and automatically generates and executes Cypher queries against the Neo4j code graph database. This feature leverages the Azure OpenAI LLM to understand user intent and convert it into valid Cypher syntax.

## Features

- 🧠 **Intelligent Query Generation**: Uses LLM to convert natural language to Cypher
- 🔍 **Schema-Aware**: Understands the code graph database schema
- ⚡ **Automatic Execution**: Generates and runs queries in one step
- 📊 **Rich Results**: Returns formatted results with explanations
- 🛡️ **Safe Execution**: Includes limits and validation to prevent resource exhaustion

## How It Works

1. **User asks a question** in natural language
2. **Agent selects text2cypher tool** based on query analysis
3. **LLM generates Cypher query** using schema knowledge
4. **Query is executed** against the Neo4j database
5. **Results are returned** with explanations and metadata

## Usage Examples

### Through the Agent

Users can ask natural language questions that will automatically trigger the text2cypher tool:

```
User: "Find all files with more than 500 lines of code"
Agent: Selects text2cypher tool
Result: 
- Generated Query: MATCH (f:File) WHERE f.total_lines > 500 RETURN f.path, f.total_lines ORDER BY f.total_lines DESC LIMIT 25
- Results: List of large files with line counts
```

### Example Questions

**Security Analysis:**
- "Which files have high-severity CVE vulnerabilities?"
- "Show me all dependencies with security issues"
- "Find public methods in vulnerable files"

**Code Quality:**
- "Find methods with more than 100 lines"
- "Show me the most complex files"
- "Which files have the most methods?"

**Developer Activity:**
- "Who are the most active developers?"
- "Which developers worked on authentication code?"
- "Show me recent changes by specific developers"

**Architecture Analysis:**
- "Find files that change together frequently"
- "Show me methods with high centrality scores"
- "Which classes extend other classes?"

## Database Schema Knowledge

The text2cypher tool understands the complete code graph schema:

### Node Types
- **File**: Source code files with properties like `path`, `total_lines`, `method_count`
- **Method**: Code methods with `name`, `estimated_lines`, `is_public`, `pagerank_score`
- **Class**: Classes with `name`, `package`, inheritance relationships
- **CVE**: Security vulnerabilities with `cvss_score`, `severity`
- **Developer**: Contributors with `name`, `email`
- **ExternalDependency**: Third-party packages with `package`, `version`, `license`

### Relationships
- `File-[:DEPENDS_ON]->ExternalDependency`
- `File-[:DECLARES]->Method`
- `CVE-[:AFFECTS]->ExternalDependency`
- `Developer-[:AUTHORED]->Commit`
- `Method-[:CALLS]->Method`
- `File-[:CO_CHANGED]->File`

## Implementation Details

### Tool Registration

The text2cypher tool is automatically registered in the tool registry:

```python
{
    "name": "text2cypher",
    "description": "Generate and execute Cypher queries from natural language questions",
    "category": "Query",
    "has_parameters": True,
    "is_prebuilt": True,
}
```

### Query Generation Process

1. **Schema Context**: Provides comprehensive database schema to LLM
2. **Prompt Engineering**: Uses specialized prompts for Cypher generation
3. **JSON Parsing**: Expects structured response with query and explanation
4. **Fallback Extraction**: Can extract queries from unstructured responses
5. **Validation**: Basic query validation before execution

### Error Handling

- **LLM Unavailable**: Graceful fallback with error messages
- **Invalid JSON**: Attempts to extract Cypher from raw text
- **Query Errors**: Database errors are captured and returned
- **Schema Mismatches**: Guided by comprehensive schema documentation

## Integration Points

### Agent Workflow

The text2cypher tool integrates seamlessly with the existing agent architecture:

1. **Query Understanding**: Agent can select text2cypher based on user intent
2. **Tool Execution**: Special parameter handling for user questions
3. **Result Processing**: Standard result format for consistent display
4. **Streaming**: Supports real-time execution feedback

### Keyword Triggers

The following keywords can trigger text2cypher selection:
- "query", "cypher", "database", "graph"
- "natural language", "custom query"
- Or any question not matching predefined tools

## Configuration

### Prerequisites

- Azure OpenAI configured with LLM access
- Neo4j database connection established
- Code graph data loaded

### Environment Setup

No additional configuration needed - the feature uses existing:
- `src.llm.llm_client` for LLM access
- `src.database.db` for query execution
- `src.tools.tool_registry` for tool management

## Best Practices

### Query Design
- Include LIMIT clauses (automatically added)
- Use proper property names from schema
- Consider relationship directions
- Order results meaningfully

### Question Formulation
- Be specific about what you want to find
- Mention relevant entities (files, methods, developers)
- Use domain terms (vulnerability, complexity, dependencies)

### Result Interpretation
- Check `result_count` for data volume
- Review `generated_query` for understanding
- Read `explanation` for query logic
- Use `db_metrics` for performance info

## Advanced Usage

### Custom Parameters

The tool accepts a `question` parameter:

```python
tool_registry.execute_tool("text2cypher", {"question": "Find vulnerable files"})
```

### Response Format

```python
{
    "tool_name": "text2cypher",
    "description": "Generated and executed Cypher query for: [question]",
    "category": "Query",
    "results": [...],          # Query results
    "result_count": 25,        # Number of results
    "db_metrics": {...},       # Database performance metrics
    "generated_query": "...",  # The Cypher query generated
    "explanation": "...",      # LLM explanation of the query
    "user_question": "..."     # Original user question
}
```

## Troubleshooting

### Common Issues

**"LLM client not configured"**
- Check Azure OpenAI settings in environment
- Verify API keys and endpoints

**"Could not extract valid Cypher query"**
- LLM response was not parseable
- Try rephrasing the question more clearly

**"Property not found" errors**
- Generated query used incorrect property names
- Schema context may need updates

### Debugging

1. Check `generated_query` field for syntax issues
2. Review `explanation` for query logic
3. Test similar queries manually in Neo4j Browser
4. Verify database connection and data

## Future Enhancements

Potential improvements for the text2cypher feature:

- **Query Validation**: Syntax checking before execution
- **Result Caching**: Cache common query patterns
- **Query Optimization**: Suggest performance improvements
- **Interactive Refinement**: Allow users to modify generated queries
- **Query History**: Track and reuse successful patterns
- **Custom Schema**: Support for domain-specific extensions

## Security Considerations

- Queries are auto-limited to prevent resource exhaustion
- No data modification queries (INSERT/DELETE/UPDATE) are generated
- All queries are logged for audit purposes
- LLM responses are validated before execution

## Example Workflows

### Security Assessment
```
User: "Show me our security risk surface"
↓
Generated: Find files with high-severity CVEs
↓
Result: List of vulnerable files with CVSS scores
```

### Code Review Planning
```
User: "Which files should we review for complexity?"
↓
Generated: Find files with high method count and large size
↓
Result: Priority list for code review
```

### Developer Onboarding
```
User: "Who are the experts on authentication code?"
↓
Generated: Find developers with most commits to auth files
↓
Result: Contact list for domain experts
```

This text2cypher capability transforms the agent from a predefined tool executor into a flexible query interface, enabling users to explore their codebase through natural conversation.
