import re
import pytest
import regex
from click.testing import CliRunner


@pytest.fixture
def sample_definition_file():
    """Create a sample definition file for testing."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create a valid definition file
        with open("valid_channel_definition.yaml", "w") as f:
            f.write(
                """
channels:
  - name: Test Channel
    channel_type: E2
    schemes:
      - external
    config:
      mo_response_content_type: application/json
      mo_response: ""
      mt_response_check: ""
      send_url: https://example.com/send_msg
      send_method: POST
      send_template: '{"chat_id":"{{.urn_path}}","text":"{{.text}}","parse_mode":"Markdown"}'
      content_type: application/x-www-form-urlencoded
      receive_template: '{"messages":[{"urn_path":"{{.message.from.id}}","text":"{{.message.text}}","contact_name":"{{.message.from.username}}","id":"{{.message.message_id}}"}]}'
      send_authorization: ""
                """
            )

        yield {
            "valid_path": "valid_channel_definition.yaml",
        }

@pytest.fixture
def valid_channel_definition():
    """Return a valid channel definition dictionary."""
    return {
        "channels": [
            {
                "name": "Test Channel",
                "channel_type": "E2",
                "schemes":["external"],
                "config": {                    
                    "mo_response_content_type": "application/json",
                    "mo_response": "",
                    "mt_response_check": "",
                    "send_url": "https://example.com/send_msg",
                    "send_method": "POST",
                    "send_template": "{\"chat_id\":\"{{.urn_path}}\",\"text\":\"{{.text}}\",\"parse_mode\":\"Markdown\"}",
                    "content_type": "application/x-www-form-urlencoded",
                    "receive_template": "{\"messages\":[{\"urn_path\":\"{{.message.from.id}}\",\"text\":\"{{.message.text}}\",\"contact_name\":\"{{.message.from.username}}\",\"id\":\"{{.message.message_id}}\"}]}",
                    "send_authorization": ""
                }
            }
        ]
    }
