/**
 * Currency Converter Module
 * -------------------------
 * Purpose:
 * - Convert prices between USD and GBP
 * - Display prices with correct currency symbol
 * - Handle marketplace-specific pricing (US=USD, UK=GBP)
 * 
 * Rules:
 * - US marketplace products are stored in USD
 * - UK marketplace products are stored in GBP
 * - User can toggle display currency (USD/GBP)
 * - Conversion rate: 1 GBP = 1.27 USD (configurable)
 */

const CurrencyConverter = {
    // Exchange rate: 1 GBP = X USD
    GBP_TO_USD_RATE: 1.27,
    USD_TO_GBP_RATE: 1 / 1.27,
    
    /**
     * Format price with correct currency symbol
     * 
     * Args:
     *   price - Numeric price value
     *   currency - 'USD' or 'GBP'
     * 
     * Returns:
     *   Formatted string like "$12.99" or "£12.99"
     */
    formatPrice(price, currency) {
        const numPrice = parseFloat(price) || 0;
        
        if (currency === 'GBP') {
            return `£${numPrice.toFixed(2)}`;
        } else {
            return `$${numPrice.toFixed(2)}`;
        }
    },
    
    /**
     * Convert price from product's native currency to display currency
     * 
     * Args:
     *   price - Original price from database
     *   productMarketplace - 'US' or 'UK' (determines source currency)
     *   displayCurrency - 'USD' or 'GBP' (desired display currency)
     * 
     * Returns:
     *   Converted price value
     */
    convertPrice(price, productMarketplace, displayCurrency) {
        const numPrice = parseFloat(price) || 0;
        
        // Determine source currency based on marketplace
        const sourceCurrency = productMarketplace === 'UK' ? 'GBP' : 'USD';
        
        // No conversion needed if source and display are same
        if (sourceCurrency === displayCurrency) {
            return numPrice;
        }
        
        // Convert GBP → USD
        if (sourceCurrency === 'GBP' && displayCurrency === 'USD') {
            return numPrice * this.GBP_TO_USD_RATE;
        }
        
        // Convert USD → GBP
        if (sourceCurrency === 'USD' && displayCurrency === 'GBP') {
            return numPrice * this.USD_TO_GBP_RATE;
        }
        
        return numPrice;
    },
    
    /**
     * Get formatted price with conversion and symbol
     * 
     * Args:
     *   price - Original price from database
     *   productMarketplace - 'US' or 'UK'
     *   displayCurrency - 'USD' or 'GBP'
     * 
     * Returns:
     *   Formatted string like "$12.99" or "£10.21"
     */
    getDisplayPrice(price, productMarketplace, displayCurrency) {
        const converted = this.convertPrice(price, productMarketplace, displayCurrency);
        return this.formatPrice(converted, displayCurrency);
    },
    
    /**
     * Get currency symbol
     * 
     * Args:
     *   currency - 'USD' or 'GBP'
     * 
     * Returns:
     *   '$' or '£'
     */
    getSymbol(currency) {
        return currency === 'GBP' ? '£' : '$';
    }
};

// Make available globally
if (typeof window !== 'undefined') {
    window.CurrencyConverter = CurrencyConverter;
}

// For ES6 modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CurrencyConverter;
}





