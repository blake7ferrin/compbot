# Property Valuation Report Feature

The bot now generates comprehensive property valuation reports with detailed reasoning, property details, and comparable properties analysis.

## Usage

### Generate and Display Report

```bash
python main.py --address "123 Main St" --city "Phoenix" --zip "85001" --report
```

This will display a full property valuation report in the terminal.

### Save Report to File

**Text Format:**
```bash
python main.py --address "123 Main St" --city "Phoenix" --zip "85001" --save-report text
```

**HTML Format:**
```bash
python main.py --address "123 Main St" --city "Phoenix" --zip "85001" --save-report html
```

**Markdown Format:**
```bash
python main.py --address "123 Main St" --city "Phoenix" --zip "85001" --save-report markdown
```

Reports are saved to the `reports/` directory with automatic filename generation.

## Report Contents

The comprehensive report includes:

### 1. Property Details Section
- Full address and location
- Property type, bedrooms, bathrooms
- Square footage, lot size, year built
- List price and days on market
- Property description
- Coordinates (if available)

### 2. Property Valuation Section
- **Estimated Property Value** - Calculated based on comparable sales
- **Valuation Reasoning** - Detailed explanation including:
  - Comparable sales analysis
  - Similarity factors and match reasons
  - Location analysis (distance from comps)
  - Size analysis (square footage comparisons)
  - Valuation method (price per sqft calculation)
  - Confidence assessment (High/Moderate/Low)
  - Pricing recommendation vs list price

### 3. Market Analysis
- Average comparable sale price
- Average price per square foot
- Comparison to subject property
- Confidence score and data quality

### 4. Comparable Properties List
For each comparable property:
- Full address and location
- Similarity score (0-100%)
- Distance from subject property
- Property details (bedrooms, bathrooms, sqft, year built)
- Sale information (price, date, days on market)
- Price difference from subject
- Price per square foot
- Match reasons (why it was selected as a comp)

## Example Report Structure

```
================================================================================
PROPERTY VALUATION REPORT
================================================================================
Generated: January 15, 2025 at 02:30 PM

================================================================================
PROPERTY DETAILS
================================================================================

Address:        123 Main Street
                Phoenix, AZ 85001
MLS/APN:        123-456-789
Property Type:  Residential
Bedrooms:       3
Bathrooms:      2.0
Square Feet:    1,500
Year Built:     2010
List Price:     $300,000

================================================================================
PROPERTY VALUATION
================================================================================

ESTIMATED PROPERTY VALUE: $295,000

VALUATION REASONING:
--------------------------------------------------------------------------------

1. COMPARABLE SALES ANALYSIS
   Analyzed 8 recently sold properties with similar characteristics:
   - 8 properties with confirmed sale prices
   - Sale price range: $280,000 to $310,000

2. SIMILARITY FACTORS
   Properties were matched based on:
   - Similar size (1,520 sqft) (5 matches)
   - Close proximity (0.50 miles) (8 matches)
   - Similar price ($298,500) (6 matches)
   - Same bedrooms (3) (8 matches)
   - Same property type (Residential) (8 matches)

3. LOCATION ANALYSIS
   - Average distance from subject: 1.2 miles
   - All comps within 3.5 miles

4. SIZE ANALYSIS
   - Average square footage difference: 2.5%

5. VALUATION METHOD
   Primary Method: Price per Square Foot
   - Average comp price per sqft: $196.67
   - Subject square footage: 1,500 sqft
   - Calculation: $196.67 × 1,500 = $295,005

6. CONFIDENCE ASSESSMENT
   Confidence Level: HIGH (85.0%)
   - Strong similarity to comparable properties
   - Recent sales data available
   - Good market representation

7. PRICING RECOMMENDATION
   - Estimated value is 1.7% LOWER than list price
   - Property may be slightly overpriced
   - Review property condition and market factors

================================================================================
COMPARABLE PROPERTIES
================================================================================

Found 8 comparable properties:

COMP #1: 456 Oak Avenue
         Phoenix, AZ 85001

  Similarity Score:     92%
  Distance:             0.5 miles
  Property Type:         Residential
  Bedrooms:             3
  Bathrooms:            2.0
  Square Feet:          1,520
  Year Built:           2012

  Sale Information:
    Sold Price:          $298,500
    Sale Date:           January 15, 2024
    Days on Market:     45
    Price Difference:    $-1,500 (-0.5%)
    Price per SqFt:      $196.38

  Match Reasons:
    • Close proximity (0.50 miles)
    • Similar size (1,520 sqft)
    • Similar price ($298,500)

...
```

## Report File Location

Reports are automatically saved to:
```
mls_comp_bot/reports/property_report_{address}_{timestamp}.{ext}
```

Example:
```
reports/property_report_123_Main_Street_20250115_143022.txt
```

## Tips

1. **Use --report for quick viewing** - See the full report in terminal
2. **Use --save-report for documentation** - Save professional reports for clients
3. **HTML format** - Best for emailing or viewing in browser
4. **Text format** - Best for printing or plain text documents
5. **Markdown format** - Best for documentation or GitHub

## Combining with Other Options

You can combine report generation with other features:

```bash
# Generate report and provide feedback
python main.py --address "123 Main St" --city "Phoenix" --save-report text --feedback 0.9

# Generate report with more comps
python main.py --address "123 Main St" --city "Phoenix" --max-comps 20 --save-report html
```

