import shutil
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from typing import Any, Literal

import click
from tabulate import tabulate

from ai.backend.client.output.types import FieldSpec
from ai.backend.client.pagination import MAX_PAGE_SIZE


def get_preferred_page_size() -> int:
    return min(MAX_PAGE_SIZE, shutil.get_terminal_size((80, 20)).lines)


_Item = Mapping[str, Any]


def tabulate_items(
    items: Iterator[_Item],
    fields: Sequence[FieldSpec],
    *,
    page_size: int | None = None,
    item_formatter: Callable[[_Item], None] | None = None,
    tablefmt: Literal["simple", "plain", "github"] = "simple",
) -> Iterator[str]:
    is_first = True
    output_count = 0
    buffered_items: list[_Item] = []
    # Column widths pinned from the first chunk's data + headers.
    # Subsequent chunks pad cells to (at least) these widths so that
    # `tabulate()` — called once per chunk for streaming/pager support —
    # produces identical column widths across chunks. Without pinning,
    # each chunk would compute widths from only its own data, causing
    # visible misalignment partway through long listings (BA-2959 / #6632).
    # We do not shrink widths once established; later chunks may grow a
    # column only if a wider value appears, which is rare and a much
    # smaller visual artifact than the per-chunk recomputation default.
    pinned_widths: list[int] = []

    # check table header/footer sizes
    header_height = 0
    if tablefmt in ("simple", "github"):
        header_height = 2
    if header_height < 0:
        raise ValueError("Header height must be non-negative")

    def _tabulate_buffer() -> Iterator[str]:
        # Pre-format every cell to a string so we can pad to pinned widths
        # before handing rows to tabulate().
        formatted_rows: list[list[str]] = [
            [f.formatter.format_console(v, f) for f, v in zip(fields, item.values(), strict=True)]
            for item in buffered_items
        ]
        headers: list[str] = (
            [] if tablefmt == "plain" else [field.humanized_name for field in fields]
        )

        if is_first:
            # Establish pinned widths from this chunk's headers and rows.
            num_cols = len(fields)
            widths = [0] * num_cols
            if headers:
                for i, h in enumerate(headers):
                    if len(h) > widths[i]:
                        widths[i] = len(h)
            for row in formatted_rows:
                for i, cell in enumerate(row):
                    if len(cell) > widths[i]:
                        widths[i] = len(cell)
            pinned_widths.extend(widths)
        else:
            # Allow widening only if a later cell exceeds the pinned width.
            # We cannot rewrite already-emitted output, so this just keeps
            # subsequent chunks self-consistent in that rare case.
            for row in formatted_rows:
                for i, cell in enumerate(row):
                    if len(cell) > pinned_widths[i]:
                        pinned_widths[i] = len(cell)

        # Pad each cell to the pinned width so tabulate() computes the
        # same column widths it produced for the first chunk.
        padded_rows: list[list[str]] = [
            [cell.ljust(pinned_widths[i]) for i, cell in enumerate(row)] for row in formatted_rows
        ]

        table = tabulate(
            padded_rows,
            headers=headers,
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
    yield from _tabulate_buffer()


def echo_via_pager(
    text_generator: Iterator[str],
    break_callback: Callable[[], None] | None = None,
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
