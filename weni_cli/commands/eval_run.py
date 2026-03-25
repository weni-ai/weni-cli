import os
from datetime import datetime

import rich_click as click
import yaml
from rich.console import Console
from rich.table import Table
from rich.live import Live

from weni_cli.clients.cli_client import CLIClient, RequestError
from weni_cli.clients.response_handlers import process_evaluation_event
from weni_cli.commands.eval_init import PLAN_FILE_NAME
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler

_RESULTS_DIR_NAME = "evaluation_results"


class EvalRunHandler(Handler):
    TESTS_FAILED_EXIT_CODE = 1

    def execute(self, **kwargs):
        formatter = Formatter()
        test_filter = kwargs.get("filter")
        plan_dir = kwargs.get("plan_dir") or os.getcwd()
        verbose = kwargs.get("verbose", False)

        try:
            plan_path = os.path.join(plan_dir, PLAN_FILE_NAME)
            if not os.path.exists(plan_path):
                raise FileNotFoundError

            with open(plan_path) as f:
                plan_config = yaml.safe_load(f)

            payload = {
                "evaluator": plan_config.get("evaluator", {}),
                "target": plan_config.get("target", {}),
                "tests": plan_config.get("tests", {}),
            }
            if test_filter:
                payload["filter"] = test_filter

            console = Console()
            test_rows: list[dict] = []
            summary_content = ""
            tests_failed = False
            num_tests = 0
            pass_count = 0

            def _build_table() -> Table:
                table = Table(title="Evaluation Results", expand=True)
                table.add_column("Test", justify="left")
                table.add_column("Status", justify="center", width=8)
                if verbose:
                    table.add_column("Reasoning", ratio=2)
                for row in test_rows:
                    status = row.get("status", "⏳")
                    cols = [row["name"], status]
                    if verbose:
                        cols.append(row.get("reasoning", ""))
                    table.add_row(*cols)
                return table

            def _handle_event(resp: dict) -> None:
                nonlocal summary_content, tests_failed, num_tests, pass_count

                event = process_evaluation_event(resp)
                if not event:
                    return

                code = event.get("code")

                if code == "EVALUATION_ERROR":
                    raise RequestError(event.get("error", "Unknown evaluation error"))

                if code == "EVALUATION_STARTED":
                    num_tests = event.get("num_tests", 0)

                elif code == "EVALUATION_TEST_STARTED":
                    test_rows.append({
                        "name": event["test_name"],
                        "status": "⏳",
                        "reasoning": "",
                    })
                    live.update(_build_table(), refresh=True)

                elif code == "EVALUATION_TEST_COMPLETED":
                    passed = event.get("passed", False)
                    row_idx = next(
                        (i for i, r in enumerate(test_rows) if r["name"] == event["test_name"]),
                        None,
                    )
                    if row_idx is not None:
                        test_rows[row_idx]["status"] = "✅" if passed else "❌"
                        test_rows[row_idx]["reasoning"] = event.get("reasoning", "") or ""
                    live.update(_build_table(), refresh=True)

                elif code == "EVALUATION_COMPLETED":
                    pass_count = event.get("pass_count", 0)
                    num_tests = event.get("num_tests", num_tests)
                    summary_content = event.get("summary_content", "")
                    tests_failed = pass_count < num_tests

            client = CLIClient()

            with Live(_build_table(), console=console, refresh_per_second=4) as live:
                client.run_evaluation(payload, _handle_event)

            if summary_content:
                self._save_summary(summary_content)

            console.print(f"\n[bold]Results: {pass_count}/{num_tests} tests passed[/bold]\n")

            if tests_failed:
                formatter.print_error_panel(
                    "One or more evaluation tests failed.",
                    title="Tests Failed",
                )
                return self.TESTS_FAILED_EXIT_CODE

            formatter.print_success_panel("Evaluation finished successfully.")
            return 0

        except FileNotFoundError:
            formatter.print_error_panel(
                f"Could not find {PLAN_FILE_NAME} in the selected directory.",
                title="Plan Not Found",
            )
            return self.TESTS_FAILED_EXIT_CODE
        except RequestError as error:
            formatter.print_error_panel(str(error), title="Evaluation Run Error")
            return self.TESTS_FAILED_EXIT_CODE
        except Exception as error:
            formatter.print_error_panel(str(error), title="Evaluation Run Error")
            return self.TESTS_FAILED_EXIT_CODE

    @staticmethod
    def _save_summary(summary_content: str) -> None:
        results_dir = os.path.join(os.getcwd(), _RESULTS_DIR_NAME)
        os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = os.path.join(results_dir, f"summary_{timestamp}.md")

        with open(summary_path, "w") as f:
            f.write(summary_content)
