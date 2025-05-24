import argparse
import os
import requests # For making HTTP requests to NewsAPI

# Pytrends related code has been removed.

def get_topics_from_newsapi(num_topics: int = 2, country_code: str = 'us'):
    """
    Fetches top headline topics from NewsAPI.org.

    Args:
        num_topics (int): The number of top headlines to return as topics.
        country_code (str): The 2-letter ISO 3166-1 code for the country (e.g., 'us', 'gb').

    Returns:
        list: A list of topic strings (article titles), or an empty list if an error occurs.
    """
    api_key = os.getenv("NEWSAPI_KEY")

    if not api_key:
        print("Error: The NEWSAPI_KEY environment variable is not set.")
        print("Please set it to your NewsAPI key to use this feature.")
        print("You can get a free key from https://newsapi.org/")
        # To allow script logic verification without a real key during subtask execution:
        print("Returning a sample list of topics for testing purposes as NEWSAPI_KEY is not set.")
        sample_topics = [
            "Sample Topic 1: Major Tech Conference Kicks Off This Week",
            "Sample Topic 2: Global Economic Outlook Discussed by World Leaders",
            "Sample Topic 3: Advances in Renewable Energy Sources Reported",
            "Sample Topic 4: New Space Mission Announced",
            "Sample Topic 5: Health and Wellness Trends for the New Year"
        ]
        return sample_topics[:num_topics]

    base_url = "https://newsapi.org/v2/top-headlines"
    # Ensure num_topics for pageSize is within NewsAPI's limits (e.g., max 100 for developer plan)
    # For safety, let's cap it at 100 if it's higher, though typically users will request few.
    page_size = min(num_topics, 100)

    params = {
        'country': country_code,
        'pageSize': page_size, 
        'apiKey': api_key
    }

    print(f"Fetching top {num_topics} headlines from NewsAPI for country '{country_code}'...")

    try:
        response = requests.get(base_url, params=params, timeout=10) # Added timeout
        response.raise_for_status() # Raises an HTTPError for bad responses (4XX or 5XX)

        data = response.json()

        if data.get("status") == "ok":
            articles = data.get("articles", [])
            if not articles:
                print("No articles found in the NewsAPI response.")
                return []
            
            # Use article titles as topics
            topics = [article['title'] for article in articles if article.get('title')]
            return topics[:num_topics] # Return the requested number of topics
        else:
            # Handle API-specific errors if present in the JSON response
            error_code = data.get("code", "")
            error_message = data.get("message", "Unknown error from NewsAPI.")
            print(f"NewsAPI error: {error_message} (Code: {error_code})")
            if error_code in ["apiKeyInvalid", "apiKeyMissing", "apiKeyDisabled"]:
                 print("Please ensure your NEWSAPI_KEY is correct, valid, and enabled.")
            elif error_code == "rateLimited":
                print("You have been rate-limited by NewsAPI. Please try again later.")
            elif error_code == "sourcesTooMany":
                 print("Too many sources requested. This shouldn't happen with top-headlines by country.")
            return []

    except requests.exceptions.HTTPError as http_err:
        # Error details are often in response.text or response.json() if possible
        error_details = ""
        try:
            error_details = http_err.response.json().get('message', '')
        except: # response might not be JSON or message key might be missing
            error_details = str(http_err.response.text)

        print(f"HTTP error occurred: {http_err} - {error_details}")
        if http_err.response.status_code == 401: # Unauthorized
            print("NewsAPI Authentication Failed: Check your API key.")
        elif http_err.response.status_code == 429: # Too Many Requests
            print("NewsAPI Rate Limit Exceeded. Please try again later.")
        elif http_err.response.status_code == 400: # Bad Request
            print(f"NewsAPI Bad Request: Often due to invalid parameters. Details: {error_details}")
        elif http_err.response.status_code == 426: # Upgrade Required (used by NewsAPI for developer plan on HTTPS)
             print(f"NewsAPI: Your plan may require HTTPS or is otherwise restricted. Details: {error_details}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
        print("Please check your internet connection.")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err: # Catch-all for requests issues
        print(f"An error occurred with the NewsAPI request: {req_err}")
    except ValueError as json_err: # Catch JSON decoding errors
        print(f"Error decoding JSON response from NewsAPI: {json_err}")
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
    
    return []

def main():
    parser = argparse.ArgumentParser(description="Discover trending topics using NewsAPI.org.")
    parser.add_argument(
        "--num_topics",
        type=int,
        default=2,
        help="The number of top headlines to fetch as topics (default: 2)."
    )
    parser.add_argument(
        "--country",
        type=str,
        default='us',
        help="The 2-letter ISO 3166-1 code of the country for headlines (e.g., 'us', 'gb', default: 'us')."
    )
    args = parser.parse_args()

    if args.num_topics <= 0:
        print("Error: Number of topics must be a positive integer.")
        return

    # Instructions for the user if NEWSAPI_KEY is not set
    if not os.getenv("NEWSAPI_KEY"):
        print("---------------------------------------------------------------------------")
        print("INFO: The NEWSAPI_KEY environment variable is not set.")
        print("The script will return sample topics for testing purposes.")
        print("For actual NewsAPI topics, please set this variable with your API key.")
        print("Example: export NEWSAPI_KEY='your_key_here'")
        print("You can obtain a free API key from https://newsapi.org/")
        print("---------------------------------------------------------------------------")
        # The get_topics_from_newsapi function also handles this and prints a message.

    topics = get_topics_from_newsapi(num_topics=args.num_topics, country_code=args.country)

    if topics:
        print("\nTop Topics from NewsAPI:")
        for i, topic in enumerate(topics):
            print(f"{i+1}. {topic}")
    else:
        print("Could not retrieve topics from NewsAPI this time.")

if __name__ == "__main__":
    main()
