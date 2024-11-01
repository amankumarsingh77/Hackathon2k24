from scholarly import scholarly
from ratelimit import limits, sleep_and_retry
from typing import List, Dict, Optional
import logging

class ScholarlyAPI:
    CALLS_PER_MINUTE = 30
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @sleep_and_retry
    @limits(calls=CALLS_PER_MINUTE, period=60)
    def search_papers(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for academic papers using Google Scholar"""
        try:
            search_query = scholarly.search_pubs(query)
            results = []
            
            for i, paper in enumerate(search_query):
                if i >= limit:
                    break
                    
                results.append({
                    'title': paper.get('title', ''),
                    'abstract': paper.get('abstract', ''),
                    'url': paper.get('url', ''),
                    'year': paper.get('year', ''),
                    'author': paper.get('author', []),
                    'citations': paper.get('num_citations', 0)
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching Google Scholar: {str(e)}")
            return [] 