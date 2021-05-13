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


@recipe(max_retries=None, slack_alert=True)
def main(context: Recipe):
    context.logger.info(f"Starting handler for job {context.job_name}")

    extract()
    transform()
    load()

    context.logger.info(f"Finished {context.job_name}")
    return


if __name__ == "__main__":
    main()
