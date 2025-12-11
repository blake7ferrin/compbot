# Quick Start: Training the Bot

## Add Google Maps API Key (Optional but Recommended)

1. Get API key from [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "Street View Static API"
3. Add to `.env` file:
   ```
   GOOGLE_MAPS_API_KEY=your_key_here
   ```

## Train with Comp Guidelines

### Method 1: Using Python Script

```python
from bot import MLSCompBot

bot = MLSCompBot()
bot.connect()

# Add guidelines
bot.guidelines_trainer.add_instruction_text(
    "Comparables should be within 1 mile and sold within 6 months"
)

bot.guidelines_trainer.add_instruction_text(
    "Bedrooms must match exactly"
)
```

### Method 2: Run Example Script

```powershell
python train_example.py
```

### Method 3: Direct Criteria

```python
bot.guidelines_trainer.add_guideline(
    description="Properties must be within 1 mile",
    criteria={"max_distance_miles": 1.0},
    priority=2.0  # High priority (must pass)
)
```

## View Guidelines

```python
guidelines = bot.guidelines_trainer.list_guidelines()
for guideline in guidelines:
    print(guideline['description'])
```

## Guidelines Are Automatic

Once added, guidelines are:
- ✅ Saved to `comp_guidelines.json`
- ✅ Automatically applied to all searches
- ✅ Used to filter and score comparables
- ✅ Update similarity weights

## Example Guidelines

```
"Comparables should be within 1 mile and sold within 6 months"
"Bedrooms must match exactly, bathrooms can vary by 0.5"
"Price should be within 15% of subject property"
"Prefer properties with similar lot sizes (within 20%)"
```

That's it! The bot learns from your instructions and applies them automatically.
