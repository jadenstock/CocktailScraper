from datetime import datetime
from typing import Dict, List
from pathlib import Path
import json

class APICallTracker:
    """Detailed tracking of API calls and associated costs"""
    def __init__(self):
        self.calls = []
        self.brave_cost_per_call = 0.00083  # Cost per Brave search call

    def add_call(self, api_type: str, details: Dict):
        """Record an API call with full details"""
        call_record = {
            'timestamp': datetime.now().isoformat(),
            'api_type': api_type,
            **details
        }
        self.calls.append(call_record)
        return call_record

    def get_total_brave_cost(self) -> float:
        """Calculate total cost of Brave API calls"""
        return sum(
            call['cost']
            for call in self.calls
            if call['api_type'] == 'brave'
        )