# Estated API Setup Guide

## ⚠️ IMPORTANT: Estated API Deprecation Notice

**Estated API is being deprecated in 2026** and migrated to ATTOM infrastructure. 

- Estated documentation will be deprecated at some point in 2026
- Your existing API keys will remain valid during the transition
- No downtime expected during migration
- Updated documentation will be available through ATTOM

**Recommendation**: Since you're already using ATTOM, Estated may become redundant. Consider:
1. Testing if ATTOM's data completeness has improved (they may be merging Estated's data)
2. Using Estated only as a temporary fallback until ATTOM improves
3. Removing Estated dependency once ATTOM data is sufficient

For issues or questions, visit: https://www.attomdata.com/contact-us/

---

## Quick Start

Estated API is integrated as a **temporary fallback** to fill in missing bedrooms/bathrooms when ATTOM data is incomplete. **Note**: This will likely become unnecessary once ATTOM completes their migration.

## Step 1: Get Your API Key

1. Go to [estated.com](https://estated.com)
2. Sign up for a free account
3. Navigate to your dashboard and get your API key
4. The free tier includes:
   - 100 property lookups per month
   - Good for testing and small-scale use

## Step 2: Add to .env File

Add these lines to your `.env` file:

```env
# Estated API (optional - fallback for missing data)
ESTATED_API_KEY=your_api_key_here
ESTATED_ENABLED=true
```

**Note**: Set `ESTATED_ENABLED=true` to enable the fallback. If you don't set this or set it to `false`, Estated won't be used.

## Step 3: Test It

1. Search for a property that's missing bedrooms/bathrooms
2. Check the logs - you should see:
   ```
   Attempting to fetch missing data from Estated API...
   ✓ Got bedrooms from Estated: 4
   ✓ Got bathrooms from Estated: 2.5
   ```

## How It Works

1. **Primary**: ATTOM API provides the initial property data
2. **Fallback**: If bedrooms/bathrooms are missing, Estated API is called
3. **Estimation**: If Estated also doesn't have the data, estimation from square footage is used

The system will:
- Only call Estated if `ESTATED_ENABLED=true` and `ESTATED_API_KEY` is set
- Only call Estated if bedrooms OR bathrooms are missing
- Fill in other missing fields if Estated has them (lot size, parking, etc.)
- Fall back to estimation if Estated doesn't have the data

## Cost Considerations

- **Free tier**: 100 lookups/month
- **Paid tiers**: Start at $49/month for more lookups
- **Usage**: Only called when ATTOM data is incomplete, so usage is minimal

## Troubleshooting

### Estated API not being called
- Check that `ESTATED_ENABLED=true` in `.env`
- Check that `ESTATED_API_KEY` is set correctly
- Check logs for error messages

### Estated returns no data
- Verify the address format matches what Estated expects
- Check that the property exists in Estated's database
- Some properties may not be in Estated's database

### API Key errors
- Verify your API key is correct
- Check that your account is active
- Ensure you haven't exceeded your monthly limit

## Example .env Configuration

```env
# ATTOM API (required)
ATTOM_API_KEY=your_attom_key

# Estated API (optional fallback)
ESTATED_API_KEY=your_estated_key
ESTATED_ENABLED=true

# Google Maps (optional)
GOOGLE_MAPS_API_KEY=your_google_key
```

## Next Steps

After setting up Estated:
1. Test with a property that has missing bedrooms/bathrooms
2. Monitor your Estated API usage in their dashboard
3. **Check if ATTOM data has improved** - they may be merging Estated's data
4. **Plan to remove Estated** once ATTOM migration is complete (2026)

## Migration Timeline

- **2025**: Estated API continues to work, but documentation won't be updated
- **2026**: Estated documentation will be deprecated (exact date TBD)
- **Future**: All functionality will be available through ATTOM

## Recommendation

Since Estated is being merged into ATTOM:
1. **Test ATTOM first** - Check if their data completeness has improved
2. **Use Estated sparingly** - Only as a temporary fallback
3. **Monitor ATTOM updates** - They may add Estated's data sources
4. **Plan migration** - Remove Estated dependency once ATTOM is sufficient

