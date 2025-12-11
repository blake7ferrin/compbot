"""Test different Oxylabs endpoints."""
import requests
from pprint import pprint

username = 'polarair_PwYr0'
password = 'Polar770777$'

payload = {
    'source': 'universal',
    'url': 'https://sandbox.oxylabs.io/',
}

endpoints = [
    'https://realtime.oxylabs.io/v1/queries',
    'https://data.oxylabs.io/v1/queries',
]

for endpoint in endpoints:
    print(f"\n{'='*80}")
    print(f"Testing endpoint: {endpoint}")
    print('='*80)
    
    try:
        response = requests.post(
            endpoint,
            auth=(username, password),
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("SUCCESS!")
            try:
                pprint(response.json())
            except:
                print(f"Response Text: {response.text[:500]}")
        else:
            print(f"FAILED - Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"ERROR: {e}")

print("\n" + "="*80)
print("IMPORTANT: Does the API Playground work for you?")
print("If yes, please copy the EXACT code it generates and share it.")
print("If no, your trial account might need activation.")
print("="*80)

