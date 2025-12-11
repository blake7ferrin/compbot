"""Direct test of Zillow URL with Oxylabs."""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

print("Testing Zillow URL with Oxylabs...")
print("=" * 80)

# Try Zillow search URL
from urllib.parse import quote
query = "3644 E CONSTITUTION DR, GILBERT, AZ 85296"
zillow_url = f"https://www.zillow.com/homes/{quote(query)}_rb/"

print(f"URL: {zillow_url}")
print("Sending request (this may take 30-90 seconds)...")
print()

payload = {
    'source': 'universal',
    'url': zillow_url,
    'render': 'html'
}

try:
    start = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Request started...")
    
    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload,
        timeout=150
    )
    
    elapsed = time.time() - start
    print(f"[{time.strftime('%H:%M:%S')}] Response received! (took {elapsed:.1f}s)")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ SUCCESS!")
        data = response.json()
        print(f"Results: {len(data.get('results', []))}")
        
        if data.get('results') and data['results'][0].get('content'):
            content = data['results'][0]['content']
            print(f"Content length: {len(content):,} chars")
            
            # Check for property data or blocking
            if 'human verification' in content.lower() or 'captcha' in content.lower():
                print("⚠ Got CAPTCHA/verification page")
            elif 'bedroom' in content.lower()[:10000] or 'bath' in content.lower()[:10000]:
                print("✓ Found property data indicators")
            elif 'zillow' in content.lower()[:5000]:
                print("✓ Got Zillow page")
            else:
                print("⚠ Unknown content type")
                
            # Show sample
            print("\nSample content (first 1000 chars):")
            print("-" * 80)
            print(content[:1000])
            print("-" * 80)
    else:
        print(f"✗ FAILED: {response.status_code}")
        print(response.text[:500])
        
except requests.exceptions.Timeout:
    print(f"\n✗ TIMEOUT after 150 seconds")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

