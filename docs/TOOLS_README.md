# 🛠️ Tools Configuration

This file documents the structure and organization of `tools.json`.

## 📋 File Structure

The `tools.json` file contains an array of tool definitions organized by category:

```json
[
  {
    "name": "tool_name",
    "description": "What the tool does",
    "category": "Security|Architecture|Quality|Team|Custom",
    "query": "Cypher query with proper formatting",
    "parameters": null
  }
]
```

## 📂 Categories

### 🔒 Security (4 tools)
- **cve_impact_analysis**: Analyze CVE impact on codebase
- **dependency_license_audit**: Audit dependencies for license compliance  
- **find_customer_facing_vulnerable_apis**: Find vulnerable customer-facing APIs
- **vulnerable_dependencies_summary**: Summary of all vulnerable dependencies

### 🏗️ Architecture (3 tools)  
- **architectural_bottlenecks**: Find high PageRank methods (architectural importance)
- **co_changed_files_analysis**: Find files frequently changed together
- **refactoring_priority_matrix**: High-impact refactoring candidates

### 💎 Quality (2 tools)
- **complex_methods_analysis**: Find high complexity methods
- **large_files_analysis**: Find files with excessive lines of code

### 👥 Team (2 tools)
- **developer_activity_summary**: Analyze developer contribution patterns
- **file_ownership_analysis**: Analyze file ownership distribution

### 🔧 Custom (1 tools)
- User-created tools appear here

## 🎯 Tool Definition Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Unique tool identifier |
| `description` | string | ✅ | Human-readable description |
| `category` | string | ✅ | Tool category for organization |
| `query` | string | ✅ | Cypher query to execute |
| `parameters` | object/null | ❌ | Query parameters (future use) |

## 📝 Query Formatting

Cypher queries are formatted for readability:
- Main clauses (MATCH, WHERE, RETURN, etc.) start at the beginning of lines
- Continuation lines are indented with 7 spaces
- Queries are multi-line strings with `\n` separators

## 🔄 Management

- **Single Source**: This JSON file is the only source of truth for tools
- **CRUD Operations**: Use the web UI or API endpoints to modify tools
- **Persistence**: Changes are automatically saved to this file
- **Backup**: Version control this file to track changes

## 🚀 Usage

Tools are loaded automatically on application startup and can be:
- **Listed**: View all available tools by category
- **Executed**: Run tools through the web interface or API
- **Modified**: Edit existing tools via the web UI
- **Created**: Add new custom tools
- **Deleted**: Remove custom tools (predefined tools are preserved)
