import click

from ai.backend.common.cli import LazyGroup


@click.group()
@click.pass_context
def main(ctx: click.Context):
    """The root entrypoint for unified CLI of agent"""
    pass


@main.group(cls=LazyGroup, import_name="ai.backend.agent.cli.config:cli")
def config():
    """Command set for configuration management."""
