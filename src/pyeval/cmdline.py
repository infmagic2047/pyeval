import click

from .code_transform import AutoImportTransformer
from .user_shell import UserShell


@click.command()
@click.argument("expr")
@click.option("--verbose", is_flag=True)
def main(expr, verbose):
    user_shell = UserShell(transformers=[AutoImportTransformer(verbose=verbose)])
    user_shell.execute_code(expr)
