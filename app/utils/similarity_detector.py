from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import Levenshtein
import numpy as np
from typing import List, Dict, Tuple

class SimilarityDetector:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer()
        self.bert_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        self.similarity_threshold = 0.5
        
    def analyze_similarity(self, source_text: List[str], comparison_texts: List[str]) -> Dict:
        """
        Analyze text similarity using multiple methods
        Returns comprehensive similarity analysis
        """
        results = {
            'tfidf_similarity': self._calculate_tfidf_similarity(source_text, comparison_texts),
            'semantic_similarity': self._calculate_semantic_similarity(source_text, comparison_texts),
            'ngram_similarity': self._calculate_ngram_similarity(source_text, comparison_texts),
            'detailed_matches': self._find_similar_passages(source_text, comparison_texts)
        }
        
        results['overall_similarity'] = self._calculate_overall_similarity(results)
        return results
    
    def _calculate_tfidf_similarity(self, source: List[str], targets: List[str]) -> float:
        """Calculate TF-IDF based cosine similarity"""
        all_texts = source + targets
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
        
        # Calculate similarity between source and each target
        source_vector = tfidf_matrix[:len(source)]
        target_vectors = tfidf_matrix[len(source):]
        
        similarities = cosine_similarity(source_vector, target_vectors)
        return float(np.mean(similarities))
    
    def _calculate_semantic_similarity(self, source: List[str], targets: List[str]) -> float:
        """Calculate BERT-based semantic similarity"""
        source_embeddings = self.bert_model.encode(source)
        target_embeddings = self.bert_model.encode(targets)
        
        similarities = cosine_similarity(source_embeddings, target_embeddings)
        return float(np.mean(similarities))
    
    def _calculate_ngram_similarity(self, source: List[str], targets: List[str], 
                                  n_range: Tuple[int, int] = (2, 4)) -> float:
        """Calculate n-gram based similarity"""
        def get_ngrams(text: str, n: int) -> set:
            return set(' '.join(text.split()[i:i+n]) for i in range(len(text.split())-n+1))
        
        similarities = []
        for n in range(n_range[0], n_range[1] + 1):
            source_ngrams = set()
            for text in source:
                source_ngrams.update(get_ngrams(text, n))
                
            target_ngrams = set()
            for text in targets:
                target_ngrams.update(get_ngrams(text, n))
            
            if source_ngrams and target_ngrams:
                similarity = len(source_ngrams.intersection(target_ngrams)) / len(source_ngrams.union(target_ngrams))
                similarities.append(similarity)
        
        return float(np.mean(similarities)) if similarities else 0.0
    
    def _find_similar_passages(self, source: List[str], targets: List[str]) -> List[Dict]:
        """Find specific similar passages using multiple methods"""
        similar_passages = []
        
        # Split texts into sentences if they're not already
        source_sentences = []
        for text in source:
            source_sentences.extend(text.split('. '))
        
        target_sentences = []
        for text in targets:
            target_sentences.extend(text.split('. '))
        
        # Get embeddings for all sentences
        source_embeddings = self.bert_model.encode(source_sentences)
        target_embeddings = self.bert_model.encode(target_sentences)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(source_embeddings, target_embeddings)
        
        # Find similar passages
        for i, source_text in enumerate(source_sentences):
            for j, target_text in enumerate(target_sentences):
                semantic_sim = similarity_matrix[i, j]
                
                # Calculate Levenshtein similarity only if semantic similarity is high enough
                if semantic_sim > self.similarity_threshold:
                    levenshtein_sim = 1 - (Levenshtein.distance(source_text, target_text) / 
                                         max(len(source_text), len(target_text)))
                    
                    # Add match if either similarity is high enough
                    if semantic_sim > self.similarity_threshold or levenshtein_sim > self.similarity_threshold:
                        similar_passages.append({
                            'source_text': source_text,
                            'target_text': target_text,
                            'semantic_similarity': float(semantic_sim),
                            'levenshtein_similarity': float(levenshtein_sim),
                            'source_index': i,
                            'target_index': j
                        })
        
        return similar_passages
    
    def _calculate_overall_similarity(self, results: Dict) -> float:
        """Calculate weighted overall similarity score"""
        weights = {
            'tfidf_similarity': 0.3,
            'semantic_similarity': 0.4,
            'ngram_similarity': 0.3
        }
        
        overall_score = sum(results[key] * weights[key] 
                          for key in weights.keys())
        
        return float(overall_score) 