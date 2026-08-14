import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import json
import re

BASE_URL = "https://www.cricbuzz.com"
CURRENT_YEAR = datetime.now().year

headers = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(headers)

series_by_year = {}

for year in range(CURRENT_YEAR, CURRENT_YEAR - 5, -1):

    URL = f"{BASE_URL}/cricket-scorecard-archives/{year}"

    try:
        response = session.get(URL, timeout=30)
        print(f"{year}: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"{year}: FAILED -> {e}")
        series_by_year[year] = []
        continue

    soup = BeautifulSoup(response.text, "html.parser")

    year_series = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):

        href = a["href"]
        name = a.get_text(" ", strip=True)

        if not name:
            continue

        # Archive series links
        if "/cricket-series/" not in href:
            continue

        if not href.rstrip("/").endswith("/matches"):
            continue

        url = urljoin(BASE_URL, href)

        if url in seen_urls:
            continue

        seen_urls.add(url)

        # ----------------------------------------------
        # Extract series ID
        # ----------------------------------------------

        match = re.search(
            r"/cricket-series/(\d+)/",
            url
        )

        if not match:
            continue

        series_id = match.group(1)

        year_series.append({
            "series_id": series_id,
            "name": name,
            "url": url
        })

    series_by_year[year] = year_series

    print(f"{year}: {len(year_series)} archive series")


print("\n" + "=" * 100)

print(json.dumps(
    series_by_year,
    indent=2,
    ensure_ascii=False
))