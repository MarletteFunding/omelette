from typing import Dict, Any

from omelette import Recipe, step, recipe


@step(max_retries=2, slack_alert=True, slack_message_text="Failed at step 'add'")
def add(context: Recipe, first: int, second: int):
    example = context.settings.example
    context.logger.debug(example)

    one = plus_one(first)
    two = one + second

    return two


def plus_one(x: int):
    return x + 1


# Add `is_lambda=True` so it properly handles AWS event & context, and initializes logging for Lambda execution
@recipe(is_lambda=True, slack_alert=True, max_retries=3)
def handle(context: Recipe, aws_event: Dict[Any, Any], aws_context: Dict[Any, Any]):
    # Access logger with context.logger, or initialize in your file with logging.getLogger(__name__)
    context.logger.info(f"Running {context.job_name}")

    # Access settings object (variables from settings.toml) with context
    example = context.settings.example
    context.logger.debug(example)

    # Access AWS Lambda event & context from arguments:
    print(aws_event)
    print(aws_context)

    # Or from context
    print(context.lambda_event)
    print(context.lambda_context)

    return add(context.args.first, context.args.second)


if __name__ == "__main__":
    import sys
    import json

    # For ease of testing, pass event as json serialized string as first command line argument
    event = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}

    # Entrypoint function can have any name, but it is what you set as the lambda handler attribute
    handle(event, {})
