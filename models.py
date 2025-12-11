"""Data models for properties and comps."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class PropertyType(str, Enum):
    """Property type enumeration."""
    RESIDENTIAL = "Residential"
    CONDO = "Condo/Co-op"
    TOWNHOUSE = "Townhouse"
    MULTI_FAMILY = "Multi-Family"
    COMMERCIAL = "Commercial"
    LAND = "Land"


class PropertyStatus(str, Enum):
    """Property listing status."""
    ACTIVE = "Active"
    PENDING = "Pending"
    SOLD = "Sold"
    OFF_MARKET = "Off Market"
    WITHDRAWN = "Withdrawn"
    EXPIRED = "Expired"


class Property(BaseModel):
    """Property model representing a real estate listing."""
    mls_number: str
    address: str
    city: str
    state: str
    zip_code: str
    property_type: PropertyType
    status: PropertyStatus
    
    # Property details
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    bathrooms_full: Optional[int] = None
    bathrooms_half: Optional[int] = None
    total_rooms: Optional[int] = None
    square_feet: Optional[int] = None
    lot_size_sqft: Optional[float] = None  # in square feet
    lot_size_acres: Optional[float] = None  # in acres (calculated)
    year_built: Optional[int] = None
    stories: Optional[int] = None
    
    # Parking
    parking_spaces: Optional[int] = None
    garage_type: Optional[str] = None
    
    # Property condition/features
    condition: Optional[str] = None  # e.g., "Excellent", "Good", "Fair", "Poor"
    architectural_style: Optional[str] = None  # e.g., "Colonial", "Ranch", "Contemporary"
    heating_type: Optional[str] = None
    cooling_type: Optional[str] = None
    roof_material: Optional[str] = None
    exterior_features: List[str] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)  # Pool, Fireplace, etc.
    
    # Upgrades and Renovations
    recent_upgrades: List[str] = Field(default_factory=list)  # e.g., "New Kitchen", "Finished Basement", "New Roof"
    renovation_year: Optional[int] = None
    major_repairs_needed: List[str] = Field(default_factory=list)
    
    # Location Features
    school_district: Optional[str] = None
    proximity_to_parks: Optional[bool] = None
    proximity_to_shopping: Optional[bool] = None
    proximity_to_highway: Optional[bool] = None
    waterfront_view: Optional[bool] = None
    view_type: Optional[str] = None  # e.g., "Mountain View", "City View", "Water View"
    
    # Pricing
    list_price: Optional[float] = None
    sold_price: Optional[float] = None
    price_per_sqft: Optional[float] = None
    
    # Dates
    list_date: Optional[datetime] = None
    sold_date: Optional[datetime] = None
    days_on_market: Optional[int] = None
    sale_recency_days: Optional[int] = None  # Days since sale (for comps)
    
    # Transaction Details
    seller_concessions: Optional[float] = None  # Amount of seller concessions
    seller_concessions_description: Optional[str] = None
    financing_type: Optional[str] = None  # e.g., "Conventional", "FHA", "Cash"
    arms_length_transaction: Optional[bool] = None  # True if arms-length sale
    
    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Photos/Images
    photos: List[str] = Field(default_factory=list)  # URLs to property photos
    street_view_url: Optional[str] = None  # Google Street View interactive URL
    street_view_image_url: Optional[str] = None  # Google Street View static image URL
    
    # Additional features
    features: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    
    # MLS metadata
    mls_data: dict = Field(default_factory=dict)
    
    def calculate_price_per_sqft(self) -> Optional[float]:
        """Calculate price per square foot."""
        price = self.sold_price or self.list_price
        if price and self.square_feet:
            return price / self.square_feet
        return None


class CompResult(BaseModel):
    """Result of comp analysis for a property."""
    subject_property: Property
    comparable_properties: List['CompProperty']
    average_price: Optional[float] = None
    average_price_per_sqft: Optional[float] = None
    estimated_value: Optional[float] = None
    confidence_score: float = 0.0


class Adjustment(BaseModel):
    """A dollar adjustment made to a comparable property."""
    category: str  # e.g., "Square Footage", "Bedrooms", "Bathrooms", "Condition", "Time", "Concessions", "Location"
    description: str
    amount: float  # Positive = add to comp price, Negative = subtract from comp price
    reason: str  # Why this adjustment was made


class CompProperty(BaseModel):
    """A comparable property with similarity score and adjustments."""
    property: Property
    similarity_score: float = Field(ge=0.0, le=1.0)
    distance_miles: Optional[float] = None
    price_difference: Optional[float] = None
    price_difference_percent: Optional[float] = None
    match_reasons: List[str] = Field(default_factory=list)
    
    # Professional adjustment fields
    adjustments: List[Adjustment] = Field(default_factory=list)
    adjusted_price: Optional[float] = None  # Comp price after all adjustments
    total_adjustment_amount: float = 0.0  # Sum of all adjustments
    adjustment_count: int = 0  # Number of adjustments made


# Update forward references
CompResult.model_rebuild()

