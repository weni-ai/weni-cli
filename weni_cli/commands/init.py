import rich_click as click
import os

from weni_cli.commands.run import DEFAULT_TEST_DEFINITION_FILE
from weni_cli.handler import Handler

TOOLS_FOLDER = "tools"
SAMPLE_AGENT_DEFINITION_FILE_NAME = "agent_definition.yaml"

SAMPLE_GET_ADDRESS_TOOL_NAME = "get_address"

SAMPLE_AGENT_DEFINITION_YAML = f"""agents:
    cep_agent:
        name: "CEP Agent"
        description: "Weni's CEP agent with components"
        instructions:
            - "You are an expert in providing addresses to the user based on a postal code provided by the user"
            - "The user will send a ZIP code (postal code) and you must provide the address corresponding to this code."
        guardrails:
            - "Don't talk about politics, religion or any other sensitive topic. Keep it neutral."
        tools:
            - get_address:
                name: "Get Address"
                source:
                    path: "tools/get_address"
                    entrypoint: "main.GetAddress"
                    path_test: "{DEFAULT_TEST_DEFINITION_FILE}"
                description: "Function to get the address from the postal code"
                parameters:
                    - cep:
                        description: "postal code of a place"
                        type: "string"
                        required: true
"""

SAMPLE_GET_ADDRESS_TOOL_PY = """from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
import requests


class GetAddress(Tool):
    def execute(self, context: Context) -> TextResponse:
        cep = context.parameters.get("cep", "")
        print(cep)
        address_response = self.get_address_by_cep(cep=cep)
        print(address_response)
        return TextResponse(data=address_response)

    def get_address_by_cep(self, cep):
        url = f"https://viacep.com.br/ws/{cep}/json/"
        response = requests.get(url)
        return response.json()
"""

SAMPLE_TESTS_YAML = """tests:
    test_1:
        parameters:
            cep: "57160000"
    test_2:
        parameters:
            cep: "57038-635"
    test_3:
        parameters:
            cep: "57160-000"
"""

SAMPLE_GET_ADDRESS_REQUIREMENTS_TXT = """requests==2.32.3
"""


class InitHandler(Handler):
    """Handles initialization of sample agent definition, tools, and tests."""

    def execute(self):
        """Execute the initialization process by creating sample files and folders."""
        self.create_sample_agent_definition_file()
        self.create_sample_tools()
        self.create_sample_tests()

    def create_sample_agent_definition_file(self):
        """Create a sample agent definition file in the current directory."""
        self._write_file(
            filename=SAMPLE_AGENT_DEFINITION_FILE_NAME,
            content=SAMPLE_AGENT_DEFINITION_YAML,
            description="Sample agent definition file",
        )

    def create_sample_tools(self):
        """Create sample tools with their respective files."""
        self.create_sample_tool(
            tool_name=SAMPLE_GET_ADDRESS_TOOL_NAME,
            code=SAMPLE_GET_ADDRESS_TOOL_PY,
            requirements=SAMPLE_GET_ADDRESS_REQUIREMENTS_TXT,
        )

    def create_sample_tool(self, tool_name, code, requirements):
        """
        Create a sample tool with its main code file and requirements.

        Args:
            tool_name: Name of the tool
            code: Python code content for the tool
            requirements: Requirements content for pip
        """
        # Ensure the tools folder structure exists
        self._ensure_directory(TOOLS_FOLDER)
        self._ensure_directory(f"{TOOLS_FOLDER}/{tool_name}")

        # Create the main tool file
        tool_path = f"{TOOLS_FOLDER}/{tool_name}/main.py"
        self._write_file(filename=tool_path, content=code, description=f"Sample tool {tool_name}")

        # Create the requirements file
        self._write_file(
            filename=f"{TOOLS_FOLDER}/{tool_name}/requirements.txt",
            content=requirements,
            description=f"Sample requirements file for {tool_name}",
        )

    def create_sample_tests(self):
        """Create sample test files for the tools."""
        self.create_sample_test(tool_name=SAMPLE_GET_ADDRESS_TOOL_NAME, test_content=SAMPLE_TESTS_YAML)

    def create_sample_test(self, tool_name, test_content):
        """
        Create a sample test file for a tool.

        Args:
            tool_name: Name of the tool to create tests for
            test_content: YAML content for the test file
        """
        test_path = f"{TOOLS_FOLDER}/{tool_name}/{DEFAULT_TEST_DEFINITION_FILE}"
        self._write_file(filename=test_path, content=test_content, description=f"Sample tests file for {tool_name}")

    def _ensure_directory(self, directory_path):
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory_path: Path of the directory to ensure
        """
        try:
            os.mkdir(directory_path)
        except FileExistsError:
            pass  # Directory already exists, which is fine
        except Exception as e:
            click.echo(f"Error creating directory {directory_path}: {str(e)}")

    def _write_file(self, filename, content, description):
        """
        Write content to a file and display a message.

        Args:
            filename: Path of the file to write
            content: Content to write to the file
            description: Description for the success message
        """
        try:
            with open(filename, "w") as f:
                f.write(content)
            click.echo(f"{description} created in: {filename}")
        except Exception as e:
            click.echo(f"Error creating {description} at {filename}: {str(e)}")
