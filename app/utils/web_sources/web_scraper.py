import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from ratelimit import limits, sleep_and_retry
import redis
from datetime import timedelta

class WebScraper:
    CALLS_PER_MINUTE = 60
    
    def __init__(self, redis_url: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        self.cache_duration = timedelta(hours=24)
    
    @sleep_and_retry
    @limits(calls=CALLS_PER_MINUTE, period=60)
    def scrape_url(self, url: str) -> Optional[str]:
        """Scrape content from a given URL with caching"""
        try:
            
            if self.redis_client:
                cached_content = self.redis_client.get(url)
                if cached_content:
                    return cached_content.decode('utf-8')
            
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            
            content = self._extract_main_content(soup)
            
            
            if self.redis_client and content:
                self.redis_client.setex(
                    url,
                    self.cache_duration,
                    content
                )
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error scraping URL {url}: {str(e)}")
            return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from webpage"""
        
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()
        
        
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        
        if main_content:
            return main_content.get_text(separator=' ', strip=True)
        
        
        return soup.get_text(separator=' ', strip=True) 