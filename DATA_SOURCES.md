# Data Sources for Enhanced Property Information

This document outlines the various ways to add more property data to the MLS Comp Bot.

## Current Data Sources

### 1. ATTOM Data Solutions API (Currently Used)
**What we're extracting:**
- ✅ Basic property info (address, type, year built)
- ✅ Square footage
- ✅ Bedrooms, bathrooms (with full/half breakdown)
- ✅ Total rooms
- ✅ Lot size (square feet and acres)
- ✅ Parking spaces and garage type
- ✅ Heating and cooling systems
- ✅ Roof material
- ✅ Exterior features
- ✅ Amenities (pool, fireplace, etc.)
- ✅ Sale history and prices
- ✅ Coordinates (lat/long)

**What ATTOM doesn't provide:**
- ❌ Property photos/images
- ❌ Property condition ratings
- ❌ Interior photos
- ❌ Recent renovation information

## Additional Data Source Options

### 2. Google Street View API (Recommended for Photos)
**Free tier:** $200/month credit (good for ~28,000 requests)
**What it provides:**
- Street-level photos of properties
- 360° panoramic views
- Static images via API

**Implementation:**
```python
# Already implemented - generates Street View URLs
street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"
```

**For embedded images (requires API key):**
```python
# Add to .env: GOOGLE_MAPS_API_KEY=your_key
street_view_image = f"https://maps.googleapis.com/maps/api/streetview?size=600x400&location={lat},{lon}&key={api_key}"
```

### 3. MLS API (Best Option - When Approved)
**What it provides:**
- ✅ Professional property photos
- ✅ Property condition/quality ratings
- ✅ Detailed room descriptions
- ✅ Recent renovations/updates
- ✅ Interior photos
- ✅ Virtual tours
- ✅ Agent notes and descriptions

**Status:** Waiting for API key approval

### 4. Zillow API / Zillow Web Scraping
**Pros:**
- Lots of property photos
- Zestimate (automated valuation)
- Property history

**Cons:**
- API access is limited/restricted
- Web scraping has legal/ethical concerns
- Terms of service restrictions

### 5. Redfin API
**Similar to Zillow:**
- Property photos
- Market data
- Limited API access

### 6. PropertyRadar / CoreLogic
**Professional data providers:**
- Comprehensive property data
- Condition assessments
- Professional photos
- **API Cost: $500/month** ⚠️ **Too expensive for most use cases**
- Requires paid subscription

### 7. County Assessor Records (Web Scraping)
**Free but limited:**
- Property tax records
- Assessor photos (if available)
- Building permits
- Requires per-county scraping

## Recommended Implementation Strategy

### Phase 1: Current (Done ✅)
- Extract all available ATTOM data
- Generate Google Street View links
- Display in web interface

### Phase 2: Google Maps API (Easy)
1. Get Google Maps API key (free tier available)
2. Add Street View embedded images
3. Add satellite view images
4. Cost: Free for reasonable usage

### Phase 3: MLS API (Best Quality)
1. Wait for API approval
2. Integrate MLS photos
3. Add condition/quality ratings
4. Add interior photos and virtual tours

### Phase 4: Hybrid Approach (Optional)
1. Use ATTOM for basic data
2. Use Google for street view
3. Use MLS for professional photos
4. Combine all sources for comprehensive view

## Property Condition Estimation

Since ATTOM doesn't provide condition ratings, we can estimate:

1. **Based on Year Built:**
   - New (0-5 years): Excellent
   - Recent (5-15 years): Very Good
   - Established (15-30 years): Good
   - Older (30-50 years): Fair
   - Historic (50+ years): Varies

2. **Based on Sale History:**
   - Recent sales suggest maintained property
   - Price trends indicate condition

3. **Based on Features:**
   - Recent renovations (if available)
   - Updated systems (heating/cooling)

4. **MLS Data (when available):**
   - Professional condition ratings
   - Inspection reports
   - Agent assessments

## Next Steps

1. ✅ Extract all ATTOM data (DONE)
2. ⏳ Add Google Maps API key for embedded images
3. ⏳ Wait for MLS API approval
4. ⏳ Add condition estimation logic
5. ⏳ Update web interface to show all new data
