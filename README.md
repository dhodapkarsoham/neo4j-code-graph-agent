# 🔍 Code Graph Agent

[![CI/CD Pipeline](https://github.com/dhodapkarsoham/neo4j-code-graph-agent/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/dhodapkarsoham/neo4j-code-graph-agent/actions)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0-orange.svg)](https://github.com/langchain-ai/langgraph)

⚠️ Work in Progress: This repository is actively being developed. Feel free to try it out and provide feedback, but expect some changes and improvements as we development continues.

## 🚀 Overview
### This repository is an extension to [Alex Woolford's](https://www.linkedin.com/in/alexwoolford) Neo4j Code Graph. 

[Neo4j Code Graph](https://github.com/alexwoolford/neo4j-code-graph) turns your codebase into a queryable knowledge graph and helps find security vulnerabilities, architectural bottlenecks, technical debt hotspots, and team coordination issues with simple Cypher queries.

⚠️ Running Code Graph steps and having a Neo4j database (self-hosted or Aura) is a pre-requisite to running the Agentic workflow using Code Graph Agent.
[Click here](https://neo4j.com/docs/aura/classic/auradb/getting-started/create-database/) to create your own Neo4j Aura instace.

Code Graph Agent is an intelligent AI system that transforms your codebase into a queryable knowledge graph and provides deep insights through natural language queries and tools management. It extends Code Graph's capabilities with:

- **🤖 LLM-Powered Analysis** - Natural language queries with intelligent tool selection
- **🔍 Text2Cypher** - Convert questions to Cypher queries automatically
- **📊 Real-time Insights** - Live analysis with detailed reasoning
- **🛠️ Custom Tools** - Create and manage analysis tools through web UI

## ✨ Key Features

### 🧠 **Intelligent Analysis**
- **Natural Language Queries** - Ask questions in plain English
- **Dynamic Schema Integration** - Always uses up-to-date database schema
- **LLM-Powered Tool Selection** - Intelligent selection of analysis tools
- **Real-time Reasoning** - See how the AI makes decisions

### 🔍 **Text2Cypher Technology**
- **Automatic Query Generation** - Convert natural language to Cypher
- **Schema-Aware** - Correct relationship directions and properties
- **Dynamic Schema Loading** - Lazy loading with caching for performance
- **Query Explanation** - Understand what each query does

### 🛠️ **Tool Management**
- **Pre-built Analysis Tools** - Security, quality, architecture, team analytics
- **Custom Tool Creation** - Build your own analysis tools
- **Visual Tool Builder** - Intuitive web interface for tool management
- **Persistent Storage** - Tools saved and available across sessions

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Interface                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Chat UI       │  │   Tools Mgmt    │  │   Results       │ │
│  │   (Real-time)   │  │   (CRUD)        │  │   (Formatted)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   API Routes    │  │  WebSocket      │  │   Static Files  │ │
│  │   (REST)        │  │  (Real-time)    │  │   (JS/CSS)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Agent                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Query         │  │   Tool          │  │   Response      │ │
│  │   Analysis      │  │   Selection     │  │   Generation    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Azure OpenAI  │  │   Neo4j         │  │   Tool Registry │ │
│  │   (LLM)         │  │   (Database)    │  │   (Storage)     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
code-graph-agent/
├── src/                          # Main source code
│   ├── app.py                    # FastAPI application entry point
│   ├── agent.py                  # LangGraph agent workflow
│   ├── tools.py                  # Tool registry and management
│   ├── llm.py                    # Azure OpenAI integration
│   ├── database.py               # Neo4j database connection
│   ├── config.py                 # Configuration management
│   ├── routes/                   # API and WebSocket routes
│   │   ├── api.py               # REST API endpoints
│   │   └── websocket.py         # WebSocket handling
│   ├── components/              # UI components
│   │   └── main_page.py         # HTML page generation
│   └── static/                  # Static assets
│       └── js/                  # JavaScript modules
│           ├── websocket.js     # WebSocket client
│           ├── formatting.js    # Response formatting
│           ├── ui.js           # UI interactions
│           └── reasoning.js    # Reasoning display
├── tests/                        # Test suite
├── requirements.txt              # Python dependencies
├── env.example                   # Environment template
├── main.py                       # Application entry point
├── start.py                      # Development server
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Neo4j Database** (local or cloud)
- **Azure OpenAI Service**
- **Modern Web Browser**

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd code-graph-agent
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Start the application**
   ```bash
   python main.py
   ```

6. **Access the web interface**
   ```
   http://localhost:8000
   ```

## ⚙️ Configuration

Create a `.env` file with the following configuration:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# Application Configuration
DEBUG=true
HOST=127.0.0.1
PORT=8000
```

## 📖 Usage

### Web Interface

The web interface provides an intuitive way to interact with your codebase:

#### 💬 **Chat Interface**
- **Natural Language Queries** - Ask questions like "What HIGH severity CVEs are affecting SomeFileName?"
- **Real-time Responses** - Get instant analysis with detailed reasoning
- **Collapsible Details** - Expand to see generated Cypher queries and explanations
- **Scrollable Results** - View all results with proper pagination

#### 🔧 **Tools Management**
- **Pre-built Tools** - Security analysis, code quality, architecture insights
- **Custom Tools** - Create your own analysis tools
- **Tool Testing** - Test tools directly from the interface
- **Tool Editing** - Modify existing custom tools

### API Usage

#### Core Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# List all tools
curl http://localhost:8000/api/tools

# Process natural language query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me complex methods with more than 100 lines"}'

# Create custom tool
curl -X POST http://localhost:8000/api/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "complex_methods",
    "description": "Find methods with high complexity",
    "category": "Custom",
    "query": "MATCH (m:Method) WHERE m.estimated_lines > 100 RETURN m.name, m.estimated_lines ORDER BY m.estimated_lines DESC LIMIT 50"
  }'
```

#### WebSocket API

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Send query
ws.send(JSON.stringify({
  type: 'query',
  query: 'What security vulnerabilities exist in my codebase?'
}));

// Handle responses
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## 🧪 Testing

### Automated Tests

```bash
# Run basic tests
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py -v

# Run specific test categories
python tests/run_tests.py basic    # Basic functionality
python tests/run_tests.py --full   # Full test suite
```

### Manual Testing

```bash
# Test API endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/tools

# Test WebSocket connection
# Use browser developer tools or WebSocket client
```

## 🔧 Development

### Project Structure

The application follows a modular architecture:

- **`src/app.py`** - Main FastAPI application
- **`src/routes/`** - API and WebSocket endpoints
- **`src/components/`** - UI components and templates
- **`src/static/js/`** - Frontend JavaScript modules
- **`src/agent.py`** - LangGraph agent workflow
- **`src/tools.py`** - Tool registry and management

### Adding New Features

1. **New API Endpoints** - Add to `src/routes/api.py`
2. **New Tools** - Extend `src/tools.py`
3. **UI Components** - Add to `src/components/`
4. **Frontend Logic** - Add to `src/static/js/`

### Code Quality

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run code quality checks
./ci/scripts/ci-runner.sh lint
./ci/scripts/ci-runner.sh security
./ci/scripts/ci-runner.sh test
```

## 🚀 Deployment

### Production Setup

1. **Environment Configuration**
   ```bash
   # Set production environment variables
   export DEBUG=false
   export HOST=0.0.0.0
   export PORT=8000
   ```

2. **Start Production Server**
   ```bash
   python main.py
   ```

3. **Reverse Proxy (Optional)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## 🔍 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Neo4j Connection Failed** | Check credentials and network connectivity |
| **Azure OpenAI Errors** | Verify API key, endpoint, and deployment name |
| **WebSocket Not Connecting** | Check firewall settings and port availability |
| **Custom Tools Not Saving** | Verify file permissions for `tools.json` |
| **Schema Loading Issues** | Check Neo4j database connectivity and permissions |

### Debug Mode

Enable debug mode for detailed logging:

```bash
export DEBUG=true
python main.py
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** following the code style
4. **Add tests** for new functionality
5. **Commit your changes** (`git commit -m 'feat: add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Development Guidelines

- Follow **Black** code formatting
- Use **type hints** for all functions
- Write **comprehensive tests**
- Update **documentation** as needed
- Ensure **all CI checks pass**

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Alex Woolford** - Original [Neo4j Code Graph](https://github.com/alexwoolford/neo4j-code-graph) project
- **LangChain** - [LangGraph](https://github.com/langchain-ai/langgraph) orchestration framework
- **FastAPI** - Modern web framework for building APIs
- **Neo4j** - Graph database technology

## 📞 Support

- **GitHub Issues** - [Create an issue](https://github.com/dhodapkarsoham/neo4j-code-graph-agent/issues)
- **Documentation** - Check the troubleshooting section above
- **Community** - Join discussions in GitHub discussions

---

**Made with ❤️ for the developer community**
