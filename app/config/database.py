from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = "mongodb+srv://amankumar77:3lS1UV4CTetpHFFZ@hackathon.q7vys.mongodb.net/?retryWrites=true&w=majority&appName=hackathon"
DB_NAME = "plagiarism_detector"


async def get_async_db():
    print(MONGODB_URI)
    client = AsyncIOMotorClient(MONGODB_URI)
    return client[DB_NAME]


def get_sync_db():
    client = MongoClient(MONGODB_URI)
    return client[DB_NAME]


def setup_indexes():
    db = get_sync_db()
    
    
    try:
        db.command({
            "createSearchIndex": "documents",
            "name": "vector_index",
            "definition": {
                "mappings": {
                    "dynamic": True,
                    "fields": {
                        "content_vector": {
                            "dimensions": 384,
                            "similarity": "cosine",
                            "type": "knnVector"
                        }
                    }
                }
            }
        })
    except Exception as e:
        print(f"Warning: Could not create vector index: {str(e)}")

    
    db.users.create_index("email", unique=True)
    db.documents.create_index("user_id")
    db.reports.create_index("user_id")
    db.reports.create_index("document_id")
    db.cache.create_index("created_at", expireAfterSeconds=86400)  