"""
Response handler implementations.

This module contains utility functions for processing responses from the CLI and Weni APIs.
"""

import rich_click as click


def process_push_display_step(resp):
    """Process response for push agents display step.

    Args:
        resp: Response object from server

    Returns:
        String with message to display, or None if no message
    """
    if not resp:
        return

    if not resp.get("success") and not resp.get("message"):
        return "Unknown error while pushing agents"

    # Add a buffer at the end to avoid the stdout last character being cut off by the spinner
    return resp.get("message") + "."


def process_evaluation_event(resp):
    """Process a streaming evaluation event from the backend.

    Args:
        resp: Response object from server

    Returns:
        Dictionary with event data if successful, None otherwise
    """
    if not resp:
        return None

    if not resp.get("success"):
        error_data = resp.get("data", {})
        return {
            "code": resp.get("code", "EVALUATION_ERROR"),
            "error": error_data.get("error", resp.get("message", "Unknown evaluation error")),
        }

    code = resp.get("code")
    data = resp.get("data", {})

    if code == "EVALUATION_STARTED":
        return {
            "code": code,
            "num_tests": data.get("num_tests"),
            "test_names": data.get("test_names"),
        }
    elif code == "EVALUATION_TEST_STARTED":
        return {
            "code": code,
            "test_name": data.get("test_name"),
            "test_index": data.get("test_index"),
            "num_tests": data.get("num_tests"),
        }
    elif code == "EVALUATION_TEST_COMPLETED":
        return {
            "code": code,
            "test_name": data.get("test_name"),
            "passed": data.get("passed"),
            "result": data.get("result"),
            "reasoning": data.get("reasoning"),
            "conversation": data.get("conversation"),
        }
    elif code == "EVALUATION_COMPLETED":
        return {
            "code": code,
            "pass_count": data.get("pass_count"),
            "num_tests": data.get("num_tests"),
            "summary_content": data.get("summary_content"),
        }

    return None


def process_test_progress(resp, verbose):
    """Process response for test run display progress.

    Args:
        resp: Response object from server
        verbose: Whether to show verbose output

    Returns:
        Dictionary with test data if successful, None otherwise
    """
    if not resp:
        return

    if not resp.get("success") and not resp.get("message"):
        click.echo("Unknown error while running test")
        return

    if not resp.get("success"):
        click.echo(resp.get("message"))
        click.echo(f"Request ID: {resp.get('request_id')}")
        return

    if resp.get("code") == "TEST_CASE_RUNNING" or resp.get("code") == "TEST_CASE_COMPLETED":
        data = resp.get("data", {})
        test_name = data.get("test_case")
        test_status_code = data.get("test_status_code")
        test_response = data.get("test_response")

        if verbose:
            return {
                "test_name": test_name,
                "test_status_code": test_status_code,
                "test_response": test_response,
                "test_logs": data.get("logs"),
            }

        return {
            "test_name": test_name,
            "test_status_code": test_status_code,
            "test_response": test_response,
        }
    else:
        click.echo(resp.get("message"))
        return None
