import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = str(Path(__file__).parent.parent.parent)
sys.path.append(src_dir)

from components.menu_scraper import MenuCrawler
import json


def main():
    crawler = MenuCrawler()

    # Test with a real bar website
    result = crawler.find_menu(
        bar_id="canon",
        website_url="https://darkroomseattle.com/"
    )

    print("\nCrawl Results:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()