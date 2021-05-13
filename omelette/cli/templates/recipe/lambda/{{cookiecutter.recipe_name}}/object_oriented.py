from omelette import Recipe


class {{cookiecutter.recipe_name.title().replace('_', '')}}(Recipe):
    def run(self) -> None:
        self.logger.info(f"Starting job {self.job_name}")

        self.logger.info(f"Lambda event: {self.lambda_event}")

        self.extract()
        self.transform()
        self.load()

        self.logger.info(f"Finished job {self.job_name}")

    def extract(self) -> str:
        pass

    def transform(self):
        pass

    def load(self):
        pass


# Required - point lambda handler to this
handler = {{cookiecutter.recipe_name.title().replace('_', '')}}.get_handler()


if __name__ == "__main__":
    import sys
    import json

    # Lambda event
    event = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    handler(event, {})
