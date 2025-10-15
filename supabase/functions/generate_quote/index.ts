/**
 * Supabase Edge Function: Generate Quote
 * ======================================
 * Purpose:
 * - Calculate optimal wholesale quotes for Book Portal
 * - Replace FastAPI backend with serverless function
 * - Apply smooth continuous ROI logic (10-20% our ROI, 10%+ seller ROI)
 * 
 * Endpoint: POST /functions/v1/generate_quote
 * 
 * Request Body:
 * {
 *   "asin": "143914995X",
 *   "marketplace": "US",
 *   "m": 0.10,              // Optional: Our ROI floor (default 10%)
 *   "fx_gbp_to_usd": 1.30   // Optional: Exchange rate (default 1.30)
 * }
 * 
 * Response:
 * {
 *   "feasible": true,
 *   "quote_q": 17.90,
 *   "seller_roi_pct": 25.50,
 *   "our_roi_pct": 15.00,
 *   "margin_abs": 5.20,
 *   "margin_pct": 15.00,
 *   "bb_avg": 23.45,
 *   "af": 3.99,
 *   "fc": 2.50,
 *   "sc": 1.00,
 *   "s_bundle": 7.49,
 *   "qmin": 13.90,
 *   "qmax_our": 15.04
 * }
 */

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// CORS headers for browser requests
// Allow requests from any origin (including file:// and localhost)
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type, x-requested-with',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Max-Age': '86400',
};

/**
 * Calculate fulfillment cost based on weight tiers
 * Same logic as Python tiers.py
 */
function calculateFulfillmentCost(weightKg: number, marketplace: string): number {
  // UK marketplace tiers (in GBP)
  if (marketplace === 'UK') {
    if (weightKg <= 0.46) return 2.29;
    if (weightKg <= 1.00) return 2.68;
    if (weightKg <= 2.00) return 3.50;
    return 4.50; // > 2 kg
  }
  
  // US marketplace tiers (in USD)
  if (weightKg <= 0.46) return 2.92;
  if (weightKg <= 1.00) return 3.43;
  if (weightKg <= 2.00) return 4.47;
  return 5.74; // > 2 kg
}

/**
 * Calculate shipping cost to seller
 * Same logic as Python tiers.py
 */
function calculateShippingCost(marketplace: string, fxGbpToUsd: number): number {
  if (marketplace === 'UK') {
    return 1.00; // GBP
  }
  // US: Convert GBP to USD
  return 1.00 * fxGbpToUsd; // USD
}

/**
 * Calculate optimal wholesale quote using smooth continuous ROI logic
 * Same algorithm as Python calculator.py
 */
function calculateQuote(inputs: {
  asin: string;
  marketplace: string;
  bbAvg: number;
  cCost: number;
  weightKg: number;
  m: number;
  fxGbpToUsd: number;
}) {
  const { asin, marketplace, bbAvg, cCost, weightKg, m, fxGbpToUsd } = inputs;

  // Step 1: Calculate components
  const BB = bbAvg;
  const C = cCost;
  
  // Fulfillment cost (tiered by weight)
  const fc = calculateFulfillmentCost(weightKg, marketplace);
  
  // Shipping to seller
  const sc = calculateShippingCost(marketplace, fxGbpToUsd);
  
  // Amazon fee (17% of Buy Box)
  const af = BB * 0.17;
  
  // Total seller costs
  const S = fc + af + sc;
  
  // Step 2: Our ROI band
  const qmin = C * (1.0 + m);        // Our 10% floor (or custom m)
  const qmaxOur = C * 1.20;          // Our 20% cap
  
  // Step 3: Seller ROI helper functions
  const qSellerFor = (r: number) => {
    // Q that gives seller exactly ROI = r
    // Formula: Q = (BB̄ - (1+r)×S) / (1+r)
    return (BB - (1.0 + r) * S) / (1.0 + r);
  };
  
  const sellerRoi = (Q: number) => {
    // Seller ROI for quote Q
    // Formula: (BB̄ - (Q + S)) / (Q + S)
    return (BB - (Q + S)) / (Q + S);
  };
  
  const ourRoi = (Q: number) => {
    // Our ROI for quote Q
    // Formula: (Q - C) / C
    return (Q - C) / C;
  };
  
  // Calculate reference quotes
  const qSeller10 = qSellerFor(0.10);
  const qSeller30 = qSellerFor(0.30);
  const qSeller40 = qSellerFor(0.40);
  
  // Step 4: Seller-favored decision logic
  let feasible = true;
  let reason: string | null = null;
  
  // Calculate seller ROI at our bounds
  const rSellerAtQmin = sellerRoi(qmin);
  const rSellerAtQmax = sellerRoi(qmaxOur);
  
  let Q: number;
  
  // Check feasibility at our floor
  if (rSellerAtQmin < 0.10) {
    // No deal: even at our 10% floor, seller gets < 10%
    feasible = false;
    reason = "No deal: seller ROI < 10% even at our 10% floor.";
    Q = qmin; // Set to floor for diagnostics
  } else {
    // Deal is feasible - determine quote level
    if (rSellerAtQmin < 0.30) {
      // Seller ROI 10-30% at our floor → stay at floor (favor seller)
      Q = qmin;
    } else {
      // Seller ROI >= 30% at our floor → increase to our 20% cap
      Q = qmaxOur;
    }
  }
  
  // Step 5: Clamp Q to our ROI band
  if (Q < qmin) Q = qmin;
  if (Q > qmaxOur) Q = qmaxOur;
  
  // Step 6: Calculate final metrics
  const rSeller = sellerRoi(Q);
  const rUs = ourRoi(Q);
  
  // Round to 2 decimal places
  const round = (n: number) => Math.round(n * 100) / 100;
  const pct = (n: number) => Math.round(n * 10000) / 100; // Convert to percentage
  
  const marginAbs = Q - C;
  const marginPct = (Q - C) / C;
  
  // Return complete outputs
  return {
    feasible,
    reason,
    quote_q: round(Q),
    seller_roi_pct: pct(rSeller),
    our_roi_pct: pct(rUs),
    margin_abs: round(marginAbs),
    margin_pct: pct(marginPct),
    // Component values
    af: round(af),
    fc: round(fc),
    sc: round(sc),
    s_bundle: round(S),
    qmin: round(qmin),
    qmax_our: round(qmaxOur),
    q_seller10: round(qSeller10),
    q_seller30: round(qSeller30),
    q_seller40: round(qSeller40),
    bb_avg: round(BB)
  };
}

/**
 * Main Edge Function handler
 */
serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response(null, { 
      status: 204,
      headers: corsHeaders 
    });
  }

  try {
    // Parse request body
    const { asin, marketplace, m = 0.10, fx_gbp_to_usd = 1.30 } = await req.json();
    
    // Validate inputs
    if (!asin || !marketplace) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields: asin, marketplace' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    if (marketplace !== 'US' && marketplace !== 'UK') {
      return new Response(
        JSON.stringify({ error: 'Marketplace must be "US" or "UK"' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_ANON_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey);
    
    console.log(`[Quote] Generating quote for ${asin} (${marketplace})`);
    
    // Fetch product data from public.catalog_rows
    const { data: product, error: productError } = await supabase
      .from('catalog_rows')
      .select('our_price, package_weight, asin, marketplace')
      .eq('asin', asin)
      .eq('marketplace', marketplace)
      .single();
    
    if (productError || !product) {
      console.error('[Quote] Product not found:', productError);
      return new Response(
        JSON.stringify({ 
          error: 'Product not found',
          detail: `No product found for ASIN ${asin} in ${marketplace} marketplace`
        }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    // Fetch last 30 days of Buy Box prices from backfill_test.dynamic_data
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    const dateStr = thirtyDaysAgo.toISOString().split('T')[0];
    
    const { data: historyData, error: historyError } = await supabase
      .schema('backfill_test')
      .from('dynamic_data')
      .select('current_buybox_price, fetch_date')
      .eq('asin', asin)
      .eq('marketplace', marketplace)
      .gte('fetch_date', dateStr)
      .order('fetch_date', { ascending: false })
      .limit(30);
    
    if (historyError || !historyData || historyData.length === 0) {
      console.error('[Quote] No Buy Box history found:', historyError);
      return new Response(
        JSON.stringify({ 
          error: 'No Buy Box data available',
          detail: `No historical Buy Box data found for ${asin} in the last 30 days`
        }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    // Calculate 30-day Buy Box average (filter out nulls)
    const prices = historyData
      .map(row => row.current_buybox_price)
      .filter(price => price !== null && price > 0);
    
    if (prices.length === 0) {
      return new Response(
        JSON.stringify({ 
          error: 'No valid Buy Box prices',
          detail: 'All Buy Box prices in history are null or zero'
        }),
        { status: 404, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    const bbAvg = prices.reduce((sum, p) => sum + p, 0) / prices.length;
    
    console.log(`[Quote] Found ${prices.length} days of Buy Box data, average: $${bbAvg.toFixed(2)}`);
    
    // Validate product has required data
    if (!product.our_price || product.our_price <= 0) {
      return new Response(
        JSON.stringify({ 
          error: 'Invalid product data',
          detail: 'Product our_price is missing or invalid'
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    if (!product.package_weight || product.package_weight <= 0) {
      return new Response(
        JSON.stringify({ 
          error: 'Invalid product data',
          detail: 'Product package_weight is missing or invalid'
        }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }
    
    // Calculate quote
    const quote = calculateQuote({
      asin,
      marketplace,
      bbAvg,
      cCost: product.our_price,
      weightKg: product.package_weight,
      m,
      fxGbpToUsd: fx_gbp_to_usd
    });
    
    console.log(`[Quote] Generated quote: $${quote.quote_q}, Seller ROI: ${quote.seller_roi_pct}%, Our ROI: ${quote.our_roi_pct}%`);
    
    // Return quote
    return new Response(
      JSON.stringify(quote),
      { 
        status: 200, 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' } 
      }
    );
    
  } catch (error) {
    console.error('[Quote] Error:', error);
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        detail: error.message 
      }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});

