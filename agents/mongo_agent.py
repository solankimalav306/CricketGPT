from db_workers.mongo import run_mongo_agent
from state import CricketState

def mongo_agent_node(state: CricketState):

    print("\n" + "=" * 100)
    print("[MONGO NODE]")
    print("=" * 100)

    return run_mongo_agent(
        state
    )