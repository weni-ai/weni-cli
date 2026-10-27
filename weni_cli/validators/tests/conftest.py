"""Shared fixtures for validator tests.

The schema tests in :mod:`test_definition` operate on synthetic agent
definitions and don't ship with real source paths or module files on disk.
The newly introduced :func:`validate_entrypoint` would otherwise reject every
one of them. Auto-mock it to ``None`` here so schema-shape tests keep their
focus. Tests that exercise the entrypoint validator itself should import it
directly from :mod:`weni_cli.validators.source`, which is not patched.
"""

import pytest


@pytest.fixture(autouse=True)
def _bypass_entrypoint_validation(mocker):
    mocker.patch(
        "weni_cli.validators.agent_definition.validate_entrypoint",
        return_value=None,
    )
