import os
import shutil
from datetime import datetime

from weni_cli.commands.eval_init import PLAN_FILE_NAME
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler

_TRACES_DIR_NAME = "agenteval_traces"
_ORIGINAL_SUMMARY_NAME = "agenteval_summary.md"
_RESULTS_DIR_NAME = "evaluation_results"


class EvalRunHandler(Handler):
    TESTS_FAILED_EXIT_CODE = 1

    def execute(self, **kwargs):
        formatter = Formatter()
        work_dir = kwargs.get("work_dir") or os.getcwd()
        tests_failed = False

        try:
            from agenteval.plan import Plan
            from agenteval.plan.exceptions import TestFailureError

            plan = Plan.load(kwargs.get("plan_dir"), plan_file_name=PLAN_FILE_NAME)
            try:
                plan.run(
                    verbose=kwargs.get("verbose", False),
                    num_threads=kwargs.get("num_threads"),
                    work_dir=kwargs.get("work_dir"),
                    filter=kwargs.get("filter"),
                    watch=kwargs.get("watch", False),
                )
            except TestFailureError:
                tests_failed = True

            self._postprocess_results(work_dir)

            if tests_failed:
                formatter.print_error_panel(
                    "One or more evaluation tests failed.",
                    title="Tests Failed",
                )
                return self.TESTS_FAILED_EXIT_CODE

            formatter.print_success_panel("Evaluation finished successfully.")
            return 0
        except ModuleNotFoundError:
            formatter.print_error_panel(
                "weni-agenteval is not installed. Reinstall dependencies and try again.",
                title="Missing Dependency",
            )
            return self.TESTS_FAILED_EXIT_CODE
        except FileNotFoundError:
            formatter.print_error_panel(
                f"Could not find {PLAN_FILE_NAME} in the selected directory.",
                title="Plan Not Found",
            )
            return self.TESTS_FAILED_EXIT_CODE
        except Exception as error:
            formatter.print_error_panel(str(error), title="Evaluation Run Error")
            return self.TESTS_FAILED_EXIT_CODE

    @staticmethod
    def _postprocess_results(work_dir: str):
        traces_dir = os.path.join(work_dir, _TRACES_DIR_NAME)
        shutil.rmtree(traces_dir, ignore_errors=True)

        original_summary = os.path.join(work_dir, _ORIGINAL_SUMMARY_NAME)
        if os.path.exists(original_summary):
            results_dir = os.path.join(work_dir, _RESULTS_DIR_NAME)
            os.makedirs(results_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_summary = os.path.join(results_dir, f"summary_{timestamp}.md")
            shutil.move(original_summary, new_summary)
