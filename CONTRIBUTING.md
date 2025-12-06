# Contributing to Local AI Helper

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork and clone the repository
```bash
git clone https://github.com/yourusername/local-ai-helper.git
cd local-ai-helper
```

2. Set up development environment
```bash
make setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. Create a feature branch
```bash
git checkout -b feature/your-feature-name
```

## Code Standards

### Python Style
- Follow PEP 8 guidelines
- Use Black for formatting: `black src/`
- Check with flake8: `flake8 src/`
- Type hints encouraged: `mypy src/`

### Testing
- Write tests for new features
- Maintain >80% code coverage
- Run tests: `pytest tests/ -v`

### Documentation
- Update README for user-facing changes
- Add docstrings to all functions/classes
- Update architecture docs if needed

## Pull Request Process

1. Update tests and ensure all pass
2. Update documentation as needed
3. Update CHANGELOG if adding features
4. Submit PR with clear description
5. Respond to review feedback

## Code Review Criteria

- Functionality: Does it work as intended?
- Tests: Are there adequate tests?
- Documentation: Is it well documented?
- Style: Follows project conventions?
- Performance: Any performance concerns?

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat(agents): add GPT-4 support to code agent

- Integrate OpenAI API for GPT-4 access
- Add configuration options for API key
- Update tests to cover new functionality

Closes #123
```

## Questions?

Open an issue for discussion before starting major changes.