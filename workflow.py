# import re

from langgraph.graph import StateGraph, MessagesState, START, END, add_messages
# from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
# from typing_extensions import TypedDict, Annotated
# import json
# import os
# from ddgs import DDGS
# from db import run_mongo_agent
# from news import fetch_player_news
# from prompt_loader import load_prompt
# from venue import venue_agent as run_venue_agent
# from db import resolve_player

# from weather_fetcher import get_weather
from logger import write_pipeline_log

from state import CricketState

from agents.planner import planner_node
from agents.scheduler import scheduler_node
from agents.matchup import matchup_agent
from agents.mongo_agent import mongo_agent_node
from agents.player import player_agent_node
from agents.weather import weather_agent_node
from agents.venue import venue_agent_node
from agents.analysis_join_node import analysis_join_node
from agents.news import news_agent
from agents.final_reasoning_agent import final_reasoning_agent
from agents.presentation_agent import presentation_agent_node
from agents.executor import executor_node, route_from_executor

load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)
# class CricketState(TypedDict):
#     messages: Annotated[list, add_messages]
#     intent: str
#     current_step: int
#     plan: list[dict]
#     schedule: dict
#     evidence: dict
#     response: str
#     search_results: list[dict]
#     queries: list[str]
#     player_db_queries: list[dict]
#     matchup_queries: list[dict]
#     venue_queries: list[dict]
#     weather_requests: list[dict]
#     mongo_results: dict
#     news_results: list
#     weather_results: list[dict]
#     final_answer: str
#     final_html: str  # Added for Angular innerHTML presentation


# ------------------------
# Node 1 : Planner Node
# ------------------------
# def planner_node(state: CricketState):
#     system_prompt = load_prompt("planner")
#     user_message = state["messages"][-1].content
#     print(f"[Planner Node] Received: {user_message}")
#     response = llm.invoke([SystemMessage(content=system_prompt)]+state["messages"])
#     planner_output = json.loads(response.content[0]["text"])
#     # print(f"[Planner Node] Intent: {planner_output['intent']}")
#     # print(f"[Planner Node] Plan: {planner_output['plan']}")
#     state["intent"] = planner_output["intent"]
#     state["plan"] = planner_output["plan"]
#     state["current_step"] = 0
#     return {
#         "intent": planner_output["intent"],
#         "plan": planner_output["plan"],
#         "current_step": 0
#     }


# ------------------------
# Node 2 : Scheduler Node
# ------------------------
# def scheduler_node(state: CricketState):
# ==================================================
# SERIES HELPERS
# ==================================================

# def extract_series_id(url):

#     match = re.search(
#         r"/cricket-series/(\d+)",
#         url
#     )

#     if not match:
#         return None

#     return int(match.group(1))

# def find_series_by_teams(
#     teams,
#     series_list
# ):

#     if len(teams) != 2:
#         return None

#     team1 = teams[0].lower()
#     team2 = teams[1].lower()

#     for series in series_list:

#         name = series["name"].lower()

#         if (
#             team1 in name
#             and team2 in name
#         ):

#             series_id = extract_series_id(
#                 series["url"]
#             )

#             if series_id is not None:

#                 return {
#                     "seriesId": series_id,
#                     "name": series["name"],
#                     "url": series["url"]
#                 }

#     return None

# def scheduler_node(state: CricketState):

#     print("\n" + "=" * 70)
#     print("[Scheduler Node]")
#     print("=" * 70)

#     # --------------------------------------------------
#     # Get scheduler task from planner
#     # --------------------------------------------------

#     scheduler_task = next(
#         (
#             item
#             for item in state["plan"]
#             if item["agent"] == "scheduler"
#         ),
#         None
#     )

#     if scheduler_task is None:

#         raise ValueError(
#             "Scheduler task not found in planner output."
#         )

#     task = scheduler_task["task"]

#     teams = scheduler_task.get(
#         "teams",
#         []
#     )

#     print("[Scheduler] Task:", task)
#     print("[Scheduler] Teams:", teams)

#     # --------------------------------------------------
#     # Fetch series catalogue
#     # --------------------------------------------------

#     print(
#         "\n[Scheduler] Fetching future series..."
#     )

#     future_series = get_future_series()

#     print(
#         "[Scheduler] Future series:",
#         len(future_series)
#     )

#     print(
#         "\n[Scheduler] Fetching past series..."
#     )

#     past_series = get_past_series()

#     print(
#         "[Scheduler] Past series:",
#         len(past_series)
#     )

#     all_series = (
#         future_series +
#         past_series
#     )

#     # --------------------------------------------------
#     # Remove duplicate series
#     # --------------------------------------------------

#     unique_series = {}

#     for series in all_series:

#         series_id = extract_series_id(
#             series["url"]
#         )

#         if series_id is not None:

#             unique_series[series_id] = {
#                 **series,
#                 "seriesId": series_id
#             }

#     all_series = list(
#         unique_series.values()
#     )

#     print(
#         "[Scheduler] Unique series:",
#         len(all_series)
#     )

#     # --------------------------------------------------
#     # Resolve opponents
#     # --------------------------------------------------

#     if len(teams) == 2:

#         print(
#             "[Scheduler] Opponents already "
#             "provided by planner."
#         )

#     else:

#         print(
#             "[Scheduler] Opponents unavailable."
#         )

#         # Searcher fallback
#         teams = find_opponents(task)

#         if not teams:

#             raise ValueError(
#                 "Could not determine opponents."
#             )

#     # --------------------------------------------------
#     # Resolve series
#     # --------------------------------------------------

#     series = find_series_by_teams(
#         teams,
#         all_series
#     )

#     if series is None:

#         raise ValueError(
#             f"Could not find series for teams: "
#             f"{teams}"
#         )

#     print(
#         "\n[Scheduler] Series resolved:"
#     )

#     print(
#         f"  {series['name']}"
#     )

#     print(
#         f"  Series ID: {series['seriesId']}"
#     )

#     # --------------------------------------------------
#     # Fetch complete series graph
#     # --------------------------------------------------

#     print(
#         "\n[Scheduler] Fetching complete "
#         "series data..."
#     )

#     series_data = fetch_series_graph(
#         series["seriesId"]
#     )

#     # --------------------------------------------------
#     # Return to graph state
#     # --------------------------------------------------

#     return {
#         "schedule": series_data
#     }



# def player_agent_node(state, llm):

#     print("\n" + "=" * 80)
#     print("[PLAYER AGENT]")
#     print("=" * 80)

#     # --------------------------------------------------
#     # Find player-agent task from planner
#     # --------------------------------------------------

#     player_task = next(
#         (
#             item
#             for item in state["plan"]
#             if item["agent"].lower() == "player agent"
#         ),
#         None
#     )

#     if player_task is None:

#         print("[Player Agent] No player task found.")

#         return {
#             "player_db_queries": []
#         }

#     task = player_task["task"]

#     print("[Player Agent] Task:")
#     print(task)


#     # --------------------------------------------------
#     # System prompt
#     # --------------------------------------------------

#     system_prompt = load_prompt("player")

#     # --------------------------------------------------
#     # Ask LLM to generate database requirements
#     # --------------------------------------------------

#     response = llm.invoke(
#         [
#             SystemMessage(
#                 content=system_prompt
#             ),
#             HumanMessage(
#                 content=task
#             )
#         ]
#     )


#     # --------------------------------------------------
#     # Parse response
#     # --------------------------------------------------

#     try:

#         content = response.content

#         if isinstance(content, list):
#             content = "".join(
#                 part.get("text", "")
#                 if isinstance(part, dict)
#                 else str(part)
#                 for part in content
#             )

#         # Remove markdown code fences if present
#         content = content.strip()

#         if content.startswith("```"):
#             content = content.replace("```json", "", 1)
#             content = content.replace("```", "")
#             content = content.strip()

#         result = json.loads(content)

#     except Exception as e:

#         print("[Player Agent] Failed to parse output:")
#         print(e)

#         print("[Player Agent] Raw response:")
#         print(content)

#         return {
#             "player_db_queries": []
#         }

#     queries = result.get("queries", [])


#     # --------------------------------------------------
#     # Logs
#     # --------------------------------------------------

#     print(
#         "\n[Player Agent] Generated queries:"
#     )

#     for i, query in enumerate(
#         queries,
#         start=1
#     ):

#         print(
#             f"{i}. {query}"
#         )


#     print(
#         "\n[Player Agent] Total queries:",
#         len(queries)
#     )


#     # --------------------------------------------------
#     # Return to graph
#     # --------------------------------------------------

#     return {
#         "player_db_queries": queries
#     }


# def matchup_agent(state: CricketState, llm):

#     print("\n" + "=" * 80)
#     print("[MATCHUP AGENT]")
#     print("=" * 80)

#     # --------------------------------------------------
#     # Planner task
#     # --------------------------------------------------

#     matchup_task = next(
#         (
#             step for step in state["plan"]
#             if step["agent"].lower() == "matchup agent"
#         ),
#         None
#     )

#     if matchup_task is None:
#         return {"matchup_queries": []}

#     task = matchup_task["task"]

#     print("Task:")
#     print(task)

#     # --------------------------------------------------
#     # LLM Reasoning
#     # --------------------------------------------------

#     system_prompt = load_prompt("matchup")

#     response = llm.invoke([
#         SystemMessage(content=system_prompt),
#         HumanMessage(content=task)
#     ])

#     content = response.content

#     if isinstance(content, list):
#         content = "".join(
#             part.get("text", "")
#             if isinstance(part, dict)
#             else str(part)
#             for part in content
#         )

#     content = (
#         content
#         .replace("```json", "")
#         .replace("```", "")
#         .strip()
#     )

#     reasoning = json.loads(content)["queries"]

#     print(f"Reasoning templates: {len(reasoning)}")

#     # --------------------------------------------------
#     # Squad maps (Safe check to avoid KeyError)
#     # --------------------------------------------------

#     schedule = state.get("schedule")
#     if not schedule:
#         schedule = {
#             "squads": {},
#             "matches": []
#         }
#         state["schedule"] = schedule

#     squads = schedule.get("squads", {})

#     teams = []
#     batters = {}
#     bowlers = {}

#     for squad in squads.values():

#         team = squad["teamName"]
#         teams.append(team)

#         batters[team] = []
#         bowlers[team] = []

#         for player in squad["players"]:

#             if player.get("isHeader"):
#                 continue

#             role = player.get("role", "").lower()
#             has_bowling = player.get("bowlingStyle")

#             if (
#                 "batsman" in role
#                 or "batter" in role
#                 or "allrounder" in role
#             ):
#                 batters[team].append(player["name"])

#             if role == "bowler" or ("allrounder" in role and has_bowling):
#                 bowlers[team].append(player["name"])

#     # Helper to detect teams from query strings when schedule is absent
#     def detect_teams(text):
#         supported_teams = [
#             "India", "Australia", "England", "South Africa", "New Zealand", 
#             "Pakistan", "Sri Lanka", "West Indies", "Bangladesh", "Afghanistan", 
#             "Zimbabwe", "Ireland"
#         ]
#         found = []
#         for t in supported_teams:
#             if re.search(r'\b' + re.escape(t) + r'\b', text, re.IGNORECASE):
#                 found.append(t)
#         return found

#     # --------------------------------------------------
#     # Deterministic expansion
#     # --------------------------------------------------

#     queries = []

#     for q in reasoning:

#         template = q["template"]

#         # ---------------- M1 & M4 ----------------

#         if template in ("M1", "M4"):

#             batter = q.get("batter")
#             bowler = q.get("bowler")

#             # Case A: Both players are explicitly specified (direct matchup)
#             if batter and bowler:
#                 bat_res = resolve_player(batter)
#                 bow_res = resolve_player(bowler)
                
#                 batter_team = bat_res.get("team") if bat_res["status"] == "resolved" else None
#                 bowler_team = bow_res.get("team") if bow_res["status"] == "resolved" else None
                
#                 if not batter_team:
#                     found_teams = detect_teams(task)
#                     if found_teams:
#                         batter_team = found_teams[0]
#                 if not bowler_team:
#                     found_teams = detect_teams(task)
#                     if len(found_teams) > 1:
#                         bowler_team = found_teams[1]
#                     elif found_teams:
#                         bowler_team = found_teams[0]
                
#                 queries.append({
#                     "template": template,
#                     "batter": batter,
#                     "bowler": bowler,
#                     "batter_team": batter_team or "India",
#                     "bowler_team": bowler_team or "Australia",
#                     "limit": q.get("limit", 5) if template == "M4" else None
#                 })
            
#             # Case B: Only batter is specified (squad-based expansion fallback)
#             elif batter:
#                 batter_team = None
#                 for t, players in batters.items():
#                     if batter in players:
#                         batter_team = t
#                         break
                
#                 if not batter_team:
#                     bat_res = resolve_player(batter)
#                     if bat_res["status"] == "resolved":
#                         batter_team = bat_res["team"]
                
#                 if batter_team:
#                     opponents = [t for t in teams if t != batter_team]
#                     if not opponents:
#                         opponents = [t for t in detect_teams(task) if t != batter_team]
#                     opponent = opponents[0] if opponents else None
                    
#                     if opponent and opponent in bowlers:
#                         for b in bowlers[opponent]:
#                             queries.append({
#                                 "template": template,
#                                 "batter": batter,
#                                 "bowler": b,
#                                 "batter_team": batter_team,
#                                 "bowler_team": opponent,
#                                 "limit": q.get("limit", 5) if template == "M4" else None
#                             })

#         # ---------------- M2 ----------------

#         elif template == "M2":

#             bowler = q.get("bowler")
#             batter = q.get("batter")

#             # Case A: Both players are specified
#             if bowler and batter:
#                 bow_res = resolve_player(bowler)
#                 bat_res = resolve_player(batter)
                
#                 bowler_team = bow_res.get("team") if bow_res["status"] == "resolved" else None
#                 batter_team = bat_res.get("team") if bat_res["status"] == "resolved" else None
                
#                 if not bowler_team:
#                     found_teams = detect_teams(task)
#                     if found_teams:
#                         bowler_team = found_teams[0]
#                 if not batter_team:
#                     found_teams = detect_teams(task)
#                     if len(found_teams) > 1:
#                         batter_team = found_teams[1]
#                     elif found_teams:
#                         batter_team = found_teams[0]
                
#                 queries.append({
#                     "template": "M2",
#                     "bowler": bowler,
#                     "batter": batter,
#                     "bowler_team": bowler_team or "India",
#                     "batter_team": batter_team or "Australia"
#                 })
            
#             # Case B: Only bowler is specified
#             elif bowler:
#                 bowler_team = None
#                 for t, players in bowlers.items():
#                     if bowler in players:
#                         bowler_team = t
#                         break
                        
#                 if not bowler_team:
#                     bow_res = resolve_player(bowler)
#                     if bow_res["status"] == "resolved":
#                         bowler_team = bow_res["team"]
                        
#                 if bowler_team:
#                     opponents = [t for t in teams if t != bowler_team]
#                     if not opponents:
#                         opponents = [t for t in detect_teams(task) if t != bowler_team]
#                     opponent = opponents[0] if opponents else None
                    
#                     if opponent and opponent in batters:
#                         for b in batters[opponent]:
#                             queries.append({
#                                 "template": "M2",
#                                 "bowler": bowler,
#                                 "batter": b,
#                                 "bowler_team": bowler_team,
#                                 "batter_team": opponent
#                             })

#         # ---------------- M3 ----------------

#         elif template == "M3":

#             player = q["player"]
#             role = q["role"]

#             player_team = None
#             if role == "batting":
#                 for t, players in batters.items():
#                     if player in players:
#                         player_team = t
#                         break
#             else:
#                 for t, players in bowlers.items():
#                     if player in players:
#                         player_team = t
#                         break

#             if not player_team:
#                 p_res = resolve_player(player)
#                 if p_res["status"] == "resolved":
#                     player_team = p_res["team"]

#             if not player_team:
#                 player_team = "India" # Fallback
                
#             opponents = [t for t in teams if t != player_team]
#             if not opponents:
#                 opponents = [t for t in detect_teams(task) if t != player_team]
#             opponent = opponents[0] if opponents else "Australia"

#             queries.append({
#                 "template": "M3",
#                 "player": player,
#                 "player_team": player_team,
#                 "opponent_team": opponent,
#                 "role": role
#             })

#         # ---------------- M5 ----------------

#         elif template == "M5":
            
#             t1, t2 = None, None
#             if len(teams) >= 2:
#                 t1, t2 = teams[0], teams[1]
#             else:
#                 found = detect_teams(task)
#                 if len(found) >= 2:
#                     t1, t2 = found[0], found[1]
#                 elif found:
#                     t1 = found[0]
#                     t2 = "Australia" if t1 != "Australia" else "India"
#                 else:
#                     t1, t2 = "India", "Australia"

#             queries.append({
#                 "template": "M5",
#                 "team1": t1,
#                 "team2": t2,
#                 "limit": q.get("limit")
#             })

#     print(f"Expanded matchup queries: {len(queries)}")

#     return {
#         "matchup_queries": queries
#     }


# def venue_agent_node(state: CricketState, llm):

#     print("\n" + "=" * 80)
#     print("[VENUE AGENT]")
#     print("=" * 80)

#     # 1. Locate the venue-agent task from planner
#     venue_task = next(
#         (
#             step for step in state["plan"]
#             if step["agent"].lower() == "venue agent"
#         ),
#         None
#     )

#     if venue_task is None:
#         user_msg = state["messages"][-1].content if state.get("messages") else ""
#         task = f"Identify the venue and city from this message and retrieve stats: {user_msg}"
#     else:
#         task = venue_task["task"]

#     print("Task:")
#     print(task)

#     # 2. Try loading the venue prompt from file system or fallback to inline prompt
#     try:
#         system_prompt = load_prompt("venue")
#     except Exception:
#         system_prompt = """You are the Venue Statistics Agent in CricketGPT.

# Your ONLY responsibility is to convert the Planner Agent's task into a structured list of venue database queries and weather requests based on the specific requirements.

# You do NOT answer the user's question.
# You do NOT provide statistics.
# You do NOT make predictions.
# You do NOT write MongoDB queries.

# The database supports three specific venue templates:
# - V1: Overall historical match stats, win margins, and toss analysis (toss win vs match win ratio).
# - V2: Batting-specific conditions (average runs per wicket, average 1st and 2nd innings scores, boundary metrics).
# - V3: Pitch condition & bowling performance (pace vs spin wicket percentages, bowl-first vs bat-first trends).

# Rules:
# 1. Analyze the Planner's task and identify the target venue and city. If not explicitly mentioned, check the schedule/upcoming match context if available in the task.
# 2. Generate ONLY the specific venue templates (V1, V2, or V3) that are directly requested or necessary to answer the task. For example, if comparing batting conditions, request V2. If asking about pitch or bowling, request V3.
# 3. If the task requires weather details, generate a weather request with the correct city and date (format: YYYY-MM-DD). If no date is given, default to the current date "2026-08-24".
# 4. Return ONLY valid JSON.

# Return ONLY valid JSON in this format:

# {
#   "venue_queries": [
#     {
#       "template": "V1 | V2 | V3",
#       "venue": "Galle International Stadium",
#       "city": "Galle"
#     }
#   ],
#   "weather_request": {
#     "city": "Galle",
#     "date": "2026-08-24"
#   }
# }"""

#     # 3. Request structured venue requirements via LLM
#     try:
#         response = llm.invoke([
#             SystemMessage(content=system_prompt),
#             HumanMessage(content=task)
#         ])
#         content = response.content

#         if isinstance(content, list):
#             content = "".join(
#                 part.get("text", "") if isinstance(part, dict) else str(part)
#                 for part in content
#             )

#         content = (
#             content
#             .replace("```json", "")
#             .replace("```", "")
#             .strip()
#         )

#         parsed = json.loads(content)
#         venue_queries = parsed.get("venue_queries", [])
#         weather_request = parsed.get("weather_request")

#     except Exception as e:
#         print(f"[Venue Agent] LLM processing failed, applying safety fallback: {e}")
#         # Default safety fallback using simple heuristics
#         user_msg = state["messages"][-1].content if state.get("messages") else ""
#         venue_name = "Galle International Stadium"
#         city_name = "Galle"
#         for v, c in [
#             ("Galle", "Galle"), 
#             ("Lord's", "London"), 
#             ("The Oval", "London"), 
#             ("Melbourne", "Melbourne"), 
#             ("Sydney", "Sydney"), 
#             ("Wankhede", "Mumbai"), 
#             ("Eden Gardens", "Kolkata")
#         ]:
#             if v.lower() in user_msg.lower():
#                 venue_name = v
#                 city_name = c
#                 break

#         venue_queries = [
#             {"template": "V1", "venue": venue_name, "city": city_name},
#             {"template": "V2", "venue": venue_name, "city": city_name},
#             {"template": "V3", "venue": venue_name, "city": city_name}
#         ]
#         weather_request = {"city": city_name, "date": "2026-08-24"}

#     print(f"Venue queries : {len(venue_queries)}")
#     print("Weather request generated")

#     return {
#         "venue_queries": venue_queries,
#         "weather_requests": [weather_request] if weather_request else []
#     }
# def mongo_agent_node(state: CricketState):

#     print("\n" + "=" * 100)
#     print("[MONGO NODE]")
#     print("=" * 100)

#     return run_mongo_agent(
#         state
#     )

# def analysis_join_node(state):
#     print("\n[JOIN] Player + Matchup + Venue ready.")
#     return {}

# def weather_agent_node(state: CricketState):

#     print("\n" + "=" * 80)
#     print("[WEATHER AGENT]")
#     print("=" * 80)

#     requests = state.get("weather_requests", [])

#     if not requests:
#         print("No weather requests.")
#         return {"weather_results": []}

#     results = []

#     print(f"Weather requests: {len(requests)}")

#     for req in requests:

#         print(f"Fetching {req['city']} | {req['date']}")

#         try:
#             weather = get_weather(req)
#             results.append(weather)

#         except Exception as e:

#             print(f"Weather API Error: {e}")

#             results.append({
#                 "status": "error",
#                 "city": req["city"],
#                 "date": req["date"],
#                 "error": str(e)
#             })

#     return {
#         "weather_results": results
#     }
# # ------------------------
# # Node 2 : LLM Node
# # ------------------------
# def llm_node(state: CricketState):
#     user_message = state["messages"][-1].content
#     print(f"[LLM Node] Received: {user_message}")
#     response = llm.invoke(state["messages"])
#     return {
#         "messages": [response]
#     }


# def final_reasoning_agent(state, llm):

#     print("\n" + "=" * 80)
#     print("[FINAL REASONING AGENT]")
#     print("=" * 80)

#     intent = state["intent"]
#     question = state["messages"][-1].content

#     mongo = state.get("mongo_results", {})

#     evidence = {
#         "player": mongo.get("player", []),
#         "matchup": mongo.get("matchup", []),
#         "venue": mongo.get("venue", []),
#         "weather": state.get("weather_results", []),
#         "schedule": state.get("schedule", {}),
#         "news": state.get("news_results", [])
#     }

#     if intent == "prediction":
#         system_prompt = load_prompt("reason_prediction")
#     else:
#         system_prompt = load_prompt("reason_analysis")

#     response = llm.invoke([
#         SystemMessage(content=system_prompt),
#         HumanMessage(
#             content=json.dumps({
#                 "question": question,
#                 "evidence": evidence
#             }, indent=2, ensure_ascii=False)
#         )
#     ])

#     return {
#         "final_answer": response.content
#     }

# ------------------------
# Node 2 : Static Node
# ------------------------
# def static_node(state: CricketState):
#     last_message = state["messages"][-1].content
#     print(f"[Static Node] Received: {last_message}")
#     return {
#         "messages": [
#             AIMessage(content="Static Agent says: Workflow Complete!")
#         ]
#     }

# def route_from_executor(state):
#     plan = state.get("plan", [])
    
#     # Since executor_node already incremented current_step, we must subtract 1
#     # to route to the correct agent for the CURRENT step.
#     idx = state.get("current_step", 1) - 1

#     # If we have finished all steps in the plan, move to mongo
#     if idx >= len(plan):
#         return "mongo_agent"

#     agent = plan[idx]["agent"].lower()

#     mapping = {
#         "scheduler": "scheduler",
#         "player agent": "player_agent",
#         "matchup agent": "matchup_agent",
#         "venue agent": "venue_agent",
#         "weather agent": "weather_agent",
#         "mongo agent": "mongo_agent",
#         "news agent": "news_agent"
#     }

#     # Safely route to the agent, fallback to mongo_agent if unrecognized
#     return mapping.get(agent, "mongo_agent")

# def executor_node(state):
#     idx = state.get("current_step", 0)
#     plan = state.get("plan", [])

#     if idx < len(plan):
#         step = plan[idx]
#         print(f"\n[EXECUTOR] Step {idx+1}/{len(plan)}: Routing to {step['agent'].upper()}...")
#     else:
#         print("\n[EXECUTOR] Plan complete. Routing to final agents.")

#     # Increment the step so the NEXT time we hit executor, it moves forward
#     return {
#         "current_step": idx + 1
#     }

# import json
# from langchain_core.messages import HumanMessage, SystemMessage

# from prompts import load_prompt


# def news_agent(state, llm):

#     print("\n" + "=" * 80)
#     print("[NEWS AGENT]")
#     print("=" * 80)

#     # --------------------------------------------------
#     # Find planner task
#     # --------------------------------------------------

#     task = next(
#         (
#             step
#             for step in state["plan"]
#             if step["agent"].lower() == "news agent"
#         ),
#         None
#     )

#     if task is None:

#         print("No news task.")

#         return {
#             "news_queries": []
#         }

#     entities = task.get(
#         "entities",
#         {}
#     )

#     players = entities.get("players", [])
#     teams = entities.get("teams", [])

#     # --------------------------------------------------
#     # Expand team -> squad players if available
#     # --------------------------------------------------

#     squads = state.get("schedule", {}).get("squads", {})

#     if teams and squads:

#         for squad in squads.values():

#             if squad["teamName"] not in teams:
#                 continue

#             for player in squad["players"]:

#                 if player.get("isHeader"):
#                     continue

#                 players.append(player["name"])

#     players = sorted(set(players))

#     print("Players for news:", players)
#     print("Teams:", teams)

#     # --------------------------------------------------
#     # LLM -> search queries
#     # --------------------------------------------------

#     system_prompt = load_prompt("news")

#     response = llm.invoke([
#         SystemMessage(content=system_prompt),
#         HumanMessage(
#             content=json.dumps(
#                 {
#                     "players": players,
#                     "teams": teams
#                 }
#             )
#         )
#     ])

#     content = response.content

#     if isinstance(content, list):

#         content = "".join(
#             part.get("text", "")
#             if isinstance(part, dict)
#             else str(part)
#             for part in content
#         )

#     content = (
#         content
#         .replace("```json", "")
#         .replace("```", "")
#         .strip()
#     )

#     result = json.loads(content)

#     queries = result.get("queries", [])

#    # --------------------------------------------------
#     # Execute DuckDuckGo News
#     # --------------------------------------------------

#     news_results = []
#     seen_urls = set()

#     with DDGS() as ddgs:

#         for query in queries:

#             try:
#                 results = ddgs.news(
#                     query=query,
#                     max_results=5
#                 )

#                 for item in results:

#                     title = item.get("title", "")
#                     url = item.get("url")

#                     # Skip duplicates
#                     if not url or url in seen_urls:
#                         continue

#                     # Ignore previews / fantasy articles
#                     lower = title.lower()

#                     if any(
#                         word in lower
#                         for word in [
#                             "match preview",
#                             "preview:",
#                             "dream11",
#                             "fantasy",
#                             "predicted xi",
#                             "prediction"
#                         ]
#                     ):
#                         continue

#                     seen_urls.add(url)

#                     news_results.append({
#                         "query": query,
#                         "title": title,
#                         "source": item.get("source"),
#                         "date": item.get("date"),
#                         "url": url
#                     })

#             except Exception as e:
#                 print(f"[News] Failed: {query} -> {e}")

#     print(f"Generated {len(queries)} search queries")
#     print(f"Fetched {len(news_results)} news articles")

#     return {
#         "news_queries": queries,
#         "news_results": news_results
#     }


# def presentation_agent_node(state: CricketState, llm):

#     print("\n" + "=" * 80)
#     print("[PRESENTATION AGENT]")
#     print("=" * 80)

#     final_answer = state.get("final_answer", "")
#     mongo_results = state.get("mongo_results", {})

#     system_prompt = load_prompt("presentation")

#     task_data = {
#         "final_analysis": final_answer,
#         "raw_mongo_data": mongo_results
#     }

#     try:
#         response = llm.invoke([
#             SystemMessage(content=system_prompt),
#             HumanMessage(content=json.dumps(task_data, indent=2, ensure_ascii=False))
#         ])
#         content = response.content

#         if isinstance(content, list):
#             content = "".join(
#                 part.get("text", "") if isinstance(part, dict) else str(part)
#                 for part in content
#             )

#         # Sanitize any accidental markdown code wrappers
#         content = (
#             content
#             .replace("```html", "")
#             .replace("```", "")
#             .strip()
#         )

#     except Exception as e:
#         print(f"[Presentation Agent] Error generating presentation layout: {e}")
#         # Clean default HTML fallback
#         content = f"""<div class="p-6 bg-white border border-slate-100 rounded-2xl shadow-sm">
#             <h2 class="text-xl font-semibold text-slate-800 mb-4">Cricket Analysis</h2>
#             <div class="prose max-w-none text-slate-600">
#                 {final_answer.replace('\\n', '<br>')}
#             </div>
#         </div>"""

#     return {
#         "final_html": content
#     }

# ------------------------
# Build Graph
# ------------------------
graph = StateGraph(CricketState)
graph.add_node("planner", lambda state: planner_node(state, llm))
graph.add_node("executor", executor_node)

graph.add_node("scheduler", scheduler_node)
graph.add_node("player_agent",lambda state: player_agent_node(state, llm))
graph.add_node("matchup_agent", lambda state: matchup_agent(state, llm))
# graph.add_node("venue_agent", venue_agent)
graph.add_node("venue_agent", lambda state: venue_agent_node(state, llm))
graph.add_node("analysis_join_node", analysis_join_node)
graph.add_node("mongo_agent", mongo_agent_node)
graph.add_node("weather_agent", weather_agent_node)
graph.add_node("final_reasoning_agent", lambda state: final_reasoning_agent(state, llm))
graph.add_node("presentation_agent", lambda state: presentation_agent_node(state, llm))
graph.add_node("news_agent", lambda state: news_agent(state, llm))
# graph.add_node("search", search_node)


graph.add_edge(START, "planner")
graph.add_edge("planner", "executor")
graph.add_conditional_edges(
    "executor",
    route_from_executor,
    {
        "scheduler": "scheduler",
        "player_agent": "player_agent",
        "matchup_agent": "matchup_agent",
        "venue_agent": "venue_agent",
        "weather_agent": "weather_agent",
        "mongo_agent": "mongo_agent",
        "news_agent": "news_agent"
    },
)
graph.add_edge("scheduler", "executor")
graph.add_edge("player_agent", "executor")
graph.add_edge("matchup_agent", "executor")
graph.add_edge("venue_agent", "executor")
graph.add_edge("weather_agent", "executor")
graph.add_edge("news_agent", "executor")
graph.add_edge("mongo_agent", "final_reasoning_agent")
graph.add_edge("final_reasoning_agent", "presentation_agent")
graph.add_edge("presentation_agent", END)
# graph.add_edge("planner", "scheduler")
# graph.add_edge("scheduler","player_agent")
# graph.add_edge("scheduler","matchup_agent")
# graph.add_edge("scheduler","venue_agent")
# graph.add_edge("player_agent", "analysis_join_node")
# graph.add_edge("matchup_agent", "analysis_join_node")
# # graph.add_edge("venue_agent", "analysis_join_node")
# graph.add_edge("venue_agent", "weather_agent")
# graph.add_edge("weather_agent", "analysis_join_node")
# graph.add_edge("analysis_join_node", "mongo_agent")
# graph.add_edge("mongo_agent", "final_reasoning_agent")
# graph.add_edge("final_reasoning_agent", END)

# graph.add_edge("planner", END)
app = graph.compile()

# ------------------------
# Run
# ------------------------
if __name__ == "__main__":
    result = app.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Visat Kohli against Pat Cummins? Who wins?"
                }
            ]
        }
    )
    # print("\nFinal Messages:\n")
    # for msg in result["messages"]:
    #     print(msg)

    write_pipeline_log(result)