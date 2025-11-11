"""
Unified Theme Manager for Elysium Streamlit App
Provides consistent styling, colors, and layout across all tabs.
"""

import streamlit as st
from typing import Dict, Any
from session_manager import SessionManager

class ThemeManager:
    """Manages consistent theming across the application."""
    
    # Color palette
    COLORS = {
        'primary': '#667eea',
        'secondary': '#764ba2',
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8',
        'light': '#f8f9fa',
        'dark': '#343a40',
        'white': '#ffffff',
        'gray_100': '#f8f9fa',
        'gray_200': '#e9ecef',
        'gray_300': '#dee2e6',
        'gray_400': '#ced4da',
        'gray_500': '#adb5bd',
        'gray_600': '#6c757d',
        'gray_700': '#495057',
        'gray_800': '#343a40',
        'gray_900': '#212529'
    }
    
    # Typography
    FONTS = {
        'primary': '"Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif',
        'monospace': '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace'
    }
    
    # Spacing
    SPACING = {
        'xs': '0.25rem',
        'sm': '0.5rem',
        'md': '1rem',
        'lg': '1.5rem',
        'xl': '2rem',
        'xxl': '3rem'
    }
    
    # Border radius
    RADIUS = {
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        'pill': '50px'
    }
    
    @staticmethod
    def load_css_file(css_file_path: str) -> str:
        """Load CSS from external file."""
        try:
            from pathlib import Path
            css_path = Path(__file__).parent / css_file_path
            if css_path.exists():
                return css_path.read_text(encoding='utf-8')
            else:
                return ""
        except Exception as e:
            st.warning(f"Could not load CSS file: {e}")
            return ""

    @staticmethod
    def apply_global_theme():
        """Apply global theme styles to the app."""
        theme = SessionManager.get_user_preference('theme', 'light')

        # Load external CSS file
        external_css = ThemeManager.load_css_file('styles.css')

        # Additional dynamic styles
        dynamic_css = f"""
        /* Theme-specific overrides */
        .theme-{theme} {{
            /* Add theme-specific styles here */
        }}

        /* Model card enhancements */
        .model-card {{
            background: var(--white);
            border-radius: var(--radius-lg);
            padding: var(--spacing-lg);
            margin: var(--spacing-md) 0;
            box-shadow: var(--shadow-sm);
            transition: all var(--transition-normal);
            border: 1px solid var(--gray-200);
        }}

        .model-card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }}

        /* Image sizing for model cards */
        .stImage > img,
        .stImage img,
        img[data-testid="stImage"],
        [data-testid="stImage"] img,
        .stApp img {{
            border-radius: var(--radius-md) !important;
            object-fit: cover !important;
            aspect-ratio: 3/4 !important;
            height: 250px !important;
            width: auto !important;
            max-width: 100% !important;
        }}

        /* Container for images */
        .stImage,
        [data-testid="stImage"] {{
            height: 250px !important;
            overflow: hidden !important;
            border-radius: var(--radius-md) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        """

        # Combine external CSS with dynamic CSS
        combined_css = f"<style>{external_css}\n{dynamic_css}</style>"
        st.markdown(combined_css, unsafe_allow_html=True)
    
    @staticmethod
    def apply_apollo_theme():
        """Apply Apollo-specific dark theme overrides."""
        apollo_css = f"""
        <style>
        /* Apollo Dark Theme Override */
        .stApp {{
            background: linear-gradient(135deg, #0A0A0F 0%, #1A1A1F 100%) !important;
            color: #FFFFFF !important;
        }}
        
        /* Override all text elements for Apollo */
        .stApp .stMarkdown,
        .stApp .stText,
        .stApp .stCaption,
        .stApp p,
        .stApp div,
        .stApp span,
        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp h4,
        .stApp h5,
        .stApp h6 {{
            color: #FFFFFF !important;
        }}
        
        /* Apollo Cards */
        .apollo-card {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #2d3748;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        
        /* Apollo Metrics */
        .apollo-metric {{
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            color: white;
        }}
        
        /* Apollo Buttons */
        .apollo-button {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .apollo-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }}
        </style>
        """
        
        st.markdown(apollo_css, unsafe_allow_html=True)
    
    @staticmethod
    def get_color(color_name: str) -> str:
        """Get a color value by name."""
        return ThemeManager.COLORS.get(color_name, '#000000')
    
    @staticmethod
    def get_gradient(start_color: str, end_color: str) -> str:
        """Get a CSS gradient string."""
        start = ThemeManager.get_color(start_color)
        end = ThemeManager.get_color(end_color)
        return f"linear-gradient(90deg, {start} 0%, {end} 100%)"
    
    @staticmethod
    def create_card_style(background: str = 'white', border: bool = True, shadow: bool = True) -> str:
        """Create a card style string."""
        bg_color = ThemeManager.get_color(background)
        border_style = f"border: 1px solid {ThemeManager.COLORS['gray_300']};" if border else ""
        shadow_style = "box-shadow: 0 2px 4px rgba(0,0,0,0.1);" if shadow else ""
        
        return f"""
        background-color: {bg_color};
        {border_style}
        {shadow_style}
        border-radius: {ThemeManager.RADIUS['md']};
        padding: {ThemeManager.SPACING['md']};
        margin: {ThemeManager.SPACING['md']} 0;
        """
    
    @staticmethod
    def create_button_style(variant: str = 'primary') -> str:
        """Create a button style string."""
        if variant == 'primary':
            return f"""
            background: {ThemeManager.get_gradient('primary', 'secondary')};
            color: white;
            border: none;
            border-radius: {ThemeManager.RADIUS['md']};
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            """
        elif variant == 'secondary':
            return f"""
            background: {ThemeManager.COLORS['white']};
            color: {ThemeManager.COLORS['primary']};
            border: 1px solid {ThemeManager.COLORS['primary']};
            border-radius: {ThemeManager.RADIUS['md']};
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            """
        else:
            return ""
