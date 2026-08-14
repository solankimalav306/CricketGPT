from langgraph.graph import StateGraph, MessagesState, START, END, add_messages
from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from typing_extensions import TypedDict, Annotated
import json
import os
from ddgs import DDGS
from prompt_loader import load_prompt
load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite"
)
class CricketState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str
    plan: list[dict]
    schedule: dict
    evidence: dict
    response: str
    search_results: list[dict]
    queries: list[str]


# ------------------------
# Node 1 : Planner Node
# ------------------------
def planner_node(state: CricketState):
    system_prompt = load_prompt("planner")
    user_message = state["messages"][-1].content
    print(f"[Planner Node] Received: {user_message}")
    response = llm.invoke([SystemMessage(content=system_prompt)]+state["messages"])
    planner_output = json.loads(response.content[0]["text"])
    # print(f"[Planner Node] Intent: {planner_output['intent']}")
    # print(f"[Planner Node] Plan: {planner_output['plan']}")
    state["intent"] = planner_output["intent"]
    state["plan"] = planner_output["plan"]
    return {
        "intent": planner_output["intent"],
        "plan": planner_output["plan"],
    }


# ------------------------
# Node 2 : Scheduler Node
# ------------------------
def scheduler_node(state: CricketState):
    


def search_node(state):

# ------------------------
# Node 2 : LLM Node
# ------------------------
def llm_node(state: CricketState):
    user_message = state["messages"][-1].content
    print(f"[LLM Node] Received: {user_message}")
    response = llm.invoke(state["messages"])
    return {
        "messages": [response]
    }


# ------------------------
# Node 2 : Static Node
# ------------------------
def static_node(state: CricketState):
    last_message = state["messages"][-1].content
    print(f"[Static Node] Received: {last_message}")
    return {
        "messages": [
            AIMessage(content="Static Agent says: Workflow Complete!")
        ]
    }
# ------------------------
# Build Graph
# ------------------------
graph = StateGraph(CricketState)
graph.add_node("planner", planner_node)
graph.add_node("scheduler", scheduler_node)
graph.add_node("search", search_node)


graph.add_edge(START, "planner")
graph.add_edge("planner", "scheduler")
graph.add_edge("scheduler", END)
app = graph.compile()
# ------------------------
# Run
# ------------------------
result = app.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "Who is the toughest bowler Travis Head will face in upcoming Bangladesh series?"
            }
        ]
    }
)
# print("\nFinal Messages:\n")
# for msg in result["messages"]:
#     print(msg)

print("\n========== AGENT CONVERSATION ==========\n")

for msg in result["messages"]:
    print(f"[{msg.type.upper()}]")
    print(msg.content)
    print("-" * 60)