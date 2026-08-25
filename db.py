import json
import re
# from pathlib import Path

# from annotated_types import doc
from pymongo import MongoClient
# from templates import get_m1_template
# from templates.matchup_templates import get_m2_template, get_m3_template, get_m4_template, get_m5_template


# ==================================================
# MONGODB
# ==================================================

client = MongoClient("mongodb://localhost:27017")

db = client["cricket_db"]
matches = db["matches"]

def execute_pipeline(pipeline):
    """
    Execute an aggregation pipeline against
    the matches collection.
    """
    # print("\n[Mongo] Executing pipeline...")
    # print(json.dumps(pipeline, indent=2, ensure_ascii=False))

    result = list(
        matches.aggregate(
            pipeline,
            allowDiskUse=True
        )
    )

    print(f"[Mongo] Documents returned: {len(result)}")
    return result


from db_workers.venue import process_venue_request
# ==================================================
# SCHEMA
# ==================================================

SCHEMA_PATH = "C:\\code\\CricketGPT\\mds\\mongoSchema.md"


def load_schema():
    with open(
        SCHEMA_PATH,
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


MONGO_SCHEMA = load_schema()


# ==================================================
# NAME NORMALIZATION
# ==================================================

def normalize_name(name):
    """
    Normalize a player name.
    """
    if not name:
        return ""

    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


# ==================================================
# PLAYER RESOLUTION
# ==================================================

# def resolve_player(full_name, team):
#     """
#     Resolve a player name to the Cricsheet representation.
#     Example:
#         Steve Smith -> SPD Smith
#         Shubman Gill -> Shubman Gill / S Gill
#     """

#     # print("\n" + "-" * 80)
#     # print("[PLAYER RESOLVER]")
#     # print("-" * 80)
#     # print("Requested player:", full_name)
#     # print("Team:", team)

#     if not full_name:
#         return {"status": "not_found", "reason": "Player name missing"}

#     if not team:
#         return {"status": "not_found", "reason": "Team missing"}

#     tokens = full_name.strip().split()
#     if len(tokens) < 2:
#         return {"status": "not_found", "reason": "Invalid player name"}

#     first_initial = tokens[0][0]
#     surname = tokens[-1]

#     regex_pattern = rf"^{re.escape(first_initial)}.*\s+{re.escape(surname)}$"
#     # print("Regex:", regex_pattern)

#     # All unique players who have represented this team
#     players = matches.distinct(f"info.players.{team}")
#     # print(f"1.Total players in team {team}: {len(players)}")
#     players = [p for p in players if isinstance(p, str)]
#     # print(f"2.Found {len(players)} players for team {team}")
#     candidates = sorted({
#         p for p in players
#         if re.match(regex_pattern, p, re.IGNORECASE)
#     })

#     # print("Candidates:", candidates)

#     if len(candidates) == 1:
#         return {
#             "status": "resolved",
#             "requested_name": full_name,
#             "resolved_name": candidates[0],
#             "team": team
#         }

#     if len(candidates) == 0:
#         return {
#             "status": "not_found",
#             "requested_name": full_name,
#             "team": team,
#             "pattern": regex_pattern
#         }

#     return {
#         "status": "ambiguous",
#         "requested_name": full_name,
#         "team": team,
#         "candidates": candidates
#     }
import re

def resolve_player(full_name, team=None):
    """
    Tier-based Player Resolution System.
    Uses Initial Exactness (Tier 1 > Tier 2 > Tier 3) followed by a Frequency Tie-Breaker.
    """
    if not full_name:
        return {"status": "not_found", "reason": "Player name missing"}

    tokens = full_name.strip().split()
    if len(tokens) < 2:
        return {"status": "not_found", "reason": "Invalid player name (needs first and last name)"}

    surname = tokens[-1]
    
    # Extract user initials (e.g., "Rohit" -> "R", "KL" -> "KL")
    user_initials = ""
    for t in tokens[:-1]:
        if t.isupper() and len(t) <= 3:
            user_initials += t
        else:
            user_initials += t[0].upper()

    # Determine which teams to search
    teams_to_check = [team] if team else [
        "India", "Australia", "England", "South Africa", "New Zealand", 
        "Pakistan", "Sri Lanka", "West Indies", "Bangladesh", "Afghanistan", 
        "Zimbabwe", "Ireland"
    ]

    candidates_info = []
    
    # Regex: Match the exact surname at the end of the string
    surname_pattern = rf"\b{re.escape(surname)}$"

    # Fetch all matching candidates from the DB
    for t in teams_to_check:
        try:
            team_players = matches.distinct(f"info.players.{t}")
            for p in team_players:
                if isinstance(p, str) and re.search(surname_pattern, p, re.IGNORECASE):
                    candidates_info.append({"name": p, "team": t})
        except Exception:
            pass

    if not candidates_info:
        return {"status": "not_found", "requested_name": full_name, "team": team}

    # ==================================================
    # SCORING (The 3 Tiers)
    # ==================================================
    tier1 = [] # Exact Full Name match (e.g., "V Kohli" == "V Kohli")
    tier2 = [] # Exact Initials match (e.g., "Rahul" (R) == "R Sharma")
    tier3 = [] # Subset Initials match (e.g., "Rohit" (R) matches "RG Sharma")
    
    for c in candidates_info:
        c_name = c["name"]
        
        # Tier 1
        if c_name.lower() == full_name.lower():
            tier1.append(c)
            continue
            
        # Parse candidate initials (Cricsheet format: "RG Sharma" -> "RG")
        c_tokens = c_name.split()
        c_initials = "".join(c_tokens[:-1]).upper()
        
        # Tier 2
        if user_initials == c_initials:
            tier2.append(c)
        # Tier 3 (Must start with the exact same first letter to prevent "Axar" (A) matching "Parthiv" (PA))
        elif c_initials.startswith(user_initials):
            tier3.append(c)

    # Determine highest available tier
    best_tier = tier1 if tier1 else (tier2 if tier2 else tier3)
        
    if not best_tier:
        return {"status": "not_found", "requested_name": full_name, "team": team}

    # ==================================================
    # FREQUENCY TIE-BREAKER (Only applied within the winning tier)
    # ==================================================
    best_candidate = None
    best_team = None
    max_match_count = -1

    for c in best_tier:
        count = matches.count_documents({f"info.players.{c['team']}": c['name']})
        if count > max_match_count:
            max_match_count = count
            best_candidate = c["name"]
            best_team = c["team"]
            
    tier_num = 1 if best_tier == tier1 else (2 if best_tier == tier2 else 3)
    print(f"[Player Resolver] '{full_name}' -> '{best_candidate}' ({best_team}) | Tier {tier_num} Match | {max_match_count} matches played.")

    return {
        "status": "resolved",
        "requested_name": full_name,
        "resolved_name": best_candidate,
        "team": best_team
    }
# ==================================================
# LLM → MONGO PIPELINE
# ==================================================

def generate_mongo_pipeline(
    natural_language_request,
    llm
):
    """
    Convert a natural-language database request
    into a MongoDB aggregation pipeline.
    """

    prompt = f"""
You are the MongoDB Query Agent for CricketGPT.

Your job is ONLY to convert the supplied analytical
requirement into a valid MongoDB aggregation pipeline.

MongoDB collection:

matches

Database schema:

{MONGO_SCHEMA}

IMPORTANT RULES:

1. Generate only a MongoDB aggregation pipeline.
2. Never invent fields.
3. Use the exact fields from the schema.
4. Use $unwind for nested innings / overs / deliveries
   whenever required.
5. Put $match as early as reasonably possible.
6. Return only the fields required by the request.
7. Do not answer the cricket question.
8. Do not make predictions.
9. Do not use external APIs.
10. Do not use Markdown.
11. Return valid JSON only.
12. Use the resolved player name and team exactly as provided.
13. Never use "$$" variables. Use "$_id" for the document id.
14. Never use unsupported operators such as $objectKeys, $getField, or JavaScript expressions.
15. If the request asks for statistics, the pipeline MUST end with $group followed by $project.
16. Never return ball-by-ball deliveries unless the analytical request explicitly asks for deliveries.
17. For player queries, always filter matches using info.players.<team> before unwinding innings.
18. For "last N matches", apply the order:
    $match (info.players.<team>)
    → $sort (info.dates descending)
    → $limit (N)
    → $unwind innings
    → $unwind overs
    → $unwind deliveries.
19. Count balls faced by excluding deliveries where extras.wides exists. Do not use $objectKeys.
20. Return only valid MongoDB aggregation stages.

Return exactly:

{{
    "pipeline": [
        ...
    ]
}}

Analytical requirement:

{natural_language_request}
"""

    print("\n[Mongo Query Generator]")
    print(f"Request: {natural_language_request}")

    response = llm.invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "".join(
            (
                part.get("text", "")
                if isinstance(part, dict)
                else str(part)
            )
            for part in content
        )

    content = content.strip()
    content = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    content = content.strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        print("[Mongo Query Generator] Invalid JSON returned by LLM")
        print(content)
        raise e

    pipeline = parsed.get("pipeline")

    if not isinstance(pipeline, list):
        raise ValueError("LLM did not return a valid 'pipeline' list.")

    print(f"[Mongo Query Generator] Pipeline stages: {len(pipeline)}")
    return pipeline


# ==================================================
# EXECUTE MONGO PIPELINE
# ==================================================



# ==================================================
# EXTRACT PLAYER + TEAM FROM NL REQUEST
# ==================================================

def extract_player_entity(request, llm):
    """
    Ask the LLM only to identify the player and
    team from the already-generated database request.
    """
    prompt = f"""
Extract the player and team from the following
CricketGPT database requirement.

Return ONLY valid JSON.

Format:

{{
    "player": "full player name",
    "team": "team/country"
}}

Rules:

1. Return the player's full name if available.
2. Return the country/team if available.
3. Do not answer the request.
4. Do not generate a Mongo query.

Requirement:

{request}
"""

    response = llm.invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "".join(
            (
                part.get("text", "")
                if isinstance(part, dict)
                else str(part)
            )
            for part in content
        )

    content = content.strip()
    content = re.sub(r"^```json\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\s*```$", "", content)

    return json.loads(content)


# ==================================================
# PLAYER REQUEST
# ==================================================

# from templates import (
#     get_p1_template,
#     get_p2_template,
#     get_p3_template,
#     get_p4_template,
#     get_p5_template,
#     get_p6_template,
#     get_p7_template,
#     get_p8_template,
#     get_p9_template
# )

# --------------------------------------------------
# Template Dispatcher
# --------------------------------------------------

# PLAYER_TEMPLATES = {
#     "P1": get_p1_template,
#     "P2": get_p2_template,
#     "P3": get_p3_template,
#     "P4": get_p4_template,
#     "P5": get_p5_template,
#     "P6": get_p6_template,
#     "P7": get_p7_template,
#     "P8": get_p8_template,
#     "P9": get_p9_template,
# }


# --------------------------------------------------
# Player Request Executor
# --------------------------------------------------

# def process_player_request(query, schedule):
    # """
    # Execute one structured Player Agent query.

    # Example query:
    # {
    #     "template": "P1",
    #     "player": "KL Rahul",
    #     "limit": 10
    # }
    # """

    # print("\n" + "=" * 80)
    # print("[PLAYER DATABASE REQUEST]")
    # print("=" * 80)
    # print(json.dumps(query, indent=2, ensure_ascii=False))

    # template_id = query["template"]
    # requested_player = query["player"]

    # # ==================================================
    # # 1. Resolve Team From Scheduler
    # # ==================================================

    # team = None

    # for squad in schedule["squads"].values():

    #     for player in squad["players"]:

    #         if player.get("isHeader"):
    #             continue

    #         if player["name"] == requested_player:
    #             team = squad["teamName"]
    #             break

    #     if team:
    #         break

    # if not team:
    #     return {
    #         "status": "not_found",
    #         "player": requested_player,
    #         "reason": "Player not present in scheduler squads"
    #     }

    # # print(f"Team : {team}")

    # # ==================================================
    # # 2. Resolve Cricsheet Name
    # # ==================================================

    # resolved = resolve_player(
    #     full_name=requested_player,
    #     team=team
    # )

    # if resolved["status"] != "resolved":
    #     return {
    #         "status": resolved["status"],
    #         "player": requested_player,
    #         "resolution": resolved
    #     }

    # actual_name = resolved["resolved_name"]

    # # print(f"Resolved : {actual_name}")

    # # ==================================================
    # # 3. Build Pipeline
    # # ==================================================

    # builder = PLAYER_TEMPLATES.get(template_id)

    # if builder is None:
    #     return {
    #         "status": "invalid_template",
    #         "template": template_id
    #     }

    # if template_id in ("P1", "P3"):
    #     pipeline = builder(
    #         player_name=actual_name,
    #         team_name=team,
    #         limit_n=query.get("limit", 10)
    #     )

    # elif template_id == "P2":
    #     pipeline = builder(
    #         player_name=actual_name,
    #         team_name=team
    #     )

    # elif template_id == "P4":
    #     pipeline = builder(
    #         player_name=actual_name,
    #         team_name=team
    #     )

    # elif template_id == "P5":
    #     pipeline = builder(
    #         player_name=actual_name,
    #         start_date=query["start_date"],
    #         end_date=query["end_date"],
    #         team_name=team
    #     )

    # elif template_id == "P6":
    #     pipeline = builder(
    #         player_name=actual_name,
    #         match_format=query["match_format"],
    #         role=query.get("role", "batting"),
    #         team_name=team
    #     )

    # elif template_id == "P7":
    #     pipeline = builder(
    #         player_name=actual_name,
    #         home_country=query["home_country"],
    #         role=query.get("role", "batting"),
    #         team_name=team
    #     )

    # elif template_id == "P8":
    #     pipeline = builder(
    #         player_name=actual_name,
    #         role=query.get("role", "batting"),
    #         team_name=team
    #     )

    # elif template_id == "P9":
    #     pipeline = builder(
    #         player_name=actual_name,
    #         team_name=team,
    #         role=query.get("role", "batting")
    #     )

    # # print("\nPipeline Built")
    # # print(json.dumps(pipeline, indent=2, ensure_ascii=False))

    # # ==================================================
    # # 4. Execute
    # # ==================================================

    # try:
    #     result = execute_pipeline(pipeline)

    # except Exception as e:
    #     return {
    #         "status": "mongo_error",
    #         "template": template_id,
    #         "player": actual_name,
    #         "error": str(e)
    #     }

    # print(f"Returned {len(result)} documents")

    # return {
    #     "status": "success",
    #     "template": template_id,
    #     "requested_player": requested_player,
    #     "resolved_player": actual_name,
    #     "team": team,
    #     "result": result
    # }

# def process_player_request(query, schedule):
#     """
#     Execute one structured Player Agent query.
#     """
#     template_id = query["template"]
#     requested_player = query["player"]

#     # ==================================================
#     # 1. Resolve Team From Scheduler (Safely)
#     # ==================================================
#     team = query.get("team")  # LLM might have provided it

#     if not team:
#         squads = schedule.get("squads", {})
#         for squad in squads.values():
#             for player in squad.get("players", []):
#                 if player.get("isHeader"):
#                     continue
#                 if player["name"] == requested_player:
#                     team = squad["teamName"]
#                     break
#             if team:
#                 break

#     # NOTICE: We REMOVED the "if not team: return error" block here!
#     # resolve_player can now handle team=None.

#     # ==================================================
#     # 2. Resolve Cricsheet Name
#     # ==================================================
#     resolved = resolve_player(
#         full_name=requested_player,
#         team=team
#     )

#     if resolved["status"] != "resolved":
#         return {
#             "status": resolved["status"],
#             "player": requested_player,
#             "resolution": resolved
#         }

#     actual_name = resolved["resolved_name"]

#     # ==================================================
#     # 3. Build Pipeline (Safely fetching args)
#     # ==================================================
#     builder = PLAYER_TEMPLATES.get(template_id)

#     if builder is None:
#         return {
#             "status": "invalid_template",
#             "template": template_id
#         }

#     if template_id in ("P1", "P3"):
#         pipeline = builder(
#             player_name=actual_name,
#             team_name=team,
#             limit_n=query.get("limit", 10)
#         )
#     elif template_id in ("P2", "P4"):
#         pipeline = builder(
#             player_name=actual_name,
#             team_name=team
#         )
#     elif template_id == "P5":
#         pipeline = builder(
#             player_name=actual_name,
#             start_date=query.get("start_date", "1800-01-01"), # Fallback dates
#             end_date=query.get("end_date", "2100-01-01"),
#             team_name=team
#         )
#     elif template_id == "P6":
#         pipeline = builder(
#             player_name=actual_name,
#             match_format=query.get("match_format", "Test"), # Fallback format
#             role=query.get("role", "batting"),
#             team_name=team
#         )
#     elif template_id == "P7":
#         pipeline = builder(
#             player_name=actual_name,
#             home_country=query.get("home_country", team if team else "India"),
#             role=query.get("role", "batting"),
#             team_name=team
#         )
#     elif template_id in ("P8", "P9"):
#         pipeline = builder(
#             player_name=actual_name,
#             team_name=team,
#             role=query.get("role", "batting")
#         )

#     # ==================================================
#     # 4. Execute
#     # ==================================================
#     try:
#         result = execute_pipeline(pipeline)
#     except Exception as e:
#         return {
#             "status": "mongo_error",
#             "template": template_id,
#             "player": actual_name,
#             "error": str(e)
#         }

#     print(f"Returned {len(result)} documents")

#     return {
#         "status": "success",
#         "template": template_id,
#         "requested_player": requested_player,
#         "resolved_player": actual_name,
#         "team": team,
#         "result": result
#     }
    
# ==================================================
# MATCHUP REQUEST
# ==================================================

# def process_matchup(query, schedule):

#     template = query["template"]

#     # ==================================================
#     # M1 : Batter vs Bowler
#     # ==================================================

#     if template == "M1":

#         batter = resolve_player(query["batter"], query["batter_team"])
#         bowler = resolve_player(query["bowler"], query["bowler_team"])

#         if batter["status"] != "resolved":
#             return {
#                 "template": "M1",
#                 "status": "batter_resolution_failed",
#                 "query": query,
#                 "resolution": batter
#             }

#         if bowler["status"] != "resolved":
#             return {
#                 "template": "M1",
#                 "status": "bowler_resolution_failed",
#                 "query": query,
#                 "resolution": bowler
#             }

#         pipeline = get_m1_template(
#             batter_name=batter["resolved_name"],
#             bowler_name=bowler["resolved_name"]
#         )

#         result = execute_pipeline(pipeline)

#         stats = result[0] if result else {
#             "runs": 0,
#             "balls": 0,
#             "dismissals": 0,
#             "strike_rate": 0
#         }

#         return {
#             "template": "M1",
#             "status": "success",
#             "batter": {
#                 "requested": query["batter"],
#                 "resolved": batter["resolved_name"],
#                 "team": query["batter_team"]
#             },
#             "bowler": {
#                 "requested": query["bowler"],
#                 "resolved": bowler["resolved_name"],
#                 "team": query["bowler_team"]
#             },
#             "stats": stats
#         }

#     # ==================================================
#     # M2 : Bowler vs Batter
#     # ==================================================

#     if template == "M2":

#         bowler = resolve_player(query["bowler"], query["bowler_team"])
#         batter = resolve_player(query["batter"], query["batter_team"])

#         if bowler["status"] != "resolved":
#             return {
#                 "template": "M2",
#                 "status": "bowler_resolution_failed",
#                 "query": query,
#                 "resolution": bowler
#             }

#         if batter["status"] != "resolved":
#             return {
#                 "template": "M2",
#                 "status": "batter_resolution_failed",
#                 "query": query,
#                 "resolution": batter
#             }

#         pipeline = get_m2_template(
#             bowler_name=bowler["resolved_name"],
#             batter_name=batter["resolved_name"]
#         )

#         result = execute_pipeline(pipeline)

#         stats = result[0] if result else {
#             "runs": 0,
#             "balls": 0,
#             "dismissals": 0,
#             "strike_rate": 0
#         }

#         return {
#             "template": "M2",
#             "status": "success",
#             "bowler": {
#                 "requested": query["bowler"],
#                 "resolved": bowler["resolved_name"],
#                 "team": query["bowler_team"]
#             },
#             "batter": {
#                 "requested": query["batter"],
#                 "resolved": batter["resolved_name"],
#                 "team": query["batter_team"]
#             },
#             "stats": stats
#         }

#     # ==================================================
#     # M3 : Player vs Team
#     # ==================================================

#     if template == "M3":

#         player = resolve_player(query["player"], query["player_team"])

#         if player["status"] != "resolved":
#             return {
#                 "template": "M3",
#                 "status": "player_resolution_failed",
#                 "query": query,
#                 "resolution": player
#             }

#         pipeline = get_m3_template(
#             player_name=player["resolved_name"],
#             opponent_team=query["opponent_team"],
#             role=query["role"]
#         )

#         result = execute_pipeline(pipeline)

#         return {
#             "template": "M3",
#             "status": "success",
#             "player": {
#                 "requested": query["player"],
#                 "resolved": player["resolved_name"],
#                 "team": query["player_team"]
#             },
#             "opponent_team": query["opponent_team"],
#             "role": query["role"],
#             "stats": result[0] if result else {}
#         }

#     # ==================================================
#     # M4 : Recent Batter vs Bowler
#     # ==================================================

#     if template == "M4":

#         batter = resolve_player(query["batter"], query["batter_team"])
#         bowler = resolve_player(query["bowler"], query["bowler_team"])

#         if batter["status"] != "resolved":
#             return {
#                 "template": "M4",
#                 "status": "batter_resolution_failed",
#                 "query": query,
#                 "resolution": batter
#             }

#         if bowler["status"] != "resolved":
#             return {
#                 "template": "M4",
#                 "status": "bowler_resolution_failed",
#                 "query": query,
#                 "resolution": bowler
#             }

#         pipeline = get_m4_template(
#             batter_name=batter["resolved_name"],
#             bowler_name=bowler["resolved_name"],
#             limit_n=query.get("limit", 5)
#         )

#         result = execute_pipeline(pipeline)

#         return {
#             "template": "M4",
#             "status": "success",
#             "batter": {
#                 "requested": query["batter"],
#                 "resolved": batter["resolved_name"],
#                 "team": query["batter_team"]
#             },
#             "bowler": {
#                 "requested": query["bowler"],
#                 "resolved": bowler["resolved_name"],
#                 "team": query["bowler_team"]
#             },
#             "limit": query.get("limit", 5),
#             "stats": result
#         }

#     # ==================================================
#     # M5 : Team vs Team
#     # ==================================================

#     if template == "M5":

#         pipeline = get_m5_template(
#             team1=query["team1"],
#             team2=query["team2"],
#             limit_n=query.get("limit")
#         )

#         result = execute_pipeline(pipeline)

#         return {
#             "template": "M5",
#             "status": "success",
#             "team1": query["team1"],
#             "team2": query["team2"],
#             "limit": query.get("limit"),
#             "stats": result[0] if result else {}
#         }

#     # ==================================================
#     # Unknown
#     # ==================================================

#     return {
#         "template": template,
#         "status": "unknown_template"
#     }
# ==================================================
# VENUE REQUEST
# ==================================================

# def process_venue_request(request, llm):
#     """
#     Venue NL request -> Mongo pipeline -> result.
#     """
#     print("\n" + "=" * 80)
#     print("[VENUE DATABASE REQUEST]")
#     print("=" * 80)
#     print(request)

#     pipeline = generate_mongo_pipeline(request, llm)
#     result = execute_pipeline(pipeline)

#     return {
#         "status": "success",
#         "request": request,
#         "pipeline": pipeline,
#         "result": result
#     }


# ==================================================
# MAIN MONGO AGENT
# ==================================================

# def run_mongo_agent(state):
#     """
#     MongoDB execution agent.
#     Executes deterministic template pipelines.
#     """

#     # print("\n" + "=" * 100)
#     # print("MONGO QUERY AGENT START")
#     # print("=" * 100)

#     mongo_results = {
#         "player": [],
#         "matchup": [],
#         "venue": [],
#         "external": []
#     }

#     schedule = state.get("schedule", {})

#     # ==================================================
#     # PLAYER TEMPLATES
#     # ==================================================

#     player_queries = state.get("player_db_queries", [])

#     # print(f"\nPlayer template queries: {len(player_queries)}")

#     for query in player_queries:

#         try:
#             result = process_player_request(
#                 query=query,
#                 schedule=schedule
#             )

#             mongo_results["player"].append(result)

#         except Exception as e:

#             mongo_results["player"].append({
#                 "status": "error",
#                 "query": query,
#                 "error": str(e)
#             })

#     # ==================================================
#     # MATCHUP TEMPLATES
#     # ==================================================

#     # ==================================================
#     # MATCHUP TEMPLATES
#     # ==================================================

#     # ==================================================
#     # MATCHUPS
#     # ==================================================

#     matchup_queries = state.get("matchup_queries", [])
#     schedule = state.get("schedule", {})

#     print(f"\nMatchup queries: {len(matchup_queries)}")

#     for query in matchup_queries:

#         try:
#             result = process_matchup(
#                 query=query,
#                 schedule=schedule
#             )

#             mongo_results["matchup"].append(result)

#         except Exception as e:

#             mongo_results["matchup"].append({
#                 "status": "error",
#                 "query": query,
#                 "error": str(e)
#             })
#     # ==================================================
#     # VENUE TEMPLATES
#     # ==================================================

#     venue_queries = state.get("venue_queries", [])

#     print(f"\nVenue template queries: {len(venue_queries)}")

#     for query in venue_queries:

#         try:
#             result = process_venue_request(
#                 query=query
#             )

#             mongo_results["venue"].append(result)

#         except Exception as e:

#             mongo_results["venue"].append({
#                 "status": "error",
#                 "query": query,
#                 "error": str(e)
#             })

#     # ==================================================
#     # EXTERNAL REQUESTS
#     # ==================================================

#     mongo_results["external"] = state.get(
#         "weather_requests",
#         []
#     )

#     # ==================================================
#     # LOGS
#     # ==================================================

#     print("\n" + "=" * 100)
#     print("MONGO QUERY AGENT COMPLETE")
#     print("=" * 100)

#     print(f"Player  : {len(mongo_results['player'])}")
#     print(f"Matchup : {len(mongo_results['matchup'])}")
#     print(f"Venue   : {len(mongo_results['venue'])}")

#     return {
#         "mongo_results": mongo_results
#     }


# ==================================================
# OPTIONAL DIRECT TEST
# ==================================================

if __name__ == "__main__":
    print("\n" + "=" * 100)
    print("PLAYER RESOLUTION TEST")
    print("=" * 100)

    tests = [
        ("Steve Smith", "Australia"),
        ("Shubman Gill", "India"),
        ("Virat Kohli", "India"),
    ]

    for name, team in tests:
        result = resolve_player(name, team)
        print(json.dumps(result, indent=2, ensure_ascii=False))