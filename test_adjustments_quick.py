"""Quick test of professional adjustments system."""
import sys
sys.stdout.reconfigure(line_buffering=True)

print("Testing Professional Adjustments System")
print("=" * 60)
print()

from bot import MLSCompBot

bot = MLSCompBot()
if bot.connect():
    print("✓ Connected to ATTOM API")
    print()
    print("Searching for comparables: 1342 E. Kramer Circle, Mesa, AZ 85203")
    print("(This will show adjustments for each comparable)")
    print()
    
    result = bot.find_comps_for_property(
        address="1342 E. Kramer Circle",
        city="Mesa",
        zip_code="85203",
        max_comps=3
    )
    
    if result and result.comparable_properties:
        print(f"✓ Found {len(result.comparable_properties)} comparables")
        print()
        print(f"Estimated Value: ${result.estimated_value:,.0f}" if result.estimated_value else "No value estimate")
        print(f"Confidence: {result.confidence_score:.1%}")
        print()
        print("=" * 60)
        print("ADJUSTMENTS DETAILS:")
        print("=" * 60)
        
        for i, comp in enumerate(result.comparable_properties, 1):
            prop = comp.property
            print()
            print(f"COMP #{i}: {prop.address}")
            print(f"  Similarity: {comp.similarity_score:.1%}")
            print(f"  Original Sale Price: ${prop.sold_price or prop.list_price:,.0f}")
            
            if comp.adjustments:
                print(f"  Adjustments ({len(comp.adjustments)}):")
                for adj in comp.adjustments:
                    print(f"    • {adj.category}: {adj.description}")
                    print(f"      ${adj.amount:+,.0f} - {adj.reason}")
                print(f"  Total Adjustments: ${comp.total_adjustment_amount:+,.0f}")
                print(f"  Adjusted Price: ${comp.adjusted_price:,.0f}")
            else:
                print("  No adjustments needed (very similar to subject)")
            print()
    else:
        print("✗ No comparables found")
    
    bot.disconnect()
else:
    print("✗ Failed to connect")

print("=" * 60)
print("Test Complete!")

