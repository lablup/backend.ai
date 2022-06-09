import click

from .extensions import ExtendedCommandGroup


@click.group(
    cls=ExtendedCommandGroup,
    context_settings={
        'help_option_names': ['-h', '--help'],
    },
)
def main() -> click.Group:
    '''Unified Command Line Interface for Backend.ai'''
    pass
