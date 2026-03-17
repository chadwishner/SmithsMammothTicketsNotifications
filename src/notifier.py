import logging

from twilio.rest import Client

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, account_sid: str, auth_token: str, from_number: str, subscribers: list[str]):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.subscribers = subscribers

    def send_notification(self, message: str):
        """Send *message* via SMS to every subscriber."""
        for number in self.subscribers:
            try:
                self.client.messages.create(
                    body=message,
                    from_=self.from_number,
                    to=number,
                )
                logger.info("SMS sent to %s", number)
            except Exception:
                logger.exception("Failed to send SMS to %s", number)