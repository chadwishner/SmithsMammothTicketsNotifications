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
    def _dismiss_toasts(self):
        """Remove any toast overlays that may block clicks."""
        self.driver.execute_script(
            "document.querySelectorAll('.app-toaster__message, .app-toaster')"
            ".forEach(el => el.remove());"
        )
        time.sleep(0.5)

    def _find_view_ticket_buttons(self):
        """Return all <button> elements whose text contains 'View Tickets'."""
        return self.driver.find_elements(
            By.XPATH,
            "//button[.//span[contains(text(),'View Tickets')]]",
        )

    def check_ticket_buttons(self) -> int:
        """Return the count of 'View Tickets' buttons on the page."""
        self._dismiss_toasts()
        buttons = self._find_view_ticket_buttons()
        logger.info("Found %d 'View Tickets' button(s)", len(buttons))
        return len(buttons)

    def handle_ticket_availability(self, button_index: int) -> bool:
        """Click the Nth 'View Tickets' button and check for availability.

        Uses a JavaScript click to bypass any overlay elements (e.g. toasts).
        After clicking, if the "Empty Event" popup appears, tickets are
        unavailable.  The popup is dismissed before returning.
        """
        self._dismiss_toasts()
        buttons = self._find_view_ticket_buttons()
        if button_index >= len(buttons):
            logger.warning("Button index %d out of range.", button_index)
            return False

        btn = buttons[button_index]
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
            btn,
        )
        time.sleep(4)

        page_text = self.driver.page_source
        if EMPTY_EVENT_TEXT in page_text:
            logger.info("Empty-event popup detected - no tickets available.")
            self._dismiss_modal()
            return False

        logger.info("Tickets appear to be available!")
        self._dismiss_modal()
        return True

    def _dismiss_modal(self):
        """Try to close any open modal/popup."""
        try:
            close_btn = self.driver.find_element(
                By.XPATH,
                "//*[contains(@class,'close') or contains(@aria-label,'Close')]",
            )
            self.driver.execute_script("arguments[0].click();", close_btn)
            time.sleep(1)
        except Exception:
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
        button_count = scraper.check_ticket_buttons()

        if button_count == 0:
            logger.info("No 'View Tickets' buttons found on the page.")
            return

        for idx in range(button_count):
            event_id = f"event-{idx}"
            if event_id in notified:
                logger.info("Already notified for %s - skipping.", event_id)
                continue

            if scraper.handle_ticket_availability(idx):
                message = (
                    "Tickets are available on Smith's Mammoth Tickets! "
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