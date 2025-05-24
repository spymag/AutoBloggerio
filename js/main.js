document.addEventListener('DOMContentLoaded', () => {
    const postListContainer = document.getElementById('post-list');
    const searchInput = document.getElementById('searchInput');
    const postsJsonPath = 'posts.json'; // Assuming posts.json is in the root

    let allPosts = []; // To store all fetched posts for searching

    if (!postListContainer) {
        console.error('Error: Post list container #post-list not found.');
        return;
    }

    function renderPosts(postsToRender) {
        // Clear the "Loading posts..." or existing posts message
        postListContainer.innerHTML = ''; 

        if (postsToRender.length === 0) {
            postListContainer.innerHTML = '<p>No posts found matching your criteria.</p>';
            if (searchInput && searchInput.value === '') { // If search is empty and no posts, show default
                postListContainer.innerHTML = '<p>No posts yet. Check back soon!</p>';
            }
            return;
        }

        postsToRender.forEach(post => {
            if (!post.title || !post.path || !post.date) {
                console.warn('Skipping post with missing data:', post);
                return; // Skip this post if essential data is missing
            }

            const article = document.createElement('article');
            
            const titleLink = document.createElement('a');
            titleLink.href = post.path;
            
            const titleHeader = document.createElement('h3'); // Using H3 for post titles in a list
            titleHeader.textContent = post.title;
            titleLink.appendChild(titleHeader);

            const dateParagraph = document.createElement('p');
            dateParagraph.classList.add('post-date');
            try {
                const formattedDate = new Date(post.date).toLocaleDateString('en-US', {
                    year: 'numeric', month: 'long', day: 'numeric'
                });
                dateParagraph.textContent = `Published on ${formattedDate}`;
            } catch (e) {
                console.warn(`Could not parse date for post "${post.title}": ${post.date}`, e);
                dateParagraph.textContent = `Date: ${post.date}`; // Fallback to raw date
            }

            article.appendChild(titleLink);
            article.appendChild(dateParagraph);
            postListContainer.appendChild(article);
        });
    }

    fetch(postsJsonPath)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} while fetching ${postsJsonPath}`);
            }
            return response.json();
        })
        .then(posts => {
            if (!Array.isArray(posts)) {
                console.error('Error: posts.json is not a valid JSON array.');
                postListContainer.innerHTML = '<p>Error loading posts: Data is not in expected format.</p>';
                return;
            }
            allPosts = posts; // Store all posts
            renderPosts(allPosts); // Initial render
        })
        .catch(error => {
            console.error('Error fetching or processing posts:', error);
            postListContainer.innerHTML = `<p>Error loading posts. Please check the console for details. (${error.message})</p>`;
            allPosts = []; // Ensure allPosts is empty on error
            renderPosts(allPosts); // Attempt to render (will show "No posts yet")
        });

    if (searchInput) {
        searchInput.addEventListener('input', (event) => {
            const searchTerm = event.target.value.toLowerCase().trim();
            if (searchTerm === "") {
                renderPosts(allPosts); // If search is cleared, show all posts
            } else {
                const filteredPosts = allPosts.filter(post => 
                    post.title && post.title.toLowerCase().includes(searchTerm)
                    // Add other fields to search if needed, e.g., post.content.toLowerCase().includes(searchTerm)
                );
                renderPosts(filteredPosts);
            }
        });
    } else {
        console.warn("Search input #searchInput not found. Search functionality will be disabled.");
    }
});
