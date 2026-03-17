import os
from dotenv import load_dotenv

load_dotenv()

SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
NOTIFY_EMAILS = [
    e.strip() for e in os.getenv("NOTIFY_EMAILS", "").split(",") if e.strip()
]

TARGET_URL = (
    "https://pa.exchange/marketplace/84f01098-97cb-11f0-8949-59ab7ccaae49"
    "/storefront/84f012c8-97cb-11f0-9a80-d5b817bca54e"
)

# Path to the file that tracks which events have already been notified
NOTIFIED_STATE_FILE = os.getenv(
    "NOTIFIED_STATE_FILE",
    os.path.join(os.path.dirname(__file__), "..", "notified_events.json"),
)