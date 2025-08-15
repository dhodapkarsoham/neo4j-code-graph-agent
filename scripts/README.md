# Project Scripts

This directory contains automation scripts and tools for the Code Graph Agent project.

## 📁 Contents

- **Makefile** - Common development commands and shortcuts
- **README.md** - This file

## 🛠️ Available Commands

The Makefile provides convenient shortcuts for common development tasks:

```bash
# Show all available commands
make help

# Development
make install-dev      # Install development dependencies
make run-dev          # Run development server
make run-prod         # Run production server

# Testing
make test             # Run tests
make test-cov         # Run tests with coverage

# Code Quality
make lint             # Run all linting checks
make format           # Format code
make security-check   # Run security checks

# CI/CD
make ci-local         # Run all CI checks locally
make check-all        # Run test, lint, and security checks

# Maintenance
make clean            # Clean up generated files
make update-deps      # Update dependencies
```

## 🔗 Related Directories

- **CI Scripts**: `ci/scripts/` - CI/CD specific scripts
- **CI Configuration**: `ci/config/` - CI/CD configuration files
- **Documentation**: `docs/ci-cd/` - CI/CD documentation

## 💡 Usage Tips

1. **Always run `make help`** to see available commands
2. **Use `make ci-local`** before pushing to run all checks
3. **Use `make format`** to automatically format your code
4. **Use `make clean`** if you encounter build issues
