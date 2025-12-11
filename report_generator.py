"""Property valuation report generator with charts, statistics, and professional styling."""

import base64
import io
import logging
import smtplib
import statistics
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import settings
from models import CompProperty, CompResult, Property

logger = logging.getLogger(__name__)

# Matplotlib for charts - optional
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for server use
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not installed. Charts will not be available. Install with: pip install matplotlib")

# ReportLab imports - only needed for PDF generation
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning(
        "ReportLab not installed. PDF generation will not be available. Install with: pip install reportlab"
    )


class ReportGenerator:
    """Generates professional property valuation reports with charts and statistics."""

    # Branding colors
    PRIMARY_COLOR = "#1a365d"  # Deep navy blue
    SECONDARY_COLOR = "#2b6cb0"  # Medium blue
    ACCENT_COLOR = "#48bb78"  # Green for positive values
    WARNING_COLOR = "#ed8936"  # Orange for warnings
    DANGER_COLOR = "#e53e3e"  # Red for negative values
    LIGHT_BG = "#f7fafc"  # Light gray background
    
    def __init__(self):
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)

    def _calculate_statistics(self, comp_result: CompResult) -> Dict:
        """Calculate comprehensive statistics from comparable properties."""
        stats = {
            "count": len(comp_result.comparable_properties),
            "avg_price": comp_result.average_price,
            "avg_psf": comp_result.average_price_per_sqft,
            "estimated_value": comp_result.estimated_value,
            "confidence": comp_result.confidence_score,
        }
        
        # Get all prices for statistical analysis
        prices = []
        adjusted_prices = []
        sqft_values = []
        price_per_sqft_values = []
        similarity_scores = []
        
        for comp in comp_result.comparable_properties:
            prop = comp.property
            if prop.sold_price:
                prices.append(prop.sold_price)
            if comp.adjusted_price:
                adjusted_prices.append(comp.adjusted_price)
            if prop.square_feet:
                sqft_values.append(prop.square_feet)
            if prop.sold_price and prop.square_feet:
                price_per_sqft_values.append(prop.sold_price / prop.square_feet)
            similarity_scores.append(comp.similarity_score)
        
        # Calculate statistics
        if prices:
            stats["min_price"] = min(prices)
            stats["max_price"] = max(prices)
            stats["price_range"] = max(prices) - min(prices)
            if len(prices) > 1:
                stats["std_dev_price"] = statistics.stdev(prices)
                stats["median_price"] = statistics.median(prices)
            else:
                stats["std_dev_price"] = 0
                stats["median_price"] = prices[0]
        
        if adjusted_prices:
            stats["min_adjusted"] = min(adjusted_prices)
            stats["max_adjusted"] = max(adjusted_prices)
            stats["adjusted_range"] = max(adjusted_prices) - min(adjusted_prices)
            if len(adjusted_prices) > 1:
                stats["std_dev_adjusted"] = statistics.stdev(adjusted_prices)
                stats["median_adjusted"] = statistics.median(adjusted_prices)
            else:
                stats["std_dev_adjusted"] = 0
                stats["median_adjusted"] = adjusted_prices[0]
            
            # Value range recommendation (mean ± std dev)
            mean_adj = statistics.mean(adjusted_prices)
            std_adj = stats.get("std_dev_adjusted", 0)
            stats["value_low"] = mean_adj - std_adj
            stats["value_high"] = mean_adj + std_adj
        
        if price_per_sqft_values:
            stats["min_psf"] = min(price_per_sqft_values)
            stats["max_psf"] = max(price_per_sqft_values)
            if len(price_per_sqft_values) > 1:
                stats["std_dev_psf"] = statistics.stdev(price_per_sqft_values)
            else:
                stats["std_dev_psf"] = 0
        
        if similarity_scores:
            stats["avg_similarity"] = statistics.mean(similarity_scores)
            stats["min_similarity"] = min(similarity_scores)
            stats["max_similarity"] = max(similarity_scores)
        
        return stats

    def _generate_price_chart(self, comp_result: CompResult) -> Optional[str]:
        """Generate a price comparison bar chart as base64 encoded image."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            # Collect data
            labels = []
            original_prices = []
            adjusted_prices = []
            
            for i, comp in enumerate(comp_result.comparable_properties[:10], 1):
                prop = comp.property
                if prop.sold_price:
                    labels.append(f"Comp #{i}")
                    original_prices.append(prop.sold_price / 1000)  # Convert to thousands
                    if comp.adjusted_price:
                        adjusted_prices.append(comp.adjusted_price / 1000)
                    else:
                        adjusted_prices.append(prop.sold_price / 1000)
            
            if not labels:
                return None
            
            # Create figure with professional styling
            fig, ax = plt.subplots(figsize=(10, 5))
            
            x = range(len(labels))
            width = 0.35
            
            bars1 = ax.bar([i - width/2 for i in x], original_prices, width, 
                          label='Original Price', color=self.SECONDARY_COLOR, alpha=0.7)
            bars2 = ax.bar([i + width/2 for i in x], adjusted_prices, width,
                          label='Adjusted Price', color=self.ACCENT_COLOR, alpha=0.9)
            
            # Add subject property line if available
            if comp_result.estimated_value:
                ax.axhline(y=comp_result.estimated_value / 1000, color=self.PRIMARY_COLOR, 
                          linestyle='--', linewidth=2, label=f'Estimated Value: ${comp_result.estimated_value:,.0f}')
            
            ax.set_ylabel('Price ($ thousands)', fontsize=12)
            ax.set_title('Comparable Properties: Original vs Adjusted Prices', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.legend(loc='upper right')
            
            # Format y-axis as currency
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f'${x:,.0f}K'))
            
            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                ax.annotate(f'${height:.0f}K',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
        
        except Exception as e:
            logger.warning(f"Failed to generate price chart: {e}")
            return None

    def _generate_similarity_chart(self, comp_result: CompResult) -> Optional[str]:
        """Generate a similarity score radar/bar chart as base64 encoded image."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            labels = []
            scores = []
            colors = []
            
            for i, comp in enumerate(comp_result.comparable_properties[:10], 1):
                labels.append(f"#{i}")
                score = comp.similarity_score * 100
                scores.append(score)
                # Color based on score
                if score >= 80:
                    colors.append(self.ACCENT_COLOR)
                elif score >= 60:
                    colors.append(self.WARNING_COLOR)
                else:
                    colors.append(self.DANGER_COLOR)
            
            if not labels:
                return None
            
            fig, ax = plt.subplots(figsize=(10, 4))
            
            bars = ax.barh(labels, scores, color=colors, alpha=0.8)
            
            # Add score labels
            for bar, score in zip(bars, scores):
                width = bar.get_width()
                ax.annotate(f'{score:.1f}%',
                           xy=(width, bar.get_y() + bar.get_height() / 2),
                           xytext=(5, 0), textcoords="offset points",
                           ha='left', va='center', fontsize=10, fontweight='bold')
            
            ax.set_xlim(0, 100)
            ax.set_xlabel('Similarity Score (%)', fontsize=12)
            ax.set_title('Comparable Similarity Scores', fontsize=14, fontweight='bold')
            
            # Add reference lines
            ax.axvline(x=80, color=self.ACCENT_COLOR, linestyle='--', alpha=0.5, label='Excellent (80%+)')
            ax.axvline(x=60, color=self.WARNING_COLOR, linestyle='--', alpha=0.5, label='Good (60%+)')
            
            plt.tight_layout()
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
        
        except Exception as e:
            logger.warning(f"Failed to generate similarity chart: {e}")
            return None

    def _generate_map_placeholder(self, comp_result: CompResult) -> str:
        """Generate a map visualization placeholder (requires Google Maps API for full implementation)."""
        subject = comp_result.subject_property
        
        # If we have coordinates, we can generate a static map URL
        if subject.latitude and subject.longitude and settings.google_maps_api_key:
            # Build static map URL with markers
            markers = f"color:red|label:S|{subject.latitude},{subject.longitude}"
            
            for i, comp in enumerate(comp_result.comparable_properties[:5], 1):
                prop = comp.property
                if prop.latitude and prop.longitude:
                    markers += f"&markers=color:blue|label:{i}|{prop.latitude},{prop.longitude}"
            
            map_url = (
                f"https://maps.googleapis.com/maps/api/staticmap?"
                f"center={subject.latitude},{subject.longitude}&zoom=13&size=600x400"
                f"&maptype=roadmap&{markers}&key={settings.google_maps_api_key}"
            )
            return f'<img src="{map_url}" alt="Property Map" style="width:100%; max-width:600px; border-radius:8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">'
        
        # Placeholder if no API key
        return '''
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 40px; text-align: center; border-radius: 8px;
                    margin: 20px 0;">
            <h3 style="margin: 0;">📍 Map Visualization</h3>
            <p style="opacity: 0.9; margin-top: 10px;">
                Configure GOOGLE_MAPS_API_KEY in .env to display an interactive property map
            </p>
        </div>
        '''

    def generate_report(self, comp_result: CompResult, format: str = "text") -> str:
        """Generate a property valuation report."""
        if format == "text":
            return self._generate_text_report(comp_result)
        elif format == "html":
            return self._generate_html_report(comp_result)
        elif format == "markdown":
            return self._generate_markdown_report(comp_result)
        elif format == "pdf":
            return self._generate_pdf_report(comp_result)
        else:
            raise ValueError(f"Unknown format: {format}")

    def save_report(self, comp_result: CompResult, format: str = "text") -> str:
        """Save report to file and return filepath."""
        report_content = self.generate_report(comp_result, format)

        # Generate filename
        subject = comp_result.subject_property
        address_safe = (
            subject.address.replace(" ", "_").replace(",", "").replace("/", "-")[:50]
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        extension = {"text": "txt", "html": "html", "markdown": "md", "pdf": "pdf"}.get(
            format, "txt"
        )

        filename = f"valuation_report_{address_safe}_{timestamp}.{extension}"
        filepath = self.reports_dir / filename

        if format == "pdf":
            # PDF is saved directly by the generator
            return str(filepath)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report_content)
            return str(filepath)

    def send_email_report(
        self, comp_result: CompResult, to_email: str, format: str = "pdf"
    ) -> bool:
        """Send property valuation report via email."""
        if not settings.email_enabled:
            logger.warning("Email is not enabled in settings")
            return False

        if not settings.email_smtp_username or not settings.email_smtp_password:
            logger.warning("Email SMTP credentials not configured")
            return False

        try:
            subject_prop = comp_result.subject_property

            # Create email
            msg = MIMEMultipart()
            msg["From"] = (
                f"{settings.email_from_name} <{settings.email_from_address or settings.email_smtp_username}>"
            )
            msg["To"] = to_email
            msg["Subject"] = (
                f"Property Valuation Report - {subject_prop.address}, {subject_prop.city}, {subject_prop.state}"
            )

            # Generate and attach PDF
            if format == "pdf":
                pdf_path = self.save_report(comp_result, format="pdf")
                with open(pdf_path, "rb") as f:
                    pdf_attachment = MIMEBase("application", "pdf")
                    pdf_attachment.set_payload(f.read())
                    encoders.encode_base64(pdf_attachment)
                    pdf_attachment.add_header(
                        "Content-Disposition",
                        f'attachment; filename=valuation_report_{subject_prop.address.replace(" ", "_")[:30]}.pdf',
                    )
                    msg.attach(pdf_attachment)

                # Add text body
                text_body = f"""Property Valuation Report

A detailed property valuation report has been generated for:
{subject_prop.address}
{subject_prop.city}, {subject_prop.state} {subject_prop.zip_code}

The PDF report is attached to this email and includes:
- Comprehensive property analysis
- Detailed comparable property evaluation
- Valuation reasoning and methodology
- Market analysis and trends

Please find the complete report attached.

Best regards,
MLS Comp Bot"""
                text_part = MIMEText(text_body, "plain")
                msg.attach(text_part)
            elif format == "html":
                report_content = self.generate_report(comp_result, format)
                html_part = MIMEText(report_content, "html")
                msg.attach(html_part)
            else:
                report_content = self.generate_report(comp_result, format)
                text_part = MIMEText(report_content, "plain")
                msg.attach(text_part)

            # Send email
            server = smtplib.SMTP(settings.email_smtp_server, settings.email_smtp_port)
            server.starttls()
            server.login(settings.email_smtp_username, settings.email_smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Successfully sent email report to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email report: {e}", exc_info=True)
            return False

    def _generate_text_report(self, comp_result: CompResult) -> str:
        """Generate plain text report."""
        subject = comp_result.subject_property
        lines = []

        lines.append("=" * 80)
        lines.append("PROPERTY VALUATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Subject Property Section
        lines.append("SUBJECT PROPERTY")
        lines.append("-" * 80)
        lines.append(f"Address: {subject.address}")
        lines.append(
            f"City, State ZIP: {subject.city}, {subject.state} {subject.zip_code}"
        )
        lines.append(f"Property Type: {subject.property_type.value}")
        if subject.mls_number:
            lines.append(f"APN/MLS#: {subject.mls_number}")
        lines.append("")

        lines.append("PROPERTY CHARACTERISTICS")
        lines.append("")
        lines.append("Size & Layout:")
        if subject.bedrooms:
            lines.append(f"  Bedrooms: {subject.bedrooms}")
        if subject.bathrooms:
            lines.append(f"  Bathrooms: {subject.bathrooms}")
            if subject.bathrooms_full or subject.bathrooms_half:
                parts = []
                if subject.bathrooms_full:
                    parts.append(f"{subject.bathrooms_full} full")
                if subject.bathrooms_half:
                    parts.append(f"{subject.bathrooms_half} half")
                lines.append(f"    ({', '.join(parts)})")
        if subject.total_rooms:
            lines.append(f"  Total Rooms: {subject.total_rooms}")
        if subject.square_feet:
            lines.append(f"  Square Feet: {subject.square_feet:,}")
        if subject.lot_size_sqft:
            lot_str = f"  Lot Size: {subject.lot_size_sqft:,.0f} sqft"
            if subject.lot_size_acres:
                lot_str += f" ({subject.lot_size_acres:.3f} acres)"
            lines.append(lot_str)
        if subject.stories:
            lines.append(f"  Stories: {subject.stories}")
        lines.append("")

        lines.append("Age & Style:")
        if subject.year_built:
            age = datetime.now().year - subject.year_built
            lines.append(f"  Year Built: {subject.year_built} ({age} years old)")
        if subject.architectural_style:
            lines.append(f"  Architectural Style: {subject.architectural_style}")
        if subject.school_district:
            lines.append(f"  School District: {subject.school_district}")
            lines.append("")

        lines.append("Condition & Features:")
        if subject.condition:
            lines.append(f"  Condition: {subject.condition}")
        if subject.recent_upgrades:
            lines.append(f"  Recent Upgrades: {', '.join(subject.recent_upgrades)}")
        if subject.renovation_year:
            lines.append(f"  Last Renovation: {subject.renovation_year}")
        if subject.major_repairs_needed:
            lines.append(
                f"  Major Repairs Needed: {', '.join(subject.major_repairs_needed)}"
            )
        if subject.heating_type:
            lines.append(f"  Heating: {subject.heating_type}")
        if subject.cooling_type:
            lines.append(f"  Cooling: {subject.cooling_type}")
        if subject.roof_material:
            lines.append(f"  Roof: {subject.roof_material}")
            lines.append("")

        lines.append("Special Features & Amenities:")
        if subject.amenities:
            lines.append(f"  Amenities: {', '.join(subject.amenities)}")
        if subject.exterior_features:
            lines.append(f"  Exterior Features: {', '.join(subject.exterior_features)}")
        if subject.parking_spaces:
            parking_str = f"  Parking: {subject.parking_spaces} spaces"
            if subject.garage_type:
                parking_str += f" ({subject.garage_type})"
            lines.append(parking_str)
        if subject.view_type:
            lines.append(f"  View: {subject.view_type}")
        if subject.waterfront_view:
            lines.append(f"  Waterfront: Yes")
        lines.append("")

        lines.append("Location & Proximity:")
        if subject.school_district:
            lines.append(f"  School District: {subject.school_district}")
        if subject.proximity_to_parks is not None:
            lines.append(
                f"  Near Parks: {'Yes' if subject.proximity_to_parks else 'No'}"
            )
        if subject.proximity_to_shopping is not None:
            lines.append(
                f"  Near Shopping: {'Yes' if subject.proximity_to_shopping else 'No'}"
            )
        if subject.proximity_to_highway is not None:
            lines.append(
                f"  Near Highway: {'Yes' if subject.proximity_to_highway else 'No'}"
            )
        lines.append("")

        lines.append("Pricing:")
        if subject.list_price:
            lines.append(f"  List Price: ${subject.list_price:,.0f}")
        if subject.sold_price:
            lines.append(f"  Sold Price: ${subject.sold_price:,.0f}")
        if subject.price_per_sqft:
            lines.append(f"  Price per SqFt: ${subject.price_per_sqft:,.2f}")
        elif subject.sold_price and subject.square_feet:
            price_per_sqft = subject.sold_price / subject.square_feet
            lines.append(f"  Price per SqFt: ${price_per_sqft:,.2f}")

        # Assessment data
        if subject.mls_data and subject.mls_data.get("assessment"):
            assessment = subject.mls_data["assessment"]
            lines.append("")
            lines.append("Assessment & Tax Info:")
            market_value = assessment.get("market", {}).get("mktTtlValue")
            assessed_value = assessment.get("assessed", {}).get("assdTtlValue")
            tax_year = assessment.get("tax", {}).get("taxYear")
            if market_value:
                lines.append(f"  Market Value: ${float(market_value):,.0f}")
            if assessed_value:
                lines.append(f"  Assessed Value: ${float(assessed_value):,.0f}")
            if tax_year:
                lines.append(f"  Tax Year: {int(tax_year)}")
        lines.append("")

        # Valuation Summary
        lines.append("VALUATION SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Number of Comparables: {len(comp_result.comparable_properties)}")
        lines.append(f"Confidence Score: {comp_result.confidence_score:.2%}")
        lines.append("")

        if comp_result.average_price:
            lines.append(f"Average Comparable Price: ${comp_result.average_price:,.0f}")
        if comp_result.average_price_per_sqft:
            lines.append(
                f"Average Price per Square Foot: ${comp_result.average_price_per_sqft:,.2f}"
            )
        if comp_result.estimated_value:
            lines.append(
                f"Estimated Property Value: ${comp_result.estimated_value:,.0f}"
            )
            if subject.list_price:
                diff = comp_result.estimated_value - subject.list_price
                diff_pct = (diff / subject.list_price) * 100
                lines.append(f"  vs. List Price: ${diff:+,.0f} ({diff_pct:+.1f}%)")
            lines.append("")

        # Comparable Properties
        if comp_result.comparable_properties:
            lines.append("COMPARABLE PROPERTIES")
            lines.append("-" * 80)

            for i, comp in enumerate(comp_result.comparable_properties, 1):
                prop = comp.property
                lines.append("")
                lines.append(f"COMP #{i}: {prop.address}")
                lines.append(f"  {prop.city}, {prop.state} {prop.zip_code}")
                lines.append(f"  Similarity Score: {comp.similarity_score:.2%}")

                if comp.distance_miles:
                    lines.append(f"  Distance: {comp.distance_miles:.2f} miles")
                lines.append("")

                lines.append("  PROPERTY CHARACTERISTICS:")
                lines.append("  Size & Layout:")
                if prop.bedrooms:
                    lines.append(f"    Bedrooms: {prop.bedrooms}")
                if prop.bathrooms:
                    lines.append(f"    Bathrooms: {prop.bathrooms}")
                    if prop.bathrooms_full or prop.bathrooms_half:
                        parts = []
                        if prop.bathrooms_full:
                            parts.append(f"{prop.bathrooms_full} full")
                        if prop.bathrooms_half:
                            parts.append(f"{prop.bathrooms_half} half")
                        lines.append(f"      ({', '.join(parts)})")
                if prop.total_rooms:
                    lines.append(f"    Total Rooms: {prop.total_rooms}")
                if prop.square_feet:
                    lines.append(f"    Square Feet: {prop.square_feet:,}")
                if prop.lot_size_sqft:
                    lot_str = f"    Lot Size: {prop.lot_size_sqft:,.0f} sqft"
                    if prop.lot_size_acres:
                        lot_str += f" ({prop.lot_size_acres:.3f} acres)"
                    lines.append(lot_str)
                if prop.stories:
                    lines.append(f"    Stories: {prop.stories}")
                lines.append("")

                lines.append("  Age & Style:")
                if prop.year_built:
                    age = datetime.now().year - prop.year_built
                    lines.append(f"    Year Built: {prop.year_built} ({age} years old)")
                if prop.architectural_style:
                    lines.append(f"    Architectural Style: {prop.architectural_style}")
                lines.append("")

                lines.append("  Condition & Features:")
                if prop.condition:
                    lines.append(f"    Condition: {prop.condition}")
                if prop.recent_upgrades:
                    lines.append(
                        f"    Recent Upgrades: {', '.join(prop.recent_upgrades)}"
                    )
                if prop.renovation_year:
                    lines.append(f"    Last Renovation: {prop.renovation_year}")
                if prop.major_repairs_needed:
                    lines.append(
                        f"    Major Repairs Needed: {', '.join(prop.major_repairs_needed)}"
                    )
                if prop.heating_type:
                    lines.append(f"    Heating: {prop.heating_type}")
                if prop.cooling_type:
                    lines.append(f"    Cooling: {prop.cooling_type}")
                if prop.roof_material:
                    lines.append(f"    Roof: {prop.roof_material}")
                lines.append("")

                lines.append("  Special Features & Amenities:")
                if prop.amenities:
                    lines.append(f"    Amenities: {', '.join(prop.amenities)}")
                if prop.exterior_features:
                    lines.append(
                        f"    Exterior Features: {', '.join(prop.exterior_features)}"
                    )
                if prop.parking_spaces:
                    parking_str = f"    Parking: {prop.parking_spaces} spaces"
                    if prop.garage_type:
                        parking_str += f" ({prop.garage_type})"
                    lines.append(parking_str)
                if prop.view_type:
                    lines.append(f"    View: {prop.view_type}")
                if prop.waterfront_view:
                    lines.append(f"    Waterfront: Yes")
                lines.append("")

                lines.append("  Location & Proximity:")
                if prop.school_district:
                    lines.append(f"    School District: {prop.school_district}")
                if prop.proximity_to_parks is not None:
                    lines.append(
                        f"    Near Parks: {'Yes' if prop.proximity_to_parks else 'No'}"
                    )
                if prop.proximity_to_shopping is not None:
                    lines.append(
                        f"    Near Shopping: {'Yes' if prop.proximity_to_shopping else 'No'}"
                    )
                if prop.proximity_to_highway is not None:
                    lines.append(
                        f"    Near Highway: {'Yes' if prop.proximity_to_highway else 'No'}"
                    )
                lines.append("")

                lines.append("  SALE & MARKET DATA:")
                if prop.sold_price:
                    lines.append(f"    Sold Price: ${prop.sold_price:,.0f}")
                    if prop.sold_date:
                        sale_date_str = prop.sold_date.strftime("%Y-%m-%d")
                        lines.append(f"    Sold Date: {sale_date_str}")
                        if prop.sale_recency_days is not None:
                            months_ago = prop.sale_recency_days / 30
                            if months_ago < 1:
                                lines.append(
                                    f"    Sale Recency: {prop.sale_recency_days} days ago"
                                )
                            elif months_ago < 12:
                                lines.append(
                                    f"    Sale Recency: {months_ago:.1f} months ago"
                                )
                            else:
                                years_ago = months_ago / 12
                                lines.append(
                                    f"    Sale Recency: {years_ago:.1f} years ago"
                                )
                    if prop.square_feet:
                        price_per_sqft = prop.sold_price / prop.square_feet
                        lines.append(f"    Price per SqFt: ${price_per_sqft:,.2f}")
                elif prop.list_price:
                    lines.append(f"    List Price: ${prop.list_price:,.0f}")
                lines.append("")

                lines.append("  Transaction Details:")
                if prop.seller_concessions:
                    lines.append(
                        f"    Seller Concessions: ${prop.seller_concessions:,.0f}"
                    )
                if prop.seller_concessions_description:
                    lines.append(f"      ({prop.seller_concessions_description})")
                if prop.financing_type:
                    lines.append(f"    Financing Type: {prop.financing_type}")
                if prop.arms_length_transaction is not None:
                    lines.append(
                        f"    Arms-Length Transaction: {'Yes' if prop.arms_length_transaction else 'No'}"
                    )
                lines.append("")

                if comp.price_difference and subject.list_price:
                    lines.append(f"  Price Comparison vs Subject:")
                    lines.append(
                        f"    Price Difference: ${comp.price_difference:+,.0f} ({comp.price_difference_percent:+.1f}%)"
                    )

                if comp.match_reasons:
                    lines.append(f"  Match Reasons: {', '.join(comp.match_reasons)}")

                # Professional Adjustments
                if comp.adjustments:
                    lines.append("")
                    lines.append(
                        f"  Professional Adjustments ({len(comp.adjustments)} adjustments, Total: ${comp.total_adjustment_amount:+,.0f}):"
                    )
                    for adj in comp.adjustments:
                        lines.append(f"    • {adj.category}: {adj.description}")
                        lines.append(
                            f"      Adjustment: ${adj.amount:+,.0f} ({adj.reason})"
                        )

                    if comp.adjusted_price:
                        comp_price = prop.sold_price or prop.list_price
                        lines.append("")
                        lines.append(f"  Original Sale Price: ${comp_price:,.0f}")
                        lines.append(f"  Adjusted Price: ${comp.adjusted_price:,.0f}")
                        lines.append(
                            f"  Net Adjustment: ${comp.total_adjustment_amount:+,.0f}"
                        )

        lines.append("")
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _generate_html_report(self, comp_result: CompResult) -> str:
        """Generate enhanced HTML report with charts, statistics, and professional styling."""
        subject = comp_result.subject_property
        stats = self._calculate_statistics(comp_result)
        
        # Generate charts
        price_chart = self._generate_price_chart(comp_result)
        similarity_chart = self._generate_similarity_chart(comp_result)
        map_html = self._generate_map_placeholder(comp_result)

        # Get broker branding
        broker_logo_path = Path(settings.broker_logo_path)
        broker_logo_base64 = ""
        if broker_logo_path.exists():
            with open(broker_logo_path, "rb") as f:
                broker_logo_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Property Valuation Report - {subject.address} | {settings.broker_company}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: {self.PRIMARY_COLOR};
            --secondary: {self.SECONDARY_COLOR};
            --accent: {self.ACCENT_COLOR};
            --warning: {self.WARNING_COLOR};
            --danger: {self.DANGER_COLOR};
            --light-bg: {self.LIGHT_BG};
            --text: #2d3748;
            --text-light: #718096;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{ 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7;
            color: var(--text);
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        
        .report-card {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-bottom: 30px;
        }}
        
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 30px 40px;
        }}
        
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .broker-brand {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        
        .broker-logo {{
            max-height: 70px;
            background: white;
            padding: 8px 15px;
            border-radius: 8px;
        }}
        
        .broker-info {{
            text-align: left;
        }}
        
        .broker-info .broker-name {{
            font-size: 1.3rem;
            font-weight: 700;
            margin: 0;
        }}
        
        .broker-info .broker-title {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin: 2px 0;
        }}
        
        .broker-info .broker-contact {{
            font-size: 0.85rem;
            opacity: 0.85;
            margin-top: 5px;
        }}
        
        .report-title {{
            text-align: right;
        }}
        
        .report-title h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 5px;
            letter-spacing: -0.5px;
        }}
        
        .report-title .subtitle {{
            font-size: 1rem;
            opacity: 0.9;
        }}
        
        .report-title .date {{
            margin-top: 8px;
            font-size: 0.85rem;
            opacity: 0.8;
        }}
        
        .section {{
            padding: 30px 40px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .section:last-child {{ border-bottom: none; }}
        
        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .section-title::before {{
            content: '';
            width: 4px;
            height: 28px;
            background: var(--accent);
            border-radius: 2px;
        }}
        
        /* Executive Summary Cards */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .summary-card {{
            background: var(--light-bg);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .summary-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .summary-card .label {{
            font-size: 0.85rem;
            color: var(--text-light);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        
        .summary-card .value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--primary);
        }}
        
        .summary-card.highlight {{
            background: linear-gradient(135deg, var(--accent) 0%, #38a169 100%);
            color: white;
        }}
        
        .summary-card.highlight .label,
        .summary-card.highlight .value {{
            color: white;
        }}
        
        /* Stats Box */
        .stats-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            margin: 20px 0;
        }}
        
        .stats-box h4 {{
            margin-bottom: 15px;
            font-size: 1.1rem;
        }}
        
        .stats-row {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-item .stat-label {{
            font-size: 0.8rem;
            opacity: 0.9;
        }}
        
        .stat-item .stat-value {{
            font-size: 1.3rem;
            font-weight: 600;
        }}
        
        /* Property Details Table */
        .details-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 20px 0;
        }}
        
        .details-table th,
        .details-table td {{
            padding: 14px 18px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .details-table th {{
            background: var(--primary);
            color: white;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .details-table th:first-child {{ border-radius: 8px 0 0 0; }}
        .details-table th:last-child {{ border-radius: 0 8px 0 0; }}
        
        .details-table tr:hover td {{
            background: var(--light-bg);
        }}
        
        .details-table td:first-child {{
            font-weight: 500;
            color: var(--primary);
            width: 35%;
        }}
        
        /* Comparable Cards */
        .comp-card {{
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            margin: 20px 0;
            overflow: hidden;
            transition: box-shadow 0.2s;
        }}
        
        .comp-card:hover {{
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }}
        
        .comp-header {{
            background: linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%);
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .comp-header h3 {{
            font-size: 1.2rem;
            font-weight: 600;
        }}
        
        .comp-score {{
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
        }}
        
        .comp-body {{
            padding: 25px;
        }}
        
        .comp-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .comp-stat {{
            text-align: center;
            padding: 15px;
            background: var(--light-bg);
            border-radius: 8px;
        }}
        
        .comp-stat .label {{
            font-size: 0.8rem;
            color: var(--text-light);
        }}
        
        .comp-stat .value {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary);
        }}
        
        /* Adjustments Table */
        .adjustments-table {{
            width: 100%;
            margin: 15px 0;
            border-collapse: collapse;
        }}
        
        .adjustments-table th {{
            background: #edf2f7;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
        }}
        
        .adjustments-table td {{
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .adjustment-positive {{ color: var(--accent); font-weight: 600; }}
        .adjustment-negative {{ color: var(--danger); font-weight: 600; }}
        
        /* Charts Section */
        .chart-container {{
            background: var(--light-bg);
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            text-align: center;
        }}
        
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        
        /* Footer */
        .footer {{
            padding: 30px 40px;
            background: var(--primary);
            color: white;
        }}
        
        .footer-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}
        
        .footer-brand {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .footer-logo {{
            max-height: 50px;
            background: white;
            padding: 5px 10px;
            border-radius: 6px;
        }}
        
        .footer-info {{
            font-size: 0.85rem;
        }}
        
        .footer-info p {{
            margin: 3px 0;
            opacity: 0.9;
        }}
        
        .footer-contact {{
            text-align: right;
            font-size: 0.85rem;
        }}
        
        .footer-contact p {{
            margin: 3px 0;
            opacity: 0.9;
        }}
        
        .footer-contact a {{
            color: white;
            text-decoration: none;
        }}
        
        .footer-contact a:hover {{
            text-decoration: underline;
        }}
        
        .footer-disclaimer {{
            width: 100%;
            text-align: center;
            font-size: 0.75rem;
            opacity: 0.7;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.2);
        }}
        
        /* Data Sources */
        .data-sources {{
            background: #fffbeb;
            border: 1px solid #fcd34d;
            border-radius: 8px;
            padding: 15px 20px;
            margin: 20px 0;
            font-size: 0.9rem;
        }}
        
        .data-sources h4 {{
            color: #b45309;
            margin-bottom: 10px;
        }}
        
        /* Print Styles */
        @media print {{
            body {{ background: white; }}
            .report-card {{ box-shadow: none; }}
            .section {{ page-break-inside: avoid; }}
            .comp-card {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-card">
            <div class="header">
                <div class="header-content">
                    <div class="broker-brand">
                        {"<img src='data:image/png;base64," + broker_logo_base64 + "' alt='" + settings.broker_company + "' class='broker-logo'>" if broker_logo_base64 else ""}
                        <div class="broker-info">
                            <p class="broker-name">{settings.broker_name}</p>
                            <p class="broker-title">{settings.broker_title} | {settings.broker_company}</p>
                            <p class="broker-contact">{settings.broker_phone} | {settings.broker_email}</p>
                        </div>
                    </div>
                    <div class="report-title">
                        <h1>📊 Property Valuation Report</h1>
                        <p class="subtitle">{subject.address}, {subject.city}, {subject.state} {subject.zip_code}</p>
                        <p class="date">Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    </div>
                </div>
            </div>
            
            <!-- Executive Summary -->
            <div class="section">
                <h2 class="section-title">Executive Summary</h2>
                <div class="summary-grid">
                    <div class="summary-card highlight">
                        <div class="label">Estimated Value</div>
                        <div class="value">${comp_result.estimated_value:,.0f}</div>
                    </div>
                    <div class="summary-card">
                        <div class="label">Avg Comp Price</div>
                        <div class="value">${stats.get('avg_price', 0):,.0f}</div>
                    </div>
                    <div class="summary-card">
                        <div class="label">Price per Sq Ft</div>
                        <div class="value">${stats.get('avg_psf', 0):,.2f}</div>
                    </div>
                    <div class="summary-card">
                        <div class="label">Confidence</div>
                        <div class="value">{comp_result.confidence_score:.0%}</div>
                    </div>
                    <div class="summary-card">
                        <div class="label">Comparables</div>
                        <div class="value">{stats.get('count', 0)}</div>
                    </div>
                </div>
                
                <!-- Statistical Analysis -->
                <div class="stats-box">
                    <h4>📈 Statistical Analysis</h4>
                    <div class="stats-row">
                        <div class="stat-item">
                            <div class="stat-label">Value Range (Low)</div>
                            <div class="stat-value">${stats.get('value_low', 0):,.0f}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Value Range (High)</div>
                            <div class="stat-value">${stats.get('value_high', 0):,.0f}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Std Deviation</div>
                            <div class="stat-value">${stats.get('std_dev_adjusted', 0):,.0f}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Median Price</div>
                            <div class="stat-value">${stats.get('median_adjusted', stats.get('median_price', 0)):,.0f}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Subject Property -->
            <div class="section">
                <h2 class="section-title">Subject Property Analysis</h2>
                <table class="details-table">
                    <tr><th>Field</th><th>Details</th></tr>
                    <tr><td>Address</td><td>{subject.address}, {subject.city}, {subject.state} {subject.zip_code}</td></tr>
                    <tr><td>Property Type</td><td>{subject.property_type.value}</td></tr>
"""

        if subject.bedrooms:
            html += f"        <p><strong>Bedrooms:</strong> {subject.bedrooms}</p>\n"
        if subject.bathrooms:
            html += f"        <p><strong>Bathrooms:</strong> {subject.bathrooms}</p>\n"
        if subject.square_feet:
            html += f"        <p><strong>Square Feet:</strong> {subject.square_feet:,}</p>\n"
        if subject.list_price:
            html += f"        <p><strong>List Price:</strong> ${subject.list_price:,.0f}</p>\n"

        html += """    </div>

    <h2>Valuation Summary</h2>
    <div class="valuation">
"""

        if comp_result.estimated_value:
            html += f"        <p><strong>Estimated Value:</strong> <span style='font-size: 1.5em; color: #27ae60;'>${comp_result.estimated_value:,.0f}</span></p>\n"
        if comp_result.average_price:
            html += f"        <p><strong>Average Comparable Price:</strong> ${comp_result.average_price:,.0f}</p>\n"
        if comp_result.average_price_per_sqft:
            html += f"        <p><strong>Average Price per SqFt:</strong> ${comp_result.average_price_per_sqft:,.2f}</p>\n"

        html += f"""        <p><strong>Confidence Score:</strong> <span class="score">{comp_result.confidence_score:.2%}</span></p>
        <p><strong>Number of Comparables:</strong> {len(comp_result.comparable_properties)}</p>
    </div>

    <h2>Comparable Properties</h2>
"""

        for i, comp in enumerate(comp_result.comparable_properties, 1):
            prop = comp.property
            html += f"""    <div class="comp">
        <h3>Comparable #{i}: {prop.address}</h3>
        <p><strong>Similarity Score:</strong> <span class="score">{comp.similarity_score:.2%}</span></p>
"""
            if comp.distance_miles:
                html += f"        <p><strong>Distance:</strong> {comp.distance_miles:.2f} miles</p>\n"

            if prop.sold_price:
                html += f"        <p><strong>Sold Price:</strong> ${prop.sold_price:,.0f}</p>\n"
                if prop.sold_date:
                    html += f"        <p><strong>Sold Date:</strong> {prop.sold_date.strftime('%Y-%m-%d')}</p>\n"
                if prop.sale_recency_days is not None:
                    months = (
                        prop.sale_recency_days / 30
                        if prop.sale_recency_days >= 30
                        else None
                    )
                    recency_str = (
                        f"{prop.sale_recency_days} days ago"
                        if prop.sale_recency_days < 30
                        else f"{months:.1f} months ago"
                    )
                    html += (
                        f"        <p><strong>Sale Recency:</strong> {recency_str}</p>\n"
                    )
            elif prop.list_price:
                html += f"        <p><strong>List Price:</strong> ${prop.list_price:,.0f}</p>\n"

            # Core property details
            if prop.bedrooms is not None or prop.bathrooms is not None:
                bb = []
                if prop.bedrooms is not None:
                    bb.append(f"{prop.bedrooms} bd")
                if prop.bathrooms is not None:
                    bb.append(f"{prop.bathrooms} ba")
                html += (
                    f"        <p><strong>Beds/Baths:</strong> {' / '.join(bb)}</p>\n"
                )
            if prop.square_feet:
                html += f"        <p><strong>Square Feet:</strong> {prop.square_feet:,}</p>\n"
            if prop.lot_size_sqft:
                lot_line = f"{prop.lot_size_sqft:,.0f} sqft"
                if prop.lot_size_acres:
                    lot_line += f" ({prop.lot_size_acres:.2f} acres)"
                html += f"        <p><strong>Lot Size:</strong> {lot_line}</p>\n"
            if prop.year_built:
                html += (
                    f"        <p><strong>Year Built:</strong> {prop.year_built}</p>\n"
                )
            if prop.stories:
                html += f"        <p><strong>Stories:</strong> {prop.stories}</p>\n"
            if prop.parking_spaces is not None:
                parking_line = f"{prop.parking_spaces} spaces"
                if prop.garage_type:
                    parking_line += f" ({prop.garage_type})"
                html += f"        <p><strong>Parking:</strong> {parking_line}</p>\n"
            if prop.heating_type:
                html += (
                    f"        <p><strong>Heating:</strong> {prop.heating_type}</p>\n"
                )
            if prop.cooling_type:
                html += (
                    f"        <p><strong>Cooling:</strong> {prop.cooling_type}</p>\n"
                )
            if prop.roof_material:
                html += f"        <p><strong>Roof:</strong> {prop.roof_material}</p>\n"
            if prop.price_per_sqft:
                html += f"        <p><strong>Price per SqFt:</strong> ${prop.price_per_sqft:,.2f}</p>\n"
            if prop.mls_data:
                dom = prop.mls_data.get("days_on_market")
                if dom:
                    html += f"        <p><strong>Days on Market (source):</strong> {dom}</p>\n"
                data_source = prop.mls_data.get("source") or prop.mls_data.get(
                    "data_source"
                )
                if data_source:
                    html += (
                        f"        <p><strong>Data Source:</strong> {data_source}</p>\n"
                    )
                desc = prop.mls_data.get("property_description")
                if desc:
                    preview = desc if len(desc) < 400 else desc[:400] + "..."
                    html += f"        <p><strong>Description (source):</strong> {preview}</p>\n"
            if prop.financing_type:
                html += f"        <p><strong>Financing:</strong> {prop.financing_type}</p>\n"
            if prop.arms_length_transaction is not None:
                html += f"        <p><strong>Arms-Length:</strong> {'Yes' if prop.arms_length_transaction else 'No'}</p>\n"
            if prop.seller_concessions:
                concessions_desc = (
                    f"{prop.seller_concessions_description}"
                    if prop.seller_concessions_description
                    else ""
                )
                html += f"        <p><strong>Seller Concessions:</strong> ${prop.seller_concessions:,.0f} {concessions_desc}</p>\n"
            if prop.amenities:
                html += f"        <p><strong>Amenities:</strong> {', '.join(prop.amenities)}</p>\n"
            if prop.exterior_features:
                html += f"        <p><strong>Exterior Features:</strong> {', '.join(prop.exterior_features)}</p>\n"
            if comp.match_reasons:
                html += f"        <p><strong>Match Reasons:</strong> {', '.join(comp.match_reasons)}</p>\n"

            # Professional Adjustments
            if comp.adjustments:
                html += f"""        <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db;">
            <h4>Professional Adjustments ({len(comp.adjustments)} adjustments, Total: ${comp.total_adjustment_amount:+,.0f})</h4>
            <ul>
"""
                for adj in comp.adjustments:
                    html += f"""                <li><strong>{adj.category}:</strong> {adj.description}<br/>
                    <span style="color: {'#27ae60' if adj.amount > 0 else '#e74c3c'};">
                        Adjustment: ${adj.amount:+,.0f}
                    </span> - {adj.reason}</li>
"""
                html += "            </ul>\n"
                if comp.adjusted_price:
                    html += f"""            <p><strong>Original Sale Price:</strong> ${prop.sold_price or prop.list_price:,.0f}</p>
            <p><strong>Adjusted Price:</strong> <span style="font-size: 1.2em; color: #27ae60;">${comp.adjusted_price:,.0f}</span></p>
            <p><strong>Net Adjustment:</strong> ${comp.total_adjustment_amount:+,.0f}</p>
        </div>
"""

            html += "    </div>\n"

        # Add footer with broker branding
        html += f"""
            </div><!-- end section -->
            
            <!-- Footer -->
            <div class="footer">
                <div class="footer-content">
                    <div class="footer-brand">
                        {"<img src='data:image/png;base64," + broker_logo_base64 + "' alt='" + settings.broker_company + "' class='footer-logo'>" if broker_logo_base64 else ""}
                        <div class="footer-info">
                            <p><strong>{settings.broker_name}</strong></p>
                            <p>{settings.broker_title} | {settings.broker_company}</p>
                            <p>{settings.broker_tagline}</p>
                        </div>
                    </div>
                    <div class="footer-contact">
                        <p>📞 {settings.broker_phone}</p>
                        <p>✉️ <a href="mailto:{settings.broker_email}">{settings.broker_email}</a></p>
                        <p>🌐 <a href="https://{settings.broker_website}" target="_blank">{settings.broker_website}</a></p>
                    </div>
                </div>
                <div class="footer-disclaimer">
                    This report is generated using automated analysis. For official appraisals, consult a licensed appraiser.
                    <br/>© {datetime.now().year} {settings.broker_company}. All rights reserved.
                </div>
            </div>
        </div><!-- end report-card -->
    </div><!-- end container -->
</body>
</html>"""

        return html

    def _generate_markdown_report(self, comp_result: CompResult) -> str:
        """Generate Markdown report."""
        subject = comp_result.subject_property
        lines = []

        lines.append("# Property Valuation Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("## Subject Property")
        lines.append("")
        lines.append(f"- **Address:** {subject.address}")
        lines.append(
            f"- **Location:** {subject.city}, {subject.state} {subject.zip_code}"
        )
        lines.append(f"- **Property Type:** {subject.property_type.value}")
        if subject.bedrooms:
            lines.append(f"- **Bedrooms:** {subject.bedrooms}")
        if subject.bathrooms:
            lines.append(f"- **Bathrooms:** {subject.bathrooms}")
        if subject.total_rooms:
            lines.append(f"- **Total Rooms:** {subject.total_rooms}")
        if subject.square_feet:
            lines.append(f"- **Square Feet:** {subject.square_feet:,}")
        if subject.lot_size_sqft:
            lot_line = f"{subject.lot_size_sqft:,.0f} sqft"
            if subject.lot_size_acres:
                lot_line += f" ({subject.lot_size_acres:.2f} acres)"
            lines.append(f"- **Lot Size:** {lot_line}")
        if subject.year_built:
            lines.append(f"- **Year Built:** {subject.year_built}")
        if subject.stories:
            lines.append(f"- **Stories:** {subject.stories}")
        if subject.parking_spaces is not None:
            parking_line = f"{subject.parking_spaces} spaces"
            if subject.garage_type:
                parking_line += f" ({subject.garage_type})"
            lines.append(f"- **Parking:** {parking_line}")
        if subject.heating_type:
            lines.append(f"- **Heating:** {subject.heating_type}")
        if subject.cooling_type:
            lines.append(f"- **Cooling:** {subject.cooling_type}")
        if subject.roof_material:
            lines.append(f"- **Roof:** {subject.roof_material}")
        if subject.school_district:
            lines.append(f"- **School District:** {subject.school_district}")
        if subject.list_price:
            lines.append(f"- **List Price:** ${subject.list_price:,.0f}")
        if subject.sold_price:
            lines.append(f"- **Sold Price:** ${subject.sold_price:,.0f}")
        if subject.price_per_sqft:
            lines.append(f"- **Price per SqFt:** ${subject.price_per_sqft:,.2f}")
        if subject.sold_date:
            lines.append(f"- **Sold Date:** {subject.sold_date.strftime('%Y-%m-%d')}")
        if subject.sale_recency_days is not None:
            recency = (
                f"{subject.sale_recency_days} days ago"
                if subject.sale_recency_days < 30
                else f"{subject.sale_recency_days/30:.1f} months ago"
            )
            lines.append(f"- **Sale Recency:** {recency}")
        if subject.amenities:
            lines.append(f"- **Amenities:** {', '.join(subject.amenities)}")
        if subject.exterior_features:
            lines.append(
                f"- **Exterior Features:** {', '.join(subject.exterior_features)}"
            )
        # Include source metadata if available
        if subject.mls_data:
            dom = subject.mls_data.get("days_on_market")
            if dom:
                lines.append(f"- **Days on Market (source):** {dom}")
            desc = subject.mls_data.get("property_description")
            if desc:
                preview = desc if len(desc) < 300 else desc[:300] + "..."
                lines.append(f"- **Description (source):** {preview}")

            # Assessment data
            assessment_data = subject.mls_data.get("assessment")
            if assessment_data:
                assessment_info = []
                market_value = assessment_data.get("market", {}).get("mktTtlValue")
                assessed_value = assessment_data.get("assessed", {}).get("assdTtlValue")
                tax_year = assessment_data.get("tax", {}).get("taxYear")
                if market_value:
                    assessment_info.append(f"Market: ${float(market_value):,.0f}")
                if assessed_value:
                    assessment_info.append(f"Assessed: ${float(assessed_value):,.0f}")
                if tax_year:
                    assessment_info.append(f"Tax Year: {int(tax_year)}")
                if assessment_info:
                    lines.append(f"- **Assessment:** {' • '.join(assessment_info)}")

        lines.append("")
        lines.append("## Valuation Summary")
        lines.append("")

        if comp_result.estimated_value:
            lines.append(f"### Estimated Value: ${comp_result.estimated_value:,.0f}")
        if comp_result.average_price:
            lines.append(
                f"- **Average Comparable Price:** ${comp_result.average_price:,.0f}"
            )
        if comp_result.average_price_per_sqft:
            lines.append(
                f"- **Average Price per SqFt:** ${comp_result.average_price_per_sqft:,.2f}"
            )

        lines.append(f"- **Confidence Score:** {comp_result.confidence_score:.2%}")
        lines.append(
            f"- **Number of Comparables:** {len(comp_result.comparable_properties)}"
        )
        lines.append("")

        if comp_result.comparable_properties:
            lines.append("## Comparable Properties")
            lines.append("")

            for i, comp in enumerate(comp_result.comparable_properties, 1):
                prop = comp.property
                lines.append(f"### Comparable #{i}: {prop.address}")
                lines.append("")
                lines.append(f"**Similarity Score:** {comp.similarity_score:.2%}")

                if comp.distance_miles:
                    lines.append(f"**Distance:** {comp.distance_miles:.2f} miles")

                if prop.sold_price:
                    lines.append(f"**Sold Price:** ${prop.sold_price:,.0f}")
                    if prop.sold_date:
                        lines.append(
                            f"**Sold Date:** {prop.sold_date.strftime('%Y-%m-%d')}"
                        )
                    if prop.sale_recency_days is not None:
                        recency = prop.sale_recency_days
                        recency_str = (
                            f"{recency} days ago"
                            if recency < 30
                            else f"{recency / 30:.1f} months ago"
                        )
                        lines.append(f"**Sale Recency:** {recency_str}")
                elif prop.list_price:
                    lines.append(f"**List Price:** ${prop.list_price:,.0f}")

                # Core property details
                if prop.bedrooms or prop.bathrooms:
                    bb = []
                    if prop.bedrooms is not None:
                        bb.append(f"{prop.bedrooms} bd")
                    if prop.bathrooms is not None:
                        bb.append(f"{prop.bathrooms} ba")
                    lines.append(f"**Beds/Baths:** {' / '.join(bb)}")
                if prop.square_feet:
                    lines.append(f"**Square Feet:** {prop.square_feet:,}")
                if prop.lot_size_sqft:
                    lot_line = f"{prop.lot_size_sqft:,.0f} sqft"
                    if prop.lot_size_acres:
                        lot_line += f" ({prop.lot_size_acres:.2f} acres)"
                    lines.append(f"**Lot Size:** {lot_line}")
                if prop.year_built:
                    lines.append(f"**Year Built:** {prop.year_built}")
                if prop.stories:
                    lines.append(f"**Stories:** {prop.stories}")
                if prop.parking_spaces is not None:
                    parking_line = f"{prop.parking_spaces} spaces"
                    if prop.garage_type:
                        parking_line += f" ({prop.garage_type})"
                    lines.append(f"**Parking:** {parking_line}")
                if prop.heating_type:
                    lines.append(f"**Heating:** {prop.heating_type}")
                if prop.cooling_type:
                    lines.append(f"**Cooling:** {prop.cooling_type}")
                if prop.roof_material:
                    lines.append(f"**Roof:** {prop.roof_material}")
                if prop.price_per_sqft:
                    lines.append(f"**Price per SqFt:** ${prop.price_per_sqft:,.2f}")
                if prop.mls_data:
                    dom = prop.mls_data.get("days_on_market")
                    if dom:
                        lines.append(f"**Days on Market (source):** {dom}")
                    data_source = prop.mls_data.get("source") or prop.mls_data.get(
                        "data_source"
                    )
                    if data_source:
                        lines.append(f"**Data Source:** {data_source}")
                    desc = prop.mls_data.get("property_description")
                    if desc:
                        preview = desc if len(desc) < 300 else desc[:300] + "..."
                        lines.append(f"**Description (source):** {preview}")
                    assessment_data = prop.mls_data.get("assessment")
                    if assessment_data:
                        assessment_info = []
                        market_value = assessment_data.get("market", {}).get(
                            "mktTtlValue"
                        )
                        assessed_value = assessment_data.get("assessed", {}).get(
                            "assdTtlValue"
                        )
                        if market_value:
                            assessment_info.append(
                                f"Market: ${float(market_value):,.0f}"
                            )
                        if assessed_value:
                            assessment_info.append(
                                f"Assessed: ${float(assessed_value):,.0f}"
                            )
                        if assessment_info:
                            lines.append(
                                f"**Assessment:** {' • '.join(assessment_info)}"
                            )
                if prop.financing_type:
                    lines.append(f"**Financing:** {prop.financing_type}")
                if prop.arms_length_transaction is not None:
                    lines.append(
                        f"**Arms-Length:** {'Yes' if prop.arms_length_transaction else 'No'}"
                    )
                if prop.seller_concessions:
                    concessions_desc = (
                        f" ({prop.seller_concessions_description})"
                        if prop.seller_concessions_description
                        else ""
                    )
                    lines.append(
                        f"**Seller Concessions:** ${prop.seller_concessions:,.0f}{concessions_desc}"
                    )
                if prop.amenities:
                    lines.append(f"**Amenities:** {', '.join(prop.amenities)}")
                if prop.exterior_features:
                    lines.append(
                        f"**Exterior Features:** {', '.join(prop.exterior_features)}"
                    )
                if comp.match_reasons:
                    lines.append(f"**Match Reasons:** {', '.join(comp.match_reasons)}")

                # Professional Adjustments
                if comp.adjustments:
                    lines.append("")
                    lines.append(
                        f"**Professional Adjustments** ({len(comp.adjustments)} adjustments, Total: ${comp.total_adjustment_amount:+,.0f}):"
                    )
                    for adj in comp.adjustments:
                        lines.append(f"- **{adj.category}:** {adj.description}")
                        lines.append(
                            f"  - Adjustment: ${adj.amount:+,.0f} ({adj.reason})"
                        )

                    if comp.adjusted_price:
                        lines.append("")
                        lines.append(
                            f"**Original Sale Price:** ${prop.sold_price or prop.list_price:,.0f}"
                        )
                        lines.append(f"**Adjusted Price:** ${comp.adjusted_price:,.0f}")
                        lines.append(
                            f"**Net Adjustment:** ${comp.total_adjustment_amount:+,.0f}"
                        )

                lines.append("")

        return "\n".join(lines)

    def _generate_pdf_report(self, comp_result: CompResult) -> str:
        """Generate professional PDF report with detailed reasoning."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "ReportLab is not installed. Please install it with: pip install reportlab"
            )

        from comp_analyzer import CompAnalyzer

        subject = comp_result.subject_property
        analyzer = CompAnalyzer()

        # Generate filename
        address_safe = (
            subject.address.replace(" ", "_").replace(",", "").replace("/", "-")[:50]
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"valuation_report_{address_safe}_{timestamp}.pdf"
        filepath = self.reports_dir / filename

        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Container for PDF content
        story = []

        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a237e"),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#283593"),
            spaceAfter=12,
            spaceBefore=12,
            fontName="Helvetica-Bold",
        )

        subheading_style = ParagraphStyle(
            "CustomSubHeading",
            parent=styles["Heading3"],
            fontSize=14,
            textColor=colors.HexColor("#3949ab"),
            spaceAfter=8,
            spaceBefore=8,
            fontName="Helvetica-Bold",
        )

        body_style = ParagraphStyle(
            "BodyText",
            parent=styles["Normal"],
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY,
        )

        # Broker branding header
        broker_header_style = ParagraphStyle(
            "BrokerHeader",
            parent=styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#1a365d"),
            alignment=TA_CENTER,
            spaceAfter=5,
        )
        
        story.append(Paragraph(f"<b>{settings.broker_name}</b>", broker_header_style))
        story.append(Paragraph(f"{settings.broker_title} | {settings.broker_company}", 
            ParagraphStyle("BrokerSub", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER, textColor=colors.grey)))
        story.append(Paragraph(f"{settings.broker_phone} | {settings.broker_email}", 
            ParagraphStyle("BrokerContact", parent=styles["Normal"], fontSize=9, alignment=TA_CENTER, textColor=colors.grey)))
        story.append(Paragraph(f"{settings.broker_website}", 
            ParagraphStyle("BrokerWeb", parent=styles["Normal"], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#2b6cb0"))))
        story.append(Spacer(1, 0.3 * inch))
        
        # Title
        story.append(Paragraph("PROPERTY VALUATION REPORT", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Report metadata
        story.append(
            Paragraph(
                f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.3 * inch))

        # Executive Summary
        story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        summary_text = f"""
        This comprehensive property valuation report provides a detailed analysis of the subject property located at
        <b>{subject.address}, {subject.city}, {subject.state} {subject.zip_code}</b>. The valuation is based on
        {len(comp_result.comparable_properties)} comparable properties that have recently sold in the area.
        The analysis employs a weighted scoring methodology that evaluates properties based on location proximity,
        physical characteristics, sale price, and market timing.
        """
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 0.2 * inch))

        # Valuation Summary Box
        valuation_data = []
        if comp_result.estimated_value:
            valuation_data.append(
                ["Estimated Property Value", f"${comp_result.estimated_value:,.0f}"]
            )
        if comp_result.average_price:
            valuation_data.append(
                ["Average Comparable Price", f"${comp_result.average_price:,.0f}"]
            )
        if comp_result.average_price_per_sqft:
            valuation_data.append(
                [
                    "Average Price per Square Foot",
                    f"${comp_result.average_price_per_sqft:,.2f}",
                ]
            )
        valuation_data.append(
            ["Confidence Score", f"{comp_result.confidence_score:.1%}"]
        )
        valuation_data.append(
            ["Number of Comparables", str(len(comp_result.comparable_properties))]
        )

        valuation_table = Table(valuation_data, colWidths=[4 * inch, 2 * inch])
        valuation_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#283593")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#e8eaf6")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#9fa8da")),
                    ("FONTSIZE", (0, 1), (-1, -1), 11),
                ]
            )
        )
        story.append(valuation_table)
        story.append(Spacer(1, 0.3 * inch))

        # Subject Property Details
        story.append(Paragraph("SUBJECT PROPERTY ANALYSIS", heading_style))

        # Property Information Table
        prop_data = [
            [
                "Address",
                f"{subject.address}, {subject.city}, {subject.state} {subject.zip_code}",
            ],
            ["Property Type", subject.property_type.value],
        ]
        if subject.mls_number:
            prop_data.append(["APN/MLS Number", subject.mls_number])
        if subject.bedrooms:
            prop_data.append(["Bedrooms", str(subject.bedrooms)])
        if subject.bathrooms:
            prop_data.append(["Bathrooms", str(subject.bathrooms)])
        if subject.square_feet:
            prop_data.append(["Square Feet", f"{subject.square_feet:,}"])
        if subject.lot_size_sqft:
            lot_str = f"{subject.lot_size_sqft:,.0f} sqft"
            if subject.lot_size_acres:
                lot_str += f" ({subject.lot_size_acres:.3f} acres)"
            prop_data.append(["Lot Size", lot_str])
        if subject.year_built:
            age = datetime.now().year - subject.year_built
            prop_data.append(["Year Built", f"{subject.year_built} ({age} years old)"])
        if subject.stories:
            prop_data.append(["Stories", str(subject.stories)])
        if subject.list_price:
            prop_data.append(["List Price", f"${subject.list_price:,.0f}"])
        if subject.sold_price:
            prop_data.append(["Sold Price", f"${subject.sold_price:,.0f}"])

        prop_table = Table(prop_data, colWidths=[2.5 * inch, 3.5 * inch])
        prop_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f5f5")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#424242")),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(prop_table)
        story.append(Spacer(1, 0.3 * inch))

        # Valuation Methodology
        story.append(Paragraph("VALUATION METHODOLOGY", heading_style))
        methodology_text = """
        <b>Comparative Market Analysis (CMA) Approach:</b><br/><br/>

        This valuation employs a sophisticated weighted scoring system that evaluates comparable properties across
        multiple dimensions. Each comparable property is scored based on the following factors, with their respective
        weights in the overall similarity calculation:
        <br/><br/>
        • <b>Location Proximity (15%):</b> Distance from subject property. Properties within 1 mile receive the highest
        scores, with scores decreasing proportionally up to the maximum search radius of 5 miles.
        <br/><br/>
        • <b>Square Footage (25%):</b> Size similarity is critical. Properties within 10% of the subject's square footage
        receive optimal scores. The scoring allows for reasonable variation while penalizing significant size differences.
        <br/><br/>
        • <b>Sale Price (20%):</b> Price comparability is evaluated against the subject's list price or estimated market
        value. Properties within 10% price range receive the highest similarity scores.
        <br/><br/>
        • <b>Bedrooms (15%):</b> Exact bedroom matches receive full points, with one-bedroom differences receiving
        reduced but acceptable scores.
        <br/><br/>
        • <b>Bathrooms (10%):</b> Bathroom count similarity, accounting for full and half baths.
        <br/><br/>
        • <b>Year Built (10%):</b> Age similarity, with properties built within 5 years receiving optimal scores.
        <br/><br/>
        • <b>Property Type (5%):</b> Matching property classifications (Residential, Condo, Townhouse, etc.).
        <br/><br/>

        The final similarity score is a weighted average of all factors. Properties with scores above 70% are considered
        strong comparables.
        <br/><br/>
        <b>Professional Dollar Adjustments:</b> Following industry-standard appraisal practices, each comparable property
        receives dollar adjustments to account for differences from the subject property. Adjustments are made for:
        <br/><br/>
        • <b>Square Footage:</b> Size differences are adjusted using local price per square foot rates
        <br/><br/>
        • <b>Bedrooms & Bathrooms:</b> Room count differences are adjusted based on typical market values
        <br/><br/>
        • <b>Lot Size:</b> Significant lot size differences are adjusted proportionally
        <br/><br/>
        • <b>Age/Depreciation:</b> Age differences are adjusted for depreciation (typically 0.7% per year)
        <br/><br/>
        • <b>Time/Market Appreciation:</b> Older sales are adjusted upward for market appreciation (typically 0.8% per month)
        <br/><br/>
        • <b>Seller Concessions:</b> Concessions are added back to sale price to determine true market value
        <br/><br/>
        The adjusted prices are then weighted based on similarity score and number of adjustments required, with comps
        requiring fewer/smaller adjustments receiving more weight in the final value estimate.
        """
        story.append(Paragraph(methodology_text, body_style))
        story.append(Spacer(1, 0.3 * inch))

        # Comparable Properties Analysis
        story.append(Paragraph("COMPARABLE PROPERTIES ANALYSIS", heading_style))

        for i, comp in enumerate(comp_result.comparable_properties, 1):
            prop = comp.property

            story.append(Paragraph(f"Comparable Property #{i}", subheading_style))

            # Comp details table
            comp_data = [
                ["Address", f"{prop.address}, {prop.city}, {prop.state}"],
                ["Similarity Score", f"{comp.similarity_score:.1%}"],
            ]
            if comp.distance_miles:
                comp_data.append(
                    ["Distance from Subject", f"{comp.distance_miles:.2f} miles"]
                )
            if prop.bedrooms:
                comp_data.append(["Bedrooms", str(prop.bedrooms)])
            if prop.bathrooms:
                comp_data.append(["Bathrooms", str(prop.bathrooms)])
            if prop.square_feet:
                comp_data.append(["Square Feet", f"{prop.square_feet:,}"])
                if subject.square_feet:
                    sqft_diff = prop.square_feet - subject.square_feet
                    sqft_pct = (sqft_diff / subject.square_feet) * 100
                    comp_data.append(
                        ["Size Difference", f"{sqft_diff:+,} sqft ({sqft_pct:+.1f}%)"]
                    )
            if prop.lot_size_sqft:
                comp_data.append(["Lot Size", f"{prop.lot_size_sqft:,.0f} sqft"])
            if prop.year_built:
                if subject.year_built:
                    age_diff = prop.year_built - subject.year_built
                    comp_data.append(
                        ["Year Built", f"{prop.year_built} ({age_diff:+d} years)"]
                    )
                else:
                    comp_data.append(["Year Built", str(prop.year_built)])
            if prop.sold_price:
                comp_data.append(["Sold Price", f"${prop.sold_price:,.0f}"])
                if prop.sold_date:
                    comp_data.append(
                        ["Sale Date", prop.sold_date.strftime("%B %d, %Y")]
                    )
                    if prop.sale_recency_days is not None:
                        if prop.sale_recency_days < 30:
                            recency = f"{prop.sale_recency_days} days ago"
                        elif prop.sale_recency_days < 365:
                            recency = f"{prop.sale_recency_days // 30} months ago"
                        else:
                            recency = f"{prop.sale_recency_days // 365} years ago"
                        comp_data.append(["Sale Recency", recency])
                if comp.price_difference and subject.list_price:
                    comp_data.append(
                        [
                            "Price vs Subject",
                            f"${comp.price_difference:+,.0f} ({comp.price_difference_percent:+.1f}%)",
                        ]
                    )
            if prop.price_per_sqft:
                comp_data.append(["Price per SqFt", f"${prop.price_per_sqft:,.2f}"])

            comp_table = Table(comp_data, colWidths=[2.5 * inch, 3.5 * inch])
            comp_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#fff3e0")),
                        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#e65100")),
                        ("ALIGN", (0, 0), (0, -1), "LEFT"),
                        ("ALIGN", (1, 0), (1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#ffb74d")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(comp_table)
            story.append(Spacer(1, 0.15 * inch))

            # Match Reasoning
            if comp.match_reasons:
                story.append(
                    Paragraph(
                        "<b>Why This Property is Comparable:</b>", styles["Normal"]
                    )
                )
                reasons_text = " • ".join(comp.match_reasons)
                story.append(Paragraph(reasons_text, body_style))
                story.append(Spacer(1, 0.15 * inch))

            # Professional Adjustments
            if comp.adjustments:
                story.append(
                    Paragraph(
                        "<b>Professional Dollar Adjustments:</b>", styles["Normal"]
                    )
                )
                story.append(Spacer(1, 0.1 * inch))

                adj_data = [["Category", "Description", "Adjustment Amount"]]
                for adj in comp.adjustments:
                    adj_data.append(
                        [adj.category, adj.description, f"${adj.amount:+,.0f}"]
                    )

                adj_table = Table(
                    adj_data, colWidths=[1.5 * inch, 2.5 * inch, 1.5 * inch]
                )
                adj_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3f2fd")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("FONTSIZE", (0, 1), (-1, -1), 9),
                            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#90caf9")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.append(adj_table)
                story.append(Spacer(1, 0.1 * inch))

                if comp.adjusted_price:
                    comp_price = prop.sold_price or prop.list_price
                    story.append(
                        Paragraph(
                            f"<b>Original Sale Price:</b> ${comp_price:,.0f} | "
                            f"<b>Total Adjustments:</b> ${comp.total_adjustment_amount:+,.0f} | "
                            f"<b>Adjusted Price:</b> ${comp.adjusted_price:,.0f}",
                            body_style,
                        )
                    )
                story.append(Spacer(1, 0.15 * inch))

            # Detailed Analysis
            analysis_parts = []
            if comp.distance_miles:
                if comp.distance_miles < 0.5:
                    analysis_parts.append(
                        "This property is in very close proximity to the subject, indicating similar neighborhood characteristics and market conditions."
                    )
                elif comp.distance_miles < 1.0:
                    analysis_parts.append(
                        "Located within one mile, this property shares similar location advantages and market dynamics."
                    )
                else:
                    analysis_parts.append(
                        f"While located {comp.distance_miles:.2f} miles away, this property provides valuable market data from a similar area."
                    )

            if prop.square_feet and subject.square_feet:
                sqft_diff_pct = (
                    abs(prop.square_feet - subject.square_feet)
                    / subject.square_feet
                    * 100
                )
                if sqft_diff_pct < 5:
                    analysis_parts.append(
                        "The square footage is nearly identical, making this an excellent size match."
                    )
                elif sqft_diff_pct < 15:
                    analysis_parts.append(
                        "The size difference is minimal and within acceptable comparison range."
                    )
                else:
                    analysis_parts.append(
                        "There is a notable size difference, which has been factored into the similarity score."
                    )

            if prop.sold_price and subject.list_price:
                price_diff_pct = (
                    abs(comp.price_difference_percent)
                    if comp.price_difference_percent
                    else 0
                )
                if price_diff_pct < 5:
                    analysis_parts.append(
                        "The sale price closely aligns with the subject's list price, indicating strong market comparability."
                    )
                elif price_diff_pct < 15:
                    analysis_parts.append(
                        "The price difference is reasonable and reflects normal market variation."
                    )
                else:
                    analysis_parts.append(
                        "The price difference suggests potential adjustments may be needed, but the property still provides valuable market data."
                    )

            if prop.sold_date and prop.sale_recency_days is not None:
                if prop.sale_recency_days < 90:
                    analysis_parts.append(
                        "This is a very recent sale, providing current and relevant market data."
                    )
                elif prop.sale_recency_days < 180:
                    analysis_parts.append(
                        "This recent sale reflects current market conditions."
                    )
                else:
                    analysis_parts.append(
                        "While this sale is older, it still provides valuable historical market context."
                    )

            if analysis_parts:
                analysis_text = " ".join(analysis_parts)
                story.append(
                    Paragraph(f"<b>Detailed Analysis:</b> {analysis_text}", body_style)
                )

            story.append(Spacer(1, 0.2 * inch))

            if i < len(comp_result.comparable_properties):
                story.append(Spacer(1, 0.1 * inch))

        # Market Insights
        story.append(PageBreak())
        story.append(Paragraph("MARKET INSIGHTS & RECOMMENDATIONS", heading_style))

        insights_text = f"""
        <b>Market Analysis Summary:</b><br/><br/>

        Based on the analysis of {len(comp_result.comparable_properties)} comparable properties, the following insights
        can be drawn:
        <br/><br/>
        """

        if comp_result.average_price and comp_result.estimated_value:
            if comp_result.estimated_value > comp_result.average_price * 1.1:
                insights_text += """
                • The estimated value is significantly higher than the average comparable price, suggesting the subject
                property may have superior features, location advantages, or recent improvements that justify the premium.
                <br/><br/>
                """
            elif comp_result.estimated_value < comp_result.average_price * 0.9:
                insights_text += """
                • The estimated value is below the average comparable price, which may indicate opportunities for
                negotiation or that the property requires updates or improvements.
                <br/><br/>
                """
            else:
                insights_text += """
                • The estimated value aligns well with the average comparable price, indicating the property is
                appropriately priced relative to the market.
                <br/><br/>
                """

        if comp_result.confidence_score > 0.8:
            insights_text += """
            • <b>High Confidence:</b> The valuation is based on a strong set of comparable properties with high
            similarity scores, providing reliable market data.
            <br/><br/>
            """
        elif comp_result.confidence_score > 0.6:
            insights_text += """
            • <b>Moderate Confidence:</b> The comparables provide reasonable market data, though some variation in
            property characteristics should be considered.
            <br/><br/>
            """
        else:
            insights_text += """
            • <b>Lower Confidence:</b> While comparable properties were found, there is greater variation in
            characteristics. Additional market research may be beneficial.
            <br/><br/>
            """

        insights_text += """
        <b>Recommendations:</b><br/><br/>

        1. <b>Review Individual Comparables:</b> Examine each comparable property's specific characteristics and
        adjust the valuation based on features not captured in the automated analysis (e.g., condition, upgrades,
        lot features).
        <br/><br/>

        2. <b>Consider Market Trends:</b> Factor in current market conditions, interest rates, and local economic
        factors that may affect property values.
        <br/><br/>

        3. <b>Professional Inspection:</b> A physical inspection of the subject property is recommended to identify
        any issues or improvements that may affect value.
        <br/><br/>

        4. <b>Additional Research:</b> Review recent listings, pending sales, and market activity in the immediate
        area for the most current market intelligence.
        <br/><br/>

        <b>Disclaimer:</b> This report is generated using automated analysis of publicly available data. It should
        be used as a starting point for valuation discussions and should be supplemented with professional appraisal,
        inspection, and market expertise for final pricing decisions.
        """

        story.append(Paragraph(insights_text, body_style))
        story.append(Spacer(1, 0.3 * inch))

        # Footer with broker branding
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("─" * 80, styles["Normal"]))
        story.append(Spacer(1, 0.15 * inch))
        
        footer_style = ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )
        
        story.append(
            Paragraph(
                f"<b>{settings.broker_name}</b> | {settings.broker_title} | {settings.broker_company}",
                footer_style,
            )
        )
        story.append(
            Paragraph(
                f"{settings.broker_phone} | {settings.broker_email} | {settings.broker_website}",
                footer_style,
            )
        )
        story.append(
            Paragraph(
                f"{settings.broker_tagline}",
                ParagraphStyle("FooterTagline", parent=footer_style, fontSize=8, textColor=colors.HexColor("#2b6cb0")),
            )
        )
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                footer_style,
            )
        )
        story.append(
            Paragraph(
                f"© {datetime.now().year} {settings.broker_company}. This report is for informational purposes only.",
                ParagraphStyle("Disclaimer", parent=footer_style, fontSize=7),
            )
        )

        # Build PDF
        doc.build(story)

        return str(filepath)
