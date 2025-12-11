"""MLS connection module supporting RETS and RESO Web API."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from config import settings
from models import Property, PropertyType, PropertyStatus

logger = logging.getLogger(__name__)


class MLSConnector:
    """Base class for MLS connectors."""
    
    def __init__(self):
        self.connected = False
    
    def connect(self) -> bool:
        """Establish connection to MLS."""
        raise NotImplementedError
    
    def disconnect(self):
        """Close connection to MLS."""
        raise NotImplementedError
    
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
        """Search for properties matching criteria."""
        raise NotImplementedError
    
    def get_property_by_mls(self, mls_number: str) -> Optional[Property]:
        """Get a specific property by MLS number."""
        raise NotImplementedError


class RETSConnector(MLSConnector):
    """RETS (Real Estate Transaction Standard) connector."""
    
    def __init__(self):
        super().__init__()
        self.session = None
        self.rets = None
        try:
            import rets
            self.rets = rets
        except ImportError:
            logger.warning("RETS library not installed. Install with: pip install rets")
            # Don't raise - allow graceful degradation
    
    def connect(self) -> bool:
        """Connect to RETS server."""
        if not self.rets:
            logger.error("RETS library not available. Install with: pip install rets")
            return False
        
        try:
            self.session = self.rets.Session(
                login_url=settings.rets_url,
                username=settings.rets_username,
                password=settings.rets_password,
                user_agent=settings.rets_user_agent
            )
            self.session.login()
            self.connected = True
            logger.info("Successfully connected to RETS server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RETS: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from RETS server."""
        if self.session:
            try:
                self.session.logout()
            except:
                pass
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
        """Search properties via RETS."""
        if not self.connected:
            raise ConnectionError("Not connected to MLS")
        
        # Build RETS query
        query_parts = []
        
        if city:
            query_parts.append(f"(City={city})")
        if zip_code:
            query_parts.append(f"(PostalCode={zip_code})")
        if property_type:
            # Map PropertyType to RETS property type codes
            query_parts.append(f"(PropertyType={property_type.value})")
        if min_price:
            query_parts.append(f"(ListPrice>={min_price})")
        if max_price:
            query_parts.append(f"(ListPrice<={max_price})")
        if min_sqft:
            query_parts.append(f"(LivingArea>={min_sqft})")
        if max_sqft:
            query_parts.append(f"(LivingArea<={max_sqft})")
        if bedrooms:
            query_parts.append(f"(BedroomsTotal={bedrooms})")
        if status:
            query_parts.append(f"(StandardStatus={status.value})")
        if sold_after:
            query_parts.append(f"(CloseDate>={sold_after.strftime('%Y-%m-%d')})")
        
        query = " AND ".join(query_parts) if query_parts else "*"
        
        try:
            # Standard RETS resource/class (adjust based on your MLS)
            results = self.session.search(
                resource="Property",
                resource_class="RES",
                search_filter=query,
                limit=limit
            )
            
            properties = []
            for row in results:
                prop = self._parse_rets_row(row)
                if prop:
                    properties.append(prop)
            
            return properties
        except Exception as e:
            logger.error(f"Error searching RETS: {e}")
            return []
    
    def _parse_rets_row(self, row: Dict[str, Any]) -> Optional[Property]:
        """Parse a RETS row into a Property model."""
        try:
            # Map RETS fields to Property model
            # Field names vary by MLS - adjust as needed
            return Property(
                mls_number=row.get("ListingID", ""),
                address=row.get("StreetName", ""),
                city=row.get("City", ""),
                state=row.get("StateOrProvince", ""),
                zip_code=row.get("PostalCode", ""),
                property_type=PropertyType(row.get("PropertyType", "Residential")),
                status=PropertyStatus(row.get("StandardStatus", "Active")),
                bedrooms=int(row.get("BedroomsTotal", 0)) if row.get("BedroomsTotal") else None,
                bathrooms=float(row.get("BathroomsTotalInteger", 0)) if row.get("BathroomsTotalInteger") else None,
                square_feet=int(row.get("LivingArea", 0)) if row.get("LivingArea") else None,
                lot_size=float(row.get("LotSizeAcres", 0)) if row.get("LotSizeAcres") else None,
                year_built=int(row.get("YearBuilt", 0)) if row.get("YearBuilt") else None,
                list_price=float(row.get("ListPrice", 0)) if row.get("ListPrice") else None,
                sold_price=float(row.get("ClosePrice", 0)) if row.get("ClosePrice") else None,
                list_date=self._parse_date(row.get("ListDate")),
                sold_date=self._parse_date(row.get("CloseDate")),
                days_on_market=int(row.get("DaysOnMarket", 0)) if row.get("DaysOnMarket") else None,
                latitude=float(row.get("Latitude", 0)) if row.get("Latitude") else None,
                longitude=float(row.get("Longitude", 0)) if row.get("Longitude") else None,
                description=row.get("PublicRemarks", ""),
                mls_data=dict(row)
            )
        except Exception as e:
            logger.error(f"Error parsing RETS row: {e}")
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string from RETS."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None
    
    def get_property_by_mls(self, mls_number: str) -> Optional[Property]:
        """Get property by MLS number."""
        results = self.search_properties(limit=1)
        # Filter by MLS number
        for prop in results:
            if prop.mls_number == mls_number:
                return prop
        return None


class RESOWebAPIConnector(MLSConnector):
    """RESO Web API connector."""
    
    def __init__(self):
        super().__init__()
        self.access_token = None
        self.token_expires = None
    
    def connect(self) -> bool:
        """Connect to RESO Web API using OAuth2."""
        import requests
        
        try:
            # OAuth2 token request
            token_url = f"{settings.reso_api_url}/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": settings.reso_client_id,
                "client_secret": settings.reso_client_secret
            }
            
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires = datetime.now() + timedelta(seconds=expires_in)
            self.connected = True
            
            logger.info("Successfully connected to RESO Web API")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RESO Web API: {e}")
            self.connected = False
            return False
    
    def _ensure_token(self):
        """Ensure access token is valid."""
        if not self.access_token or datetime.now() >= self.token_expires:
            self.connect()
    
    def disconnect(self):
        """Disconnect from RESO Web API."""
        self.access_token = None
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
        """Search properties via RESO Web API."""
        import requests
        
        if not self.connected:
            raise ConnectionError("Not connected to MLS")
        
        self._ensure_token()
        
        # Build OData query
        query_params = []
        if city:
            query_params.append(f"City eq '{city}'")
        if zip_code:
            query_params.append(f"PostalCode eq '{zip_code}'")
        if min_price:
            query_params.append(f"ListPrice ge {min_price}")
        if max_price:
            query_params.append(f"ListPrice le {max_price}")
        if min_sqft:
            query_params.append(f"LivingArea ge {min_sqft}")
        if max_sqft:
            query_params.append(f"LivingArea le {max_sqft}")
        if bedrooms:
            query_params.append(f"BedroomsTotal eq {bedrooms}")
        if sold_after:
            query_params.append(f"CloseDate ge {sold_after.isoformat()}")
        
        filter_query = " and ".join(query_params) if query_params else ""
        url = f"{settings.reso_api_url}/Property"
        if filter_query:
            url += f"?$filter={filter_query}"
        url += f"&$top={limit}"
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            properties = []
            for item in data.get("value", []):
                prop = self._parse_reso_property(item)
                if prop:
                    properties.append(prop)
            
            return properties
        except Exception as e:
            logger.error(f"Error searching RESO Web API: {e}")
            return []
    
    def _parse_reso_property(self, data: Dict[str, Any]) -> Optional[Property]:
        """Parse RESO Web API property data."""
        try:
            return Property(
                mls_number=str(data.get("ListingId", "")),
                address=data.get("UnparsedAddress", ""),
                city=data.get("City", ""),
                state=data.get("StateOrProvince", ""),
                zip_code=data.get("PostalCode", ""),
                property_type=PropertyType(data.get("PropertyType", "Residential")),
                status=PropertyStatus(data.get("StandardStatus", "Active")),
                bedrooms=data.get("BedroomsTotal"),
                bathrooms=data.get("BathroomsTotalInteger"),
                square_feet=data.get("LivingArea"),
                lot_size=data.get("LotSizeAcres"),
                year_built=data.get("YearBuilt"),
                list_price=data.get("ListPrice"),
                sold_price=data.get("ClosePrice"),
                list_date=self._parse_iso_date(data.get("ListDate")),
                sold_date=self._parse_iso_date(data.get("CloseDate")),
                days_on_market=data.get("DaysOnMarket"),
                latitude=data.get("Latitude"),
                longitude=data.get("Longitude"),
                description=data.get("PublicRemarks", ""),
                mls_data=data
            )
        except Exception as e:
            logger.error(f"Error parsing RESO property: {e}")
            return None
    
    def _parse_iso_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO date string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None
    
    def get_property_by_mls(self, mls_number: str) -> Optional[Property]:
        """Get property by MLS number."""
        import requests
        
        self._ensure_token()
        url = f"{settings.reso_api_url}/Property('{mls_number}')"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return self._parse_reso_property(data)
        except Exception as e:
            logger.error(f"Error getting property by MLS: {e}")
            return None


def get_mls_connector() -> MLSConnector:
    """Factory function to get appropriate MLS connector.
    
    Note: This function is deprecated. The codebase now uses ATTOM only.
    Use ATTOMConnector directly instead.
    """
    # Default to ATTOM (only supported option now)
    from attom_connector import ATTOMConnector
    if not settings.attom_api_key:
        raise ValueError("ATTOM API key required. Set ATTOM_API_KEY in .env")
    return ATTOMConnector(settings.attom_api_key)

