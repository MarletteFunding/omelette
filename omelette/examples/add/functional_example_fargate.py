from omelette import Recipe, context, step, recipe, argument, settings


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


# Add command line arguments using standard ArgParse.add_argument args/kwargs.
@argument("--first", "-f", type=int, required=True)
@argument("--second", "-s", type=int, required=True)
@recipe(slack_alert=True, max_retries=3)
def main(_context: Recipe):
    # Access logger with _context.logger, or initialize in your file with logging.getLogger(__name__)
    _context.logger.info(f"Running {_context.job_name}")

    # Access settings object (variables from settings.toml) with _context
    example = _context.settings.example
    _context.logger.debug(example)

    return add(_context.args.first, _context.args.second)


if __name__ == "__main__":
    main()
