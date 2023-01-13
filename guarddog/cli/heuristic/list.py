from collections.abc import Iterable
from importlib import resources

import click

import guarddog
from guarddog.configs.config import HeuristicConfig, Config


def sorted_by_key(items: Iterable[HeuristicConfig]) -> Iterable[HeuristicConfig]:
    return sorted(items, key=lambda item: item.key)


def contains_key_filter(keys: Iterable[str], items: Iterable[HeuristicConfig]):
    if keys:
        return filter(lambda item: item.key in keys, items)

    return items


def max_key_len(items: Iterable[HeuristicConfig]) -> int:
    return max([len(item.key) for item in items])


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
@click.option("--enabled/--disabled", default=None, help="Filter by disabled status.")
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode.")
def list_command(heuristic, category, enabled, verbose):
    """
    Get a list of all available heuristics.

    Results are returned sorted and its category and disabled status are shown in brackets

        e.g. heuristic_name (category, enabled)
    """

    formatter = click.HelpFormatter()

    def build_section(name, items: Iterable[HeuristicConfig]) -> None:

        filtered_items = [
            item for item in items

            if not heuristic or item.key in heuristic
            if not category or item.category in category
            if enabled is None or bool(item.disabled) != enabled
        ]

        if not filtered_items:
            return

        key_spacing = 0 if verbose else max_key_len(filtered_items)

        with formatter.section(click.style(name, bold=True)):
            for item in sorted_by_key(filtered_items):
                if verbose:
                    with formatter.section(format_item_section(item, key_spacing, bold=True)):
                        formatter.write_text(item.description)
                else:
                    formatter.write_text(format_item_section(item, key_spacing))

    with resources.as_file(resources.files(guarddog).joinpath("../.guarddog.yaml")) as file:
        config = Config().add_config_file(file)

        build_section("Metadata Heuristics", config.get_metadata())
        build_section("Sourcecode Heuristics", config.get_sourcecode())

        click.echo(formatter.getvalue())
