import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scraper import Scraper, load_notified_events, save_notified_events


class TestScraper(unittest.TestCase):
    def test_init(self):
        scraper = Scraper("http://example.com")
        self.assertEqual(scraper.url, "http://example.com")
        self.assertIsNone(scraper.driver)

    @patch("scraper.webdriver.Chrome")
    @patch("scraper.ChromeDriverManager")
    def test_check_ticket_buttons_returns_list(self, mock_cdm, mock_chrome):
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = []

        scraper = Scraper("http://example.com")
        scraper.driver = mock_driver
        buttons = scraper.check_ticket_buttons()
        self.assertIsInstance(buttons, list)

    @patch("scraper.webdriver.Chrome")
    def test_handle_ticket_availability_empty(self, mock_chrome):
        mock_driver = MagicMock()
        mock_driver.page_source = "Empty Event This event is out of tickets for now"
        mock_chrome.return_value = mock_driver

        scraper = Scraper("http://example.com")
        scraper.driver = mock_driver

        btn = MagicMock()
        result = scraper.handle_ticket_availability(btn)
        self.assertFalse(result)

    @patch("scraper.webdriver.Chrome")
    def test_handle_ticket_availability_available(self, mock_chrome):
        mock_driver = MagicMock()
        mock_driver.page_source = "<html>Some ticket info</html>"
        mock_chrome.return_value = mock_driver

        scraper = Scraper("http://example.com")
        scraper.driver = mock_driver

        btn = MagicMock()
        result = scraper.handle_ticket_availability(btn)
        self.assertTrue(result)


class TestNotifiedEventsState(unittest.TestCase):
    def setUp(self):
        self.state_file = "/tmp/test_notified_events.json"
        os.environ["NOTIFIED_STATE_FILE"] = self.state_file
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def tearDown(self):
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    @patch("scraper.NOTIFIED_STATE_FILE", "/tmp/test_notified_events.json")
    def test_save_and_load_events(self):
        events = {"event-0", "event-1"}
        save_notified_events(events)
        loaded = load_notified_events()
        self.assertEqual(loaded, events)

    @patch("scraper.NOTIFIED_STATE_FILE", "/tmp/nonexistent_test_file.json")
    def test_load_empty_when_missing(self):
        if os.path.exists("/tmp/nonexistent_test_file.json"):
            os.remove("/tmp/nonexistent_test_file.json")
        loaded = load_notified_events()
        self.assertEqual(loaded, set())


if __name__ == "__main__":
    unittest.main()