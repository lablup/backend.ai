import shutil
import sys
from typing import Any, Callable, Iterator, List, Literal, Mapping, Sequence

import click
from tabulate import tabulate

from ai.backend.client.output.types import FieldSpec

from ..pagination import MAX_PAGE_SIZE


def get_preferred_page_size() -> int:
    return min(MAX_PAGE_SIZE, shutil.get_terminal_size((80, 20)).lines)


_Item = Mapping[str, Any]


def tabulate_items(
    items: Iterator[_Item],
    fields: Sequence[FieldSpec],
    *,
    page_size: int = None,
    item_formatter: Callable[[_Item], None] = None,
    tablefmt: Literal["simple", "plain", "github"] = "simple",
) -> Iterator[str]:
    is_first = True
    output_count = 0
    buffered_items: List[_Item] = []

    # check table header/footer sizes
    header_height = 0
    if tablefmt in ("simple", "github"):
        header_height = 2
    assert header_height >= 0

    def _tabulate_buffer() -> Iterator[str]:
        table = tabulate(
            [
                [f.formatter.format_console(v, f) for f, v in zip(fields, item.values())]
                for item in buffered_items
            ],
            headers=([] if tablefmt == "plain" else [field.humanized_name for field in fields]),
            tablefmt=tablefmt,
        )
        table_rows = table.splitlines()
        if is_first:
            yield from (row + "\n" for row in table_rows)
        else:
            # strip the header for continued page outputs
            yield from (row + "\n" for row in table_rows[header_height:])

    # If we iterate until the end of items, pausing the terminal output
    # would not have effects for avoiding unnecessary queries for subsequent pages.
    # Let's buffer the items and split the formatting per page.
    if page_size is None:
        table_height = shutil.get_terminal_size((80, 20)).lines
    else:
        table_height = page_size
    page_size = max(table_height - header_height - 1, 10)
    for item in items:
        if item_formatter is not None:
            item_formatter(item)
        buffered_items.append(item)
        output_count += 1
        if output_count == page_size:
            yield from _tabulate_buffer()
            buffered_items.clear()
            is_first = False
            output_count = 0
            page_size = max(table_height - 1, 10)
    if output_count > 0:
        yield from _tabulate_buffer()


def echo_via_pager(
    text_generator: Iterator[str],
    break_callback: Callable[[], None] = None,
) -> None:
    """
    A variant of ``click.echo_via_pager()`` which implements our own simplified pagination.
    The key difference is that it holds the generator for each page, so that the generator
    won't continue querying the next results unless continued, avoiding server overloads.
    """
    # TODO: support PageUp & PageDn by buffering the output
    terminal_height = shutil.get_terminal_size((80, 20)).lines
    line_count = 0
    for text in text_generator:
        line_count += text.count("\n")
        click.echo(text, nl=False)
        if line_count == terminal_height - 1:
            if sys.stdin.isatty() and sys.stdout.isatty():
                click.echo(":", nl=False)
                # Pause the terminal so that we don't execute next-page queries indefinitely.
                # Since click.pause() ignores KeyboardInterrupt, we just use click.getchar()
                # to allow user interruption.
                k = click.getchar(echo=False)
                if k in ("q", "Q"):
                    if break_callback is not None:
                        break_callback()
                    break
                click.echo("\r", nl=False)
            line_count = 0
