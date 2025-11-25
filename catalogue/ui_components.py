"""
Catalogue UI Components
Handles all UI rendering for the catalogue including model cards, modals, and search components.
REFACTORED: Now uses HTTPS-only image handling.
"""

import streamlit as st
import pandas as pd
import logging
from typing import Dict, List, Optional, Any

# Import HTTPS image utilities
from https_image_utils import https_image_handler

logger = logging.getLogger(__name__)


class ModelCardRenderer:
    """Handles rendering of model cards with enhanced styling and interactions."""

    @staticmethod
    def display_enhanced_model_card(model_data: Dict[str, Any], col):
        """Display an enhanced model card with hover interactions and quick actions."""
        with col:
            # Create card container with hover styling
            card_id = f"card_{str(model_data['model_id'])}"

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

            # REFACTORED: Model image using HTTPS URL
            https_image_handler.render_model_thumbnail(model_data, width=280)

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
                    📏 {int(model_data['height_cm'])}cm
                </span>
                <span style="background: #f3e5f5; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">
                    💇 {model_data['hair_color'].title()}
                </span>
                <span style="background: #e8f5e8; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.75rem;">
                    👁️ {model_data['eye_color'].title()}
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "👁️ Quick View",
                    key=f"quick_{str(model_data['model_id'])}",
                    type="secondary",
                    use_container_width=True
                ):
                    st.session_state.quick_view_model = model_data['model_id']
                    st.rerun()

            with col2:
                if st.button(
                    "📊 Analytics",
                    key=f"analytics_{str(model_data['model_id'])}",
                    type="secondary",
                    use_container_width=True
                ):
                    # Set shared model context for Apollo
                    from session_manager import SessionManager
                    SessionManager.set_shared_model_context(model_data)
                    SessionManager.add_integration_message(
                        f"Viewing analytics for {model_data['name']}",
                        "success"
                    )
                    st.rerun()

            # Close card div
            st.markdown("</div>", unsafe_allow_html=True)

    @staticmethod
    def _show_image_placeholder(name: str, width: int, height: int, style: str = "default"):
        """Show a styled image placeholder."""
        if style == "light":
            bg_gradient = "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)"
            border_color = "#dee2e6"
            text_color = "#6c757d"
        else:
            bg_gradient = "linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%)"
            border_color = "#ddd"
            text_color = "#666"

        st.markdown(
            f"""
            <div style="
                width: {width}px;
                height: {height}px;
                background: {bg_gradient};
                border: 2px solid {border_color};
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: {text_color};
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            ">
                📷 {name[:15]}
            </div>
            """,
            unsafe_allow_html=True
        )


class ModalRenderer:
    """Handles rendering of quick view modals and expanded views."""

    @staticmethod
    def render_quick_view_modal(df: pd.DataFrame):
        """Render quick view modal for model details with performance optimizations."""
        model_id = st.session_state.get('quick_view_model')
        if not model_id:
            return

        # Check if model data is already cached in session state
        cache_key = f"modal_data_{str(model_id)}"
        if cache_key not in st.session_state:
            # Find model data (only when not cached)
            model_data = df[df['model_id'] == model_id]
            if model_data.empty:
                st.error("Model not found")
                st.session_state.quick_view_model = None
                return

            # Cache the model info in session state
            st.session_state[cache_key] = model_data.iloc[0].to_dict()

        model_info = st.session_state[cache_key]

        # Modal overlay with improved styling
        st.markdown("""
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.6);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(2px);
        ">
        </div>
        """, unsafe_allow_html=True)

        # Modal content with loading states
        with st.container():
            # Header with close button
            header_col1, header_col2 = st.columns([3, 1])
            with header_col1:
                st.markdown("### 👁️ Quick View")
            with header_col2:
                if st.button("❌", key="modal_close_header", help="Close modal"):
                    # Clear cached data when closing
                    if cache_key in st.session_state:
                        del st.session_state[cache_key]
                    st.session_state.quick_view_model = None
                    st.rerun()

            _, col2, _ = st.columns([1, 2, 1])

            with col2:
                # Show model details first (fast)
                st.markdown(f"## {model_info['name']}")
                st.markdown(f"**Division:** {model_info['division'].upper()}")

                # Attributes grid (fast)
                attr_col1, attr_col2 = st.columns(2)
                with attr_col1:
                    st.markdown(f"**Height:** {int(model_info['height_cm'])} cm")
                    st.markdown(f"**Hair:** {model_info['hair_color'].title()}")
                with attr_col2:
                    st.markdown(f"**Eyes:** {model_info['eye_color'].title()}")

                # REFACTORED: Image loading using HTTPS URL
                with st.spinner("Loading image..."):
                    https_image_handler.render_model_thumbnail(model_info, width=300, use_column=False)

                # Action buttons
                st.markdown("---")
                button_col1, button_col2, button_col3 = st.columns(3)

                with button_col1:
                    if st.button("📊 Analytics", key="modal_analytics", use_container_width=True):
                        from session_manager import SessionManager
                        SessionManager.set_shared_model_context(model_info)
                        SessionManager.add_integration_message(
                            f"Viewing analytics for {model_info['name']}",
                            "success"
                        )
                        # Clear cached data
                        if cache_key in st.session_state:
                            del st.session_state[cache_key]
                        st.session_state.quick_view_model = None
                        st.rerun()

                with button_col2:
                    if st.button("🎯 Athena", key="modal_athena", use_container_width=True):
                        from session_manager import SessionManager
                        SessionManager.transfer_model_to_athena(model_info, "Catalogue")
                        # Clear cached data
                        if cache_key in st.session_state:
                            del st.session_state[cache_key]
                        st.session_state.quick_view_model = None
                        st.rerun()

                with button_col3:
                    if st.button("❌ Close", key="modal_close", use_container_width=True):
                        # Clear cached data
                        if cache_key in st.session_state:
                            del st.session_state[cache_key]
                        st.session_state.quick_view_model = None
                        st.rerun()

    @staticmethod
    def _show_modal_image_fallback(name: str, width: int, height: int):
        """Show fallback image for modal."""
        st.markdown(f"""
        <div style="
            width: {width}px;
            height: {height}px;
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
            📷 {name}
        </div>
        """, unsafe_allow_html=True)


class SearchRenderer:
    """Handles rendering of search components and results."""

    @staticmethod
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
            summary_parts.append(f"**Height:** {int(height_range[0])}-{int(height_range[1])}cm")
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

    @staticmethod
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
                from session_manager import SessionManager
                SessionManager.add_notification("All filters cleared! Showing complete roster.", "success")
                st.rerun()


class ExpandedModelRenderer:
    """Handles rendering of expanded model views with full details and galleries."""

    @staticmethod
    def show_expanded_model_view(model_data: Dict[str, Any], filtered_df):
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
            current_index = ExpandedModelRenderer._get_model_index_in_filtered(model_data['model_id'], filtered_df)
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
            st.markdown(f"**Height:** {int(model_data['height_cm'])} cm")
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
            st.markdown(f"**Model ID:** {str(model_data['model_id'])}")

        st.markdown("---")

        # REFACTORED: Image Gallery Section with HTTPS URLs
        st.subheader("📸 Portfolio Gallery")

        # Use HTTPS image handler for portfolio gallery
        https_image_handler.render_portfolio_gallery(model_data, images_per_row=3, max_images=12)

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

    @staticmethod
    def _get_model_index_in_filtered(model_id, filtered_df):
        """Get the index of a model in the filtered DataFrame."""
        try:
            return filtered_df[filtered_df['model_id'] == model_id].index[0]
        except (IndexError, KeyError):
            return 0

    @staticmethod
    def _render_image_carousel(model_data: Dict[str, Any], valid_images: List[str]):
        """Render image carousel with navigation controls."""
        # Initialize carousel state
        carousel_key = f'carousel_index_{str(model_data["model_id"])}'
        if carousel_key not in st.session_state:
            st.session_state[carousel_key] = 0

        current_carousel_index = st.session_state[carousel_key]
        total_images = len(valid_images)

        # Carousel controls
        carousel_col1, carousel_col2, carousel_col3 = st.columns([1, 2, 1])

        with carousel_col1:
            if st.button("⬅️ Previous Image", disabled=(current_carousel_index <= 0), key=f"prev_img_{str(model_data['model_id'])}"):
                st.session_state[carousel_key] -= 1
                st.rerun()

        with carousel_col2:
            st.markdown(f"**Image {current_carousel_index + 1} of {total_images}**")

        with carousel_col3:
            if st.button("➡️ Next Image", disabled=(current_carousel_index >= total_images - 1), key=f"next_img_{str(model_data['model_id'])}"):
                st.session_state[carousel_key] += 1
                st.rerun()

        # Display current image in carousel
        ExpandedModelRenderer._display_carousel_image(valid_images, current_carousel_index)

        # Thumbnail strip
        st.markdown("---")
        st.markdown("**All Images:**")
        ExpandedModelRenderer._render_thumbnail_strip(model_data, valid_images)

    @staticmethod
    def _display_carousel_image(valid_images: List[str], current_index: int):
        """Display the current carousel image."""
        carousel_container = st.container()
        with carousel_container:
            try:
                # Create a centered container for the main image
                _, col2, _ = st.columns([1, 2, 1])
                with col2:
                    current_image_path = valid_images[current_index]
                    if os.path.exists(current_image_path):
                        try:
                            img = Image.open(current_image_path)
                            st.image(img, width=400, caption=f"Portfolio Image {current_index + 1}")
                        except Exception:
                            ExpandedModelRenderer._show_carousel_placeholder(current_index + 1, 400, 300)
                    else:
                        ExpandedModelRenderer._show_carousel_placeholder("Not Found", 400, 300, style="error")
            except Exception as e:
                st.error(f"Could not load image: {e}")

    @staticmethod
    def _show_carousel_placeholder(label: str, width: int, height: int, style: str = "default"):
        """Show placeholder for carousel images."""
        if style == "error":
            bg_gradient = "linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%)"
            border_color = "#ddd"
            text_color = "#666"
        else:
            bg_gradient = "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)"
            border_color = "#dee2e6"
            text_color = "#6c757d"

        st.markdown(f"""
        <div style="
            width: {width}px;
            height: {height}px;
            background: {bg_gradient};
            border: 2px solid {border_color};
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: {text_color};
            font-size: 18px;
            font-weight: bold;
            margin: 0 auto;
        ">
            📷 {label}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def _render_thumbnail_strip(model_data: Dict[str, Any], valid_images: List[str]):
        """Render thumbnail strip for quick navigation."""
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
                            if st.button(f"📷", key=f"thumb_{str(model_data['model_id'])}_{img_idx}", help=f"Jump to image {img_idx + 1}"):
                                carousel_key = f'carousel_index_{str(model_data["model_id"])}'
                                st.session_state[carousel_key] = img_idx
                                st.rerun()

                            # Show thumbnail with border if it's the current image
                            thumb_path = valid_images[img_idx]
                            if os.path.exists(thumb_path):
                                try:
                                    img = Image.open(thumb_path)
                                    # Resize for thumbnail display
                                    img.thumbnail((100, 80))
                                    st.image(img, caption=f"Thumbnail {img_idx + 1}")
                                except Exception:
                                    ExpandedModelRenderer._show_thumbnail_placeholder(img_idx + 1, 100, 80)
                            else:
                                ExpandedModelRenderer._show_thumbnail_placeholder(img_idx + 1, 100, 80, style="error")
                        except Exception as e:
                            st.error(f"Could not load thumbnail: {e}")

    @staticmethod
    def _show_thumbnail_placeholder(label: str, width: int, height: int, style: str = "default"):
        """Show placeholder for thumbnail images."""
        if style == "error":
            bg_gradient = "linear-gradient(135deg, #f0f0f0 0%, #e0e0e0 100%)"
            border_color = "#ddd"
            text_color = "#666"
        else:
            bg_gradient = "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)"
            border_color = "#dee2e6"
            text_color = "#6c757d"

        st.markdown(f"""
        <div style="
            width: {width}px;
            height: {height}px;
            background: {bg_gradient};
            border: 1px solid {border_color};
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: {text_color};
            font-size: 12px;
            font-weight: bold;
        ">
            📷 {label}
        </div>
        """, unsafe_allow_html=True)
