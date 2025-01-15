import click
import os

from zipfile import ZipFile
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
          path: "skills/order_status.zip"
          description: "Function to get the order status"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
      - get_order_details:
          name: "Get Order Details"                                                           # Maximum of 53 characters
          path: "skills/order_details.zip"
          description: "Function to get the order details"
          parameters:
            - order_id:
                description: "Order ID"
                type: "string"
                required: true
"""

SAMPLE_ORDER_STATUS_SKILL_PY = """def lambda_handler(event, context):
    order_id = event.get("order_id")

    return {"id": order_id,"status": "SHIPPED"}
"""

SAMPLE_ORDER_DETAILS_SKILL_PY = """def lambda_handler(event, context):
    order_id = event.get("order_id")

    return {"id": order_id, "details": {"name": "Product A", "quantity": 1}}
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

    def create_sample_skill(self, filename, code):
        # create the skills folder if it does not exist
        try:
            os.mkdir(SKILLS_FOLDER)
        except FileExistsError:
            pass

        skill_path = f"{SKILLS_FOLDER}/{filename}.zip"

        with ZipFile(skill_path, "w") as z:
            z.writestr(f"{filename}.py", code)

        click.echo(f"Sample skill {filename} created in: {skill_path}")
