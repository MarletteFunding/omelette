from omelette import Recipe, step, recipe, argument


@step(max_retries=2, slack_alert=True, slack_message_text="Failed at step 'add'")
def add(context: Recipe, first: int, second: int):
    example = context.settings.example
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
def main(context: Recipe):
    # Access logger with _context.logger, or initialize in your file with logging.getLogger(__name__)
    context.logger.info(f"Running {context.job_name}")

    # Access settings object (variables from settings.toml) with _context
    example = context.settings.example
    context.logger.debug(example)

    return add(context.args.first, context.args.second)


if __name__ == "__main__":
    main()
