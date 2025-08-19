# Testing Guide

This directory contains comprehensive tests for the Code Graph Agent system.

## 📁 Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── test_config.py           # Configuration management tests
├── test_mcp_tools.py        # MCP tools registry tests
├── test_llm.py             # LLM integration tests
├── test_agent.py           # LangGraph agent tests
├── test_database.py        # Database connection tests
├── test_integration.py     # Integration tests
├── test_dynamic_schema.py  # Dynamic schema generation tests
├── test_schema_queries.py  # Database schema query tests
├── run_tests.py            # Test runner script
└── README.md               # This file
```

## 🧪 Test Categories

### Unit Tests
- **test_config.py**: Configuration loading and validation
- **test_mcp_tools.py**: Tool registry operations
- **test_llm.py**: LLM client functionality
- **test_agent.py**: Agent workflow and logic
- **test_database.py**: Database connection and queries

### Schema Tests
- **test_dynamic_schema.py**: Dynamic schema generation from database
- **test_schema_queries.py**: Database schema exploration and validation

### Integration Tests
- **test_integration.py**: End-to-end system tests
- API endpoint testing
- Complete workflow validation
- Error handling scenarios

## 🚀 Running Tests

### Quick Start
```bash
# Run all tests
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py -v

# Run with coverage report
python tests/run_tests.py --coverage
```

### Specific Test Categories
```bash
# Run unit tests only
python tests/run_tests.py --unit

# Run integration tests only
python tests/run_tests.py --integration

# Run component tests only
python tests/run_tests.py --components
```

### Using pytest directly
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py

# Run tests with specific pattern
pytest -k "test_config"

# Run tests with coverage
pytest --cov=src --cov-report=html
```

## 📊 Test Coverage

The test suite aims for **80%+ code coverage** across all components:

- **Configuration Management**: 100%
- **MCP Tools Registry**: 95%+
- **LLM Integration**: 90%+
- **Agent Workflow**: 85%+
- **Database Operations**: 90%+
- **API Endpoints**: 95%+

## 🔧 Test Configuration

### pytest.ini
- Configures test discovery and execution
- Sets up coverage reporting
- Defines test markers
- Configures async test handling

### Test Markers
- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slow running tests
- `@pytest.mark.database`: Database-dependent tests
- `@pytest.mark.llm`: LLM-dependent tests

## 🎯 Test Scenarios

### Configuration Tests
- ✅ Default settings validation
- ✅ Environment variable loading
- ✅ Missing configuration handling
- ✅ Invalid configuration error handling

### MCP Tools Tests
- ✅ Tool creation and validation
- ✅ Tool persistence and loading
- ✅ Tool execution and error handling
- ✅ Tool category filtering
- ✅ Duplicate tool prevention

### LLM Integration Tests
- ✅ Client initialization
- ✅ Query analysis and tool selection
- ✅ Response generation
- ✅ Fallback mechanisms
- ✅ Error handling

### Agent Tests
- ✅ Workflow execution
- ✅ Tool selection and execution
- ✅ Response generation
- ✅ Error handling and recovery
- ✅ State management

### Database Tests
- ✅ Connection establishment
- ✅ Query execution
- ✅ Parameter handling
- ✅ Error scenarios
- ✅ Session management

### Integration Tests
- ✅ API endpoint functionality
- ✅ Complete user workflows
- ✅ Error handling scenarios
- ✅ Data persistence
- ✅ System interactions

## 🛠️ Mocking Strategy

### External Dependencies
- **Neo4j Database**: Mocked for unit tests
- **Azure OpenAI**: Mocked for all tests
- **File System**: Mocked for tool persistence tests

### Internal Dependencies
- **Tool Registry**: Mocked for agent tests
- **LLM Client**: Mocked for agent tests
- **Configuration**: Mocked for component tests

## 📈 Coverage Reports

### HTML Coverage Report
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Terminal Coverage Report
```bash
pytest --cov=src --cov-report=term-missing
```

### Coverage Threshold
- Minimum coverage: 80%
- Fails if coverage drops below threshold
- Excludes test files from coverage

## 🚨 Common Test Issues

### Import Errors
```bash
# Ensure you're in the project root
cd /path/to/code-graph-agent

# Install test dependencies
pip install -r requirements.txt
```

### Async Test Issues
```bash
# Use pytest-asyncio for async tests
pytest tests/test_agent.py -v
```

### Database Connection Issues
```bash
# Database tests are mocked by default
# No actual database connection required
```

## 🔄 Continuous Integration

### GitHub Actions (Recommended)
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python tests/run_tests.py --coverage
```

### Local Development
```bash
# Pre-commit hook (optional)
cp tests/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## 📝 Adding New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import patch, MagicMock

class TestNewComponent:
    """Test cases for NewComponent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        pass
    
    def test_specific_functionality(self):
        """Test specific functionality."""
        # Arrange
        # Act
        # Assert
        pass
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        # Arrange
        # Act
        # Assert
        pass
```

### Integration Test Template
```python
import pytest
from fastapi.testclient import TestClient

class TestNewIntegration:
    """Integration tests for new feature."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    @patch('src.web_ui.dependency')
    def test_new_endpoint(self, mock_dependency):
        """Test new API endpoint."""
        # Arrange
        mock_dependency.return_value = expected_value
        
        # Act
        response = self.client.get("/api/new-endpoint")
        
        # Assert
        assert response.status_code == 200
        assert "expected_data" in response.json()
```

## 🎉 Test Best Practices

1. **Test Naming**: Use descriptive test names
2. **Arrange-Act-Assert**: Structure tests clearly
3. **Mocking**: Mock external dependencies
4. **Coverage**: Aim for high test coverage
5. **Isolation**: Tests should be independent
6. **Documentation**: Document complex test scenarios
7. **Performance**: Keep tests fast and efficient

## 📞 Troubleshooting

### Test Failures
1. Check test output for specific errors
2. Verify dependencies are installed
3. Ensure correct Python version
4. Check file paths and imports

### Coverage Issues
1. Review uncovered code paths
2. Add tests for missing scenarios
3. Check coverage configuration
4. Verify test execution

### Performance Issues
1. Use `--tb=short` for faster output
2. Run specific test categories
3. Use parallel execution if available
4. Optimize slow tests

---

**Happy Testing! 🧪✨**
