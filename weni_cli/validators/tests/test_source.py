"""Tests for :mod:`weni_cli.validators.source`.

The autouse fixture in this folder's ``conftest.py`` patches
``weni_cli.validators.agent_definition.validate_entrypoint``. The function
under test here is imported directly from ``weni_cli.validators.source``, so
those tests bypass the schema-level patch and exercise the real validator.
"""

from __future__ import annotations

import os

import pytest
from click.testing import CliRunner

from weni_cli.validators.source import (
    ENTRYPOINT_FORMAT,
    validate_entrypoint,
)


CONTEXT = "Agent 'cep_agent': tool 'get_address'"


def _write_module(path: str, body: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as handle:
        handle.write(body)


@pytest.mark.parametrize(
    "bad_entrypoint",
    [
        "main",
        "main.Foo.Bar",
        "123.Foo",
        ".Foo",
        "main.",
        "main Foo.Bar",
        "",
    ],
)
def test_invalid_entrypoint_format_is_rejected(bad_entrypoint):
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs("tools/get_address", exist_ok=True)

        error = validate_entrypoint(CONTEXT, "tools/get_address", bad_entrypoint)

        assert error is not None
        assert ENTRYPOINT_FORMAT in error
        assert CONTEXT in error


def test_missing_source_path_is_rejected():
    runner = CliRunner()
    with runner.isolated_filesystem():
        error = validate_entrypoint(CONTEXT, "tools/get_address", "main.GetAddress")

        assert error is not None
        assert "source path 'tools/get_address' does not exist" in error
        assert CONTEXT in error


def test_missing_module_file_is_rejected():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs("tools/get_address", exist_ok=True)

        error = validate_entrypoint(CONTEXT, "tools/get_address", "main.GetAddress")

        assert error is not None
        assert "module file" in error
        assert "main.py" in error
        assert CONTEXT in error


def test_missing_class_is_rejected():
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_module("tools/get_address/main.py", "class SomethingElse:\n    pass\n")

        error = validate_entrypoint(CONTEXT, "tools/get_address", "main.GetAddress")

        assert error is not None
        assert "class 'GetAddress' not found" in error
        assert CONTEXT in error


def test_syntax_error_in_module_is_reported():
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_module("tools/get_address/main.py", "class :::: pass\n")

        error = validate_entrypoint(CONTEXT, "tools/get_address", "main.GetAddress")

        assert error is not None
        assert "failed to parse" in error
        assert CONTEXT in error


def test_happy_path_returns_none():
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_module(
            "tools/get_address/main.py",
            "class GetAddress:\n    def execute(self, context):\n        return 'ok'\n",
        )

        assert (
            validate_entrypoint(CONTEXT, "tools/get_address", "main.GetAddress")
            is None
        )


def test_class_nested_inside_function_is_not_detected():
    """Only top-level ``class`` declarations count, mirroring how the backend
    imports the module to grab the entrypoint."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        _write_module(
            "tools/get_address/main.py",
            "def factory():\n    class GetAddress:\n        pass\n    return GetAddress\n",
        )

        error = validate_entrypoint(CONTEXT, "tools/get_address", "main.GetAddress")

        assert error is not None
        assert "class 'GetAddress' not found" in error


def test_absolute_source_path_is_supported(tmp_path):
    module_dir = tmp_path / "tools" / "get_address"
    module_dir.mkdir(parents=True)
    (module_dir / "main.py").write_text("class GetAddress: pass\n")

    assert (
        validate_entrypoint(CONTEXT, str(module_dir), "main.GetAddress")
        is None
    )


def test_base_dir_resolves_relative_paths(tmp_path):
    module_dir = tmp_path / "tools" / "get_address"
    module_dir.mkdir(parents=True)
    (module_dir / "main.py").write_text("class GetAddress: pass\n")

    assert (
        validate_entrypoint(
            CONTEXT,
            "tools/get_address",
            "main.GetAddress",
            base_dir=str(tmp_path),
        )
        is None
    )
