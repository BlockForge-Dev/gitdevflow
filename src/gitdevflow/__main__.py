"""Allow running gitdevflow as a module: python -m gitdevflow."""

from gitdevflow.cli import app


def main() -> None:
    """Module entrypoint."""
    app()


if __name__ == "__main__":
    main()
