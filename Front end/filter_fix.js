// Fixed filter function - copy this to replace the existing filterCatalog function

async function filterCatalog() {
    const category = categoryFilter.value;
    
    console.log(`[Filter] Category: ${category}`);
    
    try {
        // Fetch all products for current marketplace
        const allProducts = await DataService.getAllProducts(catalogMarket);
        
        // Filter products by category
        let filteredProducts = allProducts;
        
        if (category !== 'all') {
            filteredProducts = filteredProducts.filter(p => {
                const productCategory = p.category_lvl3 || p.category;
                return productCategory === category;
            });
        }
        
        console.log(`[Filter] Showing ${filteredProducts.length} products`);
        renderCatalog(filteredProducts);
        
    } catch (error) {
        console.error('[Filter] Error filtering catalog:', error);
        catalogGrid.innerHTML = '<p style="padding: 40px; text-align: center;">Error filtering products. Please try again.</p>';
    }
}






