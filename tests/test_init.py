import os
from click.testing import CliRunner


from weni_cli.cli import init
from weni_cli.commands.init import SAMPLE_AGENT_DEFINITION_FILE_NAME, SKILLS_FOLDER


def test_init_command():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(init)

        assert result.exit_code == 0

        assert (
            result.output
            == f"Sample agent definition file created in: {SAMPLE_AGENT_DEFINITION_FILE_NAME}\nSample skill order_status created in: {SKILLS_FOLDER}/order_status.zip\nSample skill order_details created in: {SKILLS_FOLDER}/order_details.zip\n"
        )

        assert os.path.exists(SAMPLE_AGENT_DEFINITION_FILE_NAME)
        assert os.path.exists(f"{SKILLS_FOLDER}/order_status.zip")
        assert os.path.exists(f"{SKILLS_FOLDER}/order_details.zip")
