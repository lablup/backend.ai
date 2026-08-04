"""Guards the `--output` surface of the real command tree: `output_option` is applied by hand,
so it can be forgotten on a new command or collide with a command's own `--output`."""

from collections.abc import Callable, Iterator
from typing import Any, cast

import click

# These imports are what puts the lazily-loaded subtrees in the test sandbox: Pants cannot infer
# them from `LazyGroup(import_name="…")` strings, and without them the walk sees a third of the tree.
from ai.backend.client.cli.deployment import deployment
from ai.backend.client.cli.dotfile import dotfile
from ai.backend.client.cli.fair_share import fair_share
from ai.backend.client.cli.image import image
from ai.backend.client.cli.model import model
from ai.backend.client.cli.network import network
from ai.backend.client.cli.notification import notification
from ai.backend.client.cli.resource_usage import resource_usage
from ai.backend.client.cli.scheduling_history import scheduling_history
from ai.backend.client.cli.server_log import server_logs
from ai.backend.client.cli.service import service
from ai.backend.common.cli import LazyGroup

_IMPORTED_SUBTREES: tuple[click.Group, ...] = (
    deployment,
    dotfile,
    fair_share,
    image,
    model,
    network,
    notification,
    resource_usage,
    scheduling_history,
    server_logs,
    service,
)
_IMPORTED_SUBTREE_NAMES = frozenset({
    "deployment",
    "dotfile",
    "fair-share",
    "image",
    "model",
    "network",
    "notification",
    "resource-usage",
    "scheduling-history",
    "server-logs",
    "service",
})
# No v2 command uses `pass_ctx_obj`, so there is nothing to check there. Giving v2 `--output` is #13431.
_SKIPPED_SUBTREE_NAMES = frozenset({"v2"})

# `update_wrapper` copies `__name__`/`__qualname__` but never `__code__`, so the closure's own
# qualname survives decoration and identifies `pass_ctx_obj` without a marker in production code.
_PASS_CTX_OBJ_CODE = "pass_ctx_obj.<locals>.new_func"


def _routes_through_pass_ctx_obj(callback: Callable[..., Any] | None) -> bool:
    """Follow the `__wrapped__` chain so a decorator applied above `pass_ctx_obj` cannot hide it."""
    seen: set[int] = set()
    fn: Any = callback
    while fn is not None and id(fn) not in seen:
        seen.add(id(fn))
        if getattr(getattr(fn, "__code__", None), "co_qualname", "") == _PASS_CTX_OBJ_CODE:
            return True
        fn = getattr(fn, "__wrapped__", None)
    return False


def _walk_leaf_commands(
    group: click.Group, ctx: click.Context, path: tuple[str, ...] = ()
) -> Iterator[tuple[tuple[str, ...], click.Command]]:
    for name in group.list_commands(ctx):
        if not path and name in _SKIPPED_SUBTREE_NAMES:
            continue
        command = group.get_command(ctx, name)
        match command:
            case None:
                continue
            case click.Group():
                yield from _walk_leaf_commands(command, ctx, (*path, name))
            case _:
                yield (*path, name), command


def test_every_lazy_subtree_is_accounted_for(cli_entrypoint: Callable[[], click.Group]) -> None:
    """A new `LazyGroup` must join the imports and `_IMPORTED_SUBTREE_NAMES`, or
    `_SKIPPED_SUBTREE_NAMES` with a reason -- otherwise the walk below silently shrinks."""
    root = cast(click.Group, cli_entrypoint)
    lazy = {name for name, command in root.commands.items() if isinstance(command, LazyGroup)}
    assert lazy == _IMPORTED_SUBTREE_NAMES | _SKIPPED_SUBTREE_NAMES, (
        f"unaccounted lazily-loaded subtrees: {sorted(lazy - _IMPORTED_SUBTREE_NAMES - _SKIPPED_SUBTREE_NAMES)}"
    )
    assert len(_IMPORTED_SUBTREES) == len(_IMPORTED_SUBTREE_NAMES)


def test_output_option_is_applied_wherever_it_belongs(
    cli_entrypoint: Callable[[], click.Group],
) -> None:
    """Every command holding a `CLIContext` accepts `--output` exactly once: either
    `output_option` or its own (`admin export -o/--output PATH`), never both."""
    root = cast(click.Group, cli_entrypoint)
    ctx = click.Context(root)
    missing: list[str] = []
    duplicated: list[str] = []
    for path, command in _walk_leaf_commands(root, ctx):
        declarations = [param for param in command.params if "--output" in param.opts]
        if len(declarations) > 1:
            duplicated.append(" ".join(path))
        if _routes_through_pass_ctx_obj(command.callback) and not declarations:
            missing.append(" ".join(path))

    assert not duplicated, f"commands declaring `--output` twice: {sorted(set(duplicated))}"
    assert not missing, (
        "commands wearing `pass_ctx_obj` but missing `output_option`: "
        f"{sorted(set(missing))} -- add `@output_option` beneath `@pass_ctx_obj`, or declare the "
        "command's own `--output` if it means something else"
    )
