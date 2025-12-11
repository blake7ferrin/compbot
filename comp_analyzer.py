"""Comparable property analysis engine with professional dollar adjustments."""
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from geopy.distance import geodesic
import numpy as np
from config import settings
from models import Property, CompProperty, CompResult, PropertyStatus, Adjustment

logger = logging.getLogger(__name__)


class CompAnalyzer:
    """Analyzes and finds comparable properties."""
    
    def __init__(self):
        self.weights = {
            'distance': 0.15,
            'square_feet': 0.25,
            'price': 0.20,
            'bedrooms': 0.15,
            'bathrooms': 0.10,
            'year_built': 0.10,
            'property_type': 0.05
        }
        self.learning_data = []  # Store successful comp selections for training
    
    def find_comps(
        self,
        subject: Property,
        candidates: List[Property],
        max_comps: Optional[int] = None
    ) -> CompResult:
        """Find comparable properties for a subject property."""
        if not candidates:
            return CompResult(
                subject_property=subject,
                comparable_properties=[],
                confidence_score=0.0
            )
        
        max_comps = max_comps or settings.max_comps_to_return
        
        # Filter and score candidates
        comp_properties = []
        for candidate in candidates:
            # Skip if it's the same property
            if candidate.mls_number == subject.mls_number:
                continue
            
            # Calculate similarity score
            score, reasons = self._calculate_similarity(subject, candidate)
            
            # Calculate distance if coordinates available
            distance = None
            if subject.latitude and subject.longitude and candidate.latitude and candidate.longitude:
                distance = geodesic(
                    (subject.latitude, subject.longitude),
                    (candidate.latitude, candidate.longitude)
                ).miles
            
            # Filter by distance if configured
            if distance and distance > settings.max_comp_distance_miles:
                continue
            
            # Filter by minimum score - but be more lenient if subject property has missing data
            min_score = settings.min_comp_score
            # Lower threshold if subject is missing key data (bedrooms, bathrooms, or price)
            if (not subject.bedrooms or not subject.bathrooms or not subject.list_price):
                min_score = min_score * 0.8  # 20% lower threshold (0.7 -> 0.56)
            
            if score < min_score:
                continue
            
            # Calculate price differences
            price_diff = None
            price_diff_pct = None
            if subject.list_price and candidate.sold_price:
                price_diff = candidate.sold_price - subject.list_price
                price_diff_pct = (price_diff / subject.list_price) * 100
            elif subject.list_price and candidate.list_price:
                price_diff = candidate.list_price - subject.list_price
                price_diff_pct = (price_diff / subject.list_price) * 100
            
            comp_prop = CompProperty(
                property=candidate,
                similarity_score=score,
                distance_miles=distance,
                price_difference=price_diff,
                price_difference_percent=price_diff_pct,
                match_reasons=reasons
            )
            comp_properties.append(comp_prop)
        
        # Sort by similarity score (highest first)
        comp_properties.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Take top N
        comp_properties = comp_properties[:max_comps]
        
        # Apply professional dollar adjustments to each comp (Step 4 from guide)
        for comp_prop in comp_properties:
            adjustments = self._calculate_adjustments(subject, comp_prop.property)
            comp_prop.adjustments = adjustments
            comp_prop.adjustment_count = len(adjustments)
            comp_prop.total_adjustment_amount = sum(adj.amount for adj in adjustments)
            
            # Calculate adjusted price
            comp_price = comp_prop.property.sold_price or comp_prop.property.list_price
            if comp_price:
                comp_prop.adjusted_price = comp_price + comp_prop.total_adjustment_amount
        
        # Calculate statistics using ADJUSTED prices (Step 5 from guide)
        if comp_properties:
            # Use adjusted prices for final valuation
            adjusted_prices = [
                cp.adjusted_price
                for cp in comp_properties
                if cp.adjusted_price is not None
            ]
            
            if adjusted_prices:
                # Weight comps: fewer/smaller adjustments = more weight
                weights = []
                for cp in comp_properties:
                    if cp.adjusted_price is not None:
                        # Weight based on: similarity score, adjustment count, adjustment size
                        adj_count_weight = 1.0 / (1.0 + cp.adjustment_count * 0.1)  # Fewer adjustments = higher weight
                        adj_size_weight = 1.0 / (1.0 + abs(cp.total_adjustment_amount) / (cp.adjusted_price * 0.01))  # Smaller % adjustments = higher weight
                        weight = cp.similarity_score * adj_count_weight * adj_size_weight
                        weights.append(weight)
                    else:
                        weights.append(0.0)
                
                # Normalize weights
                total_weight = sum(weights)
                if total_weight > 0:
                    weights = [w / total_weight for w in weights]
                else:
                    weights = [1.0 / len(weights)] * len(weights)
                
                # Weighted average of adjusted prices
                avg_price = sum(p * w for p, w in zip(adjusted_prices, weights))
                
                # Calculate average price per sqft from adjusted prices
                sqft_prices = []
                for cp, weight in zip(comp_properties, weights):
                    if cp.adjusted_price and cp.property.square_feet:
                        sqft_prices.append((cp.adjusted_price / cp.property.square_feet) * weight)
                
                avg_price_per_sqft = sum(sqft_prices) if sqft_prices else None
                
                # Estimate value based on subject's square footage using adjusted comps
                estimated_value = None
                if avg_price_per_sqft and subject.square_feet:
                    estimated_value = avg_price_per_sqft * subject.square_feet
                
                # Confidence based on number, quality, and adjustment consistency
                base_confidence = min(1.0, len(comp_properties) / 10.0) * np.mean([cp.similarity_score for cp in comp_properties])
                # Reduce confidence if adjustments vary widely (indicates inconsistent comps)
                if len(adjusted_prices) > 1:
                    price_std = np.std(adjusted_prices)
                    price_mean = np.mean(adjusted_prices)
                    if price_mean > 0:
                        cv = price_std / price_mean  # Coefficient of variation
                        consistency_factor = max(0.5, 1.0 - cv)  # Lower CV = higher consistency
                        confidence = base_confidence * consistency_factor
                    else:
                        confidence = base_confidence
                else:
                    confidence = base_confidence
            else:
                # Fallback to unadjusted prices if no adjustments could be calculated
                sold_prices = [
                    cp.property.sold_price or cp.property.list_price
                    for cp in comp_properties
                    if cp.property.sold_price or cp.property.list_price
                ]
                if sold_prices:
                    avg_price = np.mean(sold_prices)
                    sqft_prices = []
                    for cp in comp_properties:
                        price = cp.property.sold_price or cp.property.list_price
                        if price and cp.property.square_feet:
                            sqft_prices.append(price / cp.property.square_feet)
                    avg_price_per_sqft = np.mean(sqft_prices) if sqft_prices else None
                    estimated_value = avg_price_per_sqft * subject.square_feet if avg_price_per_sqft and subject.square_feet else None
                    confidence = min(1.0, len(comp_properties) / 10.0) * np.mean([cp.similarity_score for cp in comp_properties])
                else:
                    avg_price = None
                    avg_price_per_sqft = None
                    estimated_value = None
                    confidence = 0.0
        else:
            avg_price = None
            avg_price_per_sqft = None
            estimated_value = None
            confidence = 0.0
        
        return CompResult(
            subject_property=subject,
            comparable_properties=comp_properties,
            average_price=avg_price,
            average_price_per_sqft=avg_price_per_sqft,
            estimated_value=estimated_value,
            confidence_score=confidence
        )
    
    def _calculate_similarity(self, subject: Property, candidate: Property) -> tuple:
        """Calculate similarity score between two properties."""
        scores = []
        reasons = []
        
        # Distance score (closer is better)
        if subject.latitude and subject.longitude and candidate.latitude and candidate.longitude:
            distance = geodesic(
                (subject.latitude, subject.longitude),
                (candidate.latitude, candidate.longitude)
            ).miles
            # Normalize: 0 miles = 1.0, 5 miles = 0.0
            distance_score = max(0, 1.0 - (distance / settings.max_comp_distance_miles))
            scores.append(('distance', distance_score))
            if distance_score > 0.7:
                reasons.append(f"Close proximity ({distance:.2f} miles)")
        else:
            scores.append(('distance', 0.5))  # Neutral if no coordinates
        
        # Square footage score
        if subject.square_feet and candidate.square_feet:
            sqft_diff = abs(subject.square_feet - candidate.square_feet)
            sqft_pct_diff = sqft_diff / subject.square_feet
            sqft_score = max(0, 1.0 - (sqft_pct_diff * 2))  # 10% diff = 0.8 score
            scores.append(('square_feet', sqft_score))
            if sqft_score > 0.7:
                reasons.append(f"Similar size ({candidate.square_feet:,} sqft)")
        else:
            scores.append(('square_feet', 0.5))
        
        # Price score (for sold properties, compare to subject's list price)
        if subject.list_price:
            comp_price = candidate.sold_price or candidate.list_price
            if comp_price:
                price_diff = abs(comp_price - subject.list_price)
                price_pct_diff = price_diff / subject.list_price
                price_score = max(0, 1.0 - (price_pct_diff * 2))  # 10% diff = 0.8 score
                scores.append(('price', price_score))
                if price_score > 0.7:
                    reasons.append(f"Similar price (${comp_price:,.0f})")
            else:
                scores.append(('price', 0.5))
        else:
            scores.append(('price', 0.5))
        
        # Bedrooms score - be more lenient when subject data is missing
        if subject.bedrooms and candidate.bedrooms:
            if subject.bedrooms == candidate.bedrooms:
                scores.append(('bedrooms', 1.0))
                reasons.append(f"Same bedrooms ({candidate.bedrooms})")
            elif abs(subject.bedrooms - candidate.bedrooms) == 1:
                scores.append(('bedrooms', 0.7))
            else:
                scores.append(('bedrooms', 0.3))
        elif candidate.bedrooms:
            # Subject bedrooms missing, but candidate has them - give neutral score
            scores.append(('bedrooms', 0.6))
        else:
            # Both missing - neutral score
            scores.append(('bedrooms', 0.5))
        
        # Bathrooms score - be more lenient when subject data is missing
        if subject.bathrooms and candidate.bathrooms:
            bath_diff = abs(subject.bathrooms - candidate.bathrooms)
            if bath_diff == 0:
                scores.append(('bathrooms', 1.0))
            elif bath_diff <= 0.5:
                scores.append(('bathrooms', 0.8))
            elif bath_diff <= 1.0:
                scores.append(('bathrooms', 0.5))
            else:
                scores.append(('bathrooms', 0.2))
        elif candidate.bathrooms:
            # Subject bathrooms missing, but candidate has them - give neutral score
            scores.append(('bathrooms', 0.6))
        else:
            # Both missing - neutral score
            scores.append(('bathrooms', 0.5))
        
        # Year built score (similar age)
        if subject.year_built and candidate.year_built:
            age_diff = abs(subject.year_built - candidate.year_built)
            if age_diff <= 5:
                scores.append(('year_built', 1.0))
            elif age_diff <= 10:
                scores.append(('year_built', 0.7))
            elif age_diff <= 20:
                scores.append(('year_built', 0.4))
            else:
                scores.append(('year_built', 0.2))
        else:
            scores.append(('year_built', 0.5))
        
        # Property type score
        if subject.property_type == candidate.property_type:
            scores.append(('property_type', 1.0))
            reasons.append(f"Same property type ({candidate.property_type.value})")
        else:
            scores.append(('property_type', 0.0))
        
        # Calculate weighted average
        total_score = 0.0
        total_weight = 0.0
        for factor, score in scores:
            weight = self.weights.get(factor, 0.1)
            total_score += score * weight
            total_weight += weight
        
        final_score = total_score / total_weight if total_weight > 0 else 0.0
        
        return final_score, reasons
    
    def record_comp_selection(
        self,
        subject: Property,
        selected_comps: List[CompProperty],
        user_feedback: Optional[float] = None
    ):
        """Record a comp selection for learning."""
        if not settings.enable_learning:
            return
        
        self.learning_data.append({
            'subject': subject,
            'selected_comps': selected_comps,
            'user_feedback': user_feedback,
            'timestamp': datetime.now()
        })
        
        # Keep only recent data (last 1000 selections)
        if len(self.learning_data) > 1000:
            self.learning_data = self.learning_data[-1000:]
    
    def _calculate_adjustments(self, subject: Property, comp: Property) -> List[Adjustment]:
        """Calculate professional dollar adjustments for a comparable property.
        
        Follows professional appraisal guidelines:
        - If comp is better than subject: subtract value (negative adjustment)
        - If comp is worse than subject: add value (positive adjustment)
        """
        adjustments = []
        comp_price = comp.sold_price or comp.list_price
        
        if not comp_price:
            return adjustments
        
        # Get price per square foot for size-based adjustments
        comp_price_per_sqft = comp_price / comp.square_feet if comp.square_feet else None
        subject_price_per_sqft = (subject.list_price / subject.square_feet) if (subject.list_price and subject.square_feet) else comp_price_per_sqft
        price_per_sqft = subject_price_per_sqft or comp_price_per_sqft or 200.0  # Fallback to $200/sqft if unknown
        
        # 1. Square Footage Adjustment
        if subject.square_feet and comp.square_feet:
            sqft_diff = comp.square_feet - subject.square_feet
            if abs(sqft_diff) > 50:  # Only adjust if difference is significant (>50 sqft)
                adjustment_amount = sqft_diff * price_per_sqft
                if adjustment_amount != 0:
                    adjustments.append(Adjustment(
                        category="Square Footage",
                        description=f"Size difference: {sqft_diff:+,} sqft",
                        amount=-adjustment_amount,  # Negative: comp larger subtracts value, comp smaller adds value
                        reason=f"Comp is {abs(sqft_diff):,} sqft {'larger' if sqft_diff > 0 else 'smaller'} than subject"
                    ))
        
        # 2. Bedrooms Adjustment
        if subject.bedrooms is not None and comp.bedrooms is not None:
            bed_diff = comp.bedrooms - subject.bedrooms
            if bed_diff != 0:
                # Typical bedroom value: $10,000-$20,000 depending on market
                # Use 1% of comp price per bedroom as conservative estimate
                bedroom_value = comp_price * 0.015  # 1.5% per bedroom
                adjustment_amount = -bed_diff * bedroom_value
                if adjustment_amount != 0:
                    adjustments.append(Adjustment(
                        category="Bedrooms",
                        description=f"Bedroom difference: {bed_diff:+d}",
                        amount=adjustment_amount,
                        reason=f"Comp has {abs(bed_diff)} {'more' if bed_diff > 0 else 'fewer'} bedroom(s) than subject"
                    ))
        
        # 3. Bathrooms Adjustment
        if subject.bathrooms is not None and comp.bathrooms is not None:
            bath_diff = comp.bathrooms - subject.bathrooms
            if abs(bath_diff) >= 0.5:  # Only adjust for significant differences
                # Typical bathroom value: $5,000-$15,000
                bathroom_value = comp_price * 0.01  # 1% per full bathroom
                adjustment_amount = -bath_diff * bathroom_value
                if adjustment_amount != 0:
                    adjustments.append(Adjustment(
                        category="Bathrooms",
                        description=f"Bathroom difference: {bath_diff:+.1f}",
                        amount=adjustment_amount,
                        reason=f"Comp has {abs(bath_diff):.1f} {'more' if bath_diff > 0 else 'fewer'} bathroom(s) than subject"
                    ))
        
        # 4. Lot Size Adjustment
        if subject.lot_size_sqft and comp.lot_size_sqft:
            lot_diff = comp.lot_size_sqft - subject.lot_size_sqft
            if abs(lot_diff) > 1000:  # Only adjust for significant differences (>1000 sqft)
                # Lot value typically $1-$5 per sqft depending on area
                lot_value_per_sqft = comp_price * 0.00001  # Conservative: 0.001% of price per sqft
                adjustment_amount = -lot_diff * lot_value_per_sqft
                if adjustment_amount != 0:
                    adjustments.append(Adjustment(
                        category="Lot Size",
                        description=f"Lot size difference: {lot_diff:+,} sqft",
                        amount=adjustment_amount,
                        reason=f"Comp lot is {abs(lot_diff):,} sqft {'larger' if lot_diff > 0 else 'smaller'} than subject"
                    ))
        
        # 5. Age/Year Built Adjustment
        if subject.year_built and comp.year_built:
            age_diff = comp.year_built - subject.year_built
            if abs(age_diff) > 5:  # Only adjust for significant age differences (>5 years)
                # Depreciation: typically 0.5-1% per year of age difference
                depreciation_rate = 0.007  # 0.7% per year
                if age_diff > 0:  # Comp is older
                    adjustment_amount = comp_price * depreciation_rate * age_diff
                    adjustments.append(Adjustment(
                        category="Age",
                        description=f"Age difference: {age_diff:+d} years",
                        amount=adjustment_amount,  # Positive: comp older adds value (comp is worse)
                        reason=f"Comp is {age_diff} years older than subject (depreciation adjustment)"
                    ))
                else:  # Comp is newer
                    adjustment_amount = comp_price * depreciation_rate * abs(age_diff)
                    adjustments.append(Adjustment(
                        category="Age",
                        description=f"Age difference: {age_diff:+d} years",
                        amount=-adjustment_amount,  # Negative: comp newer subtracts value (comp is better)
                        reason=f"Comp is {abs(age_diff)} years newer than subject (depreciation adjustment)"
                    ))
        
        # 6. Time/Market Appreciation Adjustment
        if comp.sold_date:
            months_ago = (datetime.now() - comp.sold_date).days / 30.0
            if months_ago > 3:  # Only adjust if sale was more than 3 months ago
                # Market appreciation: typically 0.5-1% per month (varies by market)
                appreciation_rate = 0.008  # 0.8% per month (conservative)
                adjustment_amount = comp_price * appreciation_rate * months_ago
                adjustments.append(Adjustment(
                    category="Time",
                    description=f"Sale recency: {months_ago:.1f} months ago",
                    amount=-adjustment_amount,  # Negative: older sale subtracts value (market has appreciated)
                    reason=f"Comp sold {months_ago:.1f} months ago; adjusting for market appreciation"
                ))
        
        # 7. Seller Concessions Adjustment
        if comp.seller_concessions and comp.seller_concessions > 0:
            adjustments.append(Adjustment(
                category="Concessions",
                description=f"Seller concessions: ${comp.seller_concessions:,.0f}",
                amount=comp.seller_concessions,  # Positive: add back concessions to get true market value
                reason=f"Seller paid ${comp.seller_concessions:,.0f} in concessions; adding back to sale price"
            ))
        
        # 8. Condition/Upgrades Adjustment (if data available)
        # Note: This requires condition ratings or upgrade lists which may not be available
        # For now, we'll skip this but the structure is ready for future enhancement
        
        # 9. Location Adjustment (basic - can be enhanced with traffic data)
        # Note: Detailed location adjustments (busy street vs cul-de-sac) require additional data
        # For now, distance is already factored into similarity score
        
        return adjustments
    
    def update_weights(self, new_weights: dict):
        """Update similarity weights (can be called after training)."""
        self.weights.update(new_weights)
        logger.info(f"Updated comp analysis weights: {self.weights}")

