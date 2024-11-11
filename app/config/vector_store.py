from typing import List, Dict, Optional
import numpy as np
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

class VectorStore:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.dimension = 384  # dimension of all-MiniLM-L6-v2 embeddings

    async def add_document(self, doc_id: str, vector: list, metadata: dict, text_content: str):
        """Add document to MongoDB with vector embedding"""
        document = {
            '_id': ObjectId(doc_id),
            'content_vector': vector,
            'metadata': {
                **metadata,
                'timestamp': datetime.utcnow().isoformat()
            },
            'content': text_content
        }
        
        await self.db.documents.insert_one(document)

    async def search_similar(self, query_vector: list, k: int = 5, threshold: float = 0.3) -> List[Dict]:
        """Search for similar documents using MongoDB's $vectorSearch"""
        try:
            pipeline = [
                {
                    "$search": {
                        "index": "vector_index",  # Make sure this index exists
                        "knnBeta": {
                            "vector": query_vector,
                            "path": "content_vector",
                            "k": k * 2,  # Get more results initially for better filtering
                        }
                    }
                },
                {
                    "$project": {
                        "content": 1,
                        "metadata": 1,
                        "score": { "$meta": "searchScore" },
                        "content_vector": 1
                    }
                }
            ]
            
            cursor = self.db.documents.aggregate(pipeline)
            results = await cursor.to_list(length=k * 2)
            
            # Post-process results
            similar_docs = []
            seen_docs = set()
            
            for doc in results:
                doc_id = str(doc['_id'])
                if doc_id in seen_docs:
                    continue
                
                # Calculate cosine similarity for more accurate scoring
                similarity_score = float(np.dot(query_vector, doc['content_vector']) / 
                                      (np.linalg.norm(query_vector) * np.linalg.norm(doc['content_vector'])))
                
                if similarity_score >= threshold:
                    similar_docs.append({
                        'id': doc_id,
                        'score': similarity_score,
                        'metadata': doc['metadata'],
                        'content': doc['content']
                    })
                    seen_docs.add(doc_id)
                    
                    if len(similar_docs) >= k:
                        break
            
            return similar_docs
            
        except Exception as e:
            print(f"Error in vector search: {str(e)}")
            # Fallback to basic similarity search if vector search fails
            return await self._fallback_similarity_search(query_vector, k, threshold)

    async def _fallback_similarity_search(self, query_vector: list, k: int = 5, threshold: float = 0.8) -> List[Dict]:
        """Fallback similarity search using basic vector operations"""
        cursor = self.db.documents.find({}, {
            'content': 1,
            'metadata': 1,
            'content_vector': 1
        })
        
        documents = await cursor.to_list(length=100)  # Limit to prevent memory issues
        similar_docs = []
        
        for doc in documents:
            if 'content_vector' in doc:
                similarity_score = float(np.dot(query_vector, doc['content_vector']) / 
                                      (np.linalg.norm(query_vector) * np.linalg.norm(doc['content_vector'])))
                
                if similarity_score >= threshold:
                    similar_docs.append({
                        'id': str(doc['_id']),
                        'score': similarity_score,
                        'metadata': doc.get('metadata', {}),
                        'content': doc['content']
                    })
        
        # Sort by similarity score and return top k
        similar_docs.sort(key=lambda x: x['score'], reverse=True)
        return similar_docs[:k]

    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a document from MongoDB"""
        doc = await self.db.documents.find_one({'_id': ObjectId(doc_id)})
        if doc:
            return {
                'id': str(doc['_id']),
                'metadata': doc.get('metadata', {}),
                'content': doc['content'],
                'vector': doc['content_vector']
            }
        return None