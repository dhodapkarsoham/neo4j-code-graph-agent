# Text2Cypher: Natural Language to Cypher Query Generation
# Text2Cypher Graph Model Docs Integration

## Overview

The Text2Cypher capability allows users to ask questions in natural language and automatically generates and executes Cypher queries against the Neo4j code graph database. This feature leverages the Azure OpenAI LLM to understand user intent and convert it into valid Cypher syntax.

This project can optionally augment the dynamic database schema with curated graph model documentation to improve Cypher generation quality.

## Quick start (concise)
- Ask questions in the UI or via the `/api/text2cypher` endpoint.
- Toggle curated docs via environment flags (see below).
- For LLM-focused, machine-readable semantics, the app can fetch an unlisted page:
  - LLM docs: `https://woolford.io/neo4j-code-graph/neo4j-code-graph/latest/graph-model-llm.html`
  - This page contains extra details for the model without cluttering human-facing docs.


## Toggle
- Global default via `.env`:
  - `TEXT2CYPHER_INCLUDE_GRAPH_DOCS=true|false`
  - `TEXT2CYPHER_USE_DOCS_ONLY=true|false` (if true, curated docs replace dynamic schema)
- Per-request overrides:
  - API `/api/text2cypher` accepts body `{ "question": "...", "include_graph_docs": true, "use_docs_only": true }`
  - Agent tool execution via `text2cypher` supports parameters `include_graph_docs`, `use_docs_only`.

## Source
- Remote URL: `GRAPH_MODEL_DOCS_URL=https://woolford.io/neo4j-code-graph/neo4j-code-graph/latest/graph-model-llm.html`
- Cache TTL: `GRAPH_MODEL_DOCS_TTL_SECONDS=3600` (seconds)

## How it works
- `SchemaCacheManager` builds a dynamic schema snapshot from Neo4j.
- `GraphDocsCacheManager` fetches curated docs once and caches them.
- `text2cypher` includes curated LLM docs as additional context (append mode) or as the primary schema (docs-only), depending on flags.

## Notes
- If docs are unavailable or fail to load, `text2cypher` gracefully proceeds without them.
- Large docs increase prompt size; use the TTL to avoid repeated fetches.
- Prefer append mode for reliability; use docs-only when the LLM-friendly page is up-to-date.
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

## Minimal schema primer (human-facing)

For the full graph model, see the main docs: `Graph model`.
This page intentionally avoids duplicating the entire schema.

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

## Advanced usage

### Programmatic (agent tool selection)
Use the built-in tool registry from Python to invoke Text2Cypher directly:
```python
from src.tools import tool_registry

result = tool_registry.execute_tool(
    "text2cypher",
    {"question": "Find vulnerable files"}
)
```

### Direct API (curl)
Quickly test via the REST endpoint:
```bash
curl -s http://localhost:8000/api/text2cypher \
  -H 'Content-Type: application/json' \
  -d '{"question":"Who worked on Louvain?","include_graph_docs":true,"use_docs_only":false}'
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

## Appendix: LLM guidance

For model-facing canonical chains and generation rules, see the unlisted LLM page:
`https://woolford.io/neo4j-code-graph/neo4j-code-graph/latest/graph-model-llm.html`

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
