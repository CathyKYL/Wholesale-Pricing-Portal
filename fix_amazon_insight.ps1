# PowerShell script to fix all Amazon Insight issues

$filePath = "Front end\script.js"
$content = Get-Content $filePath -Raw

# FIX 1: Add today's stats extraction (current-buybox and current-rank)
$oldStats = @"
    try {
        // Fetch historical data from last 360 days
        const history = await DataService.getHistoricalData(product.asin, currentMarket);

        // Display seller count
        const sellerCountElement = document.getElementById('seller-count');
        if (sellerCountElement) {
            sellerCountElement.textContent = history.sellerCount || 'N/A';
        }

        // Render charts with historical data
        renderChartsWithData(history);
"@

$newStats = @"
    try {
        // Fetch historical data from last 360 days
        const history = await DataService.getHistoricalData(product.asin, currentMarket);

        // Extract today's stats from the last data point
        const hasBuyBoxData = history.buyBoxHistory && history.buyBoxHistory.length > 0;
        const hasRankData = history.rankHistory && history.rankHistory.length > 0;
        
        const todayBuyBox = hasBuyBoxData 
            ? history.buyBoxHistory[history.buyBoxHistory.length - 1] 
            : null;
        const todayRank = hasRankData 
            ? history.rankHistory[history.rankHistory.length - 1] 
            : null;
        
        // Display Current Buy Box Price (Amazon Price)
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
        
        // Display seller count
        const sellerCountElement = document.getElementById('seller-count');
        if (sellerCountElement) {
            sellerCountElement.textContent = history.sellerCount || 'N/A';
        }
        
        console.log('[Display] Amazon Insight - Today''s Stats:');
        console.log(``  Buy Box Price: `${todayBuyBox ? '$' + todayBuyBox.toFixed(2) : 'N/A'}``);
        console.log(``  Sales Rank: `${todayRank ? todayRank.toLocaleString() : 'N/A'}``);
        console.log(``  Seller Count: `${history.sellerCount || 'N/A'}``);

        // Render charts with historical data
        renderChartsWithData(history);
"@

$content = $content.Replace($oldStats, $newStats)

# FIX 2: Invert Y-axis for Sales Rank (lower = better = higher on chart)
$content = $content.Replace('reverse: false, // Don''t reverse, just show as-is', 'reverse: true, // Inverted: lower rank appears higher on chart')

# FIX 3: Simplify X-axis date labels - show year once, then just months
$oldDateFormat = @"
            // Format dates to be more readable
            labels = labels.map(dateStr => {
                const date = new Date(dateStr);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            });
"@

$newDateFormat = @"
            // Format dates: show year when it changes, otherwise just month
            let lastYear = null;
            labels = labels.map(dateStr => {
                const date = new Date(dateStr);
                const year = date.getFullYear();
                const month = date.toLocaleDateString('en-US', { month: 'short' });
                
                if (lastYear !== year) {
                    lastYear = year;
                    return ``${year}- ${month}``;
                }
                return month;
            });
"@

$content = $content.Replace($oldDateFormat, $newDateFormat)

# Save the fixed file
$content | Set-Content $filePath -NoNewline

Write-Host "✅ All Amazon Insight fixes applied successfully!" -ForegroundColor Green
Write-Host "  ✅ Added today's stats extraction (current-buybox, current-rank)" -ForegroundColor Green
Write-Host "  ✅ Inverted Sales Rank Y-axis (lower = better = higher on chart)" -ForegroundColor Green  
Write-Host "  ✅ Simplified X-axis (year shown once, then just months)" -ForegroundColor Green


