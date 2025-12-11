"""Quick test of Oxylabs to see what's happening."""
import os
import sys
import requests
import time
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

print("Quick Oxylabs Test")
print("=" * 80)

redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"

payload = {
    "source": "universal",
    "url": redfin_url,
    "render": "html",
    "user_agent_type": "desktop",
    "geo_location": "United States",
    "locale": "en_US"
}

print(f"URL: {redfin_url}")
print("Sending request (max 2 minutes)...")
print()

try:
    start = time.time()
    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload,
        timeout=120
    )
    
    elapsed = time.time() - start
    print(f"Response received! (took {elapsed:.1f}s)")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('results') and data['results'][0].get('content'):
            content = data['results'][0]['content']
            print(f"Content length: {len(content):,} chars")
            
            if 'human verification' in content.lower() or 'captcha' in content.lower():
                print("\n[RESULT] Still getting CAPTCHA/verification page")
                print("Anti-bot settings didn't bypass Redfin's protection")
            elif 'bedroom' in content.lower()[:10000] or 'bath' in content.lower()[:10000]:
                print("\n[RESULT] SUCCESS! Found property data!")
                print("Anti-bot settings worked!")
            else:
                print("\n[RESULT] Got content but checking...")
                print(f"Preview: {content[:400]}")
    else:
        print(f"[RESULT] Failed: {response.status_code}")
        print(response.text[:500])
        
except requests.exceptions.Timeout:
    print(f"\n[RESULT] TIMEOUT after 120 seconds")
    print("The request is taking too long")
except Exception as e:
    print(f"\n[RESULT] ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

