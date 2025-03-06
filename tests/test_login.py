import rich_click as click
import requests_mock
import pytest

from threading import Timer
from click.testing import CliRunner

from weni_cli.cli import login
from weni_cli.wsgi import auth_queue


@pytest.fixture(autouse=True)
def slow_down_tests(mocker):
    mocker.patch("weni_cli.wsgi.serve", return_value=None)


@requests_mock.Mocker(kw="requests_mock")
def test_login(mocker, **kwargs):
    requests_mock = kwargs.get("requests_mock")
    requests_mock.post(
        "https://accounts.weni.ai/auth/realms/weni/protocol/openid-connect/token",
        status_code=200,
        json={"access_token": "654321"},
    )

    def fake_login_callback():
        auth_queue.put("123456")

    runner = CliRunner()
    with runner.isolated_filesystem():
        mocker.patch("click.launch", return_value=None)
        store_set_patch = mocker.patch("weni_cli.store.Store.set")

        t = Timer(0.1, fake_login_callback)
        t.start()
        result = runner.invoke(login)

        click.launch.assert_called_once_with(
            "https://accounts.weni.ai/auth/realms/weni/protocol/openid-connect/auth?client_id=weni-cli&redirect_uri=http://localhost:50051/sso-callback&response_type=code"
        )

        assert store_set_patch.call_count == 1
        store_set_patch.assert_called_once_with("token", "654321")

        assert result.exit_code == 0
        assert (
            result.output
            == "Opening browser for login, please wait...\nIf the browser does not open, please open the following URL manually: https://accounts.weni.ai/auth/realms/weni/protocol/openid-connect/auth?client_id=weni-cli&redirect_uri=http://localhost:50051/sso-callback&response_type=code\nLogin successful\n"
        )


def test_login_callback_error(mocker):
    def fake_login_callback():
        auth_queue.put("")

    runner = CliRunner()
    with runner.isolated_filesystem():
        mocker.patch("click.launch", return_value=None)
        store_set_patch = mocker.patch("weni_cli.store.Store.set")

        t = Timer(0.1, fake_login_callback)
        t.start()
        result = runner.invoke(login)

        assert store_set_patch.call_count == 0

        assert result.exit_code == 0
        assert (
            result.output
            == "Opening browser for login, please wait...\nIf the browser does not open, please open the following URL manually: https://accounts.weni.ai/auth/realms/weni/protocol/openid-connect/auth?client_id=weni-cli&redirect_uri=http://localhost:50051/sso-callback&response_type=code\nAn error occurred: Failed to receive code\n"
        )


@requests_mock.Mocker(kw="requests_mock")
def test_login_exchange_token_error(mocker, **kwargs):
    requests_mock = kwargs.get("requests_mock")
    requests_mock.post(
        "https://accounts.weni.ai/auth/realms/weni/protocol/openid-connect/token",
        status_code=400,
        json={"error": True},
    )

    def fake_login_callback():
        auth_queue.put("123456")

    runner = CliRunner()
    with runner.isolated_filesystem():
        mocker.patch("click.launch", return_value=None)
        store_set_patch = mocker.patch("weni_cli.store.Store.set")

        t = Timer(0.1, fake_login_callback)
        t.start()
        result = runner.invoke(login)

        assert store_set_patch.call_count == 0

        assert result.exit_code == 0
        assert (
            result.output
            == "Opening browser for login, please wait...\nIf the browser does not open, please open the following URL manually: https://accounts.weni.ai/auth/realms/weni/protocol/openid-connect/auth?client_id=weni-cli&redirect_uri=http://localhost:50051/sso-callback&response_type=code\nAn error occurred: Failed to exchange code for token\n"
        )
