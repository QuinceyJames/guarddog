import click

from guarddog.cli.heuristic.list import list_command


@click.group("heuristic")
def heuristic_command():
    """Information about the available heuristics"""
    pass


heuristic_command.add_command(list_command)
