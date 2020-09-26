import click


@click.command()
@click.argument("expr")
def main(expr):
    # TODO: better isolation
    print(eval(expr, {}, {}))
