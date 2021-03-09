import argparse
import atexit
import inspect
import logging
import os
import sys
from functools import wraps, partial
from importlib import import_module
from typing import Any, Dict, Callable, Optional

from omelette.core.settings import Settings, settings
from omelette.core.logging import init_logging
from omelette.eggs import Slack

logger = logging.getLogger(__name__)


class Recipe:
    """Context class that acts as base class for recipes that use Python classes. Otherwise, acts as singleton
    for providing context (e.g. settings, job_name, etc.) to plain functions."""
    _instance = None
    _arg_parser = None
    _required_args = None

    def __init__(self, is_lambda: bool = False):
        self.is_lambda: bool = is_lambda
        self.settings: Settings = settings
        self.job_name: Optional[str] = None
        self.job_dir: Optional[str] = None
        self.job_module: Optional[str] = None
        self.args: Optional[argparse.Namespace] = None
        self.lambda_event: Optional[Dict[Any, Any]] = None
        self.lambda_context: Optional[Dict[Any, Any]] = None
        self.logger: Optional[logging.Logger] = None

        if type(self) is not Recipe and not self.is_lambda:
            file_dir = os.path.dirname(sys.argv[0])
            self.init_recipe(file_dir)

    def __new__(cls, is_lambda: bool = False, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Recipe, cls).__new__(cls, *args, **kwargs)
        if cls._arg_parser is None:
            cls._arg_parser = argparse.ArgumentParser()
            cls._required_args = cls._arg_parser.add_argument_group('required arguments')

        # To avoid shared context between AWS Lambda invocations, register to explicitly reset cls variables
        atexit.register(cls.cleanup)

        if cls is not Recipe and issubclass(cls, Recipe):
            return super(Recipe, cls).__new__(cls, *args, **kwargs)
        else:
            return cls._instance

    def __del__(self):
        self.cleanup()

    @classmethod
    def cleanup(cls):
        cls._instance = None
        cls._arg_parser = None
        cls._required_args = None

    def parse_args(self):
        self.args = self._arg_parser.parse_args()

    @classmethod
    def add_argument(cls, *names, **kwargs):
        if kwargs.get("required"):
            cls._required_args.add_argument(*names, **kwargs)
        else:
            cls._arg_parser.add_argument(*names, **kwargs)

    def init_recipe(self, file_dir: str, lambda_event: Dict[Any, Any] = None, lambda_context: Dict[Any, Any] = None):
        if self.is_lambda:
            job_name = lambda_event.get("job_name", os.getenv("JOB_NAME"))

            if not job_name:
                raise Exception("Invalid job name: {job_name}. Pass to lambda input or set env var JOB_NAME")

            self.lambda_event = lambda_event
            self.lambda_context = lambda_context
        else:
            self.add_argument(
                "--job-name",
                "-j",
                help="Name of job in /jobs folder, used for finding configuration.",
                required=False if os.getenv("JOB_NAME") else True,
                default=os.getenv("JOB_NAME")
            )
            self.parse_args()
            job_name = self.args.job_name

        self.job_name = job_name
        available_jobs = os.listdir(file_dir + "/jobs")

        if not job_name or job_name not in available_jobs:
            raise Exception(f"Invalid job name: {job_name}")

        self.job_dir = os.path.join(file_dir, f"jobs/{job_name}/")

        self.settings.load(config_filepath=self.job_dir + "settings.toml")
        init_logging(is_lambda=self.is_lambda)
        self.logger = logging.getLogger("__main__")

        if os.path.exists(self.job_dir + f"{job_name}.py"):
            self.job_module = import_module(f".{job_name}.{job_name}", "jobs")

        return self

    def run(self):
        raise NotImplemented

    @classmethod
    def get_handler(cls, *args, **kwargs):
        def handler(event, context):
            file_dir = os.path.dirname(inspect.getfile(cls))
            _recipe = cls(is_lambda=True)
            _recipe.init_recipe(file_dir, event, context)
            return _recipe.run()

        return handler


context = Recipe()


def recipe(func=None, *, is_lambda: bool = False, max_retries: int = None, slack_alert: bool = False,
           slack_message_text: str = None):
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
        return partial(recipe,
                       is_lambda=is_lambda,
                       max_retries=max_retries,
                       slack_alert=slack_alert,
                       slack_message_text=slack_message_text)

    @wraps(func)
    def wrapper(*args, **kwargs):
        _recipe = Recipe(is_lambda=is_lambda)

        # Reset global to help with lambda shared context and try to reset the global to current instance.
        if is_lambda:
            global context
            context = _recipe

        file_dir = os.path.dirname(inspect.getfile(func))

        if is_lambda:
            lambda_event, lambda_context = args
        else:
            lambda_event = None
            lambda_context = None

        _recipe.init_recipe(file_dir, lambda_event, lambda_context)

        if slack_alert and context.settings.slack.api_token:
            slack = Slack(**context.settings.slack)
            try:
                if max_retries:
                    return retry(func, max_retries, _recipe, *args, **kwargs)
                else:
                    return func(_recipe, *args, **kwargs)
            except Exception as e:
                msg = slack_message_text or f"Error running recipe {_recipe.settings.slack.app_name}"
                slack.send_slack_alert(f"{msg}:\n {e}")
                raise e
            finally:
                Recipe.cleanup()
        else:
            try:
                if max_retries:
                    return retry(func, max_retries, _recipe, *args, **kwargs)
                else:
                    return func(_recipe, *args, **kwargs)
            finally:
                Recipe.cleanup()
    return wrapper


def argument(*names, **outer_kwargs):
    Recipe().add_argument(*names, **outer_kwargs)

    def wrapper(func, *args, **kwargs):
        return func
    return wrapper


def step(func=None, *, max_retries: int = None, slack_alert: bool = False, slack_message_text: str = None):
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
        return partial(step, max_retries=max_retries, slack_alert=slack_alert, slack_message_text=slack_message_text)

    @wraps(func)
    def wrapper(*args, **kwargs):
        _func = func

        if hasattr(context.job_module, func.__name__):
            _func = getattr(context.job_module, func.__name__)

        if slack_alert and context.settings.slack.api_token:
            slack = Slack(**context.settings.slack)
            try:
                if max_retries:
                    return retry(_func, max_retries, *args, **kwargs)
                else:
                    return _func(*args, **kwargs)
            except Exception as e:
                msg = slack_message_text or f"Error running recipe step {context.settings.slack.app_name}"
                slack.send_slack_alert(f"{msg}:\n {e}")
                raise e
        else:
            if max_retries:
                return retry(_func, max_retries, *args, **kwargs)
            else:
                return _func(*args, **kwargs)
    return wrapper


def retry(func: Callable, max_retries: int = 3, *args, **kwargs):
    retries = max_retries

    while retries > 0:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            retries -= 1

            if retries == 0:
                raise e

            logger.exception(f"Failed on execution of {func.__name__}. Retrying now. {retries} retries left.")

