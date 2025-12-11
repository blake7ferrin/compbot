"""Test script to check what fields are available in v1 API."""
import requests
import json
from config import settings

def test_v1_api():
    """Test v1 expandedprofile endpoint to see what fields are available."""
    headers = {
        "apikey": settings.attom_api_key,
        "Accept": "application/json",
    }
    
    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/expandedprofile"
    params = {
        "address1": "3644 E CONSTITUTION DR",
        "address2": "GILBERT, AZ 85296",
        "debug": "True"
    }
    
    print("Calling v1 expandedprofile API...")
    response = requests.get(url, headers=headers, params=params, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        
        # Save full response
        with open('v1_response_debug.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("Full response saved to v1_response_debug.json")
        
        # Check structure
        if "property" in data and len(data["property"]) > 0:
            prop = data["property"][0]
            print("\n=== Property Structure ===")
            print(f"Top-level keys: {list(prop.keys())[:20]}")
            
            # Check building
            building = prop.get("building", {})
            if building:
                print(f"\nBuilding keys: {list(building.keys())[:30]}")
                # Check for architectural style
                print(f"  architecturalStyle: {building.get('architecturalStyle')}")
                print(f"  style: {building.get('style')}")
                print(f"  architecturalType: {building.get('architecturalType')}")
                print(f"  condition: {building.get('condition')}")
                print(f"  propertyCondition: {building.get('propertyCondition')}")
                print(f"  renovationYear: {building.get('renovationYear')}")
                print(f"  lastRenovationYear: {building.get('lastRenovationYear')}")
            
            # Check summary
            summary = prop.get("summary", {})
            if summary:
                print(f"\nSummary keys: {list(summary.keys())[:30]}")
                print(f"  architecturalStyle: {summary.get('architecturalStyle')}")
                print(f"  style: {summary.get('style')}")
                print(f"  condition: {summary.get('condition')}")
                print(f"  propertyCondition: {summary.get('propertyCondition')}")
                print(f"  renovationYear: {summary.get('renovationYear')}")
            
            # Check school data
            school = prop.get("school") or prop.get("schools")
            if school:
                print(f"\nSchool data found: {type(school)}")
                if isinstance(school, dict):
                    print(f"  School keys: {list(school.keys())[:20]}")
                    print(f"  districtName: {school.get('districtName')}")
                    print(f"  district: {school.get('district')}")
                    print(f"  schoolDistrict: {school.get('schoolDistrict')}")
                elif isinstance(school, list) and len(school) > 0:
                    print(f"  First school: {school[0]}")
            
            # Check sale data
            sale = prop.get("sale", {})
            if sale:
                print(f"\nSale keys: {list(sale.keys())[:20]}")
                print(f"  sellerConcessions: {sale.get('sellerConcessions')}")
                print(f"  concessions: {sale.get('concessions')}")
                print(f"  sellerConcessionsDescription: {sale.get('sellerConcessionsDescription')}")
                print(f"  concessionsDescription: {sale.get('concessionsDescription')}")
                print(f"  financingType: {sale.get('financingType')}")
                print(f"  loanType: {sale.get('loanType')}")
                print(f"  armsLength: {sale.get('armsLength')}")
                print(f"  armsLengthTransaction: {sale.get('armsLengthTransaction')}")
            
            # Search for any field containing these keywords
            print("\n=== Searching for keywords in all fields ===")
            def search_dict(d, path="", depth=0):
                if depth > 3:  # Limit depth
                    return
                if isinstance(d, dict):
                    for k, v in d.items():
                        current_path = f"{path}.{k}" if path else k
                        if any(keyword in k.lower() for keyword in ['style', 'school', 'condition', 'concession', 'renovation']):
                            print(f"  Found: {current_path} = {v}")
                        if isinstance(v, (dict, list)):
                            search_dict(v, current_path, depth+1)
                elif isinstance(d, list):
                    for i, item in enumerate(d):
                        search_dict(item, f"{path}[{i}]", depth+1)
            
            search_dict(prop)
        else:
            print("No property data found in response")
            print(f"Response keys: {list(data.keys())}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text[:500])

if __name__ == "__main__":
    test_v1_api()

