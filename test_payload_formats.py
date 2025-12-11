"""Test different Oxylabs payload formats to find what works."""
import os
import requests
import time
import json
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"

# Test different formats
tests = [
    {
        "name": "Minimal (just render)",
        "payload": {
            "source": "universal",
            "url": redfin_url,
            "render": "html"
        }
    },
    {
        "name": "With user_agent_type",
        "payload": {
            "source": "universal",
            "url": redfin_url,
            "render": "html",
            "user_agent_type": "desktop"
        }
    },
    {
        "name": "With user_agent_type + geo_location",
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
    }
]

results = []

for i, test in enumerate(tests, 1):
    print(f"\n{'='*80}")
    print(f"Test {i}/{len(tests)}: {test['name']}")
    print('='*80)
    
    try:
        start = time.time()
        response = requests.post(
            'https://realtime.oxylabs.io/v1/queries',
            auth=(username, password),
            json=test['payload'],
            timeout=120
        )
        elapsed = time.time() - start
        
        result = {
            "test": test['name'],
            "status": response.status_code,
            "time": elapsed,
            "success": False,
            "has_captcha": False,
            "has_data": False
        }
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and data['results'][0].get('content'):
                content = data['results'][0]['content']
                result['content_length'] = len(content)
                
                if 'human verification' in content.lower() or 'captcha' in content.lower():
                    result['has_captcha'] = True
                    print(f"Status: 200 (took {elapsed:.1f}s) - Got CAPTCHA page")
                elif 'bedroom' in content.lower()[:10000] or 'bath' in content.lower()[:10000]:
                    result['has_data'] = True
                    result['success'] = True
                    print(f"Status: 200 (took {elapsed:.1f}s) - ✓ SUCCESS! Got property data!")
                else:
                    print(f"Status: 200 (took {elapsed:.1f}s) - Got content but unknown type")
                    print(f"Preview: {content[:200]}")
        elif response.status_code == 400:
            try:
                error = response.json()
                print(f"Status: 400 - Bad Request")
                print(f"Error: {json.dumps(error, indent=2)[:300]}")
            except:
                print(f"Status: 400 - Bad Request")
                print(f"Response: {response.text[:300]}")
        else:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:300]}")
        
        results.append(result)
        
    except Exception as e:
        print(f"Error: {e}")
        results.append({"test": test['name'], "error": str(e)})

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
for r in results:
    if 'error' in r:
        print(f"  {r['test']}: ERROR - {r['error']}")
    elif r.get('success'):
        print(f"  {r['test']}: ✓ SUCCESS - Got property data!")
    elif r.get('has_captcha'):
        print(f"  {r['test']}: ✗ Got CAPTCHA")
    elif r.get('status') == 400:
        print(f"  {r['test']}: ✗ Bad Request (format issue)")
    else:
        print(f"  {r['test']}: Status {r.get('status', 'unknown')}")

# Find the best working format
working = [r for r in results if r.get('success')]
if working:
    print(f"\n✓ Best working format: {working[0]['test']}")
    print("Use this payload format in the connector!")
else:
    print("\n⚠ No format successfully bypassed CAPTCHA")
    print("May need to try different approaches or contact Oxylabs support")

