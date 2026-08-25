import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

BASE_URL = "https://www.cricbuzz.com"
URL = f"{BASE_URL}/cricket-schedule/series/all"

headers = {
    "User-Agent": "Mozilla/5.0"
}


def get_future_series():

    session = requests.Session()
    session.headers.update(headers)

    try:
        response = session.get(
            URL,
            timeout=30
        )

        print(
            f"[Future Tour Fetcher] Status: "
            f"{response.status_code}"
        )

    except requests.exceptions.RequestException as e:

        print(
            f"[Future Tour Fetcher] FAILED -> {e}"
        )

        return []


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    # --------------------------------------------------
    # Find schedule table
    # --------------------------------------------------

    month = soup.find(
        string=re.compile(
            r"^Month$",
            re.I
        )
    )

    if not month:

        print(
            "[Future Tour Fetcher] "
            "Schedule table not found"
        )

        return []


    container = month

    for _ in range(3):

        container = container.parent


    # --------------------------------------------------
    # Extract series
    # --------------------------------------------------

    future_series = []
    seen_urls = set()


    for a in container.find_all(
        "a",
        href=True
    ):

        href = a["href"]

        text = a.get_text(
            " ",
            strip=True
        )


        if not text:
            continue


        if "/cricket-series/" not in href:
            continue


        if not href.rstrip(
            "/"
        ).endswith("/matches"):

            continue


        url = urljoin(
            BASE_URL,
            href
        )


        if url in seen_urls:
            continue

        seen_urls.add(url)


        # --------------------------------------------------
        # Series ID
        # --------------------------------------------------

        match = re.search(
            r"/cricket-series/(\d+)/",
            url
        )

        if not match:
            continue


        series_id = int(
            match.group(1)
        )


        # --------------------------------------------------
        # Clean name
        # --------------------------------------------------

        name = " ".join(
            text.split()
        )


        future_series.append({

            "seriesId": series_id,

            "name": name,

            "url": url

        })


    return future_series


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    series = get_future_series()

    print(
        "\n" + "=" * 100
    )

    print(
        f"Total future/current series: "
        f"{len(series)}"
    )

    print(
        "=" * 100
    )

    for item in series:

        print(
            f"{item['seriesId']} | "
            f"{item['name']}"
        )

        print(
            item["url"]
        )