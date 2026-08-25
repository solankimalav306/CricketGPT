from prompt_loader import load_prompt
from state import CricketState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
import json
import re
from db import resolve_player

def matchup_agent(state: CricketState, llm):

    print("\n" + "=" * 80)
    print("[MATCHUP AGENT]")
    print("=" * 80)

    # --------------------------------------------------
    # Planner task
    # --------------------------------------------------

    matchup_task = next(
        (
            step for step in state["plan"]
            if step["agent"].lower() == "matchup agent"
        ),
        None
    )

    if matchup_task is None:
        return {"matchup_queries": []}

    task = matchup_task["task"]

    print("Task:")
    print(task)

    # --------------------------------------------------
    # LLM Reasoning
    # --------------------------------------------------

    system_prompt = load_prompt("matchup")

    squads = state.get("schedule", {}).get("squads", {})

    llm_input = (
        {"task": task, "squads": squads}
        if squads
        else task
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=json.dumps(llm_input, ensure_ascii=False)
            if isinstance(llm_input, dict)
            else llm_input
        )
    ])

    content = response.content

    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            if isinstance(part, dict)
            else str(part)
            for part in content
        )

    content = (
        content
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )

    reasoning = json.loads(content)["queries"]

    print(f"Reasoning templates: {len(reasoning)}")
    for r in reasoning:
        print(f"  -> Template={r.get('template')} | batter={r.get('batter')} | bowler={r.get('bowler')} | player={r.get('player')}")

    # --------------------------------------------------
    # Squad maps (Safe check to avoid KeyError)
    # --------------------------------------------------

    schedule = state.get("schedule")
    if not schedule:
        schedule = {
            "squads": {},
            "matches": []
        }

    squads = schedule.get("squads", {})

    teams = []
    batters = {}
    bowlers = {}

    for squad in squads.values():

        team = squad["teamName"]
        teams.append(team)

        batters[team] = []
        bowlers[team] = []

        for player in squad["players"]:

            if player.get("isHeader"):
                continue

            role = player.get("role", "").lower()
            has_bowling = player.get("bowlingStyle")

            if (
                "batsman" in role
                or "batter" in role
                or "allrounder" in role
            ):
                batters[team].append(player["name"])

            if role == "bowler" or ("allrounder" in role and has_bowling):
                bowlers[team].append(player["name"])

    # Helper to detect teams from query strings when schedule is absent
    def detect_teams(text):
        supported_teams = [
            "India", "Australia", "England", "South Africa", "New Zealand", 
            "Pakistan", "Sri Lanka", "West Indies", "Bangladesh", "Afghanistan", 
            "Zimbabwe", "Ireland"
        ]
        found = []
        for t in supported_teams:
            if re.search(r'\b' + re.escape(t) + r'\b', text, re.IGNORECASE):
                found.append(t)
        return found

    # --------------------------------------------------
    # Deterministic expansion
    # --------------------------------------------------

    queries = []

    for q in reasoning:

        template = q["template"]

        # ---------------- M1 & M4 ----------------

        if template in ("M1", "M4"):

            batter = q.get("batter")
            bowler = q.get("bowler")

            # Case A: Both players are explicitly specified (direct matchup)
            if batter and bowler:
                bat_res = resolve_player(batter)
                bow_res = resolve_player(bowler)
                
                batter_team = bat_res.get("team") if bat_res["status"] == "resolved" else None
                bowler_team = bow_res.get("team") if bow_res["status"] == "resolved" else None
                
                if not batter_team:
                    found_teams = detect_teams(task)
                    if found_teams:
                        batter_team = found_teams[0]
                if not bowler_team:
                    found_teams = detect_teams(task)
                    if len(found_teams) > 1:
                        bowler_team = found_teams[1]
                    elif found_teams:
                        bowler_team = found_teams[0]
                
                queries.append({
                    "template": template,
                    "batter": batter,
                    "bowler": bowler,
                    "batter_team": batter_team or "India",
                    "bowler_team": bowler_team or "Australia",
                    "limit": q.get("limit", 5) if template == "M4" else None
                })
            
            # Case B: Only batter is specified (squad-based expansion fallback)
            elif batter:
                batter_team = None
                for t, players in batters.items():
                    if batter in players:
                        batter_team = t
                        break
                
                if not batter_team:
                    bat_res = resolve_player(batter)
                    if bat_res["status"] == "resolved":
                        batter_team = bat_res["team"]
                
                if batter_team:
                    opponents = [t for t in teams if t != batter_team]
                    if not opponents:
                        opponents = [t for t in detect_teams(task) if t != batter_team]
                    opponent = opponents[0] if opponents else None
                    
                    if opponent and opponent in bowlers:
                        for b in bowlers[opponent]:
                            queries.append({
                                "template": template,
                                "batter": batter,
                                "bowler": b,
                                "batter_team": batter_team,
                                "bowler_team": opponent,
                                "limit": q.get("limit", 5) if template == "M4" else None
                            })

        # ---------------- M2 ----------------

        elif template == "M2":

            bowler = q.get("bowler")
            batter = q.get("batter")

            # Case A: Both players are specified
            if bowler and batter:
                bow_res = resolve_player(bowler)
                bat_res = resolve_player(batter)
                
                bowler_team = bow_res.get("team") if bow_res["status"] == "resolved" else None
                batter_team = bat_res.get("team") if bat_res["status"] == "resolved" else None
                
                if not bowler_team:
                    found_teams = detect_teams(task)
                    if found_teams:
                        bowler_team = found_teams[0]
                if not batter_team:
                    found_teams = detect_teams(task)
                    if len(found_teams) > 1:
                        batter_team = found_teams[1]
                    elif found_teams:
                        batter_team = found_teams[0]
                
                queries.append({
                    "template": "M2",
                    "bowler": bowler,
                    "batter": batter,
                    "bowler_team": bowler_team or "India",
                    "batter_team": batter_team or "Australia"
                })
            
            # Case B: Only bowler is specified
            elif bowler:
                bowler_team = None
                for t, players in bowlers.items():
                    if bowler in players:
                        bowler_team = t
                        break
                        
                if not bowler_team:
                    bow_res = resolve_player(bowler)
                    if bow_res["status"] == "resolved":
                        bowler_team = bow_res["team"]
                        
                if bowler_team:
                    opponents = [t for t in teams if t != bowler_team]
                    if not opponents:
                        opponents = [t for t in detect_teams(task) if t != bowler_team]
                    opponent = opponents[0] if opponents else None
                    
                    if opponent and opponent in batters:
                        for b in batters[opponent]:
                            queries.append({
                                "template": "M2",
                                "bowler": bowler,
                                "batter": b,
                                "bowler_team": bowler_team,
                                "batter_team": opponent
                            })

        # ---------------- M3 ----------------

        elif template == "M3":

            player = q["player"]
            role = q["role"]

            player_team = None
            if role == "batting":
                for t, players in batters.items():
                    if player in players:
                        player_team = t
                        break
            else:
                for t, players in bowlers.items():
                    if player in players:
                        player_team = t
                        break

            if not player_team:
                p_res = resolve_player(player)
                if p_res["status"] == "resolved":
                    player_team = p_res["team"]

            if not player_team:
                player_team = "India" # Fallback
                
            opponents = [t for t in teams if t != player_team]
            if not opponents:
                opponents = [t for t in detect_teams(task) if t != player_team]
            opponent = opponents[0] if opponents else "Australia"

            queries.append({
                "template": "M3",
                "player": player,
                "player_team": player_team,
                "opponent_team": opponent,
                "role": role
            })

        # ---------------- M5 ----------------

        elif template == "M5":
            
            t1, t2 = None, None
            if len(teams) >= 2:
                t1, t2 = teams[0], teams[1]
            else:
                found = detect_teams(task)
                if len(found) >= 2:
                    t1, t2 = found[0], found[1]
                elif found:
                    t1 = found[0]
                    t2 = "Australia" if t1 != "Australia" else "India"
                else:
                    t1, t2 = "India", "Australia"

            queries.append({
                "template": "M5",
                "team1": t1,
                "team2": t2,
                "limit": q.get("limit")
            })

    print(f"Expanded matchup queries: {len(queries)}")

    return {
        "matchup_queries": queries
    }
