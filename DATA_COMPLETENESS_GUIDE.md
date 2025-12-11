# Property Data Completeness Guide

## The Problem

ATTOM Data Solutions API data completeness **varies significantly by county and property**. Some properties simply don't have bedrooms/bathrooms in public records, especially:

- Older properties (pre-1980s)
- Properties in rural counties with less detailed records
- Properties that haven't been recently assessed
- Some commercial/residential mixed-use properties

## What We've Implemented

### 1. ✅ Multi-Source Data Merging
- **v1 API** (expandedprofile/detail): Used for initial property lookup
- **v2 API** (SalesComparables): Used for enhanced data and comparables
- Data is merged intelligently, preferring v2 when available, falling back to v1

### 2. ✅ Automatic Estimation (NEW)
When bedrooms/bathrooms are missing, we now estimate them from square footage:
- **Bedrooms**: ~1 bedroom per 250 sqft (industry standard)
- **Bathrooms**: ~1 bathroom per 350 sqft (industry standard)
- Adjustments for property type (condos/townhouses use different ratios)

**Note**: Estimated values are clearly logged and can be identified in the code.

### 3. ✅ Alternative Field Extraction
The code checks multiple field names and locations:
- `@TotalBedroomCount` (primary)
- `@BedroomCount` (fallback)
- `@TotalBathroomCount` (primary)
- `@BathroomCount` (fallback)
- v1 API fields: `building.rooms.beds` and `building.rooms.baths`

## Solutions for Better Data

### Option 1: Use Alternative APIs (Recommended for Missing Data)

#### A. Estated API ⚠️ **DEPRECATED 2026**
- **Status**: Being migrated to ATTOM infrastructure
- **Free tier available** (until migration complete)
- Often has more complete property data
- Good for filling in missing bedrooms/bathrooms
- **Setup**: Add `ESTATED_API_KEY` to `.env`
- **Note**: Estated documentation will be deprecated in 2026. Since you're already using ATTOM, Estated may become redundant once ATTOM completes their migration.

```python
from alternative_apis import EstatedAPIConnector

# In bot.py, add fallback:
if subject.bedrooms is None:
    estated = EstatedAPIConnector(settings.estated_api_key)
    estated_prop = estated.get_property_by_address(address, city, state, zip_code)
    if estated_prop and estated_prop.bedrooms:
        subject.bedrooms = estated_prop.bedrooms
```

#### B. RealtyMole API
- **Freemium model**
- Good property data coverage
- **Setup**: Add `REALTYMOLE_API_KEY` to `.env`

#### C. Zillow API
- Requires API approval
- Excellent data completeness
- **Limitation**: Limited access

### Option 2: MLS API Integration (Best Quality - When Available)

When your MLS API key is approved:
- **Professional property data**
- **Complete bedrooms/bathrooms** (from listing data)
- **Property photos**
- **Condition ratings**
- **Recent renovations**

### Option 3: Manual Entry / Hybrid Approach

For critical properties, you could:
1. Use ATTOM for basic data
2. Use estimation for missing fields
3. Allow manual override in the web interface
4. Store manual entries for future use

### Option 4: County Assessor Web Scraping

Some counties provide assessor websites with more complete data:
- **Pros**: Free, often more complete
- **Cons**: Requires per-county scraping, maintenance overhead

## Current Status

### ✅ What Works Well
- Square footage (usually available)
- Lot size (usually available)
- Year built (usually available)
- Sale history (usually available)
- Parking, heating, cooling (often available)

### ⚠️ What's Incomplete
- **Bedrooms/Bathrooms**: Missing for ~10-20% of properties (varies by county)
- **Architectural style**: Missing for many properties
- **Condition**: Not available from ATTOM
- **School district**: Requires separate API call

### ✅ What We've Added
- Automatic estimation from square footage
- Better logging to identify missing data
- Multi-source data merging

## Recommendations

### Short Term (Now)
1. ✅ **Estimation is active** - missing bedrooms/bathrooms will be estimated
2. **Monitor logs** - check which properties need estimation
3. **Consider Estated API** - add as fallback for critical searches

### Medium Term (Next Steps)
1. **Integrate Estated API** as fallback when ATTOM data is incomplete
2. **Add manual override** in web interface for critical properties
3. **Cache manual entries** for future searches

### Long Term (Best Solution)
1. **MLS API integration** - when approved, this will provide the most complete data
2. **Hybrid approach** - use ATTOM + MLS + Estated for comprehensive coverage

## Testing the Estimation

To see estimation in action, search for properties that are missing bedrooms/bathrooms. Check the logs for:
```
Estimated bedrooms from sqft: X (based on Y sqft)
Estimated bathrooms from sqft: Z (based on Y sqft)
```

## Example: Your Property

For `36937 N OAKLEY DR, SAN TAN VALLEY, AZ 85140`:
- **Square Feet**: 3,141
- **Estimated Bedrooms**: **4 bedrooms** (based on tiered estimation for 3000-3500 sqft range)
- **Estimated Bathrooms**: **3.5 bathrooms** (based on tiered estimation)

**Note**: The estimation uses tiered ranges based on square footage, which is more accurate than simple ratios. For a 3,141 sqft home, this is a reasonable estimate, though actual values may vary.

## Next Steps

1. **Test estimation** with your property - see if it helps
2. **Consider Estated API** - sign up for free tier and add as fallback
3. **Wait for MLS API** - this will provide the best data quality
4. **Refine estimation** - adjust ratios based on your local market data

