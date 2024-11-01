from typing import List, Dict
import asyncio
from .scholarly_api import ScholarlyAPI
from .semantic_scholar import SemanticScholarAPI
from .web_scraper import WebScraper
import logging

class WebSourceManager:
    def __init__(self, redis_url: str = None):
        self.scholarly_api = ScholarlyAPI()
        self.semantic_scholar_api = SemanticScholarAPI()
        self.web_scraper = WebScraper(redis_url)
        self.logger = logging.getLogger(__name__)
    
    async def search_academic_sources(self, query: str, limit: int = 5) -> Dict:
        """Search multiple academic sources concurrently"""
        try:
            # Run API searches concurrently
            scholarly_task = asyncio.create_task(
                asyncio.to_thread(self.scholarly_api.search_papers, query, limit)
            )
            semantic_task = asyncio.create_task(
                self.semantic_scholar_api.search_papers(query, limit)
            )
            
            # Wait for results
            scholarly_results, semantic_results = await asyncio.gather(
                scholarly_task,
                semantic_task
            )

            print(scholarly_results)
            print(semantic_results)
            
            return {
                'google_scholar': scholarly_results,
                'semantic_scholar': semantic_results
            }
            
        except Exception as e:
            self.logger.error(f"Error searching academic sources: {str(e)}")
            return {'google_scholar': [], 'semantic_scholar': []}
    
    async def process_urls(self, urls: List[str]) -> Dict[str, str]:
        """Process multiple URLs concurrently"""
        try:
            tasks = [
                asyncio.create_task(
                    asyncio.to_thread(self.web_scraper.scrape_url, url)
                )
                for url in urls
            ]
            
            results = await asyncio.gather(*tasks)
            
            return {
                url: content for url, content in zip(urls, results)
                if content is not None
            }
            
        except Exception as e:
            self.logger.error(f"Error processing URLs: {str(e)}")
            return {} 