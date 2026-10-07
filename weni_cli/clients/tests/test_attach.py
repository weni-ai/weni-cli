import json

import pytest

from weni_cli.clients.cli_client import CLIClient, RequestError
from weni_cli.commands.attach import AttachHandler


class DummyResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.content = json.dumps(payload).encode()

    def json(self):
        return self._payload


@pytest.fixture
def client(mocker):
    mocker.patch("weni_cli.clients.cli_client.Store.__init__", return_value=None)
    mocker.patch("weni_cli.clients.cli_client.Store.get", return_value="token")
    mocker.patch("weni_cli.clients.cli_client.get_cli_version", return_value="0.0.0")
    return CLIClient()


def test_attach_identity_success(client, mocker):
    response = DummyResponse(
        200,
        {"consumer_id": "con_A", "attachment_status": "confirmed", "affected_protocol_ids": [1]},
    )
    request = mocker.patch.object(client.session, "request", return_value=response)
    payload = client.attach_identity("prj", "42", "commerce_user_id", "store-user-42", True)
    assert payload["consumer_id"] == "con_A"
    sent = request.call_args.kwargs["json"]
    assert sent["urn_id"] == "42"
    assert sent["anchor"]["verified"] is True
    assert "attach" in request.call_args.kwargs["url"]


@pytest.mark.parametrize(
    "status, code",
    [
        (400, "validation"),
        (409, "conflicting_consumer"),
        (403, "forbidden"),
        (503, "identity_unavailable"),
    ],
)
def test_attach_identity_errors(client, mocker, status, code):
    mocker.patch.object(client.session, "request", return_value=DummyResponse(status, {"error": code}))
    with pytest.raises(RequestError) as caught:
        client.attach_identity("prj", "42", "verified_email", "a@b.c", False)
    assert caught.value.data["error"] == code


def test_attach_command_prints_success_and_error(mocker):
    mocker.patch("weni_cli.commands.attach.Store.__init__", return_value=None)
    mocker.patch("weni_cli.commands.attach.Store.get", return_value="prj")
    echo = mocker.patch("weni_cli.commands.attach.click.echo")
    client = mocker.patch("weni_cli.commands.attach.CLIClient")
    client.return_value.attach_identity.return_value = {"consumer_id": "con_A", "attachment_status": "confirmed"}
    assert AttachHandler().execute(urn_id="42", anchor_type="commerce_user_id", anchor_value="u", verified=True) == 0
    printed = json.loads(echo.call_args.args[0])
    assert printed["consumer_id"] == "con_A"

    client.return_value.attach_identity.side_effect = RequestError("validation", status_code=400, data={"error": "validation"})
    assert AttachHandler().execute(urn_id="42", anchor_type="commerce_user_id", anchor_value="u", verified=False) == 1
    assert json.loads(echo.call_args.args[0])["error"] == "validation"
