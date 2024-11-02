from typing import List, Dict, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from app.utils.db_operations import DatabaseOperations

class SimilarityDetector:
    def __init__(self, db_ops: DatabaseOperations):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db_ops = db_ops

    def get_text_embedding(self, text: Union[str, List[str]]) -> np.ndarray:
        """Get embeddings for text or list of texts"""
        try:
            # Handle different input types
            if isinstance(text, list):
                # Join list of texts into single string
                text = ' '.join(str(t) for t in text)
            elif not isinstance(text, str):
                # Convert to string if not already
                text = str(text)
                
            # Ensure text is not empty
            if not text.strip():
                raise ValueError("Empty text provided")
                
            # Get embedding
            embedding = self.model.encode([text], convert_to_tensor=True)
            return embedding.cpu().numpy()[0] if hasattr(embedding, 'cpu') else embedding[0]
            
        except Exception as e:
            print(f"Error in get_text_embedding: {str(e)}")
            print(f"Input text type: {type(text)}")
            print(f"Input text preview: {str(text)[:200]}")
            raise

    async def find_similar_documents(self, text: str, threshold: float = 0.8) -> List[Dict]:
        vector = self.get_text_embedding(text)
        print(vector)
        similar_docs = await self.db_ops.find_similar_documents(vector.tolist(), threshold)
        return similar_docs

    def analyze_similarity(self, source_text: Union[str, List[str]], comparison_text: Union[str, List[str]]) -> Dict:
        """
        Analyze similarity between two texts using various metrics
        """
        # Get embeddings for both texts
        source_embedding = self.get_text_embedding(source_text)
        comparison_embedding = self.get_text_embedding(comparison_text)
        
        # Calculate cosine similarity and convert to Python float
        cosine_sim = float(np.dot(source_embedding, comparison_embedding) / \
                    (np.linalg.norm(source_embedding) * np.linalg.norm(comparison_embedding)))
        
        # Calculate other similarity metrics as needed
        similarity_data = {
            'cosine_similarity': cosine_sim,
            'similarity_threshold': 0.8,  # Configurable threshold
            'is_plagiarized': bool(cosine_sim > 0.8),  # Convert numpy.bool_ to Python bool
            'matched_segments': [],  # You can add text segments that match
            'similarity_score': cosine_sim * 100,  # Convert to percentage
            'tfidf_similarity': cosine_sim,  # For compatibility with report generator
            'semantic_similarity': cosine_sim,  # For compatibility with report generator
            'ngram_similarity': cosine_sim,  # For compatibility with report generator
            'overall_similarity': cosine_sim  # For compatibility with report generator
        }
        
        # If similarity is high, find matching segments
        if cosine_sim > 0.8:
            # Here you can implement logic to find specific matching segments
            source_preview = source_text[:100] if isinstance(source_text, str) else source_text[0][:100]
            comparison_preview = comparison_text[:100] if isinstance(comparison_text, str) else comparison_text[0][:100]
            
            similarity_data['matched_segments'] = [{
                'source_text': f"{source_preview}...",
                'matched_text': f"{comparison_preview}...",
                'similarity': cosine_sim,
                'semantic_similarity': cosine_sim,
                'levenshtein_similarity': 0.0  # Placeholder for now
            }]
        
        return similarity_data