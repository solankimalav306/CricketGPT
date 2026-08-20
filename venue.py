from datetime import datetime

from sentence_transformers import SentenceTransformer, util

import sys

# Correct path syntax for Windows using a raw string
sys.path.append(r"c:\code\CricketGPT")

# Import the modules
from db import db, execute_pipeline


from templates.venue_templates import get_v1_template
from templates.venue_templates import get_v2_template
from templates.venue_templates import get_v3_template


# ==================================================
# COLLECTION
# ==================================================

venues = db["venues"]

model = SentenceTransformer("all-MiniLM-L6-v2")


# ==================================================
# EXTRACT UPCOMING VENUE FROM SCHEDULER
# ==================================================

def get_match_context(schedule):

    for day in schedule["matches"]:

        for match in day["matchDetailsMap"]["match"]:

            info = match["matchInfo"]

            if info["state"] == "Upcoming":

                return {
                    "venue": info["venueInfo"]["ground"],
                    "city": info["venueInfo"]["city"],
                    "date": datetime.fromtimestamp(
                        int(info["startDate"]) / 1000
                    ).strftime("%Y-%m-%d"),
                    "team1": info["team1"]["teamName"],
                    "team2": info["team2"]["teamName"]
                }

    raise ValueError("No upcoming match found.")


# ==================================================
# VENUE RESOLVER
# ==================================================

def resolve_venue(venue_name, city):

    candidates = list(
        venues.find(
            {"city": city},
            {"_id": 0, "venue": 1, "embedding": 1}
        )
    )

    if not candidates:

        return {
            "status": "not_found",
            "requested": venue_name,
            "city": city
        }

    if len(candidates) == 1:

        return {
            "status": "resolved",
            "resolved": candidates[0]["venue"],
            "score": 1.0
        }

    query_embedding = model.encode(
        venue_name,
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    corpus = [v["embedding"] for v in candidates]

    scores = util.cos_sim(
        query_embedding,
        corpus
    )[0]

    best = int(scores.argmax())

    return {
        "status": "resolved",
        "resolved": candidates[best]["venue"],
        "score": float(scores[best])
    }


# ==================================================
# WEATHER REQUEST
# ==================================================

def build_weather_request(context):

    return {
        "city": context["city"],
        "date": context["date"],
        "parameters": [
            "temperature_2m",
            "relative_humidity_2m",
            "dew_point_2m",
            "wind_speed_10m",
            "precipitation_probability",
            "precipitation",
            "weather_code"
        ]
    }


# ==================================================
# VENUE AGENT
# ==================================================

def venue_agent(schedule):

    context = get_match_context(schedule)

    venue_queries = [
        {
            "template": "V1",
            "venue": context["venue"],
            "city": context["city"]
        },
        {
            "template": "V2",
            "venue": context["venue"],
            "city": context["city"]
        },
        {
            "template": "V3",
            "venue": context["venue"],
            "city": context["city"]
        }
    ]

    return {
        "venue_queries": venue_queries,
        "weather_request": build_weather_request(context)
    }


# ==================================================
# PROCESS VENUE TEMPLATE
# ==================================================

def process_venue_request(query):

    resolved = resolve_venue(
        query["venue"],
        query["city"]
    )

    if resolved["status"] != "resolved":

        return {
            "template": query["template"],
            "status": resolved["status"]
        }

    venue = resolved["resolved"]

    if query["template"] == "V1":
        pipeline = get_v1_template(venue)

    elif query["template"] == "V2":
        pipeline = get_v2_template(venue)

    elif query["template"] == "V3":
        pipeline = get_v3_template(venue)

    else:
        return {
            "template": query["template"],
            "status": "unknown_template"
        }

    result = execute_pipeline(pipeline)

    return {
        "template": query["template"],
        "status": "success",
        "venue": venue,
        "stats": result[0] if result else {}
    }