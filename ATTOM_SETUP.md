# ATTOM API Setup Guide

## Quick Start

You already have an ATTOM API key! Here's how to set it up:

### 1. Configure Your API Key

Edit your `.env` file:
```bash
MLS_TYPE=ATTOM
ATTOM_API_KEY=0a9dcf73ec34399b400942babd5334ce
```

(Replace with your actual API key if different)

### 2. Test the Connection

```bash
python main.py --address "1342 E. Kramer Circle" --city "Mesa" --zip "85203"
```

## How ATTOM Works

ATTOM's API is different from traditional MLS systems:

1. **Address-Based Lookups**: ATTOM requires specific addresses, not area searches
2. **Sales Comparables Endpoint**: ATTOM has a dedicated endpoint for finding comparable sales
3. **APN Instead of MLS Numbers**: ATTOM uses Assessor's Parcel Numbers (APN), not MLS numbers

## Usage Examples

### Find Comps by Address
```bash
python main.py --address "123 Main St" --city "Phoenix" --zip "85001"
```

### Find Comps with Criteria
The bot will automatically use the subject property's characteristics to find similar comps:
- Same number of bedrooms
- Similar square footage
- Similar price range
- Within configured distance

## ATTOM API Features

The bot uses ATTOM's **Sales Comparables** endpoint which:
- Finds recently sold properties similar to your subject
- Filters by distance, size, bedrooms, bathrooms, price, and more
- Returns detailed sale information including dates and prices

## Configuration Options

In your `.env` file, you can adjust:

```bash
# Maximum distance for comps (miles)
MAX_COMP_DISTANCE_MILES=5.0

# Maximum age of sold comps (days)
MAX_COMP_AGE_DAYS=180

# Minimum similarity score (0.0-1.0)
MIN_COMP_SCORE=0.7

# Maximum number of comps to return
MAX_COMPS_TO_RETURN=10
```

## API Endpoints Used

1. **Property Basic Profile**: `/propertyapi/v1.0.0/property/basicprofile`
   - Gets subject property details

2. **Sales Comparables**: `/property/v2/SalesComparables/Address/{address}/{city}/-/{state}/{zip}`
   - Finds comparable sales with advanced filtering

## Troubleshooting

### "Could not find subject property"
- Make sure the address is complete and accurate
- Include city and zip code for better results
- Check that the address exists in ATTOM's database

### "No comps found"
- Try increasing `MAX_COMP_DISTANCE_MILES` in `.env`
- Lower `MIN_COMP_SCORE` threshold
- Increase `MAX_COMP_AGE_DAYS` for more historical data

### API Errors
- Verify your API key is correct
- Check your API subscription includes the Sales Comparables endpoint
- Some ATTOM plans may have rate limits

## Advantages of ATTOM

✅ **You already have access** - No waiting for approval  
✅ **Sales Comparables endpoint** - Built specifically for comp analysis  
✅ **Comprehensive data** - Property details, sales history, assessments  
✅ **Reliable** - Professional-grade real estate data  

## Next Steps

1. Set your API key in `.env`
2. Test with a known address
3. Review the comp results
4. Provide feedback to train the bot: `--feedback 0.9`

The bot will learn from your feedback and improve comp selection over time!

