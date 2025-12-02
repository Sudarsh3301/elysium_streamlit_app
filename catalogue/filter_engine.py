"""
Catalogue Filtering System
Handles all filtering logic including AI-powered search and manual filters.
"""

import pandas as pd
import json
import logging
from typing import Dict, List, Optional, Any
import streamlit as st

# Import data processing classes
from .data_processing import AttributeMatcher, DivisionMapper, HeightCalculator

# Import Groq client
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from groq_client import GroqClient

logger = logging.getLogger(__name__)


class GroqLLMClient:
    """Handles AI query parsing using Groq API."""

    def __init__(self):
        """Initialize Groq client."""
        try:
            self.client = GroqClient()
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.client = None

    @staticmethod
    def create_system_prompt() -> str:
        """Create system prompt for the AI assistant."""
        return """You are an assistant that extracts structured search filters for a fashion model catalogue.

Given a client query, return ONLY a JSON object with these optional keys:
hair_color, eye_color, height_min, height_max, height_relative, division, bust, waist, hips, shoes.

Rules:
- If the text uses relative terms like "taller", "shorter", "petite", "above average", "below average",
  include "height_relative": "taller"/"shorter"/"petite".
- If no explicit height mentioned but relative term appears, leave numeric height blank.
- Map "mainboard" or "main" → division: "ima"
- Map "development" or "dev" → division: "dev"
- Map "commercial" → division: "mai"
- Map "editorial" → division: "mai"
- For hair colors: "brunette" = "brown", "golden" = "blonde", "jet" = "black"
- For eye colors: "aqua" = "blue", "hazel" = "green"

Examples:

Input: "taller blonde models with blue eyes from the development board"
Output:
{
  "hair_color": "blonde",
  "eye_color": "blue",
  "height_relative": "taller",
  "division": "dev"
}

Input: "shorter brunette models"
Output:
{
  "hair_color": "brown",
  "height_relative": "shorter"
}

Input: "mainboard models above average height"
Output:
{
  "height_relative": "taller",
  "division": "ima"
}

Input: "petite commercial faces with aqua eyes"
Output:
{
  "eye_color": "blue",
  "height_relative": "petite",
  "division": "mai"
}

Input: "models around 175cm with 34 inch bust"
Output:
{
  "height_min": 170,
  "height_max": 180,
  "bust": "34"
}

Input: "blonde blue-eyed model less than 165cm"
Output:
{
  "hair_color": "blonde",
  "eye_color": "blue",
  "height_max": 165
}

Return ONLY the JSON object, no additional text."""

    @staticmethod
    def create_user_prompt(user_input: str) -> str:
        """Create user prompt with the actual query."""
        return f'Input: "{user_input}"\nOutput:'

    def query_groq(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Send query to Groq API and parse response."""
        try:
            if not self.client:
                st.error("❌ Groq client not initialized. Please check your API key configuration.")
                return None

            system_prompt = self.create_system_prompt()
            user_prompt = self.create_user_prompt(user_input)

            # Use temperature 0.6 as specified in requirements
            result = self.client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.6,
                max_tokens=1024
            )

            if result is None:
                st.error("❌ Failed to get response from Groq API. Please try again.")
                return None

            return result if result else {}

        except Exception as e:
            logger.error(f"Error querying Groq: {e}")
            st.error(f"❌ Error querying AI service: {e}")
            return None


class FilterEngine:
    """Handles filtering logic for models with enhanced comparative and semantic filtering."""

    @staticmethod
    def apply_filters(df: pd.DataFrame,
                     hair_colors: Optional[List[str]] = None,
                     eye_colors: Optional[List[str]] = None,
                     height_range: Optional[tuple] = None,
                     divisions: Optional[List[str]] = None,
                     ai_filters: Optional[Dict[str, Any]] = None,
                     text_search: Optional[str] = None) -> pd.DataFrame:
        """Apply unified filtering pipeline with comparative, semantic, and fuzzy matching."""
        if df.empty:
            return df

        # Combine all filters into a single unified filter dict
        unified_filters = {}

        # Add manual filters
        if hair_colors and len(hair_colors) > 0:
            unified_filters['hair_color'] = hair_colors[0]  # Take first selection for now
        if eye_colors and len(eye_colors) > 0:
            unified_filters['eye_color'] = eye_colors[0]    # Take first selection for now
        if height_range and len(height_range) == 2:
            unified_filters['height_min'], unified_filters['height_max'] = height_range
        if divisions and len(divisions) > 0:
            unified_filters['division'] = divisions[0]      # Take first selection for now

        # Add text search
        if text_search and text_search.strip():
            unified_filters['text_search'] = text_search.strip()

        # Add AI filters (they override manual filters)
        if ai_filters and isinstance(ai_filters, dict):
            unified_filters.update(ai_filters)

        return FilterEngine._apply_unified_filters(df, unified_filters)

    @staticmethod
    def _apply_unified_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply unified filtering logic with all enhancements."""
        try:
            filtered_df = df.copy()

            # Hair color filtering with fuzzy matching
            if filters.get("hair_color"):
                hair_value = str(filters["hair_color"]).lower()
                filtered_df = filtered_df[
                    filtered_df["hair_color"].apply(
                        lambda x: AttributeMatcher.match_attribute(hair_value, x, "hair")
                    )
                ]

            # Eye color filtering with fuzzy matching
            if filters.get("eye_color"):
                eye_value = str(filters["eye_color"]).lower()
                filtered_df = filtered_df[
                    filtered_df["eye_color"].apply(
                        lambda x: AttributeMatcher.match_attribute(eye_value, x, "eye")
                    )
                ]

            # Numeric height filters with variance tolerance
            if filters.get("height_min") or filters.get("height_max"):
                min_h = filters.get("height_min", 0)
                max_h = filters.get("height_max", 300)

                # Add variance tolerance (±3cm) for more flexible matching
                variance = 3
                min_h_with_variance = max(0, min_h - variance) if min_h > 0 else 0
                max_h_with_variance = max_h + variance if max_h < 300 else 300

                filtered_df = filtered_df[
                    (filtered_df["height_cm"] >= min_h_with_variance) &
                    (filtered_df["height_cm"] <= max_h_with_variance)
                ]

            # Relative height filters
            if filters.get("height_relative"):
                height_range = HeightCalculator.calculate_relative_height_range(
                    df, filters["height_relative"]
                )
                if height_range[0] is not None and height_range[1] is not None:
                    min_h, max_h = height_range
                    filtered_df = filtered_df[
                        (filtered_df["height_cm"] >= min_h) & (filtered_df["height_cm"] <= max_h)
                    ]

            # Division filtering with semantic mapping
            if filters.get("division"):
                normalized_div = DivisionMapper.normalize_division(filters["division"])
                if normalized_div:
                    filtered_df = filtered_df[
                        filtered_df["division"].str.lower().str.contains(normalized_div, na=False)
                    ]

            # Additional attribute filters (bust, waist, hips, shoes)
            for attr in ["bust", "waist", "hips", "shoes"]:
                if filters.get(attr):
                    attr_value = str(filters[attr])
                    # Extract numeric part for comparison
                    import re
                    numeric_match = re.search(r'\d+', attr_value)
                    if numeric_match:
                        target_value = int(numeric_match.group())
                        filtered_df = filtered_df[
                            filtered_df[attr].str.contains(str(target_value), na=False)
                        ]

            # Text search functionality
            if filters.get("text_search"):
                search_text = str(filters["text_search"]).lower().strip()
                if search_text:
                    # Create search conditions for multiple fields
                    search_conditions = []

                    # Search in model name
                    if 'name' in filtered_df.columns:
                        name_mask = filtered_df['name'].str.lower().str.contains(search_text, na=False, regex=False)
                        search_conditions.append(name_mask)

                    # Search in model_id
                    if 'model_id' in filtered_df.columns:
                        id_mask = filtered_df['model_id'].str.lower().str.contains(search_text, na=False, regex=False)
                        search_conditions.append(id_mask)

                    # Search in division
                    if 'division' in filtered_df.columns:
                        div_mask = filtered_df['division'].str.lower().str.contains(search_text, na=False, regex=False)
                        search_conditions.append(div_mask)

                    # Search in hair color
                    if 'hair_color' in filtered_df.columns:
                        hair_mask = filtered_df['hair_color'].str.lower().str.contains(search_text, na=False, regex=False)
                        search_conditions.append(hair_mask)

                    # Search in eye color
                    if 'eye_color' in filtered_df.columns:
                        eye_mask = filtered_df['eye_color'].str.lower().str.contains(search_text, na=False, regex=False)
                        search_conditions.append(eye_mask)

                    # Search in profile URL if available
                    if 'profile_url' in filtered_df.columns:
                        url_mask = filtered_df['profile_url'].str.lower().str.contains(search_text, na=False, regex=False)
                        search_conditions.append(url_mask)

                    # Combine all search conditions with OR logic
                    if search_conditions:
                        combined_mask = search_conditions[0]
                        for condition in search_conditions[1:]:
                            combined_mask = combined_mask | condition
                        filtered_df = filtered_df[combined_mask]

            return filtered_df

        except Exception as e:
            logger.warning(f"Error applying unified filters: {e}")
            return df
