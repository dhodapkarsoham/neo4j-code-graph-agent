# CI/CD Documentation

This directory contains all CI/CD related documentation and configuration for the Code Graph Agent project.

## 📁 Structure

```
ci-cd/
├── README.md              # This file
├── CI_CD_SETUP.md         # Detailed setup guide
└── CI_CD_SUMMARY.md       # Quick reference
```

## 🚀 Quick Start

1. **Install dependencies**: `pip install -r requirements-dev.txt`
2. **Setup pre-commit**: `pre-commit install`
3. **Run CI locally**: `./ci/scripts/ci-runner.sh full`

## 📋 Available Documentation

- **[CI_CD_SETUP.md](CI_CD_SETUP.md)** - Comprehensive setup and configuration guide
- **[CI_CD_SUMMARY.md](CI_CD_SUMMARY.md)** - Quick reference and overview

## 🔗 Related Files

- **GitHub Actions**: `.github/workflows/`
- **CI Configuration**: `ci/config/`
- **CI Scripts**: `ci/scripts/`
- **Project Scripts**: `scripts/`
- **Development Tools**: `pyproject.toml`

## 🎯 Key Features

- ✅ Automated testing across Python versions
- ✅ Code quality checks (linting, formatting, type checking)
- ✅ Security scanning and vulnerability detection
- ✅ Automated deployment pipelines
- ✅ Pre-commit hooks for local quality assurance
