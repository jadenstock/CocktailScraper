import requests
from typing import List, Dict
import json
from openai import OpenAI
import instructor
from datetime import datetime
from instructor import OpenAISchema
from pydantic import Field


class BarInfo(OpenAISchema):
    """Information about a cocktail bar"""
    name: str = Field(..., description="The name of the bar")
    address: str = Field(..., description="The full address of the bar")
    description: str = Field(..., description="A brief description of the bar and its atmosphere")
    notable_features: List[str] = Field(..., description="Special features, signature drinks, or unique aspects")
    website: str | None = Field(None, description="The bar's website URL if available")


class CocktailResearcher:
    def __init__(self, brave_api_key: str, openai_api_key: str):
        self.brave_api_key = brave_api_key
        self.openai_client = instructor.patch(OpenAI(api_key=openai_api_key))

    def search_bars(self, city: str, num_bars: int = 5) -> List[Dict]:
        """Search for top cocktail bars in a given city"""
        headers = {
            "X-Subscription-Token": self.brave_api_key,
            "Accept": "application/json",
        }

        # Craft a specific search query for cocktail bars
        query = f"best craft cocktail bars {city} mixology"

        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params={
                "q": query,
                "count": 20  # Request more results to filter
            }
        )

        if response.status_code != 200:
            raise Exception(f"Search failed with status {response.status_code}")

        # Process results with OpenAI to extract structured information
        search_results = response.json()

        # Use OpenAI to process the search results
        prompt = f"""Given these search results about cocktail bars in {city}, extract information about the top {num_bars} most interesting craft cocktail bars.
        Focus on places known for creative drinks, mixology, and unique experiences.

        Search results:
        {json.dumps(search_results['web']['results'], indent=2)}

        Extract details for the top bars, including their names, addresses, descriptions, notable features, and websites if available.
        """

        bars = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            response_model=List[BarInfo],
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return [bar.model_dump() for bar in bars]

    def get_menu(self, bar_info: Dict) -> Dict:
        """Future method: Get cocktail menu for a specific bar"""
        pass


if __name__ == "__main__":
    # Example usage
    researcher = CocktailResearcher(
        brave_api_key="BSAwOMjy0XCjQ1uSY4sTsq8WAqdlGf6",
        openai_api_key="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"
    )

    # Search for bars in a city
    sf_bars = researcher.search_bars("San Francisco", num_bars=5)
    print(json.dumps(sf_bars, indent=2))