from omelette import Recipe


class AddLambda(Recipe):
    def run(self):
        # Access logger with self.logger, or initialize in your file with logging.getLogger(__name__)
        self.logger.info(f"Running {self.job_name}")

        # Access settings object (variables from settings.toml) with self
        # Or import global: `from omelette import settings`
        example = self.settings.example
        self.logger.debug(example)

        # Access lambda_event and lambda_context from self. These are the raw event/context from the caller.
        return self.add(self.lambda_event.get("first"), self.lambda_event.get("second"))

    def add(self, first: int, second: int):
        one = self.plus_one(first)
        two = one + second

        print(two)

        return two

    @staticmethod
    def plus_one(x: int):
        return x + 1


# Required - point lambda handler to this
handler = AddLambda.get_handler()


if __name__ == "__main__":
    import sys
    import json

    # Lambda event
    event = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    handler(event, {})
