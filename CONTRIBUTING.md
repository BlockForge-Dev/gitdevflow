# Contributing to gitdevflow

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

1. Fork and clone the repository
2. Install [Poetry](https://python-poetry.org/docs/#installation)
3. Install dependencies:
   ```bash
   poetry install --with dev
   ```
4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Workflow

1. Create a feature branch from `develop`:
   ```bash
   git checkout -b feature/your-feature develop
   ```
2. Make your changes and write tests
3. Run the test suite:
   ```bash
   make test
   ```
4. Run linters and type checks:
   ```bash
   make lint
   make type-check
   ```
5. Commit your changes with a [conventional commit](https://www.conventionalcommits.org/) message:
   ```bash
   git commit -m "feat: add new PR template support"
   ```
6. Push your branch and open a PR against `develop`

## Code Style

- We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Type annotations are required for all public functions
- Docstrings follow the Google style

## Testing

- Tests are written with [pytest](https://docs.pytest.org/)
- Aim for high test coverage on new code
- Use fixtures from `tests/conftest.py` for common test data

## Reporting Issues

- Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) for bugs
- Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) for enhancements
