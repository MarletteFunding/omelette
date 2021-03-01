from omelette import Recipe, argument


class AddFargate(Recipe):
    # Add command line arguments using standard ArgParse.add_argument args/kwargs.
    @argument("--first", "-f", type=int, required=True)
    @argument("--second", "-s", type=int, required=True)
    def run(self):
        # Access logger with self.logger, or initialize in your file with logging.getLogger(__name__)
        self.logger.info(f"Running {self.job_name}")

        # Access settings object (variables from settings.toml) with self
        # Or import global: `from omelette import settings`
        example = self.settings.example
        self.logger.debug(example)

        # Access command line arguments with self.args
        return self.add(self.args.first, self.args.second)

    def add(self, first: int, second: int):
        one = self.plus_one(first)
        two = one + second

        print(two)

        return two

    @staticmethod
    def plus_one(x: int):
        return x + 1


if __name__ == "__main__":
    # Every Recipe subclass should have a main entrypoint by overriding the `run` method.
    AddFargate().run()
