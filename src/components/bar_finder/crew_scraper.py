from crewai import Agent, Task, Crew
from langchain_community.tools import BraveSearch
import os
from typing import List, Dict, Optional
import json
from datetime import datetime
import tiktoken
from pathlib import Path

from utils import load_config

config = load_config()
BRAVE_API_KEY = config['api']['brave_api_key']
OPENAI_API_KEY = config['api']['openai_api_key']

# Updated model configurations with latest pricing
MODEL_CONFIGS = {
    'gpt-3.5-turbo': {
        'name': 'gpt-3.5-turbo',
        'max_tokens': 4096,
        'cost_per_1k_input': 0.0005,  # Updated pricing
        'cost_per_1k_output': 0.0015  # Updated pricing
    },
    'gpt-3.5-turbo-16k': {
        'name': 'gpt-3.5-turbo-16k',
        'max_tokens': 16384,
        'cost_per_1k_input': 0.003,
        'cost_per_1k_output': 0.004
    }
}


def truncate_text(text: str, max_tokens: int = 1000) -> str:
    """Truncate text to stay within token limit"""
    try:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        tokens = encoding.encode(text)
        if len(tokens) > max_tokens:
            return encoding.decode(tokens[:max_tokens]) + "..."
        return text
    except Exception as e:
        print(f"Warning: Could not truncate text: {e}")
        return text[:max_tokens * 4]  # Rough approximation


class UsageTracker:
    def __init__(self, model_config: Dict):
        self.model_config = model_config
        self.reset_session()
        self.log_file = Path("usage_logs.jsonl")

    def reset_session(self):
        """Reset session counters"""
        self.session = {
            'input_tokens': 0,
            'output_tokens': 0,
            'search_queries': 0,
            'start_time': datetime.now().isoformat(),
            'model': self.model_config['name'],
            'search_results_truncated': 0,
            'total_api_calls': 0
        }

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        try:
            encoding = tiktoken.encoding_for_model(self.model_config['name'])
            return len(encoding.encode(text))
        except Exception as e:
            print(f"Warning: Could not count tokens: {e}")
            return 0

    def add_input_tokens(self, text: str) -> int:
        """Track input tokens"""
        tokens = self.count_tokens(text)
        self.session['input_tokens'] += tokens
        return tokens

    def add_output_tokens(self, text: str) -> int:
        """Track output tokens"""
        tokens = self.count_tokens(text)
        self.session['output_tokens'] += tokens
        return tokens

    def add_search_query(self):
        """Track search queries"""
        self.session['search_queries'] += 1

    def add_api_call(self):
        """Track API calls"""
        self.session['total_api_calls'] += 1

    def add_truncation(self):
        """Track when we truncate search results"""
        self.session['search_results_truncated'] += 1

    def calculate_cost(self) -> float:
        """Calculate current session cost"""
        input_cost = (self.session['input_tokens'] / 1000) * self.model_config['cost_per_1k_input']
        output_cost = (self.session['output_tokens'] / 1000) * self.model_config['cost_per_1k_output']
        return input_cost + output_cost

    def get_status(self) -> Dict:
        """Get current session status"""
        return {
            **self.session,
            'current_cost': self.calculate_cost(),
            'input_cost': (self.session['input_tokens'] / 1000) * self.model_config['cost_per_1k_input'],
            'output_cost': (self.session['output_tokens'] / 1000) * self.model_config['cost_per_1k_output']
        }

    def save_session(self):
        """Save session data to log file"""
        session_data = {
            **self.session,
            'end_time': datetime.now().isoformat(),
            'total_cost': self.calculate_cost()
        }

        with self.log_file.open('a') as f:
            f.write(json.dumps(session_data) + '\n')

        self.reset_session()


class CocktailResearcher:
    def __init__(self, brave_api_key: str, openai_api_key: str):
        self.config = load_config()

        # Get model configuration
        model_name = self.config.get('model', {}).get('name', 'gpt-3.5-turbo')
        if model_name not in MODEL_CONFIGS:
            raise ValueError(f"Unsupported model: {model_name}")

        self.model_config = MODEL_CONFIGS[model_name]

        # Initialize usage tracker
        self.usage_tracker = UsageTracker(self.model_config)

        # Set up API keys
        os.environ["BRAVE_API_KEY"] = brave_api_key
        os.environ["OPENAI_API_KEY"] = openai_api_key

        # Get search configuration with optimized defaults
        search_results = self.config.get('search', {}).get('results_per_query', 2)

        # Initialize Brave Search tool with optimized parameters
        self.brave_tool = BraveSearch.from_api_key(
            api_key=brave_api_key,
            search_kwargs={
                "count": search_results,
                "text_only": True,  # Skip images/media
                "snippet_only": True  # Get shorter descriptions
            }
        )

        # Create researcher agent with optimized prompt
        self.researcher = Agent(
            role='Cocktail Bar Researcher',
            goal='Find and summarize cocktail bars efficiently',
            backstory="Brief, factual research on cocktail bars.",
            verbose=True,
            allow_delegation=False,
            tools=[self.brave_tool],
            llm_config={
                "config_list": [{
                    "model": self.model_config['name'],
                }]
            }
        )

    def create_search_task(self, city: str, num_bars: int = 3) -> Task:
        """Create a task to search for cocktail bars in a given city"""
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

    def process_search_results(self, results: List[Dict]) -> List[Dict]:
        """Process and truncate search results to reduce token usage"""
        processed = []
        for result in results:
            # Truncate each text field
            processed.append({
                'title': truncate_text(result.get('title', ''), 100),
                'snippet': truncate_text(result.get('snippet', ''), 200),
                'link': result.get('link', '')
            })
            self.usage_tracker.add_truncation()
        return processed

    def research_city(self, city: str, num_bars: int = 3) -> List[Dict]:
        """Execute the research for a given city"""
        try:
            # Track initial prompt tokens
            self.usage_tracker.add_input_tokens(
                f"Research task for {num_bars} bars in {city}"
            )

            crew = Crew(
                agents=[self.researcher],
                tasks=[self.create_search_task(city, num_bars)],
                verbose=True
            )

            result = crew.kickoff()
            self.usage_tracker.add_search_query()

            # Track response tokens
            self.usage_tracker.add_output_tokens(result)
            self.usage_tracker.add_api_call()

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
            # Print usage stats before saving
            status = self.usage_tracker.get_status()
            print("\nSession Usage Statistics:")
            print(f"Input Tokens: {status['input_tokens']} (${status['input_cost']:.3f})")
            print(f"Output Tokens: {status['output_tokens']} (${status['output_cost']:.3f})")
            print(f"Total Cost: ${status['current_cost']:.3f}")
            print(f"API Calls: {status['total_api_calls']}")
            print(f"Search Queries: {status['search_queries']}")
            print(f"Results Truncated: {status['search_results_truncated']}")

            # Save usage data
            self.usage_tracker.save_session()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Research cocktail bars in a city')
    parser.add_argument('--city', type=str, default="Seattle", help='City to research')
    parser.add_argument('--num-bars', type=int, default=3, help='Number of bars to find')

    args = parser.parse_args()

    researcher = CocktailResearcher(
        brave_api_key=BRAVE_API_KEY,
        openai_api_key=OPENAI_API_KEY
    )

    results = researcher.research_city(args.city, args.num_bars)
    print("\nResults:")
    print(json.dumps(results, indent=2))