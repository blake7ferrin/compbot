"""Quick test script for ATTOM comp bot."""
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("ATTOM COMP BOT TEST")
print("=" * 60)
print()

try:
    print("1. Testing imports...")
    from bot import MLSCompBot
    from config import settings
    print("   ✓ Imports successful")
    print()
    
    print("2. Checking configuration...")
    print(f"   Using ATTOM API")
    print(f"   ATTOM API Key: {settings.attom_api_key[:10]}..." if settings.attom_api_key else "   ✗ No ATTOM API key found")
    print()
    
    print("3. Initializing bot...")
    bot = MLSCompBot()
    print("   ✓ Bot initialized")
    print()
    
    print("4. Connecting to ATTOM API...")
    if bot.connect():
        print("   ✓ Connected successfully!")
        print()
        
        print("5. Testing property lookup...")
        print("   Looking up: 1342 E. Kramer Circle, Mesa, AZ 85203")
        result = bot.find_comps_for_property(
            address="1342 E. Kramer Circle",
            city="Mesa",
            zip_code="85203",
            max_comps=5
        )
        
        if result:
            print("   ✓ Found comps!")
            print()
            print(f"   Subject: {result.subject_property.address}")
            print(f"   Found {len(result.comparable_properties)} comparable properties")
            if result.estimated_value:
                print(f"   Estimated Value: ${result.estimated_value:,.0f}")
            print()
            
            if result.comparable_properties:
                print("   Top Comps:")
                for i, comp in enumerate(result.comparable_properties[:3], 1):
                    prop = comp.property
                    print(f"   {i}. {prop.address}")
                    print(f"      Score: {comp.similarity_score:.2%}")
                    if comp.distance_miles:
                        print(f"      Distance: {comp.distance_miles:.2f} miles")
                    if prop.sold_price:
                        print(f"      Sold: ${prop.sold_price:,.0f}")
        else:
            print("   ✗ No comps found")
        
        print()
        print("6. Disconnecting...")
        bot.disconnect()
        print("   ✓ Disconnected")
    else:
        print("   ✗ Failed to connect")
        print("   Check your ATTOM API key in .env file")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)

