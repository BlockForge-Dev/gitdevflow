# Contributing to gitdevflow

Thank you for your interest in contributing to **gitdevflow**!

Please review our [Contributing Guidelines](https://github.com/BlockForge-Dev/gitdevflow/blob/main/CONTRIBUTING.md) and [Code of Conduct](https://github.com/BlockForge-Dev/gitdevflow/blob/main/CODE_OF_CONDUCT.md).

## Local Development Workflow

1. **Clone Repository & Install Dependencies**:
   ```bash
   git clone https://github.com/BlockForge-Dev/gitdevflow.git
   cd gitdevflow
   poetry install --with dev,docs
   ```

2. **Pre-commit Hooks**:
   ```bash
   poetry run pre-commit install
   ```

3. **Running Quality Checks**:
   ```bash
   poetry run ruff check --fix src/ tests/
   poetry run black src/ tests/
   poetry run mypy src/
   poetry run pytest
   ```

4. **Building Documentation**:
   ```bash
   poetry run mkdocs serve
   ```
