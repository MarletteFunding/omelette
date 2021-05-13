from omelette import Recipe
from omelette.eggs import Slack


class {{cookiecutter.recipe_name.title().replace('_', '')}}(Recipe):
    def __init__(self, args=None):
        super({{cookiecutter.recipe_name.title().replace('_', '')}}, self).__init__(args)
        self.slack = Slack(**self.settings.slack)

    def run(self) -> None:
        self.logger.info(f"Starting job {self.job_name}")

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


if __name__ == "__main__":
    import sys
    sys.exit({{cookiecutter.recipe_name.title().replace('_', '')}}(sys.argv[1:]).run())
