# Google Maps API Setup for Street View

## Quick Setup

1. **Get a Google Maps API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable "Street View Static API"
   - Create credentials (API Key)
   - Restrict the key to "Street View Static API" for security

2. **Add to .env file:**
   ```
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

3. **Free Tier:**
   - $200/month credit
   - ~28,000 Street View requests/month
   - More than enough for personal use

## What You Get

- **Street View Images:** Embedded property photos
- **Interactive Links:** Click to view in Google Maps
- **Automatic:** Generated for all properties with coordinates

## Usage

The bot automatically generates Street View URLs for all properties. No additional code needed!

## Security Note

Always restrict your API key to specific APIs in Google Cloud Console to prevent unauthorized use.
