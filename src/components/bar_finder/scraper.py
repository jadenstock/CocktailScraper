"""
Alternative Bar Research Implementation
====================================

This module provides a direct approach to finding cocktail bars using Brave Search + GPT-3.5,
as an alternative to the CrewAI-based implementation in researcher.py.

Key differences from CrewAI version:
- More direct/simple implementation without agent architecture
- Gets 20 search results instead of 2
- Uses structured Pydantic models for bar data
- Better extraction of real bar data from search results
- Lower cost due to GPT-3.5 instead of GPT-4

Usage:
    from components.bar_finder.scraper import CocktailResearcher
    from core.config.settings import settings

    researcher = CocktailResearcher()
    sf_bars = researcher.search_bars("San Francisco", num_bars=5)

Trade-offs:
+ Simpler implementation
+ More reliable real-world data
+ Lower cost
- Less extensible than CrewAI
- May miss some nuanced details GPT-4 would catch
"""

import requests
from typing import List, Dict
import json
from openai import OpenAI
import instructor
from datetime import datetime
from instructor import OpenAISchema
from pydantic import Field
from core.config.settings import settings
from core.tracking import UsageTracker


class BarInfo(OpenAISchema):
    """Information about a cocktail bar"""
    name: str = Field(..., description="The name of the bar")
    address: str = Field(..., description="The full address of the bar")
    description: str = Field(..., description="A brief description of the bar and its atmosphere")
    notable_features: List[str] = Field(..., description="Special features, signature drinks, or unique aspects")
    website: str | None = Field(None, description="The bar's website URL if available")


class CocktailResearcher:
    def __init__(self):
        """Initialize researcher with API keys from config"""
        self.brave_api_key = settings.brave_api_key
        self.openai_client = instructor.patch(OpenAI(api_key=settings.openai_api_key))
        self.usage_tracker = UsageTracker(settings.model_config)

    def search_bars(self, city: str, num_bars: int = 5) -> List[Dict]:
        """Search for top cocktail bars in a given city"""
        headers = {
            "X-Subscription-Token": self.brave_api_key,
            "Accept": "application/json",
        }

        # Track the search query
        self.usage_tracker.track_brave_search(
            query=f"best craft cocktail bars {city} mixology",
            num_results=20
        )

        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params={
                "q": f"best craft cocktail bars {city} mixology",
                "count": 20  # Request more results to filter
            }
        )

        if response.status_code != 200:
            raise Exception(f"Search failed with status {response.status_code}")

        search_results = response.json()

        # Use GPT-3.5 to process the search results
        prompt = f"""Given these search results about cocktail bars in {city}, extract information about the top {num_bars} most interesting craft cocktail bars.
        Focus on places known for creative drinks, mixology, and unique experiences.

        Important: Only extract information that is explicitly mentioned in the search results.
        Do not make up or infer details that aren't present.
        If you're not sure about a detail, leave it as null.

        Search results:
        {json.dumps(search_results['web']['results'], indent=2)}

        Extract details for the top bars, including their names, addresses, descriptions, notable features, and websites if available.
        """

        # Track the LLM interaction
        self.usage_tracker.track_llm_interaction(
            description=f"Process search results for {city}",
            content=prompt
        )

        bars = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using 3.5 for cost efficiency
            response_model=List[BarInfo],
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Save usage data
        self.usage_tracker.save_session()

        return [bar.model_dump() for bar in bars]

    def get_menu(self, bar_info: Dict) -> Dict:
        """
        Future method: Get cocktail menu for a specific bar
        This is a placeholder for future menu scraping functionality
        """
        raise NotImplementedError("Menu scraping not yet implemented")


if __name__ == "__main__":
    # Example usage
    researcher = CocktailResearcher()

    # Search for bars in a city
    sf_bars = researcher.search_bars("San Francisco", num_bars=5)
    print(json.dumps(sf_bars, indent=2))