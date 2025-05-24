import argparse
import os
import json
from datetime import datetime, timezone

SITE_URL_PLACEHOLDER = "https://your-autobloggerio-site.netlify.app" # Hardcoded for now

def confirm_removal(html_filename: str) -> bool:
    """Asks the user for confirmation before proceeding with deletion."""
    prompt = f"Are you sure you want to remove {html_filename} and its related files (Markdown, meta)? [y/N]: "
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
    parser = argparse.ArgumentParser(description="Remove a blog post and its related files, and update site metadata.")
    parser.add_argument("html_filename", type=str, help="The filename of the HTML post in the 'blog/' directory (e.g., my-post.html).")
    args = parser.parse_args()

    if not args.html_filename.endswith(".html"):
        print("Error: html_filename must end with .html")
        return

    if not confirm_removal(args.html_filename):
        print("Removal cancelled by user.")
        return

    print(f"\nStarting removal process for {args.html_filename}...")
    
    # 1. Delete files
    remove_files(args.html_filename)
    
    # 2. Update posts.json
    update_posts_json(args.html_filename)
    
    # 3. Regenerate sitemap.xml
    # This should use the updated posts.json
    regenerate_sitemap()
    
    print(f"\nRemoval process for {args.html_filename} completed.")

if __name__ == "__main__":
    main()
