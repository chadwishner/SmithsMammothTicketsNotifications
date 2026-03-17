import json
import logging
import os
import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config import (
    NOTIFIED_STATE_FILE,
    SUBSCRIBER_PHONE_NUMBERS,
    TARGET_URL,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
)
from notifier import Notifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

EMPTY_EVENT_TEXT = "This event is out of tickets for now"

EVENT_UUID_RE = re.compile(r"/event/([^/]+)/tickets")


class Scraper:
    def __init__(self, url: str):
        self.url = url
        self.driver = None

    # ------------------------------------------------------------------
    # Browser lifecycle
    # ------------------------------------------------------------------
    def load_website(self) -> bool:
        """Launch a headless Chrome browser and navigate to the target URL."""
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.get(self.url)

        # Wait for the Vue app to render storefront content
        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".marketplace-storefront-branding")
                )
            )
        except Exception:
            logger.warning(
                "Storefront branding not found; page may not have fully rendered."
            )

        # Extra pause for event list to populate
        time.sleep(3)
        logger.info("Page loaded: %s", self.url)
        return True

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    # ------------------------------------------------------------------
    # Event detection
    # ------------------------------------------------------------------
    def _dismiss_toasts(self):
        """Remove any toast overlays that may block interaction."""
        self.driver.execute_script(
            "document.querySelectorAll('.app-toaster__message, .app-toaster')"
            ".forEach(el => el.remove());"
        )
        time.sleep(0.5)

    def get_events(self) -> list:
        """Find all event rows and return dicts with url, name, and event_id."""
        self._dismiss_toasts()
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "a.marketplace-event-list-row"
        )
        events = []
        for row in rows:
            href = row.get_attribute("href") or ""
            try:
                name = row.find_element(By.CSS_SELECTOR, "h5").text.strip()
            except Exception:
                name = "Unknown Event"
            match = EVENT_UUID_RE.search(href)
            event_id = match.group(1) if match else href
            events.append({"url": href, "name": name, "event_id": event_id})
        logger.info("Found %d event(s) on the page.", len(events))
        return events

    def check_event_availability(self, event_url: str) -> bool:
        """Navigate to an event ticket page and check if tickets exist."""
        self.driver.get(event_url)
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception:
            pass
        time.sleep(5)

        if EMPTY_EVENT_TEXT in self.driver.page_source:
            logger.info("No tickets available at %s", event_url)
            return False
        logger.info("Tickets appear available at %s", event_url)
        return True


# ------------------------------------------------------------------
# Notification state persistence
# ------------------------------------------------------------------
def load_notified_events() -> set:
    if os.path.exists(NOTIFIED_STATE_FILE):
        with open(NOTIFIED_STATE_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_notified_events(events: set):
    with open(NOTIFIED_STATE_FILE, "w") as f:
        json.dump(sorted(events), f)


# ------------------------------------------------------------------
# Main entry-point
# ------------------------------------------------------------------
def main():
    notifier = Notifier(
        account_sid=TWILIO_ACCOUNT_SID,
        auth_token=TWILIO_AUTH_TOKEN,
        from_number=TWILIO_FROM_NUMBER,
        subscribers=SUBSCRIBER_PHONE_NUMBERS,
    )
    notified = load_notified_events()

    scraper = Scraper(TARGET_URL)
    try:
        scraper.load_website()
        events = scraper.get_events()

        if not events:
            logger.info("No events found on the page.")
            return

        for event in events:
            if event["event_id"] in notified:
                logger.info("Already notified for %s - skipping.", event["name"])
                continue

            if scraper.check_event_availability(event["url"]):
                message = (
                    f"Tickets are available for {event['name']}! "
                    f"Check them out here: {event['url']}"
                )
                notifier.send_notification(message)
                notified.add(event["event_id"])
                logger.info("Notification sent for %s.", event["name"])
            else:
                logger.info("No tickets for %s.", event["name"])
    finally:
        scraper.close()

    save_notified_events(notified)
    logger.info("Done.")


if __name__ == "__main__":
    main()