"""Simple test of Oxylabs with a known working URL first."""
import os
import sys
import requests
import time
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

print("=" * 80)
print("SIMPLE OXYLABS TEST")
print("=" * 80)
print(f"Username: {username}")
print()

# Test 1: Simple sandbox URL (should work quickly)
print("Test 1: Simple sandbox URL (should be fast)...")
payload1 = {
    'source': 'universal',
    'url': 'https://sandbox.oxylabs.io/',
}

try:
    start = time.time()
    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload1,
        timeout=60
    )
    elapsed = time.time() - start
    print(f"  Status: {response.status_code} (took {elapsed:.1f}s)")
    if response.status_code == 200:
        data = response.json()
        print(f"  Success! Got {len(data.get('results', []))} result(s)")
    else:
        print(f"  Error: {response.text[:200]}")
except Exception as e:
    print(f"  Exception: {e}")

print()

# Test 2: Redfin URL (will be slower)
print("Test 2: Redfin URL (will be slower, 30-60s)...")
redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"
payload2 = {
    'source': 'universal',
    'url': redfin_url,
    'render': 'html'
}

print(f"  URL: {redfin_url}")
print("  Starting request (this may take 30-60 seconds)...")
print("  Please wait - DO NOT CANCEL!")
sys.stdout.flush()

try:
    start = time.time()
    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload2,
        timeout=120  # 2 minutes
    )
    elapsed = time.time() - start
    print(f"  Status: {response.status_code} (took {elapsed:.1f}s)")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  Success! Got {len(data.get('results', []))} result(s)")
        if data.get('results') and data['results'][0].get('content'):
            content = data['results'][0]['content']
            print(f"  Content length: {len(content)} characters")
            # Check if it looks like HTML
            if '<html' in content.lower()[:500]:
                print("  ✓ Got HTML content")
            else:
                print(f"  Content preview: {content[:200]}")
    else:
        print(f"  Error: {response.text[:500]}")
except requests.exceptions.Timeout:
    print("  TIMEOUT: Request took longer than 120 seconds")
except KeyboardInterrupt:
    print("\n  INTERRUPTED by user")
except Exception as e:
    print(f"  Exception: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)

