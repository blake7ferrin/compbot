"""Test Oxylabs with explicit timeout and progress updates."""
import os
import sys
import requests
import time
import signal
from dotenv import load_dotenv

load_dotenv()

# Handle timeout gracefully
def timeout_handler(signum, frame):
    raise TimeoutError("Request timed out")

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

print("=" * 80)
print("OXYLABS TEST WITH PROGRESS UPDATES")
print("=" * 80)
print(f"Username: {username}")
print()

# Test Redfin URL
redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"
payload = {
    'source': 'universal',
    'url': redfin_url,
    'render': 'html'
}

print(f"URL: {redfin_url}")
print("Starting request...")
print("(This may take 30-90 seconds - please be patient)")
print()
sys.stdout.flush()

try:
    start_time = time.time()
    
    # Make the request with a long timeout
    print("Sending request to Oxylabs API...")
    sys.stdout.flush()
    
    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload,
        timeout=120,  # 2 minute timeout
        stream=False  # Don't stream, wait for full response
    )
    
    elapsed = time.time() - start_time
    print(f"\nResponse received! (took {elapsed:.1f} seconds)")
    print(f"Status Code: {response.status_code}")
    sys.stdout.flush()
    
    if response.status_code == 200:
        print("✓ SUCCESS!")
        data = response.json()
        print(f"Got {len(data.get('results', []))} result(s)")
        
        if data.get('results') and data['results'][0].get('content'):
            content = data['results'][0]['content']
            print(f"Content length: {len(content):,} characters")
            
            # Check if we got HTML
            if '<html' in content.lower()[:1000] or '<body' in content.lower()[:1000]:
                print("✓ Got HTML content")
                # Look for property data indicators
                if 'bedroom' in content.lower() or 'bath' in content.lower():
                    print("✓ Content appears to contain property data")
                print(f"\nFirst 500 chars of HTML:")
                print("-" * 80)
                print(content[:500])
                print("-" * 80)
            else:
                print("⚠ Content doesn't look like HTML")
                print(f"Content preview: {content[:500]}")
        else:
            print("⚠ No content in results")
            print(f"Full response: {data}")
    else:
        print(f"✗ FAILED: Status {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("\n✗ TIMEOUT: Request took longer than 120 seconds")
    print("This might mean:")
    print("  - The URL is incorrect or the page doesn't exist")
    print("  - Redfin is blocking the request")
    print("  - The page is taking too long to load")
except KeyboardInterrupt:
    print("\n\n⚠ INTERRUPTED by user")
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("Test complete!")
print("=" * 80)

