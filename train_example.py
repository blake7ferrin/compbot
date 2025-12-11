"""Example script for training the bot with comp guidelines."""
from bot import MLSCompBot

# Initialize bot
bot = MLSCompBot()
bot.connect()

# Add comp guidelines using natural language
print("Adding comp guidelines...")

# Example 1: Distance and time requirements
bot.guidelines_trainer.add_instruction_text(
    "Comparables should be within 1 mile and sold within 6 months"
)

# Example 2: Bedroom requirements
bot.guidelines_trainer.add_instruction_text(
    "Bedrooms must match exactly, bathrooms can vary by 0.5"
)

# Example 3: Price requirements
bot.guidelines_trainer.add_instruction_text(
    "Price should be within 15% of subject property"
)

# Example 4: Lot size preference
bot.guidelines_trainer.add_instruction_text(
    "Prefer properties with similar lot sizes (within 20%)"
)

# View all guidelines
print("\nCurrent Guidelines:")
guidelines = bot.guidelines_trainer.list_guidelines()
for i, guideline in enumerate(guidelines, 1):
    print(f"{i}. {guideline['description']}")
    print(f"   Criteria: {guideline['criteria']}")
    print(f"   Priority: {guideline['priority']}")
    print()

print("Guidelines saved and applied! The bot will now use these rules for all searches.")
