import requests
import json
import os


def google(keyword: str) -> str:
    """
    Performs a Google search using the Serper API and returns the description of the knowledge graph
    and the titles and snippets of the organic search results.

    Parameters:
    keyword (str): The search query to be used in the Google search.

    Returns:
    str: A string containing the description from the knowledge graph and the titles and snippets of organic results.
    """
    try:
        # Define the URL and headers
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": keyword})
        headers = {
            "X-API-KEY": os.getenv("SERPER_API_KEY"),  # API key
            "Content-Type": "application/json",  # Content type for the request
        }

        # Make the request
        response = requests.post(url, headers=headers, data=payload)

        # Check for successful response (status code 200)
        if response.status_code != 200:
            raise Exception(
                f"Error: Received status code {response.status_code} from Serper API"
            )

        # Parse the response JSON
        data = response.json()

        # Extract the description from the knowledge graph
        knowledge_graph_description = data.get("knowledgeGraph", {}).get(
            "description", "No description available"
        )

        # Extract titles and snippets from organic results
        organic_info = [
            f"Title: {result.get('title', 'No title available')}\nSnippet: {result.get('snippet', 'No snippet available')}"
            for result in data.get("organic", [])
        ]

        # Combine the description and organic results into a single string
        result_text = knowledge_graph_description + "\n\n" + "\n\n".join(organic_info)
        return result_text

    except Exception as e:
        # Return a detailed error message if an exception occurs
        return f"An error occurred: {str(e)}"


# result = google("when was the chinese academy of sciences founded?")
# print(result)
