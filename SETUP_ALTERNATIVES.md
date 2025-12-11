# Quick Setup: Alternative APIs (No MLS Approval Needed)

## Option 1: Estated API (Recommended - Free Tier Available)

### Step 1: Get API Key
1. Go to [estated.com](https://estated.com)
2. Sign up for a free account
3. Get your API key from the dashboard

### Step 2: Configure
Edit your `.env` file:
```bash
MLS_TYPE=ESTATED
ESTATED_API_KEY=your_api_key_here
```

### Step 3: Test
```bash
python main.py --address "123 Main St" --city "Phoenix" --zip "85001"
```

**Note**: Estated works best with specific addresses. For area searches, you may need to provide multiple addresses.

---

## Option 2: RealtyMole API (Freemium)

### Step 1: Get API Key
1. Go to [realtymole.com](https://realtymole.com)
2. Sign up for an account
3. Get your API key from account settings

### Step 2: Configure
Edit your `.env` file:
```bash
MLS_TYPE=REALTYMOLE
REALTYMOLE_API_KEY=your_api_key_here
```

### Step 3: Test
```bash
python main.py --city "Phoenix" --bedrooms 3 --sqft 1500
```

---

## Option 3: Zillow API (Requires Approval)

### Step 1: Apply for Access
1. Visit [Zillow Developer Portal](https://www.zillowgroup.com/developers/)
2. Apply for API access
3. Wait for approval (can take time)

### Step 2: Configure (After Approval)
Edit your `.env` file:
```bash
MLS_TYPE=ZILLOW
ZILLOW_API_KEY=your_zillow_api_key
```

---

## Comparison

| API | Setup Time | Free Tier | Best For |
|-----|------------|-----------|----------|
| **Estated** | ⚡ 5 minutes | ✅ Yes | Address lookups |
| **RealtyMole** | ⚡ 5 minutes | ✅ Yes | Property searches |
| **Zillow** | ⏳ Days/Weeks | ❌ No | Comprehensive data |

## Recommendation

**Start with Estated or RealtyMole** - they're quick to set up and have free tiers. You can switch to MLS later when approved.

The bot works identically with all APIs - just change the `MLS_TYPE` in your `.env` file!

