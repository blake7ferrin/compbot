# Training the Bot with Comp Guidelines

## Overview

The bot can learn from comp guidelines and instructions you provide. This allows you to customize how the bot selects and scores comparables.

## How to Add Guidelines

### Method 1: Natural Language Instructions

You can add guidelines using natural language. The bot will parse and apply them:

```python
from bot import MLSCompBot

bot = MLSCompBot()
bot.connect()

# Add guidelines
bot.guidelines_trainer.add_instruction_text(
    "Comparables should be within 1 mile and sold within 6 months"
)

bot.guidelines_trainer.add_instruction_text(
    "Bedrooms must match exactly, bathrooms can vary by 0.5"
)

bot.guidelines_trainer.add_instruction_text(
    "Price should be within 15% of subject property"
)
```

### Method 2: Detailed Criteria

For more control, specify exact criteria:

```python
bot.guidelines_trainer.add_guideline(
    description="Properties must be within 1 mile",
    criteria={
        "max_distance_miles": 1.0
    },
    priority=2.0  # High priority (must pass)
)

bot.guidelines_trainer.add_guideline(
    description="Prefer similar lot sizes",
    criteria={
        "lot_size_tolerance_percent": 20.0
    },
    priority=1.5  # Medium priority (preference)
)
```

## Supported Criteria

- **max_distance_miles**: Maximum distance in miles
- **max_age_months**: Maximum age of sale in months
- **lot_size_tolerance_percent**: Lot size difference tolerance (%)
- **bedrooms_exact_match**: True if bedrooms must match exactly
- **bedrooms_tolerance**: Allowed bedroom difference (e.g., 1)
- **bathrooms_exact_match**: True if bathrooms must match exactly
- **bathrooms_tolerance**: Allowed bathroom difference (e.g., 0.5)
- **price_tolerance_percent**: Price difference tolerance (%)

## Priority Levels

- **2.0**: Must pass (hard requirement)
- **1.5**: Strong preference
- **1.0**: Normal preference

## Example Instructions

```
"Comparables should be within 1 mile and sold within 6 months"
"Properties must have matching bedrooms"
"Bathrooms can vary by 0.5"
"Price should be within 15% of subject"
"Prefer properties with similar lot sizes (within 20%)"
```

## Viewing Guidelines

```python
guidelines = bot.guidelines_trainer.list_guidelines()
for i, guideline in enumerate(guidelines):
    print(f"{i+1}. {guideline['description']}")
    print(f"   Criteria: {guideline['criteria']}")
    print(f"   Priority: {guideline['priority']}")
```

## Removing Guidelines

```python
bot.guidelines_trainer.remove_guideline(0)  # Remove first guideline
```

## How It Works

1. Guidelines are saved to `comp_guidelines.json`
2. Bot automatically applies guidelines when selecting comps
3. Guidelines update similarity weights and filtering
4. High-priority guidelines act as hard filters

## Integration with Web Interface

Guidelines can be added through:
- Command line
- Web interface (future feature)
- Configuration file

The bot will automatically use guidelines for all future searches!
