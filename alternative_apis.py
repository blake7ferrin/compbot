"""Alternative API connectors for Zillow, Estated, RealtyMole, Oxylabs, etc."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
from config import settings
from models import Property, PropertyType, PropertyStatus
from mls_connector import MLSConnector

logger = logging.getLogger(__name__)


class ZillowAPIConnector(MLSConnector):
    """Zillow API connector (requires API key approval)."""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://api.zillow.com/v1"

    def connect(self) -> bool:
        """Connect to Zillow API."""
        # Test connection with a simple request
        try:
            # Note: Zillow API endpoints vary - this is a placeholder
            # You'll need to check Zillow's current API documentation
            self.connected = True
            logger.info("Connected to Zillow API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Zillow API: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from Zillow API."""
        self.connected = False

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
        limit: int = 100
    ) -> List[Property]:
        """Search properties via Zillow API."""
        if not self.connected:
            raise ConnectionError("Not connected to Zillow API")

        # Note: Zillow API structure varies - adjust based on their documentation
        # This is a template that needs to be customized
        try:
            params = {
                "zws-id": self.api_key,
            }

            if city:
                params["city"] = city
            if zip_code:
                params["zipcode"] = zip_code

            # Zillow API endpoint - adjust based on current API
            response = requests.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()

            data = response.json()
            properties = []

            # Parse Zillow response - structure depends on API version
            for item in data.get("results", []):
                prop = self._parse_zillow_property(item)
                if prop:
                    properties.append(prop)

            return properties[:limit]
        except Exception as e:
            logger.error(f"Error searching Zillow API: {e}")
            return []

    def _parse_zillow_property(self, data: Dict[str, Any]) -> Optional[Property]:
        """Parse Zillow API property data."""
        try:
            return Property(
                mls_number=data.get("zpid", ""),  # Zillow Property ID
                address=data.get("address", {}).get("street", ""),
                city=data.get("address", {}).get("city", ""),
                state=data.get("address", {}).get("state", ""),
                zip_code=data.get("address", {}).get("zipcode", ""),
                property_type=PropertyType.RESIDENTIAL,  # Default
                status=PropertyStatus.ACTIVE,
                bedrooms=data.get("bedrooms"),
                bathrooms=data.get("bathrooms"),
                square_feet=data.get("finishedSqFt"),
                year_built=data.get("yearBuilt"),
                list_price=float(data.get("price", 0)) if data.get("price") else None,
                latitude=float(data.get("latitude", 0)) if data.get("latitude") else None,
                longitude=float(data.get("longitude", 0)) if data.get("longitude") else None,
                description=data.get("description", ""),
                mls_data=data
            )
        except Exception as e:
            logger.error(f"Error parsing Zillow property: {e}")
            return None

    def get_property_by_mls(self, mls_number: str) -> Optional[Property]:
        """Get property by Zillow Property ID."""
        try:
            params = {"zws-id": self.api_key, "zpid": mls_number}
            response = requests.get(f"{self.base_url}/property", params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_zillow_property(data)
        except Exception as e:
            logger.error(f"Error getting Zillow property: {e}")
            return None


class EstatedAPIConnector(MLSConnector):
    """Estated Data API connector (free tier available)."""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://apis.estated.com/v4"

    def connect(self) -> bool:
        """Connect to Estated API."""
        try:
            # Test connection
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}/property", headers=headers, params={"address": "test"})
            # Even if it fails, we're "connected" - actual errors will show in search
            self.connected = True
            logger.info("Connected to Estated API")
            return True
        except Exception as e:
            logger.warning(f"Estated API connection test: {e}")
            self.connected = True  # Still allow connection attempts
            return True

    def disconnect(self):
        """Disconnect from Estated API."""
        self.connected = False

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
        limit: int = 100
    ) -> List[Property]:
        """Search properties via Estated API."""
        if not self.connected:
            raise ConnectionError("Not connected to Estated API")

        # Note: Estated API may require address-based searches
        # This is a simplified implementation
        properties = []

        # Estated typically works with specific addresses
        # For area searches, you might need to use their bulk endpoints
        # or iterate through known addresses

        return properties[:limit]

    def get_property_by_address(self, address: str, city: str, state: str, zip_code: str) -> Optional[Property]:
        """Get property by address (Estated's primary method)."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            # Estated API expects address in a specific format
            # Try with full address string first
            full_address = f"{address}, {city}, {state} {zip_code}".strip()
            params = {
                "token": self.api_key,  # Some Estated endpoints use token instead of Bearer
                "address": full_address
            }

            # Try the property endpoint
            response = requests.get(f"{self.base_url}/property", headers=headers, params=params, timeout=10)

            # If that fails, try with individual components
            if response.status_code != 200:
                params = {
                    "token": self.api_key,
                    "address": address,
                    "city": city,
                    "state": state,
                    "zip": zip_code
                }
                response = requests.get(f"{self.base_url}/property", headers=headers, params=params, timeout=10)

            response.raise_for_status()
            data = response.json()

            # Check for errors in response
            if "error" in data:
                logger.warning(f"Estated API error: {data.get('error')}")
                return None

            return self._parse_estated_property(data)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Estated API request failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error getting Estated property: {e}")
            return None

    def _parse_estated_property(self, data: Dict[str, Any]) -> Optional[Property]:
        """Parse Estated API property data."""
        try:
            prop_data = data.get("data", {}).get("property", {})
            if not prop_data:
                logger.warning("Estated API response missing property data")
                return None

            structure = prop_data.get("structure", {})
            address = prop_data.get("address", {})
            lot = prop_data.get("lot", {})
            valuation = prop_data.get("valuation", {})

            # Extract bedrooms/bathrooms - these are the key fields we need
            bedrooms = structure.get("beds")
            bathrooms = structure.get("baths")

            # Extract square footage
            square_feet = structure.get("size", {}).get("sqft")
            if not square_feet:
                square_feet = structure.get("sqft")

            # Extract lot size
            lot_size_sqft = lot.get("sqft")
            lot_size_acres = lot.get("acre")

            # Extract year built
            year_built = structure.get("year_built")

            # Extract parking
            parking_spaces = structure.get("garage", {}).get("spaces")
            garage_type = structure.get("garage", {}).get("type")

            # Extract property type
            prop_type = prop_data.get("type", "")

            # Extract price
            list_price = valuation.get("value")
            if not list_price:
                list_price = valuation.get("price")

            return Property(
                mls_number=prop_data.get("apn", "") or prop_data.get("fips_code", ""),  # Assessor's Parcel Number
                address=address.get("line1", "") or address.get("address", ""),
                city=address.get("city", ""),
                state=address.get("state", ""),
                zip_code=address.get("postal_code", "") or address.get("zip", ""),
                property_type=self._map_property_type(prop_type),
                status=PropertyStatus.ACTIVE,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                lot_size_sqft=lot_size_sqft,
                lot_size_acres=lot_size_acres,
                year_built=year_built,
                parking_spaces=parking_spaces,
                garage_type=garage_type,
                list_price=list_price,
                latitude=address.get("lat"),
                longitude=address.get("lon"),
                mls_data=data
            )
        except Exception as e:
            logger.error(f"Error parsing Estated property: {e}", exc_info=True)
            return None

    def _map_property_type(self, estated_type: str) -> PropertyType:
        """Map Estated property type to our PropertyType enum."""
        type_map = {
            "single_family": PropertyType.RESIDENTIAL,
            "condo": PropertyType.CONDO,
            "townhouse": PropertyType.TOWNHOUSE,
            "multi_family": PropertyType.MULTI_FAMILY,
        }
        return type_map.get(estated_type.lower(), PropertyType.RESIDENTIAL)

    def get_property_by_mls(self, mls_number: str) -> Optional[Property]:
        """Estated uses APN, not MLS numbers."""
        # Would need address lookup first
        return None


class RealtyMoleAPIConnector(MLSConnector):
    """RealtyMole Property API connector (freemium model)."""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://api.realtymole.com/api"

    def connect(self) -> bool:
        """Connect to RealtyMole API."""
        try:
            self.connected = True
            logger.info("Connected to RealtyMole API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RealtyMole API: {e}")
            return False

    def disconnect(self):
        """Disconnect from RealtyMole API."""
        self.connected = False

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
        limit: int = 100
    ) -> List[Property]:
        """Search properties via RealtyMole API."""
        if not self.connected:
            raise ConnectionError("Not connected to RealtyMole API")

        try:
            params = {"api_key": self.api_key}
            if city:
                params["city"] = city
            if zip_code:
                params["zip"] = zip_code

            response = requests.get(f"{self.base_url}/properties", params=params)
            response.raise_for_status()

            data = response.json()
            properties = []

            for item in data.get("properties", []):
                prop = self._parse_realtymole_property(item)
                if prop:
                    properties.append(prop)

            return properties[:limit]
        except Exception as e:
            logger.error(f"Error searching RealtyMole API: {e}")
            return []

    def _parse_realtymole_property(self, data: Dict[str, Any]) -> Optional[Property]:
        """Parse RealtyMole API property data."""
        try:
            return Property(
                mls_number=data.get("apn", ""),
                address=data.get("address", ""),
                city=data.get("city", ""),
                state=data.get("state", ""),
                zip_code=data.get("zip", ""),
                property_type=PropertyType.RESIDENTIAL,
                status=PropertyStatus.ACTIVE,
                bedrooms=data.get("bedrooms"),
                bathrooms=data.get("bathrooms"),
                square_feet=data.get("square_feet"),
                year_built=data.get("year_built"),
                list_price=float(data.get("price", 0)) if data.get("price") else None,
                latitude=float(data.get("latitude", 0)) if data.get("latitude") else None,
                longitude=float(data.get("longitude", 0)) if data.get("longitude") else None,
                mls_data=data
            )
        except Exception as e:
            logger.error(f"Error parsing RealtyMole property: {e}")
            return None

    def get_property_by_mls(self, mls_number: str) -> Optional[Property]:
        """Get property by APN."""
        try:
            params = {"api_key": self.api_key, "apn": mls_number}
            response = requests.get(f"{self.base_url}/property", params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_realtymole_property(data)
        except Exception as e:
            logger.error(f"Error getting RealtyMole property: {e}")
            return None


class OxylabsScraperConnector(MLSConnector):
    """Oxylabs Web Scraper API connector for scraping Redfin/Zillow."""

    def __init__(self, username: str, password: str):
        super().__init__()
        self.username = username
        self.password = password
        self.base_url = "https://realtime.oxylabs.io/v1/queries"

    def connect(self) -> bool:
        """Connect to Oxylabs API."""
        try:
            # Test connection with a simple request
            self.connected = True
            logger.info("Connected to Oxylabs API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Oxylabs API: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from Oxylabs API."""
        self.connected = False

    def _build_redfin_url(self, address: str, city: str, state: str, zip_code: str) -> str:
        """Build Redfin search URL for property."""
        # Redfin search format: https://www.redfin.com/city/XXXXX/STATE/CITY
        # Or direct address search
        query = f"{address}, {city}, {state} {zip_code}"
        # URL encode the query
        from urllib.parse import quote
        encoded_query = quote(query)
        return f"https://www.redfin.com/state/{state}/{city}/filter/include=sold-3yr"

    def _build_zillow_url(self, address: str, city: str, state: str, zip_code: str) -> str:
        """Build Zillow search URL for property."""
        query = f"{address}, {city}, {state} {zip_code}"
        from urllib.parse import quote
        encoded_query = quote(query)
        return f"https://www.zillow.com/homes/{encoded_query}_rb/"

    def get_property_by_address(self, address: str, city: str, state: str, zip_code: str) -> Optional[Property]:
        """Scrape property data from Redfin using Oxylabs."""
        if not self.connected:
            raise ConnectionError("Not connected to Oxylabs API")

        try:
            # Try Zillow first (often less aggressive on bot blocking)
            zillow_url = self._build_zillow_url(address, city, state, zip_code)
            prop = self._scrape_zillow(zillow_url, address, city, state, zip_code)

            if prop and (prop.bedrooms or prop.bathrooms):
                return prop

            # If Zillow didn't work, try Redfin
            redfin_url = self._build_redfin_url(address, city, state, zip_code)
            prop = self._scrape_redfin(redfin_url, address, city, state, zip_code)

            return prop
        except Exception as e:
            logger.warning(f"Oxylabs scraping failed: {e}")
            return None

    def _scrape_redfin(self, url: str, address: str, city: str, state: str, zip_code: str) -> Optional[Property]:
        """Scrape Redfin property page."""
        try:
            # Build proper Redfin search URL - try direct property search first
            # Redfin format: https://www.redfin.com/state/AZ/city-name/address
            from urllib.parse import quote
            city_slug = city.lower().replace(' ', '-')
            address_slug = address.lower().replace(' ', '-').replace(',', '').replace('.', '')
            redfin_url = f"https://www.redfin.com/state/{state}/{city_slug}/{address_slug}"

            # If that doesn't work, we can try search page
            # redfin_url = f"https://www.redfin.com/state/{state}/{city_slug}/filter/include=sold-3yr"

            payload = {
                "source": "universal",
                "url": redfin_url,
                "render": "html",
                # Anti-bot settings to bypass CAPTCHA/verification
                "user_agent_type": "desktop",  # Mimic desktop browser
                "geo_location": "United States",  # Appear from US
                "locale": "en_US"  # English locale
            }

            logger.info(f"Calling Oxylabs API for Redfin: {redfin_url}")
            response = requests.post(
                self.base_url,
                auth=(self.username, self.password),
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # Increased timeout for anti-bot processing
            )
            response.raise_for_status()

            data = response.json()
            if not data.get("results") or not data["results"][0].get("content"):
                return None

            html = data["results"][0]["content"]

            # Check for CAPTCHA/verification or page not found
            html_lower = html.lower()
            if 'human verification' in html_lower or 'captcha' in html_lower:
                logger.warning("Redfin returned CAPTCHA/verification page - cannot extract data")
                return None
            if 'page not found' in html_lower:
                logger.warning("Redfin returned page not found - falling back")
                return None

            soup = BeautifulSoup(html, "html.parser")

            # Log a sample of what we got for debugging
            page_text_sample = soup.get_text()[:500].lower()
            logger.info(f"Redfin page sample (first 500 chars): {page_text_sample}")

            return self._parse_redfin_page(soup, address, city, state, zip_code)
        except Exception as e:
            logger.warning(f"Redfin scraping failed: {e}")
            return None

    def _scrape_zillow(self, url: str, address: str, city: str, state: str, zip_code: str) -> Optional[Property]:
        """Scrape Zillow property page."""
        try:
            # Build proper Zillow search URL
            search_query = f"{address}, {city}, {state} {zip_code}"
            from urllib.parse import quote
            encoded_query = quote(search_query)
            zillow_url = f"https://www.zillow.com/homes/{encoded_query}_rb/"

            payload = {
                "source": "universal",
                "url": zillow_url,
                "render": "html",
                # Anti-bot settings to bypass CAPTCHA/verification
                "user_agent_type": "desktop",  # Mimic desktop browser
                "geo_location": "United States",  # Appear from US
                "locale": "en_US"  # English locale
            }

            logger.info(f"Calling Oxylabs API for Zillow: {zillow_url}")
            response = requests.post(
                self.base_url,
                auth=(self.username, self.password),
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120  # Increased timeout for anti-bot processing
            )
            response.raise_for_status()

            data = response.json()
            if not data.get("results") or not data["results"][0].get("content"):
                return None

            html = data["results"][0]["content"]
            soup = BeautifulSoup(html, "html.parser")

            return self._parse_zillow_page(soup, address, city, state, zip_code)
        except Exception as e:
            logger.warning(f"Zillow scraping failed: {e}")
            return None

    def _parse_redfin_page(self, soup: BeautifulSoup, address: str, city: str, state: str, zip_code: str) -> Optional[Property]:
        """Parse Redfin property page HTML."""
        try:
            bedrooms = None
            bathrooms = None
            square_feet = None
            lot_size_sqft = None
            lot_size_acres = None
            year_built = None
            list_price = None
            cooling_type = None
            heating_type = None
            roof_material = None
            garage_type = None
            amenities_list = []
            days_on_market = None
            property_description = None
            interior_features = []
            exterior_features = []

            # Try to find property stats
            # Redfin uses various class names - try multiple approaches
            stats_section = soup.find("div", {"class": "PropertyStatsV2"}) or \
                           soup.find("div", {"data-rf-test-id": "property-stats"}) or \
                           soup.find("div", class_=re.compile(".*Stats.*"))

            if stats_section:
                # Look for bedroom/bathroom/square footage
                stats = stats_section.find_all("div", class_=re.compile(".*stat.*"))
                for stat in stats:
                    text = stat.get_text(strip=True).lower()
                    # Bedrooms
                    if "bed" in text or "br" in text:
                        bed_match = re.search(r'(\d+)', text)
                        if bed_match:
                            bedrooms = int(bed_match.group(1))
                    # Bathrooms
                    if "bath" in text or "ba" in text:
                        bath_match = re.search(r'(\d+\.?\d*)', text)
                        if bath_match:
                            bathrooms = float(bath_match.group(1))
                    # Square feet
                    if "sqft" in text or "sq ft" in text:
                        sqft_match = re.search(r'([\d,]+)', text.replace(",", ""))
                        if sqft_match:
                            square_feet = int(sqft_match.group(1))

            # Try alternative selectors
            if not bedrooms:
                bed_elem = soup.find(string=re.compile(r'\d+\s*(bed|br)', re.I))
                if bed_elem:
                    bed_match = re.search(r'(\d+)', bed_elem)
                    if bed_match:
                        bedrooms = int(bed_match.group(1))

            if not bathrooms:
                bath_elem = soup.find(string=re.compile(r'\d+\.?\d*\s*(bath|ba)', re.I))
                if bath_elem:
                    bath_match = re.search(r'(\d+\.?\d*)', bath_elem)
                    if bath_match:
                        bathrooms = float(bath_match.group(1))

            if not square_feet:
                sqft_elem = soup.find(string=re.compile(r'[\d,]+\s*sq\.?\s*ft', re.I))
                if sqft_elem:
                    sqft_match = re.search(r'([\d,]+)', sqft_elem.replace(",", ""))
                    if sqft_match:
                        square_feet = int(sqft_match.group(1))

            # Extract lot size
            lot_elem = soup.find(string=re.compile(r'[\d,\.]+\s*(acre|acres|sq\.?\s*ft)', re.I))
            if lot_elem:
                # Try to extract acres first
                acre_match = re.search(r'([\d,\.]+)\s*acre', lot_elem, re.I)
                if acre_match:
                    try:
                        lot_size_acres = float(acre_match.group(1).replace(",", ""))
                        lot_size_sqft = lot_size_acres * 43560  # Convert to sqft
                    except:
                        pass
                # Try sqft
                if not lot_size_sqft:
                    sqft_match = re.search(r'([\d,]+)\s*sq\.?\s*ft', lot_elem, re.I)
                    if sqft_match:
                        try:
                            lot_size_sqft = float(sqft_match.group(1).replace(",", ""))
                            if lot_size_sqft:
                                lot_size_acres = lot_size_sqft / 43560
                        except:
                            pass

            # Extract year built
            year_elem = soup.find(string=re.compile(r'built\s+in\s+(\d{4})|(\d{4})\s+built', re.I))
            if year_elem:
                year_match = re.search(r'(\d{4})', year_elem)
                if year_match:
                    try:
                        year_built = int(year_match.group(1))
                        if year_built < 1800 or year_built > datetime.now().year + 1:
                            year_built = None
                    except:
                        pass

            # Extract amenities and features from page text
            page_text = soup.get_text().lower()
            full_text = soup.get_text()

            # Enhanced amenities extraction
            amenity_patterns = {
                "Fireplace": [r'fireplace', r'fire place'],
                "Pool": [r'swimming pool', r'in-ground pool', r'pool'],
                "Spa": [r'spa', r'hot tub'],
                "Patio": [r'patio', r'covered patio'],
                "Deck": [r'deck'],
                "Balcony": [r'balcony'],
                "Garden": [r'garden'],
                "Fence": [r'fence', r'fenced yard'],
                "Garage": [r'garage'],
                "Basement": [r'basement'],
                "Attic": [r'attic'],
                "Walk-in Closet": [r'walk-in closet', r'walk in closet'],
                "Hardwood Floors": [r'hardwood', r'hard wood'],
                "Granite Countertops": [r'granite'],
                "Stainless Steel Appliances": [r'stainless steel'],
                "Central Air": [r'central air', r'central a/c'],
                "Dishwasher": [r'dishwasher'],
                "Washer/Dryer": [r'washer', r'dryer'],
                "Solar Panels": [r'solar'],
            }

            for amenity_name, patterns in amenity_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, page_text, re.I):
                        if amenity_name not in amenities_list:
                            amenities_list.append(amenity_name)
                        break

            # Extract garage type
            if "garage" in page_text:
                garage_match = re.search(r'(attached|detached|carport|covered)', page_text, re.I)
                if garage_match:
                    garage_type = garage_match.group(1).title()

            # Extract Days on Market (DOM)
            dom_patterns = [
                r'(\d+)\s*days?\s*on\s*market',
                r'on\s*market\s*(\d+)\s*days?',
                r'dom[:\s]+(\d+)',
                r'listed\s*(\d+)\s*days?\s*ago'
            ]
            for pattern in dom_patterns:
                dom_match = re.search(pattern, page_text, re.I)
                if dom_match:
                    try:
                        days_on_market = int(dom_match.group(1))
                        break
                    except:
                        pass

            # Extract property description
            desc_selectors = [
                soup.find("div", {"class": "PropertyDescription"}),
                soup.find("div", {"data-rf-test-id": "property-description"}),
                soup.find("div", class_=re.compile(".*description.*", re.I)),
                soup.find("p", class_=re.compile(".*description.*", re.I))
            ]
            for desc_elem in desc_selectors:
                if desc_elem:
                    property_description = desc_elem.get_text(strip=True)
                    if len(property_description) > 50:  # Only use if substantial
                        break

            # Enhanced cooling/heating/roof extraction
            # Look for HVAC information
            hvac_text = full_text.lower()
            cooling_patterns = [
                r'central\s+air',
                r'central\s+a/c',
                r'air\s+conditioning',
                r'evaporative\s+cooling',
                r'swamp\s+cooler',
                r'heat\s+pump'
            ]
            for pattern in cooling_patterns:
                if re.search(pattern, hvac_text, re.I):
                    cooling_type = re.search(pattern, hvac_text, re.I).group(0).title()
                    if self._is_valid_cooling_type(cooling_type):
                        break

            heating_patterns = [
                r'forced\s+air',
                r'gas\s+heat',
                r'electric\s+heat',
                r'heat\s+pump',
                r'radiant\s+heat',
                r'baseboard'
            ]
            for pattern in heating_patterns:
                if re.search(pattern, hvac_text, re.I):
                    heating_type = re.search(pattern, hvac_text, re.I).group(0).title()
                    break

            # Enhanced roof material extraction
            roof_patterns = [
                r'(composition|asphalt)\s+shingle',
                r'tile\s+roof',
                r'metal\s+roof',
                r'concrete\s+tile',
                r'clay\s+tile',
                r'wood\s+shingle'
            ]
            for pattern in roof_patterns:
                roof_match = re.search(pattern, page_text, re.I)
                if roof_match:
                    roof_material = roof_match.group(0).title()
                    if self._is_valid_roof_material(roof_material):
                        break

            # Get price
            price_elem = soup.find(string=re.compile(r'\$[\d,]+', re.I))
            if price_elem:
                price_match = re.search(r'\$([\d,]+)', price_elem.replace(",", ""))
                if price_match:
                    list_price = float(price_match.group(1))

            # Only return if we got at least bedrooms or bathrooms
            if bedrooms is None and bathrooms is None:
                return None

            return Property(
                mls_number="",  # Not available from scraping
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                property_type=PropertyType.RESIDENTIAL,
                status=PropertyStatus.ACTIVE,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                lot_size_sqft=lot_size_sqft,
                lot_size_acres=lot_size_acres if lot_size_sqft else None,
                year_built=year_built,
                heating_type=heating_type,
                cooling_type=cooling_type,
                roof_material=roof_material,
                amenities=amenities_list if amenities_list else [],
                garage_type=garage_type,
                list_price=list_price,
                mls_data={
                    "source": "oxylabs_redfin",
                    "days_on_market": days_on_market,
                    "property_description": property_description,
                    "interior_features": interior_features,
                    "exterior_features": exterior_features
                }
            )
        except Exception as e:
            logger.warning(f"Error parsing Redfin page: {e}")
            return None

    def _parse_zillow_page(self, soup: BeautifulSoup, address: str, city: str, state: str, zip_code: str) -> Optional[Property]:
        """Parse Zillow property page HTML with comprehensive field extraction.
        
        Uses Zillow's data-testid attributes for reliable extraction of:
        - Beds, baths, sqft (primary stats)
        - Cooling, heating, roof, materials
        - HOA, parking, pool, community features
        - Architectural style, subdivision, year built
        """
        try:
            bedrooms = None
            bathrooms = None
            square_feet = None
            lot_size_sqft = None
            lot_size_acres = None
            year_built = None
            list_price = None
            cooling_type = None
            heating_type = None
            roof_material = None
            garage_type = None
            parking_spaces = None
            amenities_list = []
            days_on_market = None
            property_description = None
            interior_features = []
            exterior_features = []
            stories = None
            architectural_style = None
            hoa_fee = None
            has_pool = False
            subdivision = None
            construction_materials = None

            # ===== METHOD 1: data-testid based extraction (most reliable) =====
            
            # Primary stats: bed-bath-sqft-facts
            stats_elem = soup.find(attrs={'data-testid': 'bed-bath-sqft-facts'})
            if stats_elem:
                stats_text = stats_elem.get_text()
                logger.info(f"Zillow stats: {stats_text}")
                
                # Parse "3beds3baths1,837sqft" format
                beds_match = re.search(r'(\d+)\s*beds?', stats_text, re.I)
                if beds_match:
                    bedrooms = int(beds_match.group(1))
                
                baths_match = re.search(r'(\d+\.?\d*)\s*baths?', stats_text, re.I)
                if baths_match:
                    bathrooms = float(baths_match.group(1))
                
                sqft_match = re.search(r'([\d,]+)\s*sq\s*ft', stats_text, re.I)
                if sqft_match:
                    square_feet = int(sqft_match.group(1).replace(',', ''))

            # ===== Extract from fact-category elements =====
            fact_categories = soup.find_all(attrs={'data-testid': 'fact-category'})
            
            for fact in fact_categories:
                fact_text = fact.get_text()
                fact_lower = fact_text.lower()
                
                # Bedrooms & Bathrooms
                if 'bedroom' in fact_lower and bedrooms is None:
                    beds_match = re.search(r'bedrooms?[:\s]*(\d+)', fact_text, re.I)
                    if beds_match:
                        bedrooms = int(beds_match.group(1))
                    baths_match = re.search(r'bathrooms?[:\s]*(\d+\.?\d*)', fact_text, re.I)
                    if baths_match:
                        bathrooms = float(baths_match.group(1))
                
                # Heating
                if 'heating' in fact_lower and not heating_type:
                    # Extract heating type (e.g., "HeatingElectric" -> "Electric")
                    heating_match = re.search(r'heating\s*[:\s]*([\w\s,]+)', fact_text, re.I)
                    if heating_match:
                        heating_type = heating_match.group(1).strip()
                
                # Cooling
                if 'cooling' in fact_lower and not cooling_type:
                    cooling_match = re.search(r'cooling\s*[:\s]*([\w\s,]+)', fact_text, re.I)
                    if cooling_match:
                        cooling_type = cooling_match.group(1).strip()
                        if cooling_type.lower() in ['refrigerator', 'none', 'no']:
                            cooling_type = None  # Filter invalid values
                
                # Interior area / Square footage
                if 'interior area' in fact_lower and not square_feet:
                    sqft_match = re.search(r'([\d,]+)\s*sq\s*ft', fact_text, re.I)
                    if sqft_match:
                        square_feet = int(sqft_match.group(1).replace(',', ''))
                
                # Parking
                if 'parking' in fact_lower:
                    total_match = re.search(r'total\s*spaces?[:\s]*(\d+)', fact_text, re.I)
                    if total_match:
                        parking_spaces = int(total_match.group(1))
                    garage_match = re.search(r'garage\s*spaces?[:\s]*(\d+)', fact_text, re.I)
                    if garage_match:
                        garage_spaces = int(garage_match.group(1))
                        if garage_spaces > 0:
                            garage_type = f"{garage_spaces}-car garage"
                    if 'garage door opener' in fact_lower:
                        interior_features.append('Garage Door Opener')
                
                # Stories
                if 'stories' in fact_lower:
                    stories_match = re.search(r'stories[:\s]*(\d+)', fact_text, re.I)
                    if stories_match:
                        stories = int(stories_match.group(1))
                
                # Pool
                if 'pool' in fact_lower:
                    if 'none' not in fact_lower and 'no pool' not in fact_lower:
                        has_pool = True
                        amenities_list.append('Pool')
                    pool_match = re.search(r'pool\s*features?[:\s]*([\w\s,]+)', fact_text, re.I)
                    if pool_match and 'none' not in pool_match.group(1).lower():
                        exterior_features.append(f"Pool: {pool_match.group(1).strip()}")
                
                # Lot size
                if 'lot' in fact_lower:
                    lot_match = re.search(r'size[:\s]*([\d,]+)\s*sq\s*ft', fact_text, re.I)
                    if lot_match:
                        lot_size_sqft = float(lot_match.group(1).replace(',', ''))
                    lot_features = re.search(r'features[:\s]*([\w\s,]+)', fact_text, re.I)
                    if lot_features:
                        exterior_features.extend([f.strip() for f in lot_features.group(1).split(',')])
                
                # Year built
                if 'year built' in fact_lower or 'condition' in fact_lower:
                    year_match = re.search(r'year\s*built[:\s]*(\d{4})', fact_text, re.I)
                    if year_match:
                        year_built = int(year_match.group(1))
                
                # Architectural style
                if 'type & style' in fact_lower or 'architectural' in fact_lower:
                    style_match = re.search(r'architectural\s*style[:\s]*([\w\s/]+)', fact_text, re.I)
                    if style_match:
                        architectural_style = style_match.group(1).strip()
                
                # Materials (roof, construction)
                if 'material' in fact_lower:
                    materials_text = fact_text
                    roof_match = re.search(r'roof[:\s]*([\w\s]+)', materials_text, re.I)
                    if roof_match:
                        roof_material = roof_match.group(1).strip()
                    construction_match = re.search(r'(stucco|wood|brick|stone|frame)', materials_text, re.I)
                    if construction_match:
                        construction_materials = construction_match.group(1).title()
                
                # HOA
                if 'hoa' in fact_lower:
                    hoa_match = re.search(r'\$(\d+)\s*(month|/mo)', fact_text, re.I)
                    if hoa_match:
                        hoa_fee = float(hoa_match.group(1))
                
                # Community features
                if 'community' in fact_lower:
                    community_match = re.search(r'community\s*features?[:\s]*([\w\s,/]+)', fact_text, re.I)
                    if community_match:
                        features = community_match.group(1).split(',')
                        amenities_list.extend([f.strip() for f in features if f.strip()])
                
                # Subdivision/Location
                if 'subdivision' in fact_lower or 'location' in fact_lower:
                    sub_match = re.search(r'subdivision[:\s]*([\w\s]+)', fact_text, re.I)
                    if sub_match:
                        subdivision = sub_match.group(1).strip()
                
                # Features (interior/exterior)
                if 'features' in fact_lower and 'community' not in fact_lower:
                    # Parse feature lists
                    features_text = fact_text
                    feature_items = re.findall(r'[\w\s]+(?:,|$)', features_text)
                    for item in feature_items:
                        item = item.strip().rstrip(',')
                        if item and len(item) > 2:
                            interior_features.append(item)

            # ===== METHOD 2: Fallback to legacy selectors =====
            if bedrooms is None or bathrooms is None:
                stats_container = soup.find("div", {"class": "ds-bed-bath-living-area-container"}) or \
                                soup.find("div", class_=re.compile(".*bed.*bath.*", re.I))

                if stats_container:
                    if bedrooms is None:
                        bed_elem = stats_container.find(string=re.compile(r'\d+\s*(bed|br)', re.I))
                        if bed_elem:
                            bed_match = re.search(r'(\d+)', str(bed_elem))
                            if bed_match:
                                bedrooms = int(bed_match.group(1))

                    if bathrooms is None:
                        bath_elem = stats_container.find(string=re.compile(r'\d+\.?\d*\s*(bath|ba)', re.I))
                        if bath_elem:
                            bath_match = re.search(r'(\d+\.?\d*)', str(bath_elem))
                            if bath_match:
                                bathrooms = float(bath_match.group(1))

                    if square_feet is None:
                        sqft_elem = stats_container.find(string=re.compile(r'[\d,]+\s*sq\.?\s*ft', re.I))
                        if sqft_elem:
                            sqft_match = re.search(r'([\d,]+)', str(sqft_elem).replace(",", ""))
                            if sqft_match:
                                square_feet = int(sqft_match.group(1))

            # ===== METHOD 3: Meta tags fallback =====
            if bedrooms is None or bathrooms is None:
                meta_desc = soup.find('meta', {'name': 'description'})
                if meta_desc:
                    desc_content = meta_desc.get('content', '')
                    if bedrooms is None:
                        beds_match = re.search(r'(\d+)\s*beds?', desc_content, re.I)
                        if beds_match:
                            bedrooms = int(beds_match.group(1))
                    if bathrooms is None:
                        baths_match = re.search(r'(\d+\.?\d*)\s*baths?', desc_content, re.I)
                        if baths_match:
                            bathrooms = float(baths_match.group(1))
                    if square_feet is None:
                        sqft_match = re.search(r'([\d,]+)\s*sq\.?\s*ft', desc_content, re.I)
                        if sqft_match:
                            square_feet = int(sqft_match.group(1).replace(',', ''))

            # Get price from Zillow
            price_elem = soup.find("span", {"data-test": "property-card-price"}) or \
                        soup.find(string=re.compile(r'\$[\d,]+', re.I))
            if price_elem:
                price_text = price_elem.get_text() if hasattr(price_elem, 'get_text') else str(price_elem)
                price_match = re.search(r'\$([\d,]+)', price_text.replace(",", ""))
                if price_match:
                    list_price = float(price_match.group(1))

            # Calculate lot acres if we have sqft
            if lot_size_sqft and not lot_size_acres:
                lot_size_acres = lot_size_sqft / 43560.0

            # Only return if we got at least bedrooms or bathrooms
            if bedrooms is None and bathrooms is None:
                logger.warning("Zillow parsing: Could not extract beds or baths")
                return None

            # Remove duplicates from amenities and features
            amenities_list = list(set(amenities_list))
            interior_features = list(set(interior_features))
            exterior_features = list(set(exterior_features))

            logger.info(f"Zillow extracted: {bedrooms} beds, {bathrooms} baths, {square_feet} sqft, cooling={cooling_type}")

            return Property(
                mls_number="",
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                property_type=PropertyType.RESIDENTIAL,
                status=PropertyStatus.ACTIVE,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                square_feet=square_feet,
                lot_size_sqft=lot_size_sqft,
                lot_size_acres=lot_size_acres,
                year_built=year_built,
                stories=stories,
                heating_type=heating_type,
                cooling_type=cooling_type,
                roof_material=roof_material,
                architectural_style=architectural_style,
                amenities=amenities_list if amenities_list else [],
                exterior_features=exterior_features if exterior_features else [],
                garage_type=garage_type,
                parking_spaces=parking_spaces,
                list_price=list_price,
                mls_data={
                    "source": "oxylabs_zillow",
                    "days_on_market": days_on_market,
                    "property_description": property_description,
                    "interior_features": interior_features,
                    "exterior_features": exterior_features,
                    "hoa_fee": hoa_fee,
                    "subdivision": subdivision,
                    "construction_materials": construction_materials,
                    "has_pool": has_pool,
                }
            )
        except Exception as e:
            logger.warning(f"Error parsing Zillow page: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    def search_properties(self, *args, **kwargs) -> List[Property]:
        """Oxylabs is for specific property lookups, not area searches."""
        return []

    def get_property_by_mls(self, mls_number: str) -> Optional[Property]:
        """Oxylabs requires address, not MLS number."""
        return None


class PropertyRadarConnector(MLSConnector):
    """PropertyRadar API connector for investor data (equity, liens, ownership)."""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://api.propertyradar.com/v1"
        self._property_cache: Dict[str, Dict[str, Any]] = {}

    def connect(self) -> bool:
        """Connect to PropertyRadar API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            # Test connection by fetching lists
            response = requests.get(
                f"{self.base_url}/lists",
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                self.connected = True
                logger.info("Connected to PropertyRadar API")
                return True
            else:
                logger.error(f"PropertyRadar connection failed: {response.status_code}")
                self.connected = False
                return False
        except Exception as e:
            logger.error(f"Failed to connect to PropertyRadar API: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from PropertyRadar API."""
        self.connected = False

    def get_property_by_address(
        self, address: str, city: str, state: str, zip_code: str
    ) -> Optional[Property]:
        """Get property data from PropertyRadar by address.
        
        Note: PropertyRadar excels at investor data (equity, liens, ownership)
        but may be missing physical characteristics like bedrooms.
        """
        if not self.connected:
            raise ConnectionError("Not connected to PropertyRadar API")

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # First, search for the property to get RadarID
            radar_id = self._find_radar_id(address, city, state, zip_code)
            if not radar_id:
                logger.warning(f"PropertyRadar: Could not find RadarID for {address}")
                return None

            # Get property details using RadarID
            property_data = self._get_property_by_radar_id(radar_id)
            if not property_data:
                return None

            return self._parse_property_data(property_data, address, city, state, zip_code)

        except Exception as e:
            logger.warning(f"PropertyRadar lookup failed: {e}")
            return None

    def _find_radar_id(self, address: str, city: str, state: str, zip_code: str) -> Optional[str]:
        """Find PropertyRadar's internal ID for a property."""
        # Check cache first
        cache_key = f"{address}|{city}|{state}|{zip_code}"
        if cache_key in self._property_cache:
            cached = self._property_cache[cache_key]
            return cached.get("RadarID")

        # This would require creating a list with the property first
        # For now, we'll try the properties endpoint directly
        logger.info(f"PropertyRadar: Searching for {address}, {city}, {state}")
        return None  # Would need list-based lookup

    def _get_property_by_radar_id(self, radar_id: str) -> Optional[Dict[str, Any]]:
        """Get full property data using RadarID."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # PropertyRadar valid fields for property lookup
            valid_fields = [
                'Address', 'City', 'State', 'ZipFive', 'RadarID', 'PType',
                'AdvancedPropertyType', 'Baths', 'SqFt', 'LotSize', 'YearBuilt',
                'AVM', 'AvailableEquity', 'LastTransferRecDate', 'LastTransferValue',
                'isFreeAndClear', 'isCashBuyer', 'isNotSameMailingOrExempt',
                'Latitude', 'Longitude', 'Pool', 'Stories', 'Heating', 'RoofType',
                'Fireplace', 'Subdivision', 'Zoning', 'LotSizeAcres'
            ]

            url = f"{self.base_url}/properties/{radar_id}"
            params = {
                'Purchase': 'true',
                'Fields': ','.join(valid_fields)
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                if results:
                    return results[0]
            else:
                logger.warning(f"PropertyRadar property lookup failed: {response.status_code}")

            return None

        except Exception as e:
            logger.warning(f"PropertyRadar property lookup error: {e}")
            return None

    def get_investor_data(self, radar_id: str) -> Dict[str, Any]:
        """Get investor-focused data (equity, liens, ownership status)."""
        property_data = self._get_property_by_radar_id(radar_id)
        if not property_data:
            return {}

        return {
            "radar_id": property_data.get("RadarID"),
            "avm": property_data.get("AVM"),
            "available_equity": property_data.get("AvailableEquity"),
            "is_free_and_clear": property_data.get("isFreeAndClear") == 1,
            "is_cash_buyer": property_data.get("isCashBuyer") == 1,
            "is_absentee_owner": property_data.get("isNotSameMailingOrExempt") == 1,
            "last_transfer_date": property_data.get("LastTransferRecDate"),
            "last_transfer_value": property_data.get("LastTransferValue"),
            "subdivision": property_data.get("Subdivision"),
            "zoning": property_data.get("Zoning"),
        }

    def _parse_property_data(
        self, data: Dict[str, Any], address: str, city: str, state: str, zip_code: str
    ) -> Property:
        """Parse PropertyRadar data into Property model."""
        # PropertyRadar doesn't have bedrooms in API, but has other useful data
        bathrooms = data.get("Baths")
        square_feet = data.get("SqFt")
        lot_size_sqft = data.get("LotSize")
        lot_size_acres = data.get("LotSizeAcres")
        year_built = data.get("YearBuilt")
        stories = data.get("Stories")

        # Investor data
        avm = data.get("AVM")
        equity = data.get("AvailableEquity")
        last_sale_price = data.get("LastTransferValue")
        last_sale_date = data.get("LastTransferRecDate")

        # Property features
        has_pool = data.get("Pool") == 1
        has_fireplace = data.get("Fireplace") == 1
        has_heating = data.get("Heating") == 1
        roof_type = data.get("RoofType")

        return Property(
            mls_number=data.get("RadarID", ""),
            address=data.get("Address", address),
            city=data.get("City", city),
            state=data.get("State", state),
            zip_code=data.get("ZipFive", zip_code),
            property_type=PropertyType.RESIDENTIAL,
            status=PropertyStatus.SOLD if last_sale_date else PropertyStatus.ACTIVE,
            bedrooms=None,  # PropertyRadar doesn't have bedrooms
            bathrooms=float(bathrooms) if bathrooms else None,
            square_feet=int(square_feet) if square_feet else None,
            lot_size_sqft=float(lot_size_sqft) if lot_size_sqft else None,
            lot_size_acres=float(lot_size_acres) if lot_size_acres else None,
            year_built=int(year_built) if year_built else None,
            stories=int(stories) if stories else None,
            roof_material=roof_type if roof_type else None,
            sold_price=float(last_sale_price) if last_sale_price else None,
            latitude=float(data.get("Latitude")) if data.get("Latitude") else None,
            longitude=float(data.get("Longitude")) if data.get("Longitude") else None,
            amenities=["Pool"] if has_pool else [],
            mls_data={
                "source": "propertyradar",
                "radar_id": data.get("RadarID"),
                "avm": avm,
                "available_equity": equity,
                "is_free_and_clear": data.get("isFreeAndClear") == 1,
                "is_cash_buyer": data.get("isCashBuyer") == 1,
                "is_absentee_owner": data.get("isNotSameMailingOrExempt") == 1,
                "subdivision": data.get("Subdivision"),
                "zoning": data.get("Zoning"),
                "has_fireplace": has_fireplace,
                "has_heating": has_heating,
            }
        )

    def search_properties(self, *args, **kwargs) -> List[Property]:
        """PropertyRadar is optimized for specific property lookups."""
        return []

    def get_property_by_mls(self, mls_number: str) -> Optional[Property]:
        """PropertyRadar uses RadarID, not MLS numbers."""
        return None
