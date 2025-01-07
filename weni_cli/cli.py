import click


# Main CLI Group
@click.group()
def cli():
    """Weni CLI"""


# Login Command
@cli.command("login")
def login():
    """Login with your Weni account"""
    from weni_cli.commands.login import LoginHandler

    LoginHandler().execute()


