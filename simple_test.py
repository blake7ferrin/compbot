#!/usr/bin/env python
"""Simple test that will definitely show output."""
import sys
print("Starting test...", file=sys.stderr)
print("Python is working!", flush=True)

try:
    print("Importing modules...", flush=True)
    from bot import MLSCompBot
    print("Bot imported!", flush=True)
    
    print("Creating bot instance...", flush=True)
    bot = MLSCompBot()
    print("Bot created!", flush=True)
    
    print("Connecting to ATTOM...", flush=True)
    if bot.connect():
        print("✓ Connected to ATTOM API!", flush=True)
        
        print("\nFinding comps for: 1342 E. Kramer Circle, Mesa, AZ 85203", flush=True)
        result = bot.find_comps_for_property(
            address="1342 E. Kramer Circle",
            city="Mesa",
            zip_code="85203",
            max_comps=5
        )
        
        if result:
            print(f"\n✓ SUCCESS! Found {len(result.comparable_properties)} comps", flush=True)
            print(f"Subject: {result.subject_property.address}", flush=True)
            if result.estimated_value:
                print(f"Estimated Value: ${result.estimated_value:,.0f}", flush=True)
        else:
            print("✗ No comps found", flush=True)
        
        bot.disconnect()
    else:
        print("✗ Failed to connect", flush=True)
        
except Exception as e:
    print(f"✗ ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc(file=sys.stdout)

print("\nTest complete!", flush=True)
