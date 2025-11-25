"""
HTTPS Image Utilities for Elysium Model Catalogue
Handles all image operations using HTTPS URLs only.
No local filesystem dependencies.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Tuple
from functools import lru_cache
import requests
from PIL import Image
import io

logger = logging.getLogger(__name__)


class HTTPSImageHandler:
    """Handles all image operations using HTTPS URLs exclusively."""
    
    # Fallback placeholder for failed image loads
    PLACEHOLDER_URL = "https://via.placeholder.com/300x400/cccccc/666666?text=No+Image"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Elysium-Model-Catalogue/1.0'
        })
    
    @staticmethod
    def get_thumbnail_url(model_data: Dict[str, Any]) -> str:
        """
        Get the thumbnail URL for a model.
        
        Args:
            model_data: Model data dictionary
            
        Returns:
            HTTPS URL for thumbnail or placeholder
        """
        # Priority 1: Dedicated thumbnail field
        thumbnail = model_data.get('thumbnail', '')
        if thumbnail and thumbnail.startswith('https://'):
            return thumbnail
        
        # Priority 2: First image from images array
        images = model_data.get('images', [])
        if images and isinstance(images, list):
            first_image = images[0]
            if first_image and first_image.startswith('https://'):
                return first_image
        
        # Priority 3: primary_thumbnail field (for compatibility)
        primary_thumb = model_data.get('primary_thumbnail', '')
        if primary_thumb and primary_thumb.startswith('https://'):
            return primary_thumb
        
        # Fallback: placeholder
        return HTTPSImageHandler.PLACEHOLDER_URL
    
    @staticmethod
    def get_portfolio_urls(model_data: Dict[str, Any]) -> List[str]:
        """
        Get all portfolio image URLs for a model.
        
        Args:
            model_data: Model data dictionary
            
        Returns:
            List of HTTPS URLs for portfolio images
        """
        images = model_data.get('images', [])
        if not images or not isinstance(images, list):
            return []
        
        # Filter to only HTTPS URLs
        portfolio_urls = [
            img for img in images 
            if img and isinstance(img, str) and img.startswith('https://')
        ]
        
        return portfolio_urls
    
    @staticmethod
    def validate_image_url(url: str, timeout: int = 5) -> bool:
        """
        Validate that an image URL is accessible.
        
        Args:
            url: Image URL to validate
            timeout: Request timeout in seconds
            
        Returns:
            True if URL is accessible, False otherwise
        """
        if not url or not url.startswith('https://'):
            return False
        
        try:
            response = requests.head(url, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False
    
    @st.cache_data
    def load_image_from_url(_self, url: str, max_size: Tuple[int, int] = (800, 600)) -> Optional[Image.Image]:
        """
        Load and optionally resize an image from HTTPS URL.
        
        Args:
            url: HTTPS URL of the image
            max_size: Maximum size tuple (width, height)
            
        Returns:
            PIL Image object or None if failed
        """
        if not url or not url.startswith('https://'):
            return None
        
        try:
            response = _self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Load image
            img = Image.open(io.BytesIO(response.content))
            
            # Resize if needed
            if max_size:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            return img
            
        except Exception as e:
            logger.warning(f"Failed to load image from {url}: {e}")
            return None
    
    def render_model_thumbnail(self, model_data: Dict[str, Any], 
                              width: int = 280, 
                              use_column: bool = True) -> None:
        """
        Render a model thumbnail in Streamlit.
        
        Args:
            model_data: Model data dictionary
            width: Image width in pixels
            use_column: Whether to use current column context
        """
        thumbnail_url = self.get_thumbnail_url(model_data)
        model_name = model_data.get('name', 'Unknown Model')
        
        try:
            if use_column:
                st.image(thumbnail_url, width=width, caption="")
            else:
                st.image(thumbnail_url, width=width, caption=model_name)
        except Exception as e:
            logger.warning(f"Failed to display thumbnail for {model_name}: {e}")
            # Show placeholder text
            st.markdown(f"""
            <div style="
                width: {width}px; 
                height: {int(width * 1.33)}px; 
                background: #f0f0f0; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                border: 1px solid #ddd;
                border-radius: 8px;
                color: #666;
                font-size: 14px;
                text-align: center;
            ">
                📷<br>Image Not Available
            </div>
            """, unsafe_allow_html=True)
    
    def render_portfolio_gallery(self, model_data: Dict[str, Any], 
                                images_per_row: int = 3,
                                max_images: int = 12) -> None:
        """
        Render a portfolio gallery for a model.
        
        Args:
            model_data: Model data dictionary
            images_per_row: Number of images per row
            max_images: Maximum number of images to display
        """
        portfolio_urls = self.get_portfolio_urls(model_data)
        
        if not portfolio_urls:
            st.info("No portfolio images available for this model.")
            return
        
        # Limit number of images
        display_urls = portfolio_urls[:max_images]
        
        # Calculate rows needed
        rows = (len(display_urls) + images_per_row - 1) // images_per_row
        
        for row in range(rows):
            cols = st.columns(images_per_row)
            for col_idx in range(images_per_row):
                img_idx = row * images_per_row + col_idx
                if img_idx < len(display_urls):
                    with cols[col_idx]:
                        try:
                            st.image(display_urls[img_idx], use_column_width=True)
                        except Exception as e:
                            logger.warning(f"Failed to display portfolio image {img_idx}: {e}")
                            st.markdown("📷 *Image unavailable*")
    
    def get_image_carousel_data(self, model_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Get carousel data for a model's images.
        
        Args:
            model_data: Model data dictionary
            
        Returns:
            List of image data dictionaries
        """
        portfolio_urls = self.get_portfolio_urls(model_data)
        
        carousel_data = []
        for i, url in enumerate(portfolio_urls):
            carousel_data.append({
                'url': url,
                'caption': f"Portfolio Image {i + 1}",
                'index': i
            })
        
        return carousel_data


# Global instance
https_image_handler = HTTPSImageHandler()
