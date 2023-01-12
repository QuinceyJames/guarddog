"""Default execution entry point if running the package via python -m."""

import sys

from guarddog.cli import cli


if __name__ == "__main__":
    sys.exit(cli())
