# CI/CD Configuration

This directory contains CI/CD configuration files and scripts for the Code Graph Agent project.

## 📁 Structure

```
ci/
├── README.md                    # This file
├── config/                      # CI/CD configuration files
│   ├── .pre-commit-config.yaml  # Pre-commit hooks configuration
│   └── requirements-dev.txt     # Development dependencies
└── scripts/                     # CI/CD automation scripts
    └── ci-runner.sh            # CI pipeline runner script
```

## 🔧 Configuration Files

### `config/.pre-commit-config.yaml`
Pre-commit hooks configuration that automatically runs:
- Code formatting (Black, isort)
- Linting (flake8)
- Type checking (mypy)
- Security checks (bandit, safety)
- Tests

### `config/requirements-dev.txt`
Development dependencies including:
- Testing tools (pytest, pytest-cov)
- Code quality tools (black, isort, flake8, mypy)
- Security tools (bandit, safety)
- Development utilities

## 🚀 Scripts

### `scripts/ci-runner.sh`
A comprehensive CI runner script that can execute:
- **install**: Install dependencies
- **test**: Run tests with coverage
- **lint**: Run all linting checks
- **security**: Run security scans
- **format**: Format code
- **build**: Build package
- **full**: Run complete CI pipeline

**Usage:**
```bash
# Run full CI pipeline
./ci/scripts/ci-runner.sh full

# Run specific step
./ci/scripts/ci-runner.sh test
./ci/scripts/ci-runner.sh lint
```

## 🔗 Related Files

- **GitHub Actions**: `.github/workflows/` - CI/CD workflows
- **Documentation**: `docs/ci-cd/` - CI/CD documentation
- **Project Scripts**: `scripts/` - General automation scripts

## 🎯 Benefits

- ✅ **Centralized Configuration** - All CI/CD configs in one place
- ✅ **Reusable Scripts** - Common operations automated
- ✅ **Consistent Environment** - Same tools used locally and in CI
- ✅ **Easy Maintenance** - Clear structure and documentation
