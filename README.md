
# Social Media Content Aggregator

A Python-based asynchronous service for collecting, deduplicating, and aggregating posts from multiple social media platforms into Google Sheets.

The project fetches recent posts from VK, Telegram, and Odnoklassniki, detects similar content across platforms, and stores unified results in a structured spreadsheet.

---

## 📌 About the Project

This tool was designed to automate daily monitoring of social media channels.  
It collects posts published within the last 24 hours, compares them using fuzzy text matching, and merges duplicates into a single unified record.

The final dataset is exported to Google Sheets with automatic formatting for convenient review and analysis.

Key focuses of the project:
- asynchronous data collection,
- working with multiple external APIs,
- text similarity detection,
- structured data export.

---

## ✨ Features

- Asynchronous data collection using `asyncio` and `aiohttp`
- VK posts parsing via official API
- Telegram channel parsing via Telethon
- Odnoklassniki page scraping via HTML parsing
- Fuzzy text matching to detect duplicate posts
- Automatic aggregation of cross-platform links
- Export to Google Sheets with formatting
- Daily separation of data into date-based worksheets

---

## 🛠 Technologies

- **Python 3**
- **asyncio / aiohttp**
- **Telethon (Telegram API)**
- **VK API**
- **BeautifulSoup**
- **Google Sheets API (gspread)**
- **fuzzywuzzy**
- **SSL / certifi**


---

## 🔄 Workflow

1. Fetch posts from VK, Telegram, and Odnoklassniki
2. Filter posts from the last 24 hours
3. Remove advertisements and empty messages
4. Compare posts using fuzzy text similarity
5. Merge duplicate posts across platforms
6. Export results to Google Sheets
7. Apply automatic formatting (wrapping, column widths)

---

## 🧪 Duplicate Detection

Text similarity is calculated using fuzzy string matching.  
If similarity exceeds a defined threshold, posts are considered duplicates and merged into a single entry with multiple platform links.

---

## 📊 Google Sheets Output

- A new worksheet is created for each day
- Columns include:
  - Post text
  - Telegram link
  - VK link
  - Odnoklassniki link
- Text wrapping and column widths are applied automatically

---

## 🚀 How to Run

```bash
pip install -r requirements.txt
python main.py
```

Before running, make sure to:
- provide valid API credentials (VK, Telegram),
- configure Google Service Account credentials,
- update channel/group URLs if needed.

---

## 🎯 Project Goals

- Practice asynchronous Python programming
- Work with multiple external APIs
- Implement real-world data aggregation logic
- Automate routine content monitoring tasks
- Build a production-oriented data pipeline

---

## 📎 Notes

This project is intended for demonstrational and practical use cases such as content monitoring, analytics preparation, or media tracking.
