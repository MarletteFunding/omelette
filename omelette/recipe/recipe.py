import argparse
import inspect
from functools import wraps, partial
import os
from typing import Any, Dict, Callable, Optional

from omelette import Settings, init_logging
from omelette.eggs import Slack


class Recipe:
    """Context class that acts as base class for recipes that use Python classes. Otherwise, acts as singleton
    for providing context (e.g. settings, job_name, etc.) to plain functions."""
    _instance = None
    _arg_parser = None
    _required_args = None

    def __init__(self):
        self.settings: Optional[Settings] = None
        self.job_name: Optional[str] = None
        self.job_dir: Optional[str] = None
        self.args = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Recipe, cls).__new__(cls)
        if cls._arg_parser is None:
            cls._arg_parser = argparse.ArgumentParser()
            cls._required_args = cls._arg_parser.add_argument_group('required arguments')
        return cls._instance

    def parse_args(self):
        self.args = self._arg_parser.parse_args()

    @classmethod
    def add_argument(cls, *names, **kwargs):
        if kwargs.get("required"):
            cls._required_args.add_argument(*names, **kwargs)
        else:
            cls._arg_parser.add_argument(*names, **kwargs)

    def _init_recipe(self, job_name: str, file_dir):
        self.job_name = job_name
        self.job_dir = file_dir
        available_jobs = os.listdir(file_dir + "/jobs")

        if not job_name or job_name not in available_jobs:
            raise Exception(f"Invalid job name: {job_name}")

        self.job_dir = os.path.join(file_dir, f"jobs/{job_name}/")
        self.settings = Settings(config_filepath=self.job_dir + "settings.toml")

        init_logging()

    def __call__(self, job_name: str, file_dir: str):
        self._init_recipe(os.getenv("JOB_NAME", job_name), file_dir)
        return self

    def run(self):
        pass


def recipe(func=None, *, slack_alert: bool = False, slack_message_text: str = None):
    """
    Decorator for the entrypoint callable in non-class-based workflows, e.g. plain Python functions. An alternative to
    sub-classing Recipe. Adds requirement for --job-name/-j argument, and will pass the Recipe context with
    initialized settings, logging, etc to the wrapped function. Optional try/except that will send a slack alert,
    controlled by parameter `slack_alert`. Can be used with or without call using (), e.g. @recipe will work and so will
    @recipe() or @recipe(slack_alert=True).

    Example:

    @recipe
    def main(context: Recipe):
        print(context.job_name)

    if __name__ == "__main__":
        main()
    """
    if func is None:
        return partial(recipe, slack_alert=slack_alert, slack_message_text=slack_message_text)

    @wraps(func)
    def wrapper(*args, **kwargs):
        _recipe = Recipe()
        _recipe.add_argument(
            "--job-name",
            "-j",
            help="Name of job in /jobs folder, used for finding configuration.",
            required=True,
            default=os.getenv("JOB_NAME")
        )
        _recipe.parse_args()
        job_name = _recipe.args.job_name
        file_dir = os.path.dirname(inspect.getfile(func))
        context = _recipe(job_name, file_dir)

        if slack_alert and context.settings.slack.api_token:
            slack = Slack(**context.settings.slack)
            try:
                return func(context, *args, **kwargs)
            except Exception as e:
                msg = slack_message_text or f"Omelette: Error running recipe {context.settings.slack.app_name}"
                slack.send_slack_alert(f"{msg}: {e}")
                raise e
        else:
            return func(context, *args, **kwargs)
    return wrapper


def recipe_arg(*names, **outer_kwargs):
    Recipe().add_argument(*names, **outer_kwargs)

    def wrapper(func, *args, **kwargs):
        return func
    return wrapper


def step(func=None, *, slack_alert: bool = False, slack_message_text: str = None):
    """
    Decorator for wrapping any plain ol' Python functions that need access to shared context from Recipe. Avoids having
    to pass context down tree of child functions.

    Example:

    @step
    def print_job_name(context: Recipe):
        print(context.job_name)

    @recipe
    def main(context: Recipe):
        print_job_name()

    if __name__ == "__main__":
        main()
    """
    if func is None:
        return partial(step, slack_alert=slack_alert, slack_message_text=slack_message_text)

    @wraps(func)
    def wrapper(*args, **kwargs):
        context = Recipe._instance
        if slack_alert and context.settings.slack.api_token:
            slack = Slack(**context.settings.slack)
            try:
                return func(context, *args, **kwargs)
            except Exception as e:
                msg = slack_message_text or f"Omelette: Error running step {context.settings.slack.app_name}"
                slack.send_slack_alert(f"{msg}: {e}")
                raise e
        else:
            return func(context, *args, **kwargs)
    return wrapper
