/**
 * Frontend Configuration
 * ----------------------
 * Purpose:
 * - Store all environment-specific configuration
 * - Toggle between mock data (for demo) and live Supabase data
 * - Configure API endpoints
 * 
 * Instructions:
 * 1. Set USE_MOCK_DATA = false to connect to live Supabase
 * 2. Update SUPABASE_URL and SUPABASE_ANON_KEY with your Supabase project credentials
 * 3. Update API_BASE_URL with your backend API URL (if using FastAPI backend)
 * 
 * To get Supabase credentials:
 * 1. Go to your Supabase project dashboard
 * 2. Click Settings → API
 * 3. Copy "Project URL" → SUPABASE_URL
 * 4. Copy "anon public" key → SUPABASE_ANON_KEY
 */

const config = {
    // ========== FEATURE TOGGLE ==========
    // Set to 'false' to use live Supabase data
    // Set to 'true' to use mock data for demo/testing
    USE_MOCK_DATA: false,  // ← LIVE DATA MODE (default)
    
    // ========== SUPABASE CONFIGURATION ==========
    // Your Supabase credentials (configured)
    SUPABASE_URL: 'https://mofhylcyainzwbrcmrqg.supabase.co',
    SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vZmh5bGN5YWluendicmNtcnFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzNDg1MTQsImV4cCI6MjA3NTkyNDUxNH0.TeaalZbVrSkqAszpZxPDSJUdoXL0wsg9veDhS1v8Bj0',
    
    // ========== API CONFIGURATION ==========
    // Supabase Edge Function URL for quote generation
    // No local backend needed - fully serverless!
    // Format: https://[PROJECT_REF].supabase.co/functions/v1/generate_quote
    // You'll get this URL after deploying: supabase functions deploy generate_quote
    EDGE_FUNCTION_URL: 'https://mofhylcyainzwbrcmrqg.supabase.co/functions/v1/generate_quote',
    
    // Legacy API_BASE_URL (deprecated - use EDGE_FUNCTION_URL instead)
    API_BASE_URL: null,
    
    // ========== APP CONFIGURATION ==========
    // Default settings for the app
    DEFAULT_MARKET: 'US',  // 'US' or 'UK'
    DEFAULT_ROI_FLOOR: 0.10,  // 10% minimum ROI
    DEFAULT_FX_RATE: 1.30,  // GBP to USD exchange rate
    
    // Historical data settings
    DAYS_OF_HISTORY: 30,  // Days of historical data to show in charts
    
    // Pagination
    DEFAULT_PAGE_SIZE: 50,
    MAX_PAGE_SIZE: 100
};

// Log configuration on page load (for debugging)
console.log('[Config] Application initialized with:', {
    mode: config.USE_MOCK_DATA ? 'MOCK DATA' : 'LIVE DATA',
    supabaseUrl: config.SUPABASE_URL,
    apiBaseUrl: config.API_BASE_URL
});

// Export configuration (for ES6 modules) or make globally available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = config;
}

