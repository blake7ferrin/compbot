"""Quick connection test."""
import os
from dotenv import load_dotenv

load_dotenv()

print("Testing ATTOM Configuration...")
print(f"MLS_TYPE: {os.getenv('MLS_TYPE', 'NOT SET')}")
print(f"ATTOM_API_KEY: {os.getenv('ATTOM_API_KEY', 'NOT SET')[:20]}..." if os.getenv('ATTOM_API_KEY') else "NOT SET")

# Test direct ATTOM API call
import requests

api_key = os.getenv('ATTOM_API_KEY')
if api_key:
    print("\nTesting ATTOM API connection...")
    headers = {
        "apikey": api_key,
        "Accept": "application/json",
    }
    
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/basicprofile"
    params = {"address": "1342 E. Kramer Circle, Mesa, AZ 85203"}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✓ API Connection Successful!")
            if "property" in data and len(data["property"]) > 0:
                prop = data["property"][0]
                address = prop.get("address", {})
                print(f"Property found: {address.get('oneLine', 'N/A')}")
        else:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

