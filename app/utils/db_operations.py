from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Dict, Optional
from app.models.models import User, Document, Report, Cache
import numpy as np

class DatabaseOperations:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create_user(self, user: User) -> str:
        result = await self.db.users.insert_one(user.dict(by_alias=True))
        return str(result.inserted_id)

    async def get_user(self, user_id: str) -> Optional[Dict]:
        return await self.db.users.find_one({"_id": ObjectId(user_id)})

    async def create_document(self, document: Document) -> str:
        result = await self.db.documents.insert_one(document.dict(by_alias=True))
        return str(result.inserted_id)

    async def get_document(self, document_id: str) -> Optional[Dict]:
        return await self.db.documents.find_one({"_id": ObjectId(document_id)})

    async def find_similar_documents(self, vector: List[float], threshold: float = 0.8) -> List[Dict]:
        """Find similar documents using vector similarity"""
        try:
            # Get all documents
            cursor = self.db.documents.find({}, {
                "filename": 1,
                "content": 1,
                "content_vector": 1,
                "file_type": 1,
                "created_at": 1
            })
            documents = await cursor.to_list(length=100)  # Limit to 100 docs for now
            
            # Calculate similarities
            similar_docs = []
            for doc in documents:
                if "content_vector" in doc:
                    # Calculate cosine similarity
                    doc_vector = doc["content_vector"]
                    similarity = float(np.dot(vector, doc_vector) / 
                                    (np.linalg.norm(vector) * np.linalg.norm(doc_vector)))
                    
                    if similarity >= threshold:
                        doc["score"] = similarity
                        similar_docs.append(doc)
            
            # Sort by similarity score
            similar_docs.sort(key=lambda x: x["score"], reverse=True)
            
            return similar_docs[:10]  # Return top 10 similar documents
            
        except Exception as e:
            print(f"Error in find_similar_documents: {str(e)}")
            raise

    async def create_report(self, report: Report) -> str:
        result = await self.db.reports.insert_one(report.dict(by_alias=True))
        return str(result.inserted_id)

    async def get_user_reports(self, user_id: str) -> List[Dict]:
        cursor = self.db.reports.find({"user_id": ObjectId(user_id)})
        return await cursor.to_list(length=None)

    async def set_cache(self, key: str, value: Dict):
        cache_doc = Cache(key=key, value=value)
        await self.db.cache.insert_one(cache_doc.dict(by_alias=True))

    async def get_cache(self, key: str) -> Optional[Dict]:
        return await self.db.cache.find_one({"key": key})

    async def get_document_vectors(self, limit: int = 5) -> List[Dict]:
        """Get documents with their vector representations"""
        cursor = self.db.documents.find(
            {},
            {
                "filename": 1,
                "content_vector": 1,
                "_id": 1
            }
        ).limit(limit)
        
        return await cursor.to_list(length=limit)

    async def print_vector_info(self):
        """Print information about vectors in the database"""
        sample_doc = await self.db.documents.find_one({"content_vector": {"$exists": True}})
        if sample_doc and "content_vector" in sample_doc:
            vector = sample_doc["content_vector"]
            print(f"Vector dimensions: {len(vector)}")
            print(f"Sample vector (first 5 elements): {vector[:5]}")
            
        count = await self.db.documents.count_documents({"content_vector": {"$exists": True}})
        print(f"Total documents with vectors: {count}")

    async def get_all_documents(self, limit: int = 100) -> List[Dict]:
        """Get all documents from the database"""
        cursor = self.db.documents.find().limit(limit)
        return await cursor.to_list(length=limit)

    async def find_similar_documents_with_search(self, vector: List[float], threshold: float = 0.8) -> List[Dict]:
        """Find similar documents using Atlas Search"""
        try:
            pipeline = [
                {
                    "$search": {
                        "index": "default",  # Use your index name here
                        "knnBeta": {
                            "vector": vector,
                            "path": "content_vector",
                            "k": 10
                        }
                    }
                },
                {
                    "$project": {
                        "filename": 1,
                        "content": 1,
                        "file_type": 1,
                        "created_at": 1,
                        "score": { "$meta": "searchScore" }
                    }
                }
            ]
            
            cursor = self.db.documents.aggregate(pipeline)
            return await cursor.to_list(length=10)
            
        except Exception as e:
            print(f"Falling back to regular similarity search: {str(e)}")
            return await self.find_similar_documents(vector, threshold)