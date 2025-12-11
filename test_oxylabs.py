"""Quick test script for Oxylabs integration."""
import os
from dotenv import load_dotenv
from bot import MLSCompBot
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_oxylabs():
    """Test Oxylabs integration with a property that has missing data."""
    
    # Check if Oxylabs is configured
    oxylabs_username = os.getenv("OXYLABS_USERNAME", "")
    oxylabs_password = os.getenv("OXYLABS_PASSWORD", "")
    oxylabs_enabled = os.getenv("OXYLABS_ENABLED", "false").lower() == "true"
    
    if not oxylabs_enabled:
        print("⚠️  Oxylabs is not enabled. Set OXYLABS_ENABLED=true in .env")
        return
    
    if not oxylabs_username or not oxylabs_password:
        print("⚠️  Oxylabs credentials not set. Add OXYLABS_USERNAME and OXYLABS_PASSWORD to .env")
        return
    
    print("✅ Oxylabs is configured")
    print(f"   Username: {oxylabs_username[:10]}...")
    print()
    
    # Test with a property that might have missing data
    # Use the property you mentioned earlier
    test_address = "36937 N OAKLEY DR"
    test_city = "SAN TAN VALLEY"
    test_state = "AZ"
    test_zip = "85140"
    
    print(f"Testing with property:")
    print(f"  Address: {test_address}")
    print(f"  City: {test_city}, {test_state} {test_zip}")
    print()
    
    try:
        bot = MLSCompBot()
        bot.connect()
        
        print("Searching for comparables...")
        result = bot.find_comps_for_property(
            address=test_address,
            city=test_city,
            state=test_state,
            zip_code=test_zip,
            max_comps=5
        )
        
        if result:
            subject = result.subject_property
            print()
            print("=" * 60)
            print("RESULTS:")
            print("=" * 60)
            print(f"Address: {subject.address}")
            print(f"Bedrooms: {subject.bedrooms or 'N/A (missing)'}")
            print(f"Bathrooms: {subject.bathrooms or 'N/A (missing)'}")
            print(f"Square Feet: {subject.square_feet or 'N/A'}")
            print()
            
            if subject.bedrooms is None or subject.bathrooms is None:
                print("⚠️  Still missing bedrooms/bathrooms")
                print("   Check logs above to see if Oxylabs was called")
            else:
                print("✅ Got bedrooms and bathrooms!")
                print("   Check logs to see which source provided the data")
            
            print()
            print(f"Comparables found: {len(result.comparable_properties)}")
            print(f"Confidence: {result.confidence_score:.1%}")
        else:
            print("❌ No results returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_oxylabs()

