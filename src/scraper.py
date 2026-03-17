import json
import logging
import os
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

        # Wait for the page body to be present
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Extra pause for JS rendering
        time.sleep(5)
        logger.info("Page loaded: %s", self.url)
        return True

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    # ------------------------------------------------------------------
    # Ticket detection
    # ------------------------------------------------------------------
    def check_ticket_buttons(self) -> list:
        """Return a list of clickable 'view ticket' elements."""
        buttons = []
        clickable = self.driver.find_elements(By.XPATH, "//button | //a")
        for el in clickable:
            text = el.text.strip().lower()
            if "view ticket" in text:
                buttons.append(el)
        logger.info("Found %d 'view ticket' button(s)", len(buttons))
        return buttons

    def handle_ticket_availability(self, button) -> bool:
        """Click a ticket button and return True if tickets are actually available.

        After clicking, the site may show an "Empty Event" popup when no
        tickets remain.  If that popup does NOT appear, tickets are available.
        """
        button.click()
        time.sleep(3)

        page_text = self.driver.page_source
        if EMPTY_EVENT_TEXT in page_text:
            logger.info("Empty-event popup detected – no tickets available.")
            # Dismiss any modal so we can continue
            self._dismiss_modal()
            return False

        logger.info("Tickets appear to be available!")
        return True

    def _dismiss_modal(self):
        """Try to close a modal/popup if one is open."""
        try:
            close_btn = self.driver.find_element(
                By.XPATH,
                "//*[contains(@class,'close') or contains(@aria-label,'Close')]",
            )
            close_btn.click()
            time.sleep(1)
        except Exception:
            # No close button found – press Escape as fallback
            from selenium.webdriver.common.keys import Keys

            webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1)


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
        buttons = scraper.check_ticket_buttons()

        if not buttons:
            logger.info("No 'view ticket' buttons found on the page.")
            return

        for idx, btn in enumerate(buttons):
            event_id = f"event-{idx}"
            if event_id in notified:
                logger.info("Already notified for %s – skipping.", event_id)
                continue

            if scraper.handle_ticket_availability(btn):
                message = (
                    "🎟️ Tickets are available on Smith's Mammoth Tickets! "
                    "Check them out here: " + TARGET_URL
                )
                notifier.send_notification(message)
                notified.add(event_id)
                logger.info("Notification sent for %s.", event_id)
            else:
                logger.info("No tickets for %s.", event_id)
    finally:
        scraper.close()

    save_notified_events(notified)
    logger.info("Done.")


if __name__ == "__main__":
    main()