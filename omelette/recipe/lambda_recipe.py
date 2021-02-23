from functools import wraps, partial
import inspect
import os
from typing import Any, Dict, Callable, Optional

from omelette import Settings, init_logging
from omelette.eggs import Slack
from omelette.recipe import Recipe


class LambdaRecipe(Recipe):
    """Context class that acts as base class for recipes that use Python classes with AWS Lambda. Otherwise, acts as
    singleton for providing context (e.g. settings, job_name, etc.) to plain function recipes, specific to AWS Lambda."""
    def __init__(self, handler: Callable = None):
        self.handler = handler
        self.event = None
        self.context = None
        super(LambdaRecipe, self).__init__()

    def __new__(cls, handler: Callable = None):
        if cls._instance is None:
            cls._instance = super(LambdaRecipe, cls).__new__(cls)
        return cls._instance

    def _init_recipe(self, job_name: str, event: Dict[Any, Any] = None, context: Dict[Any, Any] = None):
        self.job_name = job_name
        file_dir = os.path.dirname(inspect.getfile(self.handler))
        available_jobs = os.listdir(file_dir + "/jobs")

        if not job_name or job_name not in available_jobs:
            raise Exception(f"Invalid job name: {job_name}. Pass to lambda input or set env var JOB_NAME")

        self.job_dir = os.path.join(file_dir, f"jobs/{job_name}/")
        self.settings = Settings(config_filepath=self.job_dir + "settings.toml")
        self.event = event
        self.context = context

        init_logging(is_lambda=True)

    def __call__(self, event: Dict[Any, Any], context: Dict[Any, Any]):
        job_name = event.get("job_name", os.getenv("JOB_NAME"))
        self._init_recipe(job_name, event, context)
        return self


def recipe(func=None, *, slack_alert: bool = False, slack_message_text: str = None):
    """
    Decorator for the entrypoint callable in non-class-based AWS Lambda workflows, e.g. plain Python functions.
    An alternative to sub-classing LambdaRecipe. Requires input variable "job_name" to be present in Lambda event.
    Will pass the LambdaRecipe context, along with the AWS Lambda event & context to the wrapped function. Optional
    try/except that will send a slack alert, controlled by parameter `slack_alert`. Can be used with or without
    call using (), e.g. @recipe will work and so will @recipe() or @recipe(slack_alert=True).

    Example:

    @recipe
    def main(context: Recipe, event: Dict[Any, Any], aws_context: Dict[Any, Any]):
        print(context.job_name)

    if __name__ == "__main__":
        main()

    In AWS Lambda, handler would be set to `main` as it accepts the passed event and context objects due to this decorator.
    """
    if func is None:
        return partial(recipe, slack_alert=slack_alert, slack_message_text=slack_message_text)

    @wraps(func)
    def wrapper(*args, **kwargs):
        context = LambdaRecipe(func)(*args, **kwargs)

        if slack_alert and context.settings.slack.api_token:
            slack = Slack(**context.settings.slack)
            try:
                return func(context, *args)
            except Exception as e:
                msg = slack_message_text or f"Omelette: Error running recipe {context.settings.slack.app_name}"
                slack.send_slack_alert(f"{msg}: {e}")
                raise e
        else:
            return func(context, *args)
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
    def main(context: Recipe, event: Dict[Any, Any], aws_context: Dict[Any, Any]):
        print_job_name()

    if __name__ == "__main__":
        main()
    """
    if func is None:
        return partial(step, slack_alert=slack_alert, slack_message_text=slack_message_text)

    @wraps(func)
    def wrapper(*args, **kwargs):
        context = LambdaRecipe._instance

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
