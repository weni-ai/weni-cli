import click


class Handler:
    def execute(self, **kwargs):
        raise NotImplementedError()

    def exit(self, error=None):
        if error:
            click.echo(f"An error occurred: {error}")
