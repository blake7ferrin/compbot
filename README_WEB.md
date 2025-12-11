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

## Local network / remote access

If you want phones or other machines on the same Wi-Fi (or a remote buddy via SSH/ngrok) to hit your Linux-hosted instance:

1. **Create your `.env`**
   ```bash
   cp .env.example .env  # add ATTOM/Oxylabs/etc keys
   ```
2. **Run the helper script** (first time it auto-creates a virtualenv and installs deps):
   ```bash
   ./scripts/run_web_server.sh
   ```
   - Use `PORT=5000 HOST=0.0.0.0 ./scripts/run_web_server.sh` to override defaults.
   - Script exits early if `.env` is missing so API keys never get forgotten.
3. **Find the Linux box IP** (share with anyone on the LAN):
   ```bash
   hostname -I   # grab the 192.168.x.x or 10.x.x.x value
   ```
4. **Visit from another device**
   - Same network: `http://<linux-ip>:5050` (or the port you set).
   - Remote buddy: VPN into the LAN or run `ngrok http 5050` beside the server and share the HTTPS URL.
5. **Control from iOS**
   - Install an SSH client (Termius/Blink), connect to the Linux host, and run the same script/commands.
   - Leave the app running if you want to watch logs; the server keeps running until you `Ctrl+C` it.
6. **Open firewall/port-forward if needed**
   - Linux firewall: `sudo ufw allow 5050/tcp`.
   - Home router: forward external port 5050 → `<linux-ip>:5050` for truly public access (rotate API keys afterwards).

This flow keeps the heavy lifting on Linux while letting you drive everything from iOS.

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
