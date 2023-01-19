"""Default execution entry point if running the package via python -m."""

import sys
from importlib import resources

import guarddog
from guarddog.cli import cli
from guarddog.configs.config import Config

if __name__ == "__main__":
    with resources.as_file(resources.files(guarddog).joinpath("../.guarddog.yaml")) as file:
        sys.exit(cli(obj=Config().add_config_file(file)))
