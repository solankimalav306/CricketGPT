import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import re

BASE_URL = "https://www.cricbuzz.com"
URL = f"{BASE_URL}/cricket-schedule/series/all"

headers = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(headers)

try:
    response = session.get(URL, timeout=30)
    print(f"Status: {response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"FAILED -> {e}")
    exit()


soup = BeautifulSoup(response.text, "html.parser")

# --------------------------------------------------
# Find the schedule table using "Month"
# --------------------------------------------------

month = soup.find(
    string=re.compile(r"^Month$", re.I)
)

if not month:
    print("Schedule table not found")
    exit()


# Move up to the table container
container = month

for _ in range(3):
    container = container.parent


# --------------------------------------------------
# Extract series
# --------------------------------------------------

future_series = []
seen_urls = set()

for a in container.find_all("a", href=True):

    href = a["href"]
    text = a.get_text(" ", strip=True)

    if not text:
        continue

    if "/cricket-series/" not in href:
        continue

    # These are the actual schedule rows
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

    # Clean text
    text = " ".join(text.split())

    future_series.append({
        "series_id": series_id,
        "name": text,
        "url": url
    })


# --------------------------------------------------
# Output
# --------------------------------------------------

print("\n" + "=" * 100)
print(f"Total future/current series: {len(future_series)}")

print(json.dumps(
    future_series,
    indent=2,
    ensure_ascii=False
))