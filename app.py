"""
Elysium Model Catalogue - Enhanced Streamlit App (Refactored)
A polished Streamlit web app with modular architecture.
"""

import streamlit as st
import pandas as pd
import os
from typing import Dict, List, Optional, Any
import logging

# Import enhanced components
from session_manager import SessionManager
from ui_components import (
    LoadingComponents, NotificationComponents, ErrorComponents,
    HeaderComponents, FooterComponents, NavigationComponents
)
from theme_manager import ThemeManager
from athena_ui import AthenaUI

# Import modular catalogue components
from catalogue import (
    FilterEngine, OllamaClient,
    ModelCardRenderer, ModalRenderer, SearchRenderer, ExpandedModelRenderer
)

# Import unified data loader
from unified_data_loader import unified_loader

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
from path_config import paths

# Validate data files on startup
data_status = paths.validate_data_files()
missing_files = [f for f, status in data_status.items() if not status['exists']]
if missing_files:
    st.error(f"Missing data files: {', '.join(missing_files)}")
    st.info("Please ensure all CSV files are present in the 'out/' directory.")
    st.stop()

# Constants
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:4b"

def get_model_index_in_filtered(model_id: str, filtered_df: pd.DataFrame) -> int:
    """Get the index of a model in the filtered dataframe."""
    try:
        model_ids = filtered_df['model_id'].tolist()
        return model_ids.index(model_id)
    except (ValueError, KeyError):
        return 0

# Wrapper functions for backward compatibility
def display_enhanced_model_card(model_data: Dict[str, Any], col):
    """Display an enhanced model card - delegated to ModelCardRenderer."""
    ModelCardRenderer.display_enhanced_model_card(model_data, col)

def render_quick_view_modal(df: pd.DataFrame):
    """Render quick view modal - delegated to ModalRenderer."""
    ModalRenderer.render_quick_view_modal(df)

def render_ai_search_summary(ai_filters: dict, result_count: int):
    """Render AI search summary - delegated to SearchRenderer."""
    SearchRenderer.render_ai_search_summary(ai_filters, result_count)

def render_enhanced_empty_state(ai_filters: dict, full_df):
    """Render enhanced empty state - delegated to SearchRenderer."""
    SearchRenderer.render_enhanced_empty_state(ai_filters, full_df)

def show_expanded_model_view(model_data: Dict[str, Any], filtered_df: pd.DataFrame):
    """Show expanded model view - delegated to ExpandedModelRenderer."""
    ExpandedModelRenderer.show_expanded_model_view(model_data, filtered_df)

def display_model_grid_with_pagination(filtered_df: pd.DataFrame, models_per_page: int = 15):
    """Display models in a responsive grid layout with pagination."""
    if filtered_df.empty:
        st.info("🔍 No models found for this search. Try adjusting your filters.")
        return

    total_models = len(filtered_df)

    # Initialize pagination state with renamed variable to avoid conflicts
    if 'pagination_current_page' not in st.session_state:
        st.session_state.pagination_current_page = 0
    if 'models_per_page' not in st.session_state:
        st.session_state.models_per_page = models_per_page

    # Reset pagination when filters change
    if 'last_result_count' not in st.session_state:
        st.session_state.last_result_count = total_models
    elif st.session_state.last_result_count != total_models:
        st.session_state.pagination_current_page = 0
        st.session_state.last_result_count = total_models

    current_page = st.session_state.pagination_current_page
    start_idx = current_page * models_per_page
    end_idx = min(start_idx + models_per_page, total_models)

    # Display current page models
    current_models = filtered_df.iloc[start_idx:end_idx]

    # Create responsive grid
    cols_per_row = 3
    rows = len(current_models) // cols_per_row + (1 if len(current_models) % cols_per_row > 0 else 0)

    for row in range(rows):
        cols = st.columns(cols_per_row)
        for col_idx in range(cols_per_row):
            model_idx = row * cols_per_row + col_idx
            if model_idx < len(current_models):
                model_data = current_models.iloc[model_idx].to_dict()
                display_enhanced_model_card(model_data, cols[col_idx])

    # Pagination controls
    if total_models > models_per_page:
        st.markdown("---")
        total_pages = (total_models + models_per_page - 1) // models_per_page

        # Pagination info
        st.markdown(f"**Showing {start_idx + 1}-{end_idx} of {total_models} models (Page {current_page + 1} of {total_pages})**")

        # Navigation buttons
        nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 2, 1, 1])

        with nav_col1:
            if st.button("⏮️ First", disabled=(current_page == 0)):
                st.session_state.pagination_current_page = 0
                st.rerun()

        with nav_col2:
            if st.button("⬅️ Previous", disabled=(current_page == 0)):
                st.session_state.pagination_current_page = max(0, current_page - 1)
                st.rerun()

        with nav_col3:
            # Page jump selector
            page_options = list(range(1, total_pages + 1))
            selected_page = st.selectbox(
                "Jump to page:",
                page_options,
                index=current_page,
                key="page_selector"
            )
            if selected_page != current_page + 1:
                st.session_state.pagination_current_page = int(selected_page) - 1
                st.rerun()

        with nav_col4:
            if st.button("➡️ Next", disabled=(current_page >= total_pages - 1)):
                st.session_state.pagination_current_page = min(total_pages - 1, current_page + 1)
                st.rerun()

        with nav_col5:
            if st.button("⏭️ Last", disabled=(current_page >= total_pages - 1)):
                st.session_state.pagination_current_page = total_pages - 1
                st.rerun()

def display_model_grid(filtered_df: pd.DataFrame, max_results: int = 20):
    """Legacy function - redirects to paginated version."""
    display_model_grid_with_pagination(filtered_df, models_per_page=max_results)

def main():
    """Enhanced main Streamlit application with unified navigation and theming."""
    
    # Initialize session manager
    SessionManager.initialize_session()
    
    # Apply theme
    ThemeManager.apply_global_theme()
    
    # Show header
    HeaderComponents.show_global_header()

    # Show notifications
    NotificationComponents.show_notifications()

    # Navigation
    current_page = NavigationComponents.show_sidebar_navigation()
    
    # REFACTORED: Load data using unified loader
    with LoadingComponents.show_global_spinner("Loading model data..."):
        df = unified_loader.load_models()
    
    if df.empty:
        ErrorComponents.show_error_card("Data Error", "No model data available.")
        return
    
    # Route to appropriate page
    logger.info(f"Current page: '{current_page}'")
    if current_page == "Catalogue":
        logger.info("Rendering Catalogue page")
        render_catalogue_page(df)
    elif current_page == "Athena":
        logger.info("Rendering Athena page")
        render_athena_page(df)
    elif current_page == "Apollo":
        logger.info("Rendering Apollo page")
        render_apollo_page()
    else:
        logger.warning(f"Unknown page: '{current_page}'")
    
    # Show footer
    FooterComponents.show_global_footer()

def render_catalogue_page(df: pd.DataFrame):
    """Render the enhanced Catalogue page with hybrid search and interactive features."""
    try:
        st.markdown("## 🎭 Model Catalogue")
        
        # Handle quick view modal
        render_quick_view_modal(df)
        
        # Handle expanded model view
        if st.session_state.get('selected_model'):
            model_data = df[df['model_id'] == st.session_state.selected_model]
            if not model_data.empty:
                show_expanded_model_view(model_data.iloc[0].to_dict(), df)
                return
        
        # Search and filter interface
        search_col1, search_col2 = st.columns([2, 1])
        
        with search_col1:
            # Natural language search
            nl_query = st.text_input(
                "🤖 Natural Language Search",
                placeholder="e.g., 'taller blonde models with blue eyes from development'",
                key="nl_search_query"
            )
            
            if nl_query and st.button("🔍 AI Search", type="primary"):
                with st.spinner("🤖 Processing your search..."):
                    ai_filters = OllamaClient.query_ollama(OllamaClient.create_prompt(nl_query))
                    if ai_filters:
                        st.session_state.ai_filters = ai_filters
                        st.rerun()
        
        with search_col2:
            # Text search
            text_search = st.text_input(
                "📝 Text Search",
                placeholder="Search names, IDs, etc.",
                key="text_search_query"
            )
        
        # Apply filters
        ai_filters = st.session_state.get('ai_filters', {})
        filtered_df = FilterEngine.apply_filters(
            df,
            ai_filters=ai_filters,
            text_search=text_search
        )
        
        # Show AI search summary if active
        if ai_filters:
            render_ai_search_summary(ai_filters, len(filtered_df))
        
        # Show results or empty state
        if filtered_df.empty:
            render_enhanced_empty_state(ai_filters, df)
        else:
            st.markdown(f"### 📊 Results ({len(filtered_df)} models)")
            display_model_grid_with_pagination(filtered_df)
            
    except Exception as e:
        logger.error(f"Error in catalogue page: {e}")
        ErrorComponents.show_error_card("Catalogue Error", f"Error rendering catalogue: {str(e)}")

def render_athena_page(df: pd.DataFrame):
    """Render the Athena page with enhanced UI."""
    try:
        athena_ui = AthenaUI()
        athena_ui.render_athena_tab(df)
    except Exception as e:
        logger.error(f"Error in Athena page: {e}")
        ErrorComponents.show_error_card("Athena Error", f"Error loading Athena: {str(e)}")

def render_apollo_page():
    """Render the Apollo page with enhanced UI."""
    try:
        from apollo import main as apollo_main
        apollo_main()
    except Exception as e:
        logger.error(f"Error in Apollo page: {e}")
        ErrorComponents.show_error_card("Apollo Error", f"Error loading Apollo: {str(e)}")

if __name__ == "__main__":
    main()
