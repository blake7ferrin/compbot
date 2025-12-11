"""Test Oxylabs with verbose output."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("OXYLABS VERBOSE TEST")
print("=" * 80)

try:
    oxylabs_username = os.getenv("OXYLABS_USERNAME", "")
    oxylabs_password = os.getenv("OXYLABS_PASSWORD", "")
    
    print(f"Username: {oxylabs_username}")
    print(f"Password: {'*' * len(oxylabs_password) if oxylabs_password else 'NOT SET'}")
    print()
    
    if not oxylabs_username or not oxylabs_password:
        print("ERROR: Oxylabs credentials not configured")
        sys.exit(1)
    
    from alternative_apis import OxylabsScraperConnector
    
    print("Step 1: Creating connector...")
    sys.stdout.flush()
    oxylabs = OxylabsScraperConnector(oxylabs_username, oxylabs_password)
    
    print("Step 2: Connecting...")
    sys.stdout.flush()
    oxylabs.connect()
    
    print("Step 3: Calling get_property_by_address...")
    print("  Address: 3644 E CONSTITUTION DR, GILBERT, AZ 85296")
    print("  This may take 30-60 seconds...")
    sys.stdout.flush()
    
    oxylabs_prop = oxylabs.get_property_by_address("3644 E CONSTITUTION DR", "GILBERT", "AZ", "85296")
    
    print()
    print("Step 4: Results:")
    print("-" * 80)
    
    if oxylabs_prop:
        print("SUCCESS! Got property data:")
        print(f"  Bedrooms: {oxylabs_prop.bedrooms}")
        print(f"  Bathrooms: {oxylabs_prop.bathrooms}")
        print(f"  Square Feet: {oxylabs_prop.square_feet}")
        print(f"  Lot Size: {oxylabs_prop.lot_size_sqft}")
        print(f"  Year Built: {oxylabs_prop.year_built}")
        print(f"  Cooling: {oxylabs_prop.cooling_type}")
        print(f"  Roof: {oxylabs_prop.roof_material}")
        print(f"  Amenities: {oxylabs_prop.amenities}")
        print(f"  List Price: {oxylabs_prop.list_price}")
    else:
        print("FAILED: No property data returned")
        
except KeyboardInterrupt:
    print("\n\nInterrupted by user")
    sys.exit(1)
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("Test complete!")
print("=" * 80)

