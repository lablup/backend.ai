"""
Guards the `--output` surface of the real command tree.

`output_option` is applied by hand on ~150 commands, so unlike an injected option it can be
forgotten on a new command, or applied twice on one that already declares its own `--output`.
Nothing in `extensions.py` prevents either -- this does.
"""

from collections.abc import Callable, Iterator
from typing import Any, cast

import click

# The client CLI loads its subtrees through `LazyGroup(import_name="ai.backend.client.cli.…")`,
# and Pants' dependency inference cannot see those string literals. Importing each group for real
# is what puts its module in the test sandbox; without this the walk below reaches 194 of the 630
# leaf commands and reports success on the third it can see.
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
# `v2` is deliberately out of scope, not merely unimported: no v2 command uses `pass_ctx_obj` --
# they render through `print_result()` -- so the invariant below has nothing to check there.
# Its subgroups are lazily loaded in turn, so importing it would pull in ~40 further modules.
# Giving v2 an `--output` at all is #13431.
_SKIPPED_SUBTREE_NAMES = frozenset({"v2"})

# `pass_ctx_obj` wraps the command callback in a closure of this qualified name. `update_wrapper`
# copies `__name__`/`__qualname__` from the wrapped function but never `__code__`, so this survives
# the copy and identifies the decorator without production code carrying a marker for the test.
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
    """
    Fails loudly when a `LazyGroup` is added, instead of letting the walk below quietly shrink.
    Add the new subtree to the imports and to `_IMPORTED_SUBTREE_NAMES`, or to
    `_SKIPPED_SUBTREE_NAMES` with a reason.
    """
    root = cast(click.Group, cli_entrypoint)
    lazy = {name for name, command in root.commands.items() if isinstance(command, LazyGroup)}
    assert lazy == _IMPORTED_SUBTREE_NAMES | _SKIPPED_SUBTREE_NAMES, (
        f"unaccounted lazily-loaded subtrees: {sorted(lazy - _IMPORTED_SUBTREE_NAMES - _SKIPPED_SUBTREE_NAMES)}"
    )
    assert len(_IMPORTED_SUBTREES) == len(_IMPORTED_SUBTREE_NAMES)


def test_output_option_is_applied_wherever_it_belongs(
    cli_entrypoint: Callable[[], click.Group],
) -> None:
    """
    Every command holding a `CLIContext` accepts `--output`: either `output_option`, or its own
    (`admin export -o/--output PATH`, a destination file). Never both -- Click registers the two
    silently and leaves one dead in its long-option table.
    """
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
