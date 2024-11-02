from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = "mongodb+srv://amankumar77:3lS1UV4CTetpHFFZ@hackathon.q7vys.mongodb.net/?retryWrites=true&w=majority&appName=hackathon"
DB_NAME = "plagiarism_detector"

# Async client for main operations
async def get_async_db():
    print(MONGODB_URI)
    client = AsyncIOMotorClient(MONGODB_URI)
    return client[DB_NAME]

# Sync client for vector operations
def get_sync_db():
    client = MongoClient(MONGODB_URI)
    return client[DB_NAME]

# Create indexes
def setup_indexes():
    db = get_sync_db()
    
    # Create vector search index for documents
    db.documents.create_index([
        ("content_vector", "vectorSearch")
    ], {
        "vectorSearchOptions": {
            "numDimensions": 768,  # For BERT embeddings
            "similarity": "cosine"
        }
    })

    # Create regular indexes
    db.users.create_index("email", unique=True)
    db.documents.create_index("user_id")
    db.reports.create_index("user_id")
    db.reports.create_index("document_id")
    db.cache.create_index("created_at", expireAfterSeconds=86400)  # 24 hour cache