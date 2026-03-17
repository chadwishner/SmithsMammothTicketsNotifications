# Smith's Mammoth Tickets Notifications

## Overview
A Python web scraper that monitors the [Utah Mammoth Smith's ticket marketplace](https://pa.exchange/marketplace/84f01098-97cb-11f0-8949-59ab7ccaae49/storefront/84f012c8-97cb-11f0-9a80-d5b817bca54e) for ticket availability and sends email notifications when tickets are found. Runs daily via GitHub Actions.

## Features
- Scrapes the pa.exchange storefront using headless Chrome + Selenium
- Detects available events and checks each for actual ticket availability
- Sends a single HTML email listing all available events with direct ticket links
- Tracks notified events to avoid duplicate notifications
- Automated daily runs via GitHub Actions with manual trigger support

## Project Structure
```
├── src
│   ├── scraper.py        # Main scraper logic (Selenium, event detection)
│   ├── notifier.py       # Email notifications via SMTP
│   └── config.py         # Environment variable loading
├── tests
│   ├── __init__.py
│   ├── test_scraper.py   # Unit tests for the Scraper class
│   └── test_notifier.py  # Unit tests for the Notifier class
├── .github
│   └── workflows
│       └── scrape-schedule.yml  # GitHub Actions workflow (daily noon UTC)
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone and install
```bash
git clone https://github.com/yourusername/SmithsMammothTicketsNotifications.git
cd SmithsMammothTicketsNotifications
pip install -r requirements.txt
```

### 2. Configure Gmail SMTP
1. Enable 2-Step Verification on your Google account
2. Create an App Password at https://myaccount.google.com/apppasswords
3. Create a `.env` file:
   ```
   SMTP_USERNAME=you@gmail.com
   SMTP_PASSWORD=your-app-password
   NOTIFY_EMAILS=you@gmail.com,friend@gmail.com
   ```

### 3. GitHub Actions secrets
Add these secrets in your repo (Settings → Secrets → Actions):
- `SMTP_USERNAME` — your Gmail address
- `SMTP_PASSWORD` — the Gmail App Password
- `NOTIFY_EMAILS` — comma-separated recipient emails

### 4. Run locally
```bash
cd src
python scraper.py
```

### 5. Run tests
```bash
python -m pytest tests/ -v
```

## How It Works
1. Loads the storefront page with headless Chrome
2. Finds all event rows (`a.marketplace-event-list-row`) and extracts event name, date, time, venue, and ticket URL
3. Navigates to each event's ticket page to check availability
4. Sends one HTML email with all available events as clickable links
5. Saves notified event IDs to `notified_events.json` to prevent duplicates across runs