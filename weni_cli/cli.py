import rich_click as click


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


# Init Command
@cli.command("init")
def init():
    """Create a sample agent definition file and skills directory"""
    from weni_cli.commands.init import InitHandler

    InitHandler().execute()


# Run Command
@cli.command("run")
@click.argument("definition", required=True, type=click.Path(exists=True, dir_okay=False))
@click.argument("agent", required=True, type=str)
@click.argument("skill", required=True, type=str)
@click.option(
    "--file", "-f", help="The path to the test definition file", type=click.Path(exists=True, dir_okay=False)
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run_test(definition, agent, skill, file, verbose):
    """Run tests for a specific agent skill

    DEFINITION: The path to the YAML agent definition file
    AGENT: The agent name to be tested
    SKILL: The skill name to be tested
    FILE: The path to the test definition file
    """
    from weni_cli.commands.run import RunHandler

    try:
        RunHandler().execute(definition=definition, agent=agent, skill=skill, test_definition=file, verbose=verbose)
    except Exception as e:
        click.echo(f"Error: {e}")


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


@project.command("use")
@click.argument("project_uuid", required=True)
def use_project(project_uuid):
    """Set the project to be used in the CLI

    PROJECT_UUID: The UUID of the project to be used
    """
    from weni_cli.commands.project_use import ProjectUseHandler

    ProjectUseHandler().execute(project_uuid=project_uuid)


@project.command("current")
def current_project():
    """Show current selected project"""
    from weni_cli.commands.project_current import ProjectCurrentHandler

    ProjectCurrentHandler().execute()


@project.command("push")
@click.argument("definition", required=True, type=click.Path(exists=True, dir_okay=False))
@click.option("--force-update", is_flag=True, help="Force update to the project")
def push_project(definition, force_update):
    """Push an Agent definition to the current project

    DEFINITION: The path to the YAML agent definition file
    """
    from weni_cli.commands.project_push import ProjectPushHandler

    try:
        ProjectPushHandler().execute(definition=definition, force_update=force_update)
    except Exception as e:
        click.echo(f"Error: {e}")


if __name__ == "__main__":
    cli()
