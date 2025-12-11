"""Test with exact code from Oxylabs playground."""
import requests
from pprint import pprint
import sys

print("Starting test...", flush=True)
sys.stdout.flush()

# Structure payload.
payload = {
    'source': 'universal',
    'url': 'https://sandbox.oxylabs.io/',
    # 'render': 'html', # If page type requires
}

# Get response.
response = requests.request(
    'POST',
    'https://realtime.oxylabs.io/v1/queries',
    # Your credentials go here
    auth=('polarair_PwYr0', 'Polar770777$'),
    json=payload,
)

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")
print()

# Instead of response with job status and results url,
# this will return the JSON response with results.
if response.status_code == 200:
    print("SUCCESS!")
    pprint(response.json())
else:
    print("FAILED")
    print(f"Status: {response.status_code}")
    print(f"Response Text: {response.text}")
    print(f"Response Headers: {dict(response.headers)}")

