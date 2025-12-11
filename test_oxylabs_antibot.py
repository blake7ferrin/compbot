"""Test Oxylabs with anti-bot settings."""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

print("Testing Oxylabs with Anti-Bot Settings")
print("=" * 80)

redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"

# Payload with anti-bot settings
payload = {
    "source": "universal",
    "url": redfin_url,
    "render": "html",
    # Anti-bot settings
    "user_agent_type": "desktop",
    "geo_location": "United States",
    "locale": "en_US",
    "browser_instructions": [
        {
            "type": "wait",
            "wait_time": 3
        },
        {
            "type": "wait_for",
            "selector": "body"
        }
    ]
}

print(f"URL: {redfin_url}")
print("\nAnti-bot settings:")
print("  - user_agent_type: desktop")
print("  - geo_location: United States")
print("  - locale: en_US")
print("  - browser_instructions: wait 3s, wait for body")
print("\nSending request (this may take 30-90 seconds)...")
print()

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
            
            # Check for blocking
            if 'human verification' in content.lower() or 'captcha' in content.lower():
                print("✗ Still getting CAPTCHA/verification page")
                print("  May need additional anti-bot settings")
            elif 'bedroom' in content.lower()[:10000] or 'bath' in content.lower()[:10000]:
                print("✓ Found property data! Anti-bot settings worked!")
            elif 'redfin' in content.lower()[:5000] and 'property' in content.lower()[:5000]:
                print("✓ Got Redfin property page! Anti-bot settings worked!")
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

