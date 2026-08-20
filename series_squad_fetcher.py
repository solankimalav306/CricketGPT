import requests
import re
import json
from bs4 import BeautifulSoup

class CricbuzzSeriesScraper:
    def __init__(self, series_id):
        self.series_id = series_id
        self.base_url = f"https://www.cricbuzz.com/cricket-series/{self.series_id}/dummy-slug"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }

    def _fetch_page_html(self, endpoint):
        """Helper to fetch the raw HTML for a specific series page (squads, matches)."""
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.text

    # ==========================================
    # SQUAD EXTRACTION (Regex Method)
    # ==========================================
    def get_squads(self):
        """Fetches and builds a dictionary of squads mapped by teamId."""
        print(f"[*] Fetching squads for Series {self.series_id}...")
        html = self._fetch_page_html("squads")
        
        squads_meta = {}
        # Find raw blocks containing squadId
        block_pattern = r'\{[^{}]*?(?:\\")?squadId(?:\\")?\s*:\s*\d+[^{}]*?\}'
        blocks = re.findall(block_pattern, html)
        
        for block in blocks:
            squad_id_match = re.search(r'(?:\\")?squadId(?:\\")?\s*:\s*(\d+)', block)
            team_id_match = re.search(r'(?:\\")?teamId(?:\\")?\s*:\s*(\d+)', block)
            team_name_match = re.search(r'(?:\\")?squadType(?:\\")?\s*:\s*(?:\\")?([^"\\]+)(?:\\")?', block)
            
            if squad_id_match and team_id_match:
                squad_id = int(squad_id_match.group(1))
                team_id = int(team_id_match.group(1))
                team_name = team_name_match.group(1) if team_name_match else "Unknown Team"
                
                if team_id not in squads_meta:
                    squads_meta[team_id] = {
                        "squadId": squad_id,
                        "teamId": team_id,
                        "teamName": team_name
                    }
        
        final_squads = {}
        # Fetch actual players from internal API
        for team_id, squad in squads_meta.items():
            api_url = f"https://www.cricbuzz.com/api/cricket-series/series-squads/{self.series_id}/{squad['squadId']}"
            api_resp = requests.get(api_url, headers=self.headers)
            
            if api_resp.status_code == 200:
                final_squads[team_id] = {
                    **squad,
                    "players": api_resp.json().get('player', [])
                }
            else:
                print(f"    [!] Failed to fetch players for {squad['teamName']}")
                
        return final_squads

    # ==========================================
    # MATCH EXTRACTION (Payload Decoding Method)
    # ==========================================
    def get_matches(self):
        """Fetches and parses the match schedule for the series."""
        print(f"[*] Fetching matches for Series {self.series_id}...")
        html = self._fetch_page_html("matches")
        soup = BeautifulSoup(html, "html.parser")
        
        target_marker = 'self.__next_f.push([1,"'
        scripts = soup.find_all("script")
        
        for script in scripts:
            text = script.string
            if not text or target_marker not in text:
                continue
            
            # Extract the raw payload
            start = text.find(target_marker) + len('self.__next_f.push([1,')
            decoder = json.JSONDecoder()
            
            try:
                payload, _ = decoder.raw_decode(text[start:])
            except Exception:
                continue
                
            # Verify this is the payload containing matchesData
            data_start = payload.find('"matchesData":')
            if data_start == -1:
                continue
                
            details_start = payload.find('"matchDetails":', data_start)
            if details_start == -1:
                continue
                
            array_start = payload.find("[", details_start)
            if array_start == -1:
                continue
                
            # Balance brackets to extract JSON array
            depth, in_string, escaped = 0, False, False
            array_end = None
            
            for i in range(array_start, len(payload)):
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
                        
            if array_end:
                raw_match_details = payload[array_start:array_end + 1]
                try:
                    return json.loads(raw_match_details)
                except Exception as e:
                    print(f"[!] Failed to parse match array: {e}")
                    return []
                    
        return []

    # ==========================================
    # COMBINE EVERYTHING
    # ==========================================
    def get_full_series_graph(self):
        """
        Combines squads and matches into a single cohesive data structure.
        """
        squads = self.get_squads()
        matches = self.get_matches()
        
        return {
            "seriesId": self.series_id,
            "squads": squads,
            "matches": matches
        }

def fetch_series_graph(series_id: int) -> dict:
    """
    Fetch and combine all Cricbuzz data for a series.

    Returns:
        {
            "seriesId": ...,
            "squads": {...},
            "matches": [...]
        }
    """

    scraper = CricbuzzSeriesScraper(series_id)

    return scraper.get_full_series_graph()