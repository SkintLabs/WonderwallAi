# Contributing to WonderwallAi

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/SkintLabs/WonderwallAi.git
cd wonderwallai

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

All tests should pass without any API keys or external services. The test suite uses mocks for the Groq API and embedding model.

## Code Style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check wonderwallai/ tests/
ruff format wonderwallai/ tests/
```

## Pull Requests

1. Fork the repo and create a feature branch from `main`
2. Write tests for any new functionality
3. Ensure all tests pass and linting is clean
4. Open a PR with a clear description of the change

## What to Work On

Check the [Issues](https://github.com/SkintLabs/WonderwallAi/issues) page for open tasks. Good first issues are tagged with `good first issue`.

Areas where contributions are especially welcome:
- Additional API key detection patterns (new providers)
- PII pattern improvements
- Pre-built topic sets for new industries
- Documentation and examples
- Performance optimizations

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
