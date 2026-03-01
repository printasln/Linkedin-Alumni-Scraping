"""
LinkedIn Alumni Scraper
Collects profile links and current workplace info from LinkedIn alumni search.
"""

from scrapling.fetchers import StealthyFetcher
import csv
import time
import os

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
LI_AT_COOKIE = "YOUR_LI_AT_COOKIE_HERE"  # Paste your LinkedIn li_at cookie

# Search URL: 3rd+ connections, filtered by Haliç University (school ID: 1173435)
BASE_SEARCH_URL = (
    "https://www.linkedin.com/search/results/people/"
    "?origin=FACETED_SEARCH"
    "&network=%5B%22O%22%5D"
    "&schoolFilter=%5B%221173435%22%5D"
)

LINKS_FILE = "profile_links.txt"
OUTPUT_FILE = "halic_alumni.csv"

SEARCH_DELAY = 3   # seconds between search pages
PROFILE_DELAY = 4  # seconds between profile fetches
EMPTY_PAGE_LIMIT = 3
START_PAGE = 1     # change to resume from a specific page

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
cookies = [
    {
        "name": "li_at",
        "value": LI_AT_COOKIE,
        "domain": ".linkedin.com",
        "path": "/",
    }
]


def fetch_page(url: str):
    return StealthyFetcher.fetch(
        url,
        headless=False,
        network_idle=True,
        cookies=cookies,
    )


def extract_profile_links(page, existing: list) -> list:
    links = []
    for a in page.css("a"):
        href = a.attrib.get("href", "")
        if "/in/" in href and "linkedin.com" in href:
            clean = href.split("?")[0]
            if clean not in links and clean not in existing:
                links.append(clean)
    return links


def get_current_job(profile) -> tuple[str, str]:
    """
    Parses the Experience section to extract the most recent current job.
    Returns (position, company). Falls back to 'N/A' if not found.
    """
    spans = profile.css("span")
    texts = [s.text.strip() for s in spans]

    # Find the start of the Experience section
    exp_index = None
    for i, t in enumerate(texts):
        if t == "Experience":
            exp_index = i
            break

    if exp_index is None:
        return "N/A", "N/A"

    window = texts[exp_index: exp_index + 60]

    # Look for "Present" → position is 5 before, company is 3 before
    for i, t in enumerate(window):
        if "Present" in t:
            company = window[i - 3] if i >= 3 else "N/A"
            position = window[i - 5] if i >= 5 else "N/A"
            return position, company

    # Fallback: first two meaningful spans after Experience header
    meaningful = [
        t for t in window[1:]
        if t and len(t) > 2 and t not in ("Experience", "Image")
    ]
    if len(meaningful) >= 2:
        return meaningful[0], meaningful[1]

    return "N/A", "N/A"


# ─────────────────────────────────────────
# PHASE 1 — Collect profile links
# ─────────────────────────────────────────
def collect_links(start_page: int = START_PAGE):
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, "r") as f:
            all_links = [line.strip() for line in f if line.strip()]
        print(f"↩️  Resuming: {len(all_links)} links already saved, starting from page {start_page}\n")
    else:
        all_links = []
        print(f"🔍 Starting fresh link collection from page {start_page}\n")

    page_num = start_page
    empty_count = 0

    while True:
        url = BASE_SEARCH_URL + f"&page={page_num}"
        print(f"📄 Page {page_num} — {url}")

        try:
            page = fetch_page(url)
        except Exception as e:
            print(f"   ❌ Error fetching page: {e}")
            time.sleep(10)
            continue

        new_links = extract_profile_links(page, all_links)
        print(f"   → {len(new_links)} new profiles | Total: {len(all_links) + len(new_links)}")

        if not new_links:
            empty_count += 1
            print(f"   ⚠️  Empty page ({empty_count}/{EMPTY_PAGE_LIMIT}), waiting 10s...")
            if empty_count >= EMPTY_PAGE_LIMIT:
                print("   ⛔ 3 consecutive empty pages. Stopping.")
                break
            time.sleep(10)
        else:
            empty_count = 0
            all_links.extend(new_links)
            page_num += 1

            with open(LINKS_FILE, "w") as f:
                f.write("\n".join(all_links))

            time.sleep(SEARCH_DELAY)

    print(f"\n✅ Phase 1 complete — {len(all_links)} profile links saved to '{LINKS_FILE}'")
    return all_links


# ─────────────────────────────────────────
# PHASE 2 — Scrape each profile
# ─────────────────────────────────────────
def scrape_profiles():
    if not os.path.exists(LINKS_FILE):
        print("❌ No links file found. Run Phase 1 first.")
        return

    with open(LINKS_FILE, "r") as f:
        all_links = [line.strip() for line in f if line.strip()]

    print(f"📂 Loaded {len(all_links)} links from '{LINKS_FILE}'")

    # Resume support: skip already processed profiles
    done_urls = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                done_urls.add(row["profile_url"])
        print(f"   ↩️  {len(done_urls)} profiles already processed, resuming...\n")

    remaining = [l for l in all_links if l not in done_urls]
    print(f"🔄 Profiles to process: {len(remaining)}\n")

    file_exists = os.path.exists(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["name", "position", "company", "location", "profile_url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for i, url in enumerate(remaining):
            print(f"[{i + 1}/{len(remaining)}] {url}")
            try:
                profile = fetch_page(url)

                # Name
                name_el = profile.find("h1")
                name = name_el.text.strip() if name_el else "N/A"

                # Location
                location = "N/A"
                for span in profile.css("span"):
                    t = span.text.strip()
                    if ("Türkiye" in t or "Turkey" in t or "İstanbul" in t) and len(t) < 80:
                        location = t
                        break

                # Current job
                position, company = get_current_job(profile)

                row = {
                    "name": name,
                    "position": position,
                    "company": company,
                    "location": location,
                    "profile_url": url,
                }
                writer.writerow(row)
                f.flush()

                print(f"   ✅ {name} | {position} | {company} | {location}")
                time.sleep(PROFILE_DELAY)

            except Exception as e:
                print(f"   ❌ Error: {e}")
                writer.writerow({
                    "name": "ERROR", "position": "N/A",
                    "company": str(e), "location": "N/A",
                    "profile_url": url,
                })
                f.flush()
                time.sleep(6)

    print(f"\n✅ Phase 2 complete — results saved to '{OUTPUT_FILE}'")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "profiles":
        # python scraper.py profiles
        scrape_profiles()
    elif len(sys.argv) > 1 and sys.argv[1] == "links":
        # python scraper.py links
        collect_links()
    else:
        # Default: run both phases sequentially
        collect_links()
        scrape_profiles()
