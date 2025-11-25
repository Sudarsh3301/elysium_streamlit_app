"""
Unified Data Loader for Elysium Model Catalogue
Uses models_final.jsonl as the single source of truth for all model data.
Eliminates all local image dependencies and CSV image column usage.
"""

import json
import pandas as pd
import streamlit as st
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)


class UnifiedModelLoader:
    """
    Unified data loader that uses models_final.jsonl as the single source of truth.
    Provides all model data including HTTPS image URLs without any local dependencies.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the unified model loader."""
        self.project_root = project_root or self._find_project_root()
        self.models_file = self.project_root / "elysium_kb" / "models_final.jsonl"
        self._models_cache = None
        
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current_dir = Path.cwd().resolve()
        
        # Look for marker files
        marker_files = ['elysium_streamlit_app', 'elysium_kb']
        
        # Check current directory first
        if any((current_dir / marker).exists() for marker in marker_files):
            return current_dir
            
        # Check parent directories
        for parent in current_dir.parents:
            if any((parent / marker).exists() for marker in marker_files):
                return parent
                
        return current_dir
    
    @st.cache_data
    def load_models(_self) -> pd.DataFrame:
        """
        Load all models from models_final.jsonl and convert to DataFrame.
        
        Returns:
            DataFrame with all model data including HTTPS image URLs
        """
        try:
            if not _self.models_file.exists():
                logger.error(f"Models file not found: {_self.models_file}")
                return pd.DataFrame()
            
            models = []
            with open(_self.models_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        model = json.loads(line)
                        # Normalize model data
                        normalized_model = _self._normalize_model_data(model)
                        models.append(normalized_model)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON on line {line_num}: {e}")
                        continue
            
            if not models:
                logger.warning("No valid models found in models_final.jsonl")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(models)
            logger.info(f"✅ Loaded {len(df)} models from models_final.jsonl")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return pd.DataFrame()
    
    def _normalize_model_data(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize model data from JSONL format to standardized format.
        
        Args:
            model: Raw model data from JSONL
            
        Returns:
            Normalized model data
        """
        # Extract attributes
        attributes = model.get('attributes', {})
        
        # Parse height to cm
        height_cm = self._parse_height_to_cm(attributes.get('height', ''))
        
        # Normalize colors
        hair_color = self._normalize_attribute(attributes.get('hair', ''))
        eye_color = self._normalize_attribute(attributes.get('eyes', ''))
        
        # Get thumbnail (first image or dedicated thumbnail)
        images = model.get('images', [])
        thumbnail = model.get('thumbnail', '')
        if not thumbnail and images:
            thumbnail = images[0]
        
        return {
            'model_id': str(model.get('model_id', '')),
            'name': model.get('name', '').strip(),
            'division': model.get('division', '').strip().lower(),
            'profile_url': model.get('profile_url', ''),
            'thumbnail': thumbnail,
            'images': images,  # List of HTTPS URLs
            'height_cm': height_cm,
            'hair_color': hair_color,
            'eye_color': eye_color,
            'bust': attributes.get('bust', ''),
            'waist': attributes.get('waist', ''),
            'hips': attributes.get('hips', ''),
            'shoes': attributes.get('shoes', ''),
            # Add computed fields
            'primary_thumbnail': thumbnail,  # For compatibility
            'portfolio_images': images[1:] if len(images) > 1 else []  # Exclude thumbnail
        }
    
    def _parse_height_to_cm(self, height_str: str) -> int:
        """Parse height string to centimeters."""
        try:
            # Extract cm value from strings like "5' 10\" - 178"
            cm_match = re.search(r'(\d+)$', height_str.strip())
            if cm_match:
                return int(cm_match.group(1))
            
            # Fallback: try to extract feet/inches and convert
            feet_inches_match = re.search(r"(\d+)'\s*(\d+(?:\.\d+)?)", height_str)
            if feet_inches_match:
                feet = int(feet_inches_match.group(1))
                inches = float(feet_inches_match.group(2))
                return int((feet * 12 + inches) * 2.54)
            
            return 170  # Default height
        except Exception:
            return 170
    
    def _normalize_attribute(self, attr: str) -> str:
        """Normalize hair/eye color attributes."""
        return attr.lower().strip() if attr else ""
    
    def get_model_by_id(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific model by ID."""
        df = self.load_models()
        if df.empty:
            return None
        
        model_rows = df[df['model_id'] == str(model_id)]
        if model_rows.empty:
            return None
        
        return model_rows.iloc[0].to_dict()
    
    def get_models_by_division(self, division: str) -> pd.DataFrame:
        """Get models filtered by division."""
        df = self.load_models()
        if df.empty:
            return df
        
        return df[df['division'] == division.lower()]
    
    def search_models(self, query: str, limit: int = 50) -> pd.DataFrame:
        """Search models by name."""
        df = self.load_models()
        if df.empty or not query:
            return df.head(limit)
        
        # Simple name search
        mask = df['name'].str.contains(query, case=False, na=False)
        return df[mask].head(limit)


# Global instance
unified_loader = UnifiedModelLoader()
