import click
from socketchat.window import run_app

@click.command()
def schat():
    run_app()


if __name__ == "__main__":
    schat()
