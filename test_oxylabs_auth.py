"""Test Oxylabs authentication with different methods."""
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("OXYLABS_USERNAME", "")
password = os.getenv("OXYLABS_PASSWORD", "")

print("=" * 80)
print("OXYLABS AUTHENTICATION TEST")
print("=" * 80)
print(f"Username: {username}")
print(f"Password: {'*' * len(password) if password else 'NOT SET'}")
print()

base_url = "https://realtime.oxylabs.io/v1/queries"

# Test payload
test_payload = {
    "source": "universal",
    "url": "https://httpbin.org/get",  # Simple test URL
    "render": "html"
}

print("Testing Method 1: HTTP Basic Auth (requests.auth)")
print("-" * 80)
try:
    response = requests.post(
        base_url,
        auth=(username, password),
        json=test_payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ SUCCESS! Authentication works with HTTP Basic Auth")
        print(f"Response preview: {response.text[:200]}...")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"✗ Error: {e}")

print()
print("Testing Method 2: Authorization Header (Basic)")
print("-" * 80)
try:
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    
    response = requests.post(
        base_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {encoded}"
        },
        json=test_payload,
        timeout=30
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ SUCCESS! Authentication works with Authorization header")
        print(f"Response preview: {response.text[:200]}...")
    else:
        print(f"✗ Failed: {response.status_code}")
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"✗ Error: {e}")

print()
print("=" * 80)
print("If both methods fail with 401:")
print("1. Check if your API password is different from account password")
print("2. Go to Oxylabs Dashboard → Settings → API Users")
print("3. Reset or view your API password")
print("4. Update OXYLABS_PASSWORD in .env file")
print("=" * 80)

