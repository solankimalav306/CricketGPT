
from db import resolve_player
from state import CricketState
from templates.matchup_templates import get_m1_template, get_m2_template, get_m3_template, get_m4_template, get_m5_template
from db import execute_pipeline

def process_matchup(query, schedule):

    template = query["template"]

    # ==================================================
    # M1 : Batter vs Bowler
    # ==================================================

    if template == "M1":

        batter = resolve_player(query["batter"], query["batter_team"])
        bowler = resolve_player(query["bowler"], query["bowler_team"])

        if batter["status"] != "resolved":
            return {
                "template": "M1",
                "status": "batter_resolution_failed",
                "query": query,
                "resolution": batter
            }

        if bowler["status"] != "resolved":
            return {
                "template": "M1",
                "status": "bowler_resolution_failed",
                "query": query,
                "resolution": bowler
            }

        pipeline = get_m1_template(
            batter_name=batter["resolved_name"],
            bowler_name=bowler["resolved_name"]
        )

        result = execute_pipeline(pipeline)

        stats = result[0] if result else {
            "runs": 0,
            "balls": 0,
            "dismissals": 0,
            "strike_rate": 0
        }

        return {
            "template": "M1",
            "status": "success",
            "batter": {
                "requested": query["batter"],
                "resolved": batter["resolved_name"],
                "team": query["batter_team"]
            },
            "bowler": {
                "requested": query["bowler"],
                "resolved": bowler["resolved_name"],
                "team": query["bowler_team"]
            },
            "stats": stats
        }

    # ==================================================
    # M2 : Bowler vs Batter
    # ==================================================

    if template == "M2":

        bowler = resolve_player(query["bowler"], query["bowler_team"])
        batter = resolve_player(query["batter"], query["batter_team"])

        if bowler["status"] != "resolved":
            return {
                "template": "M2",
                "status": "bowler_resolution_failed",
                "query": query,
                "resolution": bowler
            }

        if batter["status"] != "resolved":
            return {
                "template": "M2",
                "status": "batter_resolution_failed",
                "query": query,
                "resolution": batter
            }

        pipeline = get_m2_template(
            bowler_name=bowler["resolved_name"],
            batter_name=batter["resolved_name"]
        )

        result = execute_pipeline(pipeline)

        stats = result[0] if result else {
            "runs": 0,
            "balls": 0,
            "dismissals": 0,
            "strike_rate": 0
        }

        return {
            "template": "M2",
            "status": "success",
            "bowler": {
                "requested": query["bowler"],
                "resolved": bowler["resolved_name"],
                "team": query["bowler_team"]
            },
            "batter": {
                "requested": query["batter"],
                "resolved": batter["resolved_name"],
                "team": query["batter_team"]
            },
            "stats": stats
        }

    # ==================================================
    # M3 : Player vs Team
    # ==================================================

    if template == "M3":

        player = resolve_player(query["player"], query["player_team"])

        if player["status"] != "resolved":
            return {
                "template": "M3",
                "status": "player_resolution_failed",
                "query": query,
                "resolution": player
            }

        pipeline = get_m3_template(
            player_name=player["resolved_name"],
            opponent_team=query["opponent_team"],
            role=query["role"]
        )

        result = execute_pipeline(pipeline)

        return {
            "template": "M3",
            "status": "success",
            "player": {
                "requested": query["player"],
                "resolved": player["resolved_name"],
                "team": query["player_team"]
            },
            "opponent_team": query["opponent_team"],
            "role": query["role"],
            "stats": result[0] if result else {}
        }

    # ==================================================
    # M4 : Recent Batter vs Bowler
    # ==================================================

    if template == "M4":

        batter = resolve_player(query["batter"], query["batter_team"])
        bowler = resolve_player(query["bowler"], query["bowler_team"])

        if batter["status"] != "resolved":
            return {
                "template": "M4",
                "status": "batter_resolution_failed",
                "query": query,
                "resolution": batter
            }

        if bowler["status"] != "resolved":
            return {
                "template": "M4",
                "status": "bowler_resolution_failed",
                "query": query,
                "resolution": bowler
            }

        pipeline = get_m4_template(
            batter_name=batter["resolved_name"],
            bowler_name=bowler["resolved_name"],
            limit_n=query.get("limit", 5)
        )

        result = execute_pipeline(pipeline)

        return {
            "template": "M4",
            "status": "success",
            "batter": {
                "requested": query["batter"],
                "resolved": batter["resolved_name"],
                "team": query["batter_team"]
            },
            "bowler": {
                "requested": query["bowler"],
                "resolved": bowler["resolved_name"],
                "team": query["bowler_team"]
            },
            "limit": query.get("limit", 5),
            "stats": result
        }

    # ==================================================
    # M5 : Team vs Team
    # ==================================================

    if template == "M5":

        pipeline = get_m5_template(
            team1=query["team1"],
            team2=query["team2"],
            limit_n=query.get("limit")
        )

        result = execute_pipeline(pipeline)

        return {
            "template": "M5",
            "status": "success",
            "team1": query["team1"],
            "team2": query["team2"],
            "limit": query.get("limit"),
            "stats": result[0] if result else {}
        }

    # ==================================================
    # Unknown
    # ==================================================

    return {
        "template": template,
        "status": "unknown_template"
    }