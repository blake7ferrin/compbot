"""Quick comparison of ATTOM vs Oxylabs - simplified version."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("QUICK DATA SOURCE COMPARISON")
print("=" * 80)
print("Property: 3644 E CONSTITUTION DR, GILBERT, AZ 85296")
print()

# Test ATTOM
print("-" * 80)
print("Testing ATTOM API...")
print("-" * 80)

try:
    from attom_connector import ATTOMConnector
    attom = ATTOMConnector()
    attom.connect()
    attom_prop = attom.get_property_by_address("3644 E CONSTITUTION DR", "GILBERT", "AZ", "85296")
    
    if attom_prop:
        print(f"✓ ATTOM Success")
        print(f"  Bedrooms: {attom_prop.bedrooms}")
        print(f"  Bathrooms: {attom_prop.bathrooms}")
        print(f"  Square Feet: {attom_prop.square_feet}")
        print(f"  Cooling: {attom_prop.cooling_type}")
        print(f"  Roof: {attom_prop.roof_material}")
        print(f"  Amenities: {attom_prop.amenities}")
    else:
        print("✗ ATTOM returned no data")
except Exception as e:
    print(f"✗ ATTOM Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test Oxylabs
print("-" * 80)
print("Testing Oxylabs (Redfin/Zillow scraping)...")
print("-" * 80)

try:
    oxylabs_username = os.getenv("OXYLABS_USERNAME", "")
    oxylabs_password = os.getenv("OXYLABS_PASSWORD", "")
    
    if not oxylabs_username or not oxylabs_password:
        print("⚠️  Oxylabs credentials not configured")
    else:
        from alternative_apis import OxylabsScraperConnector
        oxylabs = OxylabsScraperConnector(oxylabs_username, oxylabs_password)
        oxylabs.connect()
        print("  Calling Oxylabs API (this may take 10-30 seconds)...")
        sys.stdout.flush()
        
        oxylabs_prop = oxylabs.get_property_by_address("3644 E CONSTITUTION DR", "GILBERT", "AZ", "85296")
        
        if oxylabs_prop:
            print(f"✓ Oxylabs Success")
            print(f"  Bedrooms: {oxylabs_prop.bedrooms}")
            print(f"  Bathrooms: {oxylabs_prop.bathrooms}")
            print(f"  Square Feet: {oxylabs_prop.square_feet}")
            print(f"  Lot Size: {oxylabs_prop.lot_size_sqft}")
            print(f"  Year Built: {oxylabs_prop.year_built}")
            print(f"  Amenities: {oxylabs_prop.amenities}")
            print(f"  List Price: {oxylabs_prop.list_price}")
        else:
            print("✗ Oxylabs returned no data")
except Exception as e:
    print(f"✗ Oxylabs Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("Comparison complete!")
print("=" * 80)

