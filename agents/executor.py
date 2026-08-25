

from state import CricketState


def route_from_executor(state: CricketState):
    plan = state.get("plan", [])
    
    # Since executor_node already incremented current_step, we must subtract 1
    # to route to the correct agent for the CURRENT step.
    idx = state.get("current_step", 1) - 1

    # If we have finished all steps in the plan, move to mongo
    if idx >= len(plan):
        return "mongo_agent"

    agent = plan[idx]["agent"].lower()

    mapping = {
        "scheduler": "scheduler",
        "player agent": "player_agent",
        "matchup agent": "matchup_agent",
        "venue agent": "venue_agent",
        "weather agent": "weather_agent",
        "mongo agent": "mongo_agent",
        "news agent": "news_agent"
    }

    # Safely route to the agent, fallback to mongo_agent if unrecognized
    return mapping.get(agent, "mongo_agent")

def executor_node(state: CricketState):
    idx = state.get("current_step", 0)
    plan = state.get("plan", [])

    if idx < len(plan):
        step = plan[idx]
        print(f"\n[EXECUTOR] Step {idx+1}/{len(plan)}: Routing to {step['agent'].upper()}...")
    else:
        print("\n[EXECUTOR] Plan complete. Routing to final agents.")

    # Increment the step so the NEXT time we hit executor, it moves forward
    return {
        "current_step": idx + 1
    }