from ddgs import DDGS
import re


# ==================================================
# TEAM ALIASES
# ==================================================

TEAM_ALIASES = {
    "india": "India",
    "indian": "India",

    "australia": "Australia",
    "australian": "Australia",

    "england": "England",
    "english": "England",

    "sri lanka": "Sri Lanka",
    "srilanka": "Sri Lanka",

    "south africa": "South Africa",
    "new zealand": "New Zealand",

    "pakistan": "Pakistan",
    "bangladesh": "Bangladesh",

    "west indies": "West Indies",
    "afghanistan": "Afghanistan",
    "ireland": "Ireland",
    "zimbabwe": "Zimbabwe",
}


# ==================================================
# EXTRACT TEAMS
# ==================================================

def extract_teams(text):

    text = text.lower()

    found = []

    # Longest aliases first
    aliases = sorted(
        TEAM_ALIASES.keys(),
        key=len,
        reverse=True
    )

    for alias in aliases:

        if re.search(
            rf"\b{re.escape(alias)}\b",
            text
        ):

            team = TEAM_ALIASES[alias]

            if team not in found:
                found.append(team)

    return found


# ==================================================
# SEARCHER
# ==================================================

def find_opponents(query):

    print("\n[Searcher] Could not determine opponents.")
    print("[Searcher] Searching:", query)

    queries = [
        f'"{query}" cricket teams',
        f'"{query}" cricket series teams',
        f'"{query}" cricket'
    ]

    team_scores = {}
    results_seen = set()

    with DDGS() as ddgs:

        for search_query in queries:

            try:

                results = ddgs.text(
                    search_query,
                    max_results=5
                )

            except Exception as e:

                print("[Searcher] Search failed:", e)
                continue

            for result in results:

                title = result.get(
                    "title",
                    ""
                )

                body = result.get(
                    "body",
                    ""
                )

                url = result.get(
                    "href",
                    ""
                )

                # Avoid duplicate search results
                if url in results_seen:
                    continue

                results_seen.add(url)

                text = (
                    title +
                    " " +
                    body
                )

                teams = extract_teams(text)

                print(
                    f"[Searcher] {title}"
                )
                print(
                    f"[Searcher] Teams found: {teams}"
                )

                for team in teams:

                    team_scores[team] = (
                        team_scores.get(team, 0) + 1
                    )

    # --------------------------------------------------
    # Rank teams
    # --------------------------------------------------

    ranked = sorted(
        team_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    print(
        "[Searcher] Team scores:",
        ranked
    )

    if len(ranked) < 2:

        print(
            "[Searcher] Could not determine two teams."
        )

        return None

    team1 = ranked[0][0]
    team2 = ranked[1][0]

    print(
        f"[Searcher] Opponents: "
        f"{team1} vs {team2}"
    )

    return [
        team1,
        team2
    ]