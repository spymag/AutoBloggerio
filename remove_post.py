import argparse
import os
import json
from datetime import datetime, timezone

SITE_URL_PLACEHOLDER = "https://your-autobloggerio-site.netlify.app" # Hardcoded for now

def confirm_removal(posts_to_delete: list) -> bool:
    """
    Asks the user for confirmation before proceeding with the deletion of multiple posts.
    
    Args:
        posts_to_delete: A list of post dictionaries. Each dictionary should have a 'title'.
                         It's also used to determine the count of posts.
                         
    Returns:
        True if the user confirms deletion, False otherwise.
    """
    if not posts_to_delete:
        # This case should ideally be handled by the caller, but as a safeguard:
        print("No posts selected for deletion. Confirmation step skipped.")
        return False

    print(f"\nYou are about to delete the following {len(posts_to_delete)} post(s):")
    for post_data in posts_to_delete:
        print(f"  - {post_data.get('title', 'Untitled Post')}")
    
    prompt = "Are you sure you want to remove all selected posts and their related files? [y/N]: "
    user_input = input(prompt).strip().lower()
    return user_input == 'y'

def remove_files(html_filename: str):
    """Deletes the HTML, Markdown, and .meta files associated with the post."""
    html_filepath = os.path.join("blog", html_filename)
    
    markdown_basename = html_filename.replace(".html", ".md")
    markdown_filepath = os.path.join("posts", markdown_basename)
    
    meta_basename = html_filename.replace(".html", ".meta")
    meta_filepath = os.path.join("posts", meta_basename) # Correction: meta file is html_filename.replace(".html",".meta") not markdown_basename.replace(".md",".meta")

    files_to_delete = {
        "HTML": html_filepath,
        "Markdown": markdown_filepath,
        "Meta": meta_filepath
    }

    for file_type, filepath in files_to_delete.items():
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"Successfully deleted {file_type} file: {filepath}")
            except OSError as e:
                print(f"Error deleting {file_type} file {filepath}: {e}")
        else:
            print(f"{file_type} file not found: {filepath}")

def update_posts_json(html_filename: str, posts_json_path: str = "posts.json"):
    """Reads posts.json, removes the entry for the given post, and writes it back."""
    all_posts = []
    try:
        if os.path.exists(posts_json_path):
            with open(posts_json_path, "r", encoding="utf-8") as f_json:
                try:
                    all_posts = json.load(f_json)
                    if not isinstance(all_posts, list):
                        print(f"Warning: {posts_json_path} was not a valid JSON list. Re-initializing.")
                        all_posts = []
                except json.JSONDecodeError:
                    print(f"Warning: Could not decode JSON from {posts_json_path}. Re-initializing.")
                    all_posts = []
        else:
            print(f"{posts_json_path} not found. Creating a new one if posts are added later.")
            # No need to do anything else if the file doesn't exist; it will be created if a post is published

        # Filter out the post to be removed
        # Check against "filename" or "path" for flexibility
        original_count = len(all_posts)
        posts_after_removal = [
            post for post in all_posts 
            if not (post.get("filename") == html_filename or post.get("path") == os.path.join("blog", html_filename).replace(os.path.sep, '/'))
        ]

        if len(posts_after_removal) < original_count:
            with open(posts_json_path, "w", encoding="utf-8") as f_json:
                json.dump(posts_after_removal, f_json, indent=4)
            print(f"Successfully updated {posts_json_path}, removed entry for {html_filename}.")
        else:
            print(f"Entry for {html_filename} not found in {posts_json_path}. No changes made to it.")
            # Still save the file if it was malformed and re-initialized
            if not os.path.exists(posts_json_path) or (isinstance(all_posts, list) and len(all_posts) != len(posts_after_removal)): # only save if it was empty or changed
                 with open(posts_json_path, "w", encoding="utf-8") as f_json:
                    json.dump(posts_after_removal, f_json, indent=4)


    except IOError as e:
        print(f"Error reading/writing {posts_json_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while updating {posts_json_path}: {e}")


def regenerate_sitemap(posts_json_path: str = "posts.json", sitemap_xml_path: str = "sitemap.xml"):
    """Generates sitemap.xml from scratch based on the current posts.json."""
    all_posts = []
    if os.path.exists(posts_json_path):
        try:
            with open(posts_json_path, "r", encoding="utf-8") as f_json:
                all_posts = json.load(f_json)
            if not isinstance(all_posts, list):
                print(f"Warning: {posts_json_path} data for sitemap is not a list. Sitemap may be incomplete.")
                all_posts = []
        except json.JSONDecodeError:
            print(f"Error decoding {posts_json_path} for sitemap. Sitemap may be incomplete.")
            all_posts = []
        except IOError as e:
            print(f"Error reading {posts_json_path} for sitemap: {e}. Sitemap may be incomplete.")
            all_posts = []
    else:
        print(f"{posts_json_path} not found. Sitemap will be generated for homepage only or be empty if no posts.")

    try:
        sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        sitemap_content += f"<!-- IMPORTANT: Replace {SITE_URL_PLACEHOLDER} with your actual site URL -->\n"

        # Add homepage
        sitemap_content += '  <url>\n'
        sitemap_content += f'    <loc>{SITE_URL_PLACEHOLDER}/index.html</loc>\n'
        sitemap_content += f'    <lastmod>{datetime.now(timezone.utc).strftime("%Y-%m-%d")}</lastmod>\n'
        sitemap_content += '    <changefreq>daily</changefreq>\n'
        sitemap_content += '    <priority>1.0</priority>\n'
        sitemap_content += '  </url>\n'

        for post in all_posts:
            if "path" in post and "date" in post:
                post_loc = f"{SITE_URL_PLACEHOLDER}/{post['path']}"
                try:
                    post_lastmod = datetime.fromisoformat(post['date'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                except ValueError:
                    post_lastmod = datetime.now(timezone.utc).strftime("%Y-%m-%d") # Fallback
                    print(f"Warning: Could not parse date '{post.get('date')}' for sitemap entry '{post.get('path')}'. Using current date.")
                
                sitemap_content += '  <url>\n'
                sitemap_content += f'    <loc>{post_loc}</loc>\n'
                sitemap_content += f'    <lastmod>{post_lastmod}</lastmod>\n'
                sitemap_content += '    <changefreq>weekly</changefreq>\n'
                sitemap_content += '    <priority>0.8</priority>\n'
                sitemap_content += '  </url>\n'
        
        sitemap_content += '</urlset>\n'
        with open(sitemap_xml_path, "w", encoding="utf-8") as f_sitemap:
            f_sitemap.write(sitemap_content)
        print(f"Successfully regenerated {sitemap_xml_path}")

    except IOError as e:
        print(f"Error writing {sitemap_xml_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while generating {sitemap_xml_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Remove blog posts based on their sorted indices.")
    parser.add_argument("indices", type=int, nargs='+', help="A list of 1-based indices of posts to remove, after sorting by date (oldest first).")
    args = parser.parse_args()

    posts_json_path = "posts.json"
    all_posts_data = []

    # 2.a. Load posts from posts.json
    if not os.path.exists(posts_json_path):
        print(f"Error: {posts_json_path} not found. Cannot determine posts to remove.")
        return
    
    try:
        with open(posts_json_path, "r", encoding="utf-8") as f:
            all_posts_data = json.load(f)
        if not isinstance(all_posts_data, list):
            print(f"Error: {posts_json_path} does not contain a valid JSON list of posts.")
            return
    except json.JSONDecodeError:
        print(f"Error: Malformed JSON in {posts_json_path}. Cannot parse posts.")
        return
    except IOError as e:
        print(f"Error reading {posts_json_path}: {e}")
        return

    # 2.b. Sort posts by date
    valid_posts_for_sorting = []
    # Store posts that cause issues separately, though task implies they are put at the end or skipped.
    # For selection, we only care about posts that can be sorted.
    
    for post_idx, post_entry in enumerate(all_posts_data):
        post_date_str = post_entry.get("date")
        if post_date_str:
            try:
                # Handle 'Z' for UTC and ensure proper ISO format parsing
                if 'Z' in post_date_str and not post_date_str.endswith('+00:00'):
                    post_date_str = post_date_str.replace('Z', '+00:00')
                dt_obj = datetime.fromisoformat(post_date_str)
                # Store the original post entry along with its sortable date
                valid_posts_for_sorting.append({"original_post": post_entry, "date_obj": dt_obj, "original_index_in_json": post_idx})
            except ValueError:
                title = post_entry.get('title', f"Unknown Title at original index {post_idx}")
                print(f"Warning: Post '{title}' has an invalid date format ('{post_date_str}'). It will not be available for selection by index.")
        else:
            title = post_entry.get('title', f"Unknown Title at original index {post_idx}")
            print(f"Warning: Post '{title}' has no date. It will not be available for selection by index.")

    # Sort primarily by date, then by original index in JSON to ensure stable sort for same-date posts
    valid_posts_for_sorting.sort(key=lambda x: (x["date_obj"], x["original_index_in_json"]))
    
    # This is the list from which users will select posts based on displayed 1-based index
    sorted_selectable_posts = [p["original_post"] for p in valid_posts_for_sorting]
    
    if not sorted_selectable_posts:
        print("No posts with valid dates found to list or remove.")
        return
        
    print("\nAvailable posts (sorted by date, oldest first):")
    for i, post_data in enumerate(sorted_selectable_posts):
        print(f"  {i+1}. {post_data.get('title', 'Untitled Post')} (Date: {post_data.get('date', 'N/A')})")
    print("-" * 30)

    # 2.c. Create an empty list posts_to_delete
    posts_to_delete = []
    # Use a set to track indices already processed to avoid duplicates if user provides e.g. "1 1 2"
    processed_1_based_indices = set() 

    # 2.d. Iterate through user-provided indices
    for user_1_based_idx in args.indices:
        if user_1_based_idx in processed_1_based_indices:
            print(f"Info: Index {user_1_based_idx} was provided more than once. It will be processed only once.")
            continue
        processed_1_based_indices.add(user_1_based_idx)

        actual_0_based_idx = user_1_based_idx - 1 # Convert 1-based from user to 0-based for list access

        # 2.d.i. Check if the index is valid against the sorted_selectable_posts list
        if 0 <= actual_0_based_idx < len(sorted_selectable_posts):
            # 2.d.ii. Add corresponding post object to posts_to_delete
            posts_to_delete.append(sorted_selectable_posts[actual_0_based_idx])
        else:
            # 2.d.iii. Print warning for invalid index
            max_valid_index = len(sorted_selectable_posts)
            if max_valid_index == 0: # Should be caught by the "No posts" check earlier, but for safety
                 print(f"Warning: Index {user_1_based_idx} is invalid as there are no selectable posts. This index will be skipped.")
            else:
                 print(f"Warning: Index {user_1_based_idx} is invalid. Valid range is 1-{max_valid_index}. This index will be skipped.")

    # 2.e. If posts_to_delete is empty after checking all indices
    if not posts_to_delete:
        print("\nNo posts selected for deletion (either no indices provided, all were invalid, or duplicates led to empty list).")
        return

    # 2.f. Print titles of posts identified in posts_to_delete
    print("\nPosts identified for deletion (filenames are used for actual removal):")
    for post_to_remove_data in posts_to_delete:
        # The actual removal logic will need the 'filename' (e.g., 'my-post.html')
        # This filename is expected to be stored in posts.json.
        # If not directly 'filename', it might be derived from 'path' (e.g., 'blog/my-post.html')
        html_filename = post_to_remove_data.get("filename")
        if not html_filename and "path" in post_to_remove_data:
            html_filename = os.path.basename(post_to_remove_data["path"])
        
        title = post_to_remove_data.get('title', 'Untitled Post')
        if html_filename:
            print(f"  - Title: {title}, Filename: {html_filename}")
        else:
            # This case should be rare if posts.json is well-formed by publish_post.py
            print(f"  - Title: {title} (Error: Filename not found in post data. This post cannot be processed for removal by current logic.)")

    # --- Integration of confirm_removal ---
    if not confirm_removal(posts_to_delete):
        print("Removal process cancelled by user.")
        return

    print("\nUser confirmed. Proceeding with post removal...")
    
    num_successfully_processed = 0
    num_failed_to_process = 0

    for post_data in posts_to_delete:
        title = post_data.get('title', 'Untitled Post')
        html_filename = post_data.get("filename")
        
        if not html_filename and "path" in post_data: # Try to derive from path if 'filename' is missing
            html_filename = os.path.basename(post_data["path"])

        if not html_filename:
            print(f"\nError: Could not determine filename for post titled '{title}'. Skipping this post.")
            num_failed_to_process += 1
            continue

        print(f"\nProcessing removal for: '{title}' (File: {html_filename})")
        
        # 2.b. Call remove_files()
        print(f"  Attempting to remove files for {html_filename}...")
        remove_files(html_filename) # This function already prints success/failure for each file.
        
        # 2.c. Call update_posts_json()
        # TODO: Consider refactoring update_posts_json to handle a list of filenames for efficiency
        # when deleting multiple posts. For now, calling it individually.
        print(f"  Attempting to update {posts_json_path} for {html_filename}...")
        update_posts_json(html_filename, posts_json_path) # This function also prints its status.
        
        num_successfully_processed +=1

    print(f"\n--- Removal Summary ---")
    print(f"Successfully processed {num_successfully_processed} post(s) for removal.")
    if num_failed_to_process > 0:
        print(f"Failed to process {num_failed_to_process} post(s) (e.g., due to missing filenames).")

    # 3. Regenerate sitemap
    if num_successfully_processed > 0: # Only regenerate if at least one post was actually processed
        print(f"\nRegenerating sitemap ({os.path.basename(sitemap_xml_path)})...") # sitemap_xml_path is not defined, using default from function
        regenerate_sitemap(posts_json_path=posts_json_path) # Pass posts_json_path
        print("Sitemap regeneration complete.")
    else:
        print("\nSitemap regeneration skipped as no posts were successfully processed for removal.")
    
    print(f"\nRemoval process finished.")

if __name__ == "__main__":
    main()
