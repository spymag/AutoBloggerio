import argparse
import os
import re
import openai # Added for OpenAI API integration
import json
from datetime import datetime # Added for date formatting

def generate_content_with_openai(topic_string: str) -> str | None:
    """
    Generates blog post content in Markdown format using the OpenAI API.
    
    Args:
        topic_string: The topic for the blog post.

    Returns:
        The generated Markdown content as a string, or None if an error occurs.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    # REMOVE full_response_content = None # Initialize here
    if not api_key:
        print("Error: The OPENAI_API_KEY environment variable is not set.")
        print("Please set it to your OpenAI API key to use this feature.")
        # For this subtask, we will return a placeholder if no key is found,
        # to allow testing the rest of the script flow.
        # In a real deployment, you might exit or raise an error.
        current_date = datetime.now().strftime("%B %d, %Y")
        placeholder_content = f"# {topic_string}\n\nThis is a placeholder because the OpenAI API key was not found. Please set the OPENAI_API_KEY environment variable.\n\nPublished: {current_date}\n"
        return placeholder_content, "This is a placeholder meta description." # Return two values

    try:
        client = openai.OpenAI(api_key=api_key)

        prompt = f"""
        Generate a blog post of approximately 400 words (around a 2-minute read)
        on the topic: "{topic_string}".

        **Crucially, the generated content, including the title, must be entirely original and written in your own words. Do not copy or closely paraphrase from any external sources. Do not cite or mention any sources used for inspiration. Esnure that there is no citation of the sources in the title. Change the title**

        The output must be in Markdown format.
        The content should be engaging and informative.
        It should include:
        1. A main title (H1 level).
        2. An introductory paragraph.
        3. Several subsequent paragraphs providing details, insights, or examples.
        4. Subheadings (H2 or H3) to structure the content where appropriate.
        5. A concluding paragraph.
        
        The post should be well-structured and ready to publish.
        Do not include any preamble like "Here is your blog post:".
        Start directly with the H1 title.
        Ensure the Markdown is clean and follows standard formatting.

        Following the Markdown content, on a new line, provide a concise meta description of around 150 characters, suitable for SEO. Start this line with "META_DESCRIPTION: ".
        For example:
        META_DESCRIPTION: Learn about the future of AI in software development and how it's changing the game.
        """

        print(f"Generating content and meta description for topic '{topic_string}' using OpenAI API...")
        
        # For testing purposes, as the worker won't have a real API key,
        # we can add a flag or a specific topic to bypass the actual API call
        # and return a more structured placeholder.
        # However, the subtask asks to prioritize correct code structure for the API call.
        # The current check for API key handles the missing key scenario.

        completion = client.chat.completions.create(
            model="gpt-4.1-nano", #model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates blog posts in Markdown format."},
                {"role": "user", "content": prompt}
            ]
        )

        if completion.choices and completion.choices[0].message:
            full_response_content = completion.choices[0].message.content # Assigned if successful

            # The rest of the logic for splitting meta description etc. follows below
            if full_response_content:
                # Attempt to parse markdown and meta description
                # Assuming "META_DESCRIPTION: " is on its own line or clearly separated.
                parts = full_response_content.split("\nMETA_DESCRIPTION: ", 1)
                generated_markdown = parts[0].strip()
                meta_description = None
                if len(parts) > 1:
                    meta_description = parts[1].strip()
                
                if not generated_markdown: # If markdown part is empty after split
                    print("Error: OpenAI API returned content but failed to parse Markdown part. Using full response as Markdown.")
                    generated_markdown = full_response_content.strip() # Fallback
                
                # Add the current date, formatted
                current_date = datetime.now().strftime("%B %d, %Y")
                generated_markdown_with_date = f"{generated_markdown}\n\nPublished: {current_date}\n"
                
                return generated_markdown_with_date, meta_description
            else:
                print("Error: OpenAI API returned an empty response.")
                return None, None
        else:
            print("Error: OpenAI API response did not contain the expected content structure.")
            return None

    except openai.AuthenticationError as e: # Changed from APIAuthenticationError
        print(f"OpenAI API Authentication Error: {e}")
        print("Please check your API key and ensure it's correctly set in OPENAI_API_KEY.")
    except openai.RateLimitError as e:
        print(f"OpenAI API Rate Limit Exceeded: {e}")
        print("Please wait and try again later, or check your OpenAI plan limits.")
    except openai.APIConnectionError as e:
        print(f"OpenAI API Connection Error: {e}")
        print("Please check your network connection or OpenAI server status.")
    except openai.APIStatusError as e: # More general server-side errors
        print(f"OpenAI API Status Error: {e}")
    except openai.OpenAIError as e: # Catch-all for other OpenAI specific errors
        print(f"An OpenAI API error occurred: {e}")
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred during OpenAI content generation: {e}")
    # REMOVE THE FINALLY BLOCK
    
    return None, None # Return None if any error occurred


def load_affiliate_links(filepath="config/affiliate_links.json") -> list:
    """Loads affiliate link configurations from a JSON file."""
    if not os.path.exists(filepath):
        print(f"Affiliate links file not found: {filepath}. Skipping affiliate link insertion.")
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            links = json.load(f)
        if not isinstance(links, list):
            print(f"Warning: Affiliate links file {filepath} does not contain a valid JSON list. Skipping.")
            return []
        # Basic validation of link objects
        valid_links = []
        for link_obj in links:
            if isinstance(link_obj, dict) and \
               "keywords" in link_obj and isinstance(link_obj["keywords"], list) and \
               "link" in link_obj and isinstance(link_obj["link"], str) and \
               all(isinstance(kw, str) for kw in link_obj["keywords"]):
                valid_links.append(link_obj)
            else:
                print(f"Warning: Invalid affiliate link object found in {filepath}: {link_obj}")
        return valid_links
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {filepath}. Skipping affiliate link insertion.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading {filepath}: {e}. Skipping.")
        return []

def insert_affiliate_links(markdown_content: str, affiliate_links: list, max_links_per_post: int = 3) -> str:
    """
    Inserts affiliate links into the Markdown content.
    - Replaces the first occurrence of keywords with Markdown links.
    - Case-insensitive keyword matching.
    - Limits the total number of affiliate links inserted.
    """
    if not affiliate_links or not markdown_content:
        return markdown_content

    links_inserted_count = 0
    # Keep track of which affiliate configurations have already been used to link once per config
    used_affiliate_configs_indices = set() 

    # Iterate over a copy of the affiliate_links list to allow modification if needed, or just for safety
    for idx, config in enumerate(affiliate_links):
        if links_inserted_count >= max_links_per_post:
            break # Stop if max links reached

        if idx in used_affiliate_configs_indices:
            continue # Skip if this affiliate link (from this config object) has already been used

        for keyword in config.get("keywords", []):
            if not keyword.strip(): # Skip empty keywords
                continue

            # Case-insensitive search for the keyword
            # We use re.escape to ensure keyword special characters are treated literally
            # We are looking for whole word matches, not substrings within words.
            # Using (?<!\w) and (?!\w) for word boundaries that work with unicode.
            # If keyword is at the start of a line or after space/punctuation.
            # (?i) for case-insensitive. \b works for ASCII, but for broader Unicode, we need more.
            # A simpler approach for now: find, then check boundaries if necessary.
            # For now, let's use a simpler regex that finds the keyword, and we'll replace only once.
            
            # Regex to find the keyword, ensuring it's not already part of a link
            # (?i) for case-insensitive.
            # Match keyword not preceded by '[' (to avoid linking already linked text)
            # and not followed by '](http...)' (to avoid relinking or breaking existing links)
            # This regex is tricky. Let's simplify and be careful.
            # We'll find the keyword and then construct the link.
            
            # Simple case-insensitive find
            try:
                # Create a regex pattern for the keyword, case-insensitive, ensuring it's a whole word.
                # \b works for ASCII words. For broader Unicode, might need refinement.
                pattern = re.compile(r'\b(' + re.escape(keyword) + r')\b', re.IGNORECASE)
                match = pattern.search(markdown_content)

                if match:
                    original_keyword_text = match.group(1) # The actual matched text (with original casing)
                    
                    # Ensure we are not inside an existing Markdown link, e.g. [some text _keyword_ more text](url)
                    # or part of a URL. This is a complex problem.
                    # A simple check: if the keyword is immediately surrounded by '[]' or '()', skip.
                    # This is a heuristic and not foolproof.
                    
                    # For simplicity, let's assume the first found match is okay to link.
                    # A more robust solution would involve parsing Markdown, which is too complex here.

                    link_markdown = f"[{original_keyword_text}]({config['link']})"
                    
                    # Replace only the first occurrence of this specific keyword match
                    # The `count=1` ensures only the first match found by `pattern.search` and then `re.sub` is replaced.
                    markdown_content = pattern.sub(link_markdown, markdown_content, count=1)
                    
                    print(f"Inserted affiliate link for keyword: '{keyword}' -> {config['link']}")
                    links_inserted_count += 1
                    used_affiliate_configs_indices.add(idx) # Mark this config as used
                    
                    if links_inserted_count >= max_links_per_post:
                        break # Break from keywords loop
            except re.error as re_err:
                print(f"Regex error for keyword '{keyword}': {re_err}")
                continue # Skip this keyword if regex is bad
            
            if links_inserted_count >= max_links_per_post or idx in used_affiliate_configs_indices:
                break # Break from keywords loop if limits reached or current config used

    if links_inserted_count > 0:
        print(f"Total affiliate links inserted: {links_inserted_count}")
    return markdown_content

def sanitize_filename(topic: str) -> str:
    """
    Sanitizes the topic string to create a valid filename.
    """
    # Lowercase
    s = topic.lower()
    # Remove special characters, except hyphens and spaces
    s = re.sub(r'[^\w\s-]', '', s)
    # Replace spaces with hyphens
    s = re.sub(r'\s+', '-', s)
    # Remove leading/trailing hyphens
    s = s.strip('-')
    return s

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Generate a new blog post.")
    parser.add_argument("topic", type=str, help="The topic of the blog post.")
    args = parser.parse_args()

    if not args.topic:
        print("Error: No topic provided. Please specify a topic for the post.")
        return

    topic = args.topic
    
    # Create posts directory if it doesn't exist
    posts_dir = "posts"
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)
        print(f"Created directory: {posts_dir}")

    # Generate filename
    filename = sanitize_filename(topic) + ".md"
    filepath = os.path.join(posts_dir, filename)

    # Generate content
    print(f"Attempting to generate content for topic: {topic}...")
    generated_markdown, meta_description = generate_content_with_openai(topic)

    if generated_markdown:
        # Load affiliate links and insert them
        affiliate_links_data = load_affiliate_links()
        if affiliate_links_data:
            print("Attempting to insert affiliate links...")
            content_with_affiliates = insert_affiliate_links(generated_markdown, affiliate_links_data)
        else:
            content_with_affiliates = generated_markdown
            print("No affiliate links loaded or found. Proceeding without them.")

        # Save Markdown content to file
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content_with_affiliates)
            print(f"Successfully generated post: {filepath}")
            # Print the basename of the file to stdout for the workflow script
            print(f"Generated filename: {os.path.basename(filepath)}")

            # Save meta description to .meta file
            if meta_description:
                meta_filepath = os.path.splitext(filepath)[0] + ".meta"
                try:
                    with open(meta_filepath, "w", encoding="utf-8") as f_meta:
                        f_meta.write(meta_description)
                    print(f"Successfully saved meta description: {meta_filepath}")
                except IOError as e_meta:
                    print(f"Error writing meta file {meta_filepath}: {e_meta}")
            else:
                print(f"No meta description generated for topic: {topic}")
                # Create an empty .meta file or a default one if desired
                meta_filepath = os.path.splitext(filepath)[0] + ".meta"
                try:
                    with open(meta_filepath, "w", encoding="utf-8") as f_meta:
                        f_meta.write("") # Empty, publish_post.py will handle fallback
                    print(f"Created empty .meta file: {meta_filepath} (will use fallback in publish_post.py)")
                except IOError as e_meta:
                    print(f"Error writing empty meta file {meta_filepath}: {e_meta}")

        except IOError as e:
            print(f"Error writing file {filepath}: {e}")
    else:
        print(f"Failed to generate content for topic '{topic}'. Post not created.")

if __name__ == "__main__":
    # Remind user about API key if they are running this directly
    if not os.getenv("OPENAI_API_KEY"):
        print("---------------------------------------------------------------------------")
        print("INFO: The OPENAI_API_KEY environment variable is not set.")
        print("The script will proceed and use a placeholder if content generation fails.")
        print("For actual OpenAI content, please set this variable with your API key.")
        print("Example: export OPENAI_API_KEY='your_key_here'")
        print("---------------------------------------------------------------------------")
    main()
