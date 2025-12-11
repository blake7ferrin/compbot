"""Example usage of the MLS Comp Bot."""
from bot import MLSCompBot

# Initialize the bot
bot = MLSCompBot()

# Connect to MLS
print("Connecting to MLS...")
if bot.connect():
    print("Connected successfully!")
    
    # Example 1: Find comps by MLS number
    print("\n=== Example 1: Find comps by MLS number ===")
    result = bot.find_comps_for_property(mls_number="123456", max_comps=5)
    if result:
        print(f"Found {len(result.comparable_properties)} comps")
        print(f"Confidence: {result.confidence_score:.2%}")
        if result.estimated_value:
            print(f"Estimated Value: ${result.estimated_value:,.0f}")
    
    # Example 2: Find comps by address
    print("\n=== Example 2: Find comps by address ===")
    result = bot.find_comps_for_property(
        address="123 Main Street",
        city="Phoenix",
        zip_code="85001",
        max_comps=5
    )
    if result:
        print(f"Found {len(result.comparable_properties)} comps")
    
    # Example 3: Find comps by criteria
    print("\n=== Example 3: Find comps by criteria ===")
    result = bot.find_comps_by_criteria(
        city="Phoenix",
        bedrooms=3,
        bathrooms=2,
        square_feet=1500,
        list_price=300000,
        max_comps=5
    )
    if result:
        print(f"Found {len(result.comparable_properties)} comps")
    
    # Example 4: Provide feedback for learning
    if result:
        print("\n=== Example 4: Providing feedback ===")
        bot.provide_feedback(result, rating=0.9, notes="Great comps!")
        print("Feedback recorded")
    
    # Example 5: Train the model
    print("\n=== Example 5: Training model ===")
    bot.train_model()
    print("Model trained!")
    
    # Disconnect
    bot.disconnect()
    print("\nDisconnected from MLS")
else:
    print("Failed to connect. Check your .env configuration.")

