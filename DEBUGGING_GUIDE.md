# Debugging Guide - Missing Data Issue

## Quick Checks

### 1. Restart Flask App
**IMPORTANT**: After code changes, you MUST restart the Flask app:
- Stop the Flask app (Ctrl+C in the terminal where it's running)
- Restart it: `python app.py` or use `run_web.bat`

### 2. Check Browser Console
After running a search:
1. Press **F12** to open Developer Tools
2. Go to the **Console** tab
3. Look for these debug messages:
   - "Received data:"
   - "Subject property:"
   - "Subject lot_size_sqft:"
   - "Subject total_rooms:"
   - "Subject parking_spaces:"
   - "Subject heating_type:"
   - "Subject cooling_type:"

These will show what data the frontend is receiving.

### 3. Check Flask Terminal Output
Look for these log messages in the Flask terminal:
- "Extracting subject property from v2 response..."
- "Successfully extracted v2 subject: ..."
- "Enhancing subject property with v2 response data"
- "v2 subject extracted: rooms=..., lot_sqft=..., parking=..."
- "Final enhanced subject: rooms=..., lot_sqft=..., parking=..."
- "Subject property data - lot_sqft=..., rooms=..., parking=..."

### 4. Test Extraction Directly
Visit this URL in your browser (while Flask is running):
```
http://localhost:5000/test-extraction
```

This will show you:
- Raw data from ATTOM response
- Parsed data after extraction
- Whether extraction is working correctly

### 5. Check Log File
Look for `flask_app.log` in the project directory - it should contain all the log messages.

## What the Data Should Show

Based on the current `attom_response_debug.json`, you should see:
- **Lot Size**: 3,825 sqft (0.09 acres)
- **Total Rooms**: 7
- **Stories**: 2
- **Parking**: 2 spaces
- **Heating**: YES
- **Cooling**: REFRIGERATOR (this is what ATTOM returned)
- **Amenities**: Fireplace

## If Data is Still Missing

1. **Check if v2 extraction is happening**: Look for "Extracting subject property from v2 response" in logs
2. **Check if enhancement is happening**: Look for "Enhancing subject property with v2 response data" in logs
3. **Check browser console**: See what data the frontend actually receives
4. **Check the test endpoint**: Visit `/test-extraction` to see if parsing works
