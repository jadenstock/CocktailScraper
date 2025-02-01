from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import List, Dict
import json
import os

from core.tracking import UsageTracker
from .search import BarSearch
from storage.bar_storage import BarStorage  # New import


class BarResearcher:
    def __init__(self, brave_api_key: str, openai_api_key: str, model_config: Dict):
        # Existing initialization...
        self.usage_tracker = UsageTracker(model_config)
        self.bar_search = BarSearch(
            api_key=brave_api_key,
            usage_tracker=self.usage_tracker
        )

        # Initialize storage
        self.storage = BarStorage()

        # Set up environment
        os.environ["BRAVE_API_KEY"] = brave_api_key
        os.environ["OPENAI_API_KEY"] = openai_api_key

        # Configure LLM
        self.llm = ChatOpenAI(
            model_name='gpt-3.5-turbo',
            temperature=0.0
        )

        # Create researcher agent
        self.researcher = Agent(
            role='Cocktail Bar Researcher',
            goal='Find and summarize cocktail bars efficiently',
            backstory="Brief, factual research on cocktail bars.",
            verbose=True,
            allow_delegation=False,
            tools=[self.bar_search.brave_tool],
            llm=self.llm
        )

    def create_search_task(self, city: str, num_bars: int = 3) -> Task:
        """Create a task to search for cocktail bars"""
        # Get existing bars to avoid duplicates
        known_bars = self.storage.get_bar_names(city)
        exclusion_text = f"\nDo NOT include these known bars: {', '.join(known_bars)}" if known_bars else ""

        return Task(
            description=f"""Find {num_bars} craft cocktail bars in {city}.
            Search query: 'craft cocktail bar {city}'
            For each, extract only:
            - Name
            - One brief description
            - 2-3 key features
            - Website
            - Menu URL if available
            {exclusion_text}

            Return JSON list of found bars.""",
            agent=self.researcher,
            expected_output="""[{
                "name": str,
                "description": str,
                "notable_for": list[2-3 items],
                "website": str or null,
                "cocktail_menu_url": str or null
            }]"""
        )

    def research_city(self, city: str, num_bars: int = 3) -> List[Dict]:
        """Execute the research for a given city"""
        try:
            # Create and execute the research task
            crew = Crew(
                agents=[self.researcher],
                tasks=[self.create_search_task(city, num_bars)],
                verbose=True
            )

            # Execute and track the interaction
            result = crew.kickoff()
            self.usage_tracker.track_llm_interaction(
                f"Research task for {num_bars} bars in {city}",
                result
            )

            try:
                parsed_result = json.loads(result)
                if isinstance(parsed_result, list):
                    # Store new bars
                    for bar in parsed_result:
                        self.storage.add_bar(
                            city=city,
                            bar_data=bar,
                            search_query=f'craft cocktail bar {city}'
                        )
                    return parsed_result
                else:
                    raise ValueError("Invalid result format")
            except json.JSONDecodeError:
                return [{"error": "Failed to parse result as JSON"}]

        except Exception as e:
            return [{"error": f"Research failed: {str(e)}"}]
        finally:
            # Print usage stats
            status = self.usage_tracker.get_status()
            print("\nSession Usage Statistics:")
            print(f"Input Tokens: {status['input_tokens']} (${status['input_cost']:.4f})")
            print(f"Output Tokens: {status['output_tokens']} (${status['output_cost']:.4f})")
            print(f"Brave API Cost: ${status['brave_cost']:.4f}")
            print(f"Total Cost: ${status['current_cost']:.4f}")
            print(f"API Calls: {status['total_api_calls']}")
            print(f"Search Queries: {status['search_queries']}")

            # Print storage stats
            stats = self.storage.get_stats()
            print("\nStorage Statistics:")
            print(f"Total Bars: {stats['total_bars']}")
            print("\nBars by City:")
            for city, count in stats['bars_by_city'].items():
                print(f"  {city}: {count}")
            print("\nRecent Discoveries:")
            for bar in stats['recent_discoveries']:
                print(f"  {bar['name']} in {bar['city']} ({bar['discovered_at']})")

            # Save usage data
            self.usage_tracker.save_session()

    def get_discovered_bars(self, city: str) -> List[Dict]:
        """Get all previously discovered bars for a city"""
        return self.storage.get_bars(city)