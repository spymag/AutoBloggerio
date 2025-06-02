# AutoBlogger
Blog that posts on daily basis topics produced by AI

## Automated Daily Blog Posting with GitHub Actions

This project includes a GitHub Actions workflow to automate the discovery, generation, and publication of blog posts on a daily schedule.

### How It Works

The workflow is defined in `.github/workflows/daily_blog_post.yml`. It performs the following steps:

1.  **Scheduled Trigger**: Runs daily at 00:00 UTC by default (this can be configured via the `cron` expression in the workflow file). It can also be triggered manually from the GitHub Actions tab.
2.  **Checkout Code**: Checks out the latest version of your repository.
3.  **Set up Python**: Initializes a Python environment.
4.  **Install Dependencies**: Installs the Python packages listed in `requirements.txt`.
5.  **Run Workflow Script**: Executes the `main_daily_workflow.py` script. This script:
    *   Discovers trending topics using NewsAPI (or uses sample topics if the API key is not set).
    *   Generates blog post content for these topics using OpenAI's API (or uses placeholder content if the API key is not set).
    *   Publishes the generated posts by creating HTML files in the `blog/` directory and updating `posts.json`.
6.  **Commit and Push Changes**:
    *   If any new files are created or existing files (like `posts.json`, new HTML files in `blog/`, or new Markdown files in `posts/`) are modified by the workflow script, these changes are automatically committed to the repository.
    *   The commit is made by a 'GitHub Actions Bot' user.
    *   The changes are then pushed to the main branch.

### Setup Instructions

To enable and use this automated workflow, you need to configure API keys as GitHub Actions secrets:

1.  **Obtain API Keys**:
    *   **NewsAPI**: Get a free API key from [NewsAPI.org](https://newsapi.org/) by registering. This key is used by `discover_topics.py` to fetch current news headlines as potential blog topics.
    *   **OpenAI API Key**: Obtain an API key from [OpenAI](https://platform.openai.com/signup/). This key is used by `generate_post.py` to generate blog post content based on the discovered topics.

2.  **Add Secrets to GitHub Repository**:
    *   Go to your GitHub repository.
    *   Click on **Settings** (usually in the top navigation bar of the repository).
    *   In the left sidebar, navigate to **Secrets and variables** -> **Actions**.
    *   Click the **New repository secret** button for each key:
        *   Create a secret named `NEWSAPI_KEY` and paste your NewsAPI key as its value.
        *   Create another secret named `OPENAI_API_KEY` and paste your OpenAI API key as its value.

    These secrets will be securely passed to the GitHub Action when it runs.

3.  **Adjust Schedule (Optional)**:
    *   The default schedule is daily at 00:00 UTC. If you wish to change this, edit the `cron` value in `.github/workflows/daily_blog_post.yml`:
        ```yaml
        on:
          schedule:
            - cron: "0 0 * * *" # Example: Runs daily at 00:00 UTC
        ```
    *   You can use a cron schedule generator (like [crontab.guru](https://crontab.guru/)) to help create the correct syntax for your desired frequency.

### Automatic Deployment with Netlify

If you have deployed this project to Netlify (or a similar static site hosting service that integrates with GitHub):

*   When the GitHub Action commits and pushes the newly generated blog posts and updated `posts.json` to your repository, this will typically trigger a new build and deployment on Netlify.
*   This means your live blog will be automatically updated with the new posts without any manual intervention. Ensure your Netlify `publish` directory is set correctly (e.g., to the root `.` if `index.html`, `blog/`, `css/`, `js/`, and `posts.json` are all served from there, which is the current setup). The `netlify.toml` file is configured for this.

That's it! Once configured, the GitHub Action will handle the daily content generation and updates for your Autoblogger.

## Delete Selected Posts GitHub Action

This project includes a GitHub Actions workflow defined in `.github/workflows/delete-selected-posts.yml` to help you remove specific blog posts from your site.

### How It Works

The workflow can be triggered in two ways:

1.  **Manually**: You can trigger it from the GitHub Actions tab ("Delete Selected Posts" workflow) using `workflow_dispatch`. When running manually, you can provide an input named `posts_to_delete_input`.
2.  **Scheduled**: It is also scheduled to run daily at midnight UTC, though for deletion, manual triggering is more common.

### Specifying Posts for Deletion

The posts to be deleted are specified by a string of 0-based indices, where `0` is the oldest post, `1` is the next oldest, and so on. The format can be:
*   Space-separated individual numbers (e.g., `"0 3 5"`).
*   Space-separated ranges (e.g., `"0-2 4 6-7"`). A range "a-b" includes all posts from index `a` to `b`.

This string is provided via:
*   The `posts_to_delete_input` field when triggering the action manually.
*   The `POSTS_TO_DELETE` repository variable (under Settings -> Secrets and variables -> Actions -> Variables) if the manual input is not provided or for scheduled runs.

### Actions Performed

When the workflow runs, the `.github/scripts/delete_posts.py` script will:
1.  Parse the input indices.
2.  Load and sort all posts from `posts.json` by date (oldest first).
3.  Identify the specific posts corresponding to the given indices.
4.  Delete the associated files for each selected post:
    *   HTML file from the `blog/` directory.
    *   Markdown file from the `posts/` directory.
    *   Meta file from the `posts/` directory.
5.  Update `posts.json` by removing the entries for the deleted posts.
6.  Regenerate the `sitemap.xml` to reflect the changes.

### Automatic Commit

If any posts are deleted, the workflow will automatically commit the changes (deleted files, updated `posts.json`, and new `sitemap.xml`) back to your repository.

## Important Placeholders to Customize

Before deploying or using your Autobloggerio site extensively, make sure to update the following placeholder values:

1.  **Contact Email (`contact.html`)**:
    *   Open `contact.html`.
    *   Find the line: `<p>You can email us at: <a href="mailto:contact@example.com">contact@example.com</a>.</p>`
    *   Replace `contact@example.com` with your actual email address or preferred contact method.

2.  **Sitemap URL (`robots.txt` and `publish_post.py`)**:
    *   **`robots.txt`**:
        *   Open `robots.txt`.
        *   Find the line: `Sitemap: https://your-autobloggerio-site.netlify.app/sitemap.xml`
        *   Replace `https://your-autobloggerio-site.netlify.app` with your actual deployed site's base URL.
    *   **`publish_post.py`**:
        *   Open `publish_post.py`.
        *   Find the variable: `site_url_placeholder = "https://your-autobloggerio-site.netlify.app"`
        *   Replace the placeholder URL with your actual deployed site's base URL. This ensures the generated `sitemap.xml` uses correct links.

3.  **About Page Content (`about.html`)**:
    *   Open `about.html`.
    *   Customize the placeholder paragraph: `[Customize this text to tell your visitors more about your specific Autobloggerio site's mission or focus.]`

It's crucial to update these values for proper site functionality, contact methods, and SEO.

## Integrating Advertisements

This project includes predefined placeholder slots in the HTML templates where you can integrate advertisement snippets from ad networks (e.g., Google AdSense, Carbon Ads, or other ethical ad networks).

### Ad Placeholder Locations

The following ad slots have been added:

1.  **Ad Slot 1: Below Post Title (`post_template.html`)**
    *   Located directly under the main post title and before the main content begins.
    *   Identified by the CSS classes `ad-slot ad-slot-post-top`.
    *   Placeholder HTML:
        ```html
        <!-- Placeholder for Ad Slot 1: Below Post Title -->
        <div class="ad-slot ad-slot-post-top" style="min-height: 90px; margin-bottom: 20px; background-color: #f0f0f0; text-align: center; line-height: 90px;">Advertisement Placeholder (e.g., 728x90)</div>
        ```

2.  **Ad Slot 2: End of Post Content (`post_template.html`)**
    *   Located at the very end of the article content, before the affiliate disclosure and footer.
    *   Identified by the CSS classes `ad-slot ad-slot-post-bottom`.
    *   Placeholder HTML:
        ```html
        <!-- Placeholder for Ad Slot 2: End of Post Content -->
        <div class="ad-slot ad-slot-post-bottom" style="min-height: 90px; margin-top: 20px; background-color: #f0f0f0; text-align: center; line-height: 90px;">Advertisement Placeholder (e.g., 728x90)</div>
        ```

3.  **Ad Slot 3: Top of Post List on Index Page (`index.html`)**
    *   Located at the top of the main content area on the homepage, before the list of blog posts begins.
    *   Identified by the CSS classes `ad-slot ad-slot-index-top`.
    *   Placeholder HTML:
        ```html
        <!-- Placeholder for Ad Slot 3: Top of Post List on Index -->
        <div class="ad-slot ad-slot-index-top" style="min-height: 90px; margin-bottom: 20px; background-color: #f0f0f0; text-align: center; line-height: 90px;">Advertisement Placeholder (e.g., 728x90)</div>
        ```

### How to Integrate Your Ad Code

1.  **Sign up for an Ad Network**: Choose an ad network and get approved. They will provide you with HTML/JavaScript code snippets for each ad unit you create.
2.  **Locate the Placeholder**: Open the relevant HTML file (`post_template.html` or `index.html`) in a text editor.
3.  **Replace the Placeholder**:
    *   Find the HTML comment indicating the ad slot you want to use (e.g., `<!-- Placeholder for Ad Slot 1: Below Post Title -->`).
    *   You can either:
        *   **Replace the entire `<div>`**: Delete the placeholder `<div>` element and paste your ad network's code snippet in its place.
        *   **Replace the content within the `<div>`**: Keep the `<div class="ad-slot ...">` and replace its inner text (e.g., "Advertisement Placeholder...") with your ad network's code snippet. This might be useful if you want to keep the `.ad-slot` class for styling.
4.  **Save Changes**: Save the HTML file.
5.  **Commit and Push**: If you're using Git, commit these changes and push them to your repository. If Netlify or a similar service is deploying your site, it should pick up these changes automatically.

### Important Considerations

*   **Ad Network Guidelines**: Always adhere to your chosen ad network's terms of service and placement guidelines. Some networks have strict rules about where ads can be placed, how many ads per page, etc.
*   **Ad Sizes**: The placeholder divs have a `min-height: 90px` and suggest a common ad size like 728x90. You might need to adjust the styling (inline or in `css/style.css`) based on the actual ad sizes provided by your network.
*   **User Experience**: Be mindful of how ads affect the user experience. Too many ads or intrusive ads can deter visitors.
*   **Responsive Design**: Ensure your ads are responsive or that you choose ad units that work well on different screen sizes. The current site styling is basic, so further responsive design work might be needed for optimal ad display.
*   **Testing**: After integrating ad code, test your site thoroughly on different devices and browsers to ensure ads display correctly and don't break the layout.
*   **`ads.txt`**: Some ad networks require you to add an `ads.txt` file to the root of your site. Follow their instructions for this. You can place this file in the root of your project, and it will be deployed with the rest of your site by Netlify.
