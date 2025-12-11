# How to Use Oxylabs API Playground

## Overview

The [Oxylabs API Playground](https://dashboard.oxylabs.io/en/api-playground) is a great way to test your API requests before integrating them into your code.

## Step-by-Step Guide

### 1. Select Website and Scraper

1. **Select the website** you wish to scrape:
   - If the specific website (Redfin, Zillow) isn't listed, select **"Other"**
   - For property data, we use **"Other"** since Redfin/Zillow aren't in the preset list

2. **Pick the appropriate scraper**:
   - For property pages, use **"Universal"** scraper
   - This works for most websites including Redfin and Zillow

### 2. Form and Send Request

**Basic Settings:**
- **Source**: Select `universal` (or "Other" → "Universal")
- **URL**: Enter the target property URL
  - Example Redfin: `https://www.redfin.com/AZ/Gilbert/3644-E-Constitution-Dr-85296/home/12345678`
  - Example Zillow: `https://www.zillow.com/homedetails/3644-E-Constitution-Dr-Gilbert-AZ-85296/12345678_zpid/`

**Important Options:**
- **render**: Set to `html` (JavaScript rendering enabled)
  - This ensures the page is fully loaded before scraping
  - Essential for dynamic content like property listings

**Optional Advanced Settings:**
- **user_agent_type**: Can set to `desktop` or `mobile`
- **geo_location**: Set location if needed (e.g., `United States`)
- **locale**: Set language/locale (e.g., `en_US`)

### 3. Review and Export

1. Click **"Submit Request"** button
2. Wait for the API to process (usually 10-30 seconds)
3. Review results in the **"Output Preview"** tab:
   - Shows the HTML output
   - Can preview as rendered HTML or PNG screenshot
4. **Export** the data:
   - Click export button (upper right)
   - Choose JSON or HTML format
   - Use this to see what data is available

### 4. Get Hands-On

1. **Copy the input code** in your preferred programming language:
   - Python, cURL, Node.js, etc.
   - The code includes your API credentials automatically
2. **Test via terminal**:
   - Copy the code snippet
   - Run it in your terminal
   - Verify it works before integrating

## Your API Credentials

From the playground, I can see:
- **Username**: `polarair_PwYr0`
- **Password**: (Your API password - check if it's different from account password)

## Testing a Property URL

### Example Request for Redfin:

```json
{
  "source": "universal",
  "url": "https://www.redfin.com/AZ/Gilbert/3644-E-Constitution-Dr-85296/home/12345678",
  "render": "html"
}
```

### Example Request for Zillow:

```json
{
  "source": "universal",
  "url": "https://www.zillow.com/homedetails/3644-E-Constitution-Dr-Gilbert-AZ-85296/12345678_zpid/",
  "render": "html"
}
```

## Tips

1. **Always use `render: "html"`** for property pages - they're JavaScript-heavy
2. **Test with a known property URL** first to verify it works
3. **Check the HTML output** to see what data is available
4. **Use the export feature** to download and inspect the full HTML
5. **Copy the working code** from the playground to use in your integration

## Common Issues

1. **Empty results**: Make sure `render: "html"` is enabled
2. **Timeout**: Some pages take longer - be patient
3. **Blocked**: If you get blocked, try different `user_agent_type` or add delays
4. **Wrong data**: Verify the URL is correct and the property page exists

## Next Steps

Once you've tested in the playground:
1. Verify your credentials work
2. See what data is available in the HTML
3. Update the parser in `alternative_apis.py` to extract that data
4. Test the full integration

