import click
import os

from weni_cli.handler import Handler

SKILLS_FOLDER = "skills"
SAMPLE_AGENT_DEFINITION_FILE_NAME = "agent_definition.yaml"

SAMPLE_AGENT_DEFINITION_YAML = """agents:
  sample_agent:
    name: "Sample Agent"                                                                      # Maximum of 128 characters
    description: "Weni's sample agent"
    instructions:
      - "You should always be polite, respectful and helpful, even if the user is not."       # Minimum of 40 characters
      - "If you don't know the answer, don't lie. Tell the user you don't know."              # Minimum of 40 characters
    guardrails:
      - "Don't talk about politics, religion or any other sensitive topic. Keep it neutral."  # Minimum of 40 characters
    skills:
      - get_order_status:
          name: "Get Order Status"                                                            # Maximum of 53 characters
          source:
            path: "skills/order_status"
            entrypoint: "lambda_function.lambda_handler"
          description: "Function to get the order status"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
      - get_order_details:
          name: "Get Order Details"                                                           # Maximum of 53 characters
          source:
            path: "skills/order_details"
            entrypoint: "lambda_function.lambda_handler"
          description: "Function to get the order details"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
"""

SAMPLE_ORDER_STATUS_SKILL_PY = """def lambda_handler(event, context):

    agent = event['agent']
    actionGroup = event['actionGroup']
    function = event['function']
    parameters = event.get('parameters', [])

    response_body = {
        'TEXT': {
            'body': "Your order status is 'Shipped'"
        }
    }

    function_response = {
        'actionGroup': event['actionGroup'],
        'function': event['function'],
        'functionResponse': {
            'responseBody': response_body
        }
    }

    session_attributes = event['sessionAttributes']
    prompt_session_attributes = event['promptSessionAttributes']

    action_response = {
        'messageVersion': '1.0',
        'response': function_response,
        'sessionAttributes': session_attributes,
        'promptSessionAttributes': prompt_session_attributes
    }

    return action_response
"""

SAMPLE_ORDER_DETAILS_SKILL_PY = """def lambda_handler(event, context):

    agent = event['agent']
    actionGroup = event['actionGroup']
    function = event['function']
    parameters = event.get('parameters', [])

    response_body = {
        'TEXT': {
            'body': "Your order contains 2 items, a t-shirt and a pair of shoes."
        }
    }

    function_response = {
        'actionGroup': event['actionGroup'],
        'function': event['function'],
        'functionResponse': {
            'responseBody': response_body
        }
    }

    session_attributes = event['sessionAttributes']
    prompt_session_attributes = event['promptSessionAttributes']

    action_response = {
        'messageVersion': '1.0',
        'response': function_response,
        'sessionAttributes': session_attributes,
        'promptSessionAttributes': prompt_session_attributes
    }

    return action_response
"""


class InitHandler(Handler):
    def execute(self):
        self.create_sample_agent_definition_file()
        self.create_sample_skills()

    def create_sample_agent_definition_file(self):
        with open(SAMPLE_AGENT_DEFINITION_FILE_NAME, "w") as f:
            f.write(SAMPLE_AGENT_DEFINITION_YAML)

        click.echo(f"Sample agent definition file created in: {SAMPLE_AGENT_DEFINITION_FILE_NAME}")

    def create_sample_skills(self):
        self.create_sample_skill("order_status", SAMPLE_ORDER_STATUS_SKILL_PY)
        self.create_sample_skill("order_details", SAMPLE_ORDER_STATUS_SKILL_PY)

    def create_sample_skill(self, skill_name, code):
        # create the base skills folder if it does not exist
        try:
            os.mkdir(SKILLS_FOLDER)
        except FileExistsError:
            pass

        # create the specific skill folder if it does not exist
        try:
            os.mkdir(f"{SKILLS_FOLDER}/{skill_name}")
        except FileExistsError:
            pass

        skill_path = f"{SKILLS_FOLDER}/{skill_name}/lambda_function.py"

        with open(skill_path, "w") as f:
            f.write(code)

        click.echo(f"Sample skill {skill_name} created in: {skill_path}")
