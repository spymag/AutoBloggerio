# Affiliate Links Configuration (`affiliate_links.json`)

This file (`config/affiliate_links.json`) is used to manage affiliate links that can be automatically inserted into generated blog posts.

## Structure

The file should contain a JSON array of objects. Each object represents an affiliate link configuration and should have the following properties:

*   `"keywords"` (array of strings): A list of keywords or phrases to search for in the blog post content. The matching is case-insensitive.
*   `"link"` (string): The full affiliate URL that the keyword will link to.
*   `"description"` (string): A brief description of the product or service for your reference. This is not currently used in the post itself but helps manage your links.

## Example

```json
[
  {
    "keywords": ["sample product", "example tool", "specific keyword"],
    "link": "https://www.amazon.com/your-product-link?tag=yourtag-20",
    "description": "A great sample product for various needs."
  },
  {
    "keywords": ["another service", "online course platform"],
    "link": "https://www.coursera.org/your-course-link?utm_source=affiliate&utm_medium=yourid",
    "description": "An online course platform for learning new skills."
  },
  {
    "keywords": ["data storage solution", "cloud backup"],
    "link": "https://www.backblaze.com/your-referral-link",
    "description": "Backblaze cloud backup service."
  }
]
```

## How to Populate

1.  **Identify Products/Services**: Choose products or services relevant to your blog's content that offer affiliate programs.
2.  **Get Affiliate Links**: Sign up for these affiliate programs and obtain your unique affiliate URLs.
3.  **Choose Keywords**: For each affiliate link, decide on a set of keywords or phrases that, when found in a blog post, should be converted into an affiliate link.
    *   Be specific to avoid irrelevant linking.
    *   Consider variations of keywords.
4.  **Add to JSON**:
    *   Open `config/affiliate_links.json`.
    *   If the file is empty or contains only the initial example, you can replace the example or add to it.
    *   For each affiliate program, create a new JSON object with the `keywords`, `link`, and `description` fields.
    *   Add this object to the main JSON array. Ensure the overall structure remains a valid JSON array.

## How It's Used

The `generate_post.py` script will:

1.  Read this `affiliate_links.json` file.
2.  If the file is empty or doesn't exist, the affiliate linking step is skipped.
3.  For each generated blog post, it will scan the content for the keywords you've specified.
4.  If a keyword is found, its first occurrence (or a limited number of occurrences, to avoid spamming) will be replaced with a Markdown link: `[keyword](your_affiliate_link)`.
5.  A maximum of 2-3 affiliate links are typically inserted per post.

## Important Notes

*   **Case-Insensitive Matching**: Keyword matching is case-insensitive. "Sample Product" and "sample product" will both be matched.
*   **First Occurrence**: Currently, the script is set to replace only the first occurrence of a found keyword to prevent over-linking.
*   **Markdown Integrity**: The replacement aims to preserve existing Markdown structure, but complex or unusual Markdown might have unpredictable results. Always review posts if possible.
*   **Relevance**: Ensure your affiliate links are relevant to the content where they are placed. This provides value to readers and maintains trust.
*   **Disclosure**: An affiliate disclosure is automatically added to the post template (`post_template.html`) to inform readers about the potential use of affiliate links. This is a common legal and ethical requirement.

By keeping this `config/affiliate_links.json` file updated with relevant affiliate programs, you can automate a part of your blog monetization strategy.
Remember to commit this file to your repository if you want the GitHub Action to use your defined affiliate links. However, if you prefer to keep your affiliate links private, do not commit this file and manage it locally or via GitHub secrets (though the current script reads it from the file system).
