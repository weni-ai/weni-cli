import rich_click as click
from weni_cli.utils import print_version, DATE_FORMATS


# Main CLI Group
@click.group()
@click.option(
    "-v",
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Show the version and exit.",
)
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
    """Create a sample agent definition file and tools directory"""
    from weni_cli.commands.init import InitHandler

    InitHandler().execute()


# Run Command
@cli.command("run")
@click.argument("definition", required=True, type=click.Path(exists=True, dir_okay=False))
@click.argument("agent_key", required=True, type=str)
@click.argument("tool_key", required=False, type=str)
@click.option(
    "--file", "-f", help="The path to the test definition file", type=click.Path(exists=True, dir_okay=False)
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run_test(definition, agent_key, tool_key, file, verbose):
    """Run tests for an agent tool (passive) or active agent (preprocessor + rules)

    DEFINITION: The path to the YAML agent definition file
    AGENT_KEY: The agent key to be tested
    TOOL_KEY: The tool key to be tested (required for passive agents, omit for active agents)
    FILE: The path to the test definition file
    """
    from weni_cli.commands.run import RunHandler

    try:
        RunHandler().execute(
            definition=definition, agent_key=agent_key, tool_key=tool_key, test_definition=file, verbose=verbose
        )
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
@click.option("--use-apm", is_flag=True, help="Enable Elastic APM instrumentation for passive agent tool lambdas")
@click.option("--remove-apm", is_flag=True, help="Remove Elastic APM instrumentation from passive agent tool lambdas")
def push_project(definition, force_update, use_apm, remove_apm):
    """Push an Agent definition to the current project

    DEFINITION: The path to the YAML agent definition file
    """
    from weni_cli.commands.project_push import ProjectPushHandler

    try:
        ProjectPushHandler().execute(
            definition=definition,
            force_update=force_update,
            use_apm=use_apm,
            remove_apm=remove_apm,
        )
    except Exception as e:
        click.echo(f"Error: {e}")


@cli.command("logs")
@click.option("--agent", "-a", help="Agent to which the Tool belongs", type=str, required=True)
@click.option("--tool", "-t", help="Tool to which the Logs belong", type=str, required=True)
@click.option("--start-time", "-s", help="Filter by start time (ISO 8601)", type=click.DateTime(formats=DATE_FORMATS), required=False)
@click.option("--end-time", "-e", help="Filter by end time (ISO 8601)", type=click.DateTime(formats=DATE_FORMATS), required=False)
@click.option("--pattern", "-p", help="Filter by pattern", type=str, required=False)
def get_logs(agent, tool, start_time, end_time, pattern):
    """
    Get logs for a specific agent tool, optionally filtered by start and end time and pattern
    """
    from weni_cli.commands.logs import GetLogsHandler

    try:
        GetLogsHandler().get_logs(agent=agent, tool=tool, start_time=start_time, end_time=end_time, pattern=pattern)
    except Exception as e:
        click.echo(f"Error: {e}")


@cli.group()
def channel():
    """Channel management commands"""
    pass


@channel.command("create")
@click.argument("channel_definition", required=True, type=click.Path(exists=True, dir_okay=False))
def create_channel(channel_definition):
    """Create a new channel from a definition file

    CHANNEL_DEFINITION: The path to the YAML channel definition file
    """
    from weni_cli.commands.channel_create import ChannelCreateHandler

    try:
        ChannelCreateHandler().execute(channel_definition=channel_definition)
    except Exception as e:
        click.echo(f"Error: {e}")


@channel.command("list")
@click.option("--type", "-t", "channel_type", help="Filter by channel type (e.g. WAC, WWC)", type=str)
@click.option("--exclude-wpp-demo", is_flag=True, help="Hide the WhatsApp demo channel")
def list_channels(channel_type, exclude_wpp_demo):
    """List channels of the current project"""
    from weni_cli.commands.channel_list import ChannelListHandler

    try:
        ChannelListHandler().execute(channel_type=channel_type, exclude_wpp_demo=exclude_wpp_demo)
    except Exception as e:
        click.echo(f"Error: {e}")


@channel.command("get")
@click.argument("channel_uuid", required=True, type=click.UUID)
@click.option("--show-secrets", is_flag=True, help="Show config values that look like tokens, secrets or keys")
def get_channel(channel_uuid, show_secrets):
    """Show the details of a channel

    CHANNEL_UUID: The UUID of the channel
    """
    from weni_cli.commands.channel_get import ChannelGetHandler

    try:
        ChannelGetHandler().execute(channel_uuid=channel_uuid, show_secrets=show_secrets)
    except Exception as e:
        click.echo(f"Error: {e}")


@channel.command("update")
@click.argument("channel_uuid", required=True, type=click.UUID)
@click.option("--name", "-n", help="New channel name", type=str)
@click.option("--address", "-a", help="New channel address", type=str)
@click.option(
    "--config-file",
    "-c",
    help="YAML/JSON file with config keys to merge into the channel config",
    type=click.Path(exists=True, dir_okay=False),
)
def update_channel(channel_uuid, name, address, config_file):
    """Update the name, address or config of a channel

    CHANNEL_UUID: The UUID of the channel

    Config keys from --config-file are merged into the current config; keys not in the file stay unchanged.
    """
    from weni_cli.commands.channel_update import ChannelUpdateHandler

    try:
        ChannelUpdateHandler().execute(
            channel_uuid=channel_uuid, name=name, address=address, config_file=config_file
        )
    except Exception as e:
        click.echo(f"Error: {e}")


@channel.command("delete")
@click.argument("channel_uuid", required=True, type=click.UUID)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete_channel(channel_uuid, yes):
    """Deactivate a channel (soft delete)

    CHANNEL_UUID: The UUID of the channel
    """
    from weni_cli.commands.channel_delete import ChannelDeleteHandler

    try:
        ChannelDeleteHandler().execute(channel_uuid=channel_uuid, yes=yes)
    except Exception as e:
        click.echo(f"Error: {e}")


@cli.group()
def ticketer():
    """Ticketer management commands"""
    pass


@ticketer.command("create")
@click.argument("ticketer_definition", required=True, type=click.Path(exists=True, dir_okay=False))
def create_ticketer(ticketer_definition):
    """Create a new ticketer from a definition file.

    TICKETER_DEFINITION: Path to the YAML ticketer definition file.

    Generic ticketers authenticate Mailroom → partner with Bearer api_token.
    Optional OAuth2 token refresh is configured in config (all values stored as
    strings). When token_refresh_enabled is true/1/yes, token_refresh_type must
    be custom or refresh and token_refresh_config is serialized as a compact
    JSON string before it is sent to the API.
    """
    from weni_cli.commands.ticketer_create import TicketerCreateHandler

    try:
        TicketerCreateHandler().execute(ticketer_definition=ticketer_definition)
    except Exception as e:
        click.echo(f"Error: {e}")


@ticketer.command("list")
def list_ticketers():
    """List active ticketers in the selected project"""
    from weni_cli.commands.ticketer_list import TicketerListHandler

    try:
        TicketerListHandler().execute()
    except Exception as e:
        click.echo(f"Error: {e}")


@ticketer.command("get")
@click.argument("ticketer_uuid", required=True)
def get_ticketer(ticketer_uuid):
    """Show ticketer details. Secret config values are shown as ***

    TICKETER_UUID: UUID of the ticketer to inspect
    """
    from weni_cli.commands.ticketer_get import TicketerGetHandler

    try:
        TicketerGetHandler().execute(ticketer_uuid=ticketer_uuid)
    except Exception as e:
        click.echo(f"Error: {e}")


@ticketer.command("update")
@click.argument("ticketer_uuid", required=True)
@click.argument("ticketer_definition", required=True, type=click.Path(exists=True, dir_okay=False))
def update_ticketer(ticketer_uuid, ticketer_definition):
    """Replace a ticketer name and config from a definition file

    TICKETER_UUID: UUID of the ticketer to update

    TICKETER_DEFINITION: The path to the YAML ticketer definition file
    """
    from weni_cli.commands.ticketer_update import TicketerUpdateHandler

    try:
        TicketerUpdateHandler().execute(ticketer_uuid=ticketer_uuid, ticketer_definition=ticketer_definition)
    except Exception as e:
        click.echo(f"Error: {e}")


@ticketer.command("delete")
@click.argument("ticketer_uuid", required=True)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
def delete_ticketer(ticketer_uuid, yes):
    """Deactivate a ticketer and close its open tickets

    TICKETER_UUID: UUID of the ticketer to delete
    """
    from weni_cli.commands.ticketer_delete import TicketerDeleteHandler

    try:
        TicketerDeleteHandler().execute(ticketer_uuid=ticketer_uuid, yes=yes)
    except Exception as e:
        click.echo(f"Error: {e}")


@cli.group()
def eval():
    """Agent evaluation commands"""


@eval.command("init")
@click.option(
    "--plan-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
    help="Directory where the evaluation plan file will be created.",
)
def eval_init(plan_dir):
    """Initialize an agent_evaluation.yml plan file"""
    from weni_cli.commands.eval_init import EvalInitHandler

    exit_code = EvalInitHandler().execute(plan_dir=plan_dir)
    if exit_code != 0:
        raise click.exceptions.Exit(exit_code)


@eval.command("run")
@click.option(
    "--filter",
    "test_filter",
    type=str,
    required=False,
    help="Comma-separated list of tests to run.",
)
@click.option(
    "--plan-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
    help="Directory where agent_evaluation.yml is located.",
)
@click.option("--verbose", is_flag=True, default=False, help="Show detailed reasoning for each test result.")
def eval_run(test_filter, plan_dir, verbose):
    """Run agent evaluations from agent_evaluation.yml"""
    from weni_cli.commands.eval_run import EvalRunHandler

    exit_code = EvalRunHandler().execute(
        filter=test_filter,
        plan_dir=plan_dir,
        verbose=verbose,
    )
    if exit_code != 0:
        raise click.exceptions.Exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    cli()
