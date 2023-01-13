from collections.abc import Iterable
from importlib import resources

import click

import guarddog
from guarddog.configs.config import HeuristicConfig, Config


def sorted_by_key(items: Iterable[HeuristicConfig]) -> Iterable[HeuristicConfig]:
    return sorted(items, key=lambda item: item.key)


def max_key_len(items: Iterable[HeuristicConfig]) -> int:
    return max([len(item.key) for item in items], default=0)


def format_disabled_text(is_disabled: bool) -> str:
    if is_disabled:
        return click.style("disabled", fg="red")
    return click.style("enabled", fg="green")


def format_item_section(item: HeuristicConfig, spacing: int, **style_args) -> str:
    return click.style(
        "%s (%s, %s)" % (
            item.key.ljust(spacing),
            item.category,
            format_disabled_text(item.disabled)
        ),
        **style_args
    )


@click.command("list")
@click.argument("heuristic", nargs=-1)
@click.option("-c", "--category", multiple=True, help="Filter by category.")
@click.option("--disabled/--enabled", default=None, help="Filter by disabled status.")
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode.")
def list_command(heuristic, category, disabled, verbose):
    """
    Get a list of all available heuristics.

    Results are returned sorted and its category and disabled status are shown in brackets

        e.g. heuristic_name (category, enabled)
    """

    formatter = click.HelpFormatter()
    filter_map = {
        "key": heuristic,
        "category": category,
        "disabled": disabled,
    }

    def build_section(name, items: Iterable[HeuristicConfig]) -> None:
        if not items:
            return

        key_spacing = 0 if verbose else max_key_len(items)

        with formatter.section(click.style(name, bold=True)):
            for item in sorted_by_key(items):
                if verbose:
                    with formatter.section(format_item_section(item, key_spacing, bold=True)):
                        formatter.write_text(item.description)
                else:
                    formatter.write_text(format_item_section(item, key_spacing))

    with resources.as_file(resources.files(guarddog).joinpath("../.guarddog.yaml")) as file:
        config = Config().add_config_file(file)

        build_section("Metadata Heuristics", config.get_metadata(**filter_map))
        build_section("Sourcecode Heuristics", config.get_sourcecode(**filter_map))

        click.echo(formatter.getvalue())
