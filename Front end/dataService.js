/**
 * Data Service Module
 * -------------------
 * Purpose:
 * - Provide a single interface for all data operations
 * - Automatically switch between mock data and live Supabase data
 * - Handle API calls to backend for quote generation
 * - Transform data to frontend format
 * 
 * This module implements one-way data flow:
 * Data Source → State → DOM Updates
 * 
 * Usage:
 *   // Fetch all products
 *   const products = await DataService.getAllProducts();
 *   
 *   // Generate quote for a product
 *   const quote = await DataService.generateQuote(asin, marketplace);
 *   
 *   // Get historical data
 *   const history = await DataService.getHistoricalData(asin, marketplace);
 */

// Get reference to Supabase client (initialized in supabaseClient.js)
const getSupabaseClient = () => {
    return window.supabaseClient || null;
};

/**
 * Diagnostic function to test database connectivity
 * Run this in browser console: testDynamicDataAccess('your-asin', 'US')
 */
window.testDynamicDataAccess = async function(asin = '1778766800', marketplace = 'US') {
    console.log('=== DIAGNOSTIC TEST: Dynamic Data Access ===');
    console.log(`Testing with ASIN: ${asin}, Marketplace: ${marketplace}`);
    
    const client = getSupabaseClient();
    if (!client) {
        console.error('❌ Supabase client not available!');
        return;
    }
    
    console.log('✅ Supabase client found');
    
    // Test: Query the historical_data view
    console.log('\n--- Test: Query historical_data view (public schema) ---');
    try {
        const { data, error } = await client
            .from('historical_data')
            .select('*', { count: 'exact' })
            .eq('asin', asin)
            .eq('marketplace', marketplace)
            .limit(5);
        
        if (error) {
            console.error('❌ Error:', error.message);
            console.log('\n💡 SOLUTION:');
            console.log('  1. Open Supabase Dashboard → SQL Editor');
            console.log('  2. Run FIX_BACKFILL_ACCESS_VIEW.sql');
            console.log('  3. This creates the historical_data view in public schema');
        } else {
            console.log(`✅ SUCCESS! Found ${data?.length || 0} records`);
            console.log('Sample data:', data?.slice(0, 2));
            
            if (data && data.length > 0) {
                console.log('\n📊 Field Check:');
                console.log('  - fetch_date:', data[0].fetch_date);
                console.log('  - current_buybox_price:', data[0].current_buybox_price);
                console.log('  - sales_rank_current:', data[0].sales_rank_current);
                console.log('  - num_sellers:', data[0].num_sellers);
            }
            
            console.log('\n✅ Historical data access is working perfectly!');
            return; // Success!
        }
    } catch (e) {
        console.error('❌ Exception:', e);
    }
    
    console.log('\n=== END DIAGNOSTIC TEST ===');
};

const DataService = {
    /**
     * Check if we're using mock data
     * 
     * Returns:
     *   boolean - true if using mock data, false if using live data
     */
    isUsingMockData() {
        return config.USE_MOCK_DATA;
    },
    
    /**
     * Initialize data service
     * 
     * Purpose:
     * - Test connection if using live data
     * - Load initial data
     * - Log initialization status
     * 
     * Returns:
     *   Promise<Object> - { success: boolean, message: string, productCount: number }
     */
    async initialize() {
        console.log('[DataService] Initializing...');
        
        if (this.isUsingMockData()) {
            console.log('[DataService] ✅ Initialized in MOCK DATA mode');
            console.log(`[DataService] Loaded ${productsDatabase.length} mock products`);
            return {
                success: true,
                message: 'Using mock data',
                productCount: productsDatabase.length
            };
        } else {
            console.log('[DataService] Initializing in LIVE DATA mode...');
            
            // Test Supabase connection
            const connected = await testSupabaseConnection();
            
            if (!connected) {
                console.error('[DataService] ❌ Failed to connect to Supabase');
                return {
                    success: false,
                    message: 'Failed to connect to Supabase. Check config.js credentials.',
                    productCount: 0
                };
            }
            
            // Count products
            try {
                const products = await this.getAllProducts();
                console.log('[DataService] ✅ Initialized successfully');
                console.log(`[DataService] Loaded ${products.length} products from database`);
                return {
                    success: true,
                    message: 'Connected to Supabase',
                    productCount: products.length
                };
            } catch (error) {
                console.error('[DataService] ❌ Error loading products:', error);
                return {
                    success: false,
                    message: `Error loading products: ${error.message}`,
                    productCount: 0
                };
            }
        }
    },
    
    /**
     * Get all products
     * 
     * Purpose:
     * - Fetch all products from either mock database or Supabase
     * - Transform to consistent format for frontend
     * 
     * Args:
     *   marketplace (optional) - 'US' or 'UK' to filter by marketplace
     * 
     * Returns:
     *   Promise<Array> - Array of product objects
     */
    async getAllProducts(marketplace = null) {
        console.log(`[DataService] Fetching all products${marketplace ? ` for ${marketplace}` : ''}...`);
        
        if (this.isUsingMockData()) {
            // Use mock data
            let products = productsDatabase;
            
            // Filter by marketplace if provided (mock data doesn't have marketplace field yet)
            // For now, return all mock data
            
            return products;
        } else {
            // Use Supabase
            try {
                const products = await fetchSupabaseProducts(marketplace);
                
                // Transform to frontend format
                return products.map(product => this._transformProduct(product));
                
            } catch (error) {
                console.error('[DataService] Error fetching products:', error);
                throw new Error(`Failed to fetch products: ${error.message}`);
            }
        }
    },
    
    /**
     * Search for a product
     * 
     * Purpose:
     * - Search products by ASIN, title, or ISBN
     * - Return first matching product
     * 
     * Args:
     *   query - Search term
     *   searchType - 'asin', 'title', or 'isbn'
     *   marketplace - 'US' or 'UK'
     * 
     * Returns:
     *   Promise<Object|null> - Product object or null if not found
     */
    async searchProduct(query, searchType, marketplace) {
        console.log(`[DataService] Searching for ${searchType}: "${query}" in ${marketplace}...`);
        
        const products = await this.getAllProducts(marketplace);
        const queryLower = query.toLowerCase().trim();
        
        // Search logic
        let product = null;
        
        switch(searchType) {
            case 'asin':
                product = products.find(p => 
                    p.asin && p.asin.toLowerCase().includes(queryLower)
                );
                break;
            case 'title':
                product = products.find(p => 
                    p.title && p.title.toLowerCase().includes(queryLower)
                );
                break;
            case 'isbn':
                product = products.find(p => 
                    (p.isbn && p.isbn.toLowerCase().includes(queryLower)) ||
                    (p.isbn13 && p.isbn13.toLowerCase().includes(queryLower))
                );
                break;
        }
        
        if (product) {
            console.log(`[DataService] ✅ Found product: ${product.title}`);
        } else {
            console.log(`[DataService] ⚠️ No product found for: "${query}"`);
        }
        
        return product;
    },
    
    /**
     * Generate quote for a product using Supabase Edge Function
     * 
     * Purpose:
     * - Call Supabase Edge Function to calculate wholesale quote
     * - Uses real Buy Box data and sophisticated ROI logic
     * - Fully serverless - no local backend required!
     * - Returns complete quote with all calculated components
     * 
     * Args:
     *   asin - Product ASIN identifier
     *   marketplace - 'US' or 'UK'
     *   m - Our ROI floor (optional, default 0.10 = 10%)
     *   fx_gbp_to_usd - Exchange rate (optional, default 1.30)
     * 
     * Returns:
     *   Promise<Object> - Complete quote data with all calculations
     *     {
     *       feasible: boolean - Whether quote is possible
     *       reason: string - Explanation if not feasible
     *       quote_q: number - Wholesale quote price
     *       seller_roi_pct: number - Seller ROI percentage
     *       our_roi_pct: number - Our ROI percentage
     *       margin_abs: number - Our absolute margin
     *       margin_pct: number - Our margin percentage
     *       bb_avg: number - 30-day average Buy Box price
     *       af: number - Amazon fee
     *       fc: number - Fulfillment cost
     *       sc: number - Shipping cost
     *       s_bundle: number - Total seller costs
     *       qmin: number - Our minimum quote (10% ROI floor)
     *       qmax_our: number - Our maximum quote (20% ROI cap)
     *     }
     */
    async generateQuote(asin, marketplace, m = null, fx_gbp_to_usd = null) {
        console.log(`[DataService] 📊 Generating quote for ${asin} (${marketplace})...`);
        console.log(`[DataService]    Calling Supabase Edge Function: ${config.EDGE_FUNCTION_URL}`);
        
        try {
            // Build request body
            const requestBody = {
                asin: asin,
                marketplace: marketplace,
                m: m !== null ? m : config.DEFAULT_ROI_FLOOR,
                fx_gbp_to_usd: fx_gbp_to_usd !== null ? fx_gbp_to_usd : config.DEFAULT_FX_RATE
            };
            
            console.log(`[DataService]    Request params:`, requestBody);
            
            // Call Supabase Edge Function
            const response = await fetch(config.EDGE_FUNCTION_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': config.SUPABASE_ANON_KEY,
                    'Authorization': `Bearer ${config.SUPABASE_ANON_KEY}`
                },
                body: JSON.stringify(requestBody)
            });
            
            // Check response status
            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    errorData = { error: `HTTP ${response.status}`, detail: response.statusText };
                }
                
                throw new Error(
                    errorData.detail || errorData.error || 
                    `Edge Function error: ${response.status} ${response.statusText}`
                );
            }
            
            // Parse response
            const quoteData = await response.json();
            
            // Log success (keep internal calculations private)
            console.log(`[DataService] ✅ Quote generated successfully!`);
            console.log(`[DataService]    Quote Price: $${quoteData.quote_q.toFixed(2)}`);
            console.log(`[DataService]    Feasible: ${quoteData.feasible ? 'YES' : 'NO'}`);
            // Note: Internal ROI calculations, costs, and margins are kept private
            
            if (!quoteData.feasible) {
                console.warn(`[DataService]    ⚠️ Quote not feasible: ${quoteData.reason}`);
            }
            
            return quoteData;
            
        } catch (error) {
            console.error(`[DataService] ❌ Quote generation failed:`, error);
            
            // Check if Edge Function is not deployed
            if (error.message.includes('fetch') || error.message.includes('NetworkError') || error.message.includes('404')) {
                console.error(`[DataService] ❌ Cannot connect to Supabase Edge Function`);
                console.error(`[DataService]    Edge Function URL: ${config.EDGE_FUNCTION_URL}`);
                console.error(`[DataService]    Make sure Edge Function is deployed:`);
                console.error(`[DataService]    supabase functions deploy generate_quote`);
                
                // Return fallback data so UI doesn't break
                console.warn(`[DataService] ⚠️ Using fallback quote (Edge Function unavailable)`);
                const products = await this.getAllProducts(marketplace);
                const product = products.find(p => p.asin === asin);
                const fallbackPrice = product?.our_price || 10.00;
                
                return {
                    feasible: false,
                    reason: 'Edge Function unavailable - using fallback price',
                    quote_q: fallbackPrice,
                    seller_roi_pct: 0,
                    our_roi_pct: 0,
                    margin_abs: 0,
                    margin_pct: 0,
                    bb_avg: 0,
                    af: 0,
                    fc: 0,
                    sc: 0,
                    s_bundle: 0,
                    qmin: 0,
                    qmax_our: 0
                };
            }
            
            // Re-throw other errors
            throw error;
        }
    },
    
    /**
     * Get historical data for charts from backfill_test.dynamic_data
     * 
     * Purpose:
     * - Fetch real historical data from dynamic_data table (last 360 days)
     * - Returns buy box price, sales rank, and seller count
     * 
     * Args:
     *   asin - Product ASIN
     *   marketplace - 'US' or 'UK'
     * 
     * Returns:
     *   Promise<Object> - { buyBoxHistory, rankHistory, sellerCount, dates }
     */
    async getHistoricalData(asin, marketplace) {
        console.log(`[DataService] Fetching historical data for ${asin} (${marketplace}) from last 360 days...`);
        
        if (this.isUsingMockData()) {
            // Fallback to placeholder data if using mock mode
            return {
                buyBoxHistory: [15, 15.5, 16, 16.5, 17, 17.5],
                rankHistory: [1000, 950, 900, 850, 800, 750],
                sellerCount: 5,
                dates: ['6 months ago', '5 months ago', '4 months ago', '3 months ago', '2 months ago', '1 month ago']
            };
        }
        
        try {
            // Get Supabase client reference
            const supabaseClient = getSupabaseClient();
            
            if (!supabaseClient) {
                console.error('[DataService] ❌ Supabase client not available');
                throw new Error('Supabase client not initialized');
            }
            
            // Calculate date 360 days ago
            const date360DaysAgo = new Date();
            date360DaysAgo.setDate(date360DaysAgo.getDate() - 360);
            const dateString = date360DaysAgo.toISOString().split('T')[0];
            
            console.log(`[DataService] Querying historical_data view for ASIN: ${asin}, Marketplace: ${marketplace}, Last 360 days`);
            
            // Query the historical_data view (in public schema)
            // This view is automatically exposed via Supabase API - no configuration needed!
            // The view internally queries backfill_test.dynamic_data
            console.log('[DataService] Querying public.historical_data view...');
            
            const { data, error } = await supabaseClient
                .from('historical_data')
                .select('fetch_date, current_buybox_price, sales_rank_current, num_sellers')
                .eq('asin', asin)
                .eq('marketplace', marketplace)
                .gte('fetch_date', dateString)
                .order('fetch_date', { ascending: true });
            
            if (!error) {
                console.log('[DataService] ✅ Query successful!');
            }
            
            if (error) {
                console.error('[DataService] ❌ Error fetching historical data:', error);
                console.error('[DataService] Error details:', JSON.stringify(error));
                console.error('[DataService] Query parameters:', { asin, marketplace, dateString });
                throw error;
            }
            
            console.log(`[DataService] Query returned ${data?.length || 0} records`);
            
            if (!data || data.length === 0) {
                console.warn('[DataService] ⚠️ No historical data found for this product');
                console.warn('[DataService] Please verify:');
                console.warn(`  - ASIN "${asin}" exists in backfill_test.dynamic_data table`);
                console.warn(`  - Marketplace "${marketplace}" matches the database value exactly (case-sensitive)`);
                console.warn(`  - Data exists from ${dateString} onwards`);
                return {
                    buyBoxHistory: [],
                    rankHistory: [],
                    sellerCount: 0,
                    dates: []
                };
            }
            
            // Extract data arrays using correct field names
            const dates = data.map(row => row.fetch_date);
            const buyBoxHistory = data.map(row => parseFloat(row.current_buybox_price) || 0);
            const rankHistory = data.map(row => parseInt(row.sales_rank_current) || 0);
            
            // Get most recent seller count (today's data - last record)
            const sellerCount = data.length > 0 ? (parseInt(data[data.length - 1].num_sellers) || 0) : 0;
            
            console.log(`[DataService] ✅ Fetched ${data.length} days of historical data`);
            console.log(`[DataService] Date range: ${dates[0]} to ${dates[dates.length - 1]}`);
            console.log(`[DataService] Seller count today: ${sellerCount}`);
            console.log(`[DataService] Sample buybox prices:`, buyBoxHistory.slice(0, 3));
            console.log(`[DataService] Sample sales ranks:`, rankHistory.slice(0, 3));
            
            return {
                buyBoxHistory,
                rankHistory,
                sellerCount,
                dates
            };
            
        } catch (error) {
            console.error('[DataService] ❌ Failed to fetch historical data:', error);
            // Return empty data on error
            return {
                buyBoxHistory: [],
                rankHistory: [],
                sellerCount: 0,
                dates: []
            };
        }
    },
    
    /**
     * Transform product from database format to frontend format
     * 
     * Purpose:
     * - Ensure consistent product object structure
     * - Handle missing fields gracefully
     * - Map database fields to frontend fields
     * 
     * Args:
     *   product - Raw product object from database
     * 
     * Returns:
     *   Object - Transformed product object
     */
    _transformProduct(product) {
        // Get image URL - use raw value from database
        const imageUrl = product.image_url;
        
        // Keep the raw image_url as-is from database (will be processed in display layer)
        let finalImageUrl = imageUrl;
        
        // If null or empty, set to null so display layer can handle it
        if (!imageUrl || imageUrl === '' || imageUrl === 'null') {
            finalImageUrl = null;
        }
        
        return {
            id: product.id,
            asin: product.asin,
            title: product.title || 'Untitled',
            author: product.author || 'Unknown Author',
            isbn: product.isbn13 || product.isbn || '',
            publisher: product.category_lvl1 || 'Unknown Publisher',
            category: product.category_lvl2 || 'General',
            category_lvl3: product.category_lvl3 || product.category_lvl2 || 'General',
            format: 'Hardcover',  // Default format
            image: finalImageUrl,
            image_url: finalImageUrl,  // Ensure both properties exist
            description: product.description || 'No description available.',
            quotePrice: parseFloat(product.our_price) || 0,
            our_price: parseFloat(product.our_price) || 0,
            marketplace: product.marketplace,
            rrp: parseFloat(product.rrp) || 0,
            // Package information from database
            package_weight: product.package_weight ? parseFloat(product.package_weight) : null,
            package_dimensions: product.package_dimensions || null,
            // For compatibility
            historicalQuote: [],
            historicalBuyBox: [],
            historicalRank: []
        };
    }
};

// ========== EXPORTS ==========
// Make DataService available globally for vanilla JS
if (typeof window !== 'undefined') {
    window.DataService = DataService;
}

// For ES6 modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataService;
}

