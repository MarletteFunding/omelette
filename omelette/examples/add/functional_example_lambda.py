from typing import Dict, Any

from omelette import Recipe, context, step, recipe, settings


@step(max_retries=2, slack_alert=True, slack_message_text="Failed at step 'add'")
def add(first: int, second: int):
    # Access global settings & context objects: `from omelette import context, settings`:
    example = settings.example
    context.logger.debug(example)

    one = plus_one(first)
    two = one + second

    return two


def plus_one(x: int):
    return x + 1


# Add `is_lambda=True` so it properly handles AWS event & context, and initializes logging for Lambda execution
@recipe(is_lambda=True, slack_alert=True, max_retries=3)
def handle(_context: Recipe, aws_event: Dict[Any, Any], aws_context: Dict[Any, Any]):
    # Access logger with _context.logger, or initialize in your file with logging.getLogger(__name__)
    _context.logger.info(f"Running {_context.job_name}")

    # Access settings object (variables from settings.toml) with _context
    example = _context.settings.example
    _context.logger.debug(example)

    # Access AWS Lambda event & context from arguments:
    print(aws_event)
    print(aws_context)

    # Or from _context
    print(_context.lambda_event)
    print(_context.lambda_context)

    return add(_context.args.first, _context.args.second)


if __name__ == "__main__":
    import sys
    import json

    # For ease of testing, pass event as json serialized string as first command line argument
    event = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}

    # Entrypoint function can have any name, but it is what you set as the lambda handler attribute
    handle(event, {})
