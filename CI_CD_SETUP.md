# CI/CD Setup Guide

This document explains the CI/CD pipeline setup for the Code Graph Agent project.

## 🚀 Overview

Our CI/CD pipeline includes:
- **Automated Testing** across multiple Python versions
- **Code Quality Checks** (linting, formatting, type checking)
- **Security Scanning** (vulnerability detection)
- **Package Building**
- **Automated Deployment** (staging and production)

## 📁 File Structure

```
.github/
├── workflows/
│   ├── ci.yml          # Main CI pipeline
│   └── deploy.yml      # Deployment workflow
├── pyproject.toml      # Modern Python configuration
├── .pre-commit-config.yaml  # Pre-commit hooks
├── Makefile           # Development commands
├── requirements-dev.txt # Development dependencies
└── CI_CD_SETUP.md     # This file
```

## 🔧 Setup Instructions

### 1. Install Development Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Or use the Makefile
make install-dev
```

### 2. Setup Pre-commit Hooks

```bash
# Install pre-commit hooks
make setup-pre-commit

# Or manually
pre-commit install
```

### 3. Configure GitHub Secrets

For deployment, you'll need to set up these GitHub secrets:

- `NEO4J_URI`: Your Neo4j database URI
- `NEO4J_USER`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Azure OpenAI deployment name

## 🧪 Testing

### Run Tests Locally

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest tests/test_tools.py -v

# Run tests in parallel
pytest tests/ -n auto
```

### Test Coverage

We aim for >80% test coverage. View coverage reports:

```bash
# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html
```

## 🔍 Code Quality

### Linting and Formatting

```bash
# Run all quality checks
make lint

# Format code
make format

# Run individual tools
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/
```

### Security Checks

```bash
# Run security scans
make security-check

# Or individually
bandit -r src/
safety check
```



## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

#### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**
- **Test**: Runs tests on Python 3.9, 3.10, 3.11
- **Lint**: Code quality checks (Black, isort, flake8, mypy)
- **Security**: Security scanning (Bandit, Safety)
- **Build**: Package building and artifact creation

#### 2. Deployment Pipeline (`.github/workflows/deploy.yml`)

**Triggers:**
- Release publication
- Manual workflow dispatch

**Environments:**
- **Staging**: Manual deployment
- **Production**: Automatic on release

## 📊 Monitoring and Metrics

### Code Coverage

- Coverage reports are uploaded to Codecov
- Minimum coverage: 80%
- View reports at: https://codecov.io/gh/yourusername/code-graph-agent

### Security Reports

- Bandit security reports are generated
- Safety vulnerability checks
- Reports stored as GitHub artifacts

## 🛠️ Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push and create PR
git push origin feature/your-feature
```

### 2. Pre-commit Checks

Pre-commit hooks automatically run:
- Code formatting (Black, isort)
- Linting (flake8)
- Type checking (mypy)
- Security checks (bandit, safety)
- Tests

### 3. CI Pipeline

On push/PR:
1. Tests run on multiple Python versions
2. Code quality checks
3. Security scanning
4. Build verification

### 4. Deployment

**Staging:**
- Manual deployment via GitHub Actions
- Tests staging environment

**Production:**
- Automatic deployment on release
- Full test suite + security checks

## 🔧 Customization

### Adding New Tools

1. **Add to requirements-dev.txt**:
   ```
   new-tool>=1.0.0
   ```

2. **Update pyproject.toml**:
   ```toml
   [tool.new-tool]
   config = "value"
   ```

3. **Add to CI pipeline**:
   ```yaml
   - name: Run new tool
     run: new-tool src/
   ```

### Environment-Specific Configuration

Create environment-specific files:
- `.env.staging`
- `.env.production`
- `.env.local`

### Deployment Targets

Add new deployment targets in `deploy.yml`:
```yaml
deploy-custom:
  name: Deploy to Custom Environment
  runs-on: ubuntu-latest
  environment: custom
  steps:
    # Your deployment steps
```

## 🚨 Troubleshooting

### Common Issues

1. **Pre-commit fails**:
   ```bash
   # Update hooks
   pre-commit autoupdate
   
   # Run manually
   pre-commit run --all-files
   ```

2. **Build fails**:
   ```bash
   # Clean build artifacts
   make clean
   
   # Rebuild
   python -m build
   ```

3. **Tests fail locally but pass in CI**:
   ```bash
   # Run CI checks locally
   make ci-local
   ```

### Getting Help

- Check GitHub Actions logs for detailed error messages
- Review test coverage reports
- Check security scan results
- Consult the Makefile for available commands

## 📈 Best Practices

1. **Always run tests before committing**
2. **Keep test coverage above 80%**
3. **Use meaningful commit messages**
4. **Review security reports regularly**
5. **Update dependencies regularly**
6. **Monitor deployment metrics**

## 🔗 Useful Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
