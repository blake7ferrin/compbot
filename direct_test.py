"""Direct test with explicit output."""
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("Starting ATTOM Comp Bot Test...", flush=True)
print("=" * 60, flush=True)

try:
    print("\n1. Loading configuration...", flush=True)
    from config import settings
    print(f"   Using ATTOM API", flush=True)
    print(f"   API Key: {settings.attom_api_key[:15]}..." if settings.attom_api_key else "   API Key: NOT SET", flush=True)
    
    print("\n2. Creating bot...", flush=True)
    from bot import MLSCompBot
    bot = MLSCompBot()
    print("   Bot created successfully", flush=True)
    
    print("\n3. Connecting to ATTOM API...", flush=True)
    if bot.connect():
        print("   ✓ Connected!", flush=True)
        
        print("\n4. Looking up property: 1342 E. Kramer Circle, Mesa, AZ 85203", flush=True)
        result = bot.find_comps_for_property(
            address="1342 E. Kramer Circle",
            city="Mesa",
            zip_code="85203",
            max_comps=5
        )
        
        if result:
            print(f"\n   ✓ SUCCESS! Found comp analysis", flush=True)
            print(f"\n   Subject Property:", flush=True)
            print(f"     Address: {result.subject_property.address}", flush=True)
            print(f"     City: {result.subject_property.city}, {result.subject_property.state}", flush=True)
            print(f"     Bedrooms: {result.subject_property.bedrooms or 'N/A'}", flush=True)
            print(f"     Bathrooms: {result.subject_property.bathrooms or 'N/A'}", flush=True)
            print(f"     Square Feet: {result.subject_property.square_feet or 'N/A'}", flush=True)
            
            print(f"\n   Found {len(result.comparable_properties)} Comparable Properties", flush=True)
            print(f"   Confidence Score: {result.confidence_score:.2%}", flush=True)
            
            if result.estimated_value:
                print(f"   Estimated Value: ${result.estimated_value:,.0f}", flush=True)
            if result.average_price:
                print(f"   Average Comp Price: ${result.average_price:,.0f}", flush=True)
            if result.average_price_per_sqft:
                print(f"   Avg Price/SqFt: ${result.average_price_per_sqft:,.2f}", flush=True)
            
            if result.comparable_properties:
                print(f"\n   Top Comparables:", flush=True)
                for i, comp in enumerate(result.comparable_properties[:3], 1):
                    prop = comp.property
                    print(f"\n   {i}. {prop.address}", flush=True)
                    print(f"      Score: {comp.similarity_score:.2%}", flush=True)
                    if comp.distance_miles:
                        print(f"      Distance: {comp.distance_miles:.2f} miles", flush=True)
                    if prop.sold_price:
                        print(f"      Sold: ${prop.sold_price:,.0f}", flush=True)
                        if prop.sold_date:
                            print(f"      Date: {prop.sold_date.strftime('%Y-%m-%d')}", flush=True)
        else:
            print("\n   ✗ No comps found", flush=True)
        
        print("\n5. Disconnecting...", flush=True)
        bot.disconnect()
        print("   ✓ Disconnected", flush=True)
    else:
        print("   ✗ Failed to connect", flush=True)
        print("   Check your ATTOM API key in .env file", flush=True)
        
except ImportError as e:
    print(f"\n✗ Import Error: {e}", flush=True)
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\n✗ Error: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60, flush=True)
print("Test Complete!", flush=True)
