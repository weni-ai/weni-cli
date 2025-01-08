class Handler:
    def execute(self, **kwargs):
        raise NotImplementedError()

    def exit(self, error=None):
        if error:
            print(f"An error occurred: {error}")
