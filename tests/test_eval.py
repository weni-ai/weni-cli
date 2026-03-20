import os
import sys
import types
from unittest.mock import Mock, patch

import yaml
from click.testing import CliRunner

from weni_cli.cli import cli
from weni_cli.commands.eval_init import EvalInitHandler, PLAN_FILE_NAME, _DEFAULT_PLAN
from weni_cli.commands.eval_run import EvalRunHandler


def _install_fake_agenteval(monkeypatch, plan_class):
    class FakeTestFailureError(Exception):
        pass

    fake_agenteval = types.ModuleType("agenteval")
    fake_plan_module = types.ModuleType("agenteval.plan")
    fake_exceptions_module = types.ModuleType("agenteval.plan.exceptions")
    fake_plan_module.Plan = plan_class
    fake_exceptions_module.TestFailureError = FakeTestFailureError

    monkeypatch.setitem(sys.modules, "agenteval", fake_agenteval)
    monkeypatch.setitem(sys.modules, "agenteval.plan", fake_plan_module)
    monkeypatch.setitem(sys.modules, "agenteval.plan.exceptions", fake_exceptions_module)

    return FakeTestFailureError


def test_eval_init_success():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["eval", "init"])

        assert result.exit_code == 0
        assert os.path.exists(PLAN_FILE_NAME)

        with open(PLAN_FILE_NAME) as f:
            content = yaml.safe_load(f)

        assert content == _DEFAULT_PLAN
        assert content["evaluator"]["model"] == "claude-haiku-4_5-global"
        assert content["evaluator"]["aws_region"] == "us-east-1"
        assert content["target"]["type"] == "weni"


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


def test_eval_run_success(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        mock_plan = Mock()
        mock_load = Mock(return_value=mock_plan)
        plan_class = type("Plan", (), {"load": staticmethod(mock_load)})
        _install_fake_agenteval(monkeypatch, plan_class)

        result = runner.invoke(
            cli,
            [
                "eval",
                "run",
                "--filter",
                "greeting",
                "--verbose",
                "--num-threads",
                "2",
                "--watch",
            ],
        )

        assert result.exit_code == 0
        mock_load.assert_called_once_with(None, plan_file_name=PLAN_FILE_NAME)
        mock_plan.run.assert_called_once_with(
            verbose=True,
            num_threads=2,
            work_dir=None,
            filter="greeting",
            watch=True,
        )


def test_eval_run_tests_failed_returns_exit_code_1(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        mock_plan = Mock()
        mock_plan.run.side_effect = Exception("generic failure")
        mock_load = Mock(return_value=mock_plan)
        plan_class = type("Plan", (), {"load": staticmethod(mock_load)})
        _install_fake_agenteval(monkeypatch, plan_class)

        result = runner.invoke(cli, ["eval", "run"])

        assert result.exit_code == 1


def test_eval_run_test_failure_error_returns_exit_code_1(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        mock_plan = Mock()
        mock_load = Mock(return_value=mock_plan)
        plan_class = type("Plan", (), {"load": staticmethod(mock_load)})
        test_failure_error = _install_fake_agenteval(monkeypatch, plan_class)
        mock_plan.run.side_effect = test_failure_error()

        result = runner.invoke(cli, ["eval", "run"])

        assert result.exit_code == 1


def test_eval_run_removes_traces_dir(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = os.getcwd()
        traces_dir = os.path.join(cwd, "agenteval_traces")
        os.makedirs(traces_dir)
        with open(os.path.join(traces_dir, "test.json"), "w") as f:
            f.write("{}")

        mock_plan = Mock()
        mock_load = Mock(return_value=mock_plan)
        plan_class = type("Plan", (), {"load": staticmethod(mock_load)})
        _install_fake_agenteval(monkeypatch, plan_class)

        result = runner.invoke(cli, ["eval", "run"])

        assert result.exit_code == 0
        assert not os.path.exists(traces_dir)


def test_eval_run_moves_summary_to_evaluation_results(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = os.getcwd()
        summary_path = os.path.join(cwd, "agenteval_summary.md")
        with open(summary_path, "w") as f:
            f.write("# Summary")

        mock_plan = Mock()
        mock_load = Mock(return_value=mock_plan)
        plan_class = type("Plan", (), {"load": staticmethod(mock_load)})
        _install_fake_agenteval(monkeypatch, plan_class)

        with patch("weni_cli.commands.eval_run.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260319_150000"
            result = runner.invoke(cli, ["eval", "run"])

        assert result.exit_code == 0
        assert not os.path.exists(summary_path)

        results_dir = os.path.join(cwd, "evaluation_results")
        assert os.path.exists(results_dir)

        expected_file = os.path.join(results_dir, "summary_20260319_150000.md")
        assert os.path.exists(expected_file)

        with open(expected_file) as f:
            assert f.read() == "# Summary"


def test_eval_run_postprocess_on_test_failure(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        cwd = os.getcwd()
        summary_path = os.path.join(cwd, "agenteval_summary.md")
        with open(summary_path, "w") as f:
            f.write("# Summary with failures")

        traces_dir = os.path.join(cwd, "agenteval_traces")
        os.makedirs(traces_dir)
        with open(os.path.join(traces_dir, "test.json"), "w") as f:
            f.write("{}")

        mock_plan = Mock()
        mock_load = Mock(return_value=mock_plan)
        plan_class = type("Plan", (), {"load": staticmethod(mock_load)})
        test_failure_error = _install_fake_agenteval(monkeypatch, plan_class)
        mock_plan.run.side_effect = test_failure_error()

        with patch("weni_cli.commands.eval_run.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260319_150000"
            result = runner.invoke(cli, ["eval", "run"])

        assert result.exit_code == 1
        assert not os.path.exists(traces_dir)
        assert not os.path.exists(summary_path)

        results_dir = os.path.join(cwd, "evaluation_results")
        expected_file = os.path.join(results_dir, "summary_20260319_150000.md")
        assert os.path.exists(expected_file)
