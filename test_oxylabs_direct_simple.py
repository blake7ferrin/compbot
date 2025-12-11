"""Direct simple test of Oxylabs to see what happens."""
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

redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"

payload = {
    "source": "universal",
    "url": redfin_url,
    "render": "html",
    "user_agent_type": "desktop",
    "geo_location": "United States",
    "locale": "en_US"
}

print(f"Testing URL: {redfin_url}")
print("Payload:", payload)
print("\nSending request (this will take 30-90 seconds)...")
print("Please wait - DO NOT CANCEL!")
sys.stdout.flush()

try:
    start = time.time()
    print(f"\n[{time.strftime('%H:%M:%S')}] Starting request...")
    sys.stdout.flush()
    
    response = requests.post(
        'https://realtime.oxylabs.io/v1/queries',
        auth=(username, password),
        json=payload,
        timeout=120
    )
    
    elapsed = time.time() - start
    print(f"[{time.strftime('%H:%M:%S')}] Response received! (took {elapsed:.1f}s)")
    print(f"Status Code: {response.status_code}")
    sys.stdout.flush()
    
    if response.status_code == 200:
        print("\n[SUCCESS] Got 200 response!")
        data = response.json()
        print(f"Results count: {len(data.get('results', []))}")
        
        if data.get('results') and data['results'][0].get('content'):
            content = data['results'][0]['content']
            print(f"Content length: {len(content):,} characters")
            
            # Check for CAPTCHA
            if 'human verification' in content.lower()[:5000] or 'captcha' in content.lower()[:5000]:
                print("\n[RESULT] Still getting CAPTCHA/verification page")
                print("Anti-bot settings did NOT bypass Redfin's protection")
                print("\nFirst 500 chars:")
                print("-" * 80)
                print(content[:500])
            elif 'bedroom' in content.lower()[:10000] or 'bath' in content.lower()[:10000]:
                print("\n[RESULT] SUCCESS! Found property data!")
                print("Anti-bot settings WORKED!")
                # Try to find some data
                if 'bedroom' in content.lower():
                    print("Found 'bedroom' in content")
                if 'bath' in content.lower():
                    print("Found 'bath' in content")
            else:
                print("\n[RESULT] Got content but unknown type")
                print("First 800 chars:")
                print("-" * 80)
                print(content[:800])
                print("-" * 80)
        else:
            print("\n[RESULT] No content in results")
            print(f"Full response: {data}")
    elif response.status_code == 400:
        print(f"\n[ERROR] Bad Request (400)")
        try:
            error_data = response.json()
            print(f"Error details: {error_data}")
        except:
            print(f"Response: {response.text[:500]}")
    else:
        print(f"\n[ERROR] Status {response.status_code}")
        print(response.text[:500])
        
except requests.exceptions.Timeout:
    print(f"\n[ERROR] TIMEOUT after 120 seconds")
    print("The request took too long - may be stuck or Redfin is blocking")
except KeyboardInterrupt:
    print("\n\n[INTERRUPTED] Test was canceled")
except Exception as e:
    print(f"\n[ERROR] Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test complete!")
print("=" * 80)

