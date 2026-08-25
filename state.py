from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, MessagesState, START, END, add_messages

class CricketState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str
    current_step: int
    plan: list[dict]
    schedule: dict
    evidence: dict
    response: str
    search_results: list[dict]
    queries: list[str]
    player_db_queries: list[dict]
    matchup_queries: list[dict]
    venue_queries: list[dict]
    weather_requests: list[dict]
    mongo_results: dict
    news_results: list
    news_queries: list[str]
    weather_results: list[dict]
    final_answer: str
    final_html: str 