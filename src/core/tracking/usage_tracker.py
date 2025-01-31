from datetime import datetime
from pathlib import Path
import json
import tiktoken
from typing import Dict

from .api_tracker import APICallTracker


class UsageTracker:
    def __init__(self, model_config: Dict):
        self.model_config = model_config
        self.api_tracker = APICallTracker()
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

    def track_llm_interaction(self, prompt: str, response: str) -> Dict:
        """Track a complete LLM interaction"""
        input_tokens = self.add_input_tokens(prompt)
        output_tokens = self.add_output_tokens(response)

        interaction_cost = (
                (input_tokens / 1000) * self.model_config['cost_per_1k_input'] +
                (output_tokens / 1000) * self.model_config['cost_per_1k_output']
        )

        details = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': interaction_cost
        }

        return self.api_tracker.add_call('llm', details)

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

    def track_brave_search(self, query: str, num_results: int) -> Dict:
        """Track a Brave search API call"""
        self.session['search_queries'] += 1
        call_cost = self.api_tracker.brave_cost_per_call * num_results

        details = {
            'query': query,
            'num_results': num_results,
            'cost': call_cost
        }

        return self.api_tracker.add_call('brave', details)

    def calculate_cost(self) -> float:
        """Calculate current session cost"""
        input_cost = (self.session['input_tokens'] / 1000) * self.model_config['cost_per_1k_input']
        output_cost = (self.session['output_tokens'] / 1000) * self.model_config['cost_per_1k_output']
        brave_cost = self.api_tracker.get_total_brave_cost()
        return input_cost + output_cost + brave_cost

    def get_status(self) -> Dict:
        """Get current session status with detailed cost breakdown"""
        return {
            **self.session,
            'current_cost': self.calculate_cost(),
            'input_cost': (self.session['input_tokens'] / 1000) * self.model_config['cost_per_1k_input'],
            'output_cost': (self.session['output_tokens'] / 1000) * self.model_config['cost_per_1k_output'],
            'brave_cost': self.api_tracker.get_total_brave_cost(),
            'api_calls_breakdown': self.api_tracker.calls
        }

    def save_session(self):
        """Save session data to log file"""
        session_data = {
            **self.session,
            'end_time': datetime.now().isoformat(),
            'total_cost': self.calculate_cost(),
            'api_calls': self.api_tracker.calls
        }

        with self.log_file.open('a') as f:
            f.write(json.dumps(session_data) + '\n')