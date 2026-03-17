import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestNotifier(unittest.TestCase):
    @patch("notifier.Client")
    def test_send_notification(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        from notifier import Notifier

        n = Notifier(
            account_sid="sid",
            auth_token="token",
            from_number="+10000000000",
            subscribers=["+11111111111", "+12222222222"],
        )
        n.send_notification("Tickets available!")

        self.assertEqual(mock_client.messages.create.call_count, 2)
        mock_client.messages.create.assert_any_call(
            body="Tickets available!",
            from_="+10000000000",
            to="+11111111111",
        )
        mock_client.messages.create.assert_any_call(
            body="Tickets available!",
            from_="+10000000000",
            to="+12222222222",
        )

    @patch("notifier.Client")
    def test_send_notification_handles_failure(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API error")

        from notifier import Notifier

        n = Notifier(
            account_sid="sid",
            auth_token="token",
            from_number="+10000000000",
            subscribers=["+11111111111"],
        )
        # Should not raise
        n.send_notification("Tickets available!")


if __name__ == "__main__":
    unittest.main()