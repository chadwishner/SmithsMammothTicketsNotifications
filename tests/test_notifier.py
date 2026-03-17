import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from notifier import Notifier


class TestNotifier(unittest.TestCase):
    @patch("notifier.smtplib.SMTP")
    def test_send_notification(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        n = Notifier(
            smtp_username="user@gmail.com",
            smtp_password="app-password",
            recipients=["a@example.com", "b@example.com"],
        )
        result = n.send_notification("Tickets available!")

        self.assertTrue(result)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@gmail.com", "app-password")
        self.assertEqual(mock_server.send_message.call_count, 2)

    @patch("notifier.smtplib.SMTP")
    def test_send_notification_handles_failure(self, mock_smtp_cls):
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_server.send_message.side_effect = Exception("SMTP error")

        n = Notifier(
            smtp_username="user@gmail.com",
            smtp_password="app-password",
            recipients=["a@example.com"],
        )
        result = n.send_notification("Tickets available!")
        self.assertFalse(result)

    def test_send_notification_no_recipients(self):
        n = Notifier(
            smtp_username="user@gmail.com",
            smtp_password="app-password",
            recipients=[],
        )
        result = n.send_notification("Tickets available!")
        self.assertFalse(result)

    def test_send_notification_no_credentials(self):
        n = Notifier(
            smtp_username="",
            smtp_password="",
            recipients=["a@example.com"],
        )
        result = n.send_notification("Tickets available!")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()