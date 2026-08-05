# Installation

## Requirements

- Python 3.10+
- Git 2.30+
- A GitHub personal access token (for API operations)

## Install from PyPI

```bash
pip install gitdevflow
```

## Install from source

```bash
git clone https://github.com/BlockForge-Dev/gitdevflow.git
cd gitdevflow
pip install -e ".[dev]"
```

## Configuration

After installation, create a configuration file:

```bash
gitdevflow config init
```

Set your GitHub token as an environment variable:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Or add it to your `.env` file. See [Configuration](usage/config.md) for more details.
