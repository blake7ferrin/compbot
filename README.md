# MLS Comp Bot

An intelligent bot that connects to your MLS (Multiple Listing Service) and finds comparable properties for real estate analysis.

## Features

- **MLS Integration**: Supports RETS, RESO Web API, ATTOM, Zillow, Estated, and RealtyMole
- **Intelligent Comp Analysis**: Advanced algorithm to find the best comparable properties
- **Machine Learning**: Learns from your feedback to improve comp selection over time
- **Flexible Search**: Find comps by MLS number, address, or property criteria
- **Detailed Reports**: Comprehensive analysis with similarity scores, distances, and price comparisons
- **Property Valuation Reports**: Generate professional reports with valuation reasoning, property details, and comp analysis
- **Alternative APIs**: Use Estated or RealtyMole while waiting for MLS approval

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd mls_comp_bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your MLS connection:**
   ```bash
   # NOTE: this repo ships `env.example` (no leading dot) to avoid accidental commits
   cp env.example .env
   ```

   Optional: enable PropertyRadar enrichment (investor data like equity / free-and-clear / cash buyer):
   - Set `PROPERTYRADAR_ENABLED=true`
   - Set `PROPERTYRADAR_API_KEY=...`
   
   Edit `.env` with your MLS credentials:
   - **For ATTOM (Recommended)**: Set `MLS_TYPE=ATTOM` and provide your ATTOM API key
   - For RETS: Set `MLS_TYPE=RETS` and provide RETS credentials
   - For RESO Web API: Set `MLS_TYPE=RESO_WEB_API` and provide OAuth credentials
   - **While waiting for MLS approval**: Use `MLS_TYPE=ESTATED` or `MLS_TYPE=REALTYMOLE` with free API keys
   
   See `ATTOM_SETUP.md` for ATTOM setup or `API_OPTIONS.md` for other APIs.

## Usage

### Basic Usage

**Find comps by MLS number:**
```bash
python main.py --mls-number "123456"
```

**Find comps by address:**
```bash
python main.py --address "123 Main St" --city "Phoenix" --zip "85001"
```

### Optional: PropertyRadar smoke test
If you’ve enabled PropertyRadar in `.env`, you can verify connectivity and address lookup with:

```bash
python debug_propertyradar.py
```

**Find comps by criteria:**
```bash
python main.py --city "Phoenix" --bedrooms 3 --bathrooms 2 --sqft 1500 --price 300000
```

### Advanced Options

**Get more comps:**
```bash
python main.py --mls-number "123456" --max-comps 20
```

**Output as JSON:**
```bash
python main.py --mls-number "123456" --json
```

**Generate detailed property valuation report:**
```bash
python main.py --address "123 Main St" --city "Phoenix" --zip "85001" --report
```

**Save report to file (text, html, or markdown):**
```bash
python main.py --address "123 Main St" --city "Phoenix" --zip "85001" --save-report text
```

**Provide feedback for learning:**
```bash
python main.py --mls-number "123456" --feedback 0.9
```

**Train the model:**
```bash
python main.py --train
```

## Configuration

Edit `.env` to customize:

- `MIN_COMP_SCORE`: Minimum similarity score (0.0-1.0), default 0.7
- `MAX_COMP_DISTANCE_MILES`: Maximum distance for comps, default 5.0
- `MAX_COMP_AGE_DAYS`: Maximum age of sold comps, default 180
- `ENABLE_LEARNING`: Enable machine learning, default true

## How It Works

1. **Connection**: Connects to your MLS using RETS or RESO Web API
2. **Search**: Searches for candidate properties in the same area
3. **Analysis**: Scores each candidate based on:
   - Distance from subject property
   - Square footage similarity
   - Price similarity
   - Bedroom/bathroom count
   - Year built
   - Property type match
4. **Ranking**: Ranks comps by similarity score
5. **Learning**: Records successful selections and learns from feedback

## Training the Bot

The bot improves over time by learning from your feedback:

1. Use the bot to find comps
2. Review the results
3. Provide feedback: `--feedback 0.9` (0.0 = bad, 1.0 = excellent)
4. Train the model: `python main.py --train`

The bot will adjust its scoring weights based on what you consider good comps.

## MLS Setup

### RETS Setup

Most MLS systems use RETS. You'll need:
- RETS login URL
- Username and password
- User agent string (usually your application name)

### RESO Web API Setup

Modern MLS systems may use RESO Web API. You'll need:
- API endpoint URL
- OAuth2 client ID and secret
- Redirect URI (for authorization flow)

Contact your MLS provider for API access credentials.

## Troubleshooting

**Connection Issues:**
- Verify your credentials in `.env`
- Check that your MLS provider allows API access
- Ensure you have the correct MLS type (RETS vs RESO_WEB_API)

**No Comps Found:**
- Try increasing `MAX_COMP_DISTANCE_MILES`
- Lower `MIN_COMP_SCORE` threshold
- Increase `MAX_COMP_AGE_DAYS` for more historical data

**Field Mapping Issues:**
- MLS systems use different field names
- Edit `mls_connector.py` to map your MLS fields correctly
- Check your MLS documentation for field names

## Example Output

```
================================================================================
COMPARABLE PROPERTY ANALYSIS
================================================================================

Subject Property:
  Address: 123 Main St, Phoenix, AZ 85001
  MLS#: 123456
  Type: Residential
  Bedrooms: 3
  Bathrooms: 2.0
  Square Feet: 1,500
  List Price: $300,000

Found 8 Comparable Properties
Confidence Score: 85.00%

Average Comp Price: $295,000
Average Price per SqFt: $196.67
Estimated Value: $295,005

--------------------------------------------------------------------------------
COMPARABLE PROPERTIES:
--------------------------------------------------------------------------------

1. 456 Oak Ave, Phoenix, AZ 85001
   MLS#: 789012
   Similarity Score: 92%
   Distance: 0.5 miles
   Bedrooms: 3, Bathrooms: 2.0
   Square Feet: 1,520
   Sold Price: $298,500
   Sold Date: 2024-01-15
   Price Difference: $-1,500 (-0.5%)
   Match Reasons: Close proximity (0.50 miles), Similar size (1,520 sqft), Similar price ($298,500), Same bedrooms (3), Same property type (Residential)
...
```

## License

This project is provided as-is for real estate professionals.

## Support

For issues or questions:
1. Check your `.env` configuration
2. Verify MLS API access
3. Review field mappings in `mls_connector.py`
4. Check logs for detailed error messages

