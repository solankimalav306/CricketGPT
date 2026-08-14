from pathlib import Path
from pymongo import MongoClient, InsertOne
from pymongo.errors import BulkWriteError
from tqdm import tqdm
import json

# -------------------------------
# Config
# -------------------------------
DATA_FOLDER = Path("data")
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "cricket_db"
COLLECTION = "matches"

BATCH_SIZE = 500

# -------------------------------
# Mongo
# -------------------------------
client = MongoClient(MONGO_URI)

db = client[DB_NAME]
collection = db[COLLECTION]

json_files = list(DATA_FOLDER.rglob("*.json"))

print(f"Found {len(json_files)} matches.")

operations = []

for file in tqdm(json_files):

    try:
        with open(file, "r", encoding="utf-8") as f:
            match = json.load(f)

        # Use filename as unique id
        match["_id"] = file.stem

        operations.append(InsertOne(match))

        if len(operations) >= BATCH_SIZE:
            try:
                collection.bulk_write(operations, ordered=False)
            except BulkWriteError:
                pass

            operations.clear()

    except Exception as e:
        print(f"Error reading {file.name}: {e}")

# Remaining documents
if operations:
    try:
        collection.bulk_write(operations, ordered=False)
    except BulkWriteError:
        pass

print("Import complete.")