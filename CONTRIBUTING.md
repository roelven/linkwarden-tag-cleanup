# Contributing to Linkwarden Tag Cleanup Tools

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

- Check existing issues before creating a new one
- Provide clear reproduction steps
- Include your environment (Python version, OS, Linkwarden version)
- Share relevant error messages and logs

### Suggesting Features

- Open an issue with the "enhancement" label
- Describe the use case and expected behavior
- Explain why this would be useful to others

### Code Contributions

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/linkwarden-cleanup.git
   cd linkwarden-cleanup
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed

4. **Test your changes**
   - Run existing tests
   - Add new tests for new features
   - Test with a real Linkwarden instance if possible

5. **Commit your changes**
   ```bash
   git commit -m "Add: brief description of changes"
   ```

6. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 for Python code
- Use descriptive variable names
- Add docstrings to functions and classes
- Keep functions focused and small
- Use type hints where appropriate

## Testing

- Test with dry-run mode first
- Verify API calls work correctly
- Check edge cases (empty results, API errors, etc.)
- Test with different Linkwarden versions if possible

## Documentation

- Update README.md if changing core functionality
- Update relevant docs in `docs/` directory
- Add examples for new features
- Keep documentation clear and concise

## Pull Request Process

1. Update documentation for any changed functionality
2. Add or update tests as needed
3. Ensure all tests pass
4. Update CHANGELOG if applicable
5. Request review from maintainers

## Areas for Contribution

### High Priority
- Additional tag detection algorithms
- Performance optimizations
- Better error handling
- More comprehensive tests

### Medium Priority
- Web UI for configuration
- Additional LLM integrations
- Tag analytics and reporting
- Bulk operations API

### Low Priority
- Additional language support
- Docker containerization
- CI/CD pipeline
- Integration tests

## Questions?

Feel free to open an issue with the "question" label or reach out to the maintainers.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the problem, not the person
- Help others learn and grow

Thank you for contributing! 🎉
