"""Filesystem and AST-based validation for ``source.entrypoint`` definitions.

The schema validator in :mod:`weni_cli.validators.agent_definition` only checks
type and shape of YAML fields. This module complements it by verifying that
the ``source.path`` actually exists on disk, that the referenced module file
is present, and that the class named in ``entrypoint`` is declared in that
module — all without importing or executing any user code.
"""

from __future__ import annotations

import ast
import os
from typing import Optional


ENTRYPOINT_FORMAT = "module.ClassName"


def _is_valid_python_identifier(name: str) -> bool:
    return name.isidentifier()


def _parse_entrypoint(entrypoint: str) -> Optional[tuple[str, str]]:
    """Return ``(module, class_name)`` if entrypoint matches ``module.ClassName``.

    Rules:
    - Exactly one dot separating two non-empty parts.
    - Both parts must be valid Python identifiers (no digits leading, no spaces).
    """
    if not isinstance(entrypoint, str):
        return None

    parts = entrypoint.split(".")
    if len(parts) != 2:
        return None

    module, class_name = parts
    if not module or not class_name:
        return None

    if not _is_valid_python_identifier(module):
        return None

    if not _is_valid_python_identifier(class_name):
        return None

    return module, class_name


def _class_exists_in_module(module_file: str, class_name: str) -> tuple[bool, Optional[str]]:
    """Parse ``module_file`` with AST and check whether ``class_name`` is declared.

    Returns ``(found, syntax_error)``. ``syntax_error`` is set only when the
    file cannot be parsed as Python.
    """
    try:
        with open(module_file, "r", encoding="utf-8") as handle:
            source_code = handle.read()
    except OSError as error:
        return False, str(error)

    try:
        tree = ast.parse(source_code, filename=module_file)
    except SyntaxError as error:
        return False, f"{error.msg} (line {error.lineno})"

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return True, None

    return False, None


def validate_entrypoint(
    context: str,
    source_path: str,
    entrypoint: str,
    base_dir: Optional[str] = None,
) -> Optional[str]:
    """Validate ``entrypoint`` against the local filesystem.

    Args:
        context: Human-readable prefix for the error message (e.g.
            ``"Agent 'cep_agent': tool 'get_address'"``).
        source_path: Path to the resource folder, as written in the YAML.
        entrypoint: ``module.ClassName`` string from ``source.entrypoint``.
        base_dir: Directory to resolve relative paths against. Defaults to the
            current working directory, matching how the packager resolves paths.

    Returns:
        ``None`` if everything checks out, otherwise a user-facing error
        message describing the first problem encountered.
    """
    parsed = _parse_entrypoint(entrypoint)
    if parsed is None:
        return (
            f"{context}: entrypoint '{entrypoint}' must follow the format "
            f"'{ENTRYPOINT_FORMAT}'"
        )

    module, class_name = parsed

    resolved_root = base_dir if base_dir is not None else os.getcwd()
    resolved_source_path = (
        source_path
        if os.path.isabs(source_path)
        else os.path.join(resolved_root, source_path)
    )

    if not os.path.isdir(resolved_source_path):
        return f"{context}: source path '{source_path}' does not exist"

    module_file = os.path.join(resolved_source_path, f"{module}.py")
    if not os.path.isfile(module_file):
        return (
            f"{context}: module file '{source_path}{os.sep}{module}.py' not found "
            f"for entrypoint '{entrypoint}'"
        )

    found, syntax_error = _class_exists_in_module(module_file, class_name)
    if syntax_error is not None:
        return (
            f"{context}: failed to parse '{source_path}{os.sep}{module}.py' for "
            f"entrypoint '{entrypoint}': {syntax_error}"
        )

    if not found:
        return (
            f"{context}: class '{class_name}' not found in "
            f"'{source_path}{os.sep}{module}.py' for entrypoint '{entrypoint}'"
        )

    return None
