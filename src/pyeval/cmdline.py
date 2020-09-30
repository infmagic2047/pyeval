import click

from . import __version__
from .code_transform import AutoImportTransformer
from .user_shell import UserShell


@click.command()
@click.argument("expr")
@click.option("-v", "--verbose", is_flag=True, help="Show more information.")
@click.version_option(version=__version__)
def main(expr, verbose):
    user_shell = UserShell(transformers=[AutoImportTransformer(verbose=verbose)])
    user_shell.execute_code(expr)
