import os
import json
import sys
from datetime import datetime

POSTS_JSON_PATH = "posts.json"
SITEMAP_XML_PATH = "sitemap.xml"
BLOG_DIR = "blog"
POSTS_DIR = "posts"
SITE_URL = "https://your-autobloggerio-site.netlify.app"

def parse_indices(indices_str):
    """
    Parses a string of indices and ranges (e.g., "0 3 5", "0-2 4 6-7")
    into a sorted list of unique 0-based integer indices.
    """
    if not indices_str:
        print("Error: POSTS_TO_DELETE environment variable is not set or empty.")
        return None

    print(f"Parsing indices: {indices_str}")
    parsed_indices = set()
    parts = indices_str.split()
    for part in parts:
        if "-" in part:
            try:
                start, end = map(int, part.split("-"))
                if start > end:
                    print(f"Error: Invalid range '{part}'. Start index cannot be greater than end index.")
                    return None
                parsed_indices.update(range(start, end + 1))
            except ValueError:
                print(f"Error: Invalid range format '{part}'. Must be 'int-int'.")
                return None
        else:
            try:
                parsed_indices.add(int(part))
            except ValueError:
                print(f"Error: Invalid index format '{part}'. Must be an integer.")
                return None
    
    sorted_indices = sorted(list(parsed_indices))
    print(f"Parsed indices: {sorted_indices}")
    return sorted_indices

def load_and_sort_posts(file_path):
    """
    Loads posts from a JSON file, sorts them by date (oldest first).
    """
    print(f"Loading posts from {file_path}...")
    try:
        with open(file_path, "r") as f:
            posts = json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}.")
        return None

    valid_posts = []
    for i, post in enumerate(posts):
        if not isinstance(post, dict):
            print(f"Warning: Post at index {i} is not a dictionary, skipping.")
            continue
        date_str = post.get("date")
        filename = post.get("filename")
        path = post.get("path")
        
        if not date_str:
            print(f"Warning: Post {post.get('title', f'at index {i}')} is missing 'date', skipping.")
            continue
        if not filename and not path:
            print(f"Warning: Post {post.get('title', f'at index {i}')} is missing 'filename' and 'path', skipping.")
            continue
            
        try:
            # Ensure date is valid ISO format for sorting
            datetime.fromisoformat(date_str.replace("Z", "+00:00")) 
        except ValueError:
            print(f"Warning: Post {post.get('title', f'at index {i}')} has invalid date format '{date_str}', skipping.")
            continue
        
        valid_posts.append(post)

    # Sort posts by date (oldest first)
    # The strptime and strftime conversion ensures consistent format for comparison
    try:
        valid_posts.sort(key=lambda p: datetime.fromisoformat(p["date"].replace("Z", "+00:00")))
    except Exception as e:
        print(f"Error sorting posts: {e}. Please check date formats.")
        return None


    print(f"Loaded and sorted {len(valid_posts)} posts.")
    return valid_posts

def get_post_filenames(post):
    """Determines HTML, Markdown, and meta filenames for a post."""
    html_filename = post.get("filename")
    if not html_filename:
        path = post.get("path")
        if path:
            html_filename = os.path.basename(path)
        else:
            return None, None, None # Should not happen if load_and_sort_posts validated correctly

    if not html_filename.endswith(".html"):
        print(f"Warning: Post HTML filename '{html_filename}' does not end with .html. Proceeding, but this might be an error.")
        # Attempt to fix or use as is, depending on strictness desired. For now, use as is.

    base_filename = html_filename[:-5] if html_filename.endswith(".html") else html_filename
    md_filename = base_filename + ".md"
    meta_filename = base_filename + ".meta"

    return html_filename, md_filename, meta_filename


def delete_post_files(posts_to_delete_objects):
    """
    Deletes the HTML, Markdown, and meta files for the given post objects.
    """
    if not posts_to_delete_objects:
        print("No posts selected for deletion.")
        return

    for post in posts_to_delete_objects:
        title = post.get("title", "Unknown Title")
        print(f"Processing post for deletion: {title}")

        html_filename, md_filename, meta_filename = get_post_filenames(post)

        if not html_filename:
            print(f"Could not determine filenames for post: {title}. Skipping deletion.")
            continue

        paths_to_delete = [
            os.path.join(BLOG_DIR, html_filename),
            os.path.join(POSTS_DIR, md_filename),
            os.path.join(POSTS_DIR, meta_filename),
        ]

        for file_path in paths_to_delete:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                else:
                    print(f"File not found, skipping: {file_path}")
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")


def update_posts_json(all_posts, posts_to_delete_objects, file_path):
    """
    Removes deleted posts from the list and writes it back to posts.json.
    """
    print(f"Updating {file_path}...")
    
    # Create a list of unique identifiers for posts to delete (e.g., filename or path)
    # This helps in reliably removing them from the original list.
    # Using (filename, date) tuple as a more robust key if titles/filenames are not unique
    deleted_post_keys = set()
    for post in posts_to_delete_objects:
        html_filename, _, _ = get_post_filenames(post)
        if html_filename:
            deleted_post_keys.add((html_filename, post.get("date")))

    updated_posts = [
        post for post in all_posts 
        if (get_post_filenames(post)[0], post.get("date")) not in deleted_post_keys
    ]

    # Re-sort posts by date (newest first) before writing
    try:
        updated_posts.sort(key=lambda p: datetime.fromisoformat(p["date"].replace("Z", "+00:00")), reverse=True)
        print(f"Re-sorted {len(updated_posts)} posts by date (newest first).")
    except Exception as e:
        # Log an error if sorting fails for some reason, but proceed with unsorted if necessary
        print(f"Warning: Could not re-sort posts before saving: {e}")
    try:
        with open(file_path, "w") as f:
            json.dump(updated_posts, f, indent=4)
        print(f"{file_path} updated successfully. {len(all_posts) - len(updated_posts)} posts removed.")
    except IOError as e:
        print(f"Error writing updated posts to {file_path}: {e}")
        return False
    return True

def regenerate_sitemap(posts_file_path, sitemap_output_path):
    """
    Generates sitemap.xml from the current posts.json.
    """
    print(f"Regenerating {sitemap_output_path}...")
    try:
        with open(posts_file_path, "r") as f:
            posts = json.load(f)
    except FileNotFoundError:
        print(f"Error: {posts_file_path} not found. Cannot generate sitemap.")
        return False
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {posts_file_path}. Cannot generate sitemap.")
        return False

    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Add homepage
    sitemap_content += '  <url>\n'
    sitemap_content += f'    <loc>{SITE_URL}/index.html</loc>\n'
    # Add lastmod for homepage? For now, keeping it simple.
    sitemap_content += '  </url>\n'

    for post in posts:
        html_filename, _, _ = get_post_filenames(post)
        if not html_filename:
            print(f"Warning: Skipping post in sitemap due to missing filename/path: {post.get('title', 'Unknown title')}")
            continue
            
        # Ensure leading slash for URL path
        post_path = html_filename if html_filename.startswith('/') else '/' + html_filename
        # If posts are in a subdirectory like /blog/, ensure it's part of the loc
        # Assuming html_filename from get_post_filenames is just the file, not path like "blog/file.html"
        # If it can be "blog/file.html", then SITE_URL + post_path is fine.
        # If it's just "file.html", we need to prepend BLOG_DIR.
        # For now, assuming html_filename is just the name, so prepend BLOG_DIR.
        
        # Corrected logic: post.get("path") already includes "blog/" if present
        loc_path = post.get("path")
        if not loc_path: # Fallback if "path" is not present but "filename" is
            loc_path = f"{BLOG_DIR}/{html_filename}"

        # Ensure loc_path starts with a slash
        if not loc_path.startswith("/"):
            loc_path = "/" + loc_path

        sitemap_content += '  <url>\n'
        sitemap_content += f'    <loc>{SITE_URL}{loc_path}</loc>\n'
        # Add lastmod if available and consistently formatted
        date_str = post.get("date")
        if date_str:
            try:
                # Format to YYYY-MM-DD, required by sitemap
                sitemap_date = datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
                sitemap_content += f'    <lastmod>{sitemap_date}</lastmod>\n'
            except ValueError:
                print(f"Warning: Invalid date format '{date_str}' for post {post.get('title', '')}, not adding lastmod to sitemap entry.")
        sitemap_content += '  </url>\n'
        
    sitemap_content += '</urlset>\n'

    try:
        with open(sitemap_output_path, "w") as f:
            f.write(sitemap_content)
        print(f"{sitemap_output_path} regenerated successfully.")
    except IOError as e:
        print(f"Error writing sitemap to {sitemap_output_path}: {e}")
        return False
    return True

def main():
    """
    Main execution logic for the delete_posts script.
    """
    print("--- Starting Post Deletion Script ---")

    # 1. Get indices from environment variable
    indices_str = os.environ.get("POSTS_TO_DELETE")
    if not indices_str:
        print("Error: POSTS_TO_DELETE environment variable not set.")
        print("Please set it to a string of indices/ranges, e.g., '0 3 5' or '0-2 4'.")
        sys.exit(1) # Use sys.exit for clearer exit codes

    indices_to_delete = parse_indices(indices_str)
    if indices_to_delete is None:
        print("Exiting due to errors in parsing indices.")
        sys.exit(1)
    if not indices_to_delete:
        print("No valid indices provided for deletion. Exiting.")
        sys.exit(0) # Not an error, just nothing to do.

    # 2. Load and sort posts
    all_posts = load_and_sort_posts(POSTS_JSON_PATH)
    if all_posts is None:
        print(f"Exiting due to errors loading or sorting {POSTS_JSON_PATH}.")
        sys.exit(1)
    
    if not all_posts:
        print("No posts found in posts.json. Nothing to delete.")
        sys.exit(0)

    # 3. Identify posts for deletion
    posts_to_delete_objects = []
    invalid_indices = []
    for index in indices_to_delete:
        if 0 <= index < len(all_posts):
            posts_to_delete_objects.append(all_posts[index])
        else:
            invalid_indices.append(index)
            print(f"Warning: Index {index} is out of bounds (total posts: {len(all_posts)}).")

    if invalid_indices:
        print(f"Ignoring out-of-bounds indices: {invalid_indices}")

    if not posts_to_delete_objects:
        print("No posts selected for deletion after filtering (e.g., all indices out of bounds).")
        sys.exit(0)
        
    print(f"Identified {len(posts_to_delete_objects)} posts for deletion:")
    for post in posts_to_delete_objects:
         print(f"  - {post.get('title', get_post_filenames(post)[0] or 'Unknown Post')}")


    # 4. Delete post files
    delete_post_files(posts_to_delete_objects)

    # 5. Update posts.json
    if not update_posts_json(all_posts, posts_to_delete_objects, POSTS_JSON_PATH):
        print("Exiting due to error updating posts.json.")
        sys.exit(1) # Critical error if posts.json cannot be updated

    # 6. Regenerate sitemap.xml
    if not regenerate_sitemap(POSTS_JSON_PATH, SITEMAP_XML_PATH):
        # Non-critical, script can still succeed if sitemap fails, but log it.
        print("Warning: Sitemap generation failed. Please check manually.")
    
    print("--- Post Deletion Script Finished Successfully ---")
    # Implied sys.exit(0) if no errors forced an earlier exit.

if __name__ == "__main__":
    import sys # Import sys here for sys.exit()
    main()
