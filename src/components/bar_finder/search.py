from functools import lru_cache
from langchain_community.tools import BraveSearch
from typing import List, Dict
import json

def truncate_text(text: str, max_tokens: int = 1000) -> str:
    """Truncate text to stay within token limit"""
    return text[:max_tokens * 4]  # Simple approximation

class BarSearch:
    def __init__(self, api_key: str, usage_tracker=None):
        self.brave_tool = BraveSearch.from_api_key(
            api_key=api_key,
            search_kwargs={
                "count": 2,
                "text_only": True,
                "snippet_only": True
            }
        )
        self.usage_tracker = usage_tracker

    @lru_cache(maxsize=100)
    def search(self, query: str, num_results: int = 2) -> List[Dict]:
        """Perform a cached search for bars"""
        if self.usage_tracker:
            self.usage_tracker.track_brave_search(query, num_results)
        
        results = self.brave_tool.run(query)
        return self.process_results(results)

    def process_results(self, results: List[Dict]) -> List[Dict]:
        """Process and clean up search results"""
        processed = []
        for result in results:
            processed.append({
                'title': truncate_text(result.get('title', ''), 100),
                'snippet': truncate_text(result.get('snippet', ''), 200),
                'link': result.get('link', '')
            })
        return processed