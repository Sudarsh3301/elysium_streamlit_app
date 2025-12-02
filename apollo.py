"""
Apollo — Agency Intelligence Dashboard
Premium AI strategist dashboard for fashion agencies.

Purpose: Proactively identify revenue opportunities and route actions to Athena
Inputs: CSV data files from out/ directory
Outputs: Interactive intelligence dashboard with actionable insights
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from apollo_data import ApolloDataLoader, ApolloMetrics
from apollo_image_utils import apollo_image_handler, apollo_model_cache
from https_image_utils import https_image_handler

def render_apollo_thumbnail(model_data: dict, width: int = 64, key_suffix: str = "") -> None:
    """
    REFACTORED: Render model thumbnail using HTTPS URLs only.
    Replaces all the complex PIL image loading logic.
    """
    try:
        thumbnail_url = https_image_handler.get_thumbnail_url(model_data)
        st.image(thumbnail_url, width=width)
    except Exception as e:
        # Fallback to placeholder
        st.markdown(f"""
        <div style="
            width: {width}px;
            height: {int(width * 1.33)}px;
            background: #333;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            color: #666;
            font-size: 12px;
        ">📷</div>
        """, unsafe_allow_html=True)

def render_apollo_button(label: str, button_type: str = "primary", key: str = None,
                        onclick_action: str = None, disabled: bool = False) -> bool:
    """Render a standardized Apollo button with consistent styling."""
    button_class = {
        "primary": "apollo-btn",
        "secondary": "apollo-btn-secondary",
        "danger": "apollo-btn-danger",
        "filter": "apollo-filter-btn"
    }.get(button_type, "apollo-btn")

    disabled_style = "opacity: 0.5; cursor: not-allowed;" if disabled else ""
    onclick_js = f"onclick=\"{onclick_action}\"" if onclick_action else ""

    button_html = f"""
    <button class="{button_class}" {onclick_js} style="{disabled_style}"
            {'disabled' if disabled else ''}>
        {label}
    </button>
    """

    # Use columns to center the button and handle clicks
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(button_html, unsafe_allow_html=True)
        # Return a clickable state using session state
        if key and not disabled:
            return st.button("", key=f"hidden_{key}")
    return False

def render_apollo_filter_buttons(regions: list, active_region: str = None) -> str:
    """Render region/city filter buttons."""
    buttons_html = '<div style="margin: 1rem 0; text-align: center;">'

    for region in regions:
        active_class = " active" if region == active_region else ""
        buttons_html += f"""
        <button class="apollo-filter-btn{active_class}"
                onclick="selectRegion('{region}')">
            {region}
        </button>
        """

    buttons_html += '</div>'
    st.markdown(buttons_html, unsafe_allow_html=True)

    # Handle region selection through session state
    selected_region = None
    for region in regions:
        if st.button("", key=f"region_hidden_{region}"):
            selected_region = region
            break

    return selected_region

def apply_apollo_styling():
    """Apply luxury fashion styling to the Apollo dashboard."""
    st.markdown("""
    <style>
    /* Apollo Premium Styling - Override everything for dark theme */
    .stApp {
        background: linear-gradient(135deg, #0A0A0F 0%, #1A1A1F 100%) !important;
        color: #FFFFFF !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
        pointer-events: auto !important;
    }

    /* Ensure main container allows pointer events */
    .main {
        pointer-events: auto !important;
    }

    /* Remove default Streamlit padding/margins */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        pointer-events: auto !important;
    }

    /* Override all text elements to be light colored */
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
    .stApp h6 {
        color: #FFFFFF !important;
    }

    /* Sidebar dark theme */
    .stSidebar {
        background: linear-gradient(135deg, #1A1A1F 0%, #2A2A35 100%) !important;
    }

    .stSidebar .stMarkdown,
    .stSidebar p,
    .stSidebar div,
    .stSidebar span {
        color: #FFFFFF !important;
    }

    /* COMPLETELY DISABLE Streamlit's default << collapse button */
    [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* Apollo dashboard container */
    
    
    /* Typography */
    .apollo-title {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-weight: 700;
        color: #2EF0FF;
        text-align: center;
        margin-top: 0 !important;
        margin-bottom: 0.5rem;
        padding-top: 0 !important;
        text-shadow: 0 0 20px rgba(46, 240, 255, 0.3);
    }

    .apollo-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        color: #CCCCCC;
        text-align: center;
        margin-bottom: 3rem;
        font-style: italic;
    }

    .section-header {
        font-family: 'Playfair Display', serif;
        font-size: 1.8rem;
        color: #2EF0FF;
        margin-bottom: 1.5rem;
        border-bottom: 2px solid #2EF0FF;
        padding-bottom: 0.5rem;
    }
    
    /* KPI Tiles */
    .kpi-tile {
        background: linear-gradient(135deg, #1A1A1F 0%, #2A2A35 100%);
        border: 1px solid #2EF0FF;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem;
        box-shadow: 0 8px 32px rgba(46, 240, 255, 0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .kpi-tile:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(46, 240, 255, 0.2);
        border-color: #2EF0FF;
    }
    
    .kpi-tile::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #2EF0FF, #00D4FF);
    }
    
    .kpi-value {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.5rem;
    }
    
    .kpi-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #E0E0E0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .kpi-delta {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        display: inline-block;
    }
    
    .kpi-delta.positive {
        color: #00FF88;
        background: rgba(0, 255, 136, 0.1);
    }
    
    .kpi-delta.negative {
        color: #FF4444;
        background: rgba(255, 68, 68, 0.1);
    }
    
    .kpi-insight {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: #B0B0B0;
        margin-top: 0.5rem;
        font-style: italic;
    }
    
    /* Premium Cards */
    .premium-card {
        background: linear-gradient(135deg, #1A1A1F 0%, #2A2A35 100%);
        border: 1px solid rgba(46, 240, 255, 0.3);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .premium-card:hover {
        border-color: #2EF0FF;
        box-shadow: 0 8px 30px rgba(46, 240, 255, 0.1);
    }
    
    .vip-card {
        background: linear-gradient(135deg, #2A1A2A 0%, #3A2A3A 100%);
        border: 2px solid #FFD700;
        position: relative;
        overflow: hidden;
    }
    
    .vip-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255, 215, 0, 0.1), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    /* Action Buttons - Standardized Styling */
    .apollo-btn {
        background: linear-gradient(135deg, #2EF0FF 0%, #00D4FF 100%);
        color: #0D0D0F !important;
        border: none;
        border-radius: 25px;
        padding: 0.6rem 1.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.92rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        min-width: 160px;
        height: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        box-sizing: border-box;
    }

    .apollo-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(46, 240, 255, 0.4);
        background: linear-gradient(135deg, #00D4FF 0%, #2EF0FF 100%);
        color: #0D0D0F !important;
    }

    .apollo-btn-secondary {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #0D0D0F !important;
        border: none;
        border-radius: 25px;
        padding: 0.6rem 1.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.92rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        min-width: 160px;
        height: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        box-sizing: border-box;
    }

    .apollo-btn-secondary:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.4);
        background: linear-gradient(135deg, #FFA500 0%, #FFD700 100%);
        color: #0D0D0F !important;
    }

    .apollo-btn-danger {
        background: linear-gradient(135deg, #FF4444 0%, #CC3333 100%);
        color: #FFFFFF !important;
        border: none;
        border-radius: 25px;
        padding: 0.6rem 1.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.92rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        min-width: 160px;
        height: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        box-sizing: border-box;
    }

    .apollo-btn-danger:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255, 68, 68, 0.4);
        background: linear-gradient(135deg, #CC3333 0%, #FF4444 100%);
        color: #FFFFFF !important;
    }

    /* Region/City Filter Buttons */
    .apollo-filter-btn {
        background: rgba(46, 240, 255, 0.1);
        color: #2EF0FF !important;
        border: 1px solid #2EF0FF;
        border-radius: 20px;
        padding: 0.4rem 1rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.3s ease;
        min-width: 80px;
        height: 32px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        box-sizing: border-box;
        margin: 0.2rem;
    }

    .apollo-filter-btn:hover {
        background: rgba(46, 240, 255, 0.2);
        border-color: #00D4FF;
        color: #00D4FF !important;
        transform: translateY(-1px);
    }

    .apollo-filter-btn.active {
        background: linear-gradient(135deg, #2EF0FF 0%, #00D4FF 100%);
        color: #0D0D0F !important;
        border-color: #2EF0FF;
    }

    /* Icon Standardization */
    .apollo-icon {
        width: 20px;
        height: 20px;
        display: inline-block;
        margin-right: 0.5rem;
    }

    /*
     * IMPORTANT: Only hide Streamlit buttons in MAIN content area, NOT in sidebar!
     * This ensures the global navigation buttons remain visible.
     */

    /* Hide Streamlit buttons only in main content area (not sidebar) */
    .main .stButton > button,
    [data-testid="stMainBlockContainer"] .stButton > button {
        display: none !important;
    }

    /* Ensure sidebar navigation buttons are ALWAYS visible */
    .stSidebar .stButton > button,
    [data-testid="stSidebar"] .stButton > button {
        display: inline-flex !important;
        visibility: visible !important;
    }

    /* Ensure our custom buttons are visible */
    .apollo-btn, .apollo-btn-secondary, .apollo-btn-danger, .apollo-filter-btn, .apollo-cta {
        display: inline-flex !important;
        visibility: visible !important;
    }

    /* Hide Streamlit button containers only in main content, not sidebar */
    /* EXCEPT for the sidebar toggle button which must always be visible */
    .main .stButton:not(.st-key-open_sidebar_btn .stButton):not(.st-key-open_s .stButton),
    [data-testid="stMainBlockContainer"] .stButton:not(.st-key-open_sidebar_btn .stButton):not(.st-key-open_s .stButton) {
        display: none !important;
    }

    /* CRITICAL: Ensure sidebar toggle button is ALWAYS visible by targeting its key */
    .st-key-open_sidebar_btn,
    .st-key-open_sidebar_btn .stButton,
    .st-key-open_sidebar_btn .stButton button,
    .st-key-open_s,
    .st-key-open_s .stButton,
    .st-key-open_s .stButton button {
        display: inline-flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        height: auto !important;
        width: auto !important;
        min-width: 120px !important;
        min-height: 40px !important;
        pointer-events: auto !important;
        cursor: pointer !important;
        z-index: 100000 !important;
    }

    /* Make sure sidebar button containers ARE visible */
    .stSidebar .stButton,
    [data-testid="stSidebar"] .stButton {
        display: block !important;
    }

    /* Make sure button containers don't take up space only in main area */
    /* EXCEPT for the sidebar toggle button */
    .main .stButton[data-testid="stButton"]:not(.st-key-open_sidebar_btn .stButton):not(.st-key-open_s .stButton),
    [data-testid="stMainBlockContainer"] .stButton[data-testid="stButton"]:not(.st-key-open_sidebar_btn .stButton):not(.st-key-open_s .stButton) {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Legacy CTA class for backward compatibility */
    .apollo-cta {
        background: linear-gradient(135deg, #2EF0FF 0%, #00D4FF 100%);
        color: #0D0D0F !important;
        border: none;
        border-radius: 25px;
        padding: 0.6rem 1.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.92rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        min-width: 160px;
        height: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        text-decoration: none;
        box-sizing: border-box;
    }

    .apollo-cta:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(46, 240, 255, 0.4);
        background: linear-gradient(135deg, #00D4FF 0%, #2EF0FF 100%);
        color: #0D0D0F !important;
    }
    
    /* Charts */
    .plotly-chart {
        background: transparent !important;
    }
    
    /* Footer */
    .apollo-footer {
        text-align: center;
        margin-top: 3rem;
        padding: 2rem;
        border-top: 1px solid rgba(46, 240, 255, 0.3);
        color: #666666;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
    }
    
    /* Responsive Grid */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin-bottom: 3rem;
    }
    
    .two-column {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        margin-bottom: 3rem;
    }
    
    @media (max-width: 768px) {
        .two-column {
            grid-template-columns: 1fr;
        }
        .apollo-title {
            font-size: 2rem;
        }
    }
    
    /* Hide Streamlit elements */
    .stDeployButton {display: none;}
    .stDecoration {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Force white text for all elements */
    .stMarkdown, .stText, .stCaption, p, div, span, .stSelectbox label, .stButton button {
        color: #FFFFFF !important;
    }
    
    /* Plotly chart background */
    .js-plotly-plot .plotly .modebar {
        background: rgba(13, 13, 15, 0.8) !important;
    }
    </style>
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <!-- JavaScript for button interactions -->
    <script>
    function selectRegion(region) {
        // This would be handled by the hidden Streamlit buttons
        console.log('Region selected:', region);
    }

    // Ensure custom buttons are clickable
    document.addEventListener('DOMContentLoaded', function() {
        // Add click handlers to custom buttons if needed
        const customButtons = document.querySelectorAll('.apollo-btn, .apollo-btn-secondary, .apollo-btn-danger, .apollo-filter-btn');
        customButtons.forEach(button => {
            button.style.cursor = 'pointer';
        });
    });
    </script>
    """, unsafe_allow_html=True)

def render_kpi_tile(title: str, value: str, delta: float, insight: str, icon: str = "📊"):
    """Render a single KPI tile with premium styling."""
    delta_class = "positive" if delta >= 0 else "negative"
    delta_symbol = "↑" if delta >= 0 else "↓"
    delta_text = f"{delta_symbol} {abs(delta):.1f}%" if delta != 0 else "→ Stable"
    
    return f"""
    <div class="kpi-tile">
        <div class="kpi-label">{icon} {title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta {delta_class}">{delta_text}</div>
        <div class="kpi-insight">{insight}</div>
    </div>
    """

def render_kpi_hero_section(metrics: dict):
    """Render the 6 KPI hero tiles in a responsive grid."""
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    
    # Create 6 columns for KPI tiles
    cols = st.columns(3)
    
    kpi_configs = [
        ("Total Revenue", f"${metrics.get('total_revenue', {}).get('value', 0):,.0f}", 
         metrics.get('total_revenue', {}).get('delta', 0), 
         metrics.get('total_revenue', {}).get('insight', 'Revenue tracking'), "💰"),
        
        ("Conversion Rate", f"{metrics.get('conversion_rate', {}).get('value', 0):.1f}%", 
         metrics.get('conversion_rate', {}).get('delta', 0), 
         metrics.get('conversion_rate', {}).get('insight', 'Casting success'), "🎯"),
        
        ("Rebooking Rate", f"{metrics.get('rebook_rate', {}).get('value', 0):.1f}%", 
         metrics.get('rebook_rate', {}).get('delta', 0), 
         metrics.get('rebook_rate', {}).get('insight', 'Client loyalty'), "🔄"),
        
        ("Avg Time-to-Book", f"{metrics.get('avg_time_to_book', {}).get('value', 0):.1f} days", 
         metrics.get('avg_time_to_book', {}).get('delta', 0), 
         metrics.get('avg_time_to_book', {}).get('insight', 'Booking speed'), "⚡"),
        
        ("Automation Rate", f"{metrics.get('automation_rate', {}).get('value', 0):.1f}%", 
         metrics.get('automation_rate', {}).get('delta', 0), 
         metrics.get('automation_rate', {}).get('insight', 'AI efficiency'), "🤖"),
        
        ("Active Models", f"{metrics.get('active_model_ratio', {}).get('value', 0):.1f}%", 
         metrics.get('active_model_ratio', {}).get('delta', 0), 
         metrics.get('active_model_ratio', {}).get('insight', 'Portfolio usage'), "👥")
    ]
    
    # Render tiles in rows of 3
    for i in range(0, len(kpi_configs), 3):
        row_cols = st.columns(3)
        for j, col in enumerate(row_cols):
            if i + j < len(kpi_configs):
                title, value, delta, insight, icon = kpi_configs[i + j]
                with col:
                    st.markdown(render_kpi_tile(title, value, delta, insight, icon), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def navigate_to_athena(model_ids: list = None, client_ids: list = None,
                      context_intent: str = "general", brief_text: str = None):
    """Navigate to Athena tab with comprehensive preloaded context."""

    # Set selected models/clients
    if model_ids:
        st.session_state["selected_models"] = model_ids
        st.success(f"✅ Selected {len(model_ids)} models for Athena")
    if client_ids:
        st.session_state["selected_clients"] = client_ids
        st.success(f"✅ Selected {len(client_ids)} clients for Athena")

    # Set context intent for Athena to understand the purpose
    st.session_state["context_intent"] = context_intent

    # Set prefill data for Athena
    athena_prefill = {}

    if context_intent == "promote" and model_ids:
        athena_prefill = {
            "brief": brief_text or f"Promote {len(model_ids)} top-performing models for upcoming campaigns",
            "subject": f"Model Promotion Recommendation - {len(model_ids)} Models",
            "priority": "high",
            "campaign_type": "promotion"
        }
    elif context_intent == "vip_update" and client_ids:
        athena_prefill = {
            "brief": brief_text or f"VIP client portfolio update for {len(client_ids)} premium clients",
            "subject": f"VIP Client Portfolio Update - {len(client_ids)} Clients",
            "priority": "high",
            "campaign_type": "client_relations"
        }
    elif context_intent == "churn_prevention" and client_ids:
        athena_prefill = {
            "brief": brief_text or f"Re-engagement strategy for {len(client_ids)} at-risk clients",
            "subject": f"Client Re-engagement Campaign - {len(client_ids)} Clients",
            "priority": "urgent",
            "campaign_type": "retention"
        }
    elif context_intent == "inactive_models" and model_ids:
        athena_prefill = {
            "brief": brief_text or f"Reactivation campaign for {len(model_ids)} inactive models",
            "subject": f"Model Reactivation Strategy - {len(model_ids)} Models",
            "priority": "medium",
            "campaign_type": "reactivation"
        }

    st.session_state["athena_prefill"] = athena_prefill

    # Note: Tab switching in Streamlit requires manual user interaction
    st.info("💡 Switch to the **Athena** tab to continue with your selection.")

    # Store the navigation intent
    st.session_state["apollo_navigation"] = "athena"

def get_client_churn_risk(data: dict) -> pd.DataFrame:
    """Calculate client churn risk based on days since last booking."""
    if data['bookings'].empty or data['clients'].empty:
        return pd.DataFrame()

    # Get last booking date for each client
    last_bookings = data['bookings'].groupby('client_id')['confirmed_date'].max().reset_index()
    last_bookings['days_since_booking'] = (datetime.now() - last_bookings['confirmed_date']).dt.days

    # Merge with client info
    churn_risk = last_bookings.merge(data['clients'], on='client_id', how='left')
    churn_risk = churn_risk.sort_values('days_since_booking', ascending=False)

    return churn_risk

def render_churn_risk_chart(churn_data: pd.DataFrame):
    """Render client churn risk bar chart."""
    if churn_data.empty:
        return

    # Create risk categories
    churn_data['risk_level'] = pd.cut(
        churn_data['days_since_booking'],
        bins=[0, 30, 60, 90, float('inf')],
        labels=['Low', 'Medium', 'High', 'Critical']
    )

    # Create bar chart
    fig = px.bar(
        churn_data.head(10),
        x='client_name',
        y='days_since_booking',
        color='risk_level',
        color_discrete_map={
            'Low': '#00FF88',
            'Medium': '#FFD700',
            'High': '#FF8800',
            'Critical': '#FF4444'
        },
        title="Days Since Last Booking"
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_color='#2EF0FF',
        xaxis_title="Client",
        yaxis_title="Days Since Last Booking",
        showlegend=True
    )

    fig.add_hline(y=90, line_dash="dash", line_color="#FF4444",
                  annotation_text="Churn Risk Threshold", annotation_position="top right")

    st.plotly_chart(fig, use_container_width=True)

def render_agent_productivity_scatter(data: dict):
    """Render agent productivity scatter plot."""
    if data['bookings'].empty:
        st.info("No booking data available for productivity analysis.")
        return

    # Calculate agent metrics
    agent_metrics = data['bookings'].groupby('agent').agg({
        'booking_id': 'count',
        'time_to_book_days': 'mean',
        'athena_assisted': 'mean'
    }).reset_index()

    agent_metrics.columns = ['agent', 'total_bookings', 'avg_time_to_book', 'automation_usage']
    agent_metrics['automation_usage'] *= 100  # Convert to percentage

    # Create scatter plot
    fig = px.scatter(
        agent_metrics,
        x='total_bookings',
        y='avg_time_to_book',
        size='automation_usage',
        color='automation_usage',
        hover_name='agent',
        color_continuous_scale='Viridis',
        title="Agent Performance: Bookings vs Speed"
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_color='#2EF0FF',
        xaxis_title="Total Bookings",
        yaxis_title="Avg Time to Book (days)",
        coloraxis_colorbar_title="Automation Usage %"
    )

    st.plotly_chart(fig, use_container_width=True)

def calculate_hours_saved(data: dict) -> float:
    """Calculate hours saved through Athena automation."""
    if data['bookings'].empty:
        return 0.0

    # Get recent bookings (last 7 days)
    recent_cutoff = datetime.now() - timedelta(days=7)
    recent_bookings = data['bookings'][
        data['bookings']['confirmed_date'] >= recent_cutoff
    ] if 'confirmed_date' in data['bookings'].columns else pd.DataFrame()

    if recent_bookings.empty:
        return 0.0

    # Calculate time savings (assume 2 hours saved per Athena-assisted booking)
    athena_bookings = recent_bookings['athena_assisted'].sum()
    hours_saved = athena_bookings * 2.0  # 2 hours saved per automated booking

    return hours_saved

def generate_predictive_insights(data: dict) -> list:
    """Generate predictive insights from Athena events data."""
    insights = []

    if not data['athena_events'].empty:
        # Analyze trending filters
        recent_events = data['athena_events'][
            data['athena_events']['timestamp'] >= (datetime.now() - timedelta(days=30))
        ] if 'timestamp' in data['athena_events'].columns else pd.DataFrame()

        if not recent_events.empty:
            # Extract trending attributes from filters
            filter_trends = recent_events['filters_used'].value_counts().head(3)

            for i, (filter_text, count) in enumerate(filter_trends.items()):
                if 'brown hair' in filter_text.lower() and 'green eyes' in filter_text.lower():
                    insights.append({
                        'icon': '📌',
                        'title': 'Demand Surge',
                        'description': 'Luxury campaigns favor brown hair + green eyes this month.',
                        'action': 'Promote matching models',
                        'cta_type': 'promote'
                    })
                elif 'blonde' in filter_text.lower() and 'blue eyes' in filter_text.lower():
                    insights.append({
                        'icon': '📈',
                        'title': 'Classic Appeal',
                        'description': 'Blonde + blue eyes combination trending in beauty campaigns.',
                        'action': 'Prioritize classic looks',
                        'cta_type': 'promote'
                    })
                elif 'runway' in filter_text.lower() or 'editorial' in filter_text.lower():
                    insights.append({
                        'icon': '🏃‍♀️',
                        'title': 'Q1 Forecast',
                        'description': 'Runway demand +24% in Paris & Milan.',
                        'action': 'Prioritize tall editorial division',
                        'cta_type': 'scout'
                    })

    # Add default insights if no data
    if not insights:
        insights = [
            {
                'icon': '📊',
                'title': 'Market Analysis',
                'description': 'Seasonal trends indicate increased demand for diverse casting.',
                'action': 'Expand portfolio diversity',
                'cta_type': 'scout'
            },
            {
                'icon': '🎯',
                'title': 'Optimization Opportunity',
                'description': 'Automation can reduce booking time by 40-60%.',
                'action': 'Increase Athena usage',
                'cta_type': 'promote'
            }
        ]

    return insights[:2]  # Limit to 2 insights for performance

def render_insight_card(insight: dict, index: int, data: dict = None):
    """Render a single predictive insight card with model thumbnails."""
    try:
        # Validate insight structure and provide defaults
        icon = insight.get('icon', '💡')
        title = insight.get('title', 'Insight')
        description = insight.get('description', 'No description available')
        action = insight.get('action', 'Take action')
        cta_type = insight.get('cta_type', 'promote')

        cta_color = "#2EF0FF" if cta_type == 'promote' else "#00FF88"
        cta_text = "Promote (Athena)" if cta_type == 'promote' else "Scout (Artemis)"

        st.markdown(f"""
        <div class="premium-card" style="margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 2rem; margin-right: 1rem;">{icon}</span>
                <h4 style="color: #2EF0FF; margin: 0;">{title}</h4>
            </div>
            <p style="color: #E0E0E0; margin-bottom: 1rem; line-height: 1.5;">{description}</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #B0B0B0; font-size: 0.9rem;">→ {action}</span>
                <button class="apollo-cta" style="background: {cta_color};" onclick="alert('Navigating to {cta_text}...')">{cta_text}</button>
            </div>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        # Fallback card if there's an error
        st.markdown(f"""
        <div class="premium-card" style="margin-bottom: 1rem; border: 1px solid #FF4444;">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 2rem; margin-right: 1rem;">⚠️</span>
                <h4 style="color: #FF4444; margin: 0;">Insight Error</h4>
            </div>
            <p style="color: #E0E0E0; margin-bottom: 1rem; line-height: 1.5;">Unable to load insight data properly.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Add matching model thumbnails if data available
    try:
        if data and isinstance(data, dict) and 'models' in data and not data['models'].empty:
            # Get matching models based on insight type
            matching_models = []
            cta_type = insight.get('cta_type', 'promote')

            if cta_type == 'promote':
                # Get top performers
                if 'performance' in data and not data['performance'].empty:
                    try:
                        top_models = data['performance'].merge(
                            data['models'], on='model_id', how='left'
                        ).sort_values('revenue_total_usd', ascending=False).head(2)
                        matching_models = top_models.to_dict('records')
                    except Exception:
                        # Fallback to random models if merge fails
                        matching_models = data['models'].sample(min(2, len(data['models']))).to_dict('records')
            else:
                # Get random sample for scouting
                matching_models = data['models'].sample(min(2, len(data['models']))).to_dict('records')

            if matching_models and len(matching_models) > 0:
                st.markdown("**Matching Models:**")
                thumb_cols = st.columns(min(2, len(matching_models)))

                for i, model in enumerate(matching_models):
                    if isinstance(model, dict) and 'model_id' in model:
                        with thumb_cols[i]:
                            # Clickable thumbnail that adds to selection
                            if st.button("📌", key=f"select_insight_{index}_{i}",
                                       help=f"Select {model.get('name', 'Model')}"):
                                if 'selected_models' not in st.session_state:
                                    st.session_state['selected_models'] = []
                                if model['model_id'] not in st.session_state['selected_models']:
                                    st.session_state['selected_models'].append(model['model_id'])
                                    st.success(f"Added {model.get('name', 'Model')} to selection!")

                            # REFACTORED: Simple HTTPS thumbnail rendering
                            render_apollo_thumbnail(model, width=180, key_suffix=f"insight_{index}_{i}")
                            st.markdown("""
                            <div style="
                                width: 120px;
                                height: 150px;
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                border-radius: 8px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                color: white;
                                font-size: 2rem;
                                border: 1px solid rgba(46, 240, 255, 0.3);
                            ">
                                📷
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="
                            width: 120px;
                            height: 150px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            border-radius: 8px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-size: 2rem;
                            border: 1px solid rgba(46, 240, 255, 0.3);
                        ">
                            👤
                        </div>
                        """, unsafe_allow_html=True)

                        st.caption(model.get('name', 'Unknown')[:15])  # Show more characters

    except Exception as e:
        # Silently handle thumbnail errors to prevent raw data display
        pass

    # Add actual button functionality with standardized styling
    try:
        cta_type = insight.get('cta_type', 'promote')
        cta_text = "Promote (Athena)" if cta_type == 'promote' else "Scout (Artemis)"
        button_class = "apollo-btn" if cta_type == 'promote' else "apollo-btn-secondary"

        st.markdown(
            f"<button class='{button_class}'>{cta_text}</button>",
            unsafe_allow_html=True
        )
        if st.button("", key=f"insight_{index}"):
            if cta_type == 'promote':
                navigate_to_athena()
            else:
                st.info("Artemis scouting feature coming soon!")
    except Exception:
        # Fallback button with standardized styling
        st.markdown(
            f"<button class='apollo-btn-secondary'>View Details</button>",
            unsafe_allow_html=True
        )
        if st.button("", key=f"insight_fallback_{index}"):
            st.info("Feature coming soon!")



def render_enhanced_model_details_modal(model_data: dict):
    """Render enhanced model details modal with external intelligence data."""
    if not model_data:
        return

    # Modal styling
    st.markdown("""
    <style>
    .modal-container {
        background: linear-gradient(135deg, #1A1A1F 0%, #2A2A35 100%);
        border: 2px solid #2EF0FF;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
    }
    .modal-header {
        color: #2EF0FF;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-align: center;
    }
    .intel-metric {
        background: rgba(46, 240, 255, 0.1);
        border-left: 3px solid #2EF0FF;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .modal-actions {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Modal container
    st.markdown('<div class="modal-container">', unsafe_allow_html=True)

    # Header
    st.markdown(f'<div class="modal-header">📊 {model_data.get("name", "Unknown Model")} - Intelligence Profile</div>',
                unsafe_allow_html=True)

    # Two-column layout
    col1, col2 = st.columns([1, 2])

    with col1:
        # Full-size model image
        https_image_handler.render_model_thumbnail(model_data, width=300)

    with col2:
        # Basic info
        st.markdown(f"**Region:** {model_data.get('region', 'Unknown')}")
        st.markdown(f"**Division:** {model_data.get('division', 'Unknown').upper()}")
        st.markdown(f"**Category Focus:** {model_data.get('category_focus', 'General')}")

        # External intelligence metrics
        st.markdown("### 🧠 Intelligence Metrics")

        # Exposure velocity
        exposure_vel = model_data.get('exposure_velocity', 0)
        st.markdown(f"""
        <div class="intel-metric">
            <strong>🚀 Exposure Velocity:</strong> {exposure_vel:.1%}<br>
            <small>Market momentum and visibility growth</small>
        </div>
        """, unsafe_allow_html=True)

        # Engagement rate
        engagement = model_data.get('engagement_rate', 0)
        st.markdown(f"""
        <div class="intel-metric">
            <strong>💫 Engagement Rate:</strong> {engagement:.1f}%<br>
            <small>Social media audience interaction</small>
        </div>
        """, unsafe_allow_html=True)

        # Sentiment score
        sentiment = model_data.get('sentiment_score', 0)
        sentiment_color = "#00FF88" if sentiment > 0 else "#FF4444" if sentiment < 0 else "#FFD700"
        st.markdown(f"""
        <div class="intel-metric">
            <strong>😊 Sentiment Score:</strong> <span style="color: {sentiment_color}">{sentiment:.2f}</span><br>
            <small>Public perception and brand safety</small>
        </div>
        """, unsafe_allow_html=True)

        # Booking probability
        booking_prob = model_data.get('booking_probability', 0)
        st.markdown(f"""
        <div class="intel-metric">
            <strong>📈 Booking Probability:</strong> {booking_prob:.1%}<br>
            <small>Predicted likelihood of successful bookings</small>
        </div>
        """, unsafe_allow_html=True)

    # Action buttons
    st.markdown('<div class="modal-actions">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"<button class='apollo-btn'>🎯 Promote via Athena</button>",
            unsafe_allow_html=True
        )
        if st.button("", key="modal_promote_athena"):
            st.session_state["apollo_selected_models"] = [str(model_data.get('model_id', ''))]
            st.session_state["apollo_selection_reason"] = "modal_promotion"
            st.success("✅ Queued for Athena")

    with col2:
        st.markdown(
            f"<button class='apollo-btn-secondary' style='opacity: 0.5; cursor: not-allowed;'>🎭 Queue for Artemis</button>",
            unsafe_allow_html=True
        )
        if st.button("", key="modal_queue_artemis", disabled=True):
            st.info("Coming soon...")

    with col3:
        st.markdown(
            f"<button class='apollo-btn-secondary'>📚 View in Catalogue</button>",
            unsafe_allow_html=True
        )
        if st.button("", key="modal_view_catalogue"):
            st.info("🔄 Redirecting to Catalogue...")

    with col4:
        st.markdown(
            f"<button class='apollo-btn-danger'>❌ Close</button>",
            unsafe_allow_html=True
        )
        if st.button("", key="modal_close"):
            st.session_state['show_model_modal'] = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_model_quick_view_modal(model_data: dict, bookings_data: pd.DataFrame,
                                 performance_data: pd.DataFrame):
    """Render the model quick-view modal with all details and CTAs."""
    if not model_data:
        return

    # Modal styling
    st.markdown("""
    <style>
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .modal-content {
        background: linear-gradient(135deg, #1A1A1F 0%, #2A2A35 100%);
        border: 2px solid #2EF0FF;
        border-radius: 15px;
        padding: 2rem;
        max-width: 600px;
        max-height: 80vh;
        overflow-y: auto;
        position: relative;
    }
    .modal-close {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: none;
        border: none;
        color: #2EF0FF;
        font-size: 1.5rem;
        cursor: pointer;
    }
    .modal-image {
        width: 200px;
        height: 250px;
        object-fit: cover;
        border-radius: 10px;
        border: 2px solid rgba(46, 240, 255, 0.3);
    }
    .modal-section {
        margin: 1.5rem 0;
        padding: 1rem;
        background: rgba(46, 240, 255, 0.05);
        border-radius: 8px;
        border-left: 3px solid #2EF0FF;
    }
    .modal-cta {
        background: linear-gradient(135deg, #2EF0FF 0%, #00D4FF 100%);
        color: #0D0D0F;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        cursor: pointer;
        margin: 0.5rem;
        transition: all 0.3s ease;
    }
    .modal-cta:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(46, 240, 255, 0.4);
    }
    .modal-cta.secondary {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
    }
    </style>
    """, unsafe_allow_html=True)

    # Modal container
    with st.container():
        col1, col2 = st.columns([1, 2])

        with col1:
            # High-quality model image with proper aspect ratio
            thumbnail_path = model_data.get('primary_thumbnail')
            if not thumbnail_path:
                thumbnail_path = apollo_image_handler.get_primary_thumbnail(model_data)

            # Display model image with ultra-high quality and proper aspect ratio
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    from PIL import Image, ImageOps, ImageEnhance
                    # Load image with maximum quality settings
                    img = Image.open(thumbnail_path)

                    # Enhance image quality for modal display
                    if img.mode != 'RGB':
                        img = img.convert('RGB')

                    # Enhance sharpness and contrast for crisp modal display
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(1.2)  # Slight sharpness boost

                    # Resize to optimal modal size with high-quality resampling
                    # Use larger size for modal display (up to 400px width)
                    max_width, max_height = 400, 500
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                    # Use container with CSS for better image handling
                    st.markdown("""
                    <style>
                    .modal-image-container {
                        width: 100%;
                        max-width: 400px;
                        margin: 0 auto;
                    }
                    .modal-image-container img {
                        width: 100%;
                        height: auto;
                        max-height: 500px;
                        object-fit: contain;
                        border-radius: 12px;
                        border: 2px solid rgba(46, 240, 255, 0.3);
                        box-shadow: 0 8px 25px rgba(46, 240, 255, 0.2);
                        image-rendering: -webkit-optimize-contrast;
                        image-rendering: crisp-edges;
                    }
                    </style>
                    <div class="modal-image-container">
                    """, unsafe_allow_html=True)

                    st.image(img, caption="", use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                except Exception as e:
                    st.markdown(
                        f"""
                        <div style="
                            width: 100%;
                            max-width: 350px;
                            height: 450px;
                            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                            border: 2px solid #4a5568;
                            border-radius: 12px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: #a0aec0;
                            font-size: 2rem;
                            font-weight: bold;
                            margin: 0 auto;
                            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                        ">
                            📷<br><small style="font-size: 0.8rem;">Image Error</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.markdown(
                    """
                    <div style="
                        width: 100%;
                        max-width: 350px;
                        height: 450px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border: 2px solid rgba(46, 240, 255, 0.3);
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 3rem;
                        font-weight: bold;
                        margin: 0 auto;
                        box-shadow: 0 8px 25px rgba(46, 240, 255, 0.2);
                    ">
                        👤<br><small style="font-size: 0.6rem;">No Image Available</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col2:
            # Model details
            st.markdown(f"### {model_data.get('name', 'Unknown Model')}")
            st.markdown(f"**Division:** {model_data.get('division', 'N/A').upper()}")

            # Measurements & attributes
            st.markdown("#### 📏 Measurements & Attributes")

            measurements_col1, measurements_col2 = st.columns(2)
            with measurements_col1:
                st.markdown(f"**Height:** {int(model_data.get('height_cm', 0)) if model_data.get('height_cm') != 'N/A' else 'N/A'} cm")
                st.markdown(f"**Hair:** {model_data.get('hair_color', 'N/A').title()}")
            with measurements_col2:
                st.markdown(f"**Eyes:** {model_data.get('eye_color', 'N/A').title()}")
                # Add additional measurements if available
                if model_data.get('bust'):
                    st.markdown(f"**Bust:** {model_data['bust']}")
                if model_data.get('waist'):
                    st.markdown(f"**Waist:** {model_data['waist']}")
                if model_data.get('hips'):
                    st.markdown(f"**Hips:** {model_data['hips']}")

        # Recent bookings section
        st.markdown("#### 📅 Last 3 Bookings")
        model_id = model_data.get('model_id')

        if not bookings_data.empty and model_id:
            model_bookings = bookings_data[bookings_data['model_id'] == model_id]
            recent_bookings = model_bookings.sort_values('confirmed_date', ascending=False).head(3)

            if not recent_bookings.empty:
                for _, booking in recent_bookings.iterrows():
                    booking_date = booking.get('confirmed_date', 'N/A')
                    if pd.notna(booking_date):
                        booking_date = booking_date.strftime('%Y-%m-%d')

                    st.markdown(f"""
                    <div style="background: rgba(46, 240, 255, 0.1); padding: 0.5rem; margin: 0.5rem 0; border-radius: 5px;">
                        <strong>{booking_date}</strong> • {booking.get('client_id', 'Unknown Client')} •
                        ${booking.get('revenue_usd', 0):,.0f} • {booking.get('campaign_type', 'Campaign')}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent bookings found")
        else:
            st.info("Booking data not available")

        # KPIs section
        st.markdown("#### 📊 Key Performance Indicators")

        if not performance_data.empty and model_id:
            model_perf = performance_data[performance_data['model_id'] == model_id]
            if not model_perf.empty:
                perf = model_perf.iloc[0]

                kpi_col1, kpi_col2 = st.columns(2)
                with kpi_col1:
                    st.metric("Rebook Rate", f"{perf.get('rebook_rate_pct', 0):.1f}%")
                    st.metric("Total Revenue", f"${perf.get('revenue_total_usd', 0):,.0f}")
                with kpi_col2:
                    st.metric("Conversion Rate", f"{perf.get('casting_to_booking_conversion_pct', 0):.1f}%")
                    st.metric("Total Bookings", f"{perf.get('total_bookings', 0)}")
            else:
                st.info("Performance data not available")
        else:
            st.info("Performance data not available")

        # CTAs
        st.markdown("#### 🎯 Actions")
        cta_col1, cta_col2 = st.columns(2)

        with cta_col1:
            st.markdown(
                f"<button class='apollo-btn'>📩 Promote via Athena</button>",
                unsafe_allow_html=True
            )
            if st.button("", key=f"promote_modal_{model_id}"):
                # Set session state for Athena
                st.session_state["selected_models"] = [model_id]
                st.session_state["context_intent"] = "promote"
                st.session_state["athena_prefill"] = {
                    "brief": f"Promote {model_data.get('name')} for upcoming campaigns",
                    "subject": f"Model Recommendation: {model_data.get('name')}",
                    "images": [model_data.get('primary_thumbnail', '')]
                }
                st.success(f"✅ {model_data.get('name')} selected for Athena promotion")
                st.info("💡 Switch to the **Athena** tab to continue")

        with cta_col2:
            st.markdown(
                f"<button class='apollo-btn-secondary'>👁️ View Full Profile</button>",
                unsafe_allow_html=True
            )
            if st.button("", key=f"catalogue_modal_{model_id}"):
                st.session_state["selected_model"] = model_id
                st.session_state["active_tab"] = "Catalogue"
                st.info("💡 Switch to the **Catalogue** tab to view full profile")

def show_model_quick_view_modal():
    """Check if modal should be shown and render it."""
    if st.session_state.get('show_model_modal') and st.session_state.get('modal_model_data'):
        try:
            # Use the enhanced modal with external intelligence data
            render_enhanced_model_details_modal(st.session_state['modal_model_data'])

        except Exception as e:
            st.error(f"Error loading modal data: {e}")
            st.session_state['show_model_modal'] = False
            st.session_state['modal_model_data'] = None

def render_interactive_model_thumbnail(model_data: dict):
    """Render interactive model thumbnail with high-quality images and proper aspect ratios."""
    # Get the best available image path
    thumbnail_path = model_data.get('primary_thumbnail')
    if not thumbnail_path:
        thumbnail_path = apollo_image_handler.get_primary_thumbnail(model_data)

    # Container with proper aspect ratio
    st.markdown(f"""
    <div style="
        border: 1px solid #333;
        border-radius: 12px;
        padding: 1rem;
        background: linear-gradient(135deg, #1A1A1F 0%, #2A2A35 100%);
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
        max-width: 280px;
        margin: 0 auto;
    " onmouseover="this.style.transform='scale(1.02)'; this.style.borderColor='#667eea';"
       onmouseout="this.style.transform='scale(1)'; this.style.borderColor='#333';">
    """, unsafe_allow_html=True)

    # Ultra-high-quality image with proper aspect ratio and sharpness
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            from PIL import Image, ImageOps, ImageEnhance
            # Load image with maximum quality settings
            img = Image.open(thumbnail_path)

            # Enhance image quality for interactive display
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Apply sharpness enhancement for crisp display
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)  # Subtle sharpness boost

            # Resize with high-quality resampling for ultra-sharp display
            target_size = (250, 320)  # Increased from 200px to 250px for maximum clarity
            img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)

            # Display with proper aspect ratio and quality
            st.image(
                img,
                width=250,  # Increased from 200 to 250 for ultra-sharp display
                caption="",
                use_container_width=False
            )
        except Exception:
            # Fallback with proper dimensions
            st.markdown(f"""
            <div style="
                width: 200px;
                height: 250px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 8px;
                margin: 0 auto 1rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 3rem;
                color: white;
            ">
                👤
            </div>
            """, unsafe_allow_html=True)
    else:
        # Fallback placeholder with proper dimensions
        st.markdown(f"""
        <div style="
            width: 200px;
            height: 250px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            margin: 0 auto 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: white;
        ">
            👤
        </div>
        """, unsafe_allow_html=True)

    # Model info
    st.markdown(f"""
    <div style="color: white; padding: 0.5rem;">
        <h4 style="margin: 0.5rem 0; color: white;">{model_data['name']}</h4>
        <p style="color: #ccc; font-size: 0.9rem; margin: 0.25rem 0;">{model_data['division'].upper()}</p>
        <div style="display: flex; justify-content: space-around; margin-top: 1rem; font-size: 0.8rem;">
            <span style="color: #00FF88;">📊 {model_data.get('bookings', 'N/A')}</span>
            <span style="color: #2EF0FF;">💰 {model_data.get('revenue', 'N/A')}</span>
            <span style="color: #FFD700;">⭐ {model_data.get('rating', 'N/A')}</span>
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Action buttons with standardized styling
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"<button class='apollo-btn-secondary' style='width: 100%;'>👁️ Quick View</button>",
            unsafe_allow_html=True
        )
        if st.button("", key=f"apollo_quick_{model_data['model_id']}"):
            st.session_state.show_model_modal = True
            st.session_state.modal_model_data = model_data
            st.rerun()

    with col2:
        st.markdown(
            f"<button class='apollo-btn' style='width: 100%;'>🎯 Promote</button>",
            unsafe_allow_html=True
        )
        if st.button("", key=f"apollo_promote_{model_data['model_id']}"):
            # Transfer to Athena
            try:
                from session_manager import SessionManager
                SessionManager.transfer_model_to_athena(model_data, "Apollo")
            except ImportError:
                st.session_state["apollo_selected_models"] = [str(model_data['model_id'])]
                st.session_state["apollo_selection_reason"] = "apollo_promotion"
                st.success("✅ Queued for Athena")
            st.rerun()

def render_simple_insight_card(title: str, content: str, description: str, card_type: str = "info"):
    """Render simple predictive insight card (alternative function)."""
    colors = {
        "positive": {"bg": "#1B4332", "border": "#00FF88", "icon": "📈"},
        "info": {"bg": "#1A1A2E", "border": "#2EF0FF", "icon": "💡"},
        "warning": {"bg": "#3D2914", "border": "#FFD700", "icon": "⚠️"}
    }

    color_scheme = colors.get(card_type, colors["info"])

    st.markdown(f"""
    <div style="
        background: {color_scheme['bg']};
        border: 2px solid {color_scheme['border']};
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: white;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{color_scheme['icon']}</span>
            <h3 style="margin: 0; color: white;">{title}</h3>
        </div>
        <p style="font-size: 1.1rem; margin: 0.5rem 0; color: white;">{content}</p>
        <p style="font-size: 0.9rem; opacity: 0.8; margin: 0; color: #ccc;">{description}</p>
    </div>
    """, unsafe_allow_html=True)

def render_emerging_talent_section(merged_models: pd.DataFrame):
    """Render the Emerging Talent section with model cards."""
    with st.container():
        st.markdown('<h3 class="section-header">🌟 Emerging Talent</h3>', unsafe_allow_html=True)

        # Filter models with external intelligence data
        talent_models = merged_models[merged_models['exposure_velocity'].notna()].copy()

        if talent_models.empty:
            st.info("No emerging talent data available")
            return

        # Apply regional filter if active
        region_filter = st.session_state.get("apollo_filter_region")
        if region_filter:
            talent_models = talent_models[talent_models['region'] == region_filter]
            st.info(f"🌍 Filtered to {region_filter} region")

        # Sort by exposure_velocity descending
        talent_models = talent_models.sort_values(by='exposure_velocity', ascending=False)

        # Display top models in card grid (3 per row)
        display_count = min(9, len(talent_models))  # Show up to 9 models
        top_talent = talent_models.head(display_count)

        # Create grid layout
        for i in range(0, len(top_talent), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(top_talent):
                    model = top_talent.iloc[i + j]
                    render_talent_card(model, col, i + j)

def render_talent_card(model: pd.Series, col, index: int):
    """Render individual talent card."""
    with col:
        # Card container
        st.markdown(f"""
        <div style="
            border: 1px solid #2EF0FF;
            border-radius: 12px;
            padding: 1rem;
            background: linear-gradient(135deg, #1A1A1F 0%, #2A2A35 100%);
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        ">
        """, unsafe_allow_html=True)

        # Model thumbnail
        model_data = model.to_dict()
        https_image_handler.render_model_thumbnail(model_data, width=200)

        # Model info
        st.markdown(f"**{model['name']}**")
        st.markdown(f"📍 {model.get('region', 'Unknown')} • {model.get('category_focus', 'General')}")

        # Metrics
        exposure_vel = model.get('exposure_velocity', 0)
        booking_prob = model.get('booking_probability', 0)
        engagement = model.get('engagement_rate', 0)
        sentiment = model.get('sentiment_score', 0)

        # Format metrics
        st.markdown(f"🚀 **Exposure Velocity:** {exposure_vel:.1%}")
        st.markdown(f"📈 **Booking Probability:** {booking_prob:.1%}")
        st.markdown(f"💫 **Engagement:** {engagement:.1f}%")

        # Sentiment with color coding
        sentiment_color = "#00FF88" if sentiment > 0 else "#FF4444" if sentiment < 0 else "#FFD700"
        st.markdown(f'<span style="color: {sentiment_color}">😊 **Sentiment:** {sentiment:.2f}</span>',
                   unsafe_allow_html=True)

        # Action buttons with standardized styling
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👁️ View Details", key=f"talent_details_{model['model_id']}"):
                st.session_state['show_model_modal'] = True
                st.session_state['modal_model_data'] = model_data
                st.rerun()

        with col2:
            if st.button("🎯 Promote via Athena", key=f"talent_promote_{model['model_id']}"):
                st.session_state["apollo_selected_models"] = [str(model['model_id'])]
                st.session_state["apollo_selection_reason"] = "apollo_intel_signal"
                st.success("✅ Queued for Athena")

        # View in Catalogue button
        if st.button("📚 View in Catalogue", key=f"talent_catalogue_{model['model_id']}"):
            st.info("🔄 Redirecting to Catalogue...")

        st.markdown('</div>', unsafe_allow_html=True)

def render_brand_opportunity_section(merged_models: pd.DataFrame):
    """Render the Brand Opportunity Feed section."""
    with st.container():
        st.markdown('<h3 class="section-header">🎯 Brand Opportunity Feed</h3>', unsafe_allow_html=True)

        # Filter models with positive sentiment and brand mentions
        opportunity_models = merged_models[
            (merged_models['sentiment_score'] > 0) &
            (merged_models['brand_mentions_30d'] > 0) &
            (merged_models['category_focus'].notna())
        ].copy()

        if opportunity_models.empty:
            st.info("No brand opportunities identified")
            return

        # Group by category_focus
        categories = opportunity_models['category_focus'].unique()

        for category in categories[:4]:  # Show top 4 categories
            category_models = opportunity_models[
                opportunity_models['category_focus'] == category
            ].sort_values(by='sentiment_score', ascending=False)

            if len(category_models) >= 1:  # Need at least 1 model
                render_opportunity_card(category, category_models.head(3))

def render_opportunity_card(category: str, models: pd.DataFrame):
    """Render individual opportunity card."""
    st.markdown(f"""
    <div style="
        border: 1px solid #FFD700;
        border-radius: 12px;
        padding: 1.5rem;
        background: linear-gradient(135deg, #2A2A35 0%, #1A1A1F 100%);
        margin-bottom: 1rem;
    ">
        <h4 style="color: #FFD700; margin-bottom: 1rem;">💼 {category}</h4>
    </div>
    """, unsafe_allow_html=True)

    # Show candidate thumbnails
    cols = st.columns(min(3, len(models)))
    for i, (_, model) in enumerate(models.iterrows()):
        if i < 3:  # Max 3 thumbnails
            with cols[i]:
                model_data = model.to_dict()
                https_image_handler.render_model_thumbnail(model_data, width=120)
                st.caption(f"{model['name']}")

    # Generate rationale
    avg_sentiment = models['sentiment_score'].mean()
    avg_mentions = models['brand_mentions_30d'].mean()

    rationale = f"High sentiment ({avg_sentiment:.2f}) + increasing mentions ({avg_mentions:.0f}/month)"
    st.markdown(f"**Rationale:** {rationale}")

    # Action button with standardized styling
    st.markdown(
        f"<button class='apollo-btn'>🚀 Send to Athena</button>",
        unsafe_allow_html=True
    )
    if st.button("", key=f"opportunity_{category}"):
        model_ids = [str(mid) for mid in models['model_id'].tolist()]
        st.session_state["apollo_selected_models"] = model_ids
        st.session_state["apollo_selection_reason"] = "brand_opportunity"
        st.success(f"✅ {len(model_ids)} models queued for Athena")

def render_regional_market_section(merged_models: pd.DataFrame):
    """Render the Regional Momentum section."""
    with st.container():
        st.markdown('<h3 class="section-header">🌍 Regional Market Momentum</h3>', unsafe_allow_html=True)

        # Calculate regional metrics
        regional_data = merged_models.groupby('region').agg({
            'exposure_velocity': 'mean',
            'booking_probability': 'mean',
            'model_id': 'count'
        }).reset_index()

        regional_data.columns = ['region', 'avg_exposure', 'avg_booking', 'model_count']
        regional_data = regional_data.sort_values(by='avg_exposure', ascending=False)

        if regional_data.empty:
            st.info("No regional data available")
            return

        # Create horizontal bar chart
        st.markdown("**Regional Performance Metrics**")

        for _, region_data in regional_data.iterrows():
            region = region_data['region']
            exposure = region_data['avg_exposure']
            booking = region_data['avg_booking']
            count = int(region_data['model_count'])

            # Create clickable region bar
            col1, col2 = st.columns([3, 1])

            with col1:
                # Progress bars for metrics
                st.markdown(f"**{region}** ({count} models)")
                st.progress(min(exposure, 1.0), text=f"Exposure Velocity: {exposure:.1%}")
                st.progress(min(booking, 1.0), text=f"Booking Probability: {booking:.1%}")

            with col2:
                st.markdown(
                    f"<button class='apollo-filter-btn'>🔍 Filter to {region}</button>",
                    unsafe_allow_html=True
                )
                if st.button("", key=f"region_filter_{region}"):
                    st.session_state["apollo_filter_region"] = region
                    st.rerun()

        # Clear filter button with standardized styling
        if st.session_state.get("apollo_filter_region"):
            st.markdown(
                f"<button class='apollo-btn-danger'>🌐 Clear Regional Filter</button>",
                unsafe_allow_html=True
            )
            if st.button("", key="clear_region_filter"):
                st.session_state["apollo_filter_region"] = None
                st.rerun()

def render_apollo_intel_section(merged_models: pd.DataFrame):
    """Render Apollo Intelligence Recommendations."""
    with st.container():
        st.markdown('<h3 class="section-header">🧠 Apollo Intelligence Recommendations</h3>', unsafe_allow_html=True)

        recommendations = []

        # Generate recommendations based on threshold logic
        regional_booking_avg = merged_models.groupby('region')['booking_probability'].mean()

        for region, avg_booking in regional_booking_avg.items():
            if avg_booking > 0.6:
                recommendations.append({
                    'text': f"{region} market displaying strong conversion potential.",
                    'type': 'opportunity',
                    'metric': f"{avg_booking:.1%} avg booking probability"
                })

        # High engagement opportunities
        high_engagement = merged_models[merged_models['engagement_rate'] > 5.0]
        if len(high_engagement) > 0:
            recommendations.append({
                'text': f"{len(high_engagement)} models showing exceptional engagement rates.",
                'type': 'talent',
                'metric': f"Average {high_engagement['engagement_rate'].mean():.1f}% engagement"
            })

        # Sentiment risks
        low_sentiment = merged_models[merged_models['sentiment_score'] < -0.2]
        if len(low_sentiment) > 0:
            recommendations.append({
                'text': f"{len(low_sentiment)} models require sentiment monitoring.",
                'type': 'risk',
                'metric': f"Average sentiment: {low_sentiment['sentiment_score'].mean():.2f}"
            })

        # Display recommendations
        if recommendations:
            for i, rec in enumerate(recommendations):
                icon = "🚀" if rec['type'] == 'opportunity' else "⭐" if rec['type'] == 'talent' else "⚠️"
                color = "#00FF88" if rec['type'] == 'opportunity' else "#FFD700" if rec['type'] == 'talent' else "#FF4444"

                st.markdown(f"""
                <div style="
                    border-left: 4px solid {color};
                    padding: 1rem;
                    margin: 0.5rem 0;
                    background: rgba(255,255,255,0.05);
                    border-radius: 0 8px 8px 0;
                ">
                    <p style="margin: 0; color: white;">{icon} {rec['text']}</p>
                    <small style="color: #ccc;">{rec['metric']} • {pd.Timestamp.now().strftime('%H:%M')}</small>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(
                    f"<button class='apollo-btn'>🚀 Send to Athena</button>",
                    unsafe_allow_html=True
                )
                if st.button("", key=f"intel_rec_{i}"):
                    st.session_state["apollo_selected_models"] = []
                    st.session_state["apollo_selection_reason"] = "apollo_intelligence_rec"
                    st.success("✅ Recommendation queued for Athena")
        else:
            st.info("No specific recommendations at this time")

def render_alerts_section(merged_models: pd.DataFrame):
    """Render the Alerts Feed section."""
    with st.container():
        st.markdown('<h3 class="section-header">🚨 Intelligence Alerts</h3>', unsafe_allow_html=True)

        alerts = []

        # Growth spike alerts
        growth_spikes = merged_models[merged_models['followers_growth_7d'] > 10.0]
        for _, model in growth_spikes.iterrows():
            alerts.append({
                'icon': '🔥',
                'type': 'growth',
                'message': f"{model['name']} - IG growth spike",
                'detail': f"+{model['followers_growth_7d']:.1f}% in 7 days",
                'model_id': model['model_id']
            })

        # High engagement alerts
        high_engagement = merged_models[merged_models['engagement_rate'] > 5.0]
        for _, model in high_engagement.iterrows():
            alerts.append({
                'icon': '✨',
                'type': 'engagement',
                'message': f"{model['name']} - High engagement",
                'detail': f"{model['engagement_rate']:.1f}% engagement rate",
                'model_id': model['model_id']
            })

        # Sentiment risk alerts
        sentiment_risks = merged_models[merged_models['sentiment_score'] < -0.2]
        for _, model in sentiment_risks.iterrows():
            alerts.append({
                'icon': '🔴',
                'type': 'risk',
                'message': f"{model['name']} - Sentiment risk",
                'detail': f"Sentiment score: {model['sentiment_score']:.2f}",
                'model_id': model['model_id']
            })

        # Brand mention alerts
        high_mentions = merged_models[merged_models['brand_mentions_30d'] > 5]
        for _, model in high_mentions.iterrows():
            alerts.append({
                'icon': '📣',
                'type': 'mentions',
                'message': f"{model['name']} - Elevated brand mentions",
                'detail': f"{int(model['brand_mentions_30d'])} mentions in 30 days",
                'model_id': model['model_id']
            })

        # Display alerts
        if alerts:
            # Limit to most recent/important alerts
            for alert in alerts[:8]:  # Show max 8 alerts
                color = "#FF4444" if alert['type'] == 'risk' else "#00FF88" if alert['type'] == 'growth' else "#FFD700"

                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    <div style="
                        border-left: 3px solid {color};
                        padding: 0.8rem;
                        margin: 0.3rem 0;
                        background: rgba(255,255,255,0.03);
                        border-radius: 0 6px 6px 0;
                    ">
                        <p style="margin: 0; color: white; font-size: 0.9rem;">
                            {alert['icon']} {alert['message']}
                        </p>
                        <small style="color: #aaa;">{alert['detail']}</small>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(
                        f"<button class='apollo-btn-secondary' title='View model'>👁️</button>",
                        unsafe_allow_html=True
                    )
                    if st.button("", key=f"alert_view_{alert['model_id']}"):
                        # Find the model data for modal
                        model_data = merged_models[merged_models['model_id'] == alert['model_id']].iloc[0].to_dict()
                        st.session_state['show_model_modal'] = True
                        st.session_state['modal_model_data'] = model_data
                        st.rerun()
        else:
            st.info("No alerts at this time")

def main():
    """Enhanced Apollo dashboard with interactive features and cross-assistant integration."""
    # Apply styling first - this will override main app styling
    apply_apollo_styling()

    # Show integration messages
    try:
        from session_manager import SessionManager
        from ui_components import NotificationComponents
        NotificationComponents.show_integration_messages()
    except ImportError:
        pass

    # Check for shared model context
    shared_context = st.session_state.get('shared_model_context')
    if shared_context and shared_context.get('active'):
        model_data = shared_context['model_data']
        st.info(f"🔍 Viewing analytics for: **{model_data['name']}** from {model_data['division'].upper()}")

    # Wrap everything in Apollo-themed container with no top margin
    st.markdown('<div class="apollo-dashboard" style="margin-top: 0; padding-top: 0;">', unsafe_allow_html=True)

    # Header - positioned immediately at top
    st.markdown("""
    <div class="apollo-title" style="margin-top: 0; padding-top: 0;">📊 Apollo — Agency Intelligence</div>
    <div class="apollo-subtitle">"Insights that unlock revenue opportunities"</div>
    """, unsafe_allow_html=True)
    
    # Load data
    try:
        data_loader = ApolloDataLoader()
        data = data_loader.load_all_data()
        metrics_calculator = ApolloMetrics(data)
        
        # Calculate KPI metrics
        kpi_metrics = metrics_calculator.calculate_kpi_metrics()
        
        # Render KPI Hero Section
        render_kpi_hero_section(kpi_metrics)

        # NEW INTELLIGENCE SECTIONS
        # Get merged dataset with external intelligence
        merged_models = data.get('models_merged', pd.DataFrame())

        if not merged_models.empty:
            # EMERGING TALENT SECTION
            render_emerging_talent_section(merged_models)

            # BRAND OPPORTUNITY SECTION
            render_brand_opportunity_section(merged_models)

            # REGIONAL MARKET SECTION
            render_regional_market_section(merged_models)

            # APOLLO INTEL SECTION
            render_apollo_intel_section(merged_models)

            # ALERTS SECTION
            render_alerts_section(merged_models)

        # Two-column layout for main content
        st.markdown('<div class="two-column">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<h3 class="section-header">🎭 Model Intelligence</h3>', unsafe_allow_html=True)
            
            # Top Performers Leaderboard
            top_performers = metrics_calculator.get_top_performers(10)
            if not top_performers.empty:
                st.markdown("**Top Performers Leaderboard**")

                # Limit to top 3 for performance, with option to load more
                display_count = 3
                performers_to_show = top_performers.head(display_count)

                # Create leaderboard with thumbnails
                for idx, (_, performer) in enumerate(performers_to_show.iterrows()):
                    # Get thumbnail
                    thumbnail_path = performer.get('primary_thumbnail',
                                                 apollo_image_handler.get_primary_thumbnail(performer.to_dict()))

                    # Create row with thumbnail and data
                    row_col1, row_col2 = st.columns([0.15, 0.85])

                    with row_col1:
                        # REFACTORED: Use HTTPS image rendering
                        if thumbnail_path:
                            # Create a mock model data dict for the HTTPS handler
                            mock_model = {'thumbnail_url': thumbnail_path}
                            https_image_handler.render_model_thumbnail(
                                mock_model,
                                width=64
                            )
                        else:
                            # Fallback placeholder
                            st.markdown("📷 No image available")

                        # Make thumbnail clickable for modal with standardized styling
                        st.markdown(
                            f"<button class='apollo-btn-secondary' title='Quick view {performer['name']}'>👁️</button>",
                            unsafe_allow_html=True
                        )
                        if st.button("", key=f"thumb_top_{performer['model_id']}"):
                            st.session_state['show_model_modal'] = True
                            st.session_state['modal_model_data'] = performer.to_dict()
                            st.rerun()

                    with row_col2:
                        # Model data in compact format
                        st.markdown(f"""
                        <div style="background: rgba(46, 240, 255, 0.05); padding: 0.5rem; border-radius: 8px; margin-bottom: 0.5rem;">
                            <strong style="color: #2EF0FF;">{performer['name']}</strong>
                            <span style="color: #E0E0E0;">({performer['division'].upper()})</span><br>
                            <span style="color: #00FF88;">${performer['revenue_total_usd']:,.0f}</span> •
                            <span style="color: #FFD700;">{performer['casting_to_booking_conversion_pct']:.1f}% conv</span> •
                            <span style="color: #FF8800;">{performer['rebook_rate_pct']:.1f}% rebook</span>
                        </div>
                        """, unsafe_allow_html=True)

                # Show load more button if there are more performers
                if len(top_performers) > display_count:
                    st.markdown(
                        f"<button class='apollo-btn-secondary'>📊 Load {min(5, len(top_performers) - display_count)} More Performers</button>",
                        unsafe_allow_html=True
                    )
                    if st.button("", key="load_more_performers"):
                        st.info("Feature coming soon: Expandable leaderboard view")

                st.markdown(
                    f"<button class='apollo-btn'>📩 Promote Top Models via Athena</button>",
                    unsafe_allow_html=True
                )
                if st.button("", key="promote_top"):
                    navigate_to_athena(
                        model_ids=top_performers['model_id'].tolist()[:5],
                        context_intent="promote",
                        brief_text="Promote top-performing models based on revenue and conversion metrics"
                    )
            
            # Inactive Models Alert
            inactive_models = metrics_calculator.get_inactive_models()
            if not inactive_models.empty:
                st.markdown("**⚠️ Inactive Models Alert**")
                st.markdown(f"**{len(inactive_models)} models** need attention:")

                # Display as chips with thumbnails
                for _, model in inactive_models.head(10).iterrows():
                    thumbnail_path = model.get('primary_thumbnail',
                                             apollo_image_handler.get_primary_thumbnail(model.to_dict()))

                    chip_col1, chip_col2 = st.columns([0.2, 0.8])  # Increased from [0.1, 0.9] to provide more space

                    with chip_col1:
                        # REFACTORED: Use HTTPS image rendering
                        if thumbnail_path:
                            # Create a mock model data dict for the HTTPS handler
                            mock_model = {'thumbnail_url': thumbnail_path}
                            https_image_handler.render_model_thumbnail(
                                mock_model,
                                width=48
                            )
                        else:
                            # Fallback placeholder
                            st.markdown("📷 No image available")

                        # Make thumbnail clickable for modal with standardized styling
                        st.markdown(
                            f"<button class='apollo-btn-secondary' title='Quick view {model['name']}'>👁️</button>",
                            unsafe_allow_html=True
                        )
                        if st.button("", key=f"thumb_inactive_{model['model_id']}"):
                            st.session_state['show_model_modal'] = True
                            st.session_state['modal_model_data'] = model.to_dict()
                            st.rerun()

                    with chip_col2:
                        # Model chip
                        st.markdown(f"""
                        <span style="background: rgba(255, 68, 68, 0.2); color: #FF4444;
                                     padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.8rem;
                                     margin: 0.2rem; display: inline-block; cursor: pointer;">
                            {model['name']} ({model['division'].upper()})
                        </span>
                        """, unsafe_allow_html=True)

                st.markdown(
                    f"<button class='apollo-btn-secondary'>👀 View in Catalogue</button>",
                    unsafe_allow_html=True
                )
                if st.button("", key="view_inactive"):
                    st.session_state["active_tab"] = "Catalogue"
                    st.rerun()
        
        with col2:
            st.markdown('<h3 class="section-header">👑 Client & Brand Health</h3>', unsafe_allow_html=True)

            # VIP Client Cards
            vip_clients = metrics_calculator.get_vip_clients()
            if not vip_clients.empty:
                st.markdown("**VIP Client Portfolio**")

                for _, client in vip_clients.head(3).iterrows():
                    revenue = client.get('revenue_usd', 0)
                    bookings = client.get('total_bookings', 0)
                    client_id = client.get('client_id')

                    # Get top model thumbnails for this client (reduced to 2 for performance)
                    client_thumbnails = apollo_model_cache.get_model_thumbnails_for_client(
                        data['models'], data['bookings'], client_id, limit=2
                    )

                    # Simplified - no complex thumbnail strips

                    st.markdown(f"""
                    <div class="premium-card vip-card">
                        <h4 style="color: #FFD700; margin-bottom: 0.5rem;">{client['client_name']}</h4>
                        <p style="color: #E0E0E0; margin-bottom: 0.5rem;">{client.get('industry', 'Fashion')} • {client.get('region', 'Global')}</p>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                            <span style="color: #FFFFFF;"><strong>${revenue:,.0f}</strong> Revenue</span>
                            <span style="color: #FFFFFF;"><strong>{bookings}</strong> Bookings</span>
                        </div>

                    </div>
                    """, unsafe_allow_html=True)

                    # Show high-quality thumbnails in a simple row if available
                    if client_thumbnails:
                        st.markdown("**Top Models:**")
                        thumb_cols = st.columns(min(len(client_thumbnails), 3))
                        for i, thumb_path in enumerate(client_thumbnails[:3]):
                            with thumb_cols[i]:
                                # REFACTORED: Use HTTPS image rendering
                                if thumb_path:
                                    # Create a mock model data dict for the HTTPS handler
                                    mock_model = {'thumbnail_url': thumb_path}
                                    https_image_handler.render_model_thumbnail(
                                        mock_model,
                                        width=64
                                    )
                                else:
                                    # Fallback placeholder
                                    st.markdown("📷 No image available")

                st.markdown(
                    f"<button class='apollo-btn'>💎 VIP Update via Athena</button>",
                    unsafe_allow_html=True
                )
                if st.button("", key="vip_update"):
                    navigate_to_athena(
                        client_ids=vip_clients['client_id'].tolist(),
                        context_intent="vip_update",
                        brief_text="VIP client portfolio update with personalized model recommendations"
                    )

            # Client Churn Risk
            st.markdown("**⚠️ Client Churn Risk**")
            churn_risk_data = get_client_churn_risk(data)
            if not churn_risk_data.empty:
                render_churn_risk_chart(churn_risk_data)

                # Show client details with model thumbnails
                st.markdown("**High Risk Clients:**")
                high_risk_clients = churn_risk_data[churn_risk_data['days_since_booking'] > 60].head(5)

                for _, client in high_risk_clients.iterrows():
                    client_id = client.get('client_id')
                    days_since = client.get('days_since_booking', 0)

                    # Get last 3 booked models for this client
                    client_bookings = data['bookings'][data['bookings']['client_id'] == client_id]
                    if not client_bookings.empty:
                        recent_models = client_bookings.sort_values('confirmed_date', ascending=False).head(3)
                        model_thumbnails = []

                        for _, booking in recent_models.iterrows():
                            model_data = data['models'][data['models']['model_id'] == booking['model_id']]
                            if not model_data.empty:
                                thumbnail = model_data.iloc[0].get('primary_thumbnail',
                                                                 apollo_image_handler.get_primary_thumbnail(model_data.iloc[0].to_dict()))
                                model_thumbnails.append(thumbnail)

                        # Simplified - no complex thumbnail strips

                        # Risk level color
                        risk_color = "#FF4444" if days_since > 90 else "#FF8800"

                        st.markdown(f"""
                        <div style="background: rgba(255, 68, 68, 0.1); padding: 0.8rem; margin: 0.5rem 0;
                                    border-radius: 8px; border-left: 3px solid {risk_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong style="color: #FFFFFF;">{client.get('client_name', 'Unknown Client')}</strong><br>
                                    <span style="color: {risk_color}; font-size: 0.9rem;">{days_since:.0f} days since last booking</span>
                                </div>
                                <div style="text-align: right;">
                                    <span style="color: #B0B0B0; font-size: 0.8rem;">Risk Level: High</span>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown(
                    f"<button class='apollo-btn'>🔄 Re-Engage via Athena</button>",
                    unsafe_allow_html=True
                )
                if st.button("", key="reengage_clients"):
                    high_risk_clients = churn_risk_data[churn_risk_data['days_since_booking'] > 90]['client_id'].tolist()
                    navigate_to_athena(
                        client_ids=high_risk_clients,
                        context_intent="churn_prevention",
                        brief_text="Re-engagement campaign for clients at high risk of churn"
                    )

        st.markdown('</div>', unsafe_allow_html=True)

        # Operational Efficiency Section (Full Width)
        st.markdown('<h3 class="section-header">⚡ Operational Efficiency</h3>', unsafe_allow_html=True)

        efficiency_col1, efficiency_col2 = st.columns([2, 1])

        with efficiency_col1:
            # Agent Productivity Scatter
            st.markdown("**Agent Productivity Analysis**")
            render_agent_productivity_scatter(data)

        with efficiency_col2:
            # Hours Saved Tile
            hours_saved = calculate_hours_saved(data)
            st.markdown(f"""
            <div class="premium-card" style="text-align: center; background: linear-gradient(135deg, #1A2A1A 0%, #2A3A2A 100%); border-color: #00FF88;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⏱️</div>
                <div style="font-size: 2.5rem; font-weight: 700; color: #00FF88; margin-bottom: 0.5rem;">{hours_saved:.1f}</div>
                <div style="color: #E0E0E0; margin-bottom: 1rem;">Hours Saved This Week</div>
                <div style="font-size: 0.9rem; color: #B0B0B0; font-style: italic;">Powered by Athena automation</div>
                <div style="font-size: 0.8rem; color: #00FF88; margin-top: 1rem;">Athena reduces booking time by 40–60%</div>
            </div>
            """, unsafe_allow_html=True)

        # Predictive Insights Section
        st.markdown('<h3 class="section-header">🔮 Predictive Insights</h3>', unsafe_allow_html=True)
        st.markdown("**Strategy Suggestions**")

        try:
            insights = generate_predictive_insights(data)

            # Validate insights data structure
            if not insights or not isinstance(insights, list):
                insights = [
                    {
                        'icon': '📊',
                        'title': 'Market Analysis',
                        'description': 'Seasonal trends indicate increased demand for diverse casting.',
                        'action': 'Expand portfolio diversity',
                        'cta_type': 'scout'
                    },
                    {
                        'icon': '🎯',
                        'title': 'Optimization Opportunity',
                        'description': 'Automation can reduce booking time by 40-60%.',
                        'action': 'Increase Athena usage',
                        'cta_type': 'promote'
                    }
                ]

            insight_cols = st.columns(2)

            for i, insight in enumerate(insights):
                # Validate insight structure
                if isinstance(insight, dict) and all(key in insight for key in ['icon', 'title', 'description', 'action', 'cta_type']):
                    with insight_cols[i % 2]:
                        render_insight_card(insight, i, data)
                else:
                    # Skip malformed insights
                    continue

        except Exception as e:
            st.error(f"Error loading predictive insights: {e}")
            # Show fallback insights
            st.markdown("""
            <div class="premium-card">
                <h4 style="color: #2EF0FF;">📊 Market Analysis</h4>
                <p style="color: #E0E0E0;">Seasonal trends indicate increased demand for diverse casting.</p>
            </div>
            """, unsafe_allow_html=True)


        
        # Footer
        st.markdown("""
        <div class="apollo-footer">
            <p>Powered by <strong>Athena</strong> & <strong>Artemis</strong></p>
            <p style="font-size: 0.8rem; margin-top: 0.5rem;">AI Bloomberg Terminal for Fashion</p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Failed to load Apollo dashboard: {e}")
        st.markdown("""
        <div class="premium-card">
            <h3>🚧 Dashboard Unavailable</h3>
            <p>Please ensure all data files are available in the <code>out/</code> directory:</p>
            <ul>
                <li>models_normalized.csv</li>
                <li>bookings.csv</li>
                <li>model_performance.csv</li>
                <li>clients.csv</li>
                <li>athena_events.csv</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Check for modal display
        show_model_quick_view_modal()

    # Close Apollo container
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
