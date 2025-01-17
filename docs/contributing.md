# Contributing to Weni CLI

Thank you for your interest in contributing to Weni CLI! This guide will help you get started with contributing to the project.

## Development Setup

### Prerequisites

- Python >= 3.12
- Poetry >= 1.8.5
- Git

### Setting Up Development Environment

1. Fork the repository on GitHub

2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/weni-cli.git
   cd weni-cli
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise

### Testing

1. Write tests for new features:
   ```python
   def test_your_feature():
       # Your test code here
       assert expected == actual
   ```

2. Run tests:
   ```bash
   poetry run pytest
   ```

3. Check coverage:
   ```bash
   poetry run pytest --cov
   ```

### Documentation

1. Update documentation for new features
2. Add docstrings to new functions
3. Update README.md if needed
4. Add examples when relevant

## Making Changes

### Workflow

1. Create a feature branch
2. Make your changes
3. Write or update tests
4. Update documentation
5. Run tests locally
6. Commit your changes
7. Push to your fork
8. Create a Pull Request

### Commit Messages

Follow conventional commits:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example:
```bash
git commit -m "feat: add support for custom headers in requests"
```

## Pull Requests

### PR Guidelines

1. Create one PR per feature/fix
2. Include tests
3. Update documentation
4. Reference issues if applicable
5. Keep changes focused and minimal

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Other (specify)

## Testing
Describe testing done

## Documentation
List documentation updates
```

## Review Process

1. Automated checks must pass
2. Code review by maintainers
3. Documentation review
4. Changes requested if needed
5. Approval and merge

## Getting Help

- Create an issue for bugs
- Ask questions in discussions
- Join our community channels

## Development Tools

### Recommended VSCode Extensions

- Python
- YAML
- markdownlint
- GitLens

### Useful Commands

```bash
# Format code
poetry run black .

# Run linter
poetry run flake8

# Run tests
poetry run pytest

# Build documentation
poetry run mkdocs serve
```

## Release Process

1. Version bump
2. Update CHANGELOG
3. Create release PR
4. Tag release
5. Deploy to PyPI

## Community

- Be respectful and inclusive
- Help others when possible
- Share knowledge
- Follow our Code of Conduct

Thank you for contributing to Weni CLI! 🎉
