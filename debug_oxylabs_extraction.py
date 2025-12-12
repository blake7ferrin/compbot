"""Debug what Oxylabs is actually extracting."""
import os
import sys
from dotenv import load_dotenv
from bot import MLSCompBot

load_dotenv()

print("=" * 80)
print("DEBUGGING OXYLABS EXTRACTION")
print("=" * 80)

address = "3644 E CONSTITUTION DR"
city = "GILBERT"
state = "AZ"
zip_code = "85296"

print(f"\nTesting property: {address}, {city}, {state} {zip_code}\n")

try:
    bot = MLSCompBot()
    bot.connect()
    
    print("Searching for property...")
    result = bot.find_comps_for_property(
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        max_comps=1
    )
    
    if result:
        subject = result.subject_property
        print("\n" + "=" * 80)
        print("SUBJECT PROPERTY DATA")
        print("=" * 80)
        print(f"Bedrooms: {subject.bedrooms}")
        print(f"Bathrooms: {subject.bathrooms}")
        print(f"Cooling: {subject.cooling_type}")
        print(f"Roof: {subject.roof_material}")
        print(f"Amenities: {subject.amenities}")
        print(f"Amenities count: {len(subject.amenities) if subject.amenities else 0}")
        print(f"\nMLS Data (Oxylabs metadata):")
        if subject.mls_data:
            for key, value in subject.mls_data.items():
                if key == 'source':
                    print(f"  Source: {value}")
                elif key == 'days_on_market':
                    print(f"  Days on Market: {value}")
                elif key == 'property_description':
                    if value:
                        desc_preview = value[:200] + "..." if len(value) > 200 else value
                        print(f"  Property Description: {desc_preview}")
                elif key == 'interior_features':
                    print(f"  Interior Features: {value}")
                elif key == 'exterior_features':
                    print(f"  Exterior Features: {value}")
        else:
            print("  No MLS data")
        
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        
        if subject.mls_data and subject.mls_data.get('source') == 'oxylabs_redfin':
            print("[OK] Data came from Oxylabs (Redfin)")
            if subject.mls_data.get('days_on_market'):
                print("[OK] Days on Market extracted")
            if subject.mls_data.get('property_description'):
                print("[OK] Property description extracted")
            if len(subject.amenities) > 1:
                print(f"[OK] Enhanced amenities extracted ({len(subject.amenities)} items)")
            else:
                print("[WARN] Only basic amenities found")
        elif subject.mls_data and subject.mls_data.get('source') == 'oxylabs_zillow':
            print("[OK] Data came from Oxylabs (Zillow)")
        else:
            print("[WARN] Data did NOT come from Oxylabs")
            print(f"  Source: {subject.mls_data.get('source') if subject.mls_data else 'Unknown'}")
        
    else:
        print("[FAIL] No results returned")
        
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

