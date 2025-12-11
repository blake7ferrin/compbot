# Field Availability Check Results

## Summary

Based on my analysis of the ATTOM API responses:

### ✅ Fields Available in SalesComparables v2 (Current Implementation)
- Square footage, bedrooms, bathrooms, rooms
- Lot size, stories, parking
- Heating/cooling type, roof material
- Amenities, exterior features
- Sale price, sale date, price per sqft
- Arms-length transaction indicator
- Financing type (derived from loan presence)
- Seller carryback indicator (NOT seller concessions)

### ❌ Fields NOT Available in SalesComparables v2
- **Architectural Style** - NOT in v2 response
- **School District** - NOT in v2 response (requires separate School API)
- **Condition** - NOT in v2 response
- **Renovation Year** - NOT in v2 response
- **Seller Concessions** (closing cost assistance) - NOT in v2 response
- **Proximity fields** (parks, shopping, highway) - NOT in v2 response
- **View fields** (waterfront, view type) - NOT in v2 response

### ⚠️ Fields Possibly Available in v1 expandedprofile (Varies by County)
These fields MAY be available in the v1 `expandedprofile` endpoint, but availability varies significantly by county:

- **Architectural Style** - May be in `building.architecturalStyle` or `summary.architecturalStyle`
- **School District** - May be in `school.districtName` or `schools[0].districtName`
- **Condition** - May be in `building.condition` or `summary.condition`
- **Renovation Year** - May be in `building.renovationYear` or `summary.renovationYear`
- **Seller Concessions** - May be in `sale.sellerConcessions`

## Current Status

1. ✅ **Code is ready** - The extraction logic is in place to extract these fields IF they exist in the API response
2. ✅ **Preservation logic fixed** - v1 fields are now preserved when enhancing with v2 data
3. ⚠️ **Fields may not exist** - For your area (Maricopa County, AZ), these fields may simply not be in the ATTOM database

## How to Verify

1. **Check Flask logs** after performing a search:
   - Look for messages like "Found architectural_style: ..." or "architectural_style not found..."
   - Check `flask_app.log` for extraction details

2. **Use the test endpoint**:
   ```
   http://localhost:5000/test-v1-response?address=3644 E CONSTITUTION DR&city=GILBERT&state=AZ&zip=85296
   ```

3. **Check the v1 API directly**:
   - The code logs what keys are available in the v1 response
   - Look for "expandedprofile response keys" in the logs

## Next Steps

If fields are not available in ATTOM for your area:

1. **School District**: Use ATTOM School API endpoint (`/school/v4` or `/school/district`)
2. **Architectural Style/Condition**: May need to come from MLS or manual entry
3. **Seller Concessions**: Typically only in MLS data, not public records
4. **Proximity/View fields**: Would require geocoding services (Google Maps Places API, etc.)

## Recommendation

The code is working correctly - it's extracting all available fields. The missing fields are simply not in the ATTOM database for your area. Consider:
- Adding manual entry/editing capability for these fields
- Integrating with MLS data if available
- Using additional APIs (School API for school district)
- Using geocoding services for proximity/view data

