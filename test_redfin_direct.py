"""Direct test of Redfin URL with Oxylabs."""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

print("Testing Redfin URL with Oxylabs...")
print("=" * 80)

# Try the exact URL format from the connector
redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"

print(f"URL: {redfin_url}")
print("Sending request (this may take 30-90 seconds)...")
print()

payload = {
    'source': 'universal',
    'url': redfin_url,
    'render': 'html'
}

try:
    start = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Request started...")
    
    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload,
        timeout=150  # 2.5 minutes - max TTL
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
            
            # Check for property data
            if 'bedroom' in content.lower()[:5000] or 'bath' in content.lower()[:5000]:
                print("✓ Found property data indicators")
            if '3644' in content[:5000] or 'constitution' in content.lower()[:5000]:
                print("✓ Found address in content")
                
            # Show sample
            print("\nSample content (first 800 chars):")
            print("-" * 80)
            print(content[:800])
            print("-" * 80)
    else:
        print(f"✗ FAILED: {response.status_code}")
        print(response.text[:500])
        
except requests.exceptions.Timeout:
    print(f"\n✗ TIMEOUT after 150 seconds")
    print("The request is taking too long. Possible issues:")
    print("  - URL format might be incorrect")
    print("  - Redfin might be blocking the request")
    print("  - Page might not exist")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

