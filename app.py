"""
Elysium Model Catalogue - Streamlit App with AI-powered Query Parsing
A bare-bones Streamlit web app that demonstrates interactive model catalogue 
with AI-powered query parsing using Ollama for offline inference.
"""

import streamlit as st
import pandas as pd
import json
import requests
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import base64
from athena_ui import AthenaUI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Elysium Model Catalogue",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
MODELS_FILE = "../elysium_kb/models.jsonl"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:4b"  # Using available model

def get_image_base64(image_path: str) -> str:
    """Convert image to base64 string for HTML embedding."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        logger.warning(f"Could not encode image {image_path}: {e}")
        # Return a small transparent pixel as fallback
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def get_model_index_in_filtered(model_id: str, filtered_df: pd.DataFrame) -> int:
    """Get the index of a model in the filtered dataframe."""
    try:
        # Convert to list and find index
        model_ids = filtered_df['model_id'].tolist()
        return model_ids.index(model_id)
    except (ValueError, KeyError):
        return 0

class DataLoader:
    """Handles loading and normalizing model data from JSONL."""
    
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
    def load_and_normalize_models(file_path: str) -> pd.DataFrame:
        """Load models from JSONL and normalize data."""
        models = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        model = json.loads(line)
                        
                        # Flatten and normalize data
                        normalized_model = {
                            'model_id': model.get('model_id', ''),
                            'name': model.get('name', '').strip(),
                            'division': model.get('division', ''),
                            'profile_url': model.get('profile_url', ''),
                            'thumbnail': model.get('thumbnail', ''),
                            'height_cm': DataLoader.parse_height_to_cm(
                                model.get('attributes', {}).get('height', '')
                            ),
                            'hair_color': DataLoader.normalize_attribute(
                                model.get('attributes', {}).get('hair', '')
                            ),
                            'eye_color': DataLoader.normalize_attribute(
                                model.get('attributes', {}).get('eyes', '')
                            ),
                            'bust': model.get('attributes', {}).get('bust', ''),
                            'waist': model.get('attributes', {}).get('waist', ''),
                            'hips': model.get('attributes', {}).get('hips', ''),
                            'shoes': model.get('attributes', {}).get('shoes', ''),
                            'images': model.get('images', [])
                        }
                        models.append(normalized_model)
                        
        except FileNotFoundError:
            st.error(f"Models file not found: {file_path}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error loading models: {e}")
            return pd.DataFrame()
        
        df = pd.DataFrame(models)
        logger.info(f"Loaded {len(df)} models from {file_path}")
        return df

class OllamaClient:
    """Handles AI query parsing using Ollama."""
    
    @staticmethod
    def create_prompt(user_input: str) -> str:
        """Create enhanced prompt template for Ollama with comparative and semantic filtering."""
        return f"""You are an assistant that extracts structured search filters for a fashion model catalogue.

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
{{
  "hair_color": "blonde",
  "eye_color": "blue",
  "height_relative": "taller",
  "division": "dev"
}}

Input: "shorter brunette models"
Output:
{{
  "hair_color": "brown",
  "height_relative": "shorter"
}}

Input: "mainboard models above average height"
Output:
{{
  "height_relative": "taller",
  "division": "ima"
}}

Input: "petite commercial faces with aqua eyes"
Output:
{{
  "eye_color": "blue",
  "height_relative": "petite",
  "division": "mai"
}}

Input: "models around 175cm with 34 inch bust"
Output:
{{
  "height_min": 170,
  "height_max": 180,
  "bust": "34"
}}

Input: "blonde blue-eyed model less than 165cm"
Output:
{{
  "hair_color": "blonde",
  "eye_color": "blue",
  "height_max": 165
}}

Input: "{user_input}"
Output:"""

    @staticmethod
    def query_ollama(prompt: str) -> Optional[Dict[str, Any]]:
        """Send query to Ollama and parse response."""
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(OLLAMA_URL, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get('response', '').strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{[^}]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            
            return {}
            
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to Ollama. Please ensure Ollama is running on localhost:11434")
            return None
        except requests.exceptions.Timeout:
            st.error("⏱️ Ollama request timed out. Please try again.")
            return None
        except json.JSONDecodeError as e:
            st.warning(f"⚠️ Could not parse AI response as JSON: {e}")
            return {}
        except Exception as e:
            st.error(f"❌ Error querying Ollama: {e}")
            return None

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

class FilterEngine:
    """Handles filtering logic for models with enhanced comparative and semantic filtering."""

    @staticmethod
    def apply_filters(df: pd.DataFrame,
                     hair_colors: Optional[List[str]] = None,
                     eye_colors: Optional[List[str]] = None,
                     height_range: Optional[tuple] = None,
                     divisions: Optional[List[str]] = None,
                     ai_filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
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

            return filtered_df

        except Exception as e:
            logger.warning(f"Error applying unified filters: {e}")
            return df

class ImageHandler:
    """Handles local image loading and fallbacks."""

    @staticmethod
    def get_local_image_path(image_path: str) -> str:
        """Convert relative image path to absolute local path."""
        # Remove leading slash if present and ensure forward slashes
        clean_path = image_path.lstrip('/').replace('\\', '/')
        # Build absolute path from the elysium_kb directory
        local_path = os.path.join("..", "elysium_kb", clean_path)
        return local_path

    @staticmethod
    def get_thumbnail_path(model_data: Dict[str, Any]) -> str:
        """Get the best available thumbnail path for a model."""
        # First try to use local thumbnail from images array
        images = model_data.get('images', [])
        if images:
            # Look for thumbnail.jpg first
            for img in images:
                if 'thumbnail' in img.lower():
                    local_path = ImageHandler.get_local_image_path(img)
                    if os.path.exists(local_path):
                        return local_path

            # If no thumbnail found, use first image
            first_img = images[0]
            local_path = ImageHandler.get_local_image_path(first_img)
            if os.path.exists(local_path):
                return local_path

        # Fallback to remote thumbnail if available
        if model_data.get('thumbnail'):
            return model_data['thumbnail']

        # Final fallback to placeholder
        return "https://via.placeholder.com/300x400/cccccc/666666?text=No+Image"

    @staticmethod
    def get_valid_images(model_data: Dict[str, Any]) -> List[str]:
        """Get list of valid local image paths for a model."""
        valid_images = []
        images = model_data.get('images', [])

        for img_path in images:
            local_path = ImageHandler.get_local_image_path(img_path)
            if os.path.exists(local_path):
                valid_images.append(local_path)

        return valid_images

def display_model_card(model_data: Dict[str, Any], col):
    """Display a single model card in the given column."""
    with col:
        # Create card container with styling
        with st.container():
            # Model image using local path with controlled sizing
            thumbnail_path = ImageHandler.get_thumbnail_path(model_data)

            try:
                # Use a specific height parameter to force consistent sizing
                st.image(
                    thumbnail_path,
                    width=300,  # Fixed width for consistency
                    caption=""
                )
            except Exception:
                # Fallback to placeholder if image fails to load
                st.image(
                    "https://via.placeholder.com/300x250/cccccc/666666?text=No+Image",
                    width=300
                )

            # Model details
            st.markdown(f"**{model_data['name']}**")
            st.markdown(f"*Division: {model_data['division'].upper()}*")

            # Attributes in a compact format
            attr_col1, attr_col2 = st.columns(2)
            with attr_col1:
                st.markdown(f"👁️ {model_data['eye_color'].title()}")
                st.markdown(f"📏 {model_data['height_cm']} cm")
            with attr_col2:
                st.markdown(f"💇 {model_data['hair_color'].title()}")

            # View Portfolio button
            if st.button(
                "👁️ View Portfolio",
                key=f"view_{model_data['model_id']}",
                type="secondary"
            ):
                st.session_state.selected_model = model_data['model_id']
                st.rerun()

            st.markdown("---")

def show_expanded_model_view(model_data: Dict[str, Any], filtered_df: pd.DataFrame):
    """Display expanded model view with full details and image gallery."""

    # Header Section with Navigation
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

    with nav_col1:
        if st.button("← Back to Catalogue", type="secondary"):
            st.session_state.selected_model = None
            st.rerun()

    with nav_col2:
        st.markdown(f"### {model_data['name']} ({model_data['division'].upper()})")

    with nav_col3:
        # Navigation buttons
        current_index = get_model_index_in_filtered(model_data['model_id'], filtered_df)
        total_models = len(filtered_df)

        if total_models > 1:
            nav_buttons_col1, nav_buttons_col2 = st.columns(2)

            with nav_buttons_col1:
                if st.button("⬅️ Previous", disabled=(current_index <= 0)):
                    prev_model = filtered_df.iloc[current_index - 1]
                    st.session_state.selected_model = prev_model['model_id']
                    st.rerun()

            with nav_buttons_col2:
                if st.button("➡️ Next", disabled=(current_index >= total_models - 1)):
                    next_model = filtered_df.iloc[current_index + 1]
                    st.session_state.selected_model = next_model['model_id']
                    st.rerun()

            st.caption(f"Model {current_index + 1} of {total_models}")

    st.markdown("---")

    # Metadata Section
    st.subheader("📋 Model Details")

    # Create a neat layout for attributes
    detail_cols = st.columns(3)

    with detail_cols[0]:
        st.markdown(f"**Height:** {model_data['height_cm']} cm")
        st.markdown(f"**Hair:** {model_data['hair_color'].title()}")
        st.markdown(f"**Eyes:** {model_data['eye_color'].title()}")

    with detail_cols[1]:
        if model_data.get('bust'):
            st.markdown(f"**Bust:** {model_data['bust']}")
        if model_data.get('waist'):
            st.markdown(f"**Waist:** {model_data['waist']}")
        if model_data.get('hips'):
            st.markdown(f"**Hips:** {model_data['hips']}")

    with detail_cols[2]:
        if model_data.get('shoes'):
            st.markdown(f"**Shoes:** {model_data['shoes']}")
        st.markdown(f"**Division:** {model_data['division'].upper()}")
        st.markdown(f"**Model ID:** {model_data['model_id']}")

    st.markdown("---")

    # Image Gallery Section with Carousel
    st.subheader("📸 Portfolio Gallery")

    valid_images = ImageHandler.get_valid_images(model_data)

    if valid_images:
        # Initialize carousel state
        if f'carousel_index_{model_data["model_id"]}' not in st.session_state:
            st.session_state[f'carousel_index_{model_data["model_id"]}'] = 0

        current_carousel_index = st.session_state[f'carousel_index_{model_data["model_id"]}']
        total_images = len(valid_images)

        # Carousel controls
        carousel_col1, carousel_col2, carousel_col3 = st.columns([1, 2, 1])

        with carousel_col1:
            if st.button("⬅️ Previous Image", disabled=(current_carousel_index <= 0), key=f"prev_img_{model_data['model_id']}"):
                st.session_state[f'carousel_index_{model_data["model_id"]}'] -= 1
                st.rerun()

        with carousel_col2:
            st.markdown(f"**Image {current_carousel_index + 1} of {total_images}**")

        with carousel_col3:
            if st.button("➡️ Next Image", disabled=(current_carousel_index >= total_images - 1), key=f"next_img_{model_data['model_id']}"):
                st.session_state[f'carousel_index_{model_data["model_id"]}'] += 1
                st.rerun()

        # Display current image in carousel with controlled sizing
        carousel_container = st.container()
        with carousel_container:
            try:
                # Create a centered container for the main image
                _, col2, _ = st.columns([1, 2, 1])
                with col2:
                    st.image(
                        valid_images[current_carousel_index],
                        width=400,  # Fixed width to prevent stretching
                        caption=f"Portfolio Image {current_carousel_index + 1}"
                    )
            except Exception as e:
                st.error(f"Could not load image: {e}")

        # Thumbnail strip below main image
        st.markdown("---")
        st.markdown("**All Images:**")

        # Display all images in a grid for quick navigation
        images_per_row = 4
        rows = len(valid_images) // images_per_row + (1 if len(valid_images) % images_per_row > 0 else 0)

        for row in range(rows):
            cols = st.columns(images_per_row)
            for col_idx in range(images_per_row):
                img_idx = row * images_per_row + col_idx
                if img_idx < len(valid_images):
                    with cols[col_idx]:
                        try:
                            # Make thumbnail clickable to jump to that image
                            if st.button(f"📷", key=f"thumb_{model_data['model_id']}_{img_idx}", help=f"Jump to image {img_idx + 1}"):
                                st.session_state[f'carousel_index_{model_data["model_id"]}'] = img_idx
                                st.rerun()

                            # Show thumbnail with border if it's the current image
                            border_style = "border: 3px solid #667eea;" if img_idx == current_carousel_index else "border: 1px solid #ddd;"
                            st.markdown(
                                f"""
                                <div style="{border_style} border-radius: 8px; padding: 2px;">
                                    <img src="data:image/jpeg;base64,{get_image_base64(valid_images[img_idx])}"
                                         style="width: 100%; height: 80px; object-fit: cover; border-radius: 6px;"
                                         alt="Thumbnail {img_idx + 1}"/>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        except Exception as e:
                            st.error(f"Could not load thumbnail: {e}")
    else:
        st.info("No local images available for this model.")
        # Show remote thumbnail if available
        if model_data.get('thumbnail'):
            st.image(model_data['thumbnail'], width="stretch", caption="Remote Thumbnail")

    st.markdown("---")

    # Footer Buttons
    button_cols = st.columns([1, 1, 2])

    with button_cols[0]:
        if model_data.get('profile_url'):
            st.link_button("🔗 View APM Profile", model_data['profile_url'])

    with button_cols[1]:
        if st.button("✖️ Close Preview", type="primary"):
            st.session_state.selected_model = None
            st.rerun()

def display_model_grid(filtered_df: pd.DataFrame, max_results: int = 20):
    """Display models in a responsive grid layout."""
    if filtered_df.empty:
        st.info("🔍 No models found for this search. Try adjusting your filters.")
        return

    # Limit results for performance
    display_df = filtered_df.head(max_results)

    # Create grid layout (4 columns)
    cols_per_row = 4
    rows = len(display_df) // cols_per_row + (1 if len(display_df) % cols_per_row > 0 else 0)

    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            model_idx = row * cols_per_row + col_idx
            if model_idx < len(display_df):
                model_data = display_df.iloc[model_idx].to_dict()
                display_model_card(model_data, cols[col_idx])

def main():
    """Main Streamlit application."""

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }

    /* Ensure text is visible with dark text */
    .stMarkdown, .stText, .stCaption, p, div, span {
        color: #262730 !important;
    }

    /* Force dark text for markdown content */
    .stMarkdown p, .stMarkdown div {
        color: #262730 !important;
    }

    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }

    .model-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }

    .model-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        background: #f8f9fa;
    }

    /* Thumbnail image sizing - force consistent dimensions */
    .stImage > img,
    .stImage img,
    img[data-testid="stImage"],
    [data-testid="stImage"] img,
    .stApp img {
        border-radius: 8px !important;
        object-fit: cover !important;
        aspect-ratio: 3/4 !important;
        height: 250px !important;
        width: auto !important;
        max-width: 100% !important;
    }

    /* Container for images to ensure proper sizing */
    .stImage,
    [data-testid="stImage"] {
        height: 250px !important;
        overflow: hidden !important;
        border-radius: 8px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Carousel main image styling */
    .carousel-main-image {
        max-width: 400px !important;
        max-height: 500px !important;
        object-fit: contain !important;
        margin: 0 auto !important;
        display: block !important;
    }

    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        width: 100%;
    }

    /* Container styling for model cards */
    .stContainer > div {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>

    <script>
    // Force image styling on load and resize
    function applyImageStyling() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (img.src && !img.src.includes('placeholder')) {
                img.style.height = '250px';
                img.style.objectFit = 'cover';
                img.style.borderRadius = '8px';
                img.style.width = 'auto';
                img.style.maxWidth = '100%';
            }
        });
    }

    // Apply styling immediately and on DOM changes
    document.addEventListener('DOMContentLoaded', applyImageStyling);
    window.addEventListener('load', applyImageStyling);

    // Use MutationObserver to catch dynamically added images
    const observer = new MutationObserver(applyImageStyling);
    observer.observe(document.body, { childList: true, subtree: true });

    // Apply styling every 100ms for the first 2 seconds to catch late-loading images
    let attempts = 0;
    const interval = setInterval(() => {
        applyImageStyling();
        attempts++;
        if (attempts >= 20) clearInterval(interval);
    }, 100);
    </script>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎭 Elysium Model Catalogue</h1>
        <p>Local AI Demo - Search and filter real model data using AI-assisted queries</p>
    </div>
    """, unsafe_allow_html=True)

    # Create tabs
    tab1, tab2 = st.tabs(["📚 Catalogue", "🏛️ Athena"])

    # Initialize Athena UI
    athena_ui = AthenaUI()

    # Load data
    @st.cache_data
    def load_data():
        return DataLoader.load_and_normalize_models(MODELS_FILE)

    df = load_data()

    if df.empty:
        st.error("No model data available. Please check the data file.")
        return

    # Cache dataframe for Athena
    st.session_state.df_cache = df

    # Initialize session state
    if 'ai_filters' not in st.session_state:
        st.session_state.ai_filters = {}
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = None
    if 'current_model_index' not in st.session_state:
        st.session_state.current_model_index = 0
    if 'hover_model' not in st.session_state:
        st.session_state.hover_model = None

    # Catalogue Tab
    with tab1:
        # Only show filters and search when not in expanded view
        if not st.session_state.selected_model:
            # Sidebar filters
            st.sidebar.header("🔍 Manual Filters")

            # Get unique values for filters
            unique_hair_colors = sorted(df['hair_color'].dropna().unique())
            unique_eye_colors = sorted(df['eye_color'].dropna().unique())
            unique_divisions = sorted(df['division'].dropna().unique())
            min_height, max_height = int(df['height_cm'].min()), int(df['height_cm'].max())

            # Manual filter controls
            selected_hair = st.sidebar.multiselect("Hair Color", unique_hair_colors)
            selected_eyes = st.sidebar.multiselect("Eye Color", unique_eye_colors)
            selected_divisions = st.sidebar.multiselect("Division", unique_divisions)
            height_range = st.sidebar.slider(
                "Height Range (cm)",
                min_height, max_height,
                (min_height, max_height)
            )

            if st.sidebar.button("🔄 Reset Filters"):
                st.session_state.ai_filters = {}
                # Clear manual filters by rerunning with empty session state
                for key in list(st.session_state.keys()):
                    if key.startswith('multiselect') or key.startswith('slider'):
                        del st.session_state[key]
                st.rerun()

            # Main area - AI Query
            st.header("🤖 AI-Powered Search")

            user_query = st.text_area(
                "Enter client brief:",
                placeholder="e.g., 'Looking for blonde models with blue eyes around 175 cm'",
                height=100
            )

            search_col = st.columns([1])[0]

            with search_col:
                if st.button("🔍 Search with AI (Ollama)", type="primary"):
                    if user_query.strip():
                        with st.spinner("🧠 Processing with AI..."):
                            prompt = OllamaClient.create_prompt(user_query)
                            ai_result = OllamaClient.query_ollama(prompt)

                            if ai_result is not None:
                                st.session_state.ai_filters = ai_result
                                st.success("✅ AI query processed successfully!")
                            else:
                                st.error("❌ Failed to process AI query")
                    else:
                        st.warning("⚠️ Please enter a query first")

            # Display AI filters
            if st.session_state.ai_filters:
                st.subheader("🎯 AI-Parsed Filters")
                st.json(st.session_state.ai_filters)

            # Apply filters and display results
            filtered_df = FilterEngine.apply_filters(
                df,
                hair_colors=selected_hair,
                eye_colors=selected_eyes,
                height_range=height_range,
                divisions=selected_divisions,
                ai_filters=st.session_state.ai_filters
            )
        else:
            # When in expanded view, use full dataset
            filtered_df = df

        # Check if a model is selected for expanded view
        if st.session_state.selected_model:
            # Find the selected model data
            selected_model_data = df[df['model_id'] == st.session_state.selected_model]
            if not selected_model_data.empty:
                show_expanded_model_view(selected_model_data.iloc[0].to_dict(), filtered_df)
            else:
                st.error("Selected model not found.")
                st.session_state.selected_model = None
                # Show grid if model not found
                st.subheader(f"📊 Results: Displaying {min(len(filtered_df), 20)} of {len(df)} models")
                display_model_grid(filtered_df)
        else:
            # Display results count and model grid only when not in expanded view
            st.subheader(f"📊 Results: Displaying {min(len(filtered_df), 20)} of {len(df)} models")
            display_model_grid(filtered_df)

    # Athena Tab
    with tab2:
        athena_ui.render_athena_tab(df)

if __name__ == "__main__":
    main()
