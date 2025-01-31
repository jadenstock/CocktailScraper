import argparse
import json

from core.config.model_configs import MODEL_CONFIGS
from components.bar_finder.researcher import BarResearcher
from core.utils.utils import load_config  # Updated import path

def main():
    parser = argparse.ArgumentParser(description='Research cocktail bars in a city')
    parser.add_argument('--city', type=str, default="Seattle", help='City to research')
    parser.add_argument('--num-bars', type=int, default=3, help='Number of bars to find')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    # Load configuration
    config = load_config()
    BRAVE_API_KEY = config['api']['brave_api_key']
    OPENAI_API_KEY = config['api']['openai_api_key']

    # Initialize researcher
    researcher = BarResearcher(
        brave_api_key=BRAVE_API_KEY,
        openai_api_key=OPENAI_API_KEY,
        model_config=MODEL_CONFIGS['gpt-3.5-turbo']
    )

    # Execute research
    results = researcher.research_city(args.city, args.num_bars)
    print("\nResults:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()