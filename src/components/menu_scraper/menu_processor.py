from typing import List, Dict
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


class MenuDataProcessor:
    def __init__(self, model_config: Dict):
        self.llm = ChatOpenAI(
            model_name=model_config['name'],
            temperature=0,  # Keep it factual
        )

        self.clean_cocktail_prompt = ChatPromptTemplate.from_template("""
            You are a cocktail menu parser. Parse this raw text into clean, structured cocktail data.
            Focus only on actual cocktail menu items - ignore navigation menus, website content, etc.

            Each cocktail should have:
            - name: The official cocktail name
            - price: Full price with $ symbol
            - ingredients: List of ingredients, separated cleanly
            - special_notes: Any special indicators like "NON ALCOHOLIC", null if none

            Raw menu text:
            {cocktail_text}

            Return only valid JSON as an array of cocktails in this format:
            [
                {{
                    "name": "string",
                    "price": "string",
                    "ingredients": ["string"],
                    "special_notes": "string or null"
                }}
            ]

            Only include items that are clearly cocktails with both a name and ingredients.
            Exclude food items, wines, beers, or other beverages.
        """)

    def process_menu_data(self, crawler_results: Dict) -> Dict:
        """Process raw crawler results into clean, structured data"""
        processed_data = {
            "menu_urls": crawler_results.get("menu_pages", []),
            "pdf_menus": crawler_results.get("pdf_menus", []),
            "external_menu_links": crawler_results.get("external_menu_links", []),
            "cocktails": []
        }

        # Convert all raw cocktail data into one text block for processing
        raw_cocktails = crawler_results.get("cocktails", [])
        if raw_cocktails:
            combined_text = "\n".join(item.get('text', '') for item in raw_cocktails)

            try:
                chain = self.clean_cocktail_prompt | self.llm
                result = chain.invoke({"cocktail_text": combined_text})

                # Parse the LLM's JSON response
                cleaned_cocktails = json.loads(result.content)
                if isinstance(cleaned_cocktails, list):
                    processed_data["cocktails"] = cleaned_cocktails
            except Exception as e:
                print(f"Error processing cocktails: {str(e)}")

        return processed_data

    def _validate_cocktail(self, cocktail: Dict) -> bool:
        """Validate that a cocktail has the required fields"""
        required_fields = ['name', 'price', 'ingredients']
        return all(
            cocktail.get(field) and len(str(cocktail[field]).strip()) > 0
            for field in required_fields
        )