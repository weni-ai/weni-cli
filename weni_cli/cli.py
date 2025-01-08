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


# Nested CLI Project Group
@cli.group()
def project():
    """Project commands"""


# Project Group Commands
@project.command("list")
@click.option("--org", "-o", help="Filter by organization", type=click.UUID)
def list_projects(org):
    """List projects"""
    from weni_cli.commands.project_list import ProjectListHandler

    ProjectListHandler().execute(org_uuid=org)

