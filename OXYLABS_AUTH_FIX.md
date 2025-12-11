# Oxylabs Authentication Issue - 401 Unauthorized

## Problem
Getting `401 Client Error: Unauthorized` when calling Oxylabs API.

## Solution

The credentials you're using might be:
1. **Account login credentials** (wrong) - These are for logging into the dashboard
2. **API credentials** (correct) - These are specifically for API calls

## How to Find Your API Credentials

### Option 1: Dashboard → Integration Section
1. Go to Oxylabs Dashboard
2. Navigate to **"Integration with Web Scraper API"** section
3. Look for **"Username"** field - this is your API username
4. For password, you might need to:
   - Click "Change password" to see/reset API password
   - Or use a separate API password (different from account password)

### Option 2: API Playground
1. Go to [API Playground](https://dashboard.oxylabs.io/en/api-playground)
2. The playground might show your API credentials
3. Or test a request there to see what credentials work

### Option 3: Check Documentation
According to Oxylabs docs, you need:
- **Username**: Your API user (might be different from account email)
- **Password**: Your API password (might be different from account password)

## Common Issues

1. **Using account email/password instead of API credentials**
   - Account: `blake@polarservicesaz.com` / `Polar7707$`
   - API: Might be different (check dashboard)

2. **API user not created**
   - You might need to create an API user first
   - Check dashboard for "Create API User" or similar

3. **Trial account limitations**
   - Some trial accounts might have restricted access
   - Check if your trial is active

## Test Authentication

Try this in the API Playground first:
1. Go to https://dashboard.oxylabs.io/en/api-playground
2. Select "Universal" source
3. Enter a test URL
4. See if it works there
5. If it works, the credentials shown there are your API credentials

## Next Steps

1. **Check your dashboard** for API-specific credentials
2. **Test in API Playground** to verify credentials work
3. **Update .env** with the correct API credentials
4. **Re-run the comparison** test

The credentials in your `.env` might be your account login, not your API credentials. Check the dashboard for the actual API username/password.

