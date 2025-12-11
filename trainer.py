"""Machine learning trainer for improving comp selection."""
import logging
from typing import List, Dict, Any
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from comp_analyzer import CompAnalyzer
from models import Property, CompProperty

logger = logging.getLogger(__name__)


class CompTrainer:
    """Trains models to improve comp selection."""
    
    def __init__(self, analyzer: CompAnalyzer):
        self.analyzer = analyzer
        self.model = None
    
    def train_from_feedback(self, learning_data: List[Dict[str, Any]]):
        """Train model based on user feedback and successful comp selections."""
        if not learning_data or len(learning_data) < 10:
            logger.warning("Not enough learning data to train model")
            return
        
        # Extract features and targets
        X = []
        y = []
        
        for record in learning_data:
            subject = record['subject']
            selected_comps = record['selected_comps']
            feedback = record.get('user_feedback', 1.0)  # Default positive feedback
            
            # Create features for each comp selection
            for comp_prop in selected_comps:
                features = self._extract_features(subject, comp_prop.property)
                X.append(features)
                # Target: similarity score adjusted by feedback
                y.append(comp_prop.similarity_score * feedback)
        
        if len(X) < 10:
            logger.warning("Not enough training examples")
            return
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        logger.info(f"Model trained - Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
        
        # Extract feature importance to update weights
        feature_names = [
            'distance', 'sqft_diff', 'price_diff', 'bedroom_diff',
            'bathroom_diff', 'year_diff', 'property_type_match'
        ]
        
        importances = self.model.feature_importances_
        importance_dict = dict(zip(feature_names, importances))
        
        # Normalize and update weights
        total_importance = sum(importances)
        if total_importance > 0:
            normalized_weights = {
                'distance': importance_dict.get('distance', 0.15) / total_importance,
                'square_feet': importance_dict.get('sqft_diff', 0.25) / total_importance,
                'price': importance_dict.get('price_diff', 0.20) / total_importance,
                'bedrooms': importance_dict.get('bedroom_diff', 0.15) / total_importance,
                'bathrooms': importance_dict.get('bathroom_diff', 0.10) / total_importance,
                'year_built': importance_dict.get('year_diff', 0.10) / total_importance,
                'property_type': importance_dict.get('property_type_match', 0.05) / total_importance
            }
            
            # Normalize to sum to 1.0
            total = sum(normalized_weights.values())
            normalized_weights = {k: v / total for k, v in normalized_weights.items()}
            
            self.analyzer.update_weights(normalized_weights)
    
    def _extract_features(self, subject: Property, candidate: Property) -> List[float]:
        """Extract numerical features for ML model."""
        from geopy.distance import geodesic
        from config import settings
        
        features = []
        
        # Distance
        if subject.latitude and subject.longitude and candidate.latitude and candidate.longitude:
            distance = geodesic(
                (subject.latitude, subject.longitude),
                (candidate.latitude, candidate.longitude)
            ).miles
            features.append(distance / settings.max_comp_distance_miles)  # Normalize
        else:
            features.append(1.0)  # Max distance if unknown
        
        # Square footage difference (normalized)
        if subject.square_feet and candidate.square_feet:
            sqft_diff = abs(subject.square_feet - candidate.square_feet) / subject.square_feet
            features.append(sqft_diff)
        else:
            features.append(1.0)
        
        # Price difference (normalized)
        if subject.list_price:
            comp_price = candidate.sold_price or candidate.list_price
            if comp_price:
                price_diff = abs(comp_price - subject.list_price) / subject.list_price
                features.append(price_diff)
            else:
                features.append(1.0)
        else:
            features.append(1.0)
        
        # Bedroom difference (normalized)
        if subject.bedrooms and candidate.bedrooms:
            bedroom_diff = abs(subject.bedrooms - candidate.bedrooms) / max(subject.bedrooms, 1)
            features.append(bedroom_diff)
        else:
            features.append(1.0)
        
        # Bathroom difference (normalized)
        if subject.bathrooms and candidate.bathrooms:
            bathroom_diff = abs(subject.bathrooms - candidate.bathrooms) / max(subject.bathrooms, 0.5)
            features.append(bathroom_diff)
        else:
            features.append(1.0)
        
        # Year built difference (normalized)
        if subject.year_built and candidate.year_built:
            year_diff = abs(subject.year_built - candidate.year_built) / 100.0  # Normalize by 100 years
            features.append(min(year_diff, 1.0))
        else:
            features.append(1.0)
        
        # Property type match (1.0 = match, 0.0 = no match)
        features.append(1.0 if subject.property_type == candidate.property_type else 0.0)
        
        return features
    
    def predict_similarity(self, subject: Property, candidate: Property) -> float:
        """Predict similarity score using trained model."""
        if self.model is None:
            # Fall back to analyzer's method
            score, _ = self.analyzer._calculate_similarity(subject, candidate)
            return score
        
        features = self._extract_features(subject, candidate)
        prediction = self.model.predict([features])[0]
        return max(0.0, min(1.0, prediction))  # Clamp to [0, 1]

