import requests
from bs4 import BeautifulSoup
import json


URL = (
    "https://www.cricbuzz.com/cricket-series/"
    # "9629/west-indies-tour-of-india-2025/matches"
    "12687/india-tour-of-sri-lanka-2026/matches"
)

headers = {
    "User-Agent": "Mozilla/5.0"
}


# ==================================================
# FETCH
# ==================================================

response = requests.get(
    URL,
    headers=headers,
    timeout=30
)

print("Status:", response.status_code)
print("HTML length:", len(response.text))


# ==================================================
# PARSE
# ==================================================

soup = BeautifulSoup(
    response.text,
    "html.parser"
)


# ==================================================
# EXACT TARGET
# ==================================================

target = (
    'self.__next_f.push([1,"27:[\\"$\\",\\"div\\",null,'
    '{\\"className\\":\\"flex w-full\\"'
)


# ==================================================
# FIND SCRIPT
# ==================================================

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


print("\n" + "=" * 100)
print("TOTAL MATCHING SCRIPTS:", len(found_scripts))
print("=" * 100)


# ==================================================
# PARSE MATCH DATA
# ==================================================

for number, item in enumerate(found_scripts, start=1):

    script = item["text"]

    print("\n" + "=" * 100)
    print(f"MATCHING SCRIPT #{number}")
    print("SCRIPT INDEX:", item["index"])
    print("=" * 100)


    # ------------------------------------------------
    # The script is:
    #
    # self.__next_f.push([1,"....."])
    #
    # Extract the second argument of push()
    # ------------------------------------------------

    prefix = 'self.__next_f.push([1,'

    start = script.find(prefix)

    if start == -1:
        print("Push prefix not found")
        continue


    # Start immediately after:
    #
    # self.__next_f.push([1,
    #

    string_start = start + len(prefix)


    # The second argument is a JSON string.
    # Use json.JSONDecoder to parse it properly.

    decoder = json.JSONDecoder()

    try:

        payload, end = decoder.raw_decode(
            script[string_start:]
        )

    except Exception as e:

        print("Could not decode Next.js payload:")
        print(e)
        continue


    print("Payload decoded successfully")
    print("Payload length:", len(payload))


    # ------------------------------------------------
    # Find matchesData
    # ------------------------------------------------

    marker = '"matchesData":'

    data_start = payload.find(marker)

    if data_start == -1:

        print("matchesData not found in decoded payload")
        continue


    print("matchesData found at:", data_start)


    # ------------------------------------------------
    # Find matchDetails
    # ------------------------------------------------

    marker = '"matchDetails":'

    details_start = payload.find(
        marker,
        data_start
    )

    if details_start == -1:

        print("matchDetails not found")
        continue


    print(
        "matchDetails found at:",
        details_start
    )


    # ------------------------------------------------
    # Locate the array
    #
    # "matchDetails":[
    # ------------------------------------------------

    array_start = payload.find(
        "[",
        details_start
    )

    if array_start == -1:

        print("matchDetails array not found")
        continue


    # ------------------------------------------------
    # Extract balanced JSON array
    # ------------------------------------------------

    depth = 0
    in_string = False
    escaped = False

    array_end = None


    for i in range(
        array_start,
        len(payload)
    ):

        char = payload[i]


        if escaped:

            escaped = False
            continue


        if char == "\\":

            escaped = True
            continue


        if char == '"':

            in_string = not in_string
            continue


        if in_string:
            continue


        if char == "[":

            depth += 1


        elif char == "]":

            depth -= 1

            if depth == 0:

                array_end = i
                break


    if array_end is None:

        print("Could not find end of matchDetails")
        continue


    raw_match_details = payload[
        array_start:array_end + 1
    ]


    # ------------------------------------------------
    # Parse JSON
    # ------------------------------------------------

    try:

        match_details = json.loads(
            raw_match_details
        )

    except Exception as e:

        print("Failed to parse matchDetails JSON:")
        print(e)

        print("\nRAW DATA:")
        print(raw_match_details)

        continue


    # ==================================================
    # OUTPUT
    # ==================================================

    print("\n" + "=" * 100)
    print("PARSED MATCH DETAILS")
    print("=" * 100)

    print(
        json.dumps(
            match_details,
            indent=2,
            ensure_ascii=False
        )
    )