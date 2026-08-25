import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import re


BASE_URL = "https://www.cricbuzz.com"
CURRENT_YEAR = datetime.now().year

headers = {
    "User-Agent": "Mozilla/5.0"
}


def get_past_series():

    session = requests.Session()
    session.headers.update(headers)

    all_series = []
    seen_urls = set()

    # --------------------------------------------------
    # Fetch last 5 years
    # --------------------------------------------------

    for year in range(
        CURRENT_YEAR,
        CURRENT_YEAR - 5,
        -1
    ):

        URL = (
            f"{BASE_URL}/"
            f"cricket-scorecard-archives/"
            f"{year}"
        )

        try:

            response = session.get(
                URL,
                timeout=30
            )

            print(
                f"[Past Tour Fetcher] "
                f"{year}: {response.status_code}"
            )

        except requests.exceptions.RequestException as e:

            print(
                f"[Past Tour Fetcher] "
                f"{year}: FAILED -> {e}"
            )

            continue


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        year_count = 0


        # --------------------------------------------------
        # Extract series
        # --------------------------------------------------

        for a in soup.find_all(
            "a",
            href=True
        ):

            href = a["href"]

            name = a.get_text(
                " ",
                strip=True
            )


            if not name:
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


            # --------------------------------------------------
            # Deduplicate globally
            # --------------------------------------------------

            if url in seen_urls:
                continue

            seen_urls.add(url)


            # --------------------------------------------------
            # Extract series ID
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
                name.split()
            )


            all_series.append({

                "seriesId": series_id,

                "name": name,

                "url": url

            })


            year_count += 1


        print(
            f"[Past Tour Fetcher] "
            f"{year}: {year_count} archive series"
        )


    return all_series


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    series = get_past_series()

    print(
        "\n" + "=" * 100
    )

    print(
        f"Total past series: "
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