import click

from .user_shell import UserShell


@click.command()
@click.argument("expr")
def main(expr):
    user_shell = UserShell()
    user_shell.execute_code(expr)
