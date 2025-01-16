import click
import time

from weni_cli.auth import Auth
from weni_cli.handler import Handler
from weni_cli.store import STORE_TOKEN_KEY, Store
from weni_cli.wsgi import serve, shutdown, auth_queue


class LoginHandler(Handler):
    def execute(self):
        # Start our web server to receive the login callback
        serve()

        auth = Auth()

        click.echo("Opening browser for login, please wait...")
        click.echo(f"If the browser does not open, please open the following URL manually: {auth.get_login_url()}")
        click.launch(auth.get_login_url())
        code = None

        while True:
            code = auth_queue.get()
            if code is not None:
                break

        if not code:
            return self.exit("Failed to receive code")

        token = auth.exchange_code(code)

        if not token:
            return self.exit("Failed to exchange code for token")

        store = Store()

        store.set(STORE_TOKEN_KEY, token)

        click.echo("Login successful")
        time.sleep(1)
        shutdown()

    def exit(self, error=None):
        if error:
            click.echo(f"An error occurred: {error}")
        time.sleep(1)
        shutdown()
