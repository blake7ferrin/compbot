# MLS Comp Bot - Web Interface

A simple web interface for the MLS Comp Bot that allows you to search for comparable properties through a browser.

## Setup

1. **Install Flask** (if not already installed):
   ```powershell
   pip install flask
   ```
   
   Or install all requirements:
   ```powershell
   pip install -r requirements.txt
   ```

2. **Start the web server**:
   ```powershell
   python app.py
   ```
   
   Or use the batch file:
   ```powershell
   .\run_web.bat
   ```

3. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

1. Fill out the form with:
   - **Street Address** (required)
   - **City** (required)
   - **State** (required) - select from dropdown
   - **ZIP Code** (optional)
   - **Maximum Comparables** (default: 10)

2. Click **"Find Comparables"**

3. View the results showing:
   - Subject property details
   - Statistics (confidence score, average price, estimated value)
   - List of comparable properties with similarity scores

## Features

- Clean, modern web interface
- Real-time search with loading indicators
- Detailed property information
- Similarity scores and match reasons
- Price analysis and estimates
- Responsive design (works on mobile)

## Troubleshooting

- **Port 5000 already in use**: Change the port in `app.py` (line with `app.run()`)
- **Connection errors**: Make sure your ATTOM API key is set in the `.env` file
- **No results**: Try adjusting search criteria or using a different address
