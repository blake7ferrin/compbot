# Oxylabs Web Scraper API Setup Guide

## Quick Start

Oxylabs Web Scraper API is now integrated as a fallback to scrape Redfin/Zillow when ATTOM and Estated data is incomplete.

⚠️ **Important**: This scrapes Redfin/Zillow websites. Be aware of their Terms of Service. Use responsibly.

## Step 1: Get Your Credentials

1. Log into [Oxylabs Dashboard](https://dashboard.oxylabs.io/)
2. Go to your account settings
3. Find your **Username** and **Password** (API credentials)
4. You can also test in the [API Playground](https://dashboard.oxylabs.io/en/api-playground)

## Step 2: Add to .env File

Add these lines to your `.env` file:

```env
# Oxylabs Web Scraper API (optional - fallback via scraping)
OXYLABS_USERNAME=your_username_here
OXYLABS_PASSWORD=your_password_here
OXYLABS_ENABLED=true
```

**Note**: Set `OXYLABS_ENABLED=true` to enable the fallback. If you don't set this or set it to `false`, Oxylabs won't be used.

## Step 3: Test It

1. Search for a property that's missing bedrooms/bathrooms
2. Check the logs - you should see:
   ```
   Attempting to fetch missing data from Oxylabs (scraping Redfin/Zillow)...
   ✓ Got bedrooms from Oxylabs: 4
   ✓ Got bathrooms from Oxylabs: 2.5
   ```

## How It Works

1. **Primary**: ATTOM API provides the initial property data
2. **Fallback #1**: If bedrooms/bathrooms are missing, Estated API is called
3. **Fallback #2**: If still missing, Oxylabs scrapes Redfin/Zillow
4. **Estimation**: If scraping also doesn't work, estimation from square footage is used

The system will:
- Only call Oxylabs if `OXYLABS_ENABLED=true` and credentials are set
- Only call Oxylabs if bedrooms OR bathrooms are still missing after Estated
- Try Redfin first, then Zillow if Redfin doesn't work
- Fill in other missing fields if available (square feet, price, etc.)
- Fall back to estimation if scraping doesn't work

## What Gets Scraped

Oxylabs will attempt to extract:
- **Bedrooms** - From property listing pages
- **Bathrooms** - From property listing pages
- **Square Feet** - If available on the page
- **List Price** - If available on the page
- **Other details** - As available

## Cost Considerations

- **Free trial**: Available for testing
- **After trial**: Pay-per-request pricing
- **Usage**: Only called when ATTOM + Estated don't have data
- **Recommendation**: Monitor usage during trial to estimate costs

## Legal/ToS Considerations

⚠️ **Important Notes**:

- **Redfin Terms of Service**: May prohibit automated scraping
- **Zillow Terms of Service**: May restrict automated access
- **Use responsibly**: Don't abuse the service
- **Consider alternatives**: Official APIs (ATTOM, Estated) are safer

**Recommendation**: Use Oxylabs only when official APIs fail. Prefer ATTOM and Estated when possible.

## Troubleshooting

### Oxylabs not being called
- Check that `OXYLABS_ENABLED=true` in `.env`
- Check that `OXYLABS_USERNAME` and `OXYLABS_PASSWORD` are set correctly
- Check logs for error messages

### Oxylabs returns no data
- Redfin/Zillow page structure may have changed
- Property may not be listed on Redfin/Zillow
- Check Oxylabs dashboard for API errors
- Try testing in the API Playground first

### Authentication errors
- Verify your username and password are correct
- Check that your trial/account is active
- Ensure you haven't exceeded rate limits

### Parsing errors
- Redfin/Zillow may have changed their HTML structure
- The parser may need updates
- Check logs for specific parsing errors

## Example .env Configuration

```env
# ATTOM API (required)
ATTOM_API_KEY=your_attom_key

# Estated API (optional fallback)
ESTATED_API_KEY=your_estated_key
ESTATED_ENABLED=true

# Oxylabs Web Scraper (optional fallback)
OXYLABS_USERNAME=your_oxylabs_username
OXYLABS_PASSWORD=your_oxylabs_password
OXYLABS_ENABLED=true

# Google Maps (optional)
GOOGLE_MAPS_API_KEY=your_google_key
```

## Testing in API Playground

Before using in production, test in the [Oxylabs API Playground](https://dashboard.oxylabs.io/en/api-playground):

1. Select "Universal" source
2. Enter a Redfin or Zillow property URL
3. Test the request
4. Check if data is extracted correctly
5. Adjust parsing if needed

## Data Flow Priority

```
1. ATTOM API (Primary - official data)
   ↓ (if missing bedrooms/bathrooms)
2. Estated API (Fallback #1 - official API)
   ↓ (if still missing)
3. Oxylabs Scraper (Fallback #2 - scrapes Redfin/Zillow)
   ↓ (if still missing)
4. Estimation (Last resort - from square footage)
```

## Best Practices

1. **Use official APIs first** - ATTOM and Estated are safer and more reliable
2. **Monitor Oxylabs usage** - Track costs during trial
3. **Test thoroughly** - Use API Playground to verify it works
4. **Respect ToS** - Use responsibly, don't abuse
5. **Have fallbacks** - Estimation ensures you always get some data

## Next Steps

After setting up Oxylabs:
1. Test with a property that has missing bedrooms/bathrooms
2. Monitor your Oxylabs API usage in their dashboard
3. Check logs to see when Oxylabs is being called
4. Evaluate if the cost is worth it after trial

## When to Use Oxylabs

✅ **Use Oxylabs when:**
- ATTOM doesn't have the data
- Estated doesn't have the data
- You need data that's only on Redfin/Zillow
- Cost is acceptable for your use case

❌ **Skip Oxylabs when:**
- ATTOM/Estated have the data
- Cost is a concern
- You want to avoid ToS risks
- Official APIs are sufficient

## Summary

Oxylabs is a powerful tool for filling data gaps, but:
- ⚠️ **Use as last resort** - After ATTOM and Estated
- ⚠️ **Be aware of ToS** - Scraping has legal considerations
- ⚠️ **Monitor costs** - Pay-per-request can add up
- ✅ **Test first** - Use API Playground to verify

For most use cases, ATTOM + Estated + Estimation should be sufficient. Oxylabs is useful when you absolutely need data that's only available on listing sites.

