"""
Catalogue Data Processing Module
Handles loading, normalizing, and processing model data.
REFACTORED: Now uses unified_data_loader and HTTPS-only image handling.
"""

import pandas as pd
import re
import logging
from typing import Dict, List, Optional, Any
import streamlit as st

# Import unified data loader and HTTPS image utilities
from unified_data_loader import unified_loader
from https_image_utils import https_image_handler

logger = logging.getLogger(__name__)


class DataLoader:
    """
    REFACTORED: Now uses unified_data_loader instead of CSV loading.
    Maintains compatibility with existing code while using models_final.jsonl.
    """

    @staticmethod
    def parse_height_to_cm(height_str: str) -> int:
        """Parse height string to centimeters integer."""
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

            return 170  # Default height if parsing fails
        except Exception as e:
            logger.warning(f"Failed to parse height '{height_str}': {e}")
            return 170

    @staticmethod
    def normalize_attribute(attr: str) -> str:
        """Normalize hair/eye color attributes to lowercase."""
        return attr.lower().strip() if attr else ""

    @staticmethod
    def load_and_normalize_models(file_path: str = None) -> pd.DataFrame:
        """
        REFACTORED: Load models from models_final.jsonl instead of CSV.
        file_path parameter is ignored for compatibility.
        """
        try:
            # Use unified loader instead of CSV
            df = unified_loader.load_models()

            if df.empty:
                st.error("No models found in models_final.jsonl")
                return pd.DataFrame()

            logger.info(f"Loaded {len(df)} models from models_final.jsonl")
            return df

        except Exception as e:
            st.error(f"Error loading models: {e}")
            return pd.DataFrame()


class AttributeMatcher:
    """Handles fuzzy matching for model attributes with synonyms."""

    # Synonym mappings for hair colors
    HAIR_SYNONYMS = {
        "blonde": ["blonde", "light", "golden", "fair"],
        "brown": ["brown", "brunette", "dark brown", "chestnut"],
        "black": ["black", "jet", "dark", "raven"],
        "red": ["red", "auburn", "ginger", "copper"],
        "gray": ["gray", "grey", "silver"],
        "white": ["white", "platinum"]
    }

    # Synonym mappings for eye colors
    EYE_SYNONYMS = {
        "blue": ["blue", "aqua", "azure", "sapphire"],
        "brown": ["brown", "hazel", "amber", "chocolate"],
        "green": ["green", "emerald", "jade"],
        "gray": ["gray", "grey", "silver"],
        "black": ["black", "dark"]
    }

    @staticmethod
    def match_attribute(search_value: str, field_value: str, attribute_type: str = "hair") -> bool:
        """
        Check if search_value matches field_value using synonym expansion.

        Args:
            search_value: The value being searched for (e.g., "brunette")
            field_value: The actual field value (e.g., "brown")
            attribute_type: Either "hair" or "eye"
        """
        if not search_value or not field_value:
            return False

        search_lower = str(search_value).lower().strip()
        field_lower = str(field_value).lower().strip()

        # Direct match
        if search_lower in field_lower or field_lower in search_lower:
            return True

        # Synonym matching
        synonyms = AttributeMatcher.HAIR_SYNONYMS if attribute_type == "hair" else AttributeMatcher.EYE_SYNONYMS

        for canonical, synonym_list in synonyms.items():
            # If search term is in synonym list, check if field matches canonical or any synonym
            if search_lower in synonym_list:
                if canonical in field_lower or any(syn in field_lower for syn in synonym_list):
                    return True

            # If field value is in synonym list, check if search matches canonical or any synonym
            if field_lower in synonym_list:
                if canonical == search_lower or search_lower in synonym_list:
                    return True

        return False


class DivisionMapper:
    """Handles semantic division mapping and normalization."""

    DIVISION_MAPPINGS = {
        "mainboard": "ima",
        "main": "mai",
        "ima": "ima",
        "development": "dev",
        "dev": "dev",
        "commercial": "mai",
        "mai": "mai",
        "editorial": "mai"
    }

    @staticmethod
    def normalize_division(division_term: str) -> str:
        """
        Normalize semantic division terms to actual division codes.

        Args:
            division_term: The division term to normalize (e.g., "mainboard", "development")

        Returns:
            Normalized division code (e.g., "ima", "dev", "mai") or original term if no mapping
        """
        if not division_term:
            return ""

        term_lower = str(division_term).lower().strip()
        return DivisionMapper.DIVISION_MAPPINGS.get(term_lower, term_lower)


class HeightCalculator:
    """Handles relative height calculations and filtering."""

    @staticmethod
    def calculate_relative_height_range(df: pd.DataFrame, relative_term: str) -> tuple:
        """
        Calculate height range based on relative terms.

        Args:
            df: DataFrame containing height data
            relative_term: "taller", "shorter", or "petite"

        Returns:
            Tuple of (min_height, max_height) or (None, None) if invalid
        """
        if df.empty or 'height_cm' not in df.columns:
            return (None, None)

        avg_height = df['height_cm'].mean()

        if relative_term == "taller":
            return (avg_height + 3, 300)  # Above average + 3cm
        elif relative_term == "shorter":
            return (0, avg_height - 3)    # Below average - 3cm
        elif relative_term == "petite":
            return (0, 165)               # Under 165cm
        else:
            return (None, None)


class ImageHandler:
    """
    REFACTORED: Now handles HTTPS URLs only, no local filesystem dependencies.
    Maintains compatibility with existing code.
    """



    @staticmethod
    def parse_images_list(images_str) -> List[str]:
        """
        Parse images data - now expects list of HTTPS URLs.
        Maintains compatibility with old CSV string format.
        """
        if not images_str:
            return []

        try:
            # Handle list directly (from models_final.jsonl)
            if isinstance(images_str, list):
                return [img for img in images_str if img and isinstance(img, str)]

            # Handle string representation of list (legacy CSV format)
            if isinstance(images_str, str):
                if images_str.startswith('[') and images_str.endswith(']'):
                    import ast
                    parsed = ast.literal_eval(images_str)
                    return [img for img in parsed if img and isinstance(img, str)]
                else:
                    # Single image path
                    return [images_str] if images_str else []

            return []
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Could not parse images: {images_str}, error: {e}")
            return []

    @staticmethod
    def get_thumbnail_path(model_data: Dict[str, Any]) -> str:
        """
        REFACTORED: Get thumbnail HTTPS URL for a model.
        """
        return https_image_handler.get_thumbnail_url(model_data)

    @staticmethod
    def get_valid_images(model_data: Dict[str, Any]) -> List[str]:
        """
        REFACTORED: Get list of valid HTTPS URLs for a model.
        """
        return https_image_handler.get_portfolio_urls(model_data)
