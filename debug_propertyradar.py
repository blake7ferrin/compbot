"""Smoke test for PropertyRadar API connectivity + address lookup.

Usage:
  - Copy `env.example` -> `.env` and fill in:
      PROPERTYRADAR_ENABLED=true
      PROPERTYRADAR_API_KEY=...
  - Then run:
      python debug_propertyradar.py
"""

from dotenv import load_dotenv

from config import settings
from alternative_apis import PropertyRadarConnector


def main() -> int:
    load_dotenv()

    if not settings.propertyradar_enabled:
        print("PROPERTYRADAR_ENABLED is false. Set it to true in your .env.")
        return 2
    if not settings.propertyradar_api_key:
        print("PROPERTYRADAR_API_KEY is missing. Add it to your .env.")
        return 2

    # Replace with a property you know PropertyRadar should have
    address = "3644 E CONSTITUTION DR"
    city = "GILBERT"
    state = "AZ"
    zip_code = "85296"

    pr = PropertyRadarConnector(settings.propertyradar_api_key)
    if not pr.connect():
        print("Failed to connect to PropertyRadar. Check API key + subscription.")
        return 1

    prop = pr.get_property_by_address(address, city, state, zip_code)
    if not prop:
        print("No property returned (could not resolve RadarID or fetch details).")
        return 1

    print("OK: PropertyRadar returned data.")
    print(f"  RadarID: {prop.mls_data.get('radar_id') if prop.mls_data else None}")
    print(f"  AVM: {prop.mls_data.get('avm') if prop.mls_data else None}")
    print(
        f"  AvailableEquity: {prop.mls_data.get('available_equity') if prop.mls_data else None}"
    )
    print(
        f"  Flags: free_and_clear={prop.mls_data.get('is_free_and_clear') if prop.mls_data else None}, "
        f"cash_buyer={prop.mls_data.get('is_cash_buyer') if prop.mls_data else None}, "
        f"absentee_owner={prop.mls_data.get('is_absentee_owner') if prop.mls_data else None}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


