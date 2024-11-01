import aiohttp
import asyncio
from typing import List, Dict, Optional
import logging
from ratelimit import limits, sleep_and_retry

class SemanticScholarAPI:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    CALLS_PER_MINUTE = 30
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @sleep_and_retry
    @limits(calls=CALLS_PER_MINUTE, period=60)
    async def search_papers(self, query: str, limit: int = 5) -> List[Dict]:
        """Search papers using Semantic Scholar Public API"""
        async with aiohttp.ClientSession() as session:
            try:
                url = f"{self.BASE_URL}/paper/search"
                params = {
                    "query": query,
                    "limit": limit,
                    "fields": "title,abstract,url,year,authors,citationCount"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_results(data.get('data', []))
                    else:
                        self.logger.error(f"API request failed: {response.status}")
                        return []
                        
            except Exception as e:
                self.logger.error(f"Error searching Semantic Scholar: {str(e)}")
                return []
    
    def _process_results(self, results: List[Dict]) -> List[Dict]:
        """Process and clean API results"""
        processed_results = []
        for paper in results:
            processed_results.append({
                'title': paper.get('title', ''),
                'abstract': paper.get('abstract', ''),
                'url': paper.get('url', ''),
                'year': paper.get('year'),
                'authors': [author.get('name', '') for author in paper.get('authors', [])],
                'citations': paper.get('citationCount', 0)
            })
        return processed_results