"""Test anti-bot settings and save results."""
import os
import requests
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

output_file = "antibot_test_results.txt"

with open(output_file, 'w') as f:
    f.write("=" * 80 + "\n")
    f.write("OXYLABS ANTI-BOT SETTINGS TEST\n")
    f.write(f"Started: {datetime.now()}\n")
    f.write("=" * 80 + "\n\n")
    f.flush()
    
    redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"
    
    payload = {
        "source": "universal",
        "url": redfin_url,
        "render": "html",
        "user_agent_type": "desktop",
        "geo_location": "United States",
        "locale": "en_US",
        "browser_instructions": [
            {"type": "wait", "wait_time": 3},
            {"type": "wait_for", "selector": "body"}
        ]
    }
    
    f.write(f"URL: {redfin_url}\n")
    f.write("\nAnti-bot settings:\n")
    f.write(f"  - user_agent_type: desktop\n")
    f.write(f"  - geo_location: United States\n")
    f.write(f"  - locale: en_US\n")
    f.write(f"  - browser_instructions: wait 3s, wait for body\n")
    f.write("\nSending request...\n")
    f.flush()
    
    try:
        start = time.time()
        f.write(f"[{time.strftime('%H:%M:%S')}] Request started...\n")
        f.flush()
        
        response = requests.post(
            'https://realtime.oxylabs.io/v1/queries',
            auth=(username, password),
            json=payload,
            timeout=150
        )
        
        elapsed = time.time() - start
        f.write(f"[{time.strftime('%H:%M:%S')}] Response received! (took {elapsed:.1f}s)\n")
        f.write(f"Status: {response.status_code}\n")
        f.flush()
        
        if response.status_code == 200:
            f.write("✓ SUCCESS!\n")
            data = response.json()
            f.write(f"Results: {len(data.get('results', []))}\n")
            
            if data.get('results') and data['results'][0].get('content'):
                content = data['results'][0]['content']
                f.write(f"Content length: {len(content):,} chars\n")
                
                # Check for blocking
                if 'human verification' in content.lower() or 'captcha' in content.lower():
                    f.write("✗ Still getting CAPTCHA/verification page\n")
                elif 'bedroom' in content.lower()[:10000] or 'bath' in content.lower()[:10000]:
                    f.write("✓ Found property data! Anti-bot settings worked!\n")
                elif 'redfin' in content.lower()[:5000] and 'property' in content.lower()[:5000]:
                    f.write("✓ Got Redfin property page! Anti-bot settings worked!\n")
                else:
                    f.write("⚠ Unknown content type\n")
                    
                f.write("\nFirst 1500 chars:\n")
                f.write("-" * 80 + "\n")
                f.write(content[:1500])
                f.write("\n" + "-" * 80 + "\n")
        else:
            f.write(f"✗ FAILED: {response.status_code}\n")
            f.write(response.text[:500] + "\n")
            
    except Exception as e:
        f.write(f"\n✗ ERROR: {e}\n")
        import traceback
        f.write(traceback.format_exc())
    
    f.write("\n" + "=" * 80 + "\n")
    f.write(f"Completed: {datetime.now()}\n")
    f.write("=" * 80 + "\n")

print(f"Test completed! Results saved to: {output_file}")
print("Reading results...\n")

if os.path.exists(output_file):
    with open(output_file, 'r') as f:
        print(f.read())

