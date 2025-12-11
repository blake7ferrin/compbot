"""Check which fallback provided the data by testing each one."""
import os
from dotenv import load_dotenv
from bot import MLSCompBot

load_dotenv()

print("=" * 80)
print("CHECKING WHICH FALLBACK PROVIDED THE DATA")
print("=" * 80)

# Test property
address = "3644 E CONSTITUTION DR"
city = "GILBERT"
state = "AZ"
zip_code = "85296"

print(f"\nTesting property: {address}, {city}, {state} {zip_code}\n")

# Check which services are enabled
from config import settings
print("Service Status:")
print(f"  Estated Enabled: {settings.estated_enabled}")
print(f"  Estated API Key: {'SET' if settings.estated_api_key else 'NOT SET'}")
print(f"  Oxylabs Enabled: {settings.oxylabs_enabled}")
print(f"  Oxylabs Username: {settings.oxylabs_username[:20] + '...' if settings.oxylabs_username else 'NOT SET'}")
print()

# Test Estated if enabled
if settings.estated_enabled and settings.estated_api_key:
    print("Testing Estated API...")
    try:
        from alternative_apis import EstatedAPIConnector
        estated = EstatedAPIConnector(settings.estated_api_key)
        estated.connect()
        estated_prop = estated.get_property_by_address(address, city, state, zip_code)
        
        if estated_prop:
            print("  [SUCCESS] Estated returned data:")
            print(f"    Bedrooms: {estated_prop.bedrooms}")
            print(f"    Bathrooms: {estated_prop.bathrooms}")
            print(f"    Lot Size: {estated_prop.lot_size_sqft}")
            print(f"    Year Built: {estated_prop.year_built}")
            if estated_prop.bedrooms == 3 and estated_prop.bathrooms == 3:
                print("\n  ✓ Estated matches the results! Estated likely provided the data.")
        else:
            print("  [FAILED] Estated returned no data")
    except Exception as e:
        print(f"  [ERROR] Estated failed: {e}")
else:
    print("Estated is not enabled or not configured")

print()

# Test Oxylabs if enabled
if settings.oxylabs_enabled and settings.oxylabs_username and settings.oxylabs_password:
    print("Testing Oxylabs API...")
    print("  (This may take 30-90 seconds - checking if it would work...)")
    print("  Note: We won't wait for the full call, just checking configuration")
    try:
        from alternative_apis import OxylabsScraperConnector
        oxylabs = OxylabsScraperConnector(settings.oxylabs_username, settings.oxylabs_password)
        oxylabs.connect()
        print("  [INFO] Oxylabs connector created and connected")
        print("  [INFO] Oxylabs is configured and would be called if Estated fails")
        print("  [INFO] To test Oxylabs fully, it needs to make the API call (30-90s)")
    except Exception as e:
        print(f"  [ERROR] Oxylabs setup failed: {e}")
else:
    print("Oxylabs is not enabled or not configured")

print("\n" + "=" * 80)
print("CONCLUSION:")
print("=" * 80)
print("Based on the results you showed:")
print("  - Bedrooms: 3")
print("  - Bathrooms: 3")
print("  - Lot Size: 3,825 sqft")
print("  - Year Built: 2002")
print()
print("If Estated returned matching data above, Estated provided it.")
print("If Estated didn't return data, Oxylabs likely provided it.")
print("=" * 80)

