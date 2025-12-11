"""ATTOM Data Solutions API connector for comparable properties."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from config import settings
from mls_connector import MLSConnector
from models import Property, PropertyStatus, PropertyType

logger = logging.getLogger(__name__)


def _is_valid_cooling_type(value: str) -> bool:
    """Check if cooling type value is valid (not a placeholder)."""
    if not value or len(value) < 2:
        return False
    value_upper = value.upper().strip()
    invalid = [
        "NO",
        "NONE",
        "",
        "REFRIGERATOR",
        "COOLING",
        "COOLINGTYPE",
        "COOLING_TYPE",
        "COOLINGTYPE",
    ]
    if value_upper in invalid:
        return False
    # Check if it contains valid cooling terms
    valid_terms = [
        "air",
        "central",
        "evaporative",
        "heat",
        "pump",
        "window",
        "ductless",
        "mini",
        "split",
        "yes",
        "y",
        "ac",
        "a/c",
        "conditioning",
    ]
    return any(term in value.lower() for term in valid_terms) or value_upper == "YES"


def _is_valid_roof_material(value: str) -> bool:
    """Check if roof material value is valid (not a placeholder)."""
    if not value or len(value) < 3:
        return False
    value_upper = value.upper().strip()
    invalid = [
        "ROOF",
        "ROOFMATERIAL",
        "ROOF_MATERIAL",
        "ROOF MATERIAL",
        "ROOFTYPE",
        "ROOF TYPE",
    ]
    return value_upper not in invalid


class ATTOMConnector(MLSConnector):
    """ATTOM Data Solutions API connector."""

    BASE_URL_V1 = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"
    BASE_URL_V2 = "https://api.gateway.attomdata.com/property/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.attom_api_key
        self.connected = False
        self._last_subject_from_v2: Optional[Property] = None

        # Simple caches to avoid repeated API calls
        self._school_district_cache: Dict[str, str] = {}  # (lat,lon) -> district
        self._assessment_cache: Dict[str, Dict] = {}  # attom_id -> assessment data
        self._sale_detail_cache: Dict[str, Dict] = {}  # attom_id -> sale data
        self._avm_cache: Dict[str, Dict] = {}  # attom_id -> avm data
        self._community_cache: Dict[str, Dict] = {}  # geo_id -> community data

    def connect(self) -> bool:
        """Connect to ATTOM API (test connection)."""
        if not self.api_key:
            logger.error("ATTOM API key not configured")
            return False

        # Test connection with a simple property lookup
        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }
            # Simple test - try to get property detail for a known address
            # We'll just mark as connected if we have an API key
            self.connected = True
            logger.info("Connected to ATTOM API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ATTOM API: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from ATTOM API."""
        self.connected = False

    def get_property_by_address(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str] = None,
        attom_id: Optional[str] = None,
    ) -> Optional[Property]:
        """Get property details by address or ATTOM ID.

        Args:
            address: Street address
            city: City name
            state: State abbreviation
            zip_code: ZIP code (optional)
            attom_id: ATTOM property ID (optional, if provided will be used first)
        """
        if not self.connected:
            raise ConnectionError("Not connected to ATTOM API")

        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }

            # If we have an ATTOM ID, use it first (most reliable)
            if attom_id:
                logger.info(f"Using ATTOM ID lookup: {attom_id}")
                url = f"{self.BASE_URL_V1}/property/detail"
                params = {"attomid": attom_id, "debug": "True"}
                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    parsed = self._parse_property_detail(data)
                    if parsed:
                        logger.info("Successfully retrieved property using ATTOM ID")
                        return parsed

            # Build full address
            full_address = address
            if city:
                full_address += f", {city}"
            if state:
                full_address += f", {state}"
            if zip_code:
                full_address += f" {zip_code}"

            # Try expandedprofile first for most comprehensive data
            # Falls back to detail, then basicprofile if needed
            # expandedprofile requires address1 and address2 as separate parameters
            url = f"{self.BASE_URL_V1}/property/expandedprofile"
            params = {
                "address1": address.strip(),
                "address2": f"{city}, {state}" + (f" {zip_code}" if zip_code else ""),
                "debug": "True",  # Include all fields, even null ones
            }

            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    # Log response structure for debugging
                    logger.info(
                        f"expandedprofile response keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}"
                    )
                    if isinstance(data, dict) and "property" in data:
                        prop_list = data.get("property", [])
                        if prop_list and len(prop_list) > 0:
                            first_prop = prop_list[0]
                            logger.info(
                                f"Property keys: {list(first_prop.keys())[:20]}"
                            )
                            # Check for architectural style in various locations
                            building = first_prop.get("building", {})
                            summary = first_prop.get("summary", {})
                            logger.info(
                                f"Building keys: {list(building.keys())[:15] if building else 'no building'}"
                            )
                            logger.info(
                                f"Summary keys: {list(summary.keys())[:15] if summary else 'no summary'}"
                            )
                            # Check for school data
                            school_data = first_prop.get("school") or first_prop.get(
                                "schools"
                            )
                            logger.info(
                                f"School data present: {school_data is not None}"
                            )

                    parsed = self._parse_property_detail(data)
                    if parsed:
                        logger.info(
                            "Successfully retrieved property from expandedprofile endpoint"
                        )
                        logger.info(
                            f"Extracted fields - architectural_style: {parsed.architectural_style}, "
                            f"school_district: {parsed.school_district}, condition: {parsed.condition}, "
                            f"seller_concessions: {parsed.seller_concessions}"
                        )
                        return parsed

                # Try detail endpoint if expandedprofile didn't work
                if response.status_code == 404:
                    logger.info("expandedprofile returned 404, trying detail endpoint")
                    return self._try_detail_endpoint(address, city, state, zip_code)

                # Try basicprofile as last resort
                if response.status_code not in [200, 404]:
                    logger.info(
                        f"expandedprofile returned {response.status_code}, trying basicprofile"
                    )
                    url = f"{self.BASE_URL_V1}/property/basicprofile"
                    params = {"address": full_address.strip(), "debug": "True"}
                    response = requests.get(
                        url, headers=headers, params=params, timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return self._parse_property_detail(data)

                # If we get here, log the error but don't raise yet
                logger.warning(
                    f"expandedprofile returned {response.status_code}: {response.text[:200]}"
                )
            except Exception as e:
                logger.error(f"Error calling expandedprofile: {e}")
                # Fall through to try other endpoints

            # Try detail endpoint as fallback
            logger.info("Trying detail endpoint as fallback")
            detail_result = self._try_detail_endpoint(address, city, state, zip_code)
            if detail_result:
                return detail_result

            # Last resort: basicprofile
            logger.info("Trying basicprofile as last resort")
            url = f"{self.BASE_URL_V1}/property/basicprofile"
            params = {"address": full_address.strip(), "debug": "True"}
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_property_detail(data)
            except Exception as e:
                logger.error(f"Error calling basicprofile: {e}")

            return None
        except Exception as e:
            logger.error(f"Error getting property by address: {e}")
            return None

    def _try_detail_endpoint(
        self, address: str, city: str, state: str, zip_code: Optional[str] = None
    ) -> Optional[Property]:
        """Try property detail endpoint as fallback."""
        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }

            # Try with address1/address2 format first (for detail endpoint)
            url = f"{self.BASE_URL_V1}/property/detail"
            params = {
                "address1": address.strip(),
                "address2": f"{city}, {state}" + (f" {zip_code}" if zip_code else ""),
                "debug": "True",  # Include all fields, even null ones
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                parsed = self._parse_property_detail(data)
                if parsed:
                    logger.info("Successfully retrieved property from detail endpoint")
                    return parsed

            # If address1/address2 format didn't work, try single address parameter
            if response.status_code == 404:
                full_address = address
                if city:
                    full_address += f", {city}"
                if state:
                    full_address += f", {state}"
                if zip_code:
                    full_address += f" {zip_code}"

                params = {"address": full_address.strip(), "debug": "True"}
                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_property_detail(data)

            response.raise_for_status()
            return None
        except Exception as e:
            logger.error(f"Error in detail endpoint: {e}")
            return None

    def get_sales_comparables(
        self,
        address: str,
        city: str,
        state: str,
        zip_code: Optional[str] = None,
        miles: float = 5.0,
        min_comps: int = 1,
        max_comps: int = 10,
        bedrooms_range: Optional[int] = None,
        bathroom_range: Optional[float] = None,
        sqft_range: Optional[int] = None,
        sale_date_range_months: int = 6,
        sale_amount_from: Optional[float] = None,
        sale_amount_to: Optional[float] = None,
        year_built_range: Optional[int] = None,
    ) -> List[Property]:
        """Get sales comparables using ATTOM's Sales Comparables endpoint."""
        if not self.connected:
            raise ConnectionError("Not connected to ATTOM API")

        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }

            # ATTOM v2 Sales Comparables endpoint format:
            # /SalesComparables/Address/{address}/{city}/-/{state}/{zip}
            # Clean address - use just street address, not full formatted
            street_address = (
                address.split(",")[0].strip() if "," in address else address.strip()
            )
            address_encoded = requests.utils.quote(street_address)

            # Ensure city and state are provided - use defaults if empty
            city_clean = city.strip() if city else "Mesa"  # Default fallback
            city_encoded = requests.utils.quote(city_clean) if city_clean else "-"

            state_clean = state.strip() if state else "AZ"  # Default to AZ
            state_encoded = requests.utils.quote(state_clean) if state_clean else "-"

            zip_encoded = zip_code.strip() if zip_code else "-"

            # Build URL - ATTOM format requires all parameters
            url = f"{self.BASE_URL_V2}/SalesComparables/Address/{address_encoded}/{city_encoded}/-/{state_encoded}/{zip_encoded}"

            params = {
                "searchType": "Radius",
                "minComps": min_comps,
                "maxComps": max_comps,
                "debug": "True",  # Include all fields, even null ones
                "miles": miles,
                "saleDateRange": sale_date_range_months,
            }

            # ATTOM parameters for finding similar properties
            # Only add filters if we have the data - make it more lenient
            if bedrooms_range is not None:
                params["bedroomsRange"] = bedrooms_range
            if bathroom_range is not None:
                params["bathroomRange"] = bathroom_range
            if sqft_range:
                # Use ±30% tolerance for square footage
                sqft_tolerance = max(
                    int(sqft_range * 0.3), 200
                )  # At least 200 sqft tolerance
                params["sqFeetRange"] = sqft_tolerance
            # Don't use price filters if they're too low (assessed value issue)
            # Only add price filters if they seem reasonable (above $50k)
            if sale_amount_from and sale_amount_from > 50000:
                params["saleAmountRangeFrom"] = int(sale_amount_from)
            if sale_amount_to and sale_amount_to > 50000:
                params["saleAmountRangeTo"] = int(sale_amount_to)
            if year_built_range:
                params["yearBuiltRange"] = year_built_range

            logger.info(f"ATTOM API URL: {url}")
            logger.info(f"ATTOM API Params: {params}")

            response = requests.get(url, headers=headers, params=params, timeout=30)

            # Log response status
            logger.info(f"ATTOM API Response Status: {response.status_code}")

            # Accept 200 (OK) and 206 (Partial Content) as valid responses
            # 206 is used when the API returns partial data, which is still usable
            if response.status_code not in [200, 206]:
                logger.error(
                    f"ATTOM API Error {response.status_code}: {response.text[:500]}"
                )
                # Try to parse error response
                try:
                    error_data = response.json()
                    error_msg = (
                        error_data.get("Response", {})
                        .get("status", {})
                        .get("msg", "Unknown error")
                    )
                    logger.error(f"ATTOM Error Message: {error_msg}")
                except:
                    pass
                return []

            # For 206, log a warning but still process the response
            if response.status_code == 206:
                logger.warning(
                    "ATTOM API returned 206 (Partial Content) - response may be incomplete"
                )

            data = response.json()
            logger.info(
                f"ATTOM API Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
            )

            # Check for error status in the response data itself
            response_group = data.get("RESPONSE_GROUP", {})
            response_obj = response_group.get("RESPONSE", {})

            # Check for STATUS in PRODUCT_INFO_ext (common location for comp errors)
            property_info = response_group.get("RESPONSE_DATA", {}).get(
                "PROPERTY_INFORMATION_RESPONSE_ext", {}
            )
            subject_prop = property_info.get("SUBJECT_PROPERTY_ext", {})
            prop_array = subject_prop.get("PROPERTY", [])
            if prop_array and len(prop_array) > 0:
                first_prop = prop_array[0]
                product_info = first_prop.get("PRODUCT_INFO_ext", {})
                status_obj = product_info.get("STATUS", {})
                if status_obj:
                    status_code = status_obj.get("@_Code", "")
                    status_condition = status_obj.get("@_Condition", "")
                    status_msg = status_obj.get("@_Description", "") or status_obj.get(
                        "@_Message", ""
                    )
                    if status_condition == "MinimumCompsNotMet" or status_code == "29":
                        logger.warning(
                            f"ATTOM API: Minimum comparables not met. {status_msg}"
                        )
                        logger.info(
                            "This usually means there aren't enough recent sales in the area matching the criteria."
                        )
                        logger.info(
                            "Consider: increasing search radius, extending sale date range, or relaxing filters."
                        )
                        # Return empty list but don't treat as error - it's a data availability issue
                        return []

            # Also check top-level STATUS
            status_obj = response_obj.get("STATUS", {})
            if status_obj:
                status_code = status_obj.get("@_Code", "")
                status_msg = status_obj.get("@_Description", "") or status_obj.get(
                    "@_Message", ""
                )
                if status_code and status_code not in ["200", "0", "1"]:
                    logger.warning(
                        f"ATTOM response contains status code {status_code}: {status_msg}"
                    )
                elif status_msg and "error" in status_msg.lower():
                    logger.warning(f"ATTOM response indicates error: {status_msg}")

            # Save full response to file for debugging
            import json
            from pathlib import Path

            debug_file = Path("attom_response_debug.json")
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Full ATTOM response saved to: {debug_file}")

            # Log response structure for debugging
            response_str = json.dumps(data, indent=2)
            logger.info(
                f"ATTOM Response sample (first 3000 chars): {response_str[:3000]}"
            )

            # Also log all top-level keys and nested structure
            if isinstance(data, dict) and "RESPONSE_GROUP" in data:
                rg = data["RESPONSE_GROUP"]
                if isinstance(rg, dict) and "RESPONSE" in rg:
                    resp = rg["RESPONSE"]
                    if isinstance(resp, dict) and "RESPONSE_DATA" in resp:
                        rd = resp["RESPONSE_DATA"]
                        logger.info(
                            f"RESPONSE_DATA keys: {list(rd.keys()) if isinstance(rd, dict) else 'not dict'}"
                        )
                        if (
                            isinstance(rd, dict)
                            and "PROPERTY_INFORMATION_RESPONSE_ext" in rd
                        ):
                            pir = rd["PROPERTY_INFORMATION_RESPONSE_ext"]
                            logger.info(
                                f"PROPERTY_INFORMATION_RESPONSE_ext keys: {list(pir.keys()) if isinstance(pir, dict) else 'not dict'}"
                            )

                            # Check each key to see what it contains
                            for key in pir.keys():
                                value = pir[key]
                                if isinstance(value, dict):
                                    logger.info(
                                        f"  {key} (dict) has keys: {list(value.keys())[:15]}"
                                    )
                                    # Check if it has PROPERTY array
                                    if "PROPERTY" in value:
                                        prop_array = value["PROPERTY"]
                                        logger.info(
                                            f"    -> Found PROPERTY array with {len(prop_array) if isinstance(prop_array, list) else 'not list'} items"
                                        )
                                elif isinstance(value, list):
                                    logger.info(
                                        f"  {key} (list) has {len(value)} items"
                                    )
                                    if len(value) > 0 and isinstance(value[0], dict):
                                        logger.info(
                                            f"    -> First item keys: {list(value[0].keys())[:10]}"
                                        )

            comparables = self._parse_comparables_response(data)

            # Also try to extract subject property from v2 response for better data
            # This can be used to enhance the subject property if needed
            subject_from_v2 = self._extract_subject_from_v2_response(data)
            if subject_from_v2:
                # Store in a class variable so it can be accessed later
                self._last_subject_from_v2 = subject_from_v2
                logger.info(
                    f"Stored v2 subject in connector: address={subject_from_v2.address}, "
                    f"lot={subject_from_v2.lot_size_sqft}, rooms={subject_from_v2.total_rooms}, "
                    f"parking={subject_from_v2.parking_spaces}"
                )
            else:
                logger.warning("Failed to extract v2 subject from response")

            return comparables
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting sales comparables: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text[:500]}")
            return []
        except Exception as e:
            logger.error(f"Error getting sales comparables: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return []

    def _parse_property_detail(self, data: Dict[str, Any]) -> Optional[Property]:
        """Parse ATTOM property detail response."""
        try:
            properties = data.get("property", [])
            if not properties:
                return None

            prop = properties[0]
            identifier = prop.get("identifier", {})
            summary = prop.get("summary", {})
            building = prop.get("building", {})
            building_size = building.get("size", {}) if building else {}
            assessment = prop.get("assessment", {})
            address_data = prop.get("address", {})
            # Best-effort descriptive text (ATTOM often places remarks in descriptionExt/legal1)
            property_description = (
                summary.get("descriptionExt")
                or summary.get("legal1")
                or summary.get("codeExt")
                or summary.get("description")
            )

            # Extract address components
            street = address_data.get("oneLine", "") or address_data.get("line1", "")
            # If oneLine includes full address, extract just street
            if "," in street:
                street = street.split(",")[0].strip()
            city = address_data.get("city", "") or address_data.get("locality", "")
            state = (
                address_data.get("state", "")
                or address_data.get("stateProvince", "")
                or address_data.get("countrySubd", "")
            )
            zip_code = (
                address_data.get("postal1", "")
                or address_data.get("zip", "")
                or address_data.get("postalCode", "")
            )

            # If city/state still empty, try parsing from oneLine
            if not city and address_data.get("oneLine"):
                parts = address_data.get("oneLine", "").split(",")
                if len(parts) >= 2:
                    city = parts[1].strip() if not city else city
                if len(parts) >= 3:
                    state_zip = parts[2].strip().split()
                    if len(state_zip) >= 1 and not state:
                        state = state_zip[0]
                    if len(state_zip) >= 2 and not zip_code:
                        zip_code = state_zip[1]

            # Extract property details
            property_type_str = summary.get("propertyType", summary.get("propType", ""))
            property_type = self._map_property_type(property_type_str)

            year_built = summary.get("yearBuilt")
            if year_built:
                try:
                    year_built = int(year_built)
                except:
                    year_built = None

            square_feet = building_size.get("livingSize") or building_size.get(
                "bldgSize"
            )
            if square_feet:
                try:
                    square_feet = int(square_feet)
                except:
                    square_feet = None

            bedrooms = building.get("rooms", {}).get("beds")
            if bedrooms:
                try:
                    bedrooms = int(bedrooms)
                    # Treat 0 as None for residential properties (likely missing data)
                    if bedrooms == 0 and property_type == PropertyType.RESIDENTIAL:
                        bedrooms = None
                except:
                    bedrooms = None

            bathrooms = building.get("rooms", {}).get("baths")
            if bathrooms:
                try:
                    bathrooms = float(bathrooms)
                    # Treat 0 as None for residential properties (likely missing data)
                    if bathrooms == 0.0 and property_type == PropertyType.RESIDENTIAL:
                        bathrooms = None
                except:
                    bathrooms = None

            # Extract additional room details
            rooms_data = building.get("rooms", {})
            total_rooms = rooms_data.get("totalRooms") or rooms_data.get("roomsTotal")
            if total_rooms:
                try:
                    total_rooms = int(total_rooms)
                except:
                    total_rooms = None

            bathrooms_full = rooms_data.get("bathsFull") or rooms_data.get(
                "bathroomsFull"
            )
            if bathrooms_full:
                try:
                    bathrooms_full = int(bathrooms_full)
                except:
                    bathrooms_full = None

            bathrooms_half = rooms_data.get("bathsHalf") or rooms_data.get(
                "bathroomsHalf"
            )
            if bathrooms_half:
                try:
                    bathrooms_half = int(bathrooms_half)
                except:
                    bathrooms_half = None

            # Extract lot information
            lot_size_sqft = None
            lot_size_acres = None
            lot = prop.get("lot", {})
            if lot:
                lot_size_sqft = (
                    lot.get("lotSize1") or lot.get("lotSizeSqFt") or lot.get("size1")
                )
                if lot_size_sqft:
                    try:
                        lot_size_sqft = float(lot_size_sqft)
                        if lot_size_sqft > 0:
                            # Convert to acres (1 acre = 43,560 sqft)
                            lot_size_acres = lot_size_sqft / 43560.0
                    except:
                        lot_size_sqft = None

                # Also check for acres directly
                if not lot_size_acres:
                    lot_size_acres = (
                        lot.get("lotSize2")
                        or lot.get("lotSizeAcres")
                        or lot.get("size2")
                    )
                    if lot_size_acres:
                        try:
                            lot_size_acres = float(lot_size_acres)
                        except:
                            lot_size_acres = None

            # Extract stories
            stories = building.get("stories") or building.get("storyCount")
            if stories:
                try:
                    stories = int(stories)
                except:
                    stories = None

            # Extract parking information
            parking_spaces = None
            garage_type = None
            parking = building.get("parking", {})
            if parking:
                parking_spaces = (
                    parking.get("prkgSpaces")
                    or parking.get("spaces")
                    or parking.get("totalSpaces")
                )
                if parking_spaces:
                    try:
                        parking_spaces = int(parking_spaces)
                    except:
                        parking_spaces = None
                garage_type = (
                    parking.get("prkgType")
                    or parking.get("type")
                    or parking.get("garageType")
                )

            # Extract heating/cooling
            heating_type = None
            cooling_type = None
            utilities = building.get("utilities", {})
            if utilities:
                heating_type = utilities.get("heating") or utilities.get("heatingType")
                cooling_type = utilities.get("cooling") or utilities.get("coolingType")

            # Extract roof material
            roof_material = None
            roof = building.get("roof", {})
            if roof:
                roof_material = (
                    roof.get("material") or roof.get("roofMaterial") or roof.get("type")
                )

            # Extract amenities and features
            amenities_list = []
            exterior_features_list = []
            features_data = building.get("features", [])
            if features_data:
                if not isinstance(features_data, list):
                    features_data = [features_data]
                for feature in features_data:
                    if isinstance(feature, dict):
                        feature_type = feature.get("type", "")
                        feature_desc = feature.get("description", "") or feature.get(
                            "text", ""
                        )
                        if feature_type and "amenity" in feature_type.lower():
                            amenities_list.append(feature_desc or feature_type)
                        elif feature_desc:
                            exterior_features_list.append(feature_desc)

            # Also check for amenities in other locations
            amenity_data = building.get("amenities", [])
            if amenity_data:
                if not isinstance(amenity_data, list):
                    amenity_data = [amenity_data]
                for amenity in amenity_data:
                    if isinstance(amenity, dict):
                        amenity_type = amenity.get("type", "") or amenity.get(
                            "name", ""
                        )
                        if amenity_type:
                            amenities_list.append(amenity_type)

            # Extract architectural style (if available in v1 API)
            architectural_style = None
            # Check multiple possible locations for architectural style
            if building:
                architectural_style = (
                    building.get("architecturalStyle")
                    or building.get("style")
                    or building.get("architecturalType")
                    or summary.get("architecturalStyle")
                    or summary.get("style")
                )
                if architectural_style:
                    logger.debug(f"Found architectural_style: {architectural_style}")
                else:
                    logger.debug("architectural_style not found in building or summary")

            # Extract school district (if available in v1 API)
            # Note: School district may require School API endpoint for full details
            school_district = None
            school_data = prop.get("school", {}) or prop.get("schools", {})
            if school_data:
                if isinstance(school_data, dict):
                    school_district = (
                        school_data.get("districtName")
                        or school_data.get("district")
                        or school_data.get("schoolDistrict")
                    )
                elif isinstance(school_data, list) and len(school_data) > 0:
                    # If it's a list, get district from first school
                    first_school = school_data[0]
                    if isinstance(first_school, dict):
                        school_district = (
                            first_school.get("districtName")
                            or first_school.get("district")
                            or first_school.get("schoolDistrict")
                        )
            if school_district:
                logger.debug(f"Found school_district: {school_district}")
            else:
                logger.debug(
                    "school_district not found - may require School API endpoint"
                )

            # Extract condition (if available)
            condition = None
            if building:
                condition = (
                    building.get("condition")
                    or building.get("propertyCondition")
                    or building.get("overallCondition")
                    or summary.get("condition")
                    or summary.get("propertyCondition")
                )

            # Extract renovation year (if available)
            renovation_year = None
            if building:
                renovation_year_str = (
                    building.get("renovationYear")
                    or building.get("lastRenovationYear")
                    or building.get("yearRenovated")
                    or summary.get("renovationYear")
                )
                if renovation_year_str:
                    try:
                        renovation_year = int(renovation_year_str)
                    except:
                        pass

            # Get price - prioritize sale price, then market value, then assessed value
            list_price = None
            sold_price = None
            sold_date = None
            sale_recency_days = None
            seller_concessions = None
            seller_concessions_description = None
            financing_type = None
            arms_length_transaction = None

            sale = prop.get("sale", {})
            if sale:
                sale_amount = sale.get("amount", {})
                if isinstance(sale_amount, dict):
                    sale_amount = sale_amount.get("saleamt", sale_amount.get("amount"))
                if sale_amount:
                    try:
                        sold_price = float(sale_amount)
                        list_price = sold_price  # Use as list_price too
                    except:
                        pass

                # Extract sale date
                sale_date_str = sale.get("date", "") or sale.get("saleDate", "")
                if sale_date_str:
                    try:
                        if isinstance(sale_date_str, str):
                            # Try various date formats
                            for fmt in [
                                "%Y-%m-%d",
                                "%m/%d/%Y",
                                "%Y%m%d",
                                "%Y-%m-%dT%H:%M:%S",
                            ]:
                                try:
                                    sold_date = datetime.strptime(
                                        sale_date_str.split("T")[0], fmt.split("T")[0]
                                    )
                                    break
                                except:
                                    continue
                        if sold_date:
                            sale_recency_days = (datetime.now() - sold_date).days
                    except:
                        pass

                # Extract seller concessions (if available)
                seller_concessions = sale.get("sellerConcessions") or sale.get(
                    "concessions"
                )
                if seller_concessions:
                    try:
                        seller_concessions = float(seller_concessions)
                        logger.debug(f"Found seller_concessions: {seller_concessions}")
                    except:
                        seller_concessions = None
                else:
                    logger.debug("seller_concessions not found in sale data")

                seller_concessions_description = (
                    sale.get("sellerConcessionsDescription")
                    or sale.get("concessionsDescription")
                    or sale.get("concessionsNotes")
                )
                if seller_concessions_description:
                    logger.debug(
                        f"Found seller_concessions_description: {seller_concessions_description}"
                    )

                # Extract financing type
                financing_type = (
                    sale.get("financingType")
                    or sale.get("loanType")
                    or sale.get("financing")
                )

                # Extract arms-length transaction indicator
                arms_length = sale.get("armsLength") or sale.get(
                    "armsLengthTransaction"
                )
                if arms_length is not None:
                    if isinstance(arms_length, bool):
                        arms_length_transaction = arms_length
                    elif isinstance(arms_length, str):
                        arms_length_transaction = arms_length.upper() in [
                            "A",
                            "Y",
                            "YES",
                            "TRUE",
                            "1",
                        ]

            # If no sale price, try market value, then assessed value
            if not list_price and assessment:
                assessed = assessment.get("assessed", {})
                market = assessment.get("market", {})
                # Prefer market value over assessed value
                market_value = market.get("mktTtlValue")
                assessed_value = assessed.get("assdTtlValue")
                tax_year = assessment.get("tax", {}).get("taxYear")

                if market_value:
                    try:
                        market_value = float(market_value)
                        # Only use if reasonable (above $50k)
                        if market_value > 50000:
                            list_price = market_value
                    except:
                        pass

                # Fall back to assessed value if market value not available
                if not list_price and assessed_value:
                    try:
                        assessed_value = float(assessed_value)
                        # Only use if reasonable (above $50k)
                        if assessed_value > 50000:
                            list_price = assessed_value
                    except:
                        pass

            # Calculate price per sqft
            price_per_sqft = None
            if sold_price and square_feet:
                price_per_sqft = sold_price / square_feet
            elif list_price and square_feet:
                price_per_sqft = list_price / square_feet

            # Generate Google Street View URLs if coordinates available
            street_view_url = None
            street_view_image_url = None
            lat = address_data.get("latitude") or (
                prop.get("location", {}).get("latitude")
                if isinstance(prop.get("location"), dict)
                else None
            )
            lon = address_data.get("longitude") or (
                prop.get("location", {}).get("longitude")
                if isinstance(prop.get("location"), dict)
                else None
            )
            if lat and lon:
                try:
                    lat_float = float(lat)
                    lon_float = float(lon)
                    # Interactive Street View link
                    street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat_float},{lon_float}"

                    # Static Street View image (if API key available)
                    if settings.google_maps_api_key:
                        street_view_image_url = (
                            f"https://maps.googleapis.com/maps/api/streetview?"
                            f"size=600x400&location={lat_float},{lon_float}&fov=90&heading=0&pitch=0"
                            f"&key={settings.google_maps_api_key}"
                        )
                    else:
                        # Fallback without API key
                        street_view_image_url = (
                            f"https://maps.googleapis.com/maps/api/streetview?"
                            f"size=600x400&location={lat_float},{lon_float}&fov=90&heading=0&pitch=0"
                        )
                except:
                    pass

            # Log extracted data for debugging
            logger.info(
                f"Extracted property from v1 API - architectural_style={architectural_style}, "
                f"school_district={school_district}, condition={condition}, "
                f"renovation_year={renovation_year}, seller_concessions={seller_concessions}, "
                f"financing_type={financing_type}, arms_length={arms_length_transaction}"
            )

            # Add richer metadata for downstream UI/reporting
            mls_meta = {}
            if isinstance(prop, dict):
                mls_meta = dict(prop)
            mls_meta.update(
                {
                    "property_description": property_description,
                    "assessment_market_value": (
                        market_value if "market_value" in locals() else None
                    ),
                    "assessment_assessed_value": (
                        assessed_value if "assessed_value" in locals() else None
                    ),
                    "tax_year": tax_year if "tax_year" in locals() else None,
                    "data_source": "ATTOM v1 expandedprofile/detail",
                }
            )

            return Property(
                mls_number=identifier.get("apn", identifier.get("parcelNumber", "")),
                address=street,
                city=city,
                state=state,
                zip_code=zip_code,
                property_type=property_type,
                status=PropertyStatus.SOLD if sold_price else PropertyStatus.ACTIVE,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                bathrooms_full=bathrooms_full,
                bathrooms_half=bathrooms_half,
                total_rooms=total_rooms,
                square_feet=square_feet,
                lot_size_sqft=lot_size_sqft,
                lot_size_acres=lot_size_acres,
                year_built=year_built,
                stories=stories,
                parking_spaces=parking_spaces,
                garage_type=garage_type,
                architectural_style=architectural_style,
                condition=condition,
                renovation_year=renovation_year,
                heating_type=heating_type,
                cooling_type=cooling_type,
                roof_material=roof_material,
                exterior_features=exterior_features_list,
                amenities=amenities_list,
                description=property_description,
                school_district=school_district,
                list_price=list_price,
                sold_price=sold_price,
                sold_date=sold_date,
                sale_recency_days=sale_recency_days,
                price_per_sqft=price_per_sqft,
                seller_concessions=seller_concessions,
                seller_concessions_description=seller_concessions_description,
                financing_type=financing_type,
                arms_length_transaction=arms_length_transaction,
                latitude=lat,
                longitude=lon,
                street_view_url=street_view_url,
                street_view_image_url=street_view_image_url,
                mls_data=mls_meta,
            )
        except Exception as e:
            logger.error(f"Error parsing ATTOM property detail: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _parse_comparables_response(self, data: Dict[str, Any]) -> List[Property]:
        """Parse ATTOM Sales Comparables response.

        ATTOM v2 API response structure:
        RESPONSE_GROUP -> RESPONSE -> RESPONSE_DATA -> PROPERTY_INFORMATION_RESPONSE_ext -> SUBJECT_PROPERTY_ext -> PROPERTY array

        The PROPERTY array contains:
        - Index 0: Subject property with @Product_ext: "SalesCompSubjectProperty"
        - Index 1+: Comparable properties with @Product_ext: "SalesCompProperties" and COMPARABLE_PROPERTY_ext nested inside
        """
        properties = []

        try:
            response_group = data.get("RESPONSE_GROUP", {})
            response = response_group.get("RESPONSE", {})
            response_data = response.get("RESPONSE_DATA", {})
            property_info = response_data.get("PROPERTY_INFORMATION_RESPONSE_ext", {})

            # The correct location: SUBJECT_PROPERTY_ext.PROPERTY array
            # First item is subject, rest are comparables
            subject_prop_ext = property_info.get("SUBJECT_PROPERTY_ext", {})
            comps = []

            if isinstance(subject_prop_ext, dict):
                prop_array = subject_prop_ext.get("PROPERTY", [])

                if isinstance(prop_array, list) and len(prop_array) > 1:
                    # Skip first item (subject), process rest as comparables
                    for item in prop_array[1:]:  # Skip first (subject)
                        if isinstance(item, dict):
                            # Check product type to confirm it's a comparable
                            product_info = item.get("PRODUCT_INFO_ext", {})
                            product_type = product_info.get("@Product_ext", "")

                            # Extract COMPARABLE_PROPERTY_ext if it exists
                            comp_prop = item.get("COMPARABLE_PROPERTY_ext")
                            if comp_prop and isinstance(comp_prop, dict):
                                # Use the nested COMPARABLE_PROPERTY_ext object
                                comps.append(comp_prop)
                            elif product_type == "SalesCompProperties":
                                # Use the item itself if it's marked as a comparable
                                comps.append(item)
                            else:
                                # Fallback: use item if it has comparable-like structure
                                if (
                                    "@DistanceFromSubjectPropertyMilesCount" in item
                                    or "COMPARABLE_PROPERTY_ext" in item
                                ):
                                    comp_prop = item.get("COMPARABLE_PROPERTY_ext")
                                    comps.append(comp_prop if comp_prop else item)

                    if comps:
                        logger.info(
                            f"Found {len(comps)} comparables in SUBJECT_PROPERTY_ext.PROPERTY array (skipped first item which is subject)"
                        )

            # Fallback: Try direct COMPARABLE_PROPERTY_ext in property_info (unlikely but possible)
            if not comps:
                comps_raw = property_info.get("COMPARABLE_PROPERTY_ext")
                if comps_raw:
                    if isinstance(comps_raw, list):
                        comps = comps_raw
                    elif isinstance(comps_raw, dict):
                        # Check if it has a PROPERTY array
                        prop_array = comps_raw.get("PROPERTY", [])
                        if isinstance(prop_array, list):
                            comps = prop_array
                        else:
                            comps = [comps_raw]
                    logger.info(
                        f"Found {len(comps)} comparables in COMPARABLE_PROPERTY_ext"
                    )

            # Final fallback: Search all keys in property_info for PROPERTY arrays
            if not comps:
                for key in property_info.keys():
                    value = property_info[key]
                    if isinstance(value, dict) and "PROPERTY" in value:
                        prop_array = value.get("PROPERTY", [])
                        if isinstance(prop_array, list) and len(prop_array) > 1:
                            # Check if first item is subject (has @Product_ext: "SalesCompSubjectProperty")
                            first_item = prop_array[0] if prop_array else {}
                            product_info = (
                                first_item.get("PRODUCT_INFO_ext", {})
                                if isinstance(first_item, dict)
                                else {}
                            )
                            product_type = (
                                product_info.get("@Product_ext", "")
                                if isinstance(product_info, dict)
                                else ""
                            )

                            if product_type == "SalesCompSubjectProperty":
                                # Skip first (subject), use rest
                                comps = []
                                for item in prop_array[1:]:
                                    if isinstance(item, dict):
                                        comp_prop = item.get("COMPARABLE_PROPERTY_ext")
                                        comps.append(comp_prop if comp_prop else item)
                                if comps:
                                    logger.info(
                                        f"Found {len(comps)} comparables in {key}.PROPERTY array"
                                    )
                                    break

            if not comps:
                logger.warning("No comparables found in response structure")
                logger.info(
                    f"property_info keys: {list(property_info.keys()) if property_info else 'None'}"
                )
                return []

            logger.info(f"Processing {len(comps)} comparable properties")

            for comp in comps:
                if not isinstance(comp, dict):
                    logger.warning(f"Skipping non-dict comparable: {type(comp)}")
                    continue

                prop = self._parse_comparable_property_v2(comp)
                if prop:
                    properties.append(prop)
                    # Debug: log first property details
                    if len(properties) == 1:
                        logger.debug(
                            f"First comp parsed: sqft={prop.square_feet}, beds={prop.bedrooms}, apn={prop.mls_number}"
                        )
        except Exception as e:
            logger.error(f"Error parsing comparables response: {e}")
            import traceback

            traceback.print_exc()

        return properties

    def _parse_comparable_property_v2(self, comp: Dict[str, Any]) -> Optional[Property]:
        """Parse a single comparable property from ATTOM v2 API response."""
        try:
            # ATTOM v2 COMPARABLE_PROPERTY_ext structure:
            # Address info is at top level with @ attributes
            # SALES_HISTORY contains sale info
            # STRUCTURE contains building details
            # _IDENTIFICATION contains APN and coordinates

            # Extract address from top-level attributes
            street = comp.get("@_StreetAddress", "") or comp.get("StreetAddress", "")
            city = comp.get("@_City", "") or comp.get("City", "")
            state = comp.get("@_State", "") or comp.get("State", "")
            zip_code = comp.get("@_PostalCode", "") or comp.get("PostalCode", "")

            # Get distance if available
            distance = comp.get("@DistanceFromSubjectPropertyMilesCount")
            if distance:
                try:
                    distance = float(distance)
                except:
                    distance = None

            # Get property details from nested structures
            identification = comp.get("_IDENTIFICATION", {}) or comp.get(
                "IDENTIFICATION", {}
            )
            # For comparables, APN is typically in @RTPropertyID_ext, not @AssessorsParcelIdentifier
            # Subject properties have @AssessorsParcelIdentifier, comparables use @RTPropertyID_ext
            apn = (
                identification.get(
                    "@AssessorsParcelIdentifier", ""
                )  # Subject property format
                or identification.get(
                    "@RTPropertyID_ext", ""
                )  # Comparable property format (primary)
                or comp.get("@PropertyParcelID", "")  # Top-level fallback
                or identification.get(
                    "AssessorsParcelIdentifier", ""
                )  # Non-prefixed fallback
                or identification.get("@DQPropertyID_ext", "")  # Another fallback
            )

            # Get sale information from SALES_HISTORY
            sale_info = comp.get("SALES_HISTORY", {}) or comp.get("SALE", {})
            sold_price = None
            sold_date = None
            arms_length_transaction = None
            financing_type = None
            sale_recency_days = None
            seller_concessions = None
            seller_concessions_description = None

            if sale_info:
                # ATTOM v2 uses @PropertySalesAmount
                sold_price_str = (
                    sale_info.get("@PropertySalesAmount", "")
                    or sale_info.get("@_Amount", "")
                    or sale_info.get("@Amount", "")
                    or sale_info.get("Amount", "")
                )
                if sold_price_str:
                    try:
                        sold_price = float(sold_price_str)
                    except:
                        pass

                # ATTOM v2 uses @TransferDate_ext or @PropertySalesDate
                sold_date_str = (
                    sale_info.get("@TransferDate_ext", "")
                    or sale_info.get("@PropertySalesDate", "")
                    or sale_info.get("@_Date", "")
                    or sale_info.get("@Date", "")
                )
                if sold_date_str:
                    try:
                        # Handle ISO format with T (e.g., "2025-07-25T00:00:00")
                        if "T" in sold_date_str:
                            # Extract just the date part and parse it
                            date_part = sold_date_str.split("T")[0]
                            sold_date = datetime.strptime(date_part, "%Y-%m-%d")
                        else:
                            # Try various date formats
                            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"]:
                                try:
                                    sold_date = datetime.strptime(sold_date_str, fmt)
                                    break
                                except:
                                    continue
                    except Exception as e:
                        logger.debug(f"Error parsing sale date '{sold_date_str}': {e}")
                        pass

                # Extract transaction details
                arms_length = sale_info.get("@ArmsLengthTransactionIndicatorExt", "")
                if arms_length:
                    arms_length_transaction = arms_length.upper() in [
                        "A",
                        "Y",
                        "YES",
                        "TRUE",
                        "1",
                    ]
                else:
                    arms_length_transaction = None

                # Extract financing type from loans
                loans = sale_info.get("LOANS_ext", {})
                if loans:
                    loan_list = loans.get("LOAN_ext", [])
                    if loan_list and not isinstance(loan_list, list):
                        loan_list = [loan_list]
                    if loan_list and len(loan_list) > 0:
                        first_loan = loan_list[0]
                        if isinstance(first_loan, dict):
                            loan_type = first_loan.get("@_Type", "")
                            loan_amount = first_loan.get("@_Amount", "")
                            # If there's a loan, it's likely financed (not cash)
                            if (
                                loan_amount
                                and str(loan_amount).strip()
                                and str(loan_amount).strip() not in ["", "0"]
                            ):
                                try:
                                    amount_val = float(
                                        str(loan_amount).replace(",", "")
                                    )
                                    if amount_val > 0:
                                        financing_type = loan_type or "Financed"
                                    else:
                                        financing_type = "Cash"
                                except (ValueError, TypeError):
                                    financing_type = "Cash"
                            else:
                                financing_type = "Cash"

                    # Check for seller carryback (seller providing financing)
                    # Note: This is different from seller concessions (closing cost assistance)
                    # Seller carryback can be in LOANS_ext or in a separate LOAN_ext object
                    seller_carryback = loans.get("@SellerCarrybackindicator", "")
                    if not seller_carryback or str(seller_carryback).strip() in [
                        "0",
                        "",
                    ]:
                        # Also check for separate LOAN_ext object (not inside LOANS_ext)
                        loan_ext = sale_info.get("LOAN_ext", {})
                        if loan_ext and isinstance(loan_ext, dict):
                            seller_carryback = loan_ext.get(
                                "@SellerCarrybackindicator", ""
                            )

                    if (
                        seller_carryback
                        and str(seller_carryback).strip()
                        and str(seller_carryback).strip() not in ["0", ""]
                    ):
                        # Seller carryback indicates seller financing, which could be considered a form of concession
                        seller_concessions_description = "Seller financing/carryback"

                # Note: ATTOM v2 SalesComparables API does not provide seller concessions (closing cost assistance)
                # This would need to come from MLS data or other sources

                # Calculate sale recency
                sale_recency_days = None
                if sold_date:
                    try:
                        sale_recency_days = (datetime.now() - sold_date).days
                    except:
                        pass

            # Get lot information from SITE
            site = comp.get("SITE", {})
            lot_size_sqft = None
            lot_size_acres = None
            if site and isinstance(site, dict):
                lot_sqft_str = site.get("@LotSquareFeetCount", "")
                if (
                    lot_sqft_str
                    and str(lot_sqft_str).strip()
                    and str(lot_sqft_str).strip() not in ["", "0", "-1"]
                ):
                    try:
                        lot_size_sqft = float(str(lot_sqft_str).strip())
                        if lot_size_sqft > 0:
                            # Convert to acres (1 acre = 43,560 sqft)
                            lot_size_acres = lot_size_sqft / 43560.0
                    except (ValueError, TypeError):
                        pass

            # Get building details from STRUCTURE
            structure = comp.get("STRUCTURE", {}) or comp.get("BUILDING", {})
            square_feet = None
            bedrooms = None
            bathrooms = None
            bathrooms_full = None
            bathrooms_half = None
            total_rooms = None
            stories = None
            year_built = None
            parking_spaces = None
            garage_type = None
            heating_type = None
            cooling_type = None
            roof_material = None
            amenities_list = []
            exterior_features_list = []

            if structure and isinstance(structure, dict):
                # ATTOM v2 uses @GrossLivingAreaSquareFeetCount
                sqft_str = (
                    structure.get("@GrossLivingAreaSquareFeetCount")
                    or structure.get("@LivingAreaSquareFeetCount")
                    or (
                        structure.get("SIZE", {}).get("@_LivingArea", "")
                        if isinstance(structure.get("SIZE"), dict)
                        else None
                    )
                )
                # Check for empty string explicitly and try to parse
                if (
                    sqft_str is not None
                    and str(sqft_str).strip()
                    and str(sqft_str).strip() not in ["", "0", "-1", "null", "None"]
                ):
                    try:
                        sqft_val = float(str(sqft_str).strip())
                        if sqft_val > 0:  # Only use positive values
                            square_feet = int(sqft_val)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"Error parsing square feet '{sqft_str}': {e}")
                        pass

                # ATTOM v2 uses @TotalBedroomCount
                beds_str = structure.get("@TotalBedroomCount") or structure.get(
                    "@BedroomCount"
                )
                # Handle bedrooms - check if it's 0 and if TotalRoomCount suggests missing data
                if (
                    beds_str is not None
                    and str(beds_str).strip()
                    and str(beds_str).strip() not in ["", "null", "None"]
                ):
                    try:
                        beds_val = int(float(str(beds_str).strip()))
                        # If bedrooms is 0, check if TotalRoomCount suggests it's missing data
                        if beds_val == 0:
                            total_rooms_str = structure.get("@TotalRoomCount")
                            if (
                                total_rooms_str is not None
                                and str(total_rooms_str).strip()
                            ):
                                try:
                                    total_rooms = int(
                                        float(str(total_rooms_str).strip())
                                    )
                                    # If there are rooms but 0 bedrooms, likely missing data
                                    if total_rooms > 0:
                                        bedrooms = None  # Treat as missing
                                    else:
                                        bedrooms = 0  # Actually 0 bedrooms
                                except (ValueError, TypeError):
                                    bedrooms = 0  # Default to 0 if can't parse
                            else:
                                bedrooms = 0  # No room count info, assume 0 is valid
                        else:
                            bedrooms = beds_val  # Valid non-zero value
                    except (ValueError, TypeError):
                        pass

                # ATTOM v2 uses @TotalBathroomCount
                baths_str = structure.get("@TotalBathroomCount") or structure.get(
                    "@BathroomCount"
                )
                # Handle bathrooms - check if it's 0 and if TotalRoomCount suggests missing data
                if (
                    baths_str is not None
                    and str(baths_str).strip()
                    and str(baths_str).strip() not in ["", "null", "None"]
                ):
                    try:
                        baths_val = float(str(baths_str).strip())
                        # If bathrooms is 0, check if TotalRoomCount suggests it's missing data
                        if baths_val == 0.0:
                            total_rooms_str = structure.get("@TotalRoomCount")
                            if (
                                total_rooms_str is not None
                                and str(total_rooms_str).strip()
                            ):
                                try:
                                    total_rooms = int(
                                        float(str(total_rooms_str).strip())
                                    )
                                    # If there are rooms but 0 bathrooms, likely missing data
                                    if total_rooms > 0:
                                        bathrooms = None  # Treat as missing
                                    else:
                                        bathrooms = 0.0  # Actually 0 bathrooms
                                except (ValueError, TypeError):
                                    bathrooms = 0.0  # Default to 0 if can't parse
                            else:
                                bathrooms = 0.0  # No room count info, assume 0 is valid
                        else:
                            bathrooms = baths_val  # Valid non-zero value
                    except (ValueError, TypeError):
                        pass

                # Extract detailed bathroom counts
                baths_full_str = structure.get("@TotalBathroomFullCount_ext", "")
                if (
                    baths_full_str
                    and str(baths_full_str).strip()
                    and str(baths_full_str).strip() not in ["", "0"]
                ):
                    try:
                        bathrooms_full = int(float(str(baths_full_str).strip()))
                    except (ValueError, TypeError):
                        pass

                baths_half_str = structure.get("@TotalBathroomHalfCount_ext", "")
                if (
                    baths_half_str
                    and str(baths_half_str).strip()
                    and str(baths_half_str).strip() not in ["", "0"]
                ):
                    try:
                        bathrooms_half = int(float(str(baths_half_str).strip()))
                    except (ValueError, TypeError):
                        pass

                # Extract total rooms
                total_rooms_str = structure.get("@TotalRoomCount", "")
                if (
                    total_rooms_str
                    and str(total_rooms_str).strip()
                    and str(total_rooms_str).strip() not in ["", "0"]
                ):
                    try:
                        total_rooms = int(float(str(total_rooms_str).strip()))
                    except (ValueError, TypeError):
                        pass

                # Extract stories
                stories_str = structure.get("@StoriesCount", "")
                if (
                    stories_str
                    and str(stories_str).strip()
                    and str(stories_str).strip() not in ["", "0"]
                ):
                    try:
                        stories = int(float(str(stories_str).strip()))
                    except (ValueError, TypeError):
                        pass

                # Year built from STRUCTURE_ANALYSIS
                structure_analysis = structure.get("STRUCTURE_ANALYSIS", {})
                if structure_analysis:
                    year_str = structure_analysis.get(
                        "@PropertyStructureBuiltYear", ""
                    ) or structure_analysis.get("@YearBuilt", "")
                else:
                    year_str = structure.get("@YearBuilt", "")

                if year_str:
                    try:
                        year_built = int(year_str)
                    except:
                        pass

                # Extract parking information
                car_storage = structure.get("CAR_STORAGE", {})
                if car_storage:
                    car_location = car_storage.get("CAR_STORAGE_LOCATION", {})
                    if car_location:
                        parking_str = car_location.get("@_ParkingSpacesCount", "")
                        if (
                            parking_str
                            and str(parking_str).strip()
                            and str(parking_str).strip() not in ["", "0"]
                        ):
                            try:
                                parking_spaces = int(float(str(parking_str).strip()))
                            except (ValueError, TypeError):
                                pass
                        garage_type = car_location.get(
                            "@_Type", ""
                        ) or car_location.get("@_TypeOtherDescription", "")
                        if garage_type and str(garage_type).strip():
                            garage_type = str(garage_type).strip()
                        else:
                            garage_type = None

                # Extract heating/cooling
                heating = structure.get("HEATING", {})
                if heating:
                    heating_desc = heating.get("@_UnitDescription", "") or heating.get(
                        "@_TypeOtherDescription", ""
                    )
                    if (
                        heating_desc
                        and str(heating_desc).strip()
                        and str(heating_desc).strip().upper() not in ["NO", "NONE", ""]
                    ):
                        heating_type = str(heating_desc).strip()

                cooling = structure.get("COOLING", {})
                if cooling:
                    cooling_desc = cooling.get("@_UnitDescription", "") or cooling.get(
                        "@_TypeOtherDescription", ""
                    )
                    if cooling_desc and _is_valid_cooling_type(str(cooling_desc)):
                        cooling_desc = str(cooling_desc).strip()
                        if cooling_desc.upper() == "YES":
                            cooling_type = "Yes"
                        else:
                            cooling_type = cooling_desc

                # Extract roof material from exterior features
                exterior_features = structure.get("EXTERIOR_FEATURE", [])
                if exterior_features:
                    if not isinstance(exterior_features, list):
                        exterior_features = [exterior_features]
                    for feature in exterior_features:
                        if isinstance(feature, dict):
                            feature_type = feature.get("@_Type", "")
                            feature_desc = feature.get(
                                "@_Description", ""
                            ) or feature.get("@_TypeOtherDescription", "")
                            if feature_type == "Other" and "Roof" in (
                                feature_desc or ""
                            ):
                                # Filter out placeholder values
                                if feature_desc and _is_valid_roof_material(
                                    feature_desc
                                ):
                                    roof_material = feature_desc.strip()
                            elif feature_desc:
                                exterior_features_list.append(feature_desc)

                # Extract amenities
                amenities_data = structure.get("AMENITIES", {})
                if amenities_data:
                    amenity_list = amenities_data.get("AMENITY", [])
                    if amenity_list:
                        if not isinstance(amenity_list, list):
                            amenity_list = [amenity_list]
                        for amenity in amenity_list:
                            if isinstance(amenity, dict):
                                amenity_type = amenity.get("@_Type", "")
                                amenity_desc = amenity.get("@_DetailedDescription", "")
                                # Prefer @_Type, fallback to description
                                if amenity_type and str(amenity_type).strip():
                                    amenities_list.append(str(amenity_type).strip())
                                elif amenity_desc and str(amenity_desc).strip():
                                    amenities_list.append(str(amenity_desc).strip())
                else:
                    # Check for single AMENITY (not AMENITIES)
                    amenity = structure.get("AMENITY", {})
                    if amenity and isinstance(amenity, dict):
                        amenity_type = amenity.get("@_Type", "")
                        amenity_desc = amenity.get("@_DetailedDescription", "")
                        if amenity_type and str(amenity_type).strip():
                            amenities_list.append(str(amenity_type).strip())
                        elif amenity_desc and str(amenity_desc).strip():
                            amenities_list.append(str(amenity_desc).strip())

                # Remove duplicates and empty values
                amenities_list = list(
                    dict.fromkeys(
                        [a for a in amenities_list if a and len(a.strip()) > 0]
                    )
                )

            # Get coordinates from top level or identification
            lat = None
            lon = None
            lat_str = comp.get("@LatitudeNumber", "") or (
                identification.get("@LatitudeNumber", "") if identification else ""
            )
            lon_str = comp.get("@LongitudeNumber", "") or (
                identification.get("@LongitudeNumber", "") if identification else ""
            )
            if lat_str:
                try:
                    lat = float(lat_str)
                except:
                    pass
            if lon_str:
                try:
                    lon = float(lon_str)
                except:
                    pass

            # Generate Google Street View URLs if coordinates available
            street_view_url = None
            street_view_image_url = None
            if lat and lon:
                # Interactive Street View link
                street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"

                # Static Street View image (if API key available)
                if settings.google_maps_api_key:
                    street_view_image_url = (
                        f"https://maps.googleapis.com/maps/api/streetview?"
                        f"size=600x400&location={lat},{lon}&fov=90&heading=0&pitch=0"
                        f"&key={settings.google_maps_api_key}"
                    )
                else:
                    # Fallback to embeddable URL without API key (may have limitations)
                    street_view_image_url = (
                        f"https://maps.googleapis.com/maps/api/streetview?"
                        f"size=600x400&location={lat},{lon}&fov=90&heading=0&pitch=0"
                    )

            # Calculate price per sqft
            price_per_sqft = None
            if sold_price and square_feet:
                price_per_sqft = sold_price / square_feet

            # Try to extract architectural style (may not be available in SalesComparables v2)
            # Note: Architectural style is typically not available in SalesComparables endpoint
            # Would need to use property/detail or property/expandedprofile endpoint
            architectural_style = None

            # Extract school district (may not be available in SalesComparables v2)
            # Note: School district typically requires School API endpoint
            # Check if it's in the response structure
            school_district = None
            # ATTOM v2 SalesComparables doesn't include school district
            # Would need separate School API call: /school/district or /school/v4

            comp_description = (
                comp.get("@StandardUseDescription_ext")
                or comp.get("DESCRIPTION_ext")
                or comp.get("description")
            )
            mls_meta = {}
            if isinstance(comp, dict):
                mls_meta = dict(comp)
            mls_meta.update(
                {
                    "property_description": comp_description,
                    "data_source": "ATTOM v2 SalesComparables (comp)",
                }
            )

            return Property(
                mls_number=apn or "",
                address=street,
                city=city,
                state=state,
                zip_code=zip_code,
                property_type=self._map_property_type(
                    comp.get("@StandardUseCode_ext", "")
                    or comp.get("@StandardUseDescription_ext", "")
                ),
                status=PropertyStatus.SOLD if sold_price else PropertyStatus.ACTIVE,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                bathrooms_full=bathrooms_full,
                bathrooms_half=bathrooms_half,
                total_rooms=total_rooms,
                square_feet=square_feet,
                lot_size_sqft=lot_size_sqft,
                lot_size_acres=lot_size_acres,
                year_built=year_built,
                stories=stories,
                parking_spaces=parking_spaces,
                garage_type=garage_type,
                architectural_style=architectural_style,
                heating_type=heating_type,
                cooling_type=cooling_type,
                roof_material=roof_material,
                exterior_features=exterior_features_list,
                amenities=amenities_list,
                description=comp_description,
                school_district=school_district,
                sold_price=sold_price,
                sold_date=sold_date,
                sale_recency_days=sale_recency_days,
                price_per_sqft=price_per_sqft,
                seller_concessions=seller_concessions,
                seller_concessions_description=seller_concessions_description,
                arms_length_transaction=arms_length_transaction,
                financing_type=financing_type,
                latitude=lat,
                longitude=lon,
                street_view_url=street_view_url,
                street_view_image_url=street_view_image_url,
                mls_data=mls_meta,
            )
        except Exception as e:
            logger.error(f"Error parsing comparable property: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _extract_subject_from_v2_response(
        self, data: Dict[str, Any]
    ) -> Optional[Property]:
        """Extract subject property from ATTOM v2 Sales Comparables response."""
        try:
            response_group = data.get("RESPONSE_GROUP", {})
            response = response_group.get("RESPONSE", {})
            response_data = response.get("RESPONSE_DATA", {})
            property_info = response_data.get("PROPERTY_INFORMATION_RESPONSE_ext", {})
            subject_prop_ext = property_info.get("SUBJECT_PROPERTY_ext", {})

            if isinstance(subject_prop_ext, dict):
                prop_array = subject_prop_ext.get("PROPERTY", [])
                if isinstance(prop_array, list) and len(prop_array) > 0:
                    # First item is the subject property
                    subject_data = prop_array[0]
                    logger.info("Extracting subject property from v2 response...")
                    parsed = self._parse_subject_property_v2(subject_data)
                    if parsed:
                        logger.info(
                            f"Successfully extracted v2 subject: {parsed.address}, lot_sqft={parsed.lot_size_sqft}, "
                            f"rooms={parsed.total_rooms}, parking={parsed.parking_spaces}, stories={parsed.stories}, "
                            f"heating={parsed.heating_type}, cooling={parsed.cooling_type}"
                        )
                    else:
                        logger.warning("Failed to parse v2 subject property")
                    return parsed
                else:
                    logger.warning(
                        f"No PROPERTY array found or empty (found: {type(prop_array)})"
                    )
            else:
                logger.warning(
                    f"SUBJECT_PROPERTY_ext is not a dict (found: {type(subject_prop_ext)})"
                )
        except Exception as e:
            logger.error(f"Error extracting subject from v2 response: {e}")
            import traceback

            logger.error(traceback.format_exc())
        return None

    def _parse_subject_property_v2(
        self, subject_data: Dict[str, Any]
    ) -> Optional[Property]:
        """Parse subject property from ATTOM v2 response structure."""
        try:
            market_value = None
            assessed_value = None
            tax_year = None
            # Extract address
            street = subject_data.get("@_StreetAddress", "")
            city = subject_data.get("@_City", "")
            state = subject_data.get("@_State", "")
            zip_code = subject_data.get("@_PostalCode", "")

            # Get identification
            identification = subject_data.get("_IDENTIFICATION", {})
            apn = identification.get(
                "@AssessorsParcelIdentifier", ""
            ) or subject_data.get("@PropertyParcelID", "")

            # Get coordinates
            lat_str = identification.get("@LatitudeNumber", "") or subject_data.get(
                "@LatitudeNumber", ""
            )
            lon_str = identification.get("@LongitudeNumber", "") or subject_data.get(
                "@LongitudeNumber", ""
            )
            lat = float(lat_str) if lat_str else None
            lon = float(lon_str) if lon_str else None

            # Get lot information from SITE
            site = subject_data.get("SITE", {})
            lot_size_sqft = None
            lot_size_acres = None
            if site and isinstance(site, dict):
                lot_sqft_str = site.get("@LotSquareFeetCount", "")
                if (
                    lot_sqft_str
                    and str(lot_sqft_str).strip()
                    and str(lot_sqft_str).strip() not in ["", "0", "-1"]
                ):
                    try:
                        lot_size_sqft = float(str(lot_sqft_str).strip())
                        if lot_size_sqft > 0:
                            # Convert to acres (1 acre = 43,560 sqft)
                            lot_size_acres = lot_size_sqft / 43560.0
                    except (ValueError, TypeError):
                        pass

            # Get structure details
            structure = subject_data.get("STRUCTURE", {})
            square_feet = None
            bedrooms = None
            bathrooms = None
            bathrooms_full = None
            bathrooms_half = None
            total_rooms = None
            stories = None
            year_built = None
            parking_spaces = None
            garage_type = None
            heating_type = None
            cooling_type = None
            roof_material = None
            amenities_list = []
            exterior_features_list = []

            if structure and isinstance(structure, dict):
                sqft_str = structure.get("@GrossLivingAreaSquareFeetCount", "")
                # Handle empty strings
                if (
                    sqft_str
                    and str(sqft_str).strip()
                    and str(sqft_str).strip() not in ["", "0", "-1"]
                ):
                    try:
                        sqft_val = float(str(sqft_str).strip())
                        if sqft_val > 0:
                            square_feet = int(sqft_val)
                    except (ValueError, TypeError):
                        pass

                beds_str = structure.get("@TotalBedroomCount", "")
                # Handle empty strings - treat as missing data
                if (
                    beds_str
                    and str(beds_str).strip()
                    and str(beds_str).strip() not in ["", "0"]
                ):
                    try:
                        bedrooms = int(float(str(beds_str).strip()))
                        # Treat 0 as None if TotalRoomCount suggests missing data
                        if bedrooms == 0:
                            total_rooms_str = structure.get("@TotalRoomCount", "")
                            if (
                                total_rooms_str
                                and str(total_rooms_str).strip()
                                and str(total_rooms_str).strip() not in ["", "0"]
                            ):
                                try:
                                    total_rooms = int(
                                        float(str(total_rooms_str).strip())
                                    )
                                    if total_rooms > 0:
                                        bedrooms = None
                                except:
                                    pass
                    except (ValueError, TypeError):
                        pass

                baths_str = structure.get("@TotalBathroomCount", "")
                # Handle empty strings - treat as missing data
                if (
                    baths_str
                    and str(baths_str).strip()
                    and str(baths_str).strip() not in ["", "0", "0.0", "0.00"]
                ):
                    try:
                        bathrooms = float(str(baths_str).strip())
                        # Treat 0 as None if TotalRoomCount suggests missing data
                        if bathrooms == 0.0:
                            total_rooms_str = structure.get("@TotalRoomCount", "")
                            if (
                                total_rooms_str
                                and str(total_rooms_str).strip()
                                and str(total_rooms_str).strip() not in ["", "0"]
                            ):
                                try:
                                    total_rooms = int(
                                        float(str(total_rooms_str).strip())
                                    )
                                    if total_rooms > 0:
                                        bathrooms = None
                                except:
                                    pass
                    except (ValueError, TypeError):
                        pass

                # Extract detailed bathroom counts
                baths_full_str = structure.get("@TotalBathroomFullCount_ext", "")
                if (
                    baths_full_str
                    and str(baths_full_str).strip()
                    and str(baths_full_str).strip() not in ["", "0"]
                ):
                    try:
                        bathrooms_full = int(float(str(baths_full_str).strip()))
                    except (ValueError, TypeError):
                        pass

                baths_half_str = structure.get("@TotalBathroomHalfCount_ext", "")
                if (
                    baths_half_str
                    and str(baths_half_str).strip()
                    and str(baths_half_str).strip() not in ["", "0"]
                ):
                    try:
                        bathrooms_half = int(float(str(baths_half_str).strip()))
                    except (ValueError, TypeError):
                        pass

                # Extract total rooms
                total_rooms_str = structure.get("@TotalRoomCount", "")
                if (
                    total_rooms_str
                    and str(total_rooms_str).strip()
                    and str(total_rooms_str).strip() not in ["", "0"]
                ):
                    try:
                        total_rooms = int(float(str(total_rooms_str).strip()))
                    except (ValueError, TypeError):
                        pass

                # Extract stories
                stories_str = structure.get("@StoriesCount", "")
                if (
                    stories_str
                    and str(stories_str).strip()
                    and str(stories_str).strip() not in ["", "0"]
                ):
                    try:
                        stories = int(float(str(stories_str).strip()))
                    except (ValueError, TypeError):
                        pass

                structure_analysis = structure.get("STRUCTURE_ANALYSIS", {})
                if structure_analysis:
                    year_str = structure_analysis.get("@PropertyStructureBuiltYear", "")
                    if year_str:
                        try:
                            year_built = int(year_str)
                        except:
                            pass

                # Extract parking information
                car_storage = structure.get("CAR_STORAGE", {})
                if car_storage:
                    car_location = car_storage.get("CAR_STORAGE_LOCATION", {})
                    if car_location:
                        parking_str = car_location.get("@_ParkingSpacesCount", "")
                        if (
                            parking_str
                            and str(parking_str).strip()
                            and str(parking_str).strip() not in ["", "0"]
                        ):
                            try:
                                parking_spaces = int(float(str(parking_str).strip()))
                            except (ValueError, TypeError):
                                pass
                        garage_type = car_location.get(
                            "@_Type", ""
                        ) or car_location.get("@_TypeOtherDescription", "")
                        if garage_type and str(garage_type).strip():
                            garage_type = str(garage_type).strip()
                        else:
                            garage_type = None

                # Extract heating/cooling
                heating = structure.get("HEATING", {})
                if heating:
                    heating_desc = heating.get("@_UnitDescription", "") or heating.get(
                        "@_TypeOtherDescription", ""
                    )
                    if (
                        heating_desc
                        and str(heating_desc).strip()
                        and str(heating_desc).strip().upper() not in ["NO", "NONE", ""]
                    ):
                        heating_type = str(heating_desc).strip()

                cooling = structure.get("COOLING", {})
                if cooling:
                    cooling_desc = cooling.get("@_UnitDescription", "") or cooling.get(
                        "@_TypeOtherDescription", ""
                    )
                    if cooling_desc and _is_valid_cooling_type(str(cooling_desc)):
                        cooling_desc = str(cooling_desc).strip()
                        if cooling_desc.upper() == "YES":
                            cooling_type = "Yes"
                        else:
                            cooling_type = cooling_desc

                # Extract roof material from exterior features
                exterior_features = structure.get("EXTERIOR_FEATURE", [])
                if exterior_features:
                    if not isinstance(exterior_features, list):
                        exterior_features = [exterior_features]
                    for feature in exterior_features:
                        if isinstance(feature, dict):
                            feature_type = feature.get("@_Type", "")
                            feature_desc = feature.get(
                                "@_Description", ""
                            ) or feature.get("@_TypeOtherDescription", "")
                            if feature_type == "Other" and "Roof" in (
                                feature_desc or ""
                            ):
                                # Filter out placeholder values
                                if feature_desc and _is_valid_roof_material(
                                    feature_desc
                                ):
                                    roof_material = feature_desc.strip()
                            elif feature_desc:
                                exterior_features_list.append(feature_desc)

                # Extract amenities
                amenities_data = structure.get("AMENITIES", {})
                if amenities_data:
                    amenity_list = amenities_data.get("AMENITY", [])
                    if amenity_list:
                        if not isinstance(amenity_list, list):
                            amenity_list = [amenity_list]
                        for amenity in amenity_list:
                            if isinstance(amenity, dict):
                                amenity_type = amenity.get("@_Type", "")
                                amenity_desc = amenity.get("@_DetailedDescription", "")
                                # Prefer @_Type, fallback to description
                                if amenity_type and str(amenity_type).strip():
                                    amenities_list.append(str(amenity_type).strip())
                                elif amenity_desc and str(amenity_desc).strip():
                                    amenities_list.append(str(amenity_desc).strip())
                else:
                    # Check for single AMENITY (not AMENITIES)
                    amenity = structure.get("AMENITY", {})
                    if amenity and isinstance(amenity, dict):
                        amenity_type = amenity.get("@_Type", "")
                        amenity_desc = amenity.get("@_DetailedDescription", "")
                        if amenity_type and str(amenity_type).strip():
                            amenities_list.append(str(amenity_type).strip())
                        elif amenity_desc and str(amenity_desc).strip():
                            amenities_list.append(str(amenity_desc).strip())

                # Remove duplicates and empty values
                amenities_list = list(
                    dict.fromkeys(
                        [a for a in amenities_list if a and len(a.strip()) > 0]
                    )
                )

            # Get price - prioritize sale price, then market value, then assessed value
            list_price = None
            sale_history = subject_data.get("SALES_HISTORY", {})
            if sale_history:
                sale_price_str = sale_history.get("@PropertySalesAmount", "")
                if sale_price_str:
                    try:
                        list_price = float(sale_price_str)
                    except:
                        pass

            # Try market value or assessed value
            tax = subject_data.get("_TAX", {})
            if not list_price and tax:
                market_value_str = tax.get("@_AssessorMarketValue_ext", "")
                assessed_value_str = tax.get("@_TotalAssessedValueAmount", "")

                if market_value_str:
                    try:
                        market_value = float(market_value_str)
                        if market_value > 50000:
                            list_price = market_value
                    except:
                        pass

                if not list_price and assessed_value_str:
                    try:
                        assessed_value = float(assessed_value_str)
                        if assessed_value > 50000:
                            list_price = assessed_value
                    except:
                        pass

            property_type = self._map_property_type(
                subject_data.get("@StandardUseCode_ext", "")
                or subject_data.get("@StandardUseDescription_ext", "")
            )

            # Try to extract architectural style from property description
            # ATTOM may have this in various fields
            architectural_style = None
            use_description = subject_data.get("@StandardUseDescription_ext", "")
            # Some descriptions include style info, but ATTOM doesn't always provide this
            # This would need to come from MLS or other sources

            # Extract school district if available (may be in different locations)
            school_district = None
            # ATTOM v2 may not include school district in Sales Comparables response
            # Would need to use School API endpoint for this

            # Generate Google Street View URLs if coordinates available
            street_view_url = None
            street_view_image_url = None
            if lat and lon:
                # Interactive Street View link
                street_view_url = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"

                # Static Street View image (if API key available)
                if settings.google_maps_api_key:
                    street_view_image_url = (
                        f"https://maps.googleapis.com/maps/api/streetview?"
                        f"size=600x400&location={lat},{lon}&fov=90&heading=0&pitch=0"
                        f"&key={settings.google_maps_api_key}"
                    )
                else:
                    # Fallback to embeddable URL without API key
                    street_view_image_url = (
                        f"https://maps.googleapis.com/maps/api/streetview?"
                        f"size=600x400&location={lat},{lon}&fov=90&heading=0&pitch=0"
                    )

            # Log extracted data for debugging
            logger.info(
                f"Parsed subject property v2 - rooms={total_rooms}, lot_sqft={lot_size_sqft}, parking={parking_spaces}, "
                f"heating={heating_type}, cooling={cooling_type}, roof={roof_material}, "
                f"amenities={len(amenities_list)}, exterior={len(exterior_features_list)}"
            )

            # Extract sale information for subject (if it's a recent sale)
            sold_price = None
            sold_date = None
            sale_recency_days = None
            seller_concessions = None
            seller_concessions_description = None
            financing_type = None
            arms_length_transaction = None
            if sale_history:
                # Already extracted list_price from sale_history above
                # Also extract as sold_price if it's a sale
                sale_price_str = sale_history.get("@PropertySalesAmount", "")
                if sale_price_str:
                    try:
                        sold_price = float(sale_price_str)
                    except:
                        pass

                sale_date_str = sale_history.get("@PropertySalesDate", "")
                if sale_date_str:
                    try:
                        if "T" in sale_date_str:
                            sold_date = datetime.fromisoformat(
                                sale_date_str.replace("Z", "+00:00").split("T")[0]
                            )
                        else:
                            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"]:
                                try:
                                    sold_date = datetime.strptime(sale_date_str, fmt)
                                    break
                                except:
                                    continue
                        if sold_date:
                            sale_recency_days = (datetime.now() - sold_date).days
                    except:
                        pass

                # Extract arms-length transaction indicator
                arms_length = sale_history.get("@ArmsLengthTransactionIndicatorExt", "")
                if arms_length:
                    arms_length_transaction = arms_length.upper() in [
                        "A",
                        "Y",
                        "YES",
                        "TRUE",
                        "1",
                    ]

                # Extract financing type from loans
                loans = sale_history.get("LOANS_ext", {})
                if loans:
                    loan_list = loans.get("LOAN_ext", [])
                    if loan_list and not isinstance(loan_list, list):
                        loan_list = [loan_list]
                    if loan_list and len(loan_list) > 0:
                        first_loan = loan_list[0]
                        if isinstance(first_loan, dict):
                            loan_type = first_loan.get("@_Type", "")
                            loan_amount = first_loan.get("@_Amount", "")
                            if (
                                loan_amount
                                and float(str(loan_amount).replace(",", "")) > 0
                            ):
                                financing_type = loan_type or "Financed"
                            else:
                                financing_type = "Cash"

                    # Check for seller carryback
                    seller_carryback = loans.get("@SellerCarrybackindicator", "")
                    if (
                        seller_carryback
                        and str(seller_carryback).strip()
                        and str(seller_carryback).strip() not in ["0", ""]
                    ):
                        seller_concessions_description = "Seller financing/carryback"

            # Calculate price per sqft if we have price and square feet
            price_per_sqft = None
            if sold_price and square_feet:
                price_per_sqft = sold_price / square_feet
            elif list_price and square_feet:
                price_per_sqft = list_price / square_feet

            # Build metadata for UI/reporting
            mls_meta = {}
            if isinstance(subject_data, dict):
                mls_meta = dict(subject_data)
            mls_meta.update(
                {
                    "property_description": subject_data.get(
                        "@StandardUseDescription_ext"
                    )
                    or subject_data.get("DESCRIPTION_ext")
                    or subject_data.get("description"),
                    "data_source": "ATTOM v2 SalesComparables (subject)",
                }
            )

            return Property(
                mls_number=apn or "",
                address=street,
                city=city,
                state=state,
                zip_code=zip_code,
                property_type=property_type,
                status=PropertyStatus.SOLD if sold_price else PropertyStatus.ACTIVE,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                bathrooms_full=bathrooms_full,
                bathrooms_half=bathrooms_half,
                total_rooms=total_rooms,
                square_feet=square_feet,
                lot_size_sqft=lot_size_sqft,
                lot_size_acres=lot_size_acres,
                year_built=year_built,
                stories=stories,
                parking_spaces=parking_spaces,
                garage_type=garage_type,
                architectural_style=architectural_style,
                heating_type=heating_type,
                cooling_type=cooling_type,
                roof_material=roof_material,
                exterior_features=exterior_features_list,
                amenities=amenities_list,
                description=(
                    subject_data.get("@StandardUseDescription_ext")
                    or subject_data.get("DESCRIPTION_ext")
                    or subject_data.get("description")
                ),
                school_district=school_district,
                list_price=list_price,
                sold_price=sold_price,
                sold_date=sold_date,
                sale_recency_days=sale_recency_days,
                price_per_sqft=price_per_sqft,
                seller_concessions=seller_concessions,
                seller_concessions_description=seller_concessions_description,
                financing_type=financing_type,
                arms_length_transaction=arms_length_transaction,
                latitude=lat,
                longitude=lon,
                street_view_url=street_view_url,
                street_view_image_url=street_view_image_url,
                mls_data=mls_meta,
            )
        except Exception as e:
            logger.error(f"Error parsing subject property from v2: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _parse_comparable_property(self, comp: Dict[str, Any]) -> Optional[Property]:
        """Parse a single comparable property from ATTOM response."""
        try:
            # ATTOM comparables structure may vary - try multiple formats
            address_data = comp.get("address", {}) or comp.get("Address", {})
            identifier = comp.get("identifier", {}) or comp.get("Identifier", {})
            summary = comp.get("summary", {}) or comp.get("Summary", {})
            building = comp.get("building", {}) or comp.get("Building", {})
            sale = comp.get("sale", {}) or comp.get("Sale", {})

            # Extract address
            street = (
                address_data.get("oneLine", "")
                or address_data.get("line1", "")
                or comp.get("address", "")
            )
            city = address_data.get("city", "") or comp.get("city", "")
            state = address_data.get("state", "") or comp.get("state", "")
            zip_code = (
                address_data.get("postal1", "")
                or address_data.get("zip", "")
                or comp.get("zip", "")
            )

            # Property type
            property_type_str = summary.get("propertyType", "") or comp.get(
                "propertyType", ""
            )
            property_type = self._map_property_type(property_type_str)

            # Building details
            building_size = building.get("size", {}) if building else {}
            square_feet = (
                building_size.get("livingSize")
                or building_size.get("bldgSize")
                or comp.get("squareFeet")
            )
            if square_feet:
                try:
                    square_feet = int(square_feet)
                except:
                    square_feet = None

            bedrooms = (
                building.get("rooms", {}).get("beds")
                if building
                else comp.get("bedrooms")
            )
            if bedrooms:
                try:
                    bedrooms = int(bedrooms)
                except:
                    bedrooms = None

            bathrooms = (
                building.get("rooms", {}).get("baths")
                if building
                else comp.get("bathrooms")
            )
            if bathrooms:
                try:
                    bathrooms = float(bathrooms)
                except:
                    bathrooms = None

            year_built = summary.get("yearBuilt") or comp.get("yearBuilt")
            if year_built:
                try:
                    year_built = int(year_built)
                except:
                    year_built = None

            # Sale information
            sold_price = (
                sale.get("amount", {})
                if isinstance(sale.get("amount"), dict)
                else sale.get("amount") or comp.get("salePrice")
            )
            if sold_price:
                try:
                    sold_price = float(sold_price)
                except:
                    sold_price = None

            sold_date_str = sale.get("date", "") or comp.get("saleDate", "")
            sold_date = None
            if sold_date_str:
                try:
                    # Try various date formats
                    if isinstance(sold_date_str, str):
                        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"]:
                            try:
                                sold_date = datetime.strptime(sold_date_str, fmt)
                                break
                            except:
                                continue
                except:
                    pass

            # Distance (if provided)
            distance = comp.get("distance") or comp.get("Distance")

            # Metadata and description
            comp_description = (
                summary.get("description")
                or summary.get("propertyDescription")
                or comp.get("description")
            )
            mls_meta = {}
            if isinstance(comp, dict):
                mls_meta = dict(comp)
            mls_meta.update(
                {
                    "property_description": comp_description,
                    "data_source": "ATTOM v2 SalesComparables (comp)",
                }
            )

            return Property(
                mls_number=identifier.get("apn", "")
                or comp.get("apn", "")
                or comp.get("parcelNumber", ""),
                address=street,
                city=city,
                state=state,
                zip_code=zip_code,
                property_type=property_type,
                status=PropertyStatus.SOLD if sold_price else PropertyStatus.ACTIVE,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                year_built=year_built,
                sold_price=sold_price,
                sold_date=sold_date,
                description=comp_description,
                latitude=address_data.get("latitude") or comp.get("latitude"),
                longitude=address_data.get("longitude") or comp.get("longitude"),
                mls_data=mls_meta,
            )
        except Exception as e:
            logger.error(f"Error parsing comparable property: {e}")
            return None

    def _map_property_type(self, attom_type: str) -> PropertyType:
        """Map ATTOM property type to our PropertyType enum."""
        if not attom_type:
            return PropertyType.RESIDENTIAL

        attom_type_lower = attom_type.lower()

        if "condo" in attom_type_lower or "co-op" in attom_type_lower:
            return PropertyType.CONDO
        elif "townhouse" in attom_type_lower or "town house" in attom_type_lower:
            return PropertyType.TOWNHOUSE
        elif "multi" in attom_type_lower or "duplex" in attom_type_lower:
            return PropertyType.MULTI_FAMILY
        elif "commercial" in attom_type_lower:
            return PropertyType.COMMERCIAL
        elif "land" in attom_type_lower or "vacant" in attom_type_lower:
            return PropertyType.LAND
        else:
            return PropertyType.RESIDENTIAL

    # Implement MLSConnector interface methods
    def search_properties(
        self,
        city: Optional[str] = None,
        zip_code: Optional[str] = None,
        property_type: Optional[PropertyType] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_sqft: Optional[int] = None,
        max_sqft: Optional[int] = None,
        bedrooms: Optional[int] = None,
        status: Optional[PropertyStatus] = None,
        sold_after: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Property]:
        """Search properties - ATTOM doesn't support general search, use get_sales_comparables instead."""
        logger.warning(
            "ATTOM doesn't support general property search. Use get_sales_comparables() or get_property_by_address() instead."
        )
        return []

    def get_property_by_mls(self, mls_number: str) -> Optional[Property]:
        """Get property by APN (ATTOM uses APN, not MLS numbers)."""
        # ATTOM uses APN, not MLS numbers
        # Would need address lookup first
        logger.warning(
            "ATTOM uses APN, not MLS numbers. Use get_property_by_address() instead."
        )
        return None

    # ============================================================================
    # SCHOOL API INTEGRATION
    # ============================================================================

    def get_school_district_by_location(
        self, latitude: float, longitude: float
    ) -> Optional[str]:
        """Get school district for a location using ATTOM School API."""
        if not self.connected:
            return None

        # Check cache first
        cache_key = f"{latitude:.6f},{longitude:.6f}"
        if cache_key in self._school_district_cache:
            return self._school_district_cache[cache_key]

        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }

            url = f"{self.BASE_URL_V1}/school/districtdetail"
            params = {"latitude": latitude, "longitude": longitude, "debug": "True"}

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()

                # Parse school district response
                if isinstance(data, dict) and "school" in data:
                    schools = data["school"]
                    if isinstance(schools, list) and len(schools) > 0:
                        school = schools[0]
                        district_name = (
                            school.get("districtName")
                            or school.get("district")
                            or school.get("schoolDistrict")
                        )
                        if district_name:
                            logger.debug(f"Found school district: {district_name}")
                            # Cache the result
                            self._school_district_cache[cache_key] = district_name
                            return district_name

            logger.debug("No school district found for location")
            # Cache negative result too
            self._school_district_cache[cache_key] = None
            return None

        except Exception as e:
            logger.warning(f"School API district lookup failed: {e}")
            return None

    def get_schools_by_location(
        self,
        latitude: float,
        longitude: float,
        radius_miles: int = 5,
        max_schools: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get schools within radius of a location."""
        if not self.connected:
            return []

        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }

            url = f"{self.BASE_URL_V1}/school/schoolradius"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "radius": radius_miles,
                "maxschools": max_schools,
                "debug": "True",
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()

                if isinstance(data, dict) and "school" in data:
                    schools = data["school"]
                    if isinstance(schools, list):
                        return schools

            return []

        except Exception as e:
            logger.warning(f"School API radius lookup failed: {e}")
            return []

    # ============================================================================
    # ASSESSMENT API INTEGRATION
    # ============================================================================

    def get_assessment_detail(
        self,
        attom_id: str = None,
        address: str = None,
        city: str = None,
        state: str = None,
        zip_code: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed assessment and tax information for a property."""
        if not self.connected:
            return None

        # Check cache first
        cache_key = attom_id or f"{address}_{city}_{state}_{zip_code}"
        if cache_key in self._assessment_cache:
            return self._assessment_cache[cache_key]

        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }

            url = f"{self.BASE_URL_V1}/assessment/detail"
            params = {"debug": "True"}

            # Use ATTOM ID if available, otherwise address
            if attom_id:
                params["attomid"] = attom_id
            elif address and city:
                params["address1"] = address.strip()
                params["address2"] = f"{city}, {state}" + (
                    f" {zip_code}" if zip_code else ""
                )
            else:
                return None

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Cache the result
                self._assessment_cache[cache_key] = data
                return data

            # Cache negative result
            self._assessment_cache[cache_key] = None
            return None

        except Exception as e:
            logger.warning(f"Assessment API lookup failed: {e}")
            return None

    # ============================================================================
    # SALE API INTEGRATION
    # ============================================================================

    def get_sale_detail(
        self,
        attom_id: str = None,
        address: str = None,
        city: str = None,
        state: str = None,
        zip_code: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Get detailed sale transaction information."""
        if not self.connected:
            return None

        # Check cache first
        cache_key = attom_id or f"{address}_{city}_{state}_{zip_code}"
        if cache_key in self._sale_detail_cache:
            return self._sale_detail_cache[cache_key]

        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }

            url = f"{self.BASE_URL_V1}/sale/detail"
            params = {"debug": "True"}

            # Use ATTOM ID if available, otherwise address
            if attom_id:
                params["attomid"] = attom_id
            elif address and city:
                params["address1"] = address.strip()
                params["address2"] = f"{city}, {state}" + (
                    f" {zip_code}" if zip_code else ""
                )
            else:
                return None

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Cache the result
                self._sale_detail_cache[cache_key] = data
                return data

            # Cache negative result
            self._sale_detail_cache[cache_key] = None
            return None

        except Exception as e:
            logger.warning(f"Sale API lookup failed: {e}")
            return None

    # ============================================================================
    # AVM API INTEGRATION
    # ============================================================================

    def get_avm_detail(
        self,
        attom_id: str = None,
        address: str = None,
        city: str = None,
        state: str = None,
        zip_code: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Get automated valuation model data."""
        if not self.connected:
            return None

        # Check cache first
        cache_key = attom_id or f"{address}_{city}_{state}_{zip_code}"
        if cache_key in self._avm_cache:
            return self._avm_cache[cache_key]

        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }

            url = f"{self.BASE_URL_V1}/attomavm/detail"
            params = {"debug": "True"}

            # Use ATTOM ID if available, otherwise address
            if attom_id:
                params["attomid"] = attom_id
            elif address and city:
                params["address1"] = address.strip()
                params["address2"] = f"{city}, {state}" + (
                    f" {zip_code}" if zip_code else ""
                )
            else:
                return None

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Cache the result
                self._avm_cache[cache_key] = data
                return data

            # Cache negative result
            self._avm_cache[cache_key] = None
            return None

        except Exception as e:
            logger.warning(f"AVM API lookup failed: {e}")
            return None

    # ============================================================================
    # COMMUNITY API INTEGRATION (Area API)
    # ============================================================================

    def get_community_detail(
        self, geo_id: str = None, latitude: float = None, longitude: float = None
    ) -> Optional[Dict[str, Any]]:
        """Get community/neighborhood demographic and economic data."""
        if not self.connected:
            return None

        # Determine cache key
        if geo_id:
            cache_key = geo_id
        elif latitude is not None and longitude is not None:
            cache_key = f"{latitude:.6f},{longitude:.6f}"
        else:
            return None

        # Check cache first
        if cache_key in self._community_cache:
            return self._community_cache[cache_key]

        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }

            # Use new V4 endpoint
            url = "https://api.gateway.attomdata.com/areaapi/v4/area/full"
            params = {}

            if geo_id:
                params["geoIdV4"] = geo_id
            elif latitude is not None and longitude is not None:
                # First get geo ID from lat/lon
                geo_id_result = self._get_geo_id_from_location(latitude, longitude)
                if geo_id_result:
                    params["geoIdV4"] = geo_id_result
                    cache_key = geo_id_result  # Update cache key to use geo_id
                else:
                    return None
            else:
                return None

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Cache the result
                self._community_cache[cache_key] = data
                return data

            # Cache negative result
            self._community_cache[cache_key] = None
            return None

        except Exception as e:
            logger.warning(f"Community API lookup failed: {e}")
            return None

    def _get_geo_id_from_location(
        self, latitude: float, longitude: float
    ) -> Optional[str]:
        """Convert lat/lon to ATTOM geo ID."""
        try:
            headers = {
                "apikey": self.api_key,
                "Accept": "application/json",
            }

            url = "https://api.gateway.attomdata.com/areaapi/v4/geoId/lookup"
            params = {"latitude": latitude, "longitude": longitude}

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Parse to get geoIdV4
                if isinstance(data, dict) and "area" in data:
                    areas = data["area"]
                    if isinstance(areas, list) and len(areas) > 0:
                        area = areas[0]
                        geo_id = area.get("geoIdV4")
                        return geo_id

            return None

        except Exception as e:
            logger.warning(f"Geo ID lookup failed: {e}")
            return None

    # ============================================================================
    # ENRICHMENT METHODS - Add data from additional APIs
    # ============================================================================

    def enrich_property_with_additional_data(
        self, property: Property, max_api_calls: int = 3
    ) -> Property:
        """Enrich a property with data from additional ATTOM APIs."""
        if not self.connected or not property:
            return property

        api_calls_made = 0

        # Skip enrichment if we already have all the key data we want
        has_school = bool(property.school_district)
        has_description = bool(property.description)
        has_assessment = bool(property.mls_data and property.mls_data.get("assessment"))
        has_sale_data = bool(
            property.mls_data and property.mls_data.get("sale_detail_data")
        )
        has_avm_data = bool(property.mls_data and property.mls_data.get("avm_data"))

        # Only skip if we have most key data types
        if (
            has_school
            and has_description
            and has_assessment
            and (has_sale_data or has_avm_data)
        ):
            logger.debug("Property already has comprehensive data, skipping enrichment")
            return property

        # Get coordinates for API calls that need them
        lat = property.latitude
        lon = property.longitude

        if lat and lon:
            # 1. School district lookup (if missing)
            if not property.school_district and api_calls_made < max_api_calls:
                school_district = self.get_school_district_by_location(lat, lon)
                if school_district:
                    property.school_district = school_district
                    logger.info(f"✓ Added school district: {school_district}")
                api_calls_made += 1

            # 2. Community data (demographics, etc.) - if we want neighborhood stats
            # This is optional as it's a lot of data and may not be needed for all properties
            # if api_calls_made < max_api_calls:
            #     community_data = self.get_community_detail(latitude=lat, longitude=lon)
            #     if community_data:
            #         property.mls_data["community_data"] = community_data
            #         logger.info("✓ Added community data")
            #     api_calls_made += 1

        # Get ATTOM ID for detailed lookups (if available)
        attom_id = None
        if property.mls_data:
            # Try to extract ATTOM ID from various places
            attom_id = (
                property.mls_data.get("attom_id")
                or property.mls_data.get("attomID")
                or property.mls_data.get("@RTPropertyID_ext")
                or property.mls_data.get("RTPropertyID_ext")
            )

        # If no ATTOM ID but we have address, we could try to get it via property search
        # But that would be another API call, so skip for now

        if attom_id:
            # 3. Enhanced assessment data (more detailed than basic v1 assessment)
            if (
                not property.mls_data.get("assessment_detail_data")
                and api_calls_made < max_api_calls
            ):
                assessment_data = self.get_assessment_detail(attom_id=attom_id)
                if assessment_data:
                    property.mls_data["assessment_detail_data"] = assessment_data
                    logger.info("✓ Added enhanced assessment data")
                api_calls_made += 1

            # 4. Enhanced sale data
            if (
                not property.mls_data.get("sale_detail_data")
                and api_calls_made < max_api_calls
            ):
                sale_data = self.get_sale_detail(attom_id=attom_id)
                if sale_data:
                    property.mls_data["sale_detail_data"] = sale_data
                    logger.info("✓ Added enhanced sale data")
                api_calls_made += 1

            # 5. AVM data (automated valuation)
            if not property.mls_data.get("avm_data") and api_calls_made < max_api_calls:
                avm_data = self.get_avm_detail(attom_id=attom_id)
                if avm_data:
                    property.mls_data["avm_data"] = avm_data
                    logger.info("✓ Added AVM data")
                api_calls_made += 1

        return property
