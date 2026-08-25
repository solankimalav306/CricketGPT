

from state import CricketState
from data_fetchers.weather_fetcher import get_weather

def weather_agent_node(state: CricketState):

    print("\n" + "=" * 80)
    print("[WEATHER AGENT]")
    print("=" * 80)

    requests = state.get("weather_requests", [])

    if not requests:
        print("No weather requests.")
        return {"weather_results": []}

    results = []

    print(f"Weather requests: {len(requests)}")

    for req in requests:

        print(f"Fetching {req['city']} | {req['date']}")

        try:
            weather = get_weather(req)
            results.append(weather)

        except Exception as e:

            print(f"Weather API Error: {e}")

            results.append({
                "status": "error",
                "city": req["city"],
                "date": req["date"],
                "error": str(e)
            })

    return {
        "weather_results": results
    }