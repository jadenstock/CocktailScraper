from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import List, Dict
import json
import os

from core.tracking import UsageTracker
from .search import BarSearch


class BarResearcher:
    def __init__(self, brave_api_key: str, openai_api_key: str, model_config: Dict):
        # Initialize tracking
        self.usage_tracker = UsageTracker(model_config)

        # Initialize search
        self.bar_search = BarSearch(
            api_key=brave_api_key,
            usage_tracker=self.usage_tracker
        )

        # Set up environment
        os.environ["BRAVE_API_KEY"] = brave_api_key
        os.environ["OPENAI_API_KEY"] = openai_api_key

        # Configure LLM specifically for GPT-3.5-turbo
        llm = ChatOpenAI(
            model_name='gpt-3.5-turbo',
            temperature=0.7
        )

        # Create researcher agent with specific LLM
        self.researcher = Agent(
            role='Cocktail Bar Researcher',
            goal='Find and summarize cocktail bars efficiently',
            backstory="Brief, factual research on cocktail bars.",
            verbose=True,
            allow_delegation=False,
            tools=[self.bar_search.brave_tool],
            llm=llm  # Use our configured LLM
        )

    def create_search_task(self, city: str, num_bars: int = 3) -> Task:
        """Create a task to search for cocktail bars"""
        return Task(
            description=f"""Find {num_bars} craft cocktail bars in {city}.
            Search query: 'craft cocktail bar {city}'
            For each, extract only:
            - Name
            - One brief description
            - 2-3 key features
            - Website
            - Menu URL if available

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
                if isinstance(parsed_result, list) and len(parsed_result) <= num_bars:
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

            # Save usage data
            self.usage_tracker.save_session()