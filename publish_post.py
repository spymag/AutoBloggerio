import argparse
import os
import markdown2
import re
import json # For handling posts.json
from datetime import datetime, timezone # For timestamps

def extract_h1_title(markdown_content: str, fallback_filename: str) -> str:
    """
    Extracts the H1 title from Markdown content.
    If no H1 is found, generates a title from the fallback_filename.
    """
    match = re.search(r'^#\s+(.*)', markdown_content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    else:
        # Fallback: Convert filename to title (e.g., "my-post.md" -> "My Post")
        title = fallback_filename.replace(".md", "")
        title = title.replace("-", " ")
        # Capitalize first letter of each word
        return ' '.join(word.capitalize() for word in title.split())

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
    # 1. Setup command-line argument parsing
    parser = argparse.ArgumentParser(description="Publish a blog post from a Markdown file.")
    parser.add_argument("markdown_filename", type=str, help="The name of the Markdown file in the 'posts' directory (e.g., my-topic.md).")
    args = parser.parse_args()

    markdown_file_basename = args.markdown_filename
    markdown_filepath = os.path.join("posts", markdown_file_basename)

    # 2. Define paths and create directories
    post_template_path = "post_template.html"
    blog_dir = "blog"
    
    if not os.path.exists(blog_dir):
        try:
            os.makedirs(blog_dir)
            print(f"Created directory: {blog_dir}")
        except OSError as e:
            print(f"Error creating directory {blog_dir}: {e}")
            return

    # 3. Read the Markdown file
    try:
        with open(markdown_filepath, "r", encoding="utf-8") as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"Error: Markdown file not found at {markdown_filepath}")
        return
    except IOError as e:
        print(f"Error reading file {markdown_filepath}: {e}")
        return

    # Replace {{DATE}} placeholder with current date
    # Using UTC date for consistency, though a local date might also be acceptable
    # depending on desired timezone handling for "Published" date.
    # For this task, let's use the current UTC date.
    current_date_formatted = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    markdown_content = markdown_content.replace("Published: {{DATE}}", f"Published: {current_date_formatted}")
    # Also handle variations in case the placeholder has different spacing or casing,
    # though the primary target is "Published: {{DATE}}"
    markdown_content = re.sub(r'Published:\s*\{\{DATE\}\}', f"Published: {current_date_formatted}", markdown_content, flags=re.IGNORECASE)


    # 4. Convert Markdown to HTML
    try:
        html_content = markdown2.markdown(markdown_content, extras=["fenced-code-blocks", "cuddled-lists", "tables"])
    except Exception as e:
        print(f"Error converting Markdown to HTML: {e}")
        return
        
    # 5. Read the post_template.html
    try:
        with open(post_template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
    except FileNotFoundError:
        print(f"Error: Post template not found at {post_template_path}")
        return
    except IOError as e:
        print(f"Error reading file {post_template_path}: {e}")
        return

    # 6. Inject content into the template
    # Derive title
    post_title = extract_h1_title(markdown_content, markdown_file_basename)
    sanitized_title_for_filename = sanitize_filename(post_title)

    # Replace placeholders
    final_html = template_content.replace("{{POST_TITLE}}", post_title)
    final_html = final_html.replace("{{POST_CONTENT}}", html_content)

    # 6. Inject content into the template
    # Derive title
    post_title = extract_h1_title(markdown_content, markdown_file_basename)
    
    # Read .meta file for meta description
    meta_description = ""
    meta_filepath = os.path.join("posts", markdown_file_basename.replace(".md", ".meta"))
    if os.path.exists(meta_filepath):
        try:
            with open(meta_filepath, "r", encoding="utf-8") as f_meta:
                meta_description = f_meta.read().strip()
            if meta_description:
                 print(f"Successfully read meta description from {meta_filepath}")
            else:
                print(f"Meta file {meta_filepath} was empty.")
        except IOError as e_meta:
            print(f"Error reading meta file {meta_filepath}: {e_meta}. Using fallback.")
    else:
        print(f"Meta file {meta_filepath} not found. Using fallback meta description.")

    if not meta_description:
        # Fallback: first ~150 chars of post content (after stripping Markdown)
        # Simple Markdown stripping: remove lines starting with #, *, -, >, ``` and HTML tags
        text_content = re.sub(r'^\s*#+\s*.*$', '', markdown_content, flags=re.MULTILINE) # Remove headers
        text_content = re.sub(r'^\s*[\*\-]\s*.*$', '', text_content, flags=re.MULTILINE) # Remove list items
        text_content = re.sub(r'^\s*>\s*.*$', '', text_content, flags=re.MULTILINE)    # Remove blockquotes
        text_content = re.sub(r'```.*?```', '', text_content, flags=re.DOTALL)         # Remove code blocks
        text_content = re.sub(r'<[^>]+>', '', text_content)                             # Remove HTML tags
        text_content = ' '.join(text_content.split()) # Normalize whitespace
        meta_description = text_content[:150].strip() + "..." if len(text_content) > 150 else text_content.strip()
        if meta_description:
            print(f"Generated fallback meta description: \"{meta_description[:50]}...\"")
        else:
            meta_description = "Read more on Autobloggerio." # Absolute fallback
            print("Used absolute fallback meta description as content was too short or empty.")


    # Replace placeholders
    final_html = template_content.replace("{{POST_TITLE}}", post_title)
    final_html = final_html.replace("{{POST_CONTENT}}", html_content)
    final_html = final_html.replace("{{META_DESCRIPTION}}", meta_description.replace('"', '&quot;')) # Escape quotes

    # 7. Save the new HTML file
    html_filename = sanitized_title_for_filename + ".html"
    output_filepath = os.path.join(blog_dir, html_filename)
    posts_json_path = "posts.json" # In the root directory
    sitemap_xml_path = "sitemap.xml" # In the root directory
    site_url_placeholder = "https://your-autobloggerio-site.netlify.app" # Placeholder for sitemap

    try:
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(final_html)
        print(f"Successfully published post: {output_filepath}")

        # 8. Update posts.json
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
            
            new_post_entry = {
                "title": post_title,
                "filename": html_filename,
                "path": output_filepath.replace(os.path.sep, '/'),
                "date": datetime.now(timezone.utc).isoformat()
            }

            updated = False
            for i, post in enumerate(all_posts):
                if post.get("path") == new_post_entry["path"]:
                    all_posts[i] = new_post_entry
                    updated = True
                    print(f"Updated existing entry in {posts_json_path} for {new_post_entry['path']}")
                    break
            if not updated:
                all_posts.append(new_post_entry)
                print(f"Added new entry to {posts_json_path} for {new_post_entry['path']}")

            all_posts.sort(key=lambda x: x.get("date", ""), reverse=True)

            with open(posts_json_path, "w", encoding="utf-8") as f_json:
                json.dump(all_posts, f_json, indent=4)
            print(f"Successfully updated {posts_json_path}")

        except Exception as e_json:
            print(f"Error updating {posts_json_path}: {e_json}")
            # Continue to sitemap generation even if posts.json fails, it might use old data or be empty

        # 9. Generate sitemap.xml
        try:
            sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            sitemap_content += f"<!-- IMPORTANT: Replace {site_url_placeholder} with your actual site URL -->\n"

            # Add homepage
            sitemap_content += '  <url>\n'
            sitemap_content += f'    <loc>{site_url_placeholder}/index.html</loc>\n'
            # Use current date for homepage lastmod, or a fixed date if preferred
            sitemap_content += f'    <lastmod>{datetime.now(timezone.utc).strftime("%Y-%m-%d")}</lastmod>\n'
            sitemap_content += '    <changefreq>daily</changefreq>\n'
            sitemap_content += '    <priority>1.0</priority>\n'
            sitemap_content += '  </url>\n'

            # Add blog posts from all_posts (which should be the most current list)
            if not all_posts and os.path.exists(posts_json_path): # If all_posts is empty due to error above, try reading again
                 print(f"Attempting to read {posts_json_path} again for sitemap as current list is empty.")
                 with open(posts_json_path, "r", encoding="utf-8") as f_json_sitemap:
                     all_posts_sitemap = json.load(f_json_sitemap)
                     if not isinstance(all_posts_sitemap, list): all_posts_sitemap = []
                 posts_for_sitemap = all_posts_sitemap
            else:
                 posts_for_sitemap = all_posts


            for post in posts_for_sitemap:
                if "path" in post and "date" in post:
                    post_loc = f"{site_url_placeholder}/{post['path']}"
                    # Format date to YYYY-MM-DD
                    try:
                        post_lastmod = datetime.fromisoformat(post['date'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    except ValueError:
                        post_lastmod = datetime.now(timezone.utc).strftime("%Y-%m-%d") # Fallback
                        print(f"Warning: Could not parse date '{post['date']}' for sitemap. Using current date.")
                    
                    sitemap_content += '  <url>\n'
                    sitemap_content += f'    <loc>{post_loc}</loc>\n'
                    sitemap_content += f'    <lastmod>{post_lastmod}</lastmod>\n'
                    sitemap_content += '    <changefreq>weekly</changefreq>\n' # Or 'monthly'
                    sitemap_content += '    <priority>0.8</priority>\n'
                    sitemap_content += '  </url>\n'
            
            sitemap_content += '</urlset>\n'
            with open(sitemap_xml_path, "w", encoding="utf-8") as f_sitemap:
                f_sitemap.write(sitemap_content)
            print(f"Successfully generated/updated {sitemap_xml_path}")

        except Exception as e_sitemap:
            print(f"Error generating {sitemap_xml_path}: {e_sitemap}")

    except IOError as e:
        print(f"Error writing HTML file {output_filepath}: {e}")

if __name__ == "__main__":
    main()
