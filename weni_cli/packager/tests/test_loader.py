"""Tests for the shared agent resource loaders."""

import io
import os

import pytest
from click.testing import CliRunner

from weni_cli.packager import loader


def _fake_zip(content: bytes = b"fake zip"):
    return io.BytesIO(content)


@pytest.fixture
def passive_definition() -> dict:
    return {
        "agents": {
            "agent_a": {
                "name": "Agent A",
                "tools": [
                    {
                        "tool_a": {
                            "name": "Tool A",
                            "source": {"path": "tools/tool_a", "entrypoint": "main.Tool"},
                        }
                    }
                ],
            }
        }
    }


@pytest.fixture
def active_definition() -> dict:
    return {
        "agents": {
            "agent_a": {
                "name": "Agent A",
                "rules": {
                    "rule_x": {
                        "name": "Rule X",
                        "template": "tpl_x",
                        "source": {"path": "rules/rule_x", "entrypoint": "main.RuleX"},
                    }
                },
                "pre_processing": {
                    "name": "PP",
                    "source": {"path": "pre_processors/processor", "entrypoint": "processing.PreProcessor"},
                    "result_examples_file": "result_example.json",
                },
            }
        }
    }


class TestLoadToolsFolders:
    def test_returns_zip_for_each_tool(self, mocker, passive_definition):
        mocker.patch.object(
            loader,
            "create_agent_resource_folder_zip",
            return_value=(_fake_zip(b"tool"), None),
        )

        result, error = loader.load_tools_folders(passive_definition)

        assert error is None
        assert "agent_a:tool_a" in result
        assert result["agent_a:tool_a"].read() == b"tool"

    def test_returns_error_when_zip_fails(self, mocker, passive_definition):
        mocker.patch.object(
            loader,
            "create_agent_resource_folder_zip",
            return_value=(None, Exception("boom")),
        )

        result, error = loader.load_tools_folders(passive_definition)

        assert result is None
        assert error is not None
        assert "Failed to create tool folder" in error
        assert "boom" in error


class TestLoadRulesFolders:
    def test_returns_zip_for_each_rule(self, mocker, active_definition):
        mocker.patch.object(
            loader,
            "create_agent_resource_folder_zip",
            return_value=(_fake_zip(b"rule"), None),
        )

        result, error = loader.load_rules_folders(active_definition)

        assert error is None
        assert "agent_a:rule_x" in result

    def test_returns_error_when_zip_fails(self, mocker, active_definition):
        mocker.patch.object(
            loader,
            "create_agent_resource_folder_zip",
            return_value=(None, Exception("boom")),
        )

        result, error = loader.load_rules_folders(active_definition)

        assert result is None
        assert error is not None
        assert "Failed to create rule folder" in error


class TestLoadPreprocessingFolder:
    def test_returns_preprocessor_and_example(self, mocker, active_definition):
        mocker.patch.object(
            loader,
            "create_agent_resource_folder_zip",
            return_value=(_fake_zip(b"pre"), None),
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            os.makedirs("pre_processors/processor", exist_ok=True)
            with open(f"pre_processors/processor{os.sep}result_example.json", "w") as f:
                f.write('{"foo": "bar"}')

            result, error = loader.load_preprocessing_folder(active_definition)

        assert error is None
        assert "agent_a:preprocessor_folder" in result
        assert "agent_a:preprocessor_example" in result

    def test_skips_agents_without_pre_processing(self, mocker):
        mocker.patch.object(loader, "create_agent_resource_folder_zip", return_value=(_fake_zip(), None))
        definition = {"agents": {"agent_a": {"name": "Agent A"}}}

        result, error = loader.load_preprocessing_folder(definition)

        assert error is None
        assert result == {}

    def test_returns_error_when_example_file_missing(self, mocker, active_definition):
        mocker.patch.object(
            loader,
            "create_agent_resource_folder_zip",
            return_value=(_fake_zip(b"pre"), None),
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            result, error = loader.load_preprocessing_folder(active_definition)

        assert result is None
        assert error is not None
        assert "Failed to open preprocessing example" in error

    def test_returns_error_when_zip_fails(self, mocker, active_definition):
        mocker.patch.object(
            loader,
            "create_agent_resource_folder_zip",
            return_value=(None, Exception("boom")),
        )

        result, error = loader.load_preprocessing_folder(active_definition)

        assert result is None
        assert error is not None
        assert "Failed to create preprocessing folder" in error


class TestLoadActiveAgentResources:
    def test_combines_rules_and_preprocessor(self, mocker, active_definition):
        mocker.patch.object(
            loader,
            "create_agent_resource_folder_zip",
            return_value=(_fake_zip(b"data"), None),
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            os.makedirs("pre_processors/processor", exist_ok=True)
            with open(f"pre_processors/processor{os.sep}result_example.json", "w") as f:
                f.write("{}")

            result, error = loader.load_active_agent_resources(active_definition)

        assert error is None
        assert "agent_a:rule_x" in result
        assert "agent_a:preprocessor_folder" in result
        assert "agent_a:preprocessor_example" in result

    def test_scopes_to_specific_agent(self, mocker):
        mocker.patch.object(
            loader,
            "create_agent_resource_folder_zip",
            return_value=(_fake_zip(b"data"), None),
        )

        definition = {
            "agents": {
                "agent_a": {
                    "name": "Agent A",
                    "rules": {
                        "rule_x": {
                            "name": "Rule X",
                            "template": "tpl_x",
                            "source": {"path": "rules/rule_x", "entrypoint": "main.RuleX"},
                        }
                    },
                    "pre_processing": {
                        "name": "PP",
                        "source": {
                            "path": "pre_processors/agent_a",
                            "entrypoint": "processing.PreProcessor",
                        },
                    },
                },
                "agent_b": {
                    "name": "Agent B",
                    "rules": {
                        "rule_y": {
                            "name": "Rule Y",
                            "template": "tpl_y",
                            "source": {"path": "rules/rule_y", "entrypoint": "main.RuleY"},
                        }
                    },
                    "pre_processing": {
                        "name": "PP",
                        "source": {
                            "path": "pre_processors/agent_b",
                            "entrypoint": "processing.PreProcessor",
                        },
                    },
                },
            }
        }

        result, error = loader.load_active_agent_resources(definition, agent_key="agent_a")

        assert error is None
        keys = list(result.keys())
        assert all(k.startswith("agent_a:") for k in keys), keys
        assert "agent_b:rule_y" not in result

    def test_returns_error_when_agent_not_found(self):
        result, error = loader.load_active_agent_resources({"agents": {}}, agent_key="missing")
        assert result is None
        assert error is not None
        assert "missing" in error
