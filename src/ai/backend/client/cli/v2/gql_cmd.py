"""``backend.ai v2 gql`` CLI command for raw GraphQL queries."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click

from .helpers import create_v2_registry, load_v2_config, print_result


@click.command()
@click.argument("query", required=False)
@click.option(
    "-f",
    "--file",
    "query_file",
    type=click.Path(exists=True),
    default=None,
    help="Read the GraphQL query from a file instead of an argument.",
)
@click.option(
    "--var",
    "variables",
    multiple=True,
    help="Query variable as key=value (e.g., --var limit=5). Repeatable.",
)
@click.option(
    "--v2",
    "use_v2",
    is_flag=True,
    default=False,
    help="Target the Strawberry (v2) schema. Only needed in direct API mode; "
    "session mode serves both schemas on a single endpoint.",
)
def gql(
    query: str | None,
    query_file: str | None,
    variables: tuple[str, ...],
    use_v2: bool,
) -> None:
    """Send a raw GraphQL query to the Backend.AI server.

    \b
    Examples:
      ./bai gql '{ keypair_list(limit: 3, offset: 0) { items { access_key } } }'
      ./bai gql --v2 '{ myKeypairs(first: 5) { count edges { node { accessKey } } } }'
      ./bai gql -f query.graphql
      echo '{ domain(name: "default") { name } }' | ./bai gql
    """
    # Resolve query source: argument > file > stdin
    if query is None and query_file is None:
        if not sys.stdin.isatty():
            query = sys.stdin.read().strip()
        if not query:
            click.echo("Error: Provide a query as argument, --file, or via stdin.", err=True)
            raise SystemExit(1)
    elif query_file is not None:
        query = Path(query_file).read_text().strip()

    if not query:
        click.echo("Error: Empty query.", err=True)
        raise SystemExit(1)

    # Parse variables
    vars_dict: dict[str, str] | None = None
    if variables:
        vars_dict = {}
        for v in variables:
            if "=" not in v:
                click.echo(f"Error: Variable must be key=value, got: {v}", err=True)
                raise SystemExit(1)
            key, value = v.split("=", 1)
            vars_dict[key] = value

    async def _run() -> None:
        registry = await create_v2_registry(load_v2_config())
        try:
            result = await registry.gql.query(query, variables=vars_dict, v2=use_v2)
            print_result(result)
        finally:
            await registry.close()

    asyncio.run(_run())
