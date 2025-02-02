from typing import Optional, List, Dict
import json
from storage.bar_storage import BarStorage
from .crawler import MenuCrawler  # Relative import
import logging
from datetime import datetime

class MenuScraperController:
    """Controls the process of discovering menu URLs for bars"""

    def __init__(self):
        self.storage = BarStorage()
        self.crawler = MenuCrawler()
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('menu_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MenuScraperController')

    def process_bars_without_menus(self, city: Optional[str] = None,
                                   limit: Optional[int] = None,
                                   verbose: bool = False):
        """
        Process bars that don't have menu information yet

        Args:
            city: Optional city to filter by
            limit: Maximum number of bars to process
            verbose: If True, show detailed progress
        """
        # Get bars that have websites but no menu info
        bars = self.get_bars_needing_menus(city)

        if not bars:
            self.logger.info(f"No bars found needing menu processing for {'all cities' if city is None else city}")
            return

        if limit:
            bars = bars[:limit]

        self.logger.info(f"Found {len(bars)} bars to process")

        for i, bar in enumerate(bars, 1):
            if not bar['website']:
                continue

            if verbose:
                print(f"Processing {i}/{len(bars)}: {bar['name']}")

            self.logger.info(f"Processing {bar['name']} ({bar['id']})")
            try:
                # Use crawler to find menus
                crawler_results = self.crawler.find_menu(
                    bar_id=bar['id'],
                    website_url=bar['website']
                )

                if crawler_results and "error" not in crawler_results:
                    # Update storage with found menu info
                    self.storage.update_menu_info(
                        bar_id=bar['id'],
                        menu_urls=crawler_results.get("menu_pages", []),
                        menu_data=crawler_results
                    )
                    if verbose:
                        print(f"✓ Found menu information for {bar['name']}")
                    self.logger.info(f"Successfully updated menu info for {bar['name']}")
                else:
                    if verbose:
                        print(f"✗ No menu information found for {bar['name']}")
                    self.logger.warning(f"No menu information found for {bar['name']}")

            except Exception as e:
                if verbose:
                    print(f"✗ Error processing {bar['name']}: {str(e)}")
                self.logger.error(f"Error processing {bar['name']}: {str(e)}")
                continue

    def get_bars_needing_menus(self, city: Optional[str] = None) -> List[Dict]:
        """Get bars that have websites but no menu information"""
        # Get all bars for city (or all cities)
        bars = self.storage.get_bars(city=city, include_raw=True)

        # Filter for bars that:
        # 1. Have a website
        # 2. Don't have menu_urls in their raw_data
        return [
            bar for bar in bars
            if bar['website'] and (
                    not bar['raw_data'] or
                    'menu_urls' not in json.loads(bar['raw_data'])
            )
        ]