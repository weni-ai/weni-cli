from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler


class EvalInitHandler(Handler):
    PLAN_ALREADY_EXISTS_EXIT_CODE = 2

    def execute(self, **kwargs):
        plan_dir = kwargs.get("plan_dir")
        formatter = Formatter()

        try:
            from agenteval.plan import Plan

            plan_path = Plan.init_plan(plan_dir=plan_dir)
            formatter.print_success_panel(f"Evaluation plan created at: {plan_path}")
            return 0
        except ModuleNotFoundError:
            formatter.print_error_panel(
                "weni-agenteval is not installed. Reinstall dependencies and try again.",
                title="Missing Dependency",
            )
            return 1
        except FileExistsError:
            formatter.print_error_panel(
                "An evaluation plan already exists in the selected directory.",
                title="Plan Already Exists",
            )
            return self.PLAN_ALREADY_EXISTS_EXIT_CODE
        except Exception as error:
            formatter.print_error_panel(str(error), title="Evaluation Init Error")
            return 1
