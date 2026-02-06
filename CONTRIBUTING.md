# Contributing to Apprentice MCP Agent

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork and clone the repository
2. Run the setup script:
   ```bash
   bash setup.sh
   ```
3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
4. Configure your `.env` file with test credentials

## Running Tests

Run all tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_agent.py -v
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all public functions and classes
- Keep functions focused and small

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Add/update tests as needed
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request with a clear description

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or error messages

## Questions?

Feel free to open an issue for any questions or discussions.
