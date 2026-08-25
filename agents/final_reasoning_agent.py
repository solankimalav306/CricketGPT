import re

from state import CricketState
from prompt_loader import load_prompt
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
import json


def final_reasoning_agent(state, llm):

    print("\n" + "=" * 80)
    print("[FINAL REASONING AGENT]")
    print("=" * 80)

    intent = state["intent"]
    question = state["messages"][-1].content

    mongo = state.get("mongo_results", {})

    evidence = {
        "player": mongo.get("player", []),
        "matchup": mongo.get("matchup", []),
        "venue": mongo.get("venue", []),
        "weather": state.get("weather_results", []),
        "schedule": state.get("schedule", {}),
        "news": state.get("news_results", [])
    }

    if intent == "prediction":
        system_prompt = load_prompt("reason_prediction")
    else:
        system_prompt = load_prompt("reason_analysis")

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=json.dumps({
                "question": question,
                "evidence": evidence
            }, indent=2, ensure_ascii=False)
        )
    ])

    return {
        "final_answer": response.content
    }