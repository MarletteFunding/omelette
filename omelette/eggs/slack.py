import logging
import os
from typing import Dict, Any, List, Optional

from slack import WebClient
from slack.errors import SlackApiError

logger = logging.getLogger(__name__)


class Slack:
    """Wrapper around Slack WebClient. Adds retry logic to posting messages, and a simple entrypoint for sending alerts."""

    def __init__(self, api_token: str, channel_id: str, app_name: str, enabled: bool = False, **kwargs):
        self.channel_id = channel_id
        self.app_name = app_name
        self.client = WebClient(token=api_token)
        self.environment = os.getenv("PROJECT_ENV", "local")
        self.enabled = enabled

    def send_slack_alert(self, message: str, app_name: str = None, job_owner_id: str = None):
        if not self.enabled:
            logger.info("Trying to send message to Slack but it is not enabled.")
            return

        app_name = app_name or self.app_name

        attachment = {
            "pretext": f"*Alert from `{self.environment.upper()} {app_name}` Job*",
            "mrkdwn_in": ["text", "pretext"],
            "color": "danger",
            "text": message
        }

        # Send to default channel
        channel = self.channel_id
        self._slack_post_message(channel, [attachment])

        # Also send to job owner as a DM if present
        if job_owner_id:
            self._slack_post_message(job_owner_id, [attachment])

    def _slack_post_message(self, channel: str, attachments: List[Dict[str, Any]], retry_count: int = 3):
        retries = retry_count

        while retries > 0:
            try:
                self.client.chat_postMessage(channel=channel, attachments=attachments)
                break
            except SlackApiError as e:
                retries -= 1
                logger.exception("Error sending slack alert.")

                if retries == 0:
                    raise e
