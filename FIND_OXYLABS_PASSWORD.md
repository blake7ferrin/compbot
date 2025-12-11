# How to Find Your Oxylabs API Password

## The Problem
- ✅ Username is correct: `polarair_PwYr0` (from API Playground)
- ❌ Password is wrong: Getting 401 Unauthorized

## Solution: Find Your API Password

The API password is **different** from your account login password. Here's how to find it:

### Method 1: API Playground (Easiest)

1. Go to [API Playground](https://dashboard.oxylabs.io/en/api-playground)
2. Look at the **code snippet** it generates (Python, cURL, etc.)
3. The code will show your credentials in the format:
   ```python
   auth = ('polarair_PwYr0', 'YOUR_API_PASSWORD_HERE')
   ```
   or
   ```bash
   --user "polarair_PwYr0:YOUR_API_PASSWORD_HERE"
   ```
4. **Copy that password** - that's your API password!

### Method 2: Dashboard → API Users

1. Log into [Oxylabs Dashboard](https://dashboard.oxylabs.io/)
2. Go to **Settings** or **API Users** section
3. Find your API user: `polarair_PwYr0`
4. You should see:
   - Option to **"View Password"** (if it's visible)
   - Option to **"Reset Password"** (to generate a new one)
   - Option to **"Change Password"** (to set a new one)

### Method 3: Test in Playground First

1. In the API Playground, make a test request
2. If it works there, the playground is using the correct password
3. Check the browser's Network tab (F12 → Network) to see the actual request
4. Look for the Authorization header - it will show the password (base64 encoded)

### Method 4: Generate New API Password

If you can't find the password:

1. Go to Dashboard → API Users
2. Find `polarair_PwYr0`
3. Click **"Reset Password"** or **"Change Password"**
4. Generate a new password
5. **Save it immediately** - you might not be able to see it again
6. Update your `.env` file with the new password

## Update Your .env File

Once you have the correct password:

```env
OXYLABS_USERNAME=polarair_PwYr0
OXYLABS_PASSWORD=your_actual_api_password_here
OXYLABS_ENABLED=true
```

## Test It

After updating, run:
```bash
python test_oxylabs_auth.py
```

You should see:
```
✓ SUCCESS! Authentication works
```

## Common Issues

1. **Using account password instead of API password**
   - Account password: `Polar7707$` (for logging into dashboard)
   - API password: Different (for API calls)

2. **Password not set for API user**
   - You might need to set/reset the password for the API user first

3. **Trial account limitations**
   - Some trial accounts might need activation
   - Check if your trial is active and has API access enabled

## Quick Check

The easiest way is to:
1. Open API Playground
2. Make a test request (it should work there)
3. Copy the code snippet it generates
4. Extract the password from that code
5. Use that password in your `.env` file

