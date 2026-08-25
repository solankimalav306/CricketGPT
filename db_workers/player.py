from db import resolve_player
from state import CricketState
from db import execute_pipeline
from templates import (
    get_p1_template,
    get_p2_template,
    get_p3_template,
    get_p4_template,
    get_p5_template,
    get_p6_template,
    get_p7_template,
    get_p8_template,
    get_p9_template
)

PLAYER_TEMPLATES = {
    "P1": get_p1_template,
    "P2": get_p2_template,
    "P3": get_p3_template,
    "P4": get_p4_template,
    "P5": get_p5_template,
    "P6": get_p6_template,
    "P7": get_p7_template,
    "P8": get_p8_template,
    "P9": get_p9_template,
}

def process_player_request(query, schedule):
    """
    Execute one structured Player Agent query.
    """
    template_id = query["template"]
    requested_player = query["player"]

    # ==================================================
    # 1. Resolve Team From Scheduler (Safely)
    # ==================================================
    team = query.get("team")  # LLM might have provided it

    if not team:
        squads = schedule.get("squads", {})
        for squad in squads.values():
            for player in squad.get("players", []):
                if player.get("isHeader"):
                    continue
                if player["name"] == requested_player:
                    team = squad["teamName"]
                    break
            if team:
                break

    # NOTICE: We REMOVED the "if not team: return error" block here!
    # resolve_player can now handle team=None.

    # ==================================================
    # 2. Resolve Cricsheet Name
    # ==================================================
    resolved = resolve_player(
        full_name=requested_player,
        team=team
    )

    if resolved["status"] != "resolved":
        return {
            "status": resolved["status"],
            "player": requested_player,
            "resolution": resolved
        }

    actual_name = resolved["resolved_name"]

    # ==================================================
    # 3. Build Pipeline (Safely fetching args)
    # ==================================================
    builder = PLAYER_TEMPLATES.get(template_id)

    if builder is None:
        return {
            "status": "invalid_template",
            "template": template_id
        }

    if template_id in ("P1", "P3"):
        pipeline = builder(
            player_name=actual_name,
            team_name=team,
            limit_n=query.get("limit", 10)
        )
    elif template_id in ("P2", "P4"):
        pipeline = builder(
            player_name=actual_name,
            team_name=team
        )
    elif template_id == "P5":
        pipeline = builder(
            player_name=actual_name,
            start_date=query.get("start_date", "1800-01-01"), # Fallback dates
            end_date=query.get("end_date", "2100-01-01"),
            team_name=team
        )
    elif template_id == "P6":
        pipeline = builder(
            player_name=actual_name,
            match_format=query.get("match_format", "Test"), # Fallback format
            role=query.get("role", "batting"),
            team_name=team
        )
    elif template_id == "P7":
        pipeline = builder(
            player_name=actual_name,
            home_country=query.get("home_country", team if team else "India"),
            role=query.get("role", "batting"),
            team_name=team
        )
    elif template_id in ("P8", "P9"):
        pipeline = builder(
            player_name=actual_name,
            team_name=team,
            role=query.get("role", "batting")
        )

    # ==================================================
    # 4. Execute
    # ==================================================
    try:
        result = execute_pipeline(pipeline)
    except Exception as e:
        return {
            "status": "mongo_error",
            "template": template_id,
            "player": actual_name,
            "error": str(e)
        }

    print(f"Returned {len(result)} documents")

    return {
        "status": "success",
        "template": template_id,
        "requested_player": requested_player,
        "resolved_player": actual_name,
        "team": team,
        "result": result
    }