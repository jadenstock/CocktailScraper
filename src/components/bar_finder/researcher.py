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

    # src/components/bar_finder/researcher.py

    def create_search_task(self, city: str, num_bars: int = 3) -> Task:
        """Create a task to search for cocktail bars"""
        # Get existing bars to avoid duplicates
        known_bars = self.storage.get_bar_names(city)
        exclusion_text = f"\nDo NOT include these known bars: {', '.join(known_bars)}" if known_bars else ""

        # Generate search query
        search_query = self.bar_search.generate_search_query(city, known_bars)

        return Task(
            description=f"""Find {num_bars} craft cocktail bars in {city} using the provided search tool.

    IMPORTANT INSTRUCTIONS:
    1. Use the search tool with this exact query: '{search_query}'
    2. Only extract information about bars that appear in the search results
    3. Do NOT make up or hallucinate information about bars
    4. If a detail isn't in the search results, mark it as null
    5. Each bar MUST have a verifiable source from the search results{exclusion_text}

    For each bar from the search results, extract:
    - Name (exactly as it appears in results)
    - One brief description (using only information from results)
    - 2-3 key features (mentioned in results)
    - Website (from results only)
    - Menu URL if available (from results only)

    Return as a JSON list of found bars.
    If you cannot find enough verified bars in the search results, return fewer bars rather than making up information.""",
            agent=self.researcher,
            expected_output="""[{
                "name": str,
                "description": str,
                "notable_for": list[2-3 items],
                "website": str or null,
                "cocktail_menu_url": str or null,
                "source": str  # URL where this info was found
            }]"""
        )

    def research_city(self, city: str, num_bars: int = 5) -> List[Dict]:
        """Execute the research for a given city"""
        try:
            # Create and execute the research task
            crew = Crew(
                agents=[self.researcher],
                tasks=[self.create_search_task(city, num_bars)],
                verbose=True
            )

            result = crew.kickoff()
            self.usage_tracker.track_llm_interaction(
                f"Research task for {num_bars} bars in {city}",
                result
            )

            try:
                parsed_result = json.loads(result)
                if isinstance(parsed_result, list):
                    # Validate results
                    valid_results = []
                    for bar in parsed_result:
                        # Only accept bars that have at least a name and either a website or description
                        if bar.get('name') and (bar.get('website') or bar.get('description')):
                            valid_results.append(bar)

                    # Store new bars
                    for bar in valid_results:
                        self.storage.add_bar(city=city, bar_data=bar)
                    return valid_results
                else:
                    raise ValueError("Invalid result format")

            except json.JSONDecodeError:
                return [{"error": "Failed to parse result as JSON"}]

        except Exception as e:
            return [{"error": f"Research failed: {str(e)}"}]
        finally:
            # Print usage stats...
            pass

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