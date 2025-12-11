"""Training system for learning from comp guidelines and instructions."""
import logging
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from comp_analyzer import CompAnalyzer
from models import Property, CompProperty
from config import settings

logger = logging.getLogger(__name__)


class CompGuidelinesTrainer:
    """Trains the bot from comp guidelines and instructions."""
    
    def __init__(self, analyzer: CompAnalyzer):
        self.analyzer = analyzer
        self.guidelines_file = Path("comp_guidelines.json")
        self.guidelines: List[Dict[str, Any]] = []
        self.load_guidelines()
    
    def load_guidelines(self):
        """Load comp guidelines from file."""
        if self.guidelines_file.exists():
            try:
                with open(self.guidelines_file, 'r', encoding='utf-8') as f:
                    self.guidelines = json.load(f)
                logger.info(f"Loaded {len(self.guidelines)} comp guidelines")
            except Exception as e:
                logger.error(f"Error loading guidelines: {e}")
                self.guidelines = []
        else:
            self.guidelines = []
    
    def save_guidelines(self):
        """Save comp guidelines to file."""
        try:
            with open(self.guidelines_file, 'w', encoding='utf-8') as f:
                json.dump(self.guidelines, f, indent=2, default=str)
            logger.info(f"Saved {len(self.guidelines)} comp guidelines")
        except Exception as e:
            logger.error(f"Error saving guidelines: {e}")
    
    def add_guideline(
        self,
        description: str,
        criteria: Dict[str, Any],
        priority: float = 1.0,
        examples: Optional[List[str]] = None
    ):
        """
        Add a comp guideline.
        
        Args:
            description: Description of the guideline (e.g., "Properties should be within 1 mile")
            criteria: Dictionary of criteria (e.g., {"max_distance_miles": 1.0, "min_similarity": 0.8})
            priority: Priority weight (1.0 = normal, 2.0 = high priority)
            examples: List of example addresses or scenarios
        """
        guideline = {
            'description': description,
            'criteria': criteria,
            'priority': priority,
            'examples': examples or [],
            'usage_count': 0
        }
        self.guidelines.append(guideline)
        self.save_guidelines()
        logger.info(f"Added guideline: {description}")
        self.apply_guidelines()
    
    def add_instruction_text(self, instruction_text: str):
        """
        Parse and add guidelines from natural language instructions.
        
        Example instructions:
        - "Comparables should be within 1 mile and sold within 6 months"
        - "Prefer properties with similar lot sizes (within 20%)"
        - "Bedrooms must match exactly, bathrooms can vary by 0.5"
        - "Price should be within 15% of subject property"
        """
        # Simple keyword-based parsing (can be enhanced with NLP)
        criteria = {}
        priority = 1.0
        
        instruction_lower = instruction_text.lower()
        
        # Parse distance requirements
        if "mile" in instruction_lower or "miles" in instruction_lower:
            import re
            distance_match = re.search(r'within\s+(\d+(?:\.\d+)?)\s+miles?', instruction_lower)
            if distance_match:
                criteria['max_distance_miles'] = float(distance_match.group(1))
        
        # Parse time requirements
        if "month" in instruction_lower or "months" in instruction_lower:
            import re
            month_match = re.search(r'within\s+(\d+)\s+months?', instruction_lower)
            if month_match:
                criteria['max_age_months'] = int(month_match.group(1))
        
        # Parse similarity requirements
        if "similar" in instruction_lower and "lot" in instruction_lower:
            import re
            lot_match = re.search(r'within\s+(\d+)%', instruction_lower)
            if lot_match:
                criteria['lot_size_tolerance_percent'] = float(lot_match.group(1))
        
        # Parse bedroom requirements
        if "bedroom" in instruction_lower:
            if "match exactly" in instruction_lower or "must match" in instruction_lower:
                criteria['bedrooms_exact_match'] = True
            elif "vary" in instruction_lower or "within" in instruction_lower:
                import re
                bed_match = re.search(r'within\s+(\d+)', instruction_lower)
                if bed_match:
                    criteria['bedrooms_tolerance'] = int(bed_match.group(1))
        
        # Parse bathroom requirements
        if "bathroom" in instruction_lower:
            if "match exactly" in instruction_lower:
                criteria['bathrooms_exact_match'] = True
            elif "vary" in instruction_lower:
                import re
                bath_match = re.search(r'by\s+(\d+(?:\.\d+)?)', instruction_lower)
                if bath_match:
                    criteria['bathrooms_tolerance'] = float(bath_match.group(1))
        
        # Parse price requirements
        if "price" in instruction_lower and "within" in instruction_lower:
            import re
            price_match = re.search(r'within\s+(\d+)%', instruction_lower)
            if price_match:
                criteria['price_tolerance_percent'] = float(price_match.group(1))
        
        # Check for priority keywords
        if "must" in instruction_lower or "required" in instruction_lower:
            priority = 2.0
        elif "prefer" in instruction_lower or "should" in instruction_lower:
            priority = 1.5
        
        if criteria:
            self.add_guideline(instruction_text, criteria, priority)
            return True
        else:
            logger.warning(f"Could not parse instruction: {instruction_text}")
            return False
    
    def apply_guidelines(self):
        """Apply guidelines to update analyzer settings and weights."""
        if not self.guidelines:
            return
        
        # Update settings based on guidelines
        for guideline in self.guidelines:
            criteria = guideline.get('criteria', {})
            priority = guideline.get('priority', 1.0)
            
            # Update max distance if specified
            if 'max_distance_miles' in criteria:
                new_distance = criteria['max_distance_miles']
                if priority >= 2.0:  # High priority - override
                    settings.max_comp_distance_miles = new_distance
                elif new_distance < settings.max_comp_distance_miles:  # Use stricter
                    settings.max_comp_distance_miles = new_distance
            
            # Update max age if specified
            if 'max_age_months' in criteria:
                new_age_days = criteria['max_age_months'] * 30
                if priority >= 2.0:
                    settings.max_comp_age_days = new_age_days
                elif new_age_days < settings.max_comp_age_days:
                    settings.max_comp_age_days = new_age_days
        
        # Update similarity weights based on guidelines
        # Count how many guidelines mention each factor
        factor_mentions = {
            'distance': 0,
            'square_feet': 0,
            'price': 0,
            'bedrooms': 0,
            'bathrooms': 0,
            'lot_size': 0,
            'year_built': 0
        }
        
        for guideline in self.guidelines:
            criteria = guideline.get('criteria', {})
            priority = guideline.get('priority', 1.0)
            weight = priority
            
            if 'max_distance_miles' in criteria:
                factor_mentions['distance'] += weight
            if 'lot_size_tolerance_percent' in criteria:
                factor_mentions['lot_size'] += weight
            if 'bedrooms_exact_match' in criteria or 'bedrooms_tolerance' in criteria:
                factor_mentions['bedrooms'] += weight
            if 'bathrooms_exact_match' in criteria or 'bathrooms_tolerance' in criteria:
                factor_mentions['bathrooms'] += weight
            if 'price_tolerance_percent' in criteria:
                factor_mentions['price'] += weight
        
        # Adjust weights if guidelines emphasize certain factors
        total_mentions = sum(factor_mentions.values())
        if total_mentions > 0:
            # Increase weights for frequently mentioned factors
            current_weights = self.analyzer.weights.copy()
            for factor, mentions in factor_mentions.items():
                if mentions > 0:
                    # Increase weight proportionally
                    boost = (mentions / total_mentions) * 0.2  # Max 20% boost
                    if factor in current_weights:
                        current_weights[factor] = min(1.0, current_weights[factor] + boost)
            
            # Renormalize weights
            total = sum(current_weights.values())
            if total > 0:
                current_weights = {k: v / total for k, v in current_weights.items()}
                self.analyzer.update_weights(current_weights)
                logger.info(f"Updated weights based on {len(self.guidelines)} guidelines")
    
    def filter_by_guidelines(
        self,
        subject: Property,
        candidates: List[Property]
    ) -> List[Property]:
        """Filter candidates based on guidelines."""
        if not self.guidelines:
            return candidates
        
        filtered = []
        for candidate in candidates:
            passes = True
            
            for guideline in self.guidelines:
                criteria = guideline.get('criteria', {})
                priority = guideline.get('priority', 1.0)
                
                # Check distance requirement
                if 'max_distance_miles' in criteria:
                    from geopy.distance import geodesic
                    if subject.latitude and subject.longitude and candidate.latitude and candidate.longitude:
                        distance = geodesic(
                            (subject.latitude, subject.longitude),
                            (candidate.latitude, candidate.longitude)
                        ).miles
                        if distance > criteria['max_distance_miles']:
                            if priority >= 2.0:  # Must pass
                                passes = False
                                break
                
                # Check lot size requirement
                if 'lot_size_tolerance_percent' in criteria and subject.lot_size_sqft and candidate.lot_size_sqft:
                    lot_diff_pct = abs(subject.lot_size_sqft - candidate.lot_size_sqft) / subject.lot_size_sqft * 100
                    if lot_diff_pct > criteria['lot_size_tolerance_percent']:
                        if priority >= 2.0:
                            passes = False
                            break
                
                # Check bedroom requirement
                if 'bedrooms_exact_match' in criteria and criteria['bedrooms_exact_match']:
                    if subject.bedrooms and candidate.bedrooms and subject.bedrooms != candidate.bedrooms:
                        if priority >= 2.0:
                            passes = False
                            break
                elif 'bedrooms_tolerance' in criteria:
                    if subject.bedrooms and candidate.bedrooms:
                        bed_diff = abs(subject.bedrooms - candidate.bedrooms)
                        if bed_diff > criteria['bedrooms_tolerance']:
                            if priority >= 2.0:
                                passes = False
                                break
                
                # Check bathroom requirement
                if 'bathrooms_exact_match' in criteria and criteria['bathrooms_exact_match']:
                    if subject.bathrooms and candidate.bathrooms and subject.bathrooms != candidate.bathrooms:
                        if priority >= 2.0:
                            passes = False
                            break
                elif 'bathrooms_tolerance' in criteria:
                    if subject.bathrooms and candidate.bathrooms:
                        bath_diff = abs(subject.bathrooms - candidate.bathrooms)
                        if bath_diff > criteria['bathrooms_tolerance']:
                            if priority >= 2.0:
                                passes = False
                                break
                
                # Check price requirement
                if 'price_tolerance_percent' in criteria and subject.list_price:
                    comp_price = candidate.sold_price or candidate.list_price
                    if comp_price:
                        price_diff_pct = abs(comp_price - subject.list_price) / subject.list_price * 100
                        if price_diff_pct > criteria['price_tolerance_percent']:
                            if priority >= 2.0:
                                passes = False
                                break
            
            if passes:
                filtered.append(candidate)
        
        return filtered
    
    def list_guidelines(self) -> List[Dict[str, Any]]:
        """List all current guidelines."""
        return self.guidelines.copy()
    
    def remove_guideline(self, index: int):
        """Remove a guideline by index."""
        if 0 <= index < len(self.guidelines):
            removed = self.guidelines.pop(index)
            self.save_guidelines()
            logger.info(f"Removed guideline: {removed.get('description', 'Unknown')}")
            self.apply_guidelines()
            return True
        return False
