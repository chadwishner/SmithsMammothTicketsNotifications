import os
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
SUBSCRIBER_PHONE_NUMBERS = (
    [n.strip() for n in os.getenv("SUBSCRIBER_NUMBERS", "").split(",") if n.strip()]
)

TARGET_URL = (
    "https://pa.exchange/marketplace/84f01098-97cb-11f0-8949-59ab7ccaae49"
    "/storefront/84f012c8-97cb-11f0-9a80-d5b817bca54e"
)

# Path to the file that tracks which events have already been notified
NOTIFIED_STATE_FILE = os.getenv(
    "NOTIFIED_STATE_FILE",
    os.path.join(os.path.dirname(__file__), "..", "notified_events.json"),
)