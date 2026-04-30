"""Tests for the active test definition validator."""

import pytest

from weni_cli.validators.agent_definition import validate_active_test_definition


def _valid_test_data():
    return {
        "tests": {
            "case_1": {
                "payload": {"OrderId": "123", "State": "payment-pending"},
                "params": {},
                "credentials": {},
                "project": {"vtex_account": "loja"},
                "project_rules": [],
                "ignored_official_rules": [],
                "global_rule": None,
            }
        }
    }


def test_valid_definition_returns_none():
    assert validate_active_test_definition(_valid_test_data()) is None


def test_minimal_definition_with_only_payload_is_valid():
    data = {"tests": {"case_1": {"payload": {"x": 1}}}}
    assert validate_active_test_definition(data) is None


def test_global_rule_can_be_string():
    data = {"tests": {"c": {"payload": {}, "global_rule": "def global_rule(data): return True"}}}
    assert validate_active_test_definition(data) is None


def test_rejects_non_dict_root():
    assert "must be an object" in validate_active_test_definition([])


def test_rejects_missing_tests_key():
    assert "missing required root key 'tests'" in validate_active_test_definition({})


def test_rejects_non_dict_tests():
    assert "'tests' must be an object" in validate_active_test_definition({"tests": []})


def test_rejects_empty_tests():
    assert "must contain at least one test case" in validate_active_test_definition({"tests": {}})


def test_rejects_non_dict_test_entry():
    data = {"tests": {"c": "not-a-dict"}}
    assert "must be an object" in validate_active_test_definition(data)


def test_rejects_missing_payload():
    data = {"tests": {"c": {"params": {}}}}
    assert "missing required field 'payload'" in validate_active_test_definition(data)


def test_rejects_non_dict_payload():
    data = {"tests": {"c": {"payload": "x"}}}
    assert "'payload' must be an object" in validate_active_test_definition(data)


@pytest.mark.parametrize("field", ["params", "credentials", "project"])
def test_rejects_non_dict_optional_field(field):
    data = {"tests": {"c": {"payload": {}, field: "x"}}}
    assert f"'{field}' must be an object" in validate_active_test_definition(data)


def test_rejects_non_list_project_rules():
    data = {"tests": {"c": {"payload": {}, "project_rules": "x"}}}
    assert "'project_rules' must be a list" in validate_active_test_definition(data)


def test_rejects_non_list_ignored_official_rules():
    data = {"tests": {"c": {"payload": {}, "ignored_official_rules": {}}}}
    assert "'ignored_official_rules' must be a list" in validate_active_test_definition(data)


def test_rejects_non_string_global_rule():
    data = {"tests": {"c": {"payload": {}, "global_rule": 123}}}
    assert "'global_rule' must be a string or null" in validate_active_test_definition(data)
