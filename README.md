# gitdevflow

[![CI](https://github.com/your-username/gitdevflow/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/gitdevflow/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/gitdevflow)](https://pypi.org/project/gitdevflow/)
[![Python](https://img.shields.io/pypi/pyversions/gitdevflow)](https://pypi.org/project/gitdevflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A developer-friendly CLI tool for streamlining Git-based development workflows.

## Features

- **PR Management** — Create, list, and manage pull requests from the terminal
- **Changelog Generation** — Automatically generate changelogs from merged PRs
- **Flexible Configuration** — YAML-based config with environment variable overrides

## Installation

```bash
pip install gitdevflow
```

## Quick Start

```bash
# Set your GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Initialize configuration
gitdevflow config init

# Create a pull request
gitdevflow pr create --title "Add feature X" --base main

# List open PRs
gitdevflow pr list

# Generate changelog
gitdevflow changelog generate --since v0.1.0
```

## Development

```bash
# Clone the repository
git clone https://github.com/your-username/gitdevflow.git
cd gitdevflow

# Install dependencies
poetry install --with dev

# Run tests
make test

# Run linters
make lint

# Run type checker
make type-check
```

## Documentation

Full documentation is available at [https://your-username.github.io/gitdevflow/](https://your-username.github.io/gitdevflow/).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
