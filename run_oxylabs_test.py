"""Run Oxylabs test and save results to file."""
import os
import sys
import requests
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

output_file = "oxylabs_test_results.txt"

with open(output_file, 'w') as f:
    f.write("=" * 80 + "\n")
    f.write("OXYLABS TEST RESULTS\n")
    f.write(f"Started: {datetime.now()}\n")
    f.write("=" * 80 + "\n\n")
    f.flush()
    
    try:
        # Test 1: Simple URL
        f.write("Test 1: Simple sandbox URL\n")
        f.write("-" * 80 + "\n")
        f.flush()
        
        payload1 = {
            'source': 'universal',
            'url': 'https://sandbox.oxylabs.io/',
        }
        
        start = time.time()
        response1 = requests.post(
            'https://realtime.oxylabs.io/v1/queries',
            auth=(username, password),
            json=payload1,
            timeout=30
        )
        elapsed = time.time() - start
        
        f.write(f"Status: {response1.status_code} (took {elapsed:.1f}s)\n")
        if response1.status_code == 200:
            f.write("✓ SUCCESS\n")
        else:
            f.write(f"✗ FAILED: {response1.text[:200]}\n")
        f.write("\n")
        f.flush()
        
        # Test 2: Redfin URL
        f.write("Test 2: Redfin URL\n")
        f.write("-" * 80 + "\n")
        redfin_url = "https://www.redfin.com/state/AZ/gilbert/3644-e-constitution-dr"
        f.write(f"URL: {redfin_url}\n")
        f.write("Starting request (this may take 30-90 seconds)...\n")
        f.flush()
        
        payload2 = {
            'source': 'universal',
            'url': redfin_url,
            'render': 'html'
        }
        
        start = time.time()
        response2 = requests.post(
            'https://realtime.oxylabs.io/v1/queries',
            auth=(username, password),
            json=payload2,
            timeout=120
        )
        elapsed = time.time() - start
        
        f.write(f"Status: {response2.status_code} (took {elapsed:.1f}s)\n")
        
        if response2.status_code == 200:
            f.write("✓ SUCCESS\n")
            data = response2.json()
            f.write(f"Got {len(data.get('results', []))} result(s)\n")
            
            if data.get('results') and data['results'][0].get('content'):
                content = data['results'][0]['content']
                f.write(f"Content length: {len(content):,} characters\n")
                
                # Save a sample of the content
                f.write("\nFirst 1000 characters:\n")
                f.write("-" * 80 + "\n")
                f.write(content[:1000])
                f.write("\n" + "-" * 80 + "\n")
        else:
            f.write(f"✗ FAILED: {response2.text[:500]}\n")
            
    except requests.exceptions.Timeout:
        f.write("\n✗ TIMEOUT: Request took longer than 120 seconds\n")
    except Exception as e:
        f.write(f"\n✗ ERROR: {e}\n")
        import traceback
        f.write(traceback.format_exc())
    
    f.write("\n" + "=" * 80 + "\n")
    f.write(f"Completed: {datetime.now()}\n")
    f.write("=" * 80 + "\n")

print(f"Test completed! Results saved to: {output_file}")
print("Reading results...")
print()

with open(output_file, 'r') as f:
    print(f.read())

