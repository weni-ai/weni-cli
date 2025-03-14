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
