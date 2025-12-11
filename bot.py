"""Main bot interface for ATTOM comp analysis."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from attom_connector import ATTOMConnector
from comp_analyzer import CompAnalyzer
from comp_guidelines_trainer import CompGuidelinesTrainer
from config import settings
from models import CompResult, Property, PropertyStatus
from trainer import CompTrainer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def estimate_rooms_from_sqft(
    square_feet: Optional[int], property_type=None
) -> Tuple[Optional[int], Optional[float]]:
    """
    Estimate bedrooms and bathrooms from square footage when data is missing.
    Uses industry-standard averages based on typical home layouts:
    - Small homes (<1500 sqft): 2-3 bedrooms, 1-2 bathrooms
    - Medium homes (1500-2500 sqft): 3-4 bedrooms, 2-3 bathrooms
    - Large homes (2500-3500 sqft): 4-5 bedrooms, 3-4 bathrooms
    - Very large homes (>3500 sqft): 5-6 bedrooms, 4-5 bathrooms
    """
    if not square_feet or square_feet <= 0:
        return None, None

    # Use tiered estimation based on square footage ranges
    # This is more accurate than a simple ratio
    if square_feet < 1000:
        estimated_bedrooms = 2
        estimated_bathrooms = 1.0
    elif square_feet < 1500:
        estimated_bedrooms = 2
        estimated_bathrooms = 1.5
    elif square_feet < 2000:
        estimated_bedrooms = 3
        estimated_bathrooms = 2.0
    elif square_feet < 2500:
        estimated_bedrooms = 3
        estimated_bathrooms = 2.5
    elif square_feet < 3000:
        estimated_bedrooms = 4
        estimated_bathrooms = 3.0
    elif square_feet < 3500:
        estimated_bedrooms = 4
        estimated_bathrooms = 3.5
    elif square_feet < 4000:
        estimated_bedrooms = 5
        estimated_bathrooms = 4.0
    elif square_feet < 5000:
        estimated_bedrooms = 5
        estimated_bathrooms = 4.5
    else:
        # For very large homes, use ratio but cap reasonably
        estimated_bedrooms = min(6, max(5, int(square_feet / 800)))
        estimated_bathrooms = min(6.0, max(5.0, round(square_feet / 900, 1)))

    # Adjust for property type
    if property_type and hasattr(property_type, "value"):
        prop_type_str = property_type.value.lower()
        if "condo" in prop_type_str or "townhouse" in prop_type_str:
            # Condos/townhouses typically have 1 less bedroom for same sqft
            estimated_bedrooms = max(1, estimated_bedrooms - 1)
            estimated_bathrooms = max(1.0, estimated_bathrooms - 0.5)
        elif "multi" in prop_type_str:
            # Multi-family may have more bedrooms
            estimated_bedrooms = estimated_bedrooms + 1

    return estimated_bedrooms, estimated_bathrooms


class MLSCompBot:
    """Main bot class for finding comparable properties using ATTOM."""

    def __init__(self):
        self.connector: Optional[ATTOMConnector] = None
        self.analyzer = CompAnalyzer()
        self.trainer = CompTrainer(self.analyzer)
        self.guidelines_trainer = CompGuidelinesTrainer(self.analyzer)
        self.connected = False

    def connect(self) -> bool:
        """Connect to ATTOM API."""
        try:
            self.connector = ATTOMConnector()
            success = self.connector.connect()
            self.connected = success
            if success:
                logger.info("Bot connected to ATTOM API successfully")
            return success
        except Exception as e:
            logger.error(f"Failed to connect to ATTOM API: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from ATTOM API."""
        if self.connector:
            self.connector.disconnect()
        self.connected = False

    def find_comps_for_property(
        self,
        mls_number: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        max_comps: Optional[int] = None,
    ) -> Optional[CompResult]:
        """Find comparable properties for a given property using ATTOM."""
        if not self.connected:
            logger.error("Not connected to ATTOM API. Call connect() first.")
            return None

        # Get subject property - ATTOM requires address-based lookup
        # Note: We'll get better data from the v2 Sales Comparables response
        # So we'll use v1 for initial lookup, then enhance with v2 data
        subject = None

        if address and city:
            # First, try to get property by address
            # We'll enhance it later with v2 data which may include ATTOM ID
            subject = self.connector.get_property_by_address(
                address=address,
                city=city or "",
                state=state or "AZ",  # Default to AZ if not provided
                zip_code=zip_code,
            )
        elif mls_number:
            logger.warning(
                "ATTOM uses APN, not MLS numbers. Please provide address instead."
            )
            return None
        else:
            logger.error("Address and city are required for ATTOM API")
            return None

        if not subject:
            logger.error("Could not find subject property in ATTOM database")
            return None

        logger.info(
            f"Found subject property: {subject.address}, {subject.city}, {subject.state}"
        )

        # Use ATTOM's Sales Comparables endpoint
        sold_after = datetime.now() - timedelta(days=settings.max_comp_age_days)
        months_ago = (datetime.now() - sold_after).days // 30

        # For ATTOM, don't use assessed value for price filtering (it's too low)
        # Only filter by price if we have a realistic market value
        price_from = None
        price_to = None
        # If list_price seems like assessed value (too low), don't use it for filtering
        if subject.list_price and subject.list_price > 100000:
            price_from = subject.list_price * 0.7
            price_to = subject.list_price * 1.3

        # Use original input values if subject values are empty
        search_city = subject.city or city or "Mesa"
        search_state = subject.state or state or "AZ"
        search_zip = subject.zip_code or zip_code

        # Calculate similarity parameters for better comp matching
        # ATTOM's Sales Comparables endpoint uses these to find similar properties:
        # - bedroomsRange: ±1 bedroom tolerance
        # - bathroomRange: ±0.5 bathroom tolerance
        # - sqFeetRange: ±30% square footage tolerance
        # - yearBuiltRange: ±15 years age tolerance
        # The bot will then score and rank results by similarity

        logger.info(
            f"Searching for comparables with: {search_city}, {search_state}, sqft={subject.square_feet}, beds={subject.bedrooms}"
        )

        # Try initial search with standard criteria
        candidates = self.connector.get_sales_comparables(
            address=subject.address,
            city=search_city,
            state=search_state,
            zip_code=search_zip,
            miles=settings.max_comp_distance_miles,
            max_comps=(max_comps or settings.max_comps_to_return)
            * 3,  # Get more candidates to filter
            bedrooms_range=subject.bedrooms,  # ATTOM will use this with ±1 tolerance
            bathroom_range=subject.bathrooms,  # ATTOM will use this with ±0.5 tolerance
            sqft_range=subject.square_feet,  # ATTOM will calculate ±30% tolerance
            sale_date_range_months=min(
                max(months_ago, 6), 12
            ),  # At least 6 months, max 12
            sale_amount_from=price_from,
            sale_amount_to=price_to,
            year_built_range=15 if subject.year_built else None,  # ±15 years
        )

        # If no candidates found, try with relaxed criteria (rural/smaller areas)
        if not candidates:
            logger.info(
                "No comparables found with standard criteria. Trying with relaxed criteria..."
            )
            # Relax: increase radius, extend date range, remove price filters
            candidates = self.connector.get_sales_comparables(
                address=subject.address,
                city=search_city,
                state=search_state,
                zip_code=search_zip,
                miles=min(
                    settings.max_comp_distance_miles * 2, 10.0
                ),  # Double the radius, max 10 miles
                max_comps=(max_comps or settings.max_comps_to_return) * 3,
                bedrooms_range=None,  # Remove bedroom filter
                bathroom_range=None,  # Remove bathroom filter
                sqft_range=subject.square_feet,  # Keep sqft but it's already ±30%
                sale_date_range_months=12,  # Extend to 12 months
                sale_amount_from=None,  # Remove price filters
                sale_amount_to=None,
                year_built_range=None,  # Remove year built filter
            )
            if candidates:
                logger.info(f"Found {len(candidates)} candidates with relaxed criteria")

        logger.info(f"Found {len(candidates)} candidate properties")

        # Enhance subject property with data from v2 response if available
        # v2 response has much more complete data, so prefer it over v1
        # Check if v2 subject was extracted and stored
        v2_subject = None
        if hasattr(self.connector, "_last_subject_from_v2"):
            v2_subject = getattr(self.connector, "_last_subject_from_v2", None)
            logger.info(f"Checking for v2 subject: found={v2_subject is not None}")
            if v2_subject:
                logger.info(
                    f"v2 subject address: {v2_subject.address}, lot={v2_subject.lot_size_sqft}, rooms={v2_subject.total_rooms}"
                )

        if v2_subject:
            logger.info("Enhancing subject property with v2 response data")
            logger.info(
                f"v2 subject extracted: rooms={v2_subject.total_rooms}, lot_sqft={v2_subject.lot_size_sqft}, "
                f"lot_acres={v2_subject.lot_size_acres}, parking={v2_subject.parking_spaces}, "
                f"stories={v2_subject.stories}, heating={v2_subject.heating_type}, "
                f"cooling={v2_subject.cooling_type}, roof={v2_subject.roof_material}, "
                f"amenities={v2_subject.amenities}, exterior={v2_subject.exterior_features}"
            )

            # Replace subject with v2 data (v2 is more complete from Sales Comparables endpoint)
            # Keep v1 data only if v2 doesn't have it
            # IMPORTANT: Preserve v1 fields that v2 doesn't have (architectural_style, school_district, condition, etc.)

            # Store v1-only fields before overwriting
            v1_architectural_style = subject.architectural_style
            v1_condition = subject.condition
            v1_recent_upgrades = (
                subject.recent_upgrades.copy() if subject.recent_upgrades else []
            )
            v1_renovation_year = subject.renovation_year
            v1_major_repairs_needed = (
                subject.major_repairs_needed.copy()
                if subject.major_repairs_needed
                else []
            )
            v1_school_district = subject.school_district
            v1_proximity_to_parks = subject.proximity_to_parks
            v1_proximity_to_shopping = subject.proximity_to_shopping
            v1_proximity_to_highway = subject.proximity_to_highway
            v1_waterfront_view = subject.waterfront_view
            v1_view_type = subject.view_type
            v1_seller_concessions = subject.seller_concessions
            v1_seller_concessions_description = subject.seller_concessions_description
            v1_financing_type = subject.financing_type
            v1_arms_length_transaction = subject.arms_length_transaction
            v1_sold_price = subject.sold_price
            v1_sold_date = subject.sold_date
            v1_sale_recency_days = subject.sale_recency_days
            v1_price_per_sqft = subject.price_per_sqft

            # Update with v2 data
            subject.bedrooms = (
                v2_subject.bedrooms
                if v2_subject.bedrooms is not None
                else subject.bedrooms
            )
            subject.bathrooms = (
                v2_subject.bathrooms
                if v2_subject.bathrooms is not None
                else subject.bathrooms
            )
            subject.bathrooms_full = (
                v2_subject.bathrooms_full
                if v2_subject.bathrooms_full is not None
                else subject.bathrooms_full
            )
            subject.bathrooms_half = (
                v2_subject.bathrooms_half
                if v2_subject.bathrooms_half is not None
                else subject.bathrooms_half
            )
            subject.total_rooms = (
                v2_subject.total_rooms
                if v2_subject.total_rooms is not None
                else subject.total_rooms
            )
            subject.square_feet = (
                v2_subject.square_feet
                if v2_subject.square_feet is not None
                else subject.square_feet
            )
            subject.lot_size_sqft = (
                v2_subject.lot_size_sqft
                if v2_subject.lot_size_sqft is not None
                else subject.lot_size_sqft
            )
            subject.lot_size_acres = (
                v2_subject.lot_size_acres
                if v2_subject.lot_size_acres is not None
                else subject.lot_size_acres
            )
            subject.year_built = (
                v2_subject.year_built
                if v2_subject.year_built is not None
                else subject.year_built
            )
            subject.stories = (
                v2_subject.stories
                if v2_subject.stories is not None
                else subject.stories
            )
            subject.parking_spaces = (
                v2_subject.parking_spaces
                if v2_subject.parking_spaces is not None
                else subject.parking_spaces
            )
            subject.garage_type = (
                v2_subject.garage_type
                if v2_subject.garage_type
                else subject.garage_type
            )
            subject.heating_type = (
                v2_subject.heating_type
                if v2_subject.heating_type
                else subject.heating_type
            )
            subject.cooling_type = (
                v2_subject.cooling_type
                if v2_subject.cooling_type
                else subject.cooling_type
            )
            subject.roof_material = (
                v2_subject.roof_material
                if v2_subject.roof_material
                else subject.roof_material
            )
            # For lists, replace if v2 has data
            if v2_subject.exterior_features:
                subject.exterior_features = v2_subject.exterior_features
            if v2_subject.amenities:
                subject.amenities = v2_subject.amenities
            subject.street_view_url = (
                v2_subject.street_view_url
                if v2_subject.street_view_url
                else subject.street_view_url
            )
            subject.street_view_image_url = (
                v2_subject.street_view_image_url
                if v2_subject.street_view_image_url
                else subject.street_view_image_url
            )

            # Use better price from v2 if available
            if v2_subject.list_price:
                if (
                    not subject.list_price
                    or v2_subject.list_price > subject.list_price * 1.5
                ):
                    subject.list_price = v2_subject.list_price

            # Restore v1-only fields (v2 doesn't have these, so preserve from v1)
            subject.architectural_style = v1_architectural_style
            subject.condition = v1_condition
            subject.recent_upgrades = v1_recent_upgrades
            subject.renovation_year = v1_renovation_year
            subject.major_repairs_needed = v1_major_repairs_needed
            subject.school_district = v1_school_district
            subject.proximity_to_parks = v1_proximity_to_parks
            subject.proximity_to_shopping = v1_proximity_to_shopping
            subject.proximity_to_highway = v1_proximity_to_highway
            subject.waterfront_view = v1_waterfront_view
            subject.view_type = v1_view_type

            # Preserve v1 transaction data, but use v2 if it's more complete
            if v2_subject.sold_price:
                subject.sold_price = v2_subject.sold_price
            elif v1_sold_price:
                subject.sold_price = v1_sold_price

            if v2_subject.sold_date:
                subject.sold_date = v2_subject.sold_date
            elif v1_sold_date:
                subject.sold_date = v1_sold_date

            if v2_subject.sale_recency_days is not None:
                subject.sale_recency_days = v2_subject.sale_recency_days
            elif v1_sale_recency_days is not None:
                subject.sale_recency_days = v1_sale_recency_days

            if v2_subject.price_per_sqft:
                subject.price_per_sqft = v2_subject.price_per_sqft
            elif v1_price_per_sqft:
                subject.price_per_sqft = v1_price_per_sqft

            # Preserve v1 transaction details (v2 may have some, but v1 might be more complete)
            if v2_subject.arms_length_transaction is not None:
                subject.arms_length_transaction = v2_subject.arms_length_transaction
            elif v1_arms_length_transaction is not None:
                subject.arms_length_transaction = v1_arms_length_transaction

            if v2_subject.financing_type:
                subject.financing_type = v2_subject.financing_type
            elif v1_financing_type:
                subject.financing_type = v1_financing_type

            # Seller concessions are only in v1, so always preserve
            subject.seller_concessions = v1_seller_concessions
            subject.seller_concessions_description = v1_seller_concessions_description

            logger.info(
                f"Final enhanced subject: rooms={subject.total_rooms}, lot_sqft={subject.lot_size_sqft}, "
                f"lot_acres={subject.lot_size_acres}, parking={subject.parking_spaces}, "
                f"stories={subject.stories}, heating={subject.heating_type}, cooling={subject.cooling_type}, "
                f"roof={subject.roof_material}, amenities={len(subject.amenities) if subject.amenities else 0}, "
                f"exterior_features={len(subject.exterior_features) if subject.exterior_features else 0}"
            )

            # Enrich with additional ATTOM APIs (School, Assessment, Sale, AVM)
            subject = self.connector.enrich_property_with_additional_data(
                subject, max_api_calls=3
            )

        else:
            logger.warning("No v2 subject data available for enhancement")

        # Try Estated API as fallback if bedrooms/bathrooms are missing
        # NOTE: Estated is being deprecated in 2026 and migrated to ATTOM
        # This is a temporary fallback until ATTOM completes their migration
        if settings.estated_enabled and settings.estated_api_key:
            if subject.bedrooms is None or subject.bathrooms is None:
                try:
                    from alternative_apis import EstatedAPIConnector

                    logger.info(
                        "Attempting to fetch missing data from Estated API (deprecated 2026 - migrating to ATTOM)..."
                    )
                    estated = EstatedAPIConnector(settings.estated_api_key)
                    estated.connect()
                    estated_prop = estated.get_property_by_address(
                        subject.address, subject.city, subject.state, subject.zip_code
                    )

                    if estated_prop:
                        # Fill in missing bedrooms
                        if (
                            subject.bedrooms is None
                            and estated_prop.bedrooms is not None
                        ):
                            subject.bedrooms = estated_prop.bedrooms
                            logger.info(
                                f"✓ Got bedrooms from Estated: {estated_prop.bedrooms}"
                            )

                        # Fill in missing bathrooms
                        if (
                            subject.bathrooms is None
                            and estated_prop.bathrooms is not None
                        ):
                            subject.bathrooms = estated_prop.bathrooms
                            logger.info(
                                f"✓ Got bathrooms from Estated: {estated_prop.bathrooms}"
                            )

                        # Fill in other missing fields if available
                        if subject.square_feet is None and estated_prop.square_feet:
                            subject.square_feet = estated_prop.square_feet
                        if subject.lot_size_sqft is None and estated_prop.lot_size_sqft:
                            subject.lot_size_sqft = estated_prop.lot_size_sqft
                        if (
                            subject.lot_size_acres is None
                            and estated_prop.lot_size_acres
                        ):
                            subject.lot_size_acres = estated_prop.lot_size_acres
                        if subject.year_built is None and estated_prop.year_built:
                            subject.year_built = estated_prop.year_built
                        if (
                            subject.parking_spaces is None
                            and estated_prop.parking_spaces
                        ):
                            subject.parking_spaces = estated_prop.parking_spaces
                        if not subject.garage_type and estated_prop.garage_type:
                            subject.garage_type = estated_prop.garage_type
                    else:
                        logger.warning("Estated API did not return property data")
                except Exception as e:
                    logger.warning(f"Estated API fallback failed: {e}")

        # Try Oxylabs Web Scraper as fallback if bedrooms/bathrooms are still missing
        # NOTE: This scrapes Redfin/Zillow - be aware of ToS considerations
        if (
            settings.oxylabs_enabled
            and settings.oxylabs_username
            and settings.oxylabs_password
        ):
            if subject.bedrooms is None or subject.bathrooms is None:
                try:
                    from alternative_apis import OxylabsScraperConnector

                    logger.info(
                        "Attempting to fetch missing data from Oxylabs (scraping Redfin/Zillow)..."
                    )
                    oxylabs = OxylabsScraperConnector(
                        settings.oxylabs_username, settings.oxylabs_password
                    )
                    oxylabs.connect()
                    oxylabs_prop = oxylabs.get_property_by_address(
                        subject.address, subject.city, subject.state, subject.zip_code
                    )

                    if oxylabs_prop:
                        # Fill in missing bedrooms
                        if (
                            subject.bedrooms is None
                            and oxylabs_prop.bedrooms is not None
                        ):
                            subject.bedrooms = oxylabs_prop.bedrooms
                            logger.info(
                                f"✓ Got bedrooms from Oxylabs: {oxylabs_prop.bedrooms}"
                            )

                        # Fill in missing bathrooms
                        if (
                            subject.bathrooms is None
                            and oxylabs_prop.bathrooms is not None
                        ):
                            subject.bathrooms = oxylabs_prop.bathrooms
                            logger.info(
                                f"✓ Got bathrooms from Oxylabs: {oxylabs_prop.bathrooms}"
                            )

                        # Fill in other missing fields if available
                        if subject.square_feet is None and oxylabs_prop.square_feet:
                            subject.square_feet = oxylabs_prop.square_feet
                        if subject.lot_size_sqft is None and oxylabs_prop.lot_size_sqft:
                            subject.lot_size_sqft = oxylabs_prop.lot_size_sqft
                        if subject.year_built is None and oxylabs_prop.year_built:
                            subject.year_built = oxylabs_prop.year_built
                        if subject.list_price is None and oxylabs_prop.list_price:
                            subject.list_price = oxylabs_prop.list_price
                        
                        # NEW: Extract additional fields from Oxylabs/Zillow
                        if subject.cooling_type is None and oxylabs_prop.cooling_type:
                            subject.cooling_type = oxylabs_prop.cooling_type
                            logger.info(f"✓ Got cooling type from Oxylabs: {oxylabs_prop.cooling_type}")
                        if subject.heating_type is None and oxylabs_prop.heating_type:
                            subject.heating_type = oxylabs_prop.heating_type
                            logger.info(f"✓ Got heating type from Oxylabs: {oxylabs_prop.heating_type}")
                        if subject.roof_material is None and oxylabs_prop.roof_material:
                            subject.roof_material = oxylabs_prop.roof_material
                        if subject.architectural_style is None and oxylabs_prop.architectural_style:
                            subject.architectural_style = oxylabs_prop.architectural_style
                            logger.info(f"✓ Got architectural style from Oxylabs: {oxylabs_prop.architectural_style}")
                        if subject.stories is None and oxylabs_prop.stories:
                            subject.stories = oxylabs_prop.stories
                        if subject.parking_spaces is None and oxylabs_prop.parking_spaces:
                            subject.parking_spaces = oxylabs_prop.parking_spaces
                        if not subject.amenities and oxylabs_prop.amenities:
                            subject.amenities = oxylabs_prop.amenities
                        if not subject.exterior_features and oxylabs_prop.exterior_features:
                            subject.exterior_features = oxylabs_prop.exterior_features
                        
                        # Merge mls_data for additional fields (HOA, subdivision, etc.)
                        if oxylabs_prop.mls_data:
                            if not subject.mls_data:
                                subject.mls_data = {}
                            oxylabs_extras = oxylabs_prop.mls_data
                            if oxylabs_extras.get("hoa_fee"):
                                subject.mls_data["hoa_fee"] = oxylabs_extras["hoa_fee"]
                                logger.info(f"✓ Got HOA fee from Oxylabs: ${oxylabs_extras['hoa_fee']}/mo")
                            if oxylabs_extras.get("subdivision"):
                                subject.mls_data["subdivision"] = oxylabs_extras["subdivision"]
                            if oxylabs_extras.get("has_pool"):
                                subject.mls_data["has_pool"] = oxylabs_extras["has_pool"]
                            subject.mls_data["oxylabs_source"] = oxylabs_extras.get("source", "oxylabs")
                    else:
                        logger.warning("Oxylabs did not return property data")
                except Exception as e:
                    logger.warning(f"Oxylabs fallback failed: {e}")

        # Try PropertyRadar API for investor data (equity, liens, ownership)
        # NOTE: PropertyRadar excels at investor data but may not have bedrooms
        if settings.propertyradar_enabled and settings.propertyradar_api_key:
            try:
                from alternative_apis import PropertyRadarConnector

                logger.info(
                    "Attempting to fetch investor data from PropertyRadar API..."
                )
                pr_connector = PropertyRadarConnector(settings.propertyradar_api_key)
                pr_connector.connect()
                
                # PropertyRadar is best for investor data, merge with existing
                pr_prop = pr_connector.get_property_by_address(
                    subject.address, subject.city, subject.state, subject.zip_code
                )

                if pr_prop and pr_prop.mls_data:
                    if not subject.mls_data:
                        subject.mls_data = {}
                    
                    pr_data = pr_prop.mls_data
                    
                    # Investor data that ATTOM/Oxylabs don't have
                    if pr_data.get("avm"):
                        subject.mls_data["propertyradar_avm"] = pr_data["avm"]
                        logger.info(f"✓ Got AVM from PropertyRadar: ${pr_data['avm']:,}")
                    if pr_data.get("available_equity"):
                        subject.mls_data["available_equity"] = pr_data["available_equity"]
                        logger.info(f"✓ Got equity from PropertyRadar: ${pr_data['available_equity']:,}")
                    if pr_data.get("is_free_and_clear"):
                        subject.mls_data["is_free_and_clear"] = True
                        logger.info("✓ Property is FREE AND CLEAR (no mortgage)")
                    if pr_data.get("is_cash_buyer"):
                        subject.mls_data["is_cash_buyer"] = True
                    if pr_data.get("is_absentee_owner"):
                        subject.mls_data["is_absentee_owner"] = True
                    if pr_data.get("subdivision") and not subject.mls_data.get("subdivision"):
                        subject.mls_data["subdivision"] = pr_data["subdivision"]
                    if pr_data.get("zoning"):
                        subject.mls_data["zoning"] = pr_data["zoning"]
                    
                    # Fill physical data if still missing
                    if subject.bathrooms is None and pr_prop.bathrooms:
                        subject.bathrooms = pr_prop.bathrooms
                    if subject.stories is None and pr_prop.stories:
                        subject.stories = pr_prop.stories
                    if subject.roof_material is None and pr_prop.roof_material:
                        subject.roof_material = pr_prop.roof_material
                    
                    subject.mls_data["propertyradar_source"] = True
                    logger.info("✓ PropertyRadar investor data merged successfully")
            except Exception as e:
                logger.warning(f"PropertyRadar fallback failed: {e}")

        # Estimate bedrooms/bathrooms from square footage if still missing
        if (
            subject.bedrooms is None or subject.bathrooms is None
        ) and subject.square_feet:
            estimated_beds, estimated_baths = estimate_rooms_from_sqft(
                subject.square_feet, subject.property_type
            )
            if subject.bedrooms is None and estimated_beds:
                subject.bedrooms = estimated_beds
                logger.info(
                    f"Estimated bedrooms from sqft: {estimated_beds} (based on {subject.square_feet:,} sqft)"
                )
            if subject.bathrooms is None and estimated_baths:
                subject.bathrooms = estimated_baths
                logger.info(
                    f"Estimated bathrooms from sqft: {estimated_baths} (based on {subject.square_feet:,} sqft)"
                )

        # Find comps
        comp_result = self.analyzer.find_comps(subject, candidates, max_comps=max_comps)

        # Enrich comps with additional ATTOM APIs (limit to top comps to avoid too many API calls)
        if comp_result.comparable_properties:
            enriched_count = 0
            for comp in comp_result.comparable_properties[
                :5
            ]:  # Only enrich top 5 comps
                if enriched_count >= 2:  # Limit total API calls for comps
                    break
                original_property = comp.property
                enriched_property = self.connector.enrich_property_with_additional_data(
                    original_property, max_api_calls=2
                )
                if enriched_property != original_property:
                    comp.property = enriched_property
                    enriched_count += 1

        # Record for learning
        if settings.enable_learning:
            self.analyzer.record_comp_selection(
                subject, comp_result.comparable_properties
            )

        return comp_result

    def find_comps_by_criteria(
        self,
        city: str,
        state: str = "AZ",
        property_type: Optional[str] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        square_feet: Optional[int] = None,
        list_price: Optional[float] = None,
        zip_code: Optional[str] = None,
        max_comps: Optional[int] = None,
    ) -> Optional[CompResult]:
        """Find comps by criteria - ATTOM requires an address, so this creates a virtual search."""
        if not self.connected:
            logger.error("Not connected to ATTOM API. Call connect() first.")
            return None

        logger.warning(
            "ATTOM API requires a specific address. Use find_comps_for_property() with an address instead."
        )
        return None

    def train_model(self):
        """Train the model using collected learning data."""
        if not settings.enable_learning:
            logger.warning("Learning is disabled in settings")
            return

        learning_data = self.analyzer.learning_data
        if not learning_data:
            logger.warning("No learning data available")
            return

        logger.info(f"Training model with {len(learning_data)} records")
        self.trainer.train_from_feedback(learning_data)
        logger.info("Model training completed")

    def provide_feedback(
        self, comp_result: CompResult, rating: float, notes: Optional[str] = None
    ):
        """Provide feedback on comp results for learning."""
        if not settings.enable_learning:
            return

        # Update the learning data with feedback
        for record in self.analyzer.learning_data:
            if record["subject"].mls_number == comp_result.subject_property.mls_number:
                record["user_feedback"] = rating
                if notes:
                    record["notes"] = notes
                break

        # Retrain if we have enough data
        if len(self.analyzer.learning_data) >= 10:
            self.train_model()
