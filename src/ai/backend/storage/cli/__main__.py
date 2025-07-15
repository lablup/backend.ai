import click

from ai.backend.common.cli import LazyGroup


@click.group(invoke_without_command=False, context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
def main(ctx: click.Context):
    """The root entrypoint for unified CLI of storage-proxy"""
    pass


@main.group(cls=LazyGroup, import_name="ai.backend.storage.cli.config:cli")
def config():
    """Command set for configuration management."""
