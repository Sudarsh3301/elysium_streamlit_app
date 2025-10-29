"""
Apollo Image Utilities
Handles thumbnail extraction, caching, and image processing for the Apollo dashboard.
"""

import os
import ast
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from functools import lru_cache
import hashlib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ApolloImageHandler:
    """Handles image processing and caching for Apollo dashboard."""
    
    # Placeholder image as base64 (1x1 transparent pixel)
    PLACEHOLDER_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    def __init__(self):
        self.thumbnail_cache = {}
        
    @staticmethod
    def parse_images_column(images_str: str) -> List[str]:
        """Parse the images column from CSV (string representation of list)."""
        if not images_str or pd.isna(images_str):
            return []
        
        try:
            # Handle string representation of list
            if isinstance(images_str, str):
                if images_str.startswith('[') and images_str.endswith(']'):
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
    def get_primary_thumbnail(model_data: Dict[str, Any]) -> str:
        """
        Extract primary thumbnail using the priority order:
        1. images[0] if present and valid
        2. thumbnail field if present
        3. generic placeholder image
        """
        # Parse images column
        images = ApolloImageHandler.parse_images_column(model_data.get('images', ''))
        
        # Priority 1: First image from images array
        if images:
            first_image = images[0]
            local_path = ApolloImageHandler.get_local_image_path(first_image)
            if os.path.exists(local_path):
                return local_path
            # If local doesn't exist, try the path as-is (might be remote URL)
            return first_image
        
        # Priority 2: Thumbnail field
        if model_data.get('thumbnail'):
            thumbnail_url = model_data['thumbnail']
            # Check if it's a local path that exists
            if not thumbnail_url.startswith('http'):
                local_path = ApolloImageHandler.get_local_image_path(thumbnail_url)
                if os.path.exists(local_path):
                    return local_path
            return thumbnail_url
        
        # Priority 3: Placeholder
        return "https://via.placeholder.com/150x200/cccccc/666666?text=No+Image"
    
    @staticmethod
    def get_local_image_path(image_path: str) -> str:
        """Convert relative image path to absolute local path."""
        if os.path.isabs(image_path):
            return image_path

        # Clean the image path
        clean_path = image_path.lstrip('/')

        # Try different base paths in order of preference
        base_paths = [
            "../elysium_kb",  # From streamlit app directory
            "elysium_kb",     # From repo root
            "../model-dataset",  # Alternative location
            "model-dataset",     # Alternative from root
            ".",              # Current directory
            ".."              # Parent directory
        ]

        for base_path in base_paths:
            full_path = os.path.join(base_path, clean_path)
            if os.path.exists(full_path):
                return full_path

        # Return original path if not found locally
        return image_path
    
    def get_image_path(self, image_path: str) -> str:
        """Get the resolved local image path or return a placeholder."""
        if not image_path:
            return None

        # Handle remote URLs - return as-is
        if image_path.startswith('http'):
            return image_path

        # Resolve local path
        resolved_path = self.get_local_image_path(image_path)

        # Check if file exists
        if os.path.exists(resolved_path):
            return resolved_path
        else:
            logger.warning(f"Image not found: {image_path} -> {resolved_path}")
            return None

    
    def render_circular_thumbnail(self, image_path: str, size: int = 32,
                                 alt_text: str = "Model", css_class: str = "",
                                 tooltip_data: dict = None) -> str:
        """Render a circular thumbnail with specified size and optional tooltip."""
        # Get resolved image path
        resolved_path = self.get_image_path(image_path)

        # Use placeholder if image not found
        if not resolved_path or not os.path.exists(resolved_path):
            image_src = f"data:image/png;base64,{self.PLACEHOLDER_IMAGE}"
        else:
            # For now, use a simple file:// URL (this may need adjustment based on Streamlit setup)
            image_src = f"data:image/png;base64,{self.PLACEHOLDER_IMAGE}"  # Simplified for now

        # Create tooltip content if data provided
        tooltip_content = ""
        if tooltip_data:
            last_booking = tooltip_data.get('last_booking_date', 'N/A')
            division = tooltip_data.get('division', 'N/A').upper()
            revenue = tooltip_data.get('revenue_total_usd', 0)
            rebook_rate = tooltip_data.get('rebook_rate_pct', 0)
            last_client = tooltip_data.get('last_client', 'N/A')

            tooltip_content = f"""
            title="Model: {alt_text}
Division: {division}
Last Booking: {last_booking}
Total Revenue: ${revenue:,.0f}
Rebook Rate: {rebook_rate:.1f}%
Last Client: {last_client}"
            """

        return f"""
        <img src="{image_src}"
             alt="{alt_text}"
             class="apollo-thumbnail {css_class}"
             {tooltip_content}
             style="width: {size}px; height: {size}px; border-radius: 50%;
                    object-fit: cover; border: 2px solid rgba(46, 240, 255, 0.3);
                    cursor: pointer; transition: all 0.3s ease;"
             onmouseover="this.style.borderColor='#2EF0FF'; this.style.transform='scale(1.1)'"
             onmouseout="this.style.borderColor='rgba(46, 240, 255, 0.3)'; this.style.transform='scale(1)'"
        />
        """
    
    def render_thumbnail_strip(self, thumbnails: List[str], size: int = 32,
                              max_count: int = 3, lazy_load: bool = True) -> str:
        """Render a horizontal strip of thumbnails with optional lazy loading."""
        if not thumbnails:
            return ""

        # For performance, limit initial rendering to first 1 thumbnail if lazy loading enabled
        initial_count = min(1, max_count) if lazy_load else max_count
        display_thumbnails = thumbnails[:initial_count]

        thumbnail_html = []
        for i, thumb_path in enumerate(display_thumbnails):
            thumbnail_html.append(
                self.render_circular_thumbnail(
                    thumb_path, size, f"Model {i+1}", f"thumb-{i}"
                )
            )

        # Add "more" indicator if there are additional thumbnails
        more_indicator = ""
        remaining_count = len(thumbnails) - initial_count
        if remaining_count > 0:
            more_indicator = f"""
            <div style="width: {size}px; height: {size}px; border-radius: 50%;
                        background: rgba(46, 240, 255, 0.2); border: 2px solid rgba(46, 240, 255, 0.3);
                        display: flex; align-items: center; justify-content: center;
                        font-size: {size//3}px; color: #2EF0FF; font-weight: bold; cursor: pointer;"
                        title="Click to load {remaining_count} more thumbnails">
                +{remaining_count}
            </div>
            """

        return f"""
        <div style="display: flex; gap: 8px; align-items: center;">
            {' '.join(thumbnail_html)}
            {more_indicator}
        </div>
        """

    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 1),
            "cache_size": len(self.image_cache),
            "max_cache_size": self._max_cache_size
        }

class ApolloModelCache:
    """Caches model data with thumbnails for performance."""
    
    def __init__(self):
        self.models_with_thumbnails = {}
        self.last_update = None
        
    @st.cache_data
    def get_models_with_thumbnails(_self, models_df: pd.DataFrame) -> pd.DataFrame:
        """Add primary_thumbnail column to models dataframe with caching."""
        if models_df.empty:
            return models_df
        
        # Create a copy to avoid modifying original
        enhanced_df = models_df.copy()
        
        # Add primary_thumbnail column
        enhanced_df['primary_thumbnail'] = enhanced_df.apply(
            lambda row: ApolloImageHandler.get_primary_thumbnail(row.to_dict()), 
            axis=1
        )
        
        return enhanced_df
    
    def get_model_thumbnails_for_client(self, models_df: pd.DataFrame, 
                                       bookings_df: pd.DataFrame, 
                                       client_id: str, limit: int = 3) -> List[str]:
        """Get thumbnails for top models associated with a client."""
        if bookings_df.empty or models_df.empty:
            return []
        
        # Get models booked by this client, sorted by revenue
        client_bookings = bookings_df[bookings_df['client_id'] == client_id]
        if client_bookings.empty:
            return []
        
        # Get top models by revenue for this client
        model_revenue = client_bookings.groupby('model_id')['revenue_usd'].sum().reset_index()
        model_revenue = model_revenue.sort_values('revenue_usd', ascending=False).head(limit)
        
        # Get thumbnails for these models
        thumbnails = []
        for _, row in model_revenue.iterrows():
            model_data = models_df[models_df['model_id'] == row['model_id']]
            if not model_data.empty:
                thumbnail = ApolloImageHandler.get_primary_thumbnail(model_data.iloc[0].to_dict())
                thumbnails.append(thumbnail)
        
        return thumbnails
    
    def get_model_thumbnails_for_height_bucket(self, models_df: pd.DataFrame, 
                                              min_height: float, max_height: float, 
                                              limit: int = 3) -> List[Tuple[str, str]]:
        """Get thumbnails and names for models in a height bucket."""
        if models_df.empty or 'height_cm' not in models_df.columns:
            return []
        
        # Filter models in height range
        height_models = models_df[
            (models_df['height_cm'] >= min_height) & 
            (models_df['height_cm'] < max_height)
        ]
        
        if height_models.empty:
            return []
        
        # Sample random models from this bucket
        sample_models = height_models.sample(min(limit, len(height_models)))
        
        # Get thumbnails and names
        result = []
        for _, model in sample_models.iterrows():
            thumbnail = ApolloImageHandler.get_primary_thumbnail(model.to_dict())
            result.append((thumbnail, model['name']))
        
        return result

# Global instances for reuse
apollo_image_handler = ApolloImageHandler()
apollo_model_cache = ApolloModelCache()
