from typing import Optional, Dict
from .crawler import MenuCrawler  # Changed to relative import
from .menu_processor import MenuDataProcessor  # Changed to relative import
from storage.bar_storage import BarStorage
from core.config.model_configs import MODEL_CONFIGS


class MenuService:
    def __init__(self):
        self.crawler = MenuCrawler()
        self.processor = MenuDataProcessor(MODEL_CONFIGS['gpt-3.5-turbo'])
        self.storage = BarStorage()

    def process_bar_menu(self, bar_id: str, website_url: str) -> Optional[Dict]:
        """Main entry point for processing a bar's menu"""
        try:
            # First try the crawler approach
            crawler_results = self.crawler.find_menu(bar_id, website_url)

            if self._has_valid_results(crawler_results):
                # Process and clean the data
                processed_data = self.processor.process_menu_data(crawler_results)

                # Store the results
                self.storage.update_menu_info(
                    bar_id=bar_id,
                    menu_urls=processed_data["menu_urls"],
                    menu_data=processed_data
                )

                return processed_data

            return None

        except Exception as e:
            print(f"Error processing menu for {bar_id}: {str(e)}")
            return None

    def _has_valid_results(self, results: Dict) -> bool:
        """Check if crawler found useful information"""
        if not results or "error" in results:
            return False

        # Check if we found any type of menu information
        return any([
            results.get("menu_pages"),
            results.get("cocktails"),
            results.get("pdf_menus"),
            results.get("external_menu_links")
        ])