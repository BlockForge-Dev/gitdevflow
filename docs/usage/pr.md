# PR Commands

## Overview

Manage pull requests directly from your terminal.

## Commands

### `gitdevflow pr create`

Create a new pull request.

```bash
gitdevflow pr create --title "Add feature X" --base main
```

**Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `--title` | PR title | Required |
| `--base` | Base branch | `main` |
| `--draft` | Create as draft | `false` |
| `--body` | PR description | Empty |

### `gitdevflow pr list`

List open pull requests.

```bash
gitdevflow pr list --state open --limit 10
```

### `gitdevflow pr merge`

Merge a pull request.

```bash
gitdevflow pr merge 42 --strategy squash
```
