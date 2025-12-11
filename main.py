"""Command-line interface for MLS Comp Bot."""
import argparse
import json
import sys
from bot import MLSCompBot
from config import settings
from report_generator import ReportGenerator

def print_comp_result(result):
    """Pretty print comp results."""
    print("\n" + "="*80)
    print("COMPARABLE PROPERTY ANALYSIS")
    print("="*80)
    
    subject = result.subject_property
    print(f"\nSubject Property:")
    print(f"  Address: {subject.address}, {subject.city}, {subject.state} {subject.zip_code}")
    print(f"  MLS#: {subject.mls_number}")
    print(f"  Type: {subject.property_type.value}")
    print(f"  Bedrooms: {subject.bedrooms or 'N/A'}")
    print(f"  Bathrooms: {subject.bathrooms or 'N/A'}")
    print(f"  Square Feet: {subject.square_feet:,}" if subject.square_feet else "  Square Feet: N/A")
    print(f"  List Price: ${subject.list_price:,.0f}" if subject.list_price else "  List Price: N/A")
    
    print(f"\nFound {len(result.comparable_properties)} Comparable Properties")
    print(f"Confidence Score: {result.confidence_score:.2%}")
    
    if result.average_price:
        print(f"\nAverage Comp Price: ${result.average_price:,.0f}")
    if result.average_price_per_sqft:
        print(f"Average Price per SqFt: ${result.average_price_per_sqft:,.2f}")
    if result.estimated_value:
        print(f"Estimated Value: ${result.estimated_value:,.0f}")
    
    print("\n" + "-"*80)
    print("COMPARABLE PROPERTIES:")
    print("-"*80)
    
    for i, comp in enumerate(result.comparable_properties, 1):
        prop = comp.property
        print(f"\n{i}. {prop.address}, {prop.city}, {prop.state}")
        print(f"   MLS#: {prop.mls_number}")
        print(f"   Similarity Score: {comp.similarity_score:.2%}")
        if comp.distance_miles:
            print(f"   Distance: {comp.distance_miles:.2f} miles")
        print(f"   Bedrooms: {prop.bedrooms or 'N/A'}, Bathrooms: {prop.bathrooms or 'N/A'}")
        print(f"   Square Feet: {prop.square_feet:,}" if prop.square_feet else "   Square Feet: N/A")
        if prop.sold_price:
            print(f"   Sold Price: ${prop.sold_price:,.0f}")
            if prop.sold_date:
                print(f"   Sold Date: {prop.sold_date.strftime('%Y-%m-%d')}")
        elif prop.list_price:
            print(f"   List Price: ${prop.list_price:,.0f}")
        if comp.price_difference:
            print(f"   Price Difference: ${comp.price_difference:,.0f} ({comp.price_difference_percent:+.1f}%)")
        if comp.match_reasons:
            print(f"   Match Reasons: {', '.join(comp.match_reasons)}")
    
    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="MLS Comp Bot - Find comparable properties")
    parser.add_argument("--mls-number", help="MLS number of subject property")
    parser.add_argument("--address", help="Address of subject property")
    parser.add_argument("--city", help="City for search")
    parser.add_argument("--state", help="State for search (e.g., AZ, CA)")
    parser.add_argument("--zip", help="ZIP code for search")
    parser.add_argument("--property-type", help="Property type (Residential, Condo, etc.)")
    parser.add_argument("--bedrooms", type=int, help="Number of bedrooms")
    parser.add_argument("--bathrooms", type=float, help="Number of bathrooms")
    parser.add_argument("--sqft", type=int, help="Square footage")
    parser.add_argument("--price", type=float, help="List price")
    parser.add_argument("--max-comps", type=int, default=10, help="Maximum number of comps to return")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--report", action="store_true", help="Generate detailed property valuation report")
    parser.add_argument("--save-report", type=str, help="Save report to file (specify format: text, html, or markdown)")
    parser.add_argument("--train", action="store_true", help="Train the model with collected data")
    parser.add_argument("--feedback", type=float, help="Provide feedback rating (0.0-1.0) for last result")
    
    args = parser.parse_args()
    
    # Initialize bot
    bot = MLSCompBot()
    
    # Connect to ATTOM API
    print("Connecting to ATTOM API...")
    if not bot.connect():
        print("ERROR: Failed to connect to ATTOM API. Check your ATTOM_API_KEY in .env file.")
        sys.exit(1)
    
    try:
        # Train model if requested
        if args.train:
            print("Training model...")
            bot.train_model()
            print("Training completed!")
            return
        
        # Find comps
        result = None
        
        if args.mls_number:
            print(f"Finding comps for MLS# {args.mls_number}...")
            result = bot.find_comps_for_property(mls_number=args.mls_number, max_comps=args.max_comps)
        elif args.address:
            print(f"Finding comps for {args.address}...")
            result = bot.find_comps_for_property(
                address=args.address,
                city=args.city,
                state=args.state,
                zip_code=args.zip,
                max_comps=args.max_comps
            )
        elif args.city:
            print(f"Finding comps by criteria in {args.city}...")
            print("NOTE: ATTOM API requires a specific address. Please use --address instead.")
            result = None
        else:
            parser.print_help()
            sys.exit(1)
        
        if not result:
            print("ERROR: Could not find comparable properties.")
            sys.exit(1)
        
        # Generate report if requested
        if args.report or args.save_report:
            report_gen = ReportGenerator()
            
            if args.save_report:
                # Save report to file
                format_type = args.save_report.lower()
                if format_type not in ["text", "html", "markdown"]:
                    print(f"ERROR: Invalid format '{format_type}'. Use: text, html, or markdown")
                    sys.exit(1)
                
                filepath = report_gen.save_report(result, format=format_type)
                print(f"\n✓ Report saved to: {filepath}")
                print(f"  Format: {format_type.upper()}")
                
                # Also show preview
                print("\n" + "="*80)
                print("REPORT PREVIEW (first 50 lines):")
                print("="*80)
                report_content = report_gen.generate_report(result, format_type)
                preview_lines = report_content.split('\n')[:50]
                print('\n'.join(preview_lines))
                if len(report_content.split('\n')) > 50:
                    print(f"\n... ({len(report_content.split('\n')) - 50} more lines - see full report in file)")
            else:
                # Just display report
                report_content = report_gen.generate_report(result, "text")
                print(report_content)
            
            # Handle feedback
            if args.feedback is not None:
                bot.provide_feedback(result, args.feedback)
                print(f"\nFeedback recorded: {args.feedback:.2f}")
            
            return
        
        # Output results
        if args.json:
            # Convert to JSON-serializable format
            output = {
                "subject_property": {
                    "mls_number": result.subject_property.mls_number,
                    "address": result.subject_property.address,
                    "city": result.subject_property.city,
                    "state": result.subject_property.state,
                    "zip_code": result.subject_property.zip_code,
                    "property_type": result.subject_property.property_type.value,
                    "bedrooms": result.subject_property.bedrooms,
                    "bathrooms": result.subject_property.bathrooms,
                    "square_feet": result.subject_property.square_feet,
                    "list_price": result.subject_property.list_price,
                },
                "comparable_properties": [
                    {
                        "mls_number": cp.property.mls_number,
                        "address": cp.property.address,
                        "city": cp.property.city,
                        "state": cp.property.state,
                        "zip_code": cp.property.zip_code,
                        "similarity_score": cp.similarity_score,
                        "distance_miles": cp.distance_miles,
                        "sold_price": cp.property.sold_price,
                        "list_price": cp.property.list_price,
                        "bedrooms": cp.property.bedrooms,
                        "bathrooms": cp.property.bathrooms,
                        "square_feet": cp.property.square_feet,
                        "sold_date": cp.property.sold_date.isoformat() if cp.property.sold_date else None,
                        "price_difference": cp.price_difference,
                        "price_difference_percent": cp.price_difference_percent,
                        "match_reasons": cp.match_reasons
                    }
                    for cp in result.comparable_properties
                ],
                "average_price": result.average_price,
                "average_price_per_sqft": result.average_price_per_sqft,
                "estimated_value": result.estimated_value,
                "confidence_score": result.confidence_score
            }
            print(json.dumps(output, indent=2))
        else:
            print_comp_result(result)
        
        # Handle feedback
        if args.feedback is not None:
            bot.provide_feedback(result, args.feedback)
            print(f"\nFeedback recorded: {args.feedback:.2f}")
    
    finally:
        bot.disconnect()


if __name__ == "__main__":
    main()

