# Quick Start Guide

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure MLS Connection

Copy the example environment file:
```bash
copy .env.example .env
```

Edit `.env` with your MLS credentials. You'll need to get these from your MLS provider.

### For RETS (Most Common):
```
MLS_TYPE=RETS
RETS_URL=https://your-mls-rets-url.com/rets/login
RETS_USERNAME=your_username
RETS_PASSWORD=your_password
RETS_USER_AGENT=MLSCompBot/1.0
```

### For RESO Web API:
```
MLS_TYPE=RESO_WEB_API
RESO_API_URL=https://api.your-mls.com
RESO_CLIENT_ID=your_client_id
RESO_CLIENT_SECRET=your_client_secret
```

## 3. Test Connection

Try finding comps for a property:

```bash
python main.py --mls-number "YOUR_MLS_NUMBER"
```

Or by address:
```bash
python main.py --address "123 Main St" --city "Your City" --zip "12345"
```

## 4. Common Issues

### "Failed to connect to MLS"
- Double-check your credentials in `.env`
- Verify your MLS provider allows API access
- Contact your MLS for API documentation

### "No comps found"
- Try increasing distance: Edit `.env` and set `MAX_COMP_DISTANCE_MILES=10`
- Lower the minimum score: Set `MIN_COMP_SCORE=0.5`
- Check that there are sold properties in your area

### Field Mapping Errors
Different MLS systems use different field names. You may need to edit `mls_connector.py` to match your MLS fields. Common fields to check:
- `ListingID` vs `MLSNumber` vs `ListingKey`
- `StreetName` vs `UnparsedAddress` vs `StreetAddress`
- `LivingArea` vs `SquareFeet` vs `TotalLivingArea`

## 5. Get Help

Check the main README.md for detailed documentation.

