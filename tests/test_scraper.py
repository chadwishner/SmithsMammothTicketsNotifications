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
    def test_get_events_empty(self, mock_cdm, mock_chrome):
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.find_elements.return_value = []

        scraper = Scraper("http://example.com")
        scraper.driver = mock_driver
        events = scraper.get_events()
        self.assertIsInstance(events, list)
        self.assertEqual(len(events), 0)

    @patch("scraper.webdriver.Chrome")
    @patch("scraper.ChromeDriverManager")
    def test_get_events_extracts_info(self, mock_cdm, mock_chrome):
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        mock_row = MagicMock()
        mock_row.get_attribute.return_value = (
            "https://pa.exchange/marketplace/abc/storefront/def/event/12345/tickets"
        )
        mock_h5 = MagicMock()
        mock_h5.text = "Edmonton Oilers at Utah Mammoth"
        mock_row.find_element.return_value = mock_h5
        mock_driver.find_elements.return_value = [mock_row]

        scraper = Scraper("http://example.com")
        scraper.driver = mock_driver
        events = scraper.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["name"], "Edmonton Oilers at Utah Mammoth")
        self.assertEqual(events[0]["event_id"], "12345")
        self.assertIn("/event/12345/tickets", events[0]["url"])

    @patch("scraper.webdriver.Chrome")
    def test_check_event_availability_empty(self, mock_chrome):
        mock_driver = MagicMock()
        mock_driver.page_source = "This event is out of tickets for now"
        mock_chrome.return_value = mock_driver

        scraper = Scraper("http://example.com")
        scraper.driver = mock_driver

        result = scraper.check_event_availability("http://example.com/event/123/tickets")
        self.assertFalse(result)

    @patch("scraper.webdriver.Chrome")
    def test_check_event_availability_available(self, mock_chrome):
        mock_driver = MagicMock()
        mock_driver.page_source = "<html>Some ticket info</html>"
        mock_chrome.return_value = mock_driver

        scraper = Scraper("http://example.com")
        scraper.driver = mock_driver

        result = scraper.check_event_availability("http://example.com/event/123/tickets")
        self.assertTrue(result)

    @patch("scraper.webdriver.Chrome")
    @patch("scraper.ChromeDriverManager")
    def test_get_events_missing_h5_falls_back(self, mock_cdm, mock_chrome):
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        mock_row = MagicMock()
        mock_row.get_attribute.return_value = "http://example.com/event/abc/tickets"
        mock_row.find_element.side_effect = Exception("no h5")
        mock_driver.find_elements.return_value = [mock_row]

        scraper = Scraper("http://example.com")
        scraper.driver = mock_driver
        events = scraper.get_events()
        self.assertEqual(events[0]["name"], "Unknown Event")

    @patch("scraper.webdriver.Chrome")
    @patch("scraper.ChromeDriverManager")
    def test_get_events_no_uuid_in_url(self, mock_cdm, mock_chrome):
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        mock_row = MagicMock()
        mock_row.get_attribute.return_value = "http://example.com/some-page"
        mock_h5 = MagicMock()
        mock_h5.text = "Test Event"
        mock_row.find_element.return_value = mock_h5
        mock_driver.find_elements.return_value = [mock_row]

        scraper = Scraper("http://example.com")
        scraper.driver = mock_driver
        events = scraper.get_events()
        self.assertEqual(events[0]["event_id"], "http://example.com/some-page")


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