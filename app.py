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
                            'hair': DataLoader.normalize_attribute(
                                model.get('attributes', {}).get('hair', '')
                            ),
                            'eyes': DataLoader.normalize_attribute(
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
        """Create prompt template for Ollama."""
        return f"""You are a model search assistant.
Given a text client brief, extract structured filters as a valid JSON object.

Only return a JSON object with these keys if mentioned:
haircolor, eyecolor, heightmin, heightmax, division.

Example:
Input: "Looking for blonde models around 175cm with blue eyes"
Output:
{{
  "haircolor": "blonde",
  "eyecolor": "blue",
  "heightmin": 170,
  "heightmax": 180
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

class FilterEngine:
    """Handles filtering logic for models."""
    
    @staticmethod
    def apply_filters(df: pd.DataFrame,
                     hair_colors: Optional[List[str]] = None,
                     eye_colors: Optional[List[str]] = None,
                     height_range: Optional[tuple] = None,
                     ai_filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Apply combined manual and AI filters to the dataset."""
        filtered_df = df.copy()
        
        # Apply manual filters
        if hair_colors:
            filtered_df = filtered_df[
                filtered_df['hair'].str.contains('|'.join(hair_colors), case=False, na=False)
            ]
        
        if eye_colors:
            filtered_df = filtered_df[
                filtered_df['eyes'].str.contains('|'.join(eye_colors), case=False, na=False)
            ]
        
        if height_range:
            min_height, max_height = height_range
            filtered_df = filtered_df[
                (filtered_df['height_cm'] >= min_height) & 
                (filtered_df['height_cm'] <= max_height)
            ]
        
        # Apply AI filters
        if ai_filters:
            if 'haircolor' in ai_filters:
                filtered_df = filtered_df[
                    filtered_df['hair'].str.contains(ai_filters['haircolor'], case=False, na=False)
                ]
            
            if 'eyecolor' in ai_filters:
                filtered_df = filtered_df[
                    filtered_df['eyes'].str.contains(ai_filters['eyecolor'], case=False, na=False)
                ]
            
            if 'heightmin' in ai_filters:
                filtered_df = filtered_df[filtered_df['height_cm'] >= ai_filters['heightmin']]
            
            if 'heightmax' in ai_filters:
                filtered_df = filtered_df[filtered_df['height_cm'] <= ai_filters['heightmax']]
            
            if 'division' in ai_filters:
                filtered_df = filtered_df[
                    filtered_df['division'].str.contains(ai_filters['division'], case=False, na=False)
                ]
        
        return filtered_df

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
                st.markdown(f"👁️ {model_data['eyes'].title()}")
                st.markdown(f"📏 {model_data['height_cm']} cm")
            with attr_col2:
                st.markdown(f"💇 {model_data['hair'].title()}")

            # View Portfolio button
            if st.button(
                "👁️ View Portfolio",
                key=f"view_{model_data['model_id']}",
                type="secondary"
            ):
                st.session_state.selected_model = model_data['model_id']
                st.rerun()

            st.markdown("---")

def show_expanded_model_view(model_data: Dict[str, Any]):
    """Display expanded model view with full details and image gallery."""

    # Header Section
    st.markdown(f"### {model_data['name']} ({model_data['division'].upper()})")

    # Back button
    if st.button("← Back to Catalogue", type="secondary"):
        st.session_state.selected_model = None
        st.rerun()

    st.markdown("---")

    # Metadata Section
    st.subheader("📋 Model Details")

    # Create a neat layout for attributes
    detail_cols = st.columns(3)

    with detail_cols[0]:
        st.markdown(f"**Height:** {model_data['height_cm']} cm")
        st.markdown(f"**Hair:** {model_data['hair'].title()}")
        st.markdown(f"**Eyes:** {model_data['eyes'].title()}")

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

    # Image Gallery Section
    st.subheader("📸 Portfolio Gallery")

    valid_images = ImageHandler.get_valid_images(model_data)

    if valid_images:
        # Display images in rows of 4
        images_per_row = 4
        rows = len(valid_images) // images_per_row + (1 if len(valid_images) % images_per_row > 0 else 0)

        for row in range(rows):
            cols = st.columns(images_per_row)
            for col_idx in range(images_per_row):
                img_idx = row * images_per_row + col_idx
                if img_idx < len(valid_images):
                    with cols[col_idx]:
                        try:
                            st.image(
                                valid_images[img_idx],
                                width="stretch",
                                caption=f"Image {img_idx + 1}"
                            )
                        except Exception as e:
                            st.error(f"Could not load image: {e}")
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

    # Load data
    @st.cache_data
    def load_data():
        return DataLoader.load_and_normalize_models(MODELS_FILE)

    df = load_data()

    if df.empty:
        st.error("No model data available. Please check the data file.")
        return

    # Initialize session state
    if 'ai_filters' not in st.session_state:
        st.session_state.ai_filters = {}
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = None

    # Only show filters and search when not in expanded view
    if not st.session_state.selected_model:
        # Sidebar filters
        st.sidebar.header("🔍 Manual Filters")

        # Get unique values for filters
        unique_hair_colors = sorted(df['hair'].dropna().unique())
        unique_eye_colors = sorted(df['eyes'].dropna().unique())
        min_height, max_height = int(df['height_cm'].min()), int(df['height_cm'].max())

        # Manual filter controls
        selected_hair = st.sidebar.multiselect("Hair Color", unique_hair_colors)
        selected_eyes = st.sidebar.multiselect("Eye Color", unique_eye_colors)
        height_range = st.sidebar.slider(
            "Height Range (cm)",
            min_height, max_height,
            (min_height, max_height)
        )

        if st.sidebar.button("🔄 Reset Filters"):
            st.session_state.ai_filters = {}
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
            show_expanded_model_view(selected_model_data.iloc[0].to_dict())
        else:
            st.error("Selected model not found.")
            st.session_state.selected_model = None
    else:
        # Display results count
        st.subheader(f"📊 Results: Displaying {min(len(filtered_df), 20)} of {len(df)} models")

        # Display model grid
        display_model_grid(filtered_df)

if __name__ == "__main__":
    main()
