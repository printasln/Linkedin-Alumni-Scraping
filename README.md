# LinkedIn Alumni Scraper

A Python tool that collects LinkedIn profiles of Haliç University alumni and extracts their current workplace information.

Built with [Scrapling](https://github.com/D4Vinci/Scrapling) — a powerful stealth web scraping library.

---

## ⚠️ Disclaimer

This tool is intended for **personal research and educational purposes only**.  
LinkedIn's Terms of Service prohibit automated scraping. Use responsibly and at your own risk.  
Do **not** use this tool for commercial purposes or mass data collection.

---

## Features

- Collects all alumni profile links from LinkedIn search (3rd+ connections, filtered by school)
- Resumes automatically if interrupted — no duplicate work
- Extracts name, current position, company, and location from each profile
- Saves results to CSV
- Configurable delays to reduce ban risk

---

## Requirements

- Python 3.10+
- A LinkedIn account

Install dependencies:

```bash
pip install "scrapling[fetchers]"
scrapling install
```

---

## Setup

### 1. Get your LinkedIn `li_at` cookie

1. Log in to LinkedIn in your browser
2. Open DevTools → **Application** → **Cookies** → `https://www.linkedin.com`
3. Find the `li_at` row and copy its **Value**

### 2. Configure the scraper

Open `scraper.py` and paste your cookie:

```python
LI_AT_COOKIE = "paste_your_li_at_value_here"
```

To target a different university, update the `schoolFilter` ID in `BASE_SEARCH_URL`:

```python
BASE_SEARCH_URL = (
    "https://www.linkedin.com/search/results/people/"
    "?origin=FACETED_SEARCH"
    "&network=%5B%22O%22%5D"
    "&schoolFilter=%5B%221173435%22%5D"  # ← change this ID
)
```

To find a school's ID: search for it on LinkedIn, apply the school filter, and copy the ID from the URL.

---

## Usage

### Run both phases (recommended)

```bash
python scraper.py
```

### Phase 1 only — collect profile links

```bash
python scraper.py links
```

Links are saved to `profile_links.txt`. If interrupted, re-running will resume from where it left off.

To resume from a specific page, set `START_PAGE` in the config:

```python
START_PAGE = 87  # resume from page 87
```

### Phase 2 only — scrape profiles

```bash
python scraper.py profiles
```

Reads from `profile_links.txt` and saves results to `halic_alumni.csv`. Already-processed profiles are skipped automatically.

---

## Output

`halic_alumni.csv` with the following columns:

| Column | Description |
|---|---|
| `name` | Full name |
| `position` | Current job title |
| `company` | Current employer |
| `location` | City / country |
| `profile_url` | LinkedIn profile URL |

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `LI_AT_COOKIE` | — | Your LinkedIn session cookie |
| `START_PAGE` | `1` | Page to start/resume from |
| `SEARCH_DELAY` | `3` | Seconds between search pages |
| `PROFILE_DELAY` | `4` | Seconds between profile fetches |
| `EMPTY_PAGE_LIMIT` | `3` | Stop after N consecutive empty pages |

---

## Project Structure

```
linkedin-scraper/
├── scraper.py          # Main script
├── profile_links.txt   # Collected profile URLs (auto-generated)
├── halic_alumni.csv    # Final output (auto-generated)
├── requirements.txt
└── README.md
```

---

## How It Works

**Phase 1 — Link Collection**  
Iterates through LinkedIn search result pages, extracts all `/in/` profile URLs, and saves them to a text file. Skips duplicates and resumes from the last saved state if interrupted.

**Phase 2 — Profile Scraping**  
Visits each profile page and parses the Experience section to find the most recent current job (identified by "Present" in the date range). Extracts position, company, and location. Results are appended to CSV immediately after each profile so no data is lost on interruption.
