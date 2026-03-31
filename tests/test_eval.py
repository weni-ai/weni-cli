import json
import os
from unittest.mock import Mock, patch, MagicMock

import yaml
from click.testing import CliRunner

from weni_cli.cli import cli
from weni_cli.commands.eval_init import EvalInitHandler, PLAN_FILE_NAME, _DEFAULT_PLAN
from weni_cli.commands.eval_run import EvalRunHandler


# --- eval init tests (unchanged) ---


def test_eval_init_success():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["eval", "init"])

        assert result.exit_code == 0
        assert os.path.exists(PLAN_FILE_NAME)

        with open(PLAN_FILE_NAME) as f:
            content = yaml.safe_load(f)

        assert content == _DEFAULT_PLAN
        assert "tests" in content
        assert "evaluator" not in content
        assert "target" not in content


def test_eval_init_plan_exists_returns_exit_code_2():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open(PLAN_FILE_NAME, "w") as f:
            f.write("existing plan")

        result = runner.invoke(cli, ["eval", "init"])

        assert result.exit_code == EvalInitHandler.PLAN_ALREADY_EXISTS_EXIT_CODE


def test_eval_init_with_plan_dir():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs("custom_dir")
        result = runner.invoke(cli, ["eval", "init", "--plan-dir", "custom_dir"])

        assert result.exit_code == 0
        assert os.path.exists(os.path.join("custom_dir", PLAN_FILE_NAME))


# --- eval run tests (rewritten for backend flow) ---


def _create_plan_file(plan_dir=None):
    """Helper to create a valid agent_evaluation.yml in the given directory."""
    plan = {
        "tests": {
            "greeting": {
                "steps": ["Send a greeting message"],
                "expected_results": ["Agent responds with a greeting"],
            }
        },
    }
    path = os.path.join(plan_dir, PLAN_FILE_NAME) if plan_dir else PLAN_FILE_NAME
    with open(path, "w") as f:
        yaml.safe_dump(plan, f, sort_keys=False)
    return plan


def _make_ndjson_events(pass_count=1, num_tests=1, summary_content="# Summary"):
    """Build a list of NDJSON event dicts simulating a full evaluation."""
    return [
        {
            "success": True,
            "code": "EVALUATION_STARTED",
            "data": {"num_tests": num_tests, "test_names": ["greeting"]},
        },
        {
            "success": True,
            "code": "EVALUATION_TEST_STARTED",
            "data": {"test_name": "greeting", "test_index": 1, "num_tests": num_tests},
        },
        {
            "success": True,
            "code": "EVALUATION_TEST_COMPLETED",
            "data": {
                "test_name": "greeting",
                "passed": pass_count > 0,
                "result": "Test passed" if pass_count > 0 else "Test failed",
                "reasoning": "The agent responded correctly.",
                "conversation": [
                    {"role": "user", "message": "Hello"},
                    {"role": "agent", "message": "Hi there!"},
                ],
            },
        },
        {
            "success": True,
            "code": "EVALUATION_COMPLETED",
            "data": {
                "pass_count": pass_count,
                "num_tests": num_tests,
                "summary_content": summary_content,
            },
        },
    ]


def _patch_cli_client(monkeypatch, events):
    """Patch CLIClient to simulate streaming NDJSON events."""

    def fake_run_evaluation(self, plan_config, event_callback):
        for event in events:
            event_callback(event)

    monkeypatch.setattr(
        "weni_cli.commands.eval_run.CLIClient.run_evaluation",
        fake_run_evaluation,
    )
    monkeypatch.setattr(
        "weni_cli.commands.eval_run.CLIClient.__init__",
        lambda self: None,
    )


def test_eval_run_success(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        _create_plan_file()
        events = _make_ndjson_events(pass_count=1, num_tests=1)
        _patch_cli_client(monkeypatch, events)

        result = runner.invoke(cli, ["eval", "run"])

        assert result.exit_code == 0
        assert os.path.exists("evaluation_results")
        summary_files = os.listdir("evaluation_results")
        assert len(summary_files) == 1
        assert summary_files[0].startswith("summary_")
        assert summary_files[0].endswith(".md")


def test_eval_run_with_filter(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        _create_plan_file()
        events = _make_ndjson_events()

        captured_payloads = []
        original_init = lambda self: None

        def fake_run_evaluation(self, plan_config, event_callback):
            captured_payloads.append(plan_config)
            for event in events:
                event_callback(event)

        monkeypatch.setattr("weni_cli.commands.eval_run.CLIClient.__init__", original_init)
        monkeypatch.setattr("weni_cli.commands.eval_run.CLIClient.run_evaluation", fake_run_evaluation)

        result = runner.invoke(cli, ["eval", "run", "--filter", "greeting"])

        assert result.exit_code == 0
        assert captured_payloads[0]["filter"] == "greeting"


def test_eval_run_plan_not_found():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["eval", "run"])

        assert result.exit_code == 1


def test_eval_run_test_failure(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        _create_plan_file()
        events = _make_ndjson_events(pass_count=0, num_tests=1)
        _patch_cli_client(monkeypatch, events)

        result = runner.invoke(cli, ["eval", "run"])

        assert result.exit_code == 1


def test_eval_run_saves_summary_with_timestamp(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        _create_plan_file()
        events = _make_ndjson_events(summary_content="# Test Summary Content")
        _patch_cli_client(monkeypatch, events)

        with patch("weni_cli.commands.eval_run.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260319_150000"
            result = runner.invoke(cli, ["eval", "run"])

        assert result.exit_code == 0

        expected_file = os.path.join("evaluation_results", "summary_20260319_150000.md")
        assert os.path.exists(expected_file)

        with open(expected_file) as f:
            assert f.read() == "# Test Summary Content"


def test_eval_run_backend_error(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        _create_plan_file()
        events = [
            {
                "success": False,
                "code": "EVALUATION_ERROR",
                "data": {"error": "AWS credentials not configured"},
            },
        ]
        _patch_cli_client(monkeypatch, events)

        result = runner.invoke(cli, ["eval", "run"])

        assert result.exit_code == 1


def test_eval_run_verbose_shows_reasoning(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        _create_plan_file()
        events = _make_ndjson_events()
        _patch_cli_client(monkeypatch, events)

        result = runner.invoke(cli, ["eval", "run", "--verbose"])

        assert result.exit_code == 0
        assert "Reasoning" in result.output or "correctly" in result.output
