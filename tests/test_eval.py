import sys
import types
from unittest.mock import Mock

from click.testing import CliRunner

from weni_cli.cli import cli
from weni_cli.commands.eval_init import EvalInitHandler


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


def test_eval_init_success(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        mock_init_plan = Mock(return_value="/tmp/agenteval.yml")
        plan_class = type("Plan", (), {"init_plan": staticmethod(mock_init_plan)})
        _install_fake_agenteval(monkeypatch, plan_class)

        result = runner.invoke(cli, ["eval", "init"])

        assert result.exit_code == 0
        mock_init_plan.assert_called_once_with(plan_dir=None)


def test_eval_init_plan_exists_returns_exit_code_2(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        mock_init_plan = Mock(side_effect=FileExistsError)
        plan_class = type("Plan", (), {"init_plan": staticmethod(mock_init_plan)})
        _install_fake_agenteval(monkeypatch, plan_class)

        result = runner.invoke(cli, ["eval", "init"])

        assert result.exit_code == EvalInitHandler.PLAN_ALREADY_EXISTS_EXIT_CODE


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
        mock_load.assert_called_once_with(None)
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
