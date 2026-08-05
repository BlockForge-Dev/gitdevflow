# Changelog

## Overview

Automatically generate changelogs from merged pull requests.

## Commands

### `gitdevflow changelog generate`

Generate a changelog from merged PRs since the last release.

```bash
gitdevflow changelog generate --since v0.1.0
```

**Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `--since` | Start tag/commit | Last tag |
| `--output` | Output file | `CHANGELOG.md` |
| `--format` | Output format (`md`, `json`) | `md` |
| `--group-by` | Group entries by label | `true` |

### `gitdevflow changelog validate`

Validate the existing changelog format.

```bash
gitdevflow changelog validate
```
