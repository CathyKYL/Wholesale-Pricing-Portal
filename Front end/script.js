/* ========================================
   LIVE DATA MODE - NO MOCK DATA
   ======================================== */
// All product data is fetched from PostgreSQL database via Supabase
// See dataService.js for data fetching logic

/* ========================================
   GLOBAL STATE & ELEMENTS
   ======================================== */
let currentMarket = 'US';
let currentCurrency = 'USD';  // Track current display currency
let catalogMarket = 'US';  // Track catalog marketplace filter
let currentProduct = null;
let charts = {
    buybox: null,
    rank: null
};

// DOM Elements
const navTabs = document.querySelectorAll('.nav-tab');
const tabContents = document.querySelectorAll('.tab-content');
const searchBtn = document.getElementById('search-btn');
const searchInput = document.getElementById('search-input');
const searchType = document.getElementById('search-type');
const marketToggle = document.getElementById('market-toggle');
const initialMessage = document.getElementById('initial-message');
const resultsSection = document.getElementById('results-section');
const catalogGrid = document.getElementById('catalog-grid');
const logoHome = document.getElementById('logo-home');
const searchResultsSection = document.getElementById('search-results-section');
const searchResultsGrid = document.getElementById('search-results-grid');
const searchSuggestionsDropdown = document.getElementById('search-suggestions');

/* ========================================
   TAB SWITCHING
   ======================================== */
navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const targetTab = tab.getAttribute('data-tab');
        
        // Update active nav tab
        navTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update active content
        tabContents.forEach(content => {
            if (content.id === `${targetTab}-tab`) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
        
        // Initialize catalog if switching to catalog tab
        if (targetTab === 'catalog') {
            initializeCatalog();
        }
    });
});

/* ========================================
   CATALOG DROPDOWN NAVIGATION
   ======================================== */
// Populate catalog dropdown navigation from database using category_lvl3
async function populateHeaderCategoryDropdown() {
    try {
        console.log('[Dropdown] Loading categories from database...');
        
        // Fetch all products to extract unique categories
        const products = await DataService.getAllProducts();
        
        // Get unique categories from category_lvl3 field
        const categories = new Set();
        products.forEach(p => {
            // Use category_lvl3, fallback to category_lvl2 or category
            const category = p.category_lvl3 || p.category_lvl2 || p.category;
            if (category && category !== 'null' && category !== '' && category !== 'General') {
                categories.add(category);
            }
        });
        
        // Sort categories alphabetically
        const sortedCategories = Array.from(categories).sort();
        
        // Get dropdown container
        const dropdown = document.getElementById('catalog-dropdown');
        
        // Clear existing items except "All Categories"
        dropdown.innerHTML = '<a href="#" class="dropdown-item" data-category="all">All Categories</a>';
        
        // Add categories from database
        sortedCategories.forEach(category => {
            const link = document.createElement('a');
            link.href = '#';
            link.className = 'dropdown-item';
            link.setAttribute('data-category', category);
            link.textContent = category;
            dropdown.appendChild(link);
        });
        
        console.log(`[Dropdown] ✅ Loaded ${sortedCategories.length} categories from category_lvl3`);
        
        // Add click event listeners to all dropdown items
        setupDropdownEventListeners();
        
    } catch (error) {
        console.error('[Dropdown] Error loading categories:', error);
        // Keep default "All Categories" if error occurs
    }
}

// Setup event listeners for dropdown items (called after populating)
function setupDropdownEventListeners() {
    // Use event delegation on the parent dropdown container
    // This is more reliable than attaching to individual items
    const dropdown = document.getElementById('catalog-dropdown');
    
    // Remove old listener if exists
    if (dropdown._clickHandler) {
        dropdown.removeEventListener('click', dropdown._clickHandler);
    }
    
    // Create new click handler
    dropdown._clickHandler = async (e) => {
        // Check if clicked element is a dropdown item
        const dropdownItem = e.target.closest('.dropdown-item');
        if (!dropdownItem) return;
        
        e.preventDefault();
        const category = dropdownItem.getAttribute('data-category');
        
        console.log(`[Dropdown] Category clicked: ${category}`);
        
        // Switch to catalog tab
        const catalogTab = document.querySelector('[data-tab="catalog"]');
        if (catalogTab) {
            catalogTab.click();
        }
        
        // Wait a moment for catalog to initialize
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Set category filter value
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter) {
            if (category === 'all') {
                categoryFilter.value = 'all';
            } else {
                categoryFilter.value = category;
            }
            
            console.log(`[Dropdown] Filter set to: ${categoryFilter.value}`);
            
            // Trigger filter immediately
            await filterCatalog();
        }
    };
    
    // Attach listener to parent
    dropdown.addEventListener('click', dropdown._clickHandler);
    
    console.log('[Dropdown] ✅ Event listeners attached via delegation');
}

/* ========================================
   MARKET TOGGLE
   ======================================== */
const marketUS = document.getElementById('market-us');
const marketUK = document.getElementById('market-uk');

marketToggle.addEventListener('change', async (e) => {
    // Update current market
    if (e.target.checked) {
        currentMarket = 'UK';
        marketUK.classList.add('active');
        marketUS.classList.remove('active');
    } else {
        currentMarket = 'US';
        marketUS.classList.add('active');
        marketUK.classList.remove('active');
    }
    
    console.log(`[Market] Switched to ${currentMarket} marketplace`);
    
    // If we have a current product and results are visible, refresh the quote
    if (resultsSection.classList.contains('active') && currentProduct) {
        console.log('[Market] Re-generating quote for new marketplace...');
        
        // Update shipping text
        updateShippingText();
        
        // Re-display product with new market data
        await displayProductResults(currentProduct);
    }
});

// Initialize market labels
marketUS.classList.add('active');

/* ========================================
   CURRENCY TOGGLE (HEADER)
   ======================================== */
const currencyToggleHeader = document.getElementById('currency-toggle-header');
const currencyUSDLabel = document.getElementById('currency-usd-header');
const currencyGBPLabel = document.getElementById('currency-gbp-header');

// Initialize currency labels
currencyUSDLabel.classList.add('active');

if (currencyToggleHeader) {
    currencyToggleHeader.addEventListener('change', (e) => {
        // Update current currency
        if (e.target.checked) {
            currentCurrency = 'GBP';
            currencyGBPLabel.classList.add('active');
            currencyUSDLabel.classList.remove('active');
        } else {
            currentCurrency = 'USD';
            currencyUSDLabel.classList.add('active');
            currencyGBPLabel.classList.remove('active');
        }
        
        console.log(`[Currency] 💱 Switched to ${currentCurrency}`);
        
        // Refresh current view with new currency
        if (resultsSection.classList.contains('active') && currentProduct) {
            console.log(`[Currency] 🔄 Updating product display...`);
            displayProductResults(currentProduct);
        }
        
        // Refresh catalog if visible
        if (document.getElementById('catalog-tab').classList.contains('active')) {
            console.log(`[Currency] 🔄 Refreshing catalog...`);
            initializeCatalog();
        }
    });
    console.log('[Init] ✅ Currency toggle initialized');
} else {
    console.error('[Init] ❌ Currency toggle not found!');
}

/* ========================================
   GLOBAL EXPANDABLE SEARCH BAR
   ======================================== */
const globalSearchBar = document.getElementById('global-search-bar');
const headerSearchBtn = document.getElementById('header-search-btn');
const closeSearchBtn = document.getElementById('close-search-btn');
const globalSearchInput = document.getElementById('global-search-input');
const globalSearchBtn = document.getElementById('global-search-btn');
const globalSearchType = document.getElementById('global-search-type');
const globalMarketToggle = document.getElementById('global-market-toggle');
const globalMarketUS = document.getElementById('global-market-us');
const globalMarketUK = document.getElementById('global-market-uk');

// Toggle global search bar when clicking header search button
if (headerSearchBtn) {
    headerSearchBtn.addEventListener('click', () => {
        toggleGlobalSearch();
    });
    console.log('[Init] ✅ Header search button initialized');
}

// Close search bar when clicking close button
if (closeSearchBtn) {
    closeSearchBtn.addEventListener('click', () => {
        closeGlobalSearch();
    });
}

// Function to open global search bar
function openGlobalSearch() {
    globalSearchBar.classList.add('active');
    headerSearchBtn.classList.add('search-active');
    // Focus on search input after animation
    setTimeout(() => {
        globalSearchInput.focus();
    }, 300);
    console.log('[Global Search] 🔍 Search bar opened');
}

// Function to close global search bar
function closeGlobalSearch() {
    globalSearchBar.classList.remove('active');
    headerSearchBtn.classList.remove('search-active');
    console.log('[Global Search] ✖️ Search bar closed');
}

// Function to toggle global search bar
function toggleGlobalSearch() {
    if (globalSearchBar.classList.contains('active')) {
        closeGlobalSearch();
    } else {
        openGlobalSearch();
    }
}

// Global search button click handler
if (globalSearchBtn) {
    globalSearchBtn.addEventListener('click', performGlobalSearch);
}

// Global search input - search on Enter key
if (globalSearchInput) {
    globalSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performGlobalSearch();
        }
    });
    
    // Auto-suggest as user types (restored)
    globalSearchInput.addEventListener('input', debounce(handleSearchInput, 300));
    
    // Close suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-input-wrapper') && !e.target.closest('.search-suggestions')) {
            closeSuggestions();
        }
    });
}

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Handle search input for auto-suggestions
async function handleSearchInput(e) {
    const query = e.target.value.trim();
    const searchType = globalSearchType.value;
    const marketplace = globalMarketToggle.checked ? 'UK' : 'US';
    
    // Only show suggestions if query is at least 2 characters
    if (query.length < 2) {
        closeSuggestions();
        return;
    }
    
    try {
        // Fetch all products and filter locally for suggestions
        const allProducts = await DataService.getAllProducts(marketplace);
        
        // Filter products based on search type and query (partial match)
        let suggestions = [];
        const queryLower = query.toLowerCase();
        
        switch(searchType) {
            case 'asin':
                suggestions = allProducts.filter(p => 
                    p.asin && p.asin.toLowerCase().includes(queryLower)
                ).slice(0, 8); // Show up to 8 matches
                break;
            case 'title':
                suggestions = allProducts.filter(p => 
                    p.title && p.title.toLowerCase().includes(queryLower)
                ).slice(0, 8); // Show up to 8 matches
                break;
            case 'isbn':
                suggestions = allProducts.filter(p => 
                    (p.isbn && p.isbn.toLowerCase().includes(queryLower)) ||
                    (p.isbn13 && p.isbn13.toLowerCase().includes(queryLower))
                ).slice(0, 8); // Show up to 8 matches
                break;
        }
        
        // Display suggestions
        displaySuggestions(suggestions);
        
    } catch (error) {
        console.error('[Suggestions] Error fetching suggestions:', error);
        closeSuggestions();
    }
}

// Display search suggestions
function displaySuggestions(products) {
    if (!products || products.length === 0) {
        closeSuggestions();
        console.log('[Suggestions] No products to display');
        return;
    }
    
    console.log(`[Suggestions] Displaying ${products.length} suggestions`);
    
    // Clear existing suggestions
    searchSuggestionsDropdown.innerHTML = '';
    
    // Add suggestion items
    products.forEach(product => {
        const suggestionItem = document.createElement('div');
        suggestionItem.className = 'suggestion-item';
        
        // Get image URL
        let imageUrl = product.image_url || product.image;
        if (!imageUrl || imageUrl === '' || imageUrl === 'null' || imageUrl === null) {
            imageUrl = 'https://via.placeholder.com/40x56/999/fff?text=No+Image';
        } else if (!imageUrl.startsWith('http://') && !imageUrl.startsWith('https://')) {
            if (imageUrl.startsWith('/')) {
                imageUrl = `https://images-na.ssl-images-amazon.com${imageUrl}`;
            } else {
                imageUrl = `https://images-na.ssl-images-amazon.com/images/I/${imageUrl}`;
            }
        }
        
        suggestionItem.innerHTML = `
            <img src="${imageUrl}" alt="${product.title || 'Book'}" class="suggestion-image" onerror="this.src='https://via.placeholder.com/40x56/999/fff?text=No+Image'">
            <div class="suggestion-details">
                <div class="suggestion-title">${product.title || 'Untitled'}</div>
                <div class="suggestion-meta">${product.author || 'Unknown Author'} • ${product.asin || '-'}</div>
            </div>
        `;
        
        // Click handler - show product details
        suggestionItem.addEventListener('click', () => {
            selectProduct(product);
        });
        
        searchSuggestionsDropdown.appendChild(suggestionItem);
    });
    
    // Show suggestions dropdown
    searchSuggestionsDropdown.classList.add('active');
    
    console.log(`[Suggestions] ✅ Dropdown shown with ${products.length} items`);
}

// Close suggestions dropdown
function closeSuggestions() {
    if (searchSuggestionsDropdown) {
        searchSuggestionsDropdown.classList.remove('active');
        searchSuggestionsDropdown.innerHTML = '';
    }
}

// Select a product from suggestions (show product details)
async function selectProduct(product) {
    closeSuggestions();
    closeGlobalSearch();
    
    // Save current product
    currentProduct = product;
    
    // Update current market to match product
    currentMarket = product.marketplace || 'US';
    if (currentMarket === 'UK') {
        marketToggle.checked = true;
        marketUK.classList.add('active');
        marketUS.classList.remove('active');
    } else {
        marketToggle.checked = false;
        marketUS.classList.add('active');
        marketUK.classList.remove('active');
    }
    
    // Switch to quotation tab
    document.querySelector('[data-tab="quotation"]').click();
    
    // Display product details
    await displayProductResults(product);
}

// Global market toggle handler
if (globalMarketToggle) {
    globalMarketToggle.addEventListener('change', (e) => {
        // Update labels
        if (e.target.checked) {
            globalMarketUK.classList.add('active');
            globalMarketUS.classList.remove('active');
        } else {
            globalMarketUS.classList.add('active');
            globalMarketUK.classList.remove('active');
        }
    });
    console.log('[Init] ✅ Global market toggle initialized');
}

// Perform global search - shows search results page instead of single product
async function performGlobalSearch() {
    const query = globalSearchInput.value.trim();
    const type = globalSearchType.value;
    const marketplace = globalMarketToggle.checked ? 'UK' : 'US';
    
    // Validate input
    if (!query) {
        alert('Please enter a search term');
        globalSearchInput.focus();
        return;
    }
    
    // Close suggestions
    closeSuggestions();
    
    // Show loading state
    globalSearchBtn.textContent = 'Searching...';
    globalSearchBtn.disabled = true;
    
    try {
        console.log(`[Global Search] Looking for ${type}: "${query}" in ${marketplace} marketplace...`);
        
        // Fetch all products and filter for matches
        const allProducts = await DataService.getAllProducts(marketplace);
        
        // Filter products based on search type and query
        let searchResults = [];
        const queryLower = query.toLowerCase();
        
        switch(type) {
            case 'asin':
                searchResults = allProducts.filter(p => 
                    p.asin && p.asin.toLowerCase().includes(queryLower)
                );
                break;
            case 'title':
                searchResults = allProducts.filter(p => 
                    p.title && p.title.toLowerCase().includes(queryLower)
                );
                break;
            case 'isbn':
                searchResults = allProducts.filter(p => 
                    (p.isbn && p.isbn.toLowerCase().includes(queryLower)) ||
                    (p.isbn13 && p.isbn13.toLowerCase().includes(queryLower))
                );
                break;
        }
        
        if (searchResults.length === 0) {
            alert(`No products found for "${query}". Please try a different search term.`);
            return;
        }
        
        // Update current market to match search
        currentMarket = marketplace;
        if (marketplace === 'UK') {
            marketToggle.checked = true;
            marketUK.classList.add('active');
            marketUS.classList.remove('active');
        } else {
            marketToggle.checked = false;
            marketUS.classList.add('active');
            marketUK.classList.remove('active');
        }
        
        // Switch to quotation tab
        document.querySelector('[data-tab="quotation"]').click();
        
        // Display search results in catalog layout
        displaySearchResults(searchResults, query, type);
        
        // Close search bar after successful search
        closeGlobalSearch();
        
        // Clear search input
        globalSearchInput.value = '';
        
        console.log(`[Global Search] ✅ Found ${searchResults.length} results for "${query}"`);
        
    } catch (error) {
        console.error('[Global Search] Error during search:', error);
        alert(`Search failed: ${error.message}`);
    } finally {
        // Reset button state
        globalSearchBtn.textContent = 'Search';
        globalSearchBtn.disabled = false;
    }
}

// Display search results in catalog layout
function displaySearchResults(products, query, searchType) {
    // Hide initial message and product details section
    if (initialMessage) {
        initialMessage.style.display = 'none';
    }
    if (resultsSection) {
        resultsSection.classList.remove('active');
        resultsSection.style.display = 'none';
    }
    
    // Show search results section
    searchResultsSection.classList.add('active');
    
    // Update search results header
    document.getElementById('search-results-title').textContent = `Search Results for "${query}"`;
    document.getElementById('search-results-count').textContent = `Found ${products.length} product${products.length !== 1 ? 's' : ''} matching your search`;
    
    // Clear existing results
    searchResultsGrid.innerHTML = '';
    
    // Render each product as a catalog item
    products.forEach(product => {
        const catalogItem = document.createElement('div');
        catalogItem.className = 'catalog-item';
        
        // Handle image URL properly
        let imageUrl = product.image_url || product.image;
        
        if (!imageUrl || imageUrl === '' || imageUrl === 'null' || imageUrl === null) {
            imageUrl = 'https://via.placeholder.com/160x220/999/fff?text=No+Image';
        } else if (!imageUrl.startsWith('http://') && !imageUrl.startsWith('https://')) {
            if (imageUrl.startsWith('/')) {
                imageUrl = `https://images-na.ssl-images-amazon.com${imageUrl}`;
            } else {
                imageUrl = `https://images-na.ssl-images-amazon.com/images/I/${imageUrl}`;
            }
        }
        
        // Note: Price is calculated when user clicks into product details
        // Not shown in preview to avoid displaying inaccurate pre-calculated prices
        
        catalogItem.innerHTML = `
            <div class="catalog-item-image">
                <img src="${imageUrl}" alt="${product.title || 'Untitled'}" onerror="this.src='https://via.placeholder.com/160x220/999/fff?text=No+Image'">
            </div>
            <h3>${product.title || 'Untitled'}</h3>
            <div class="catalog-item-meta"><strong>Author:</strong> ${product.author || 'Unknown'}</div>
            <span class="catalog-item-category">${product.category_lvl3 || product.category || 'General'}</span>
        `;
        
        // Click to view product details
        catalogItem.addEventListener('click', async () => {
            currentProduct = product;
            await displayProductResults(product);
        });
        
        searchResultsGrid.appendChild(catalogItem);
    });
    
    // Scroll to search results
    searchResultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    console.log(`[Search Results] ✅ Rendered ${products.length} products in catalog layout`);
}

// ESC key to close search bar
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && globalSearchBar.classList.contains('active')) {
        closeGlobalSearch();
    }
});

/* ========================================
   LOGO - RETURN TO HOME
   ======================================== */
if (logoHome) {
    logoHome.addEventListener('click', () => {
        // Switch to quotation tab
        const quotationTab = document.querySelector('[data-tab="quotation"]');
        if (quotationTab) {
            quotationTab.click();
        }
        
        // Hide results sections and show initial welcome message
        if (resultsSection) {
            resultsSection.classList.remove('active');
            resultsSection.style.display = 'none';
        }
        
        if (searchResultsSection) {
            searchResultsSection.classList.remove('active');
        }
        
        if (initialMessage) {
            initialMessage.style.display = 'flex';
        }
        
        // Close global search bar if open
        if (globalSearchBar.classList.contains('active')) {
            closeGlobalSearch();
        }
        
        // Close suggestions if open
        closeSuggestions();
        
        // Clear current product
        currentProduct = null;
        
        console.log('[Logo] 🏠 Returned to home page');
    });
    console.log('[Init] ✅ Logo home button initialized');
}

/* ========================================
   CATALOG MARKETPLACE TOGGLE
   ======================================== */
const catalogMarketToggle = document.getElementById('catalog-market-toggle');
const catalogMarketUS = document.getElementById('catalog-market-us');
const catalogMarketUK = document.getElementById('catalog-market-uk');

if (catalogMarketToggle) {
    catalogMarketToggle.addEventListener('change', (e) => {
        // Update catalog marketplace filter
        if (e.target.checked) {
            catalogMarket = 'UK';
            catalogMarketUK.classList.add('active');
            catalogMarketUS.classList.remove('active');
        } else {
            catalogMarket = 'US';
            catalogMarketUS.classList.add('active');
            catalogMarketUK.classList.remove('active');
        }
        
        console.log(`[Catalog] 🔄 Switched to ${catalogMarket} marketplace`);
        console.log(`[Catalog] 🔄 Reloading products...`);
        
        // Reload catalog with new marketplace
        initializeCatalog();
    });
    console.log('[Init] ✅ Catalog marketplace toggle initialized');
} else {
    console.error('[Init] ❌ Catalog marketplace toggle not found!');
}

/* ========================================
   PRODUCT INFO TAB SWITCHING
   ======================================== */
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('info-tab-btn')) {
        const targetTab = e.target.getAttribute('data-info-tab');
        
        // Update active tab button
        document.querySelectorAll('.info-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        e.target.classList.add('active');
        
        // Update active tab content
        document.querySelectorAll('.info-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${targetTab}-content`).classList.add('active');
    }
});

/* ========================================
   SEARCH FUNCTIONALITY
   ======================================== */
searchBtn.addEventListener('click', performSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch();
    }
});

async function performSearch() {
    const query = searchInput.value.trim();
    const type = searchType.value;
    
    // Validate input
    if (!query) {
        alert('Please enter a search term');
        return;
    }
    
    // Show loading state
    searchBtn.textContent = 'Searching...';
    searchBtn.disabled = true;
    
    try {
        console.log(`[Search] Looking for ${type}: "${query}" in ${currentMarket} marketplace...`);
        
        // Search for product using DataService
        let product = await DataService.searchProduct(query, type, currentMarket);
    
    if (!product) {
            // No exact match - try to be helpful
            console.warn('[Search] No exact match found');
            
            // For demo: if using mock data, show first product as fallback
            if (config.USE_MOCK_DATA) {
        product = productsDatabase[0];
                console.log('[Search] Using first mock product as fallback for demo');
            } else {
                alert(`No product found for "${query}". Please try a different search term.`);
                return;
            }
        }
        
        // Save current product and display results
    currentProduct = product;
        await displayProductResults(product);
        
    } catch (error) {
        console.error('[Search] Error during search:', error);
        alert(`Search failed: ${error.message}`);
    } finally {
        // Reset button state
        searchBtn.textContent = 'Search';
        searchBtn.disabled = false;
    }
}

/* ========================================
   DISPLAY PRODUCT RESULTS (INTEGRATED WITH LIVE DATA)
   ======================================== */
async function displayProductResults(product) {
    console.log('[Display] Rendering product results...');
    
    // Hide initial message and search results, show product details
    initialMessage.style.display = 'none';
    if (searchResultsSection) {
        searchResultsSection.classList.remove('active');
    }
    resultsSection.classList.add('active');
    resultsSection.style.display = 'block';
    
    // ========== STEP 1: Display Product Information ==========
    
    // Update product image and title
    let productImage = product.image_url || product.image;
    
    // Handle image URL - convert to full Amazon CDN URL
    if (!productImage || productImage === '' || productImage === 'null' || productImage === null) {
        // No image in database
        productImage = 'https://via.placeholder.com/160x220/999/fff?text=No+Image';
    } else if (productImage.startsWith('http://') || productImage.startsWith('https://')) {
        // Already a full URL - use as-is
        console.log(`[Display] Using full URL: ${productImage.substring(0, 60)}...`);
    } else if (productImage.startsWith('/')) {
        // Relative path - prepend Amazon CDN
        productImage = `https://images-na.ssl-images-amazon.com${productImage}`;
        console.log(`[Display] Converted relative path: ${productImage.substring(0, 60)}...`);
    } else {
        // Just a filename (like "81o91RV67ML.jpg") - build full Amazon URL
        productImage = `https://images-na.ssl-images-amazon.com/images/I/${productImage}`;
        console.log(`[Display] Built Amazon URL from filename: ${productImage.substring(0, 60)}...`);
    }
    
    const imgElement = document.getElementById('product-img');
    imgElement.src = productImage;
    imgElement.onerror = function() {
        console.error(`[Display] Failed to load image: ${this.src}`);
        this.src = 'https://via.placeholder.com/160x220/999/fff?text=No+Image';
    };
    
    document.getElementById('product-title').textContent = product.title || 'Untitled';
    
    // Update description
    document.getElementById('product-description').textContent = product.description || 'No description available.';
    
    // Update specifications - fetch from database
    document.getElementById('product-author').textContent = product.author || 'Unknown';
    document.getElementById('product-asin').textContent = product.asin || '-';
    
    // Handle ISBN - hide row if not available
    const isbnRow = document.getElementById('isbn-row');
    const isbnValue = product.isbn || product.isbn13;
    if (isbnValue && isbnValue !== '-' && isbnValue !== 'null') {
        document.getElementById('product-isbn').textContent = isbnValue;
        isbnRow.style.display = 'flex';
    } else {
        isbnRow.style.display = 'none';
    }
    
    // Category - use category_lvl3, fallback to category_lvl2 or category_lvl1
    const categoryValue = product.category_lvl3 || product.category_lvl2 || product.category || 'General';
    document.getElementById('product-category').textContent = categoryValue;
    
    // Weight - fetch from database package_weight field (in kg)
    if (product.package_weight && product.package_weight > 0) {
        // Format weight to 2 decimal places
        const weightValue = parseFloat(product.package_weight).toFixed(2);
        document.getElementById('product-weight').textContent = `${weightValue} kg`;
    } else {
        document.getElementById('product-weight').textContent = '-';
    }
    
    // Package dimensions - fetch from database package_dimensions field
    if (product.package_dimensions && product.package_dimensions !== 'null' && product.package_dimensions.trim() !== '') {
        document.getElementById('product-dimensions').textContent = product.package_dimensions;
    } else {
        document.getElementById('product-dimensions').textContent = '-';
    }
    
    // Update shipping text based on market
    updateShippingText();
    
    // ========== STEP 2: Generate Quote Using Backend Calculator ==========
    // This ensures the whole calculation completes BEFORE displaying the price
    
    // Show loading state while calculating
    const quotePriceElement = document.getElementById('current-quote-price');
    quotePriceElement.textContent = 'Calculating...';
    quotePriceElement.style.opacity = '0.6';
    
    console.log('[Display] 🔄 Starting quote calculation...');
    
    try {
        // Call backend API to calculate quote
        // This performs the full calculation with Buy Box data, ROI logic, etc.
        const quoteData = await DataService.generateQuote(product.asin, product.marketplace);
        
        console.log('[Display] ✅ Quote calculation complete:', quoteData);
        
        // Check if quote is feasible
        if (!quoteData.feasible) {
            console.warn('[Display] ⚠️ Quote not feasible:', quoteData.reason);
            // Still display the quote but with warning
            quotePriceElement.textContent = 'Quote Unavailable';
            quotePriceElement.style.opacity = '1';
            
            // Show reason in console for debugging
            console.warn('[Display] Reason:', quoteData.reason);
        } else {
            // Use calculated quote price (quote_q) from backend
            const calculatedQuotePrice = quoteData.quote_q;
            
            // Convert to display currency
            const displayPrice = CurrencyConverter.getDisplayPrice(
                calculatedQuotePrice, 
                product.marketplace, 
                currentCurrency
            );
            
            // Update current quote price with calculated value
            quotePriceElement.textContent = displayPrice;
            quotePriceElement.style.opacity = '1';
            
            console.log('[Display] ✅ Displaying calculated quote: ' + displayPrice);
            // Note: Internal calculations (ROI, fees, costs) are kept private and not logged
        }
        
        // ========== STEP 3: Update ROI Calculator - Only Show Buy Price ==========
        // Purpose: Let users input their own numbers for ROI calculation
        // We only provide our quote price as the "Buy Price"
        // All other fields remain at 0 for user input
        
        // Convert calculated quote for calculator (keep as number)
        const convertedQuotePrice = CurrencyConverter.convertPrice(
            quoteData.quote_q, 
            product.marketplace, 
            currentCurrency
        );
        
        // Buy Price = Calculated quote price (our wholesale price offer)
        document.getElementById('buy-price').value = convertedQuotePrice.toFixed(2);
        
        // Set all other fields to 0 - let users input their own numbers
        document.getElementById('sale-price').value = '0.00';
        document.getElementById('amazon-fees').value = '0.00';
        document.getElementById('fulfillment-fee').value = '0.00';
        document.getElementById('shipping-cost').value = '0.00';
        
        // Calculate ROI with initial values
        calculateROI();
        
        console.log('[Display] ✅ ROI Calculator ready for user input');
        
    } catch (error) {
        console.error('[Display] ❌ Error generating quote:', error);
        
        // Fallback to database price if quote calculation fails
        const fallbackPrice = product.our_price || 10.00;
        const displayPrice = CurrencyConverter.getDisplayPrice(
            fallbackPrice, 
            product.marketplace, 
            currentCurrency
        );
        
        quotePriceElement.textContent = displayPrice + ' (est.)';
        quotePriceElement.style.opacity = '1';
        
        // Fill calculator with fallback values
        const convertedFallbackPrice = CurrencyConverter.convertPrice(
            fallbackPrice, 
            product.marketplace, 
            currentCurrency
        );
        
        document.getElementById('buy-price').value = convertedFallbackPrice.toFixed(2);
        document.getElementById('sale-price').value = '0.00';
        document.getElementById('amazon-fees').value = '0.00';
        document.getElementById('fulfillment-fee').value = '0.00';
        document.getElementById('shipping-cost').value = '0.00';
        calculateROI();
        
        console.warn('[Display] ⚠️ Using fallback price from database');
    }
    
    // ========== STEP 4: Fetch and Render Amazon Insight (Historical Charts + Current Stats) ==========
    
    try {
        // Fetch historical data from last 360 days
        const history = await DataService.getHistoricalData(product.asin, currentMarket);
        
        // Extract today's data (most recent values from the historical data)
        const hasBuyBoxData = history.buyBoxHistory && history.buyBoxHistory.length > 0;
        const hasRankData = history.rankHistory && history.rankHistory.length > 0;
        
        // Get today's Buy Box Price (last element in array)
        const todayBuyBox = hasBuyBoxData 
            ? history.buyBoxHistory[history.buyBoxHistory.length - 1] 
            : null;
        
        // Get today's Sales Rank (last element in array)
        const todayRank = hasRankData 
            ? history.rankHistory[history.rankHistory.length - 1] 
            : null;
        
        // Display Current Buy Box Price
        const buyBoxElement = document.getElementById('current-buybox');
        if (buyBoxElement) {
            if (todayBuyBox && todayBuyBox > 0) {
                const convertedBuyBox = CurrencyConverter.getDisplayPrice(
                    todayBuyBox,
                    product.marketplace,
                    currentCurrency
                );
                buyBoxElement.textContent = convertedBuyBox;
            } else {
                buyBoxElement.textContent = 'N/A';
            }
        }
        
        // Display Current Sales Rank
        const rankElement = document.getElementById('current-rank');
        if (rankElement) {
            if (todayRank && todayRank > 0) {
                // Format large numbers with commas (e.g., 1,234,567)
                rankElement.textContent = todayRank.toLocaleString();
            } else {
                rankElement.textContent = 'N/A';
            }
        }
        
        // Display Number of Sellers
        const sellerCountElement = document.getElementById('seller-count');
        if (sellerCountElement) {
            sellerCountElement.textContent = history.sellerCount || 'N/A';
        }
        
        // Log today's stats for debugging
        console.log('[Display] Amazon Insight - Today\'s Stats:');
        console.log(`  Buy Box Price: ${todayBuyBox ? '$' + todayBuyBox.toFixed(2) : 'N/A'}`);
        console.log(`  Sales Rank: ${todayRank ? todayRank.toLocaleString() : 'N/A'}`);
        console.log(`  Seller Count: ${history.sellerCount || 'N/A'}`);
        
        // Render charts with historical data
        renderChartsWithData(history);
        
    } catch (error) {
        console.error('[Display] Error fetching Amazon Insight data:', error);
        
        // Show error state for all stats
        const buyBoxElement = document.getElementById('current-buybox');
        const rankElement = document.getElementById('current-rank');
        const sellerCountElement = document.getElementById('seller-count');
        
        if (buyBoxElement) buyBoxElement.textContent = 'N/A';
        if (rankElement) rankElement.textContent = 'N/A';
        if (sellerCountElement) sellerCountElement.textContent = 'N/A';
        
        // Generate placeholder charts
        renderChartsWithData({
            buyBoxHistory: [15, 15.5, 16, 16.5, 17, 17.5],
            rankHistory: [1000, 950, 900, 850, 800, 750],
            dates: ['6mo ago', '5mo ago', '4mo ago', '3mo ago', '2mo ago', '1mo ago']
        });
    }
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    console.log('[Display] ✅ Product results rendered successfully');
}

/* ========================================
   UPDATE SHIPPING TEXT BASED ON MARKET
   ======================================== */
function updateShippingText() {
    // Shipping text is now static in HTML: "Available for International and UK delivery"
    // This function is kept for compatibility but no longer changes the text
    const shippingText = document.getElementById('shipping-text');
    if (shippingText && !shippingText.textContent) {
        shippingText.textContent = 'Available for International and UK delivery';
    }
}

/* ========================================
   CHART RENDERING WITH CHART.JS (AMAZON INSIGHT - 360 DAYS)
   ======================================== */
function renderChartsWithData(history) {
    // Destroy existing charts if they exist
    if (charts.buybox) charts.buybox.destroy();
    if (charts.rank) charts.rank.destroy();
    
    // Format date labels for display with year shown once when it changes
    let labels = history.dates || [];
    if (labels.length > 0) {
        // Sample dates to show reasonable number of labels (every 30 days)
        const step = Math.ceil(labels.length / 12);
        const sampledDates = labels.filter((_, idx) => idx % step === 0);
        
        // Format dates: Show year when it changes, then just month names
        let lastYear = null;
        labels = sampledDates.map(dateStr => {
            const date = new Date(dateStr);
            const year = date.getFullYear();
            const month = date.toLocaleDateString('en-US', { month: 'short' });
            
            // If year changed from last label, show "YYYY- Mon"
            if (lastYear !== year) {
                lastYear = year;
                return `${year}- ${month}`;
            }
            // Otherwise just show month
            return month;
        });
    }
    
    // Sample data to match labels
    const step = Math.ceil((history.buyBoxHistory?.length || 0) / 12);
    const buyBoxData = (history.buyBoxHistory || []).filter((_, idx) => idx % step === 0);
    const rankData = (history.rankHistory || []).filter((_, idx) => idx % step === 0);
    
    const dataLength = history.dates?.length || 0;
    
    // Common chart options
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        },
        scales: {
            y: {
                beginAtZero: false,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    callback: function(value) {
                        return '$' + value.toFixed(2);
                    }
                }
            },
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    maxRotation: 45,
                    minRotation: 45
                }
            }
        }
    };
    
    // Amazon Price Chart (formerly Buy Box Price)
    const buyboxCtx = document.getElementById('buybox-chart').getContext('2d');
    charts.buybox = new Chart(buyboxCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Amazon Price',
                data: buyBoxData,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: commonOptions
    });
    
    // Sales Rank Chart (Y-axis inverted: lower rank = higher on chart = better)
    const rankCtx = document.getElementById('rank-chart').getContext('2d');
    charts.rank = new Chart(rankCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sales Rank',
                data: rankData,
                borderColor: '#e74c3c',
                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 2,
                pointHoverRadius: 5
            }]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: {
                    ...commonOptions.scales.y,
                    reverse: false, // Normal: lower rank appears lower on chart
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString(); // Format as number with commas
                        }
                    }
                }
            },
            plugins: {
                ...commonOptions.plugins,
                tooltip: {
                    ...commonOptions.plugins.tooltip,
                    callbacks: {
                        label: function(context) {
                            return 'Rank: ' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            }
        }
    });
    
    console.log(`[Amazon Insight] ✅ Rendered 2 charts with ${dataLength} days of data`);
}

/* ========================================
   ROI CALCULATOR
   ======================================== */
const roiInputs = [
    document.getElementById('buy-price'),
    document.getElementById('sale-price'),
    document.getElementById('amazon-fees'),
    document.getElementById('fulfillment-fee'),
    document.getElementById('shipping-cost')
];

roiInputs.forEach(input => {
    input.addEventListener('input', calculateROI);
});

function calculateROI() {
    // Get all input values
    const buyPrice = parseFloat(document.getElementById('buy-price').value) || 0;
    const salePrice = parseFloat(document.getElementById('sale-price').value) || 0;
    const amazonFees = parseFloat(document.getElementById('amazon-fees').value) || 0;
    const fulfillmentFee = parseFloat(document.getElementById('fulfillment-fee').value) || 0;
    const shippingCost = parseFloat(document.getElementById('shipping-cost').value) || 0;
    
    const roiValueElement = document.getElementById('roi-value');
    
    // If sales price is 0 and other fees are 0, show "-" (user hasn't input data yet)
    if (salePrice === 0 && amazonFees === 0 && fulfillmentFee === 0 && shippingCost === 0) {
        roiValueElement.textContent = '-';
        roiValueElement.style.color = '#6b6b6b'; // Neutral gray color
        roiValueElement.classList.remove('negative');
        console.log(`[ROI] Awaiting user input`);
        return;
    }
    
    // ROI Calculation: ROI = (Profit / Total Cost) * 100
    // Profit = Sales Price - (Buy Price + Amazon Fee + Fulfillment Fee + Shipping Cost)
    const totalCost = buyPrice + amazonFees + fulfillmentFee + shippingCost;
    const profit = salePrice - totalCost;
    const roi = totalCost > 0 ? (profit / totalCost) * 100 : 0;
    
    roiValueElement.textContent = `${roi.toFixed(2)}%`;
    
    // Color coding based on ROI percentage
    if (roi > 0) {
        roiValueElement.classList.remove('negative');
        roiValueElement.style.color = '#27ae60'; // Green for positive ROI
    } else {
        roiValueElement.classList.add('negative');
        roiValueElement.style.color = '#e74c3c'; // Red for negative ROI
    }
    
    console.log(`[ROI] Calculated: ${roi.toFixed(2)}% (Sales: ${salePrice}, Total Cost: ${totalCost}, Profit: ${profit})`);
}

/* ========================================
   CATALOG INITIALIZATION (UPDATED FOR LIVE DATA)
   ======================================== */
async function initializeCatalog() {
    console.log(`[Catalog] 📦 Loading products for ${catalogMarket} marketplace in ${currentCurrency}...`);
    
    try {
        // Populate category filter from category_lvl3
        await populateCategoryFilter();
        
        // Fetch products for current catalog marketplace
        const products = await DataService.getAllProducts(catalogMarket);
        console.log(`[Catalog] ✅ Fetched ${products.length} products from ${catalogMarket} marketplace`);
        renderCatalog(products);
        
    } catch (error) {
        console.error('[Catalog] ❌ Error loading catalog:', error);
        catalogGrid.innerHTML = '<p style="padding: 40px; text-align: center;">Failed to load catalog. Please try again later.</p>';
    }
}

function renderCatalog(products) {
    catalogGrid.innerHTML = '';
    
    if (!products || products.length === 0) {
        catalogGrid.innerHTML = '<p style="padding: 40px; text-align: center;">No products available.</p>';
        return;
    }
    
    products.forEach(product => {
        const catalogItem = document.createElement('div');
        catalogItem.className = 'catalog-item';
        
        // Handle image URL properly - check for actual data
        let imageUrl = product.image_url || product.image;
        
        if (!imageUrl || imageUrl === '' || imageUrl === 'null' || imageUrl === null) {
            // No image in database - use placeholder
            imageUrl = 'https://via.placeholder.com/160x220/999/fff?text=No+Image';
        } else if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
            // Already a full URL - use as-is
            // Do nothing
        } else if (imageUrl.startsWith('/')) {
            // Relative path - prepend Amazon CDN
            imageUrl = `https://images-na.ssl-images-amazon.com${imageUrl}`;
        } else {
            // Just a filename (like "81o91RV67ML.jpg") - build full Amazon URL
            imageUrl = `https://images-na.ssl-images-amazon.com/images/I/${imageUrl}`;
        }
        
        // Note: Price is calculated dynamically when user clicks into product
        // Not displayed in catalog preview to avoid showing inaccurate stored prices
        
        catalogItem.innerHTML = `
            <div class="catalog-item-image">
                <img src="${imageUrl}" alt="${product.title || 'Untitled'}" onerror="this.src='https://via.placeholder.com/160x220/999/fff?text=No+Image'">
            </div>
            <h3>${product.title || 'Untitled'}</h3>
            <div class="catalog-item-meta"><strong>Author:</strong> ${product.author || 'Unknown'}</div>
            <span class="catalog-item-category">${product.category_lvl3 || product.category || 'General'}</span>
        `;
        
        // Click to view in quotation tab
        catalogItem.addEventListener('click', async () => {
            currentProduct = product;
            document.querySelector('[data-tab="quotation"]').click();
            await displayProductResults(product);
        });
        
        catalogGrid.appendChild(catalogItem);
    });
    
    console.log(`[Catalog] ✅ Rendered ${products.length} products`);
    console.log(`[Catalog]    Marketplace: ${catalogMarket} | Currency: ${currentCurrency}`);
}

/* ========================================
   CATALOG FILTERING
   ======================================== */
const categoryFilter = document.getElementById('category-filter');

// Populate category filter dynamically from database using category_lvl3
async function populateCategoryFilter() {
    try {
        console.log('[Catalog Filter] Loading categories from database...');
        const products = await DataService.getAllProducts(catalogMarket);
        
        // Get unique categories from category_lvl3 field
        const categories = new Set();
        products.forEach(p => {
            // Use category_lvl3, fallback to category_lvl2 or category
            const category = p.category_lvl3 || p.category_lvl2 || p.category;
            if (category && category !== 'null' && category !== '') {
                categories.add(category);
            }
        });
        
        // Sort categories alphabetically
        const sortedCategories = Array.from(categories).sort();
        
        // Clear existing options (except "All Categories")
        categoryFilter.innerHTML = '<option value="all">All Categories</option>';
        
        // Add category options from category_lvl3
        sortedCategories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            categoryFilter.appendChild(option);
        });
        
        console.log(`[Catalog Filter] ✅ Loaded ${sortedCategories.length} categories from category_lvl3`);
        
    } catch (error) {
        console.error('[Catalog Filter] Error loading categories:', error);
    }
}

categoryFilter.addEventListener('change', filterCatalog);

async function filterCatalog() {
    const category = categoryFilter.value;
    
    console.log(`[Filter] Filtering by category: ${category}`);
    
    try {
        // Fetch all products for current marketplace
        const allProducts = await DataService.getAllProducts(catalogMarket);
        
        // Filter products by category using category_lvl3
        let filteredProducts = allProducts;
        
        if (category !== 'all') {
            filteredProducts = filteredProducts.filter(p => {
                // Use category_lvl3, fallback to category_lvl2 or category
                const productCategory = p.category_lvl3 || p.category_lvl2 || p.category;
                return productCategory === category;
            });
        }
        
        // Render filtered products
        renderCatalog(filteredProducts);
        console.log(`[Catalog] ✅ Filtered to ${filteredProducts.length} products (category: ${category})`);
        
    } catch (error) {
        console.error('[Catalog] Error filtering catalog:', error);
        catalogGrid.innerHTML = '<p style="padding: 40px; text-align: center;">Failed to filter catalog. Please try again later.</p>';
    }
}

/* ========================================
   CONTACT BUTTON HANDLER
   ======================================== */
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('contact-btn') || e.target.closest('.contact-btn')) {
        alert('Thank you for your interest! Our sales team will contact you shortly.\n\nFor immediate assistance:\nEmail: sales@bookportal.com\nPhone: +1 (555) 123-4567');
    }
});

/* ========================================
   INITIALIZATION
   ======================================== */
document.addEventListener('DOMContentLoaded', async () => {
    console.log('='.repeat(80));
    console.log('📚 WHOLESALE PORTAL - Wholesale Quotation Platform');
    console.log('='.repeat(80));
    console.log('');
    
    // Initialize DataService and test connection
    const initResult = await DataService.initialize();
    
    if (initResult.success) {
        console.log(`✅ Wholesale Portal initialized successfully`);
        console.log(`📦 Mode: ${config.USE_MOCK_DATA ? 'MOCK DATA (Demo)' : 'LIVE DATA (Supabase)'}`);
        console.log(`📊 Loaded ${initResult.productCount} products`);
        
        // Populate header category dropdown from category_lvl3 in database
        await populateHeaderCategoryDropdown();
        
    } else {
        console.error(`❌ Initialization failed: ${initResult.message}`);
        console.error('⚠️  Falling back to mock data mode');
        
        // Show error message to user
        const initialMessage = document.getElementById('initial-message');
        if (initialMessage) {
            initialMessage.querySelector('h2').textContent = 'Connection Error';
            initialMessage.querySelector('p').textContent = 
                `${initResult.message}. Using demo data instead.`;
        }
    }
    
    console.log('');
    console.log('Ready for use! Try searching for a book.');
    console.log('='.repeat(80));
});
