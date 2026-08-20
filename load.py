from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

client = MongoClient("mongodb://localhost:27017")

db = client["cricket_db"]
matches = db["matches"]
venues = db["venues"]

venues.drop()

model = SentenceTransformer("all-MiniLM-L6-v2")

pipeline = [
    {
        "$group": {
            "_id": {
                "venue": "$info.venue",
                "city": {
                    "$ifNull": ["$info.city", "Unknown"]
                }
            }
        }
    },
    {
        "$sort": {
            "_id.city": 1,
            "_id.venue": 1
        }
    }
]

docs = list(matches.aggregate(pipeline))

print(f"Found {len(docs)} unique venues")
print(docs[0])

for doc in docs:

    venue = doc["_id"]["venue"]
    city = doc["_id"]["city"]

    embedding = model.encode(
        venue,
        normalize_embeddings=True
    ).tolist()

    venues.insert_one({
        "venue": venue,
        "city": city,
        "embedding": embedding
    })

venues.create_index([("city", 1)])
venues.create_index([("venue", 1)])
venues.create_index([("city", 1), ("venue", 1)], unique=True)

print(f"Inserted {venues.count_documents({})} venues")