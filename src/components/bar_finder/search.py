from langchain_community.tools import BraveSearch
from typing import List, Dict
import random


class BarSearch:
    def __init__(self, api_key: str, usage_tracker=None):
        self.brave_tool = BraveSearch.from_api_key(
            api_key=api_key,
            search_kwargs={
                "count": 10,  # Increased result count
                "text_only": False,  # Get full results
                "snippet_only": False
            }
        )
        self.usage_tracker = usage_tracker

        # Search variations to get different types of bars
        self.search_patterns = [
            "best craft cocktail bars in {}",
            "top mixology bars {}",
            "hidden speakeasy bars {}",
            "upscale cocktail lounges {}",
            "innovative cocktail bars {}"
        ]

    def generate_search_query(self, city: str, excluded_bars: List[str] = None) -> str:
        """Generate a search query, incorporating exclusions"""
        # Pick a random search pattern
        pattern = random.choice(self.search_patterns)
        query = pattern.format(city)

        # If we have bars to exclude, add them to the query
        if excluded_bars and len(excluded_bars) > 0:
            # Add exclusion terms, but limit to prevent query from getting too long
            exclusions = ' '.join(f'-"{bar}"' for bar in excluded_bars[:5])
            query = f"{query} {exclusions}"

        return query

    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Perform a search for bars"""
        if self.usage_tracker:
            self.usage_tracker.track_brave_search(query, num_results)

        results = self.brave_tool.run(query)
        return self.process_results(results)

    def process_results(self, results: List[Dict]) -> List[Dict]:
        """Process and clean up search results"""
        processed = []
        for result in results:
            # Extract more detailed information
            processed.append({
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'link': result.get('link', ''),
                'description': result.get('description', ''),
                'additional_links': result.get('additional_links', []),
                'source': 'brave_search'  # Mark the source of this information
            })
        return processed