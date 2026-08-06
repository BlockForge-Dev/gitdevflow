# gitdevflow

[![CI](https://github.com/BlockForge-Dev/gitdevflow/actions/workflows/ci.yml/badge.svg)](https://github.com/BlockForge-Dev/gitdevflow/actions/workflows/ci.yml)
[![Docs](https://github.com/BlockForge-Dev/gitdevflow/actions/workflows/docs.yml/badge.svg)](https://BlockForge-Dev.github.io/gitdevflow/)
[![PyPI](https://img.shields.io/pypi/v/gitdevflow)](https://pypi.org/project/gitdevflow/)
[![Python](https://img.shields.io/pypi/pyversions/gitdevflow)](https://pypi.org/project/gitdevflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**gitdevflow** is a modern, developer-friendly CLI tool for automating Git-based development workflows, Conventional Commit validation, PR management, and automated changelog generation.

---

## Key Features

- 🐙 **Pull Request Management** — Create, list, check Conventional Commits, auto-label, and merge pull requests directly from your terminal.
- 📜 **Changelog Generation** — Automatically generate structured release notes in Markdown or JSON from git tag/commit comparisons and merged PRs.
- 🎨 **Rich Terminal UX** — Beautiful, colored terminal output, interactive setup wizards, progress bars, and Markdown previews using [Rich](https://github.com/Textualize/rich).
- ⚙️ **Flexible Configuration** — Layered 12-factor configuration via YAML (`~/.gitdevflow.yaml`) and environment variable overrides (`GITHUB_TOKEN`).
- 🤖 **Commit Compliance** — Enforce Conventional Commit title and branch naming conventions for CI pipelines.

---

## Installation

### Using pip
```bash
pip install gitdevflow
```

### Using pipx (Recommended for CLI tools)
```bash
pipx install gitdevflow
```

### From Source
```bash
git clone https://github.com/BlockForge-Dev/gitdevflow.git
cd gitdevflow
poetry install
```

---

## Quick Start

### 1. Initialize Configuration
```bash
export GITHUB_TOKEN="ghp_your_github_personal_access_token"
gitdevflow config init
```

### 2. PR Management
```bash
# List open PRs as a styled Rich table
gitdevflow pr list --repo owner/repository

# Check PR title compliance against Conventional Commits
gitdevflow pr check --repo owner/repository

# Automatically auto-label PRs based on branch/title prefix rules
gitdevflow pr label --repo owner/repository

# Create a new PR interactively
gitdevflow pr create --repo owner/repository --base main
```

### 3. Changelog Generation
```bash
# Generate Markdown changelog between tags
gitdevflow changelog generate --from-ref v0.1.0 --to-ref HEAD --output CHANGELOG.md

# Export changelog as structured JSON
gitdevflow changelog generate --from-ref v0.1.0 --output - --format json
```

---

## Documentation

Full documentation is available at [https://BlockForge-Dev.github.io/gitdevflow/](https://BlockForge-Dev.github.io/gitdevflow/).

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on setting up your environment and submitting pull requests.

---

## License

Licensed under the [MIT License](LICENSE).
