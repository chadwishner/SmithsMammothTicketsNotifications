# Ticket Scraper

## Overview
Ticket Scraper is a Python-based web scraper designed to monitor ticket availability on specified websites. It checks for "view ticket" buttons and sends notifications via SMS using Twilio when tickets become available. The scraper is scheduled to run daily using GitHub Actions.

## Features
- Loads specified websites to check for ticket availability.
- Identifies "view ticket" buttons on the page.
- Sends SMS notifications to subscribers when tickets are available.
- Configurable via environment variables for easy setup.

## Project Structure
```
ticket-scraper
├── src
│   ├── scraper.py        # Main logic for the web scraper
│   ├── notifier.py       # Handles SMS notifications
│   └── config.py         # Configuration settings and environment variables
├── tests
│   ├── __init__.py       # Marks the tests directory as a package
│   ├── test_scraper.py   # Unit tests for the Scraper class
│   └── test_notifier.py  # Unit tests for the Notifier class
├── .github
│   └── workflows
│       └── scrape-schedule.yml  # GitHub Actions workflow for daily scraping
├── requirements.txt      # Project dependencies
├── .env.example          # Example environment variables
├── .gitignore            # Files and directories to ignore by Git
└── README.md             # Project documentation
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ticket-scraper.git
   cd ticket-scraper
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env` and fill in your Twilio credentials and subscriber phone numbers.

4. Run the scraper:
   ```
   python src/scraper.py
   ```

## Usage
- The scraper will check the specified website for ticket availability and send notifications to the configured phone numbers when tickets are available.
- The scraping process is automated to run daily through GitHub Actions.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.