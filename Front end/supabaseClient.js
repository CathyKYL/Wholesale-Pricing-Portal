/**
 * Supabase Client Module
 * ----------------------
 * Purpose:
 * - Initialize and export Supabase client for database access
 * - Handle connection errors gracefully
 * - Provide helper functions for common queries
 * 
 * Usage:
 *   import { supabase, testConnection } from './supabaseClient.js'
 *   
 *   // Test connection
 *   await testConnection()
 *   
 *   // Query products
 *   const { data, error } = await supabase.from('catalog_rows').select('*')
 */

/**
 * Initialize Supabase client
 * 
 * Purpose:
 * - Create authenticated connection to Supabase database
 * - Use config values for URL and API key
 * 
 * Returns:
 *   Supabase client instance or null if using mock data
 */
function initializeSupabase() {
    // If using mock data, don't initialize Supabase
    if (config.USE_MOCK_DATA) {
        console.log('[Supabase] Using mock data mode - Supabase client not initialized');
        return null;
    }
    
    // Validate configuration
    if (!config.SUPABASE_URL || config.SUPABASE_URL === 'https://your-project.supabase.co') {
        console.error('[Supabase] ERROR: SUPABASE_URL not configured in config.js');
        return null;
    }
    
    if (!config.SUPABASE_ANON_KEY || config.SUPABASE_ANON_KEY === 'your-anon-key-here') {
        console.error('[Supabase] ERROR: SUPABASE_ANON_KEY not configured in config.js');
        return null;
    }
    
    try {
        // Create Supabase client using CDN library
        // Note: The Supabase library must be loaded via CDN in index.html:
        // <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
        
        if (typeof supabase === 'undefined' || !supabase.createClient) {
            console.error('[Supabase] ERROR: Supabase library not loaded. Add CDN script to index.html');
            return null;
        }
        
        const client = supabase.createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY);
        
        console.log('[Supabase] ✅ Client initialized successfully');
        console.log('[Supabase] Project URL:', config.SUPABASE_URL);
        
        return client;
        
    } catch (error) {
        console.error('[Supabase] Failed to initialize client:', error);
        return null;
    }
}

/**
 * Test Supabase connection
 * 
 * Purpose:
 * - Verify we can connect to Supabase
 * - Test basic query functionality
 * - Log connection status
 * 
 * Returns:
 *   Promise<boolean> - true if connection successful, false otherwise
 */
async function testConnection() {
    if (!supabaseClient) {
        console.log('[Supabase] Connection test skipped - using mock data mode');
        return false;
    }
    
    try {
        console.log('[Supabase] Testing connection...');
        
        // Simple query to test connection - count products
        const { count, error } = await supabaseClient
            .from('catalog_rows')
            .select('*', { count: 'exact', head: true });
        
        if (error) {
            console.error('[Supabase] ❌ Connection test failed:', error.message);
            return false;
        }
        
        console.log('[Supabase] ✅ Connection successful!');
        console.log(`[Supabase] Found ${count} products in database`);
        return true;
        
    } catch (error) {
        console.error('[Supabase] ❌ Connection test error:', error);
        return false;
    }
}

/**
 * Fetch all products from Supabase
 * 
 * Purpose:
 * - Get all products from public.catalog_rows table
 * - Transform data to match frontend format
 * - Handle errors gracefully
 * 
 * Returns:
 *   Promise<Array> - Array of product objects
 */
async function fetchProducts(marketplace = null) {
    if (!supabaseClient) {
        throw new Error('Supabase client not initialized - check config.js');
    }
    
    try {
        console.log(`[Supabase] Fetching products${marketplace ? ` for ${marketplace}` : ''}...`);
        
        // Build query
        let query = supabaseClient
            .from('catalog_rows')
            .select(`
                id,
                asin,
                marketplace,
                title,
                author,
                available_stock,
                rrp,
                our_price,
                isbn13,
                description,
                image_url,
                category_lvl1,
                category_lvl2,
                category_lvl3,
                package_dimensions,
                package_weight
            `);
        
        // Add marketplace filter if provided
        if (marketplace) {
            query = query.eq('marketplace', marketplace);
        }
        
        const { data, error } = await query;
        
        if (error) {
            console.error('[Supabase] Error fetching products:', error);
            throw error;
        }
        
        console.log(`[Supabase] ✅ Fetched ${data.length} products`);
        return data;
        
    } catch (error) {
        console.error('[Supabase] Failed to fetch products:', error);
        throw error;
    }
}

/**
 * Fetch historical Buy Box data for a product
 * 
 * Purpose:
 * - Get last 30 days of Buy Box price history
 * - Used for charts and analytics
 * 
 * Args:
 *   asin - Product ASIN identifier
 *   marketplace - 'US' or 'UK'
 * 
 * Returns:
 *   Promise<Array> - Array of { date, buy_box_price } objects
 */
async function fetchBuyBoxHistory(asin, marketplace) {
    if (!supabaseClient) {
        throw new Error('Supabase client not initialized');
    }
    
    try {
        console.log(`[Supabase] Fetching Buy Box history for ${asin} (${marketplace})...`);
        
        // Query Backfill_test.dynamic_data table
        const { data, error } = await supabaseClient
            .schema('Backfill_test')
            .from('dynamic_data')
            .select('date, buy_box_price')
            .eq('asin', asin)
            .eq('marketplace', marketplace)
            .order('date', { ascending: false })
            .limit(30);
        
        if (error) {
            console.error('[Supabase] Error fetching Buy Box history:', error);
            throw error;
        }
        
        // Filter out null values
        const filtered = data.filter(row => row.buy_box_price !== null);
        
        console.log(`[Supabase] ✅ Fetched ${filtered.length} Buy Box prices`);
        return filtered;
        
    } catch (error) {
        console.error('[Supabase] Failed to fetch Buy Box history:', error);
        throw error;
    }
}

// ========== INITIALIZE CLIENT ==========
// Create the Supabase client instance
const supabaseClient = initializeSupabase();

// ========== EXPORTS ==========
// Export client and helper functions for use in other modules

// For vanilla JS (no module system), attach to window object
if (typeof window !== 'undefined') {
    window.supabaseClient = supabaseClient;
    window.testSupabaseConnection = testConnection;
    window.fetchSupabaseProducts = fetchProducts;
    window.fetchBuyBoxHistory = fetchBuyBoxHistory;
}

// For ES6 modules (if using a bundler)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        supabaseClient,
        testConnection,
        fetchProducts,
        fetchBuyBoxHistory
    };
}

