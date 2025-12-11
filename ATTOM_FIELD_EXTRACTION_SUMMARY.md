# ATTOM API Field Extraction Summary

## Overview
This document summarizes the review of ATTOM API documentation and the current field extraction implementation. It identifies which fields are available from which endpoints and which fields require additional API calls.

## API Endpoints Used

### 1. `/property/v2/SalesComparables` (v2 API)
Used for finding comparable properties. Returns subject property + comparables in a single response.

### 2. `/propertyapi/v1.0.0/property/expandedprofile` (v1 API)
Used for detailed subject property information. Provides more comprehensive data than basicprofile.

### 3. `/propertyapi/v1.0.0/property/detail` (v1 API)
Fallback endpoint for property details.

## Field Availability by Endpoint

### ✅ Available in SalesComparables v2 (Comparables)

**Property Characteristics:**
- ✅ Square footage (`@GrossLivingAreaSquareFeetCount`)
- ✅ Bedrooms (`@TotalBedroomCount`)
- ✅ Bathrooms (`@TotalBathroomCount`, `@TotalBathroomFullCount_ext`, `@TotalBathroomHalfCount_ext`)
- ✅ Total rooms (`@TotalRoomCount`)
- ✅ Stories (`@StoriesCount`)
- ✅ Year built (`@PropertyStructureBuiltYear` in `STRUCTURE_ANALYSIS`)
- ✅ Lot size (`@LotSquareFeetCount` in `SITE`)
- ✅ Parking spaces (`@_ParkingSpacesCount` in `CAR_STORAGE`)
- ✅ Garage type (`@_Type` in `CAR_STORAGE`)
- ✅ Heating type (`@_UnitDescription` in `HEATING`)
- ✅ Cooling type (`@_UnitDescription` in `COOLING`)
- ✅ Roof material (from `EXTERIOR_FEATURE` with type "Other" and description containing "Roof")
- ✅ Amenities (`AMENITY` array with `@_Type`)
- ✅ Exterior features (`EXTERIOR_FEATURE` array)

**Sale & Market Data:**
- ✅ Sale price (`@PropertySalesAmount` in `SALES_HISTORY`)
- ✅ Sale date (`@TransferDate_ext` or `@PropertySalesDate` in `SALES_HISTORY`)
- ✅ Sale recency (calculated from sale date)
- ✅ Price per square foot (`@PricePerSquareFootAmount` or calculated)
- ✅ Arms-length transaction (`@ArmsLengthTransactionIndicatorExt`)
- ✅ Financing type (derived from `LOANS_ext` - presence of loan indicates financing)
- ⚠️ Seller concessions (NOT directly available - only seller carryback indicator)

### ⚠️ Partially Available / Requires Additional Endpoints

**Property Characteristics:**
- ⚠️ Architectural style - NOT available in SalesComparables v2. May be available in v1 `expandedprofile` or `detail` endpoints, but field availability varies by county.
- ⚠️ Condition - NOT available in SalesComparables v2. May be available in v1 endpoints, but not consistently.
- ⚠️ Renovation year - NOT available in SalesComparables v2. May be available in v1 endpoints, but not consistently.
- ⚠️ School district - NOT available in SalesComparables v2. Requires separate School API endpoint: `/school/district` or `/school/v4`.
- ⚠️ Proximity to parks/shopping/highway - NOT available. Would require Points of Interest API.
- ⚠️ Waterfront view - NOT available. Would require additional data sources.
- ⚠️ View type - NOT available. Would require additional data sources.

**Sale & Market Data:**
- ⚠️ Seller concessions (closing cost assistance) - NOT directly available in ATTOM API. Only `@SellerCarrybackindicator` is available, which indicates seller financing (different from concessions).
- ⚠️ Seller concessions description - NOT available.

### ✅ Available in expandedprofile/detail v1 (Subject Property)

**Additional fields that may be available (varies by county):**
- ✅ Architectural style (if present in county records)
- ✅ School district (if school data is included)
- ✅ Condition (if present in county records)
- ✅ Renovation year (if present in county records)
- ✅ Seller concessions (if present in sale records)

**Note:** Field availability in v1 endpoints varies significantly by county. Some counties provide more detailed information than others.

## Current Implementation Status

### ✅ Implemented Extractions

1. **From SalesComparables v2:**
   - All basic property characteristics (sqft, beds, baths, rooms, lot, etc.)
   - Sale price, date, recency
   - Price per square foot
   - Arms-length transaction indicator
   - Financing type (derived from loan presence)
   - Seller carryback indicator (captured as seller_concessions_description)

2. **From expandedprofile/detail v1:**
   - Architectural style (if available)
   - School district (if available)
   - Condition (if available)
   - Renovation year (if available)
   - Seller concessions (if available in sale records)
   - Financing type
   - Arms-length transaction

### ⚠️ Fields Not Available from ATTOM API

These fields are included in the Property model but cannot be extracted from ATTOM API responses:

1. **Proximity fields** (`proximity_to_parks`, `proximity_to_shopping`, `proximity_to_highway`)
   - Would require Points of Interest API or geocoding services

2. **View fields** (`waterfront_view`, `view_type`)
   - Would require additional data sources or manual input

3. **Seller concessions (closing cost assistance)**
   - Not available in ATTOM API
   - Only seller carryback (seller financing) is available

4. **School district (for comparables)**
   - Not included in SalesComparables v2 response
   - Would require separate School API call for each property

## Recommendations

1. **For fields not available in SalesComparables:**
   - Consider making additional API calls to `property/detail` or `property/expandedprofile` for each comparable to get architectural style, school district, etc.
   - This would increase API calls and response time, so consider making it optional.

2. **For school district:**
   - Use School API endpoint: `/school/v4` with property coordinates
   - This requires additional API calls but provides accurate school district information

3. **For proximity and view fields:**
   - Consider integrating with Google Maps Places API or similar services
   - Or allow manual input/editing of these fields

4. **For seller concessions:**
   - This data may need to come from MLS or other sources
   - Consider allowing manual input or integration with MLS data

## Code Updates Made

1. ✅ Enhanced `_parse_property_detail()` to extract:
   - Architectural style
   - School district
   - Condition
   - Renovation year
   - Seller concessions
   - Financing type
   - Arms-length transaction
   - Sale recency
   - Price per square foot

2. ✅ Enhanced `_parse_comparable_property_v2()` to extract:
   - Seller carryback indicator (as seller_concessions_description)
   - All transaction details (arms-length, financing type, sale recency)

3. ✅ Enhanced `_parse_subject_property_v2()` to extract:
   - All transaction details from SALES_HISTORY
   - Seller carryback indicator

4. ✅ Added comments documenting field availability and limitations

## Testing Recommendations

1. Test with properties from different counties to verify field availability
2. Test with properties that have seller carryback to verify extraction
3. Test with properties that have school district data in v1 endpoints
4. Verify that missing fields gracefully default to None without errors
