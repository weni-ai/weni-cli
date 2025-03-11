import rich_click as click


class Handler:
    def execute(self, **kwargs):  # pragma: no cover
        raise NotImplementedError()

    def exit(self, error=None):
        if error:
            click.echo(f"An error occurred: {error}")
