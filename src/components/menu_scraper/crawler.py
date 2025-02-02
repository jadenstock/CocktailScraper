from pathlib import Path
from typing import Dict, List, Union, Optional
from datetime import datetime
import json
import logging
from bs4 import BeautifulSoup
import re
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin


class MenuCrawler:
    """Crawls bar websites to find and extract menu information"""

    def __init__(self, output_dir: str = "data/menu_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.setup_logging()
        self.init_patterns()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('menu_crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('MenuCrawler')

    def init_patterns(self):
        # Menu page patterns
        self.menu_url_patterns = [
            '/menu', '/drinks', '/cocktails', '/bar',
            '/food-and-drink', '/libations'
        ]

        # Terms that indicate a cocktail menu item
        self.cocktail_terms = [
            'martini', 'negroni', 'manhattan', 'margarita',
            'old fashioned', 'mojito', 'craft', 'house special',
            'signature', 'seasonal', 'classic'
        ]

        # Common ingredients for validation
        self.ingredients = [
            'vodka', 'gin', 'rum', 'tequila', 'whiskey', 'bourbon',
            'scotch', 'brandy', 'cognac', 'vermouth', 'bitters',
            'liqueur', 'syrup', 'juice', 'lime', 'lemon', 'orange',
            'mint', 'cucumber', 'basil', 'rosemary', 'ginger'
        ]

        # Price pattern
        self.price_pattern = re.compile(r'\$\d+(?:\.\d{2})?')

    def find_menu(self, bar_id: str, website_url: str) -> Dict[str, Union[List[str], Dict]]:
        """Find menu information for a given bar"""
        try:
            self.logger.info(f"Starting menu search for {bar_id} at {website_url}")

            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch()
                context = browser.new_context()
                page = context.new_page()

                # First check homepage
                page.goto(website_url, wait_until='networkidle', timeout=30000)
                menu_links = self._find_menu_links(page)
                homepage_data = self._process_page(page)

                # Initialize results
                menu_data = {
                    "menu_pages": [website_url],
                    "cocktails": homepage_data.get("cocktails", []),
                    "pdf_menus": homepage_data.get("pdf_menus", []),
                    "external_menu_links": homepage_data.get("external_links", [])
                }

                # Check each menu link found
                for link in menu_links:
                    try:
                        page.goto(link, wait_until='networkidle', timeout=30000)
                        page_data = self._process_page(page)

                        menu_data["menu_pages"].append(link)
                        menu_data["cocktails"].extend(page_data.get("cocktails", []))
                        menu_data["pdf_menus"].extend(page_data.get("pdf_menus", []))
                        menu_data["external_menu_links"].extend(
                            page_data.get("external_links", [])
                        )
                    except Exception as e:
                        self.logger.error(f"Error processing {link}: {str(e)}")
                        continue

                # Take screenshots
                self._take_menu_screenshots(page, bar_id, menu_data["menu_pages"])

                # Save results
                self._save_menu_data(bar_id, menu_data)
                browser.close()

                return menu_data

        except Exception as e:
            self.logger.error(f"Error processing {bar_id}: {str(e)}")
            return {"error": str(e)}

    def _find_menu_links(self, page) -> List[str]:
        """Find menu-related links on the page"""
        links = page.evaluate('''() => {
            return Array.from(document.getElementsByTagName('a'))
                .map(a => ({
                    href: a.href,
                    text: a.textContent.toLowerCase()
                }))
                .filter(a => a.href.startsWith('http'));
        }''')

        menu_links = []
        for link in links:
            if any(pattern in link['href'].lower() for pattern in self.menu_url_patterns):
                menu_links.append(link['href'])
            elif any(term in link['text'] for term in ['menu', 'cocktail', 'drinks']):
                menu_links.append(link['href'])

        return list(set(menu_links))  # Remove duplicates

    def _process_page(self, page) -> Dict:
        """Extract menu information from a page"""
        content = page.content()
        soup = BeautifulSoup(content, 'html.parser')

        # Collect all text content from the page
        all_text = []
        for item in soup.stripped_strings:
            text = item.strip()
            if text and len(text) > 1:  # Skip empty or single-char strings
                all_text.append(text)

        return {
            "cocktails": [{"text": ' '.join(all_text)}],  # Send all text to the LLM
            "pdf_menus": self._find_pdf_menus(soup, page.url),
            "external_links": self._find_external_menu_links(soup)
        }

    def _looks_like_cocktail(self, text: str) -> bool:
        """Detect cocktail menu items with a better balance of precision and recall"""
        text = text.lower().strip()

        # Basic requirements
        has_price = bool(self.price_pattern.search(text))
        has_spirit = any(spirit in text for spirit in [
            'vodka', 'gin', 'rum', 'tequila', 'whiskey', 'bourbon',
            'scotch', 'mezcal', 'brandy', 'cognac', 'vermouth'
        ])

        # Exclude obvious non-cocktails
        non_cocktail_terms = [
            'beer', 'wine', 'coffee', 'espresso', 'tea',
            'bottles', 'draft', 'glass', 'pitcher',
            'appetizer', 'entree', 'pasta', 'pizza'
        ]

        is_non_cocktail = any(term in text for term in non_cocktail_terms)

        # More forgiving test for cocktail likelihood
        return not is_non_cocktail

    def _find_pdf_menus(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find PDF menu links on the page"""
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if href.endswith('.pdf'):
                full_url = urljoin(base_url, href)
                pdf_links.append(full_url)
        return list(set(pdf_links))

    def _find_external_menu_links(self, soup: BeautifulSoup) -> List[str]:
        """Find links to external menu services"""
        external_services = [
            'untappd.com', 'toasttab.com', 'opentable.com',
            'resy.com', 'tockify.com', 'square.site'
        ]

        external_links = []
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if any(service in href for service in external_services):
                external_links.append(link['href'])
        return list(set(external_links))

    def _parse_cocktail_item(self, text: str) -> Optional[Dict]:
        """Extract structured information from a cocktail menu item"""
        # Common pattern: Name - Description $Price
        # or Name $Price Description
        lines = text.split('\n')
        if not lines:
            return None

        item = {
            'text': text.strip(),
            'price': None,
            'ingredients': []
        }

        # Find price
        price_match = self.price_pattern.search(text)
        if price_match:
            item['price'] = price_match.group()

        # Find ingredients
        item['ingredients'] = [
            ingredient for ingredient in self.ingredients
            if ingredient in text.lower()
        ]

        return item if item['price'] and item['ingredients'] else None


    def _take_menu_screenshots(self, page, bar_id: str, urls: List[str]):
        """Take screenshots of menu pages"""
        screenshot_dir = self.output_dir / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)

        for i, url in enumerate(urls):
            try:
                page.goto(url, wait_until='networkidle')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{bar_id}_menu_{i}_{timestamp}.png"
                page.screenshot(
                    path=str(screenshot_dir / filename),
                    full_page=True
                )
            except Exception as e:
                self.logger.error(f"Error screenshotting {url}: {str(e)}")

    def _save_menu_data(self, bar_id: str, data: Dict):
        """Save extracted menu data to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"{bar_id}_menu_{timestamp}.json"

        with filepath.open('w') as f:
            json.dump(data, f, indent=2)