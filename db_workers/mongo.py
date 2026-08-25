from db_workers.player import process_player_request
from db_workers.matchup import process_matchup
from db_workers.venue import process_venue_request

def run_mongo_agent(state):
    """
    MongoDB execution agent.
    Executes deterministic template pipelines.
    """

    # print("\n" + "=" * 100)
    # print("MONGO QUERY AGENT START")
    # print("=" * 100)

    mongo_results = {
        "player": [],
        "matchup": [],
        "venue": [],
        "external": []
    }

    schedule = state.get("schedule", {})

    # ==================================================
    # PLAYER TEMPLATES
    # ==================================================

    player_queries = state.get("player_db_queries", [])

    # print(f"\nPlayer template queries: {len(player_queries)}")

    for query in player_queries:

        try:
            result = process_player_request(
                query=query,
                schedule=schedule
            )

            mongo_results["player"].append(result)

        except Exception as e:

            mongo_results["player"].append({
                "status": "error",
                "query": query,
                "error": str(e)
            })

    # ==================================================
    # MATCHUP TEMPLATES
    # ==================================================

    # ==================================================
    # MATCHUP TEMPLATES
    # ==================================================

    # ==================================================
    # MATCHUPS
    # ==================================================

    matchup_queries = state.get("matchup_queries", [])
    schedule = state.get("schedule", {})

    print(f"\nMatchup queries: {len(matchup_queries)}")

    for query in matchup_queries:

        try:
            result = process_matchup(
                query=query,
                schedule=schedule
            )

            mongo_results["matchup"].append(result)

        except Exception as e:

            mongo_results["matchup"].append({
                "status": "error",
                "query": query,
                "error": str(e)
            })
    # ==================================================
    # VENUE TEMPLATES
    # ==================================================

    venue_queries = state.get("venue_queries", [])

    print(f"\nVenue template queries: {len(venue_queries)}")

    for query in venue_queries:

        try:
            result = process_venue_request(
                query=query
            )

            mongo_results["venue"].append(result)

        except Exception as e:

            mongo_results["venue"].append({
                "status": "error",
                "query": query,
                "error": str(e)
            })

    # ==================================================
    # EXTERNAL REQUESTS
    # ==================================================

    mongo_results["external"] = state.get(
        "weather_requests",
        []
    )

    # ==================================================
    # LOGS
    # ==================================================

    print("\n" + "=" * 100)
    print("MONGO QUERY AGENT COMPLETE")
    print("=" * 100)

    print(f"Player  : {len(mongo_results['player'])}")
    print(f"Matchup : {len(mongo_results['matchup'])}")
    print(f"Venue   : {len(mongo_results['venue'])}")

    return {
        "mongo_results": mongo_results
    }

