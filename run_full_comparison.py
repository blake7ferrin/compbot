"""Run full ATTOM vs Oxylabs comparison and save results."""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

output_file = "comparison_results.txt"

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("ATTOM vs OXYLABS COMPARISON\n")
    f.write(f"Property: 3644 E CONSTITUTION DR, GILBERT, AZ 85296\n")
    f.write(f"Started: {datetime.now()}\n")
    f.write("=" * 80 + "\n\n")
    f.flush()
    
    # Test ATTOM
    f.write("-" * 80 + "\n")
    f.write("ATTOM API RESULTS\n")
    f.write("-" * 80 + "\n")
    f.flush()
    
    try:
        from attom_connector import ATTOMConnector
        attom = ATTOMConnector()
        attom.connect()
        attom_prop = attom.get_property_by_address("3644 E CONSTITUTION DR", "GILBERT", "AZ", "85296")
        
        if attom_prop:
            f.write("[SUCCESS] ATTOM Success\n")
            f.write(f"  Bedrooms: {attom_prop.bedrooms}\n")
            f.write(f"  Bathrooms: {attom_prop.bathrooms}\n")
            f.write(f"  Square Feet: {attom_prop.square_feet}\n")
            f.write(f"  Cooling: {attom_prop.cooling_type}\n")
            f.write(f"  Roof: {attom_prop.roof_material}\n")
            f.write(f"  Amenities: {attom_prop.amenities}\n")
        else:
            f.write("[FAILED] ATTOM returned no data\n")
    except Exception as e:
        f.write(f"[ERROR] ATTOM Error: {e}\n")
        import traceback
        f.write(traceback.format_exc())
    
    f.write("\n")
    f.flush()
    
    # Test Oxylabs
    f.write("-" * 80 + "\n")
    f.write("OXYLABS (Redfin/Zillow Scraping) RESULTS\n")
    f.write("-" * 80 + "\n")
    f.flush()
    
    try:
        oxylabs_username = os.getenv("OXYLABS_USERNAME", "")
        oxylabs_password = os.getenv("OXYLABS_PASSWORD", "")
        
        if not oxylabs_username or not oxylabs_password:
            f.write("[WARNING] Oxylabs credentials not configured\n")
        else:
            f.write("Calling Oxylabs API (this may take 30-90 seconds)...\n")
            f.flush()
            
            from alternative_apis import OxylabsScraperConnector
            oxylabs = OxylabsScraperConnector(oxylabs_username, oxylabs_password)
            oxylabs.connect()
            
            oxylabs_prop = oxylabs.get_property_by_address("3644 E CONSTITUTION DR", "GILBERT", "AZ", "85296")
            
            if oxylabs_prop:
                f.write("[SUCCESS] Oxylabs Success\n")
                f.write(f"  Bedrooms: {oxylabs_prop.bedrooms}\n")
                f.write(f"  Bathrooms: {oxylabs_prop.bathrooms}\n")
                f.write(f"  Square Feet: {oxylabs_prop.square_feet}\n")
                f.write(f"  Lot Size: {oxylabs_prop.lot_size_sqft}\n")
                f.write(f"  Year Built: {oxylabs_prop.year_built}\n")
                f.write(f"  Cooling: {oxylabs_prop.cooling_type}\n")
                f.write(f"  Roof: {oxylabs_prop.roof_material}\n")
                f.write(f"  Amenities: {oxylabs_prop.amenities}\n")
                f.write(f"  List Price: {oxylabs_prop.list_price}\n")
            else:
                f.write("[FAILED] Oxylabs returned no data\n")
    except Exception as e:
        f.write(f"[ERROR] Oxylabs Error: {e}\n")
        import traceback
        f.write(traceback.format_exc())
    
    f.write("\n")
    f.write("=" * 80 + "\n")
    f.write(f"Completed: {datetime.now()}\n")
    f.write("=" * 80 + "\n")

print(f"\nComparison complete! Results saved to: {output_file}\n")
print("Reading results...\n")
print("=" * 80)

if os.path.exists(output_file):
    with open(output_file, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print("Results file not found")

