import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(
        self,
        smtp_username: str,
        smtp_password: str,
        recipients: list[str],
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
    ):
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.recipients = recipients

    def send_notification(self, html_body: str, subject: str = "Mammoth Tickets Available!") -> bool:
        """Send an HTML email to every recipient. Returns True if at least one sent."""
        if not self.recipients:
            logger.warning("No recipient emails configured – skipping notification.")
            return False
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not set – skipping notification.")
            return False

        sent = False
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                for recipient in self.recipients:
                    try:
                        msg = EmailMessage()
                        msg["Subject"] = subject
                        msg["From"] = self.smtp_username
                        msg["To"] = recipient
                        msg.set_content(html_body, subtype="html")
                        server.send_message(msg)
                        logger.info("Email sent to %s", recipient)
                        sent = True
                    except Exception:
                        logger.exception("Failed to send email to %s", recipient)
        except Exception:
            logger.exception("Failed to connect to SMTP server %s:%s", self.smtp_host, self.smtp_port)
        return sent