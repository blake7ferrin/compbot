"""Flask web application for Robo Comp - AI Property Valuation."""

import logging
import sys
import os

from flask import Flask, jsonify, render_template, request, send_from_directory

from bot import MLSCompBot
from config import settings
from report_generator import ReportGenerator
from models import Property

# Configure logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("flask_app.log", mode="a"),
    ],
)

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates"),
)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "robocomp-secret-key-2025")

# Initialize bot (will connect on first use)
bot = None


def get_bot():
    """Get or initialize the bot."""
    global bot
    if bot is None:
        bot = MLSCompBot()
        if not bot.connect():
            # Make failures obvious (usually missing ATTOM_API_KEY)
            raise RuntimeError(
                "Failed to connect to ATTOM API. Set ATTOM_API_KEY in your .env and restart the server."
            )
    return bot


def _mask_secret(value: str, keep: int = 4) -> str:
    """Mask a secret for safe display in debug/status endpoints."""
    if not value:
        return ""
    value = str(value)
    if len(value) <= keep:
        return "*" * len(value)
    return f"{value[:keep]}{'*' * (len(value) - keep)}"


def _missing_fields(prop: Property, fields: list[str]) -> list[str]:
    """Return a list of field names that are missing/empty on a Property."""
    missing: list[str] = []
    data = prop.model_dump()
    for field in fields:
        value = data.get(field)
        if value is None:
            missing.append(field)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(field)
            continue
        if isinstance(value, list) and len(value) == 0:
            missing.append(field)
            continue
        if isinstance(value, dict) and len(value) == 0:
            missing.append(field)
            continue
    return missing


@app.route("/api/status")
def api_status():
    """Lightweight status endpoint to help debug config/runtime issues (no secrets)."""
    try:
        attom_key = settings.attom_api_key or ""
        bot_connected = False
        connector_status = {}
        attom_debug_path = os.path.join(os.getcwd(), "attom_response_debug.json")
        flask_log_path = os.path.join(os.getcwd(), "flask_app.log")

        global bot
        if bot is not None:
            bot_connected = bool(getattr(bot, "connected", False))
            connector = getattr(bot, "connector", None)
            if connector is not None:
                connector_status = {
                    "connected": bool(getattr(connector, "connected", False)),
                    "last_status_code": getattr(connector, "last_status_code", None),
                    "last_error": getattr(connector, "last_error", None),
                    "last_endpoint": getattr(connector, "last_endpoint", None),
                }

        return jsonify(
            {
                "success": True,
                "cwd": os.getcwd(),
                "env_file_present": os.path.exists(os.path.join(os.getcwd(), ".env")),
                "attom_response_debug_present": os.path.exists(attom_debug_path),
                "attom_response_debug_size": (
                    os.path.getsize(attom_debug_path)
                    if os.path.exists(attom_debug_path)
                    else None
                ),
                "flask_app_log_present": os.path.exists(flask_log_path),
                "flask_app_log_size": (
                    os.path.getsize(flask_log_path)
                    if os.path.exists(flask_log_path)
                    else None
                ),
                "attom_api_key_configured": bool(attom_key),
                "attom_api_key_masked": (
                    _mask_secret(attom_key, keep=4) if attom_key else ""
                ),
                "estated_enabled": bool(
                    settings.estated_enabled and settings.estated_api_key
                ),
                "maricopa_assessor_enabled": bool(
                    settings.maricopa_assessor_enabled
                    and settings.maricopa_assessor_base_url
                ),
                "maricopa_assessor_base_url_configured": bool(
                    settings.maricopa_assessor_base_url
                ),
                "maricopa_assessor_api_key_configured": bool(
                    settings.maricopa_assessor_api_key
                ),
                "maricopa_assessor_api_key_masked": (
                    _mask_secret(settings.maricopa_assessor_api_key, keep=4)
                    if settings.maricopa_assessor_api_key
                    else ""
                ),
                "bot_initialized": bot is not None,
                "bot_connected": bot_connected,
                "connector": connector_status,
            }
        )
    except Exception as e:
        logging.error(f"Error in /api/status: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/")
def index():
    """Main page with search form."""
    return render_template(
        "index.html", google_maps_api_key=settings.google_maps_api_key
    )


@app.route("/test-v1-response")
def test_v1_response():
    """Test endpoint to see what v1 API actually returns."""
    try:
        address = request.args.get("address", "3644 E CONSTITUTION DR")
        city = request.args.get("city", "GILBERT")
        state = request.args.get("state", "AZ")
        zip_code = request.args.get("zip", "85296")

        from attom_connector import ATTOMConnector

        connector = ATTOMConnector()
        connector.connect()

        # Get property from v1 API
        property_obj = connector.get_property_by_address(address, city, state, zip_code)

        if property_obj:
            return jsonify(
                {
                    "success": True,
                    "property": {
                        "architectural_style": property_obj.architectural_style,
                        "school_district": property_obj.school_district,
                        "condition": property_obj.condition,
                        "renovation_year": property_obj.renovation_year,
                        "seller_concessions": property_obj.seller_concessions,
                        "seller_concessions_description": property_obj.seller_concessions_description,
                        "financing_type": property_obj.financing_type,
                        "arms_length_transaction": property_obj.arms_length_transaction,
                        "all_fields": property_obj.model_dump(),
                    },
                }
            )
        else:
            return jsonify({"success": False, "error": "Could not retrieve property"})
    except Exception as e:
        import traceback

        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        )


@app.route("/test-extraction")
def test_extraction():
    """Test endpoint to check data extraction."""
    import json

    try:
        with open("attom_response_debug.json", "r") as f:
            data = json.load(f)

        from attom_connector import ATTOMConnector

        connector = ATTOMConnector()

        subject_data = data["RESPONSE_GROUP"]["RESPONSE"]["RESPONSE_DATA"][
            "PROPERTY_INFORMATION_RESPONSE_ext"
        ]["SUBJECT_PROPERTY_ext"]["PROPERTY"][0]
        parsed = connector._parse_subject_property_v2(subject_data)

        if parsed:
            return jsonify(
                {
                    "success": True,
                    "raw_lot_size": subject_data.get("SITE", {}).get(
                        "@LotSquareFeetCount"
                    ),
                    "raw_total_rooms": subject_data.get("STRUCTURE", {}).get(
                        "@TotalRoomCount"
                    ),
                    "raw_parking": subject_data.get("STRUCTURE", {})
                    .get("CAR_STORAGE", {})
                    .get("CAR_STORAGE_LOCATION", {})
                    .get("@_ParkingSpacesCount"),
                    "parsed": {
                        "lot_size_sqft": parsed.lot_size_sqft,
                        "lot_size_acres": parsed.lot_size_acres,
                        "total_rooms": parsed.total_rooms,
                        "stories": parsed.stories,
                        "parking_spaces": parsed.parking_spaces,
                        "heating_type": parsed.heating_type,
                        "cooling_type": parsed.cooling_type,
                        "amenities": parsed.amenities,
                        "exterior_features": parsed.exterior_features,
                    },
                }
            )
        else:
            return jsonify({"success": False, "error": "Failed to parse"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/test-full-flow")
def test_full_flow():
    """Test the full flow: extraction -> enhancement -> JSON output."""
    import json

    from bot import MLSCompBot

    try:
        bot = MLSCompBot()
        bot.connect()

        # Use the address from the debug file
        result = bot.find_comps_for_property(
            address="3644 E CONSTITUTION DR",
            city="GILBERT",
            state="AZ",
            zip_code="85296",
            max_comps=5,
        )

        if result:
            subject = result.subject_property
            return jsonify(
                {
                    "success": True,
                    "subject_data": {
                        "lot_size_sqft": subject.lot_size_sqft,
                        "lot_size_acres": subject.lot_size_acres,
                        "total_rooms": subject.total_rooms,
                        "stories": subject.stories,
                        "parking_spaces": subject.parking_spaces,
                        "heating_type": subject.heating_type,
                        "cooling_type": subject.cooling_type,
                        "amenities": subject.amenities,
                        "exterior_features": subject.exterior_features,
                    },
                    "has_v2_data": hasattr(bot.connector, "_last_subject_from_v2")
                    and bot.connector._last_subject_from_v2 is not None,
                }
            )
        else:
            return jsonify({"success": False, "error": "No result returned"})
    except Exception as e:
        import traceback

        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        )


@app.route("/search", methods=["POST"])
def search():
    """Handle search request."""
    try:
        data = request.get_json() or request.form

        address = data.get("address", "").strip()
        city = data.get("city", "").strip()
        state = data.get("state", "").strip()
        zip_code = data.get("zip", "").strip()
        email = data.get("email", "").strip()
        try:
            max_comps = int(data.get("max_comps", 10))
        except (ValueError, TypeError):
            max_comps = 10

        if not address or not city or not state:
            return jsonify({"error": "Address, city, and state are required"}), 400

        # Get bot and search
        try:
            bot_instance = get_bot()
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        result = bot_instance.find_comps_for_property(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code if zip_code else None,
            max_comps=max_comps,
        )

        if not result:
            # Provide a more actionable error message depending on what failed.
            connector = getattr(bot_instance, "connector", None)
            status_code = (
                getattr(connector, "last_status_code", None) if connector else None
            )
            connector_error = (
                getattr(connector, "last_error", None) if connector else None
            )
            bot_error = getattr(bot_instance, "last_error", None)

            if status_code in (401, 403):
                msg = "ATTOM rejected the request (401/403). Verify ATTOM_API_KEY and that your plan includes this endpoint."
                return (
                    jsonify(
                        {
                            "error": msg,
                            "details": connector_error,
                            "bot_error": bot_error,
                        }
                    ),
                    502,
                )
            if status_code == 429:
                msg = "ATTOM rate limit reached (429). Wait a bit and try again."
                return (
                    jsonify(
                        {
                            "error": msg,
                            "details": connector_error,
                            "bot_error": bot_error,
                        }
                    ),
                    502,
                )
            if bot_error and str(bot_error).startswith("subject_not_found"):
                msg = "ATTOM could not find that subject property. Double-check the address, and try including the ZIP code."
                return (
                    jsonify(
                        {
                            "error": msg,
                            "details": connector_error,
                            "bot_error": bot_error,
                        }
                    ),
                    404,
                )
            if bot_error and str(bot_error).startswith("no_comps"):
                msg = "ATTOM returned no comps for that property with current criteria. Try increasing radius or widening the sale date range."
                return (
                    jsonify(
                        {
                            "error": msg,
                            "details": connector_error,
                            "bot_error": bot_error,
                        }
                    ),
                    404,
                )

            # Generic fallback
            return (
                jsonify(
                    {
                        "error": "Could not find comparable properties. Try adjusting your search criteria.",
                        "details": connector_error,
                        "bot_error": bot_error,
                    }
                ),
                404,
            )

        # Log subject property data for debugging
        subject = result.subject_property
        logging.info("=" * 80)
        logging.info("SUBJECT PROPERTY DATA BEING SENT TO FRONTEND:")
        logging.info(f"  Lot Size (sqft): {subject.lot_size_sqft}")
        logging.info(f"  Lot Size (acres): {subject.lot_size_acres}")
        logging.info(f"  Total Rooms: {subject.total_rooms}")
        logging.info(f"  Stories: {subject.stories}")
        logging.info(f"  Parking Spaces: {subject.parking_spaces}")
        logging.info(f"  Heating Type: {subject.heating_type}")
        logging.info(f"  Cooling Type: {subject.cooling_type}")
        logging.info(f"  Roof Material: {subject.roof_material}")
        logging.info(f"  Amenities: {subject.amenities}")
        logging.info(f"  Exterior Features: {subject.exterior_features}")
        logging.info("=" * 80)

        # Convert result to JSON-serializable format
        debug_enabled = str(request.args.get("debug", "")).lower() in {
            "1",
            "true",
            "yes",
        }

        # Full dumps (helpful for debugging + ensures the UI can access any field we add later)
        subject_full = result.subject_property.model_dump(mode="json")
        comps_full = [cp.model_dump(mode="json") for cp in result.comparable_properties]

        output = {
            "subject_property": {
                "address": result.subject_property.address,
                "city": result.subject_property.city,
                "state": result.subject_property.state,
                "zip_code": result.subject_property.zip_code,
                "mls_number": result.subject_property.mls_number,
                "property_type": result.subject_property.property_type.value,
                "status": (
                    result.subject_property.status.value
                    if getattr(result.subject_property, "status", None) is not None
                    else None
                ),
                "bedrooms": result.subject_property.bedrooms,
                "bathrooms": result.subject_property.bathrooms,
                "bathrooms_full": result.subject_property.bathrooms_full,
                "bathrooms_half": result.subject_property.bathrooms_half,
                "total_rooms": result.subject_property.total_rooms,
                "square_feet": result.subject_property.square_feet,
                "lot_size_sqft": result.subject_property.lot_size_sqft,
                "lot_size_acres": result.subject_property.lot_size_acres,
                "year_built": result.subject_property.year_built,
                "stories": result.subject_property.stories,
                "parking_spaces": result.subject_property.parking_spaces,
                "garage_type": result.subject_property.garage_type,
                "heating_type": result.subject_property.heating_type,
                "cooling_type": result.subject_property.cooling_type,
                "roof_material": result.subject_property.roof_material,
                "exterior_features": result.subject_property.exterior_features,
                "amenities": result.subject_property.amenities,
                "architectural_style": result.subject_property.architectural_style,
                "condition": result.subject_property.condition,
                "recent_upgrades": result.subject_property.recent_upgrades,
                "renovation_year": result.subject_property.renovation_year,
                "major_repairs_needed": result.subject_property.major_repairs_needed,
                "school_district": result.subject_property.school_district,
                "proximity_to_parks": result.subject_property.proximity_to_parks,
                "proximity_to_shopping": result.subject_property.proximity_to_shopping,
                "proximity_to_highway": result.subject_property.proximity_to_highway,
                "waterfront_view": result.subject_property.waterfront_view,
                "view_type": result.subject_property.view_type,
                "list_price": result.subject_property.list_price,
                "sold_price": result.subject_property.sold_price,
                "price_per_sqft": result.subject_property.price_per_sqft,
                "list_date": (
                    result.subject_property.list_date.isoformat()
                    if result.subject_property.list_date
                    else None
                ),
                "sold_date": (
                    result.subject_property.sold_date.isoformat()
                    if result.subject_property.sold_date
                    else None
                ),
                # Backward compatible: historically this endpoint exposed the "source DOM"
                # from mls_data under the days_on_market key.
                "days_on_market": (
                    result.subject_property.mls_data.get("days_on_market")
                    if result.subject_property.mls_data
                    else None
                ),
                # New: listing-level DOM on the Property model (if present)
                "days_on_market_listing": result.subject_property.days_on_market,
                "sale_recency_days": result.subject_property.sale_recency_days,
                "seller_concessions": result.subject_property.seller_concessions,
                "seller_concessions_description": result.subject_property.seller_concessions_description,
                "financing_type": result.subject_property.financing_type,
                "arms_length_transaction": result.subject_property.arms_length_transaction,
                "latitude": result.subject_property.latitude,
                "longitude": result.subject_property.longitude,
                "photos": result.subject_property.photos,
                "features": result.subject_property.features,
                "description": result.subject_property.description,
                "street_view_url": result.subject_property.street_view_url,
                "street_view_image_url": result.subject_property.street_view_image_url,
                # Pass through any source metadata (e.g., Oxylabs DOM/description)
                "mls_data": result.subject_property.mls_data,
                # Convenience fields for UI
                "days_on_market_source": (
                    result.subject_property.mls_data.get("days_on_market")
                    if result.subject_property.mls_data
                    else None
                ),
                "property_description": (
                    result.subject_property.mls_data.get("property_description")
                    if result.subject_property.mls_data
                    else None
                ),
            },
            "comparable_properties": [
                {
                    "address": cp.property.address,
                    "city": cp.property.city,
                    "state": cp.property.state,
                    "zip_code": cp.property.zip_code,
                    "mls_number": cp.property.mls_number,
                    "similarity_score": cp.similarity_score,
                    "distance_miles": cp.distance_miles,
                    "bedrooms": cp.property.bedrooms,
                    "bathrooms": cp.property.bathrooms,
                    "bathrooms_full": cp.property.bathrooms_full,
                    "bathrooms_half": cp.property.bathrooms_half,
                    "total_rooms": cp.property.total_rooms,
                    "square_feet": cp.property.square_feet,
                    "lot_size_sqft": cp.property.lot_size_sqft,
                    "lot_size_acres": cp.property.lot_size_acres,
                    "year_built": cp.property.year_built,
                    "stories": cp.property.stories,
                    "parking_spaces": cp.property.parking_spaces,
                    "garage_type": cp.property.garage_type,
                    "heating_type": cp.property.heating_type,
                    "cooling_type": cp.property.cooling_type,
                    "roof_material": cp.property.roof_material,
                    "exterior_features": cp.property.exterior_features,
                    "amenities": cp.property.amenities,
                    "architectural_style": cp.property.architectural_style,
                    "condition": cp.property.condition,
                    "recent_upgrades": cp.property.recent_upgrades,
                    "renovation_year": cp.property.renovation_year,
                    "major_repairs_needed": cp.property.major_repairs_needed,
                    "school_district": cp.property.school_district,
                    "proximity_to_parks": cp.property.proximity_to_parks,
                    "proximity_to_shopping": cp.property.proximity_to_shopping,
                    "proximity_to_highway": cp.property.proximity_to_highway,
                    "waterfront_view": cp.property.waterfront_view,
                    "view_type": cp.property.view_type,
                    "sold_price": cp.property.sold_price,
                    "list_price": cp.property.list_price,
                    "price_per_sqft": cp.property.price_per_sqft,
                    "list_date": (
                        cp.property.list_date.isoformat()
                        if cp.property.list_date
                        else None
                    ),
                    "sold_date": (
                        cp.property.sold_date.isoformat()
                        if cp.property.sold_date
                        else None
                    ),
                    "days_on_market": (
                        cp.property.mls_data.get("days_on_market")
                        if cp.property.mls_data
                        else None
                    ),
                    "days_on_market_listing": cp.property.days_on_market,
                    "sale_recency_days": cp.property.sale_recency_days,
                    "seller_concessions": cp.property.seller_concessions,
                    "seller_concessions_description": cp.property.seller_concessions_description,
                    "financing_type": cp.property.financing_type,
                    "arms_length_transaction": cp.property.arms_length_transaction,
                    "price_difference": cp.price_difference,
                    "price_difference_percent": cp.price_difference_percent,
                    "match_reasons": cp.match_reasons,
                    "adjustment_count": cp.adjustment_count,
                    "total_adjustment_amount": cp.total_adjustment_amount,
                    "adjusted_price": cp.adjusted_price,
                    "adjustments": [
                        adj.model_dump(mode="json") for adj in cp.adjustments
                    ],
                    "street_view_url": cp.property.street_view_url,
                    "street_view_image_url": cp.property.street_view_image_url,
                    # Source metadata (e.g., Oxylabs)
                    "mls_data": cp.property.mls_data,
                    "days_on_market_source": (
                        cp.property.mls_data.get("days_on_market")
                        if cp.property.mls_data
                        else None
                    ),
                    "property_description": (
                        cp.property.mls_data.get("property_description")
                        if cp.property.mls_data
                        else None
                    ),
                }
                for cp in result.comparable_properties
            ],
            "average_price": result.average_price,
            "average_price_per_sqft": result.average_price_per_sqft,
            "estimated_value": result.estimated_value,
            "confidence_score": result.confidence_score,
            "subject_property_full": subject_full,
            "comparable_properties_full": comps_full,
        }

        if debug_enabled:
            # High-signal fields that users typically expect to be present
            key_fields = [
                "bedrooms",
                "bathrooms",
                "square_feet",
                "year_built",
                "lot_size_sqft",
                "parking_spaces",
                "heating_type",
                "cooling_type",
                "roof_material",
                "school_district",
                "list_price",
                "sold_price",
                "sold_date",
            ]
            output["debug"] = {
                "subject_missing_fields": _missing_fields(
                    result.subject_property, key_fields
                ),
                "subject_data_source": (
                    (result.subject_property.mls_data or {}).get("data_source")
                    or (result.subject_property.mls_data or {}).get("source")
                ),
                "connector_last_status_code": getattr(
                    getattr(bot_instance, "connector", None), "last_status_code", None
                ),
                "connector_last_endpoint": getattr(
                    getattr(bot_instance, "connector", None), "last_endpoint", None
                ),
            }

        # Send email report if email provided
        email_sent = False
        email_error = None
        if email:
            if not settings.email_enabled:
                email_error = "Email is not enabled. Please configure email settings in .env file."
            elif not settings.email_smtp_username or not settings.email_smtp_password:
                email_error = "Email SMTP credentials not configured. Please add EMAIL_SMTP_USERNAME and EMAIL_SMTP_PASSWORD to .env file."
            else:
                try:
                    report_gen = ReportGenerator()
                    email_sent = report_gen.send_email_report(
                        result, email, format="pdf"
                    )
                    if not email_sent:
                        email_error = (
                            "Email sending failed. Check server logs for details."
                        )
                    else:
                        logging.info(f"Successfully sent email report to {email}")
                except Exception as e:
                    logging.error(f"Error sending email: {e}", exc_info=True)
                    email_error = f"Error sending email: {str(e)}"

        # Add email status to response
        if email:
            output["email_sent"] = email_sent
            if email_error:
                output["email_error"] = email_error

        return jsonify(output)

    except Exception as e:
        logging.error(f"Error in search: {e}", exc_info=True)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Using port 5050 since 5000 is often taken by macOS ControlCenter
    app.run(debug=True, host="0.0.0.0", port=5050)
