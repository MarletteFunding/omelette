import json
from typing import Any, Dict

from omelette import Recipe, step, recipe
from omelette.eggs import SftpS3Interface, Files, Sftp, S3, Snowflake, Kafka


@step
def extract(context: Recipe):
    pass


@step
def transform(context: Recipe):
    pass


@step
def load(context: Recipe):
    pass


@recipe(is_lambda=True, max_retries=None, slack_alert=True)
def handle(context: Recipe, aws_event: Dict[Any, Any], aws_context: Dict[Any, Any]):
    context.logger.info(f"Starting handler for job {context.job_name}")

    extract()
    transform()
    load()

    context.logger.info(f"Finished {context.job_name}")
    return


if __name__ == "__main__":
    import sys

    event = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    handle(event, {})
