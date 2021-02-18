import re
from typing import Union


def validate_underscore_name(text: str) -> Union[bool, str]:
    if len(text) > 0 and re.match("^[A-Za-z0-9_]*$", text):
        return True
    else:
        return "Please enter a name with only letters, numbers, and underscores"


def validate_schedule_expression(text: str) -> Union[bool, str]:
    invalid_response = "Invalid schedule. Must be AWS compatible rate() or cron() expression. " \
                       "See https://docs.aws.amazon.com/eventbridge/latest/userguide/scheduled-events.html"

    if text.startswith("rate(") and text.endswith(")"):
        rate = re.findall(r'\((.*?)\)', text)[0]
        rate_parts = rate.split(" ")

        if len(rate_parts) != 2:
            return invalid_response
        elif rate_parts[1] not in {"minute", "minutes", "hour", "hours", "day", "days"}:
            return invalid_response

        try:
            int(rate_parts[0])
        except TypeError:
            return invalid_response

        return True
    elif text.startswith("cron(") and text.endswith(")"):
        # TODO: validate against AWS cron rules. See https://github.com/beemhq/aws-cron-parser/blob/master/src/lib/parse.ts for inspiration
        return True
    else:
        return invalid_response
