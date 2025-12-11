# PropertyRadar API Integration Guide

## Overview

**Yes, PropertyRadar has a comprehensive API!** This could be an excellent addition to your data sources, especially since Estated is being deprecated.

## API Features

According to [PropertyRadar's developer documentation](https://developers.propertyradar.com/):

### ✅ What PropertyRadar API Offers:
- **250+ property search criteria** - Very comprehensive
- **Property data access** - Addresses, ownership, property details
- **Owner information** - Contact details, phone numbers, emails
- **List building** - Create and manage property lists
- **Automations** - Set up automated workflows
- **REST API** - Standard REST with JSON responses
- **OAuth support** - For partner applications

### 📊 Data Available:
- Property addresses and details
- Owner information
- Contact information (phone, email)
- Property characteristics
- Market data
- And much more (250+ criteria!)

## Getting Started

### Step 1: Activate Free Trial
1. Log into your PropertyRadar account
2. Click profile icon → "Account Settings"
3. Click "Get API Free Trial" at the bottom
4. **30-day free trial** available

### Step 2: Get Your API Key
1. Go to "Account Settings"
2. Scroll to bottom
3. Find your API key under "Integration Name"
4. Click to reveal your actual key

### Step 3: Access Documentation
- **API Docs**: https://developers.propertyradar.com/
- **Help Center**: https://help.propertyradar.com/

## Requirements

⚠️ **Important**: 
- **Paid PropertyRadar subscription required** (after trial)
- API is for **end-users only** (not for resale applications)
- **OAuth available** for partner applications

## Comparison to Your Current Stack

| Feature | ATTOM | Estated (deprecated) | PropertyRadar |
|---------|-------|---------------------|---------------|
| **API Available** | ✅ Yes | ✅ Yes (until 2026) | ✅ Yes |
| **Data Completeness** | ⚠️ Varies by county | ✅ Good | ✅ Excellent (250+ criteria) |
| **Owner Info** | ❌ Limited | ❌ No | ✅ Yes (phone, email) |
| **Cost** | Paid | Free tier → Paid | Paid subscription required |
| **Status** | Primary source | Deprecated 2026 | Available now |

## Integration Strategy

### Option 1: Replace Estated with PropertyRadar
Since Estated is being deprecated, PropertyRadar could be a better fallback:

```
1. ATTOM API (Primary)
   ↓ (if missing data)
2. PropertyRadar API (Fallback - better than Estated)
   ↓ (if still missing)
3. Estimation from square footage
```

### Option 2: Use PropertyRadar for Owner Data
PropertyRadar excels at owner information (phone, email) which ATTOM doesn't provide:

```
1. ATTOM API (Property data)
2. PropertyRadar API (Owner contact info)
3. Combine both sources
```

### Option 3: PropertyRadar as Primary
If PropertyRadar has better data completeness:

```
1. PropertyRadar API (Primary - if data is better)
2. ATTOM API (Fallback)
3. Estimation (Last resort)
```

## Implementation

### Basic API Structure

PropertyRadar uses REST API with JSON:

```python
# Example API call structure
import requests

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Search properties
response = requests.get(
    "https://api.propertyradar.com/v1/properties",
    headers=headers,
    params={
        "address": "123 Main St",
        "city": "Phoenix",
        "state": "AZ"
    }
)
```

### Integration into Your Bot

You could add PropertyRadar as a connector similar to Estated:

```python
# In alternative_apis.py
class PropertyRadarConnector(MLSConnector):
    """PropertyRadar API connector."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.propertyradar.com/v1"
    
    def get_property_by_address(self, address, city, state, zip_code):
        # Implement PropertyRadar API call
        # Parse response
        # Return Property object
```

## Advantages for Your Use Case

### ✅ Better Than Estated:
- **More comprehensive** - 250+ search criteria vs Estated's limited fields
- **Owner contact info** - Phone numbers, emails (ATTOM doesn't have this)
- **Not being deprecated** - Long-term solution
- **Professional grade** - Used by real estate professionals

### ✅ Complements ATTOM:
- **Owner information** - ATTOM doesn't provide phone/email
- **Better data completeness** - May fill gaps ATTOM has
- **Market insights** - Additional market data

## Cost Considerations

- **Free trial**: 30 days
- **After trial**: **$500/month** (very expensive)
- **Value**: Only worth it if you need owner contact info and have high-volume use case
- **Recommendation**: **Skip PropertyRadar** - too expensive for most use cases

## Recommendations

### ⚠️ Cost Prohibitive ($500/month)

**PropertyRadar API is too expensive** for most use cases. At $500/month, it's not cost-effective unless you:
- Have very high volume (thousands of properties/month)
- Absolutely need owner contact information
- Have a business model that justifies the cost

### Better Alternatives:

1. **Stick with ATTOM + Estimation** (Current setup)
   - ATTOM is your primary (already paid)
   - Estimation fills gaps (free)
   - Cost: Just ATTOM subscription

2. **Use Estated while it lasts** (Until 2026)
   - Free tier: 100/month
   - Paid: $49+/month
   - Much cheaper than PropertyRadar

3. **Consider RealtyMole** (If needed)
   - Freemium model
   - Lower cost than PropertyRadar
   - Good for property data

### Recommendation: **Skip PropertyRadar API**

At $500/month, it's not worth it unless you have a specific high-value use case that requires owner contact information.

## Next Steps

1. **Activate API trial** (if you have PropertyRadar account)
2. **Review API documentation**: https://developers.propertyradar.com/
3. **Test API calls** - See what data is available
4. **Compare to ATTOM** - Check if PropertyRadar has better completeness
5. **Decide on integration** - If data is better, integrate it

## Integration Priority

Since Estated is being deprecated, PropertyRadar could be a good replacement:

**Current (with Estated deprecated):**
- ATTOM → Estated (deprecated) → Estimation

**With PropertyRadar:**
- ATTOM → PropertyRadar → Estimation

This would give you a more reliable, long-term fallback solution.

## Questions to Ask PropertyRadar

1. **API pricing** - What's the cost after trial?
2. **Rate limits** - How many API calls per month?
3. **Data completeness** - Do they have bedrooms/bathrooms for all properties?
4. **Owner data** - What owner information is available?
5. **Integration support** - Do they offer integration help?

## Resources

- **API Documentation**: https://developers.propertyradar.com/
- **Help Center**: https://help.propertyradar.com/
- **Activate Trial**: Log into PropertyRadar → Account Settings → Get API Free Trial
- **Zapier Integration**: https://www.propertyradar.com/integrations

## Summary

**PropertyRadar API is available and could be excellent for your project:**

✅ **Pros:**
- Comprehensive (250+ criteria)
- Owner contact information
- Not being deprecated
- Professional-grade data

⚠️ **Cons:**
- Requires paid subscription
- Need to evaluate cost vs. value

**Recommendation**: If you already have PropertyRadar, definitely activate the API trial and test it. It could be a better replacement for Estated and provide data ATTOM doesn't have (like owner contact info).

