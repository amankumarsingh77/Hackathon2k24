from typing import List, Dict, Union, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer, util
from app.utils.db_operations import DatabaseOperations
import logging
import torch
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

class SimilarityDetector:
    def __init__(self, db_ops: DatabaseOperations):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db_ops = db_ops
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)
        self.batch_size = 32
        self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 3))

    def get_text_embedding(self, text: Union[str, List[str]]) -> np.ndarray:
        """Get embeddings with batching and better error handling"""
        try:
            # Normalize input
            if isinstance(text, list):
                texts = [str(t) for t in text]
            else:
                texts = [str(text)]

            # Remove empty texts
            texts = [t.strip() for t in texts if t.strip()]
            if not texts:
                raise ValueError("No valid text provided")

            # Process in batches
            embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                batch_embedding = self.model.encode(
                    batch,
                    convert_to_tensor=True,
                    device=self.device,
                    show_progress_bar=False,
                    normalize_embeddings=True
                )
                embeddings.append(batch_embedding.cpu().numpy())

            # Combine results
            final_embedding = np.vstack(embeddings) if len(embeddings) > 1 else embeddings[0]
            return final_embedding.mean(axis=0) if len(texts) > 1 else final_embedding[0]

        except Exception as e:
            logging.error(f"Error in get_text_embedding: {str(e)}")
            raise

    def analyze_similarity(self, source_text: Union[str, List[str]], comparison_text: Union[str, List[str]]) -> Dict:
        """Enhanced similarity analysis with multiple metrics"""
        # Ensure texts are strings
        source_text = ' '.join(source_text) if isinstance(source_text, list) else source_text
        comparison_text = ' '.join(comparison_text) if isinstance(comparison_text, list) else comparison_text

        # Get sentence-level embeddings
        source_sentences = sent_tokenize(source_text)
        comparison_sentences = sent_tokenize(comparison_text)

        # Calculate sentence-level similarities
        sentence_similarities = []
        for src_sent in source_sentences:
            src_emb = self.get_text_embedding(src_sent)
            best_similarity = 0
            for comp_sent in comparison_sentences:
                comp_emb = self.get_text_embedding(comp_sent)
                similarity = float(util.cos_sim(
                    torch.tensor(src_emb), 
                    torch.tensor(comp_emb)
                ).cpu().numpy()[0])
                best_similarity = max(best_similarity, similarity)
            sentence_similarities.append(best_similarity)

        # Calculate different similarity metrics
        # 1. Average sentence-level similarity
        avg_sent_similarity = np.mean(sentence_similarities)

        # 2. TF-IDF similarity
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([source_text, comparison_text])
            tfidf_similarity = float((tfidf_matrix * tfidf_matrix.T).A[0][1])
        except:
            tfidf_similarity = 0.0

        # 3. Overall document embeddings similarity
        source_embedding = self.get_text_embedding(source_text)
        comparison_embedding = self.get_text_embedding(comparison_text)
        doc_similarity = float(util.cos_sim(
            torch.tensor(source_embedding), 
            torch.tensor(comparison_embedding)
        ).cpu().numpy()[0])

        # Combine metrics with weights
        overall_similarity = (
            0.4 * avg_sent_similarity +  # Sentence-level similarity
            0.3 * tfidf_similarity +     # Local text features
            0.3 * doc_similarity         # Global document similarity
        )

        # Find matching segments
        matched_segments = self._find_matching_segments(
            source_sentences, 
            comparison_sentences,
            threshold=0.8
        ) if overall_similarity > 0.3 else []

        return {
            'sentence_similarity': float(avg_sent_similarity),
            'tfidf_similarity': float(tfidf_similarity),
            'document_similarity': float(doc_similarity),
            'overall_similarity': float(overall_similarity),
            'similarity_score': float(overall_similarity * 100),
            'matched_segments': matched_segments,
            'similarity_breakdown': {
                'exact_matches': len([s for s in sentence_similarities if s > 0.9]),
                'high_similarity': len([s for s in sentence_similarities if 0.7 < s <= 0.9]),
                'moderate_similarity': len([s for s in sentence_similarities if 0.5 < s <= 0.7]),
                'low_similarity': len([s for s in sentence_similarities if s <= 0.5])
            }
        }

    def _find_matching_segments(self, source_sentences: List[str], 
                              comparison_sentences: List[str], 
                              threshold: float = 0.8) -> List[Dict]:
        """Find matching text segments with similarity scores"""
        matches = []
        
        for i, src_sent in enumerate(source_sentences):
            src_emb = self.get_text_embedding(src_sent)
            
            for j, comp_sent in enumerate(comparison_sentences):
                comp_emb = self.get_text_embedding(comp_sent)
                similarity = float(util.cos_sim(
                    torch.tensor(src_emb), 
                    torch.tensor(comp_emb)
                ).cpu().numpy()[0])
                
                if similarity > threshold:
                    matches.append({
                        'source_text': src_sent,
                        'matched_text': comp_sent,
                        'similarity': similarity,
                        'source_index': i,
                        'match_index': j
                    })
        
        # Sort matches by similarity score
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches[:10]  # Return top 10 matches