# Configuration

## Overview

gitdevflow uses a YAML configuration file with environment variable overrides.

## Configuration File

By default, gitdevflow looks for `.gitdevflow.yml` in your project root.

```yaml
# .gitdevflow.yml
github:
  owner: your-username
  repo: your-repo
  token: ${GITHUB_TOKEN}  # Environment variable reference

pr:
  default_base: main
  template: .github/PULL_REQUEST_TEMPLATE.md
  labels:
    - auto-merge

changelog:
  output: CHANGELOG.md
  group_by_labels: true
  categories:
    - name: "✨ Features"
      labels: ["enhancement", "feature"]
    - name: "🐛 Bug Fixes"
      labels: ["bug", "fix"]
    - name: "📚 Documentation"
      labels: ["docs", "documentation"]
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | GitHub personal access token |
| `GITDEVFLOW_CONFIG` | Custom config file path |

## Commands

### `gitdevflow config show`

Display the current configuration.

```bash
gitdevflow config show
```

### `gitdevflow config validate`

Validate the configuration file.

```bash
gitdevflow config validate
```
