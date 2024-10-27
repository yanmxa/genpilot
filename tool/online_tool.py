import httpx
from dotenv import load_dotenv

load_dotenv()

import httpx


def wikipedia(q: str) -> str:
    """
    Search Wikipedia using the Wikipedia API and return the first snippet of the search result.

    Args:
        q (str): The search query term.

    Returns:
        str: The snippet from the first search result.

    Example:
        result = wikipedia("Python programming language")
        print(result)  # Outputs a snippet related to Python programming language.
    """
    response = httpx.get(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",  # Action type: querying the search API
            "list": "search",  # Get a list of search results
            "srsearch": q,  # Search term or query
            "format": "json",  # Return results in JSON format
        },
    )
    if not response.json()["query"] or len(response.json()["query"]["search"]) == 0:
        return "Result not found!"
    return response.json()["query"]["search"][0]["snippet"]
