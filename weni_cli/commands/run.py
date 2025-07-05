from io import BufferedReader
from typing import Optional
import rich_click as click
import os
import tempfile
import shutil

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.console import group

from weni_cli.clients.cli_client import CLIClient
from weni_cli.formatter.formatter import Formatter
from weni_cli.handler import Handler
from weni_cli.packager.packager import create_agent_resource_folder_zip
from weni_cli.store import STORE_PROJECT_UUID_KEY, Store
from weni_cli.validators.definition import format_definition, load_agent_definition, load_test_definition


DEFAULT_TEST_DEFINITION_FILE = "test_definition.yaml"


class RunHandler(Handler):
    def execute(self, **kwargs):
        definition_path = kwargs.get("definition")
        agent_key = kwargs.get("agent_key")
        resource_key = kwargs.get("resource_key")
        test_definition_path = kwargs.get("test_definition")
        verbose = kwargs.get("verbose", False)
        
        store = Store()
        project_uuid = store.get(STORE_PROJECT_UUID_KEY)
        formatter = Formatter()

        if not project_uuid:
            click.echo("No project selected, please select a project first")
            return

        definition_data, error = load_agent_definition(definition_path)
        if error:
            formatter.print_error_panel(
                f"Invalid agent definition YAML file format, error:\n{error}", 
                title="Error loading agent definition"
            )
            return

        # Validate agent existence
        if agent_key not in definition_data.get("agents", {}):
            formatter.print_error_panel(
                f"Agent '{agent_key}' not found in the definition file.",
                title="Invalid Agent"
            )
            return

        # Detect agent type and route to appropriate handler
        agent_data = definition_data["agents"][agent_key]
        agent_type = "active" if agent_data.get("rules") else "passive"

        if agent_type == "active":
            self._handle_active_agent(
                project_uuid, definition_data, agent_key, resource_key, 
                test_definition_path, verbose, formatter
            )
        else:
            self._handle_passive_agent(
                project_uuid, definition_data, agent_key, resource_key, 
                test_definition_path, verbose, formatter
            )

    def _handle_active_agent(self, project_uuid, definition_data, agent_key, rule_key, test_definition_path, verbose, formatter):
        """Handle testing for active agents (rules-based)."""
        agent_data = definition_data["agents"][agent_key]
        agent_rules = list(agent_data.get("rules", {}).keys())
        
        # Validate rules exist
        if not agent_rules:
            formatter.print_error_panel(
                f"No rules found in agent '{agent_key}'.",
                title="No Rules Available"
            )
            return
        
        # If no specific rule provided, test all rules
        if not rule_key:
            self._run_all_rules_tests(
                project_uuid, definition_data, agent_key, test_definition_path, verbose, formatter
            )
            return
        
        # Validate specific rule exists
        if rule_key not in agent_rules:
            formatter.print_error_panel(
                f"Rule '{rule_key}' not found in agent '{agent_key}'.\nAvailable rules: {', '.join(agent_rules)}",
                title="Invalid Rule"
            )
            return
        
        # Test specific rule
        self._run_single_rule_test(
            project_uuid, definition_data, agent_key, rule_key, test_definition_path, verbose
        )

    def _handle_passive_agent(self, project_uuid, definition_data, agent_key, tool_key, test_definition_path, verbose, formatter):
        """Handle testing for passive agents (tools-based)."""
        agent_data = definition_data["agents"][agent_key]
        
        # For passive agents, tool_key is required
        if not tool_key:
            formatter.print_error_panel(
                "Tool key is required for passive agents.",
                title="Missing Tool Key"
            )
            return
        
        # Validate tools exist and find the specified tool
        agent_tools = []
        for tool in agent_data.get("tools", []):
            if isinstance(tool, dict):
                agent_tools.extend(tool.keys())

        if tool_key not in agent_tools:
            formatter.print_error_panel(
                f"Tool '{tool_key}' not found in agent '{agent_key}'.\nAvailable tools: {', '.join(agent_tools)}",
                title="Invalid Tool"
            )
            return
        
        # Test the tool
        self._run_single_tool_test(
            project_uuid, definition_data, agent_key, tool_key, test_definition_path, verbose
        )

    def _run_single_rule_test(self, project_uuid, definition_data, agent_key, rule_key, test_definition_path, verbose):
        """Run test for a single rule."""
        try:
            # Load test definition
            if not test_definition_path:
                test_definition_path = self._load_default_rule_test_definition(definition_data, agent_key, rule_key)

            if not test_definition_path:
                click.echo(f"Error: Failed to get default test definition file: {DEFAULT_TEST_DEFINITION_FILE} in rule folder.")
                click.echo("You can use the --file option to specify a different file.")
                return

            # Load rule folder
            rule_folder, error = self._load_rule_folder(definition_data, agent_key, rule_key)
            if error:
                click.echo(f"❌ Error loading rule folder: {error}")
                return

            # Load and validate test definition
            test_definition, error = load_test_definition(test_definition_path)
            if error:
                click.echo(f"❌ Error loading test definition: {error}")
                return

            # Format definition and get paths
            definition = format_definition(definition_data)
            rule_source_path = self._get_rule_source_path(definition, agent_key, rule_key)
            credentials = self._load_resource_credentials(rule_source_path)
            rule_globals = self._load_resource_globals(rule_source_path)

            # Run the test
            self._execute_rule_test(
                project_uuid, definition, rule_folder, rule_key, agent_key,
                test_definition, credentials, rule_globals, verbose
            )

        except Exception as e:
            click.echo(f"❌ Error testing rule '{rule_key}': {e}")

    def _run_single_tool_test(self, project_uuid, definition_data, agent_key, tool_key, test_definition_path, verbose):
        """Run test for a single tool."""
        try:
            # Load test definition
            if not test_definition_path:
                test_definition_path = self._load_default_tool_test_definition(definition_data, agent_key, tool_key)

            if not test_definition_path:
                click.echo(f"Error: Failed to get default test definition file: {DEFAULT_TEST_DEFINITION_FILE} in tool folder.")
                click.echo("You can use the --file option to specify a different file.")
                return

            # Load tool folder
            tool_folder, error = self._load_tool_folder(definition_data, agent_key, tool_key)
            if error:
                click.echo(f"❌ Error loading tool folder: {error}")
                return

            # Load and validate test definition
            test_definition, error = load_test_definition(test_definition_path)
            if error:
                click.echo(f"❌ Error loading test definition: {error}")
                return

            # Format definition and get paths
            definition = format_definition(definition_data)
            tool_source_path = self._get_tool_source_path(definition, agent_key, tool_key)
            credentials = self._load_resource_credentials(tool_source_path)
            tool_globals = self._load_resource_globals(tool_source_path)

            # Run the test
            self._execute_tool_test(
                project_uuid, definition, tool_folder, tool_key, agent_key,
                test_definition, credentials, tool_globals, verbose
            )

        except Exception as e:
            click.echo(f"❌ Error testing tool '{tool_key}': {e}")

    def _run_all_rules_tests(self, project_uuid, definition_data, agent_key, test_definition_path, verbose, formatter):
        """Run tests for all rules in an active agent."""
        agent_data = definition_data["agents"][agent_key]
        agent_rules = list(agent_data.get("rules", {}).keys())
        
        click.echo(f"Testing all rules for agent '{agent_key}': {', '.join(agent_rules)}")
        click.echo("=" * 80)
        
        for rule_key in agent_rules:
            click.echo(f"\n🔄 Testing rule: {rule_key}")
            click.echo("-" * 40)
            
            self._run_single_rule_test(
                project_uuid, definition_data, agent_key, rule_key, test_definition_path, verbose
            )
            
            click.echo(f"✅ Completed testing rule: {rule_key}")
                
        click.echo("\n" + "=" * 80)
        click.echo(f"🏁 Finished testing all rules for agent '{agent_key}'")

    def _execute_rule_test(self, project_uuid, definition, rule_folder, rule_key, agent_key, test_definition, credentials, rule_globals, verbose):
        """Execute the actual rule test using CLIClient."""
        test_rows = []
        
        with Live(self._display_test_results([], rule_key, verbose), refresh_per_second=4) as live:
            def update_live_callback(test_name, test_result, status_code, code, verbose):
                self._update_live_display(test_rows, test_name, test_result, status_code, code, live, rule_key, verbose)

            client = CLIClient()
            test_logs = client.run_rule_test(
                project_uuid, definition, rule_folder, rule_key, agent_key,
                test_definition, credentials, rule_globals, "active",
                update_live_callback, verbose
            )

        if verbose:
            self._render_response_and_logs(test_logs)

    def _execute_tool_test(self, project_uuid, definition, tool_folder, tool_key, agent_key, test_definition, credentials, tool_globals, verbose):
        """Execute the actual tool test using CLIClient."""
        test_rows = []
        
        with Live(self._display_test_results([], tool_key, verbose), refresh_per_second=4) as live:
            def update_live_callback(test_name, test_result, status_code, code, verbose):
                self._update_live_display(test_rows, test_name, test_result, status_code, code, live, tool_key, verbose)

            client = CLIClient()
            test_logs = client.run_tool_test(
                project_uuid, definition, tool_folder, tool_key, agent_key,
                test_definition, credentials, tool_globals, "passive",
                update_live_callback, verbose
            )

        if verbose:
            self._render_response_and_logs(test_logs)

    # Helper methods for file operations
    def _get_tool_source_path(self, definition, agent_key, tool_key) -> Optional[str]:
        agent_data = definition.get("agents", {}).get(agent_key)
        if not agent_data:
            return None

        for tool in agent_data.get("tools", []):
            if tool.get("key") == tool_key:
                return tool.get("source", {}).get("path")
        return None

    def _get_rule_source_path(self, definition, agent_key, rule_key) -> Optional[str]:
        agent_data = definition.get("agents", {}).get(agent_key)
        if not agent_data:
            return None

        rules = agent_data.get("rules", {})
        if rule_key in rules:
            return rules[rule_key].get("source", {}).get("path")
        return None

    def _load_resource_credentials(self, resource_source_path: str) -> Optional[dict]:
        credentials = {}
        try:
            with open(f"{resource_source_path}/.env", "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    credentials[key] = value
        except Exception:
            return {}
        return credentials

    def _load_resource_globals(self, resource_source_path: str) -> Optional[dict]:
        globals = {}
        try:
            with open(f"{resource_source_path}/.globals", "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    globals[key] = value
        except Exception:
            return {}
        return globals

    def _load_default_tool_test_definition(self, definition, agent_key, tool_key) -> Optional[str]:
        try:
            agent_data = definition.get("agents", {}).get(agent_key)
            if not agent_data:
                return None

            for tool in agent_data.get("tools", []):
                for key, tool_data in tool.items():
                    if key == tool_key:
                        path_test = tool_data.get("source", {}).get("path_test")
                        tool_path = tool_data.get("source", {}).get("path")
                        if path_test:
                            return f"{tool_path}/{path_test}"
                        else:
                            return f"{tool_path}/{DEFAULT_TEST_DEFINITION_FILE}"
            return None
        except Exception as e:
            click.echo(f"Error: Failed to load default test definition file: {e}")
            return None

    def _load_default_rule_test_definition(self, definition, agent_key, rule_key) -> Optional[str]:
        try:
            agent_data = definition.get("agents", {}).get(agent_key)
            if not agent_data:
                return None

            rules = agent_data.get("rules", {})
            if rule_key in rules:
                rule_data = rules[rule_key]
                rule_path = rule_data.get("source", {}).get("path")
                if rule_path:
                    return f"{rule_path}/{DEFAULT_TEST_DEFINITION_FILE}"
            return None
        except Exception as e:
            click.echo(f"Error: Failed to load default rule test definition file: {e}")
            return None

    def _load_tool_folder(self, definition, agent_key, tool_key) -> tuple[Optional[BufferedReader], Optional[Exception]]:
        agent_data = definition.get("agents", {}).get(agent_key)
        if not agent_data:
            return None, Exception(f"Agent {agent_key} not found in definition")

        tools = agent_data.get("tools", [])
        tool_data = None
        for tool in tools:
            for key, data in tool.items():
                if key == tool_key:
                    tool_data = data
                    break

        if not tool_data:
            return None, Exception(f"Tool {tool_key} not found in agent {agent_key}")

        tool_folder, error = create_agent_resource_folder_zip(tool_key, tool_data.get("source").get("path"))
        if error:
            return None, Exception(f"Failed to create tool folder for tool {tool_key} in agent {agent_key}\n{error}")

        return tool_folder, None

    def _load_rule_folder(self, definition, agent_key, rule_key) -> tuple[Optional[BufferedReader], Optional[Exception]]:
        agent_data = definition.get("agents", {}).get(agent_key)
        if not agent_data:
            return None, Exception(f"Agent {agent_key} not found in definition")

        rules = agent_data.get("rules", {})
        if rule_key not in rules:
            return None, Exception(f"Rule {rule_key} not found in agent {agent_key}")

        rule_data = rules[rule_key]
        rule_path = rule_data.get("source", {}).get("path")
        if not rule_path:
            return None, Exception(f"Rule {rule_key} in agent {agent_key} is missing source path")

        temp_dir = tempfile.mkdtemp()
        try:
            # Copia a pasta da regra para o temp_dir
            shutil.copytree(rule_path, f"{temp_dir}/rule_temp")
            lambda_path = f"{temp_dir}/rule_temp/lambda_function.py"
            if not os.path.exists(lambda_path):
                # Extrai o nome da classe do entrypoint
                entrypoint = rule_data.get("source", {}).get("entrypoint", "")
                class_name = self._get_class_name_from_entrypoint(entrypoint)
                if class_name:
                    lambda_content = self._generate_lambda_function_template(rule_key, class_name)
                    with open(lambda_path, "w") as f:
                        f.write(lambda_content)
            # Cria o zip a partir do diretório temporário
            rule_folder, error = create_agent_resource_folder_zip(rule_key, f"{temp_dir}/rule_temp")
            if error:
                return None, Exception(f"Failed to create rule folder for rule {rule_key} in agent {agent_key}\n{error}")
            return rule_folder, None
        except Exception as e:
            return None, Exception(f"Failed to prepare rule folder for rule {rule_key} in agent {agent_key}\n{e}")
        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

    # Display and formatting methods
    def _format_response_for_display(self, test_result):
        """Format response for better display"""
        if not test_result:
            return "waiting..."

        if isinstance(test_result, dict) and "response" in test_result:
            response = test_result.get("response")
            function_response = response.get("functionResponse")

            if not function_response:
                return str(response)

            response_body = function_response.get("responseBody")
            if not response_body:
                return str(function_response)

            response_body_text = response_body.get("TEXT")
            if not response_body_text:
                return str(response_body)

            return response_body_text.get("body", "")
        else:
            return str(test_result)

    def _get_status_icon(self, status_code):
        if status_code == 200:
            return "✅"
        return "❌"

    def _display_test_results(self, rows, tool_name, verbose=False):
        """Create a table to display test results."""
        if not rows:
            return None

        table = Table(title=f"Test Results for {tool_name}", expand=True)
        table.add_column("Test Name", justify="left")
        table.add_column("Status", justify="center")
        table.add_column("Response", ratio=2, no_wrap=True)

        for row in rows:
            status = self._get_status_icon(row.get("status")) if row.get("code") == "TEST_CASE_COMPLETED" else "⏳"
            response_display = self._format_response_for_display(row.get("response"))
            table.add_row(row.get("name"), status, response_display)

        return table

    def _update_live_display(self, test_rows, test_name, test_result, status_code, code, live_display, tool_name, verbose=False):
        """Update the live display with test results."""
        # Check if test_name is already in test_rows, if not, add it
        row_index = next((i for i, row in enumerate(test_rows) if row.get("name") == test_name), None)
        if row_index is None:
            test_rows.append({"name": test_name, "status": status_code, "response": test_result, "code": code})
        else:
            test_rows[row_index]["status"] = status_code
            test_rows[row_index]["response"] = test_result
            test_rows[row_index]["code"] = code

        live_display.update(self._display_test_results(test_rows, tool_name, verbose), refresh=True)

    def _render_response_and_logs(self, logs):
        console = Console()

        @group()
        def get_panels():
            if log.get("test_response"):
                yield Panel(
                    self._format_response_for_display(log.get("test_response")),
                    title="[bold yellow]Response[/bold yellow]",
                    title_align="left",
                )

            if log.get("test_logs"):
                yield Panel(
                    log.get("test_logs").strip("\n"),
                    title="[bold blue]Logs[/bold blue]",
                    title_align="left",
                )

        console.print("\n")
        for log in logs:
            if log.get("test_response") or log.get("test_logs"):
                console.print(
                    Panel(
                        get_panels(),
                        title=f"[bold green]Test Results for {log.get('test_name')}[/bold green]",
                        title_align="left",
                    )
                )

    def _get_class_name_from_entrypoint(self, entrypoint):
        """Extract class name from entrypoint string like 'main.PaymentApproved'."""
        if not entrypoint or '.' not in entrypoint:
            return None
        return entrypoint.split('.')[-1]

    def _generate_lambda_function_template(self, rule_name, class_name):
        """Generate the standard lambda_function.py template used in active agent push."""
        template = """import json
from main import {class_name}

def lambda_handler(event, context):
    try:
        # Initialize the rule instance
        rule_instance = {class_name}()
        
        # Try to find webhook data in various places
        webhook_data = None
        
        # Option 1: Check if payload has data
        if event.get('payload') and isinstance(event.get('payload'), dict) and event['payload']:
            webhook_data = event['payload']
        
        # Option 2: Check if webhook_data field exists
        elif event.get('webhook_data'):
            webhook_data = event['webhook_data']
        
        # Option 3: Check if data field exists
        elif event.get('data'):
            webhook_data = event['data']
        
        # Option 4: Look in params for individual fields
        elif event.get('params'):
            params = event['params']
            # Create a fake webhook with basic data from params
            webhook_data = {{
                'orderId': params.get('order_id'),
                'status': 'payment-approved',
                'customerId': 'unknown',
                'customerName': params.get('customer_name', 'Cliente')
            }}
        
        # Fallback: use entire event
        else:
            webhook_data = event
        
        contact_data = event.get('params', {{}})
        
        # Check if rule should trigger
        should_trigger = rule_instance.should_trigger(webhook_data)
        
        if should_trigger:
            result = rule_instance.execute(contact_data, webhook_data)
            return {{
                'statusCode': 200,
                'body': json.dumps({{
                    'success': True,
                    'result': result,
                    'template': rule_instance.template,
                    'display_name': rule_instance.display_name
                }})
            }}
        else:
            return {{
                'statusCode': 200,
                'body': json.dumps({{
                    'success': False,
                    'message': 'Rule conditions not met'
                }})
            }}
            
    except Exception as e:
        return {{
            'statusCode': 500,
            'body': json.dumps({{
                'success': False,
                'error': str(e)
            }})
        }}
"""
        return template.format(class_name=class_name)
