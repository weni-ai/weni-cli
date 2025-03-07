import pytest
from click.testing import CliRunner
from pathlib import Path

from weni_cli.cli import init
from weni_cli.commands.init import (
    SAMPLE_AGENT_DEFINITION_FILE_NAME,
    SKILLS_FOLDER,
    SAMPLE_GET_ADDRESS_SKILL_NAME,
    DEFAULT_TEST_DEFINITION_FILE,
    SAMPLE_AGENT_DEFINITION_YAML,
    SAMPLE_GET_ADDRESS_SKILL_PY,
    SAMPLE_TESTS_YAML,
    SAMPLE_GET_ADDRESS_REQUIREMENTS_TXT,
)


@pytest.fixture
def cli_runner():
    """Fixture providing a CLI runner with isolated filesystem."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


def test_init_command_exit_code(cli_runner):
    """Test that the init command executes successfully."""
    result = cli_runner.invoke(init)
    assert result.exit_code == 0, f"Command failed with output: {result.output}"


def test_init_command_creates_agent_definition_file(cli_runner):
    """Test that the init command creates the agent definition file."""
    result = cli_runner.invoke(init)

    # Check file existence
    agent_def_file = Path(SAMPLE_AGENT_DEFINITION_FILE_NAME)
    assert agent_def_file.exists(), f"Agent definition file not created: {agent_def_file}"

    # Check file content
    with open(agent_def_file, "r") as f:
        content = f.read()
    assert content == SAMPLE_AGENT_DEFINITION_YAML, "Agent definition file has incorrect content"

    # Check output message
    assert f"Sample agent definition file created in: {SAMPLE_AGENT_DEFINITION_FILE_NAME}" in result.output


def test_init_command_creates_skill_files(cli_runner):
    """Test that the init command creates the skill files."""
    result = cli_runner.invoke(init)

    # Check main.py
    skill_file = Path(f"{SKILLS_FOLDER}/{SAMPLE_GET_ADDRESS_SKILL_NAME}/main.py")
    assert skill_file.exists(), f"Skill file not created: {skill_file}"

    # Check content of main.py
    with open(skill_file, "r") as f:
        content = f.read()
    assert content == SAMPLE_GET_ADDRESS_SKILL_PY, "Skill file has incorrect content"

    # Check requirements.txt
    requirements_file = Path(f"{SKILLS_FOLDER}/{SAMPLE_GET_ADDRESS_SKILL_NAME}/requirements.txt")
    assert requirements_file.exists(), f"Requirements file not created: {requirements_file}"

    # Check content of requirements.txt
    with open(requirements_file, "r") as f:
        content = f.read()
    assert content == SAMPLE_GET_ADDRESS_REQUIREMENTS_TXT, "Requirements file has incorrect content"

    # Check output messages
    assert f"Sample skill {SAMPLE_GET_ADDRESS_SKILL_NAME} created in:" in result.output
    assert f"Sample requirements file for {SAMPLE_GET_ADDRESS_SKILL_NAME} created in:" in result.output


def test_init_command_creates_test_files(cli_runner):
    """Test that the init command creates the test files."""
    result = cli_runner.invoke(init)

    # Check test file
    test_file = Path(f"{SKILLS_FOLDER}/{SAMPLE_GET_ADDRESS_SKILL_NAME}/{DEFAULT_TEST_DEFINITION_FILE}")
    assert test_file.exists(), f"Test file not created: {test_file}"

    # Check content of test file
    with open(test_file, "r") as f:
        content = f.read()
    assert content == SAMPLE_TESTS_YAML, "Test file has incorrect content"

    # Check output message
    assert f"Sample tests file for {SAMPLE_GET_ADDRESS_SKILL_NAME} created in:" in result.output


def test_init_command_creates_required_directories(cli_runner):
    """Test that the init command creates all required directories."""
    cli_runner.invoke(init)

    # Check skills directory
    skills_dir = Path(SKILLS_FOLDER)
    assert skills_dir.exists() and skills_dir.is_dir(), f"Skills directory not created: {skills_dir}"

    # Check skill-specific directory
    skill_dir = Path(f"{SKILLS_FOLDER}/{SAMPLE_GET_ADDRESS_SKILL_NAME}")
    assert skill_dir.exists() and skill_dir.is_dir(), f"Skill directory not created: {skill_dir}"
