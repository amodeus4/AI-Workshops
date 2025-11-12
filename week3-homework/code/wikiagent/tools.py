import requests
from typing import Any, Dict, List


class WikipediaTools:
    """Tools for searching and fetching content from Wikipedia."""

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Wikipedia for pages matching the given query.

        Args:
            query (str): The search query string. Use "+" for spaces in multi-word queries.

        Returns:
            A list of search results containing page titles and snippets.
        """
        # Replace spaces with "+" for the API
        query_encoded = query.replace(" ", "+")
        
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query_encoded,
            #"srlimit": limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("query", {}).get("search", [])
            return results
        except requests.exceptions.RequestException as e:
            print(f"Error searching Wikipedia: {e}")
            return []

    def get_page(self, page_title: str) -> str:
        """
        Fetch the raw content of a Wikipedia page.

        Args:
            page_title (str): The title of the Wikipedia page to fetch.

        Returns:
            The raw content of the Wikipedia page as a string.
        """
        # Replace spaces with underscores for the API
        page_encoded = page_title.replace(" ", "_")
        
        url = "https://en.wikipedia.org/w/index.php"
        params = {
            "title": page_encoded,
            "action": "raw"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Wikipedia page '{page_title}': {e}")
            return ""


def get_wikipedia_tools() -> WikipediaTools:
    """
    Factory function to get Wikipedia tools instance.

    Returns:
        WikipediaTools: An instance of the WikipediaTools class.
    """
    return WikipediaTools()


# functions for direct use
def search_wikipedia(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search Wikipedia for pages matching the query."""
    tools = get_wikipedia_tools()
    return tools.search(query, limit)


def get_wikipedia_page(page_title: str) -> str:
    """Fetch the raw content of a Wikipedia page."""
    tools = get_wikipedia_tools()
    return tools.get_page(page_title)



