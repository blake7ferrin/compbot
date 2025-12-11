"""Compare data extraction from ATTOM vs Oxylabs for the same property."""
import os
from dotenv import load_dotenv
from bot import MLSCompBot
from attom_connector import ATTOMConnector
from alternative_apis import OxylabsScraperConnector
import logging
from pprint import pprint

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def compare_sources(address: str, city: str, state: str, zip_code: str):
    """Compare data extraction from ATTOM vs Oxylabs."""
    import sys
    
    print("=" * 80, flush=True)
    print("DATA SOURCE COMPARISON", flush=True)
    print("=" * 80, flush=True)
    print(f"Property: {address}, {city}, {state} {zip_code}", flush=True)
    print(flush=True)
    
    # Test ATTOM
    print("-" * 80)
    print("ATTOM API DATA")
    print("-" * 80)
    attom_data = {}
    
    try:
        attom = ATTOMConnector()
        attom.connect()
        
        # Get property from ATTOM
        attom_prop = attom.get_property_by_address(address, city, state, zip_code)
        
        if attom_prop:
            attom_data = {
                "Bedrooms": attom_prop.bedrooms,
                "Bathrooms": attom_prop.bathrooms,
                "Bathrooms Full": attom_prop.bathrooms_full,
                "Bathrooms Half": attom_prop.bathrooms_half,
                "Total Rooms": attom_prop.total_rooms,
                "Square Feet": attom_prop.square_feet,
                "Lot Size (sqft)": attom_prop.lot_size_sqft,
                "Lot Size (acres)": attom_prop.lot_size_acres,
                "Year Built": attom_prop.year_built,
                "Stories": attom_prop.stories,
                "Parking Spaces": attom_prop.parking_spaces,
                "Garage Type": attom_prop.garage_type,
                "Heating Type": attom_prop.heating_type,
                "Cooling Type": attom_prop.cooling_type,
                "Roof Material": attom_prop.roof_material,
                "Architectural Style": attom_prop.architectural_style,
                "Condition": attom_prop.condition,
                "Amenities": attom_prop.amenities,
                "Exterior Features": attom_prop.exterior_features,
                "Recent Upgrades": attom_prop.recent_upgrades,
                "Renovation Year": attom_prop.renovation_year,
                "School District": attom_prop.school_district,
                "List Price": attom_prop.list_price,
                "Sold Price": attom_prop.sold_price,
                "Price per SqFt": attom_prop.price_per_sqft,
                "Sold Date": attom_prop.sold_date,
            }
            
            for key, value in attom_data.items():
                if value is not None and value != "" and value != []:
                    print(f"  {key:25} {value}")
        else:
            print("  ❌ No data returned from ATTOM")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test Oxylabs
    print("-" * 80)
    print("OXYLABS (Redfin/Zillow Scraping) DATA")
    print("-" * 80)
    oxylabs_data = {}
    
    try:
        oxylabs_username = os.getenv("OXYLABS_USERNAME", "")
        oxylabs_password = os.getenv("OXYLABS_PASSWORD", "")
        
        if not oxylabs_username or not oxylabs_password:
            print("  ⚠️  Oxylabs credentials not configured")
        else:
            oxylabs = OxylabsScraperConnector(oxylabs_username, oxylabs_password)
            oxylabs.connect()
            
            oxylabs_prop = oxylabs.get_property_by_address(address, city, state, zip_code)
            
            if oxylabs_prop:
                oxylabs_data = {
                    "Bedrooms": oxylabs_prop.bedrooms,
                    "Bathrooms": oxylabs_prop.bathrooms,
                    "Bathrooms Full": oxylabs_prop.bathrooms_full,
                    "Bathrooms Half": oxylabs_prop.bathrooms_half,
                    "Total Rooms": oxylabs_prop.total_rooms,
                    "Square Feet": oxylabs_prop.square_feet,
                    "Lot Size (sqft)": oxylabs_prop.lot_size_sqft,
                    "Lot Size (acres)": oxylabs_prop.lot_size_acres,
                    "Year Built": oxylabs_prop.year_built,
                    "Stories": oxylabs_prop.stories,
                    "Parking Spaces": oxylabs_prop.parking_spaces,
                    "Garage Type": oxylabs_prop.garage_type,
                    "Heating Type": oxylabs_prop.heating_type,
                    "Cooling Type": oxylabs_prop.cooling_type,
                    "Roof Material": oxylabs_prop.roof_material,
                    "Architectural Style": oxylabs_prop.architectural_style,
                    "Condition": oxylabs_prop.condition,
                    "Amenities": oxylabs_prop.amenities,
                    "Exterior Features": oxylabs_prop.exterior_features,
                    "Recent Upgrades": oxylabs_prop.recent_upgrades,
                    "Renovation Year": oxylabs_prop.renovation_year,
                    "School District": oxylabs_prop.school_district,
                    "List Price": oxylabs_prop.list_price,
                    "Sold Price": oxylabs_prop.sold_price,
                    "Price per SqFt": oxylabs_prop.price_per_sqft,
                    "Sold Date": oxylabs_prop.sold_date,
                }
                
                for key, value in oxylabs_data.items():
                    if value is not None and value != "" and value != []:
                        print(f"  {key:25} {value}")
            else:
                print("  ❌ No data returned from Oxylabs")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Comparison
    print("=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    all_fields = set(list(attom_data.keys()) + list(oxylabs_data.keys()))
    
    print("\nFields where ATTOM has data but Oxylabs doesn't:")
    attom_only = []
    for field in all_fields:
        attom_val = attom_data.get(field)
        oxylabs_val = oxylabs_data.get(field)
        if attom_val and (not oxylabs_val or oxylabs_val == "" or oxylabs_val == []):
            attom_only.append(field)
            print(f"  ✓ {field:30} ATTOM: {attom_val}")
    
    if not attom_only:
        print("  (none)")
    
    print("\nFields where Oxylabs has data but ATTOM doesn't:")
    oxylabs_only = []
    for field in all_fields:
        attom_val = attom_data.get(field)
        oxylabs_val = oxylabs_data.get(field)
        if oxylabs_val and (not attom_val or attom_val == "" or attom_val == []):
            oxylabs_only.append(field)
            print(f"  ✓ {field:30} Oxylabs: {oxylabs_val}")
    
    if not oxylabs_only:
        print("  (none)")
    
    print("\nFields where both have data (comparing values):")
    both_have = []
    for field in all_fields:
        attom_val = attom_data.get(field)
        oxylabs_val = oxylabs_data.get(field)
        if attom_val and oxylabs_val:
            both_have.append(field)
            match = "✓" if str(attom_val) == str(oxylabs_val) else "⚠"
            print(f"  {match} {field:30} ATTOM: {attom_val:20} | Oxylabs: {oxylabs_val}")
    
    if not both_have:
        print("  (none)")
    
    print("\nFields missing from both:")
    missing_both = []
    for field in all_fields:
        attom_val = attom_data.get(field)
        oxylabs_val = oxylabs_data.get(field)
        if (not attom_val or attom_val == "" or attom_val == []) and (not oxylabs_val or oxylabs_val == "" or oxylabs_val == []):
            missing_both.append(field)
    
    if missing_both:
        for field in missing_both:
            print(f"  ✗ {field}")
    else:
        print("  (all fields have data from at least one source)")
    
    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if attom_only:
        print(f"\n✓ ATTOM provides {len(attom_only)} unique fields: {', '.join(attom_only[:5])}")
    if oxylabs_only:
        print(f"\n✓ Oxylabs provides {len(oxylabs_only)} unique fields: {', '.join(oxylabs_only[:5])}")
    if both_have:
        matches = sum(1 for f in both_have if str(attom_data.get(f)) == str(oxylabs_data.get(f)))
        print(f"\n✓ Both sources agree on {matches}/{len(both_have)} fields")
    
    print("\n💡 Best Strategy:")
    print("  1. Use ATTOM as primary (official data, more comprehensive)")
    print("  2. Use Oxylabs to fill gaps (especially bedrooms/bathrooms)")
    print("  3. Cross-validate when both have data")
    print("  4. Use estimation as last resort")

if __name__ == "__main__":
    # Test with the property you mentioned
    compare_sources(
        address="3644 E CONSTITUTION DR",
        city="GILBERT",
        state="AZ",
        zip_code="85296"
    )

