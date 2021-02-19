import logging
import os

from omelette import init_logging
from omelette import Settings

from omelette.eggs import Sftp, Snowflake, Slack, Files, S3, SftpS3Interface

init_logging(is_lambda=True)
logger = logging.getLogger(__name__)

settings = Settings(config_filepath="settings.toml")  # change to point to your settings.toml file as needed


def main():
    """Replace with your own recipe steps. Recipes are plain Python, so feel free to use extra functions, classes, etc.
    as long as you correctly call the entrypoint below in `if __name__ == "__main__"`"""
    logger.info(f"Starting recipe: {{recipe_name}}")
    pass


if __name__ == "__main__":
    slack = Slack(**settings.slack)

    try:
        main()
    except Exception as e:
        slack.send_slack_alert(f"Error running {{recipe_name}}: {e}")
