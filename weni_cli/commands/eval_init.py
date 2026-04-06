import os

import yaml

from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler

PLAN_FILE_NAME = "agent_evaluation.yml"

_DEFAULT_PLAN = {
    "tests": {
        "greeting": {
            "steps": ["Send a greeting message to the agent"],
            "expected_results": ["Agent responds with a friendly greeting"],
        }
    },
}


class EvalInitHandler(Handler):
    PLAN_ALREADY_EXISTS_EXIT_CODE = 2

    def execute(self, **kwargs):
        plan_dir = kwargs.get("plan_dir") or os.getcwd()
        formatter = Formatter()

        try:
            plan_path = os.path.join(plan_dir, PLAN_FILE_NAME)

            if os.path.exists(plan_path):
                raise FileExistsError

            with open(plan_path, "w") as stream:
                yaml.safe_dump(_DEFAULT_PLAN, stream, sort_keys=False)

            formatter.print_success_panel(f"Evaluation plan created at: {plan_path}")
            return 0
        except FileExistsError:
            formatter.print_error_panel(
                "An evaluation plan already exists in the selected directory.",
                title="Plan Already Exists",
            )
            return self.PLAN_ALREADY_EXISTS_EXIT_CODE
        except Exception as error:
            formatter.print_error_panel(str(error), title="Evaluation Init Error")
            return 1
