from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler


class EvalRunHandler(Handler):
    TESTS_FAILED_EXIT_CODE = 1

    def execute(self, **kwargs):
        formatter = Formatter()

        try:
            from agenteval.plan import Plan
            from agenteval.plan.exceptions import TestFailureError

            plan = Plan.load(kwargs.get("plan_dir"))
            plan.run(
                verbose=kwargs.get("verbose", False),
                num_threads=kwargs.get("num_threads"),
                work_dir=kwargs.get("work_dir"),
                filter=kwargs.get("filter"),
                watch=kwargs.get("watch", False),
            )
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
                "Could not find agenteval.yml in the selected directory.",
                title="Plan Not Found",
            )
            return self.TESTS_FAILED_EXIT_CODE
        except TestFailureError:
            formatter.print_error_panel(
                "One or more evaluation tests failed.",
                title="Tests Failed",
            )
            return self.TESTS_FAILED_EXIT_CODE
        except Exception as error:
            formatter.print_error_panel(str(error), title="Evaluation Run Error")
            return self.TESTS_FAILED_EXIT_CODE
