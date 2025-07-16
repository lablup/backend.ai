import click

from ai.backend.common.cli import LazyGroup


@click.group()
@click.pass_context
def main(ctx: click.Context):
    """The root entrypoint for unified CLI of the web server"""
    pass


@main.group(cls=LazyGroup, import_name="ai.backend.web.cli.config:cli")
def config():
    """Command set for configuration management."""
