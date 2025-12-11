"""Final test of anti-bot settings with simplified format."""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

print("=" * 80)
print("FINAL ANTI-BOT SETTINGS TEST")
print("=" * 80)

redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"

# Simplified payload (removed browser_instructions that caused 400 error)
payload = {
    "source": "universal",
    "url": redfin_url,
    "render": "html",
    "user_agent_type": "desktop",
    "geo_location": "United States",
    "locale": "en_US"
}

print(f"URL: {redfin_url}")
print("\nAnti-bot settings:")
print("  - user_agent_type: desktop")
print("  - geo_location: United States")
print("  - locale: en_US")
print("  - (browser_instructions removed - was causing 400 error)")
print("\nSending request (30-90 seconds)...")
print()

try:
    start = time.time()
    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload,
        timeout=150
    )
    
    elapsed = time.time() - start
    print(f"Response received! (took {elapsed:.1f}s)")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ SUCCESS!")
        data = response.json()
        if data.get('results') and data['results'][0].get('content'):
            content = data['results'][0]['content']
            print(f"Content length: {len(content):,} chars")
            
            if 'human verification' in content.lower() or 'captcha' in content.lower():
                print("✗ Still getting CAPTCHA/verification")
                print("  May need Oxylabs Web Unblocker or different approach")
            elif 'bedroom' in content.lower()[:10000] or 'bath' in content.lower()[:10000]:
                print("✓✓✓ FOUND PROPERTY DATA! Anti-bot settings worked!")
                print("\nSample (first 500 chars):")
                print("-" * 80)
                print(content[:500])
            else:
                print("⚠ Got content but checking type...")
                print(f"Preview: {content[:300]}")
    elif response.status_code == 400:
        print("✗ Bad Request - payload format issue")
        print(response.text[:500])
    else:
        print(f"✗ Failed: {response.status_code}")
        print(response.text[:300])
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

