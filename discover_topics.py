import argparse
import os
import requests # For making HTTP requests to NewsAPI

# Pytrends related code has been removed.

def get_topics_from_newsapi(num_topics: int = 2, country_code: str = 'us'):
    api_key = os.getenv("NEWSAPI_KEY")

    if not api_key:
        print("Error: The NEWSAPI_KEY environment variable is not set.")
        print("Please set it to your NewsAPI key to use this feature.")
        print("You can get a free key from https://newsapi.org/")
        print("Returning a sample list of topics for testing purposes as NEWSAPI_KEY is not set.")
        
        sample_topics = [
            "AI Breakthrough: Advanced Algorithm Solves Complex Problem", # AI sample
            "Sample Topic 2: Global Economic Outlook Discussed by World Leaders",
            "Sample Topic 3: Advances in Renewable Energy Sources Reported",
            "Sample Topic 4: New Space Mission Announced",
            "Sample Topic 5: Health and Wellness Trends for the New Year"
        ]
        # Construct final_sample_topics based on num_topics, prioritizing AI.
        if num_topics > 0:
            final_sample_topics = [sample_topics[0]] # Start with AI topic
            # Add more general topics if needed
            general_samples_for_fallback = [st for st in sample_topics[1:] if st != sample_topics[0]]
            needed = num_topics - len(final_sample_topics)
            if needed > 0:
                final_sample_topics.extend(general_samples_for_fallback[:needed])
            return final_sample_topics
        else:
            return []

    base_url = "https://newsapi.org/v2/top-headlines" 
    everything_url = "https://newsapi.org/v2/everything"

    all_fetched_topics = []
    processed_topic_titles = set() # To avoid duplicates

    # 1. Fetch AI Topic
    if num_topics >= 1:
        ai_params = {
            'q': '"Artificial Intelligence" OR AI', 
            'language': 'en', 
            'pageSize': 5, 
            'sortBy': 'relevancy', 
            'apiKey': api_key
        }
        print(f"Fetching 1 AI-related topic from NewsAPI...")
        try:
            response_ai = requests.get(everything_url, params=ai_params, timeout=10)
            response_ai.raise_for_status()
            data_ai = response_ai.json()

            if data_ai.get("status") == "ok" and data_ai.get("articles"):
                for article in data_ai["articles"]:
                    title = article.get('title')
                    if title and title not in processed_topic_titles:
                        all_fetched_topics.append(title)
                        processed_topic_titles.add(title)
                        print(f"Found AI topic: {title}")
                        break 
                if not any("AI" in topic or "Artificial Intelligence" in topic for topic in all_fetched_topics if topic): # Check if any fetched topic is AI related
                    print("No AI-specific topic found in the first batch of AI query, will rely on general news if needed.")
            else:
                error_message = data_ai.get('message', 'No articles found or error')
                print(f"Could not fetch AI specific topics: {error_message} (Code: {data_ai.get('code')})")
        except requests.exceptions.HTTPError as http_err_ai:
            error_details_ai = ""
            try:
                error_details_ai = http_err_ai.response.json().get('message', str(http_err_ai.response.text))
            except:
                error_details_ai = str(http_err_ai.response.text)
            print(f"HTTP error fetching AI topics: {http_err_ai} - {error_details_ai}")
        except requests.exceptions.RequestException as e_ai:
            print(f"Error fetching AI topics: {e_ai}")
        except ValueError as json_err_ai: 
            print(f"Error decoding JSON response for AI topics from NewsAPI: {json_err_ai}")

    # 2. Fetch General Topics if still needed
    remaining_topics_needed = num_topics - len(all_fetched_topics)
    
    if remaining_topics_needed > 0:
        general_params = {
            'country': country_code,
            'pageSize': min(remaining_topics_needed, 100), 
            'apiKey': api_key,
            'category': 'general' 
        }
        print(f"Fetching {remaining_topics_needed} general headlines from NewsAPI for country '{country_code}'...")
        try:
            response_general = requests.get(base_url, params=general_params, timeout=10)
            response_general.raise_for_status()
            data_general = response_general.json()

            if data_general.get("status") == "ok" and data_general.get("articles"):
                for article in data_general["articles"]:
                    title = article.get('title')
                    if title and title not in processed_topic_titles:
                        all_fetched_topics.append(title)
                        processed_topic_titles.add(title)
                        if len(all_fetched_topics) >= num_topics:
                            break 
            else:
                error_message_gen = data_general.get('message', 'No articles found or error')
                print(f"Could not fetch general topics: {error_message_gen} (Code: {data_general.get('code')})")
        except requests.exceptions.HTTPError as http_err_gen:
            error_details_gen = ""
            try:
                error_details_gen = http_err_gen.response.json().get('message', str(http_err_gen.response.text))
            except:
                error_details_gen = str(http_err_gen.response.text)
            print(f"HTTP error fetching general topics: {http_err_gen} - {error_details_gen}")
        except requests.exceptions.RequestException as e_gen:
            print(f"Error fetching general topics: {e_gen}")
        except ValueError as json_err_gen: 
            print(f"Error decoding JSON response for general topics from NewsAPI: {json_err_gen}")

    if not all_fetched_topics and num_topics > 0 :
        print("No topics fetched from NewsAPI despite efforts. Returning fallback sample topics.")
        # Fallback to sample if all API calls fail and topics are expected
        fallback_sample_topics = [ # Renamed to avoid conflict with outer scope sample_topics
            "AI Breakthrough: Advanced Algorithm Solves Complex Problem", 
            "Sample Topic 2: Global Economic Outlook Discussed by World Leaders",
            "Sample Topic 3: Advances in Renewable Energy Sources Reported",
        ]
        # Ensure AI sample is first if num_topics allows
        final_fallback_topics = [fallback_sample_topics[0]] if num_topics >=1 else []
        if num_topics > 1:
            # Add general topics ensuring not to duplicate if the first AI topic was also general by chance
            general_fallbacks = [t for t in fallback_sample_topics[1:] if t != fallback_sample_topics[0]]
            final_fallback_topics.extend(general_fallbacks[:num_topics - len(final_fallback_topics)])
        return final_fallback_topics[:num_topics] # Ensure correct number returned

    return all_fetched_topics[:num_topics]

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

    if not os.getenv("NEWSAPI_KEY"):
        print("---------------------------------------------------------------------------")
        print("INFO: The NEWSAPI_KEY environment variable is not set.")
        print("The script will return sample topics for testing purposes.")
        print("For actual NewsAPI topics, please set this variable with your API key.")
        print("Example: export NEWSAPI_KEY='your_key_here'")
        print("You can obtain a free API key from https://newsapi.org/")
        print("---------------------------------------------------------------------------")

    topics = get_topics_from_newsapi(num_topics=args.num_topics, country_code=args.country)

    if topics:
        print("\nTop Topics from NewsAPI:")
        for i, topic in enumerate(topics):
            print(f"{i+1}. {topic}")
    else:
        print("Could not retrieve topics from NewsAPI this time, or no topics were requested.")

if __name__ == "__main__":
    main()
