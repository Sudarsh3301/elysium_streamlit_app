"""
Elysium Model Catalogue - Enhanced Streamlit App
A polished Streamlit web app with unified navigation, loading experience,
error handling, and session continuity across all tabs.
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

# Import enhanced components
from session_manager import SessionManager
from ui_components import (
    LoadingComponents, NotificationComponents, ErrorComponents,
    HeaderComponents, FooterComponents, NavigationComponents
)
from theme_manager import ThemeManager
from athena_ui import AthenaUI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Elysium Model Catalogue v0.4",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import path configuration
from path_config import paths, get_data_file, get_image_path

# Validate data files on startup
data_status = paths.validate_data_files()
missing_files = [f for f, status in data_status.items() if not status['exists']]
if missing_files:
    st.error(f"Missing data files: {', '.join(missing_files)}")
    st.info("Please ensure all CSV files are present in the 'out/' directory.")
    st.stop()

# Constants
MODELS_FILE = str(get_data_file("models_normalized.csv"))
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
        """Load models from CSV and normalize data."""
        try:
            # Load CSV file
            df = pd.read_csv(file_path)

            # Ensure required columns exist
            required_columns = ['name', 'division', 'height_cm', 'hair_color', 'eye_color']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                st.error(f"Missing required columns in CSV: {missing_columns}")
                return pd.DataFrame()

            # Normalize data
            df['hair_color'] = df['hair_color'].fillna('').astype(str).str.lower().str.strip()
            df['eye_color'] = df['eye_color'].fillna('').astype(str).str.lower().str.strip()
            df['name'] = df['name'].fillna('').astype(str).str.strip()
            df['division'] = df['division'].fillna('').astype(str).str.strip()

            # Ensure height_cm is numeric
            df['height_cm'] = pd.to_numeric(df['height_cm'], errors='coerce').fillna(0).astype(int)

            # Add missing columns if they don't exist
            if 'model_id' not in df.columns:
                df['model_id'] = df.index.astype(str)
            if 'profile_url' not in df.columns:
                df['profile_url'] = ''
            if 'thumbnail' not in df.columns:
                df['thumbnail'] = df.get('images', '')
            if 'images' not in df.columns:
                df['images'] = df.get('thumbnail', '')

            logger.info(f"Loaded {len(df)} models from {file_path}")
            return df

        except FileNotFoundError:
            st.error(f"Models file not found: {file_path}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error loading models: {e}")
            return pd.DataFrame()

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
        resolved_path = get_image_path(image_path)
        if resolved_path and resolved_path.exists():
            return str(resolved_path)

        # Return original path if not found locally
        return image_path

    @staticmethod
    def parse_images_list(images_str) -> List[str]:
        """Parse the images column from CSV (string representation of list)."""
        if not images_str or pd.isna(images_str):
            return []

        try:
            # Handle string representation of list
            if isinstance(images_str, str):
                if images_str.startswith('[') and images_str.endswith(']'):
                    import ast
                    return ast.literal_eval(images_str)
                else:
                    # Single image path
                    return [images_str]
            elif isinstance(images_str, list):
                return images_str
            else:
                return []
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Could not parse images column: {images_str}, error: {e}")
            return []

    @staticmethod
    def get_thumbnail_path(model_data: Dict[str, Any]) -> str:
        """Get the best available thumbnail path for a model."""
        # Parse the images column properly
        images_raw = model_data.get('images', [])
        images = ImageHandler.parse_images_list(images_raw)

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

        # Final fallback to a simple text placeholder
        return None  # Return None to indicate no image found

    @staticmethod
    def get_valid_images(model_data: Dict[str, Any]) -> List[str]:
        """Get list of valid local image paths for a model."""
        valid_images = []
        # Parse the images column properly
        images_raw = model_data.get('images', [])
        images = ImageHandler.parse_images_list(images_raw)

        for img_path in images:
            local_path = ImageHandler.get_local_image_path(img_path)
            if os.path.exists(local_path):
                valid_images.append(local_path)

        return valid_images

def display_enhanced_model_card(model_data: Dict[str, Any], col):
    """Display an enhanced model card with hover interactions and quick actions."""
    with col:
        # Create card container with hover styling
        card_id = f"card_{model_data['model_id']}"

        # Enhanced card with hover effects
        st.markdown(f"""
        <div id="{card_id}" style="
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            background: white;
            transition: all 0.3s ease;
            cursor: pointer;
        " onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 25px rgba(0,0,0,0.15)'; this.style.borderColor='#667eea';"
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'; this.style.borderColor='#e0e0e0';">
        """, unsafe_allow_html=True)

        # Model image using local path with controlled sizing
        thumbnail_path = ImageHandler.get_thumbnail_path(model_data)

        # Display image or placeholder
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                # Use PIL to load and display the image
                from PIL import Image
                img = Image.open(thumbnail_path)
                st.image(img, width=280, caption="")
            except Exception as e:
                # If PIL fails, show a styled placeholder
                st.markdown(
                    f"""
                    <div style="
                        width: 280px;
                        height: 220px;
                        background: linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%);
                        border: 2px solid #ddd;
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #666;
                        font-size: 16px;
                        font-weight: bold;
                        margin-bottom: 10px;
                    ">
                        📷 {model_data['name'][:15]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            # Show a styled placeholder when no image is found
            st.markdown(
                f"""
                <div style="
                    width: 280px;
                    height: 220px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #6c757d;
                    font-size: 16px;
                    font-weight: bold;
                    margin-bottom: 10px;
                ">
                    📷 {model_data['name'][:15]}
                </div>
                """,
                unsafe_allow_html=True
            )

        # Model details
        st.markdown(f"**{model_data['name']}**")
        st.markdown(f"*Division: {model_data['division'].upper()}*")

        # Hover overlay with key attributes
        st.markdown(f"""
        <div style="
            display: flex;
            flex-wrap: wrap;
            gap: 0.3rem;
            margin: 0.5rem 0;
        ">
            <span style="background: #e3f2fd; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">
                📏 {model_data['height_cm']}cm
            </span>
            <span style="background: #f3e5f5; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">
                � {model_data['hair_color'].title()}
            </span>
            <span style="background: #e8f5e8; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">
                �️ {model_data['eye_color'].title()}
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "�️ Quick View",
                key=f"quick_{model_data['model_id']}",
                type="secondary",
                use_container_width=True
            ):
                st.session_state.quick_view_model = model_data['model_id']
                st.rerun()

        with col2:
            if st.button(
                "� Analytics",
                key=f"analytics_{model_data['model_id']}",
                type="secondary",
                use_container_width=True
            ):
                # Set shared model context for Apollo
                SessionManager.set_shared_model_context(model_data)
                SessionManager.add_integration_message(
                    f"Viewing analytics for {model_data['name']}",
                    "success"
                )
                st.rerun()

        # Close card div
        st.markdown("</div>", unsafe_allow_html=True)

def render_quick_view_modal(df: pd.DataFrame):
    """Render quick view modal for model details."""
    model_id = st.session_state.get('quick_view_model')
    if not model_id:
        return

    # Find model data
    model_data = df[df['model_id'] == model_id]
    if model_data.empty:
        st.error("Model not found")
        st.session_state.quick_view_model = None
        return

    model_info = model_data.iloc[0].to_dict()

    # Modal overlay
    st.markdown("""
    <div style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    ">
    </div>
    """, unsafe_allow_html=True)

    # Modal content
    with st.container():
        st.markdown("### 👁️ Quick View")

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            # Model image
            thumbnail_path = ImageHandler.get_thumbnail_path(model_info)
            if thumbnail_path and os.path.exists(thumbnail_path):
                st.image(thumbnail_path, width=300)
            else:
                st.markdown(f"""
                <div style="
                    width: 300px;
                    height: 400px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border: 2px solid #dee2e6;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #6c757d;
                    font-size: 18px;
                    font-weight: bold;
                    margin: 0 auto;
                ">
                    📷 {model_info['name']}
                </div>
                """, unsafe_allow_html=True)

            # Model details
            st.markdown(f"## {model_info['name']}")
            st.markdown(f"**Division:** {model_info['division'].upper()}")

            # Attributes grid
            attr_col1, attr_col2 = st.columns(2)
            with attr_col1:
                st.markdown(f"**Height:** {model_info['height_cm']} cm")
                st.markdown(f"**Hair:** {model_info['hair_color'].title()}")
            with attr_col2:
                st.markdown(f"**Eyes:** {model_info['eye_color'].title()}")

            # Action buttons
            button_col1, button_col2, button_col3 = st.columns(3)

            with button_col1:
                if st.button("📊 View Analytics", key="modal_analytics", use_container_width=True):
                    SessionManager.set_shared_model_context(model_info)
                    SessionManager.add_integration_message(
                        f"Viewing analytics for {model_info['name']}",
                        "success"
                    )
                    st.session_state.quick_view_model = None
                    st.rerun()

            with button_col2:
                if st.button("🎯 Send to Athena", key="modal_athena", use_container_width=True):
                    SessionManager.transfer_model_to_athena(model_info, "Catalogue")
                    st.session_state.quick_view_model = None
                    st.rerun()

            with button_col3:
                if st.button("❌ Close", key="modal_close", use_container_width=True):
                    st.session_state.quick_view_model = None
                    st.rerun()

def render_ai_search_summary(ai_filters: dict, result_count: int):
    """Render AI search summary with parsed filters."""
    st.markdown("#### 🤖 AI Search Summary")

    summary_parts = []
    if ai_filters.get('hair_color'):
        summary_parts.append(f"**Hair:** {ai_filters['hair_color']}")
    if ai_filters.get('eye_color'):
        summary_parts.append(f"**Eyes:** {ai_filters['eye_color']}")
    if ai_filters.get('height_range'):
        height_range = ai_filters['height_range']
        summary_parts.append(f"**Height:** {height_range[0]}-{height_range[1]}cm")
    if ai_filters.get('division'):
        summary_parts.append(f"**Division:** {ai_filters['division'].upper()}")

    if summary_parts:
        summary_text = " • ".join(summary_parts)
        st.markdown(f"""
        <div style="
            background: rgba(102, 126, 234, 0.1);
            border-left: 4px solid #667eea;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
        ">
            <strong>🎯 Parsed from your search:</strong> {summary_text}
            <br><small>Found {result_count} models matching these criteria</small>
        </div>
        """, unsafe_allow_html=True)

def render_enhanced_empty_state(ai_filters: dict, full_df):
    """Render enhanced empty state with helpful suggestions."""
    st.markdown("""
    <div style="
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        margin: 2rem 0;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
        <h3 style="color: #495057; margin-bottom: 1rem;">No Models Found</h3>
        <p style="color: #6c757d; margin-bottom: 2rem;">
            Don't worry! Let's help you find the perfect models for your campaign.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Helpful suggestions
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 💡 Try This")
        st.markdown("""
        - Broaden your height range
        - Try different hair/eye colors
        - Use more general terms
        - Check all divisions
        """)

    with col2:
        st.markdown("#### 🎯 Quick Filters")
        # Show popular combinations
        popular_combos = [
            {"hair": "blonde", "eyes": "blue", "count": len(full_df[(full_df['hair_color'].str.contains('blonde', case=False, na=False)) & (full_df['eye_color'].str.contains('blue', case=False, na=False))])},
            {"hair": "brown", "eyes": "brown", "count": len(full_df[(full_df['hair_color'].str.contains('brown', case=False, na=False)) & (full_df['eye_color'].str.contains('brown', case=False, na=False))])},
            {"hair": "black", "eyes": "brown", "count": len(full_df[(full_df['hair_color'].str.contains('black', case=False, na=False)) & (full_df['eye_color'].str.contains('brown', case=False, na=False))])}
        ]

        for combo in popular_combos:
            if combo['count'] > 0:
                if st.button(f"{combo['hair'].title()} hair, {combo['eyes']} eyes ({combo['count']} models)", key=f"combo_{combo['hair']}_{combo['eyes']}"):
                    st.session_state.ai_filters = {
                        'hair_color': combo['hair'],
                        'eye_color': combo['eyes']
                    }
                    st.rerun()

    with col3:
        st.markdown("#### 🚀 Next Steps")
        st.markdown("""
        - **Reset filters** to see all models
        - **Try natural language** search
        - **Browse by division** (IMA/DEV)
        - **Contact us** for custom searches
        """)

        if st.button("🔄 Reset All Filters", type="primary", use_container_width=True):
            st.session_state.ai_filters = {}
            if 'nl_search_query' in st.session_state:
                st.session_state.nl_search_query = ""
            SessionManager.add_notification("All filters cleared! Showing complete roster.", "success")
            st.rerun()

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
                    current_image_path = valid_images[current_carousel_index]
                    if os.path.exists(current_image_path):
                        try:
                            from PIL import Image
                            img = Image.open(current_image_path)
                            st.image(img, width=400, caption=f"Portfolio Image {current_carousel_index + 1}")
                        except Exception:
                            st.markdown(
                                f"""
                                <div style="
                                    width: 400px;
                                    height: 300px;
                                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                                    border: 2px solid #dee2e6;
                                    border-radius: 8px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    color: #6c757d;
                                    font-size: 18px;
                                    font-weight: bold;
                                    margin: 0 auto;
                                ">
                                    📷 Portfolio Image {current_carousel_index + 1}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            f"""
                            <div style="
                                width: 400px;
                                height: 300px;
                                background: linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%);
                                border: 2px solid #ddd;
                                border-radius: 8px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                color: #666;
                                font-size: 18px;
                                font-weight: bold;
                                margin: 0 auto;
                            ">
                                📷 Image Not Found
                            </div>
                            """,
                            unsafe_allow_html=True
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
                            thumb_path = valid_images[img_idx]
                            if os.path.exists(thumb_path):
                                try:
                                    from PIL import Image
                                    img = Image.open(thumb_path)
                                    # Resize for thumbnail display
                                    img.thumbnail((100, 80))
                                    st.image(img, caption=f"Thumbnail {img_idx + 1}")
                                except Exception:
                                    st.markdown(
                                        f"""
                                        <div style="
                                            width: 100px;
                                            height: 80px;
                                            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                                            border: 1px solid #dee2e6;
                                            border-radius: 6px;
                                            display: flex;
                                            align-items: center;
                                            justify-content: center;
                                            color: #6c757d;
                                            font-size: 12px;
                                            font-weight: bold;
                                        ">
                                            📷 {img_idx + 1}
                                        </div>
                                        """,
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.markdown(
                                    f"""
                                    <div style="
                                        width: 100px;
                                        height: 80px;
                                        background: linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%);
                                        border: 1px solid #ddd;
                                        border-radius: 6px;
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        color: #666;
                                        font-size: 12px;
                                        font-weight: bold;
                                    ">
                                        📷 {img_idx + 1}
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
                display_enhanced_model_card(model_data, cols[col_idx])

def main():
    """Enhanced main Streamlit application with unified navigation and theming."""

    try:
        # Initialize session state first
        SessionManager.initialize_session()

        # Apply global theme
        ThemeManager.apply_global_theme()

        # Show global header - TESTING SIMPLE VERSION
        HeaderComponents.show_global_header()

        # Show notifications
        NotificationComponents.show_notifications()

        # Show sidebar navigation
        NavigationComponents.show_sidebar_navigation()

        # Show breadcrumbs
        NavigationComponents.show_breadcrumbs()

        # Get current page from session
        current_page = SessionManager.get_page()

        # Load data with loading indicator
        SessionManager.set_loading(True, "Loading model data...")

        @st.cache_data
        def load_data():
            return DataLoader.load_and_normalize_models(MODELS_FILE)

        try:
            df = load_data()
            if df.empty:
                ErrorComponents.show_data_error()
                return

            # Cache dataframe in session
            st.session_state.df_cache = df
            st.session_state.data_loaded = True
            from datetime import datetime
            st.session_state.data_load_time = datetime.now()

        except Exception as e:
            SessionManager.log_error(e, "Data loading")
            ErrorComponents.show_data_error()
            return
        finally:
            SessionManager.set_loading(False)

        # Route to appropriate page based on navigation
        if current_page == "Catalogue":
            render_catalogue_page(df)
        elif current_page == "Athena":
            render_athena_page(df)
        elif current_page == "Apollo":
            render_apollo_page()
        else:
            # Default to catalogue
            SessionManager.set_page("Catalogue")
            render_catalogue_page(df)

        # Show global footer and status bar
        FooterComponents.show_global_footer()
        FooterComponents.show_status_bar()

    except Exception as e:
        SessionManager.log_error(e, "Main application")
        ErrorComponents.show_error_card(
            "Application Error",
            f"An unexpected error occurred: {str(e)}",
            [
                "Try refreshing the page",
                "Reset the session using the sidebar",
                "Check the browser console for more details"
            ]
        )

def render_catalogue_page(df: pd.DataFrame):
    """Render the enhanced Catalogue page with hybrid search and interactive features."""
    try:
        st.title("🎭 Elysium Model Catalogue")
        st.markdown("*Discover and explore our diverse talent roster*")

        # Show integration messages
        NotificationComponents.show_integration_messages()

        # Handle quick view modal
        if st.session_state.get('quick_view_model'):
            render_quick_view_modal(df)

        # Only show filters and search when not in expanded view
        if not st.session_state.selected_model:
            # Enhanced search section
            st.markdown("### 🔍 Hybrid Search & Discovery")

            # Search mode tabs
            search_tab1, search_tab2 = st.tabs(["🤖 Natural Language", "🔧 Structured Filters"])

            with search_tab1:
                # Natural language search
                col1, col2 = st.columns([3, 1])
                with col1:
                    user_query = st.text_area(
                        "Describe what you're looking for:",
                        placeholder="e.g., 'tall blonde models for fashion shoot' or 'brunette with green eyes for commercial'",
                        height=80,
                        key="nl_search_query"
                    )

                with col2:
                    st.markdown("#### 💡 Search Tips")
                    st.markdown("""
                    - Use natural language
                    - Mention height, hair, eyes
                    - Specify campaign type
                    - Include style preferences
                    """)

                if st.button("🔍 Search with AI (Ollama)", type="primary", use_container_width=True):
                    if user_query.strip():
                        SessionManager.set_loading(True, "Processing AI query...")
                        try:
                            prompt = OllamaClient.create_prompt(user_query)
                            ai_result = OllamaClient.query_ollama(prompt)

                            if ai_result is not None:
                                st.session_state.ai_filters = ai_result
                                SessionManager.add_notification("AI query processed successfully!", "success")
                            else:
                                SessionManager.add_notification("Failed to process AI query", "error")
                        except Exception as e:
                            SessionManager.log_error(e, "AI query processing")
                            ErrorComponents.show_ai_error()
                        finally:
                            SessionManager.set_loading(False)
                    else:
                        SessionManager.add_notification("Please enter a query first", "warning")

            with search_tab2:
                # Sidebar filters section
                with st.sidebar:
                    st.markdown("### 🔍 Manual Filters")

                    # Get unique values for filters
                    unique_hair_colors = sorted(df['hair_color'].dropna().unique())
                    unique_eye_colors = sorted(df['eye_color'].dropna().unique())
                    unique_divisions = sorted(df['division'].dropna().unique())
                    min_height, max_height = int(df['height_cm'].min()), int(df['height_cm'].max())

                    # Manual filter controls
                    selected_hair = st.multiselect("Hair Color", unique_hair_colors)
                    selected_eyes = st.multiselect("Eye Color", unique_eye_colors)
                    selected_divisions = st.multiselect("Division", unique_divisions)
                    height_range = st.slider(
                        "Height Range (cm)",
                        min_height, max_height,
                        (min_height, max_height)
                    )

                    if st.button("🔄 Reset All Filters", use_container_width=True):
                        st.session_state.ai_filters = {}
                        # Clear natural language search
                        if 'nl_search_query' in st.session_state:
                            st.session_state.nl_search_query = ""
                        SessionManager.add_notification("All filters reset successfully", "success")
                        st.rerun()

                # Structured filter display in main area
                st.markdown("#### 🔧 Quick Filters")
                filter_col1, filter_col2, filter_col3 = st.columns(3)

                with filter_col1:
                    quick_hair = st.selectbox("Hair Color", ["All"] + unique_hair_colors, key="quick_hair")

                with filter_col2:
                    quick_eyes = st.selectbox("Eye Color", ["All"] + unique_eye_colors, key="quick_eyes")

                with filter_col3:
                    quick_division = st.selectbox("Division", ["All"] + unique_divisions, key="quick_division")

            # Display AI filters
            if st.session_state.ai_filters:
                st.markdown("### 🎯 AI-Parsed Filters")
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
                ErrorComponents.show_error_card("Model Not Found", "The selected model could not be found.")
                st.session_state.selected_model = None
                st.rerun()
        else:
            # Enhanced results display with comprehensive feedback
            if not filtered_df.empty:
                # Success state with results
                result_count = len(filtered_df)
                total_count = len(df)

                if result_count == total_count:
                    st.markdown(f"### 🎭 All {total_count} Models")
                    st.info("💡 Showing complete roster. Use filters above to narrow your search!")
                else:
                    st.markdown(f"### 🎯 Found {result_count} of {total_count} Models")

                    # Show search effectiveness
                    effectiveness = (result_count / total_count) * 100
                    if effectiveness > 80:
                        st.success(f"🎯 Great match! Found {effectiveness:.0f}% of our roster.")
                    elif effectiveness > 50:
                        st.info(f"📊 Good results! Found {effectiveness:.0f}% of our roster.")
                    else:
                        st.warning(f"🔍 Narrow search! Found {effectiveness:.0f}% of our roster. Consider broadening filters.")

                # Show AI filter summary if used
                if st.session_state.ai_filters:
                    render_ai_search_summary(st.session_state.ai_filters, result_count)

                display_model_grid(filtered_df)

                # Pagination and next steps
                if result_count > 12:
                    st.info(f"📄 Showing all {result_count} results. Use quick actions on model cards for next steps!")

            else:
                # Enhanced empty state with helpful suggestions
                render_enhanced_empty_state(st.session_state.ai_filters, df)

    except Exception as e:
        SessionManager.log_error(e, "Catalogue page rendering")
        ErrorComponents.show_error_card("Page Error", f"Error rendering catalogue: {str(e)}")

def render_athena_page(df: pd.DataFrame):
    """Render the Athena page with enhanced UI."""
    try:
        # Initialize Athena UI
        athena_ui = AthenaUI()
        athena_ui.render_athena_tab(df)
    except Exception as e:
        SessionManager.log_error(e, "Athena page rendering")
        ErrorComponents.show_error_card("Athena Error", f"Error loading Athena: {str(e)}")

def render_apollo_page():
    """Render the Apollo page with enhanced UI."""
    try:
        # Apply Apollo-specific theme
        ThemeManager.apply_apollo_theme()

        # Import Apollo module
        from apollo import main as apollo_main
        apollo_main()
    except ImportError as e:
        SessionManager.log_error(e, "Apollo import")
        ErrorComponents.show_error_card(
            "Apollo Dashboard Unavailable",
            "Failed to load Apollo dashboard module.",
            ["Ensure apollo.py is in the pages/ directory", "Check file permissions"]
        )
    except Exception as e:
        SessionManager.log_error(e, "Apollo page rendering")
        ErrorComponents.show_error_card(
            "Apollo Dashboard Error",
            f"Error loading Apollo dashboard: {str(e)}",
            ["Check that all required data files are available in the out/ directory"]
        )

if __name__ == "__main__":
    main()
