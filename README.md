# 🕵️ Neo4j Code Graph Agent

[![CI/CD Pipeline](https://github.com/dhodapkarsoham/neo4j-code-graph-agent/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/dhodapkarsoham/neo4j-code-graph-agent/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Type Checked: mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](https://mypy-lang.org/)
[![Security: Bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://bandit.readthedocs.io/)
[![Vulnerabilities: Safety](https://img.shields.io/badge/vulnerabilities-safety-green.svg)](https://pyup.io/safety/)

⚠️ Work in Progress: This repository is actively being developed. Feel free to try it out and provide feedback, but expect some changes and improvements as we development continues.

### This repository is an extension to [Alex Woolford's](https://www.linkedin.com/in/alexwoolford) Neo4j Code Graph 🙌. <br>
[Neo4j Code Graph](https://github.com/alexwoolford/neo4j-code-graph) turns your codebase into a queryable knowledge graph and helps find security vulnerabilities, architectural bottlenecks, technical debt hotspots, and team coordination issues with simple Cypher queries.

Neo4j Code Graph Agent (this repo) is an intelligent agentic AI system that analyzes Neo4j Code Graph using Neo4j, LangGraph, and Azure OpenAI. The system also provides a web interface and offers both pre-built and ability to add custom tools for code graph analysis.

## 🚀 Features

### Core Capabilities
- **Intelligent Code Analysis**: LLM-powered analysis of code repositories using Neo4j graph database
- **Custom Tool Creation**: Create and manage custom Cypher queries through an intuitive web interface
- **Agentic Workflows**: LangGraph-powered agent orchestration for complex analysis tasks
- **Modern Web UI**: React-based interface with real-time tool management and query processing

### Pre-built Analysis Tools
- **Security Analysis**: CVE impact analysis, vulnerable dependency detection
- **Code Quality**: Complexity analysis, large file detection, refactoring recommendations
- **Architecture**: Bottleneck detection, co-change analysis, architectural insights
- **Team Analytics**: Developer activity, file ownership, contribution patterns

### Custom Tool Management
- **Visual Tool Builder**: Create custom tools with name, description, and Cypher queries
- **Real-time Editing**: Edit tool properties (name, description, query) for custom tools
- **Persistent Storage**: Tools are automatically saved and persist across restarts
- **LLM Integration**: Custom tools are intelligently selected by the LLM based on user queries

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Web UI  │    │   FastAPI       │    │   LangGraph     │
│                 │◄──►│   Backend       │◄──►│   Agent         │
│ - Tool Manager  │    │ - API Endpoints │    │ - Query Analysis│
│ - Chat Interface│    │ - WebSocket     │    │ - Tool Selection│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Azure OpenAI  │    │   Neo4j         │
                       │   LLM Service   │    │   Database      │
                       │ - GPT-4o        │    │ - Code Graph    │
                       │ - Tool Selection│    │ - Cypher Queries│
                       └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- Neo4j Database (local or cloud)
- Azure OpenAI Service
- Web browser for testing UI (tested on Firefox, Safari, Arc, Comet)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd code-graph-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=api-version
AZURE_OPENAI_DEPLOYMENT_NAME=deployment-name

# Application Configuration
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

## 🚀 Quick Start

1. **Start the application**
   ```bash
   python main.py
   ```

2. **Access the web interface**
   ```
   http://localhost:8000
   ```

3. **Start analyzing your code**
   - Use pre-built tools for common analysis tasks
   - Create custom tools for specific queries
   - Ask questions in natural language

## 📖 Usage

### Web Interface

The web interface provides two main sections:

#### 1. Ask Questions
- **Natural Language Queries**: Ask questions about your codebase in plain English
- **Intelligent Tool Selection**: The LLM automatically selects the best tools for your query
- **Real-time Results**: Get instant analysis results with detailed reasoning
- **Reasoning Display**: See how the LLM made decisions with collapsible reasoning details

#### 2. Tools Management
- **Pre-built Tools**: Browse and test existing analysis tools
- **Custom Tool Creation**: Create new tools with custom Cypher queries
- **Tool Editing**: Edit name, description, and queries for custom tools
- **Tool Testing**: Test tools directly from the interface

### Creating Custom Tools

1. Navigate to the "Tools Management" tab
2. Click "Create New Tool"
3. Fill in the tool details:
   - **Name**: Unique identifier for the tool
   - **Description**: What the tool does
   - **Category**: Tool category (Custom)
   - **Query**: Cypher query to execute
4. Click "Create Tool"

### Editing Custom Tools

1. Find your custom tool in the Tools Management tab
2. Click "Details" to open the tool editor
3. Modify the name, description, or Cypher query
4. Click "Save Changes"

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - Web interface
- `GET /api/health` - Health check
- `GET /api/tools` - List all tools
- `POST /api/tools` - Create new tool
- `PUT /api/tools/{name}/update` - Update tool
- `DELETE /api/tools/{name}` - Delete tool
- `POST /api/query` - Process natural language query

### Tool Management
- `GET /api/tools/{name}/details` - Get tool details
- `GET /api/tools/{name}/test` - Test tool execution

## 🏗️ Project Structure

```
code-graph-agent/
├── src/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Neo4j database connection
│   ├── llm.py              # Azure OpenAI integration
│   ├── agent.py            # LangGraph agent workflow
│   ├── mcp_tools.py        # Tool registry and management
│   └── web_ui.py           # FastAPI app and React UI
├── requirements.txt         # Python dependencies
├── env.example             # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🧪 Testing

### Automated Tests
Run the test suite to verify system functionality:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run basic smoke tests (recommended)
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py -v

# Run specific test patterns
python tests/run_tests.py basic    # Basic functionality tests
python tests/run_tests.py --full   # Full test suite (may have issues)
```

### Manual API Testing
Test the API endpoints manually:

```bash
# Health check
curl http://localhost:8000/api/health

# List tools
curl http://localhost:8000/api/tools

# Create custom tool
curl -X POST http://localhost:8000/api/tools \
  -H "Content-Type: application/json" \
  -d '{"name": "test_tool", "description": "Test tool", "category": "Custom", "query": "MATCH (n) RETURN n LIMIT 5"}'

# Query the agent
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me complex methods"}'
```

The basic test suite verifies:
- ✅ Module imports and initialization
- ✅ Configuration loading
- ✅ Tool registry functionality  
- ✅ LLM client setup
- ✅ Agent workflow creation
- ✅ Core system integration

## 🔍 Troubleshooting

### Common Issues

1. **Neo4j Connection Failed**
   - Verify Neo4j is running
   - Check connection credentials in `.env`
   - Ensure network connectivity

2. **Azure OpenAI Not Working**
   - Verify API key and endpoint in `.env`
   - Check deployment name and API version
   - Ensure sufficient quota/credits

3. **Custom Tools Not Persisting**
   - Check file permissions for `tools.json`
   - Verify the application has write access to the project directory

4. **LLM Not Selecting Custom Tools**
   - Ensure custom tools are properly saved
   - Check that tools have appropriate descriptions
   - Verify the LLM configuration is correct

## 🚀 CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

### Automated Checks
- **Tests**: Runs on Python 3.9, 3.10, and 3.11
- **Code Quality**: Black formatting, isort imports, flake8 linting
- **Type Checking**: mypy static type analysis
- **Security**: Bandit security scanning, Safety vulnerability checks
- **Build**: Package building and validation

### Development Workflow
```bash
# Install development dependencies
pip install -r requirements.txt

# Run local CI checks
./ci/scripts/ci-runner.sh full

# Or run individual checks
./ci/scripts/ci-runner.sh test    # Run tests
./ci/scripts/ci-runner.sh lint    # Run linting
./ci/scripts/ci-runner.sh security # Run security checks
```

### Pre-commit Hooks
Set up pre-commit hooks for automatic code quality checks:
```bash
# Install pre-commit
pip install pre-commit

# Install the git hook scripts
pre-commit install

# Run against all files
pre-commit run --all-files
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow the existing code style (Black + isort)
- Add type hints to new functions
- Include tests for new features
- Update documentation as needed
- Ensure all CI checks pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔩 Tech stack

- **Neo4j**: Graph database technology
- **LangGraph**: Agent orchestration framework
- **Azure OpenAI**: LLM
- **React**: Frontend framework
- **FastAPI**: Backend framework

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the API documentation

---
