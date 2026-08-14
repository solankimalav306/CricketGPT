import requests
from bs4 import BeautifulSoup


URL = (
    "https://www.cricbuzz.com/cricket-series/"
    "9629/west-indies-tour-of-india-2025/matches"
)

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(
    URL,
    headers=headers,
    timeout=30
)

print("Status:", response.status_code)
print("HTML length:", len(response.text))

soup = BeautifulSoup(
    response.text,
    "html.parser"
)


# ==================================================
# EXACT NEXT.JS DATA BLOCK
# ==================================================

target = (
    'self.__next_f.push([1,"27:[\\"$\\",\\"div\\",null,'
    '{\\"className\\":\\"flex w-full\\"'
)


scripts = soup.find_all("script")

found_scripts = []


for i, script in enumerate(scripts):

    text = script.string

    if not text:
        continue

    if target in text:

        found_scripts.append({
            "index": i,
            "text": text
        })


# ==================================================
# OUTPUT
# ==================================================

print("\n" + "=" * 100)
print("TOTAL MATCHING SCRIPTS:", len(found_scripts))
print("=" * 100)


for item in found_scripts:

    print("\n" + "=" * 100)
    print("SCRIPT INDEX:", item["index"])
    print("SCRIPT LENGTH:", len(item["text"]))
    print("=" * 100)

    print(item["text"])