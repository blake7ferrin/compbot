"""Test anti-bot settings with corrected format."""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

print("Testing Oxylabs with Anti-Bot Settings (Fixed Format)")
print("=" * 80)

redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"

# Try different payload formats
payloads_to_test = [
    {
        "name": "Basic with user agent and geo",
        "payload": {
            "source": "universal",
            "url": redfin_url,
            "render": "html",
            "user_agent_type": "desktop",
            "geo_location": "United States"
        }
    },
    {
        "name": "With locale",
        "payload": {
            "source": "universal",
            "url": redfin_url,
            "render": "html",
            "user_agent_type": "desktop",
            "geo_location": "United States",
            "locale": "en_US"
        }
    },
    {
        "name": "With wait instruction (simplified)",
        "payload": {
            "source": "universal",
            "url": redfin_url,
            "render": "html",
            "user_agent_type": "desktop",
            "geo_location": "United States",
            "browser_instructions": {
                "wait": 3000  # Wait 3 seconds in milliseconds
            }
        }
    }
]

for test in payloads_to_test:
    print(f"\n{'='*80}")
    print(f"Test: {test['name']}")
    print('='*80)
    print(f"URL: {redfin_url}")
    print("Payload keys:", list(test['payload'].keys()))
    print("Sending request...")
    
    try:
        start = time.time()
        response = requests.post(
            'https://realtime.oxylabs.io/v1/queries',
            auth=(username, password),
            json=test['payload'],
            timeout=120
        )
        
        elapsed = time.time() - start
        print(f"Status: {response.status_code} (took {elapsed:.1f}s)")
        
        if response.status_code == 200:
            print("✓ SUCCESS!")
            data = response.json()
            if data.get('results') and data['results'][0].get('content'):
                content = data['results'][0]['content']
                print(f"Content length: {len(content):,} chars")
                
                if 'human verification' in content.lower() or 'captcha' in content.lower():
                    print("✗ Still getting CAPTCHA")
                elif 'bedroom' in content.lower()[:10000] or 'bath' in content.lower()[:10000]:
                    print("✓ Found property data! This format works!")
                    break
                else:
                    print("⚠ Got content but unknown type")
                    print(f"Preview: {content[:300]}")
        elif response.status_code == 400:
            print(f"✗ Bad Request - payload format issue")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Response: {response.text[:500]}")
        else:
            print(f"✗ Failed: {response.status_code}")
            print(response.text[:300])
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print()

print("\n" + "=" * 80)
print("Testing complete!")
print("=" * 80)

