"""
Template Manager for Athena PDF Generation System
Handles template selection, data preprocessing, and HTML rendering for different deck styles.
"""

import os
import re
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

# Import path management and HTTPS image handling
from path_config import paths
from https_image_utils import https_image_handler

# Optional imports for template rendering
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False

logger = logging.getLogger(__name__)

class TemplateManager:
    """Manages PDF template selection, data preprocessing, and rendering."""
    
    # Template mapping configuration
    TEMPLATE_MAP = {
        "Agency Standard": {
            "file": "agency_standard.html",
            "description": "Single-model one-pager with hero image and measurements",
            "max_models": 1,
            "use_case": "Individual model presentation"
        },
        "Campaign Pitch": {
            "file": "campaign_pitch.html", 
            "description": "Multi-model campaign deck with cover page",
            "max_models": 6,
            "use_case": "Campaign proposals and client pitches"
        },
        "Editorial Lookbook": {
            "file": "editorial_lookbook.html",
            "description": "Visual-first high-end presentation",
            "max_models": 8,
            "use_case": "Editorial and fashion showcases"
        },
        "Compact Comp Sheet": {
            "file": "compact_comp.html",
            "description": "3x3 grid overview for quick casting",
            "max_models": 9,
            "use_case": "Bulk casting and quick reference"
        }
    }
    
    # Color themes based on campaign keywords
    THEME_KEYWORDS = {
        "desert": "theme-desert",
        "western": "theme-desert", 
        "cowboy": "theme-desert",
        "editorial": "theme-editorial",
        "fashion": "theme-editorial",
        "luxury": "theme-editorial",
        "commercial": "theme-commercial",
        "beauty": "theme-commercial",
        "lifestyle": "theme-commercial"
    }
    
    def __init__(self, templates_dir: str = "templates"):
        """Initialize template manager with templates directory."""
        self.templates_dir = Path(templates_dir)
        
        if not JINJA_AVAILABLE:
            raise ImportError("Template rendering requires 'jinja2' package. Install with: pip install jinja2")
        
        # Set up Jinja environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['slugify'] = self._slugify
        self.env.filters['format_height'] = self._format_height
        self.env.filters['calculate_fit_score'] = self._calculate_fit_score
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available templates with metadata."""
        return self.TEMPLATE_MAP.copy()
    
    def validate_template_selection(self, template_name: str, models: List[Dict[str, Any]]) -> tuple[bool, str]:
        """Validate if template can handle the number of selected models."""
        if template_name not in self.TEMPLATE_MAP:
            return False, f"Template '{template_name}' not found"
        
        template_config = self.TEMPLATE_MAP[template_name]
        max_models = template_config["max_models"]
        
        if len(models) > max_models:
            return False, f"Template '{template_name}' supports max {max_models} models, but {len(models)} selected"
        
        if len(models) == 0:
            return False, "No models selected for PDF generation"
        
        return True, "Valid selection"
    
    def preprocess_data(self, template_name: str, models: List[Dict[str, Any]], 
                       client_brief: str = "", agent_name: str = "Athena") -> Dict[str, Any]:
        """Preprocess data for template rendering."""
        
        # Base data structure
        data = {
            "timestamp": datetime.now().strftime("%B %d, %Y"),
            "agent_name": agent_name,
            "agency": {
                "name": "Elysium Agency",
                "contact": "bookings@elysiumagency.com",
                "website": "www.elysiumagency.com"
            },
            "models": self._process_models(models),
            "template_name": template_name,
            "theme_class": self._detect_theme(client_brief)
        }
        
        # Add campaign information if brief provided
        if client_brief:
            data["campaign"] = self._process_campaign_info(client_brief)
        
        # Template-specific data processing (use processed models)
        processed_models = data["models"]
        if template_name == "Agency Standard":
            data.update(self._process_agency_standard_data(processed_models))
        elif template_name == "Campaign Pitch":
            data.update(self._process_campaign_pitch_data(processed_models, client_brief))
        elif template_name == "Editorial Lookbook":
            data.update(self._process_editorial_data(processed_models))
        elif template_name == "Compact Comp Sheet":
            data.update(self._process_comp_sheet_data(processed_models))
        
        return data
    
    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render HTML template with provided data."""
        try:
            template_config = self.TEMPLATE_MAP[template_name]
            template_file = template_config["file"]
            
            template = self.env.get_template(template_file)
            html_content = template.render(**data)
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise
    
    def _process_models(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process model data for template rendering."""
        processed_models = []
        
        for model in models:
            processed_model = model.copy()
            
            # Ensure required fields exist
            processed_model.setdefault('name', 'Unknown Model')
            processed_model.setdefault('division', 'Unknown')
            processed_model.setdefault('height_cm', 170)
            processed_model.setdefault('hair_color', 'Unknown')
            processed_model.setdefault('eye_color', 'Unknown')
            processed_model.setdefault('images', [])
            
            # REFACTORED: Process images - use HTTPS URLs directly
            processed_images = processed_model.get('images', [])
            # Filter out any empty/invalid URLs
            processed_images = [img for img in processed_images if img and isinstance(img, str)]

            processed_model['images'] = processed_images
            processed_model['hero_image'] = processed_images[0] if processed_images else https_image_handler.PLACEHOLDER_URL
            processed_model['thumbnail_images'] = processed_images[1:4] if len(processed_images) > 1 else []
            
            processed_models.append(processed_model)
        
        return processed_models
    
    def _process_campaign_info(self, client_brief: str) -> Dict[str, Any]:
        """Extract campaign information from client brief."""
        # Simple keyword extraction for campaign type
        campaign_type = "Fashion Campaign"
        if "cowboy" in client_brief.lower() or "western" in client_brief.lower():
            campaign_type = "Western Campaign"
        elif "editorial" in client_brief.lower():
            campaign_type = "Editorial Shoot"
        elif "beauty" in client_brief.lower():
            campaign_type = "Beauty Campaign"
        elif "commercial" in client_brief.lower():
            campaign_type = "Commercial Shoot"
        
        return {
            "title": f"{campaign_type} — {datetime.now().strftime('%b %Y')}",
            "brief": client_brief,
            "type": campaign_type
        }
    
    def _detect_theme(self, client_brief: str) -> str:
        """Detect color theme based on campaign keywords."""
        brief_lower = client_brief.lower()
        
        for keyword, theme_class in self.THEME_KEYWORDS.items():
            if keyword in brief_lower:
                return f"themed {theme_class}"
        
        return "themed"  # Default theme
    
    def _process_agency_standard_data(self, models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data specific to Agency Standard template."""
        return {
            "model": models[0] if models else None,
            "layout_type": "single_model"
        }
    
    def _process_campaign_pitch_data(self, models: List[Dict[str, Any]], client_brief: str) -> Dict[str, Any]:
        """Process data specific to Campaign Pitch template."""
        return {
            "cover_models": models[:4],  # Up to 4 models for cover collage
            "detailed_models": models,   # All models get detail pages
            "layout_type": "multi_page"
        }
    
    def _process_editorial_data(self, models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data specific to Editorial Lookbook template."""
        return {
            "featured_models": models[:8],  # Limit to 8 for editorial
            "layout_type": "visual_first"
        }
    
    def _process_comp_sheet_data(self, models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data specific to Compact Comp Sheet template."""
        return {
            "grid_models": models[:9],  # 3x3 grid maximum
            "layout_type": "grid_compact"
        }
    
    # Jinja2 custom filters
    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        return re.sub(r'[^\w\s-]', '', text).strip().lower().replace(' ', '_')
    
    def _format_height(self, height_cm: int) -> str:
        """Format height in both cm and feet/inches."""
        if not height_cm:
            return "Unknown"
        
        # Convert to feet and inches
        total_inches = height_cm / 2.54
        feet = int(total_inches // 12)
        inches = int(total_inches % 12)
        
        return f"{height_cm}cm ({feet}'{inches}\")"
    
    def _calculate_fit_score(self, model: Dict[str, Any], filters: Dict[str, Any] = None) -> int:
        """Calculate a fit score for the model (for demo purposes)."""
        # Simple scoring algorithm - in real implementation this would be more sophisticated
        score = 75  # Base score
        
        if filters:
            # Add points for matching criteria
            if filters.get('hair_color') and model.get('hair_color'):
                if filters['hair_color'].lower() in model['hair_color'].lower():
                    score += 15
            
            if filters.get('eye_color') and model.get('eye_color'):
                if filters['eye_color'].lower() in model['eye_color'].lower():
                    score += 10
        
        # Add some randomness for demo
        score += random.randint(-5, 5)
        
        return min(100, max(60, score))  # Keep between 60-100
