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

def apply_apollo_styling():
    """Apply luxury fashion styling to the Apollo dashboard."""
    st.markdown("""
    <style>
    /* Apollo Premium Styling - Override everything for dark theme */
    .stApp {
        background: linear-gradient(135deg, #0A0A0F 0%, #1A1A1F 100%) !important;
        color: #FFFFFF !important;
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

    /* Apollo dashboard container */
    .apollo-dashboard {
        background: transparent;
        color: #FFFFFF !important;
        min-height: 100vh;
        padding: 1rem;
    }
    
    /* Typography */
    .apollo-title {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-weight: 700;
        color: #2EF0FF;
        text-align: center;
        margin-bottom: 0.5rem;
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
    
    /* Action Buttons */
    .apollo-cta {
        background: linear-gradient(135deg, #2EF0FF 0%, #00D4FF 100%);
        color: #0D0D0F;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 1.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .apollo-cta:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(46, 240, 255, 0.4);
        background: linear-gradient(135deg, #00D4FF 0%, #2EF0FF 100%);
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
                            thumbnail_path = model.get('primary_thumbnail')
                            if not thumbnail_path:
                                try:
                                    thumbnail_path = apollo_image_handler.get_primary_thumbnail(model)
                                except Exception:
                                    thumbnail_path = None

                    # Clickable thumbnail that adds to selection
                    if st.button("📌", key=f"select_insight_{index}_{i}",
                               help=f"Select {model.get('name', 'Model')}"):
                        if 'selected_models' not in st.session_state:
                            st.session_state['selected_models'] = []
                        if model['model_id'] not in st.session_state['selected_models']:
                            st.session_state['selected_models'].append(model['model_id'])
                            st.success(f"Added {model.get('name', 'Model')} to selection!")

                    # Render ultra-high-quality thumbnail with proper aspect ratio
                    resolved_path = apollo_image_handler.get_image_path(thumbnail_path)
                    if resolved_path and os.path.exists(resolved_path):
                        try:
                            from PIL import Image, ImageOps
                            # Load image with high-quality settings
                            img = Image.open(resolved_path)

                            # Enhance image quality with proper resampling
                            # Convert to RGB if needed for better quality
                            if img.mode != 'RGB':
                                img = img.convert('RGB')

                            # Resize with high-quality resampling for crisp display
                            target_size = (180, 240)  # Increased from 120px to 180px for ultra-sharp display
                            img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)

                            # Enhanced thumbnail display with CSS styling
                            st.markdown("""
                            <style>
                            .insight-thumbnail img {
                                border-radius: 8px !important;
                                border: 1px solid rgba(46, 240, 255, 0.3) !important;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
                                transition: transform 0.2s ease !important;
                                object-fit: cover !important;
                                image-rendering: -webkit-optimize-contrast !important;
                                image-rendering: crisp-edges !important;
                            }
                            .insight-thumbnail img:hover {
                                transform: scale(1.05) !important;
                                border-color: #2EF0FF !important;
                            }
                            </style>
                            <div class="insight-thumbnail">
                            """, unsafe_allow_html=True)

                            st.image(
                                img,
                                width=180,  # Increased from 120 to 180 for ultra-sharp display
                                caption="",
                                use_container_width=False
                            )
                            st.markdown("</div>", unsafe_allow_html=True)
                        except Exception:
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

    # Add actual button functionality
    try:
        cta_type = insight.get('cta_type', 'promote')
        cta_text = "Promote (Athena)" if cta_type == 'promote' else "Scout (Artemis)"

        if st.button(f"{cta_text}", key=f"insight_{index}"):
            if cta_type == 'promote':
                navigate_to_athena()
            else:
                st.info("Artemis scouting feature coming soon!")
    except Exception:
        # Fallback button
        if st.button("View Details", key=f"insight_fallback_{index}"):
            st.info("Feature coming soon!")

def render_height_distribution(models_df: pd.DataFrame):
    """Render height distribution histogram."""
    if models_df.empty or 'height_cm' not in models_df.columns:
        return

    # Clean height data
    height_data = models_df['height_cm'].dropna()

    if height_data.empty:
        return

    # Create histogram
    fig = px.histogram(
        height_data,
        nbins=20,
        title="Model Height Distribution",
        labels={'value': 'Height (cm)', 'count': 'Number of Models'},
        color_discrete_sequence=['#2EF0FF']
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        title_font_color='#2EF0FF',
        xaxis_title="Height (cm)",
        yaxis_title="Number of Models",
        showlegend=False
    )

    # Add insight text
    avg_height = height_data.mean()
    tall_models = len(height_data[height_data >= 175])
    total_models = len(height_data)

    fig.add_annotation(
        text=f"Editorial line-up concentration + runway advantage<br>Avg: {avg_height:.0f}cm | {tall_models}/{total_models} models ≥175cm",
        xref="paper", yref="paper",
        x=0.98, y=0.98,
        xanchor="right", yanchor="top",
        bgcolor="rgba(46, 240, 255, 0.1)",
        bordercolor="#2EF0FF",
        borderwidth=1,
        font=dict(color="white", size=10)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Interactive height buckets with thumbnails
    st.markdown("**Height Categories:**")
    height_buckets = [
        ("Petite (≤165cm)", models_df[models_df['height_cm'] <= 165]),
        ("Standard (166-174cm)", models_df[(models_df['height_cm'] > 165) & (models_df['height_cm'] <= 174)]),
        ("Tall (175-184cm)", models_df[(models_df['height_cm'] > 174) & (models_df['height_cm'] <= 184)]),
        ("Editorial (≥185cm)", models_df[models_df['height_cm'] >= 185])
    ]

    bucket_cols = st.columns(4)
    for i, (bucket_name, bucket_models) in enumerate(height_buckets):
        with bucket_cols[i]:
            if not bucket_models.empty:
                st.markdown(f"**{bucket_name}**")
                st.caption(f"{len(bucket_models)} models")

                # Show up to 3 thumbnails for this bucket
                sample_models = bucket_models.head(3)
                for _, model in sample_models.iterrows():
                    thumbnail_path = model.get('primary_thumbnail',
                                             apollo_image_handler.get_primary_thumbnail(model.to_dict()))

                    # Clickable thumbnail for modal
                    if st.button("👁️", key=f"height_thumb_{model['model_id']}",
                               help=f"Quick view {model['name']}"):
                        st.session_state['show_model_modal'] = True
                        st.session_state['modal_model_data'] = model.to_dict()
                        st.rerun()

                    # Render ultra-high-quality thumbnail with proper aspect ratio
                    resolved_path = apollo_image_handler.get_image_path(thumbnail_path)
                    if resolved_path and os.path.exists(resolved_path):
                        try:
                            from PIL import Image, ImageOps, ImageEnhance
                            # Load image with maximum quality settings
                            img = Image.open(resolved_path)

                            # Enhance image quality for height distribution display
                            if img.mode != 'RGB':
                                img = img.convert('RGB')

                            # Apply sharpness enhancement for crisp small display
                            enhancer = ImageEnhance.Sharpness(img)
                            img = enhancer.enhance(1.25)  # Strong sharpness boost for small thumbnails

                            # Resize with high-quality resampling for ultra-sharp display
                            target_size = (90, 120)  # Increased from 64px to 90px for better clarity
                            img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)

                            # Enhanced height bucket thumbnail display with CSS styling
                            st.markdown("""
                            <style>
                            .height-bucket-thumbnail img {
                                border-radius: 6px !important;
                                border: 1px solid rgba(46, 240, 255, 0.4) !important;
                                box-shadow: 0 2px 8px rgba(46, 240, 255, 0.2) !important;
                                transition: all 0.2s ease !important;
                                object-fit: cover !important;
                                image-rendering: -webkit-optimize-contrast !important;
                                image-rendering: crisp-edges !important;
                            }
                            .height-bucket-thumbnail img:hover {
                                transform: scale(1.05) !important;
                                border-color: #2EF0FF !important;
                                box-shadow: 0 3px 12px rgba(46, 240, 255, 0.4) !important;
                            }
                            </style>
                            <div class="height-bucket-thumbnail">
                            """, unsafe_allow_html=True)

                            st.image(
                                img,
                                width=90,  # Increased from 64 to 90 for ultra-sharp display
                                caption="",
                                use_container_width=False
                            )
                            st.markdown("</div>", unsafe_allow_html=True)
                        except Exception:
                            st.markdown("""
                            <div style="
                                width: 90px;
                                height: 120px;
                                background: linear-gradient(135deg, #2EF0FF 0%, #1A8FFF 100%);
                                border-radius: 6px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                color: white;
                                font-size: 1.5rem;
                                border: 1px solid rgba(46, 240, 255, 0.4);
                                box-shadow: 0 2px 8px rgba(46, 240, 255, 0.2);
                                margin: 0 auto;
                            ">
                                📷
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="
                            width: 90px;
                            height: 120px;
                            background: linear-gradient(135deg, #2EF0FF 0%, #1A8FFF 100%);
                            border-radius: 6px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-size: 1.5rem;
                            border: 1px solid rgba(46, 240, 255, 0.4);
                            box-shadow: 0 2px 8px rgba(46, 240, 255, 0.2);
                            margin: 0 auto;
                        ">
                            👤
                        </div>
                        """, unsafe_allow_html=True)
                    st.caption(model['name'][:10])
            else:
                st.markdown(f"**{bucket_name}**")
                st.caption("No models")

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
            if st.button("📩 Promote via Athena", key=f"promote_modal_{model_id}", type="primary"):
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
            if st.button("👁️ View Full Profile", key=f"catalogue_modal_{model_id}", type="secondary"):
                st.session_state["selected_model"] = model_id
                st.session_state["active_tab"] = "Catalogue"
                st.info("💡 Switch to the **Catalogue** tab to view full profile")

def show_model_quick_view_modal():
    """Check if modal should be shown and render it."""
    if st.session_state.get('show_model_modal') and st.session_state.get('modal_model_data'):
        # Get additional data for modal
        try:
            data_loader = ApolloDataLoader()
            data = data_loader.load_all_data()

            render_model_quick_view_modal(
                st.session_state['modal_model_data'],
                data.get('bookings', pd.DataFrame()),
                data.get('performance', pd.DataFrame())
            )

            # Close modal button
            if st.button("✖️ Close", key="close_modal"):
                st.session_state['show_model_modal'] = False
                st.session_state['modal_model_data'] = None
                st.rerun()

        except Exception as e:
            st.error(f"Error loading modal data: {e}")
            st.session_state['show_model_modal'] = False

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

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👁️ Quick View", key=f"apollo_quick_{model_data['model_id']}", type="secondary", use_container_width=True):
            st.session_state.show_model_modal = True
            st.session_state.modal_model_data = model_data
            st.rerun()

    with col2:
        if st.button("🎯 Promote", key=f"apollo_promote_{model_data['model_id']}", type="primary", use_container_width=True):
            # Transfer to Athena
            from session_manager import SessionManager
            SessionManager.transfer_model_to_athena(model_data, "Apollo")
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

def render_apollo_tab_navigation():
    """Render the internal tab navigation for Apollo."""
    # Initialize tab state
    if 'apollo_active_tab' not in st.session_state:
        st.session_state.apollo_active_tab = 'Overview'

    # Tab styling
    st.markdown("""
    <style>
    .apollo-tab-container {
        background: linear-gradient(135deg, #1A1A1F 0%, #2A2A35 100%);
        border-radius: 12px;
        padding: 0.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(46, 240, 255, 0.3);
    }
    .apollo-tab-button {
        background: transparent;
        border: none;
        color: #CCCCCC;
        padding: 0.75rem 1.5rem;
        margin: 0 0.25rem;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 0.9rem;
    }
    .apollo-tab-button:hover {
        background: rgba(46, 240, 255, 0.1);
        color: #2EF0FF;
    }
    .apollo-tab-button.active {
        background: linear-gradient(135deg, #2EF0FF 0%, #00D4FF 100%);
        color: #0D0D0F;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(46, 240, 255, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

    # Tab buttons
    tabs = ['Overview', 'Models Intelligence', 'Market Intelligence', 'External Intelligence']
    tab_icons = ['📊', '🎭', '🌍', '🔮']

    st.markdown('<div class="apollo-tab-container">', unsafe_allow_html=True)
    cols = st.columns(4)

    for i, (tab, icon) in enumerate(zip(tabs, tab_icons)):
        with cols[i]:
            if st.button(f"{icon} {tab}", key=f"apollo_tab_{tab.replace(' ', '_')}",
                        help=f"Switch to {tab} view"):
                st.session_state.apollo_active_tab = tab
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    return st.session_state.apollo_active_tab

def main():
    """Enhanced Apollo dashboard with modular tab-based interface."""
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

    # Wrap everything in Apollo-themed container
    st.markdown('<div class="apollo-dashboard">', unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="apollo-title">📊 Apollo — Agency Intelligence</div>
    <div class="apollo-subtitle">"Insights that unlock revenue opportunities"</div>
    """, unsafe_allow_html=True)

    # Render tab navigation
    active_tab = render_apollo_tab_navigation()

    # Load data
    try:
        data_loader = ApolloDataLoader()
        data = data_loader.load_all_data()
        metrics_calculator = ApolloMetrics(data)

        # Route to appropriate tab
        if active_tab == 'Overview':
            render_overview_tab(data, metrics_calculator)
        elif active_tab == 'Models Intelligence':
            render_models_intelligence_tab(data, metrics_calculator)
        elif active_tab == 'Market Intelligence':
            render_market_intelligence_tab(data, metrics_calculator)
        elif active_tab == 'External Intelligence':
            render_external_intelligence_tab(data, metrics_calculator)
        else:
            st.error(f"Unknown tab: {active_tab}")

        # Check for modal display
        show_model_quick_view_modal()

                                st.image(
                                    img,
                                    width=120,  # Increased from 100 to 120 for ultra-sharp display
                                    caption="",
                                    use_container_width=False  # Fixed deprecated parameter
                                )
                                st.markdown("</div>", unsafe_allow_html=True)
                            except Exception:
                                st.markdown("""
                                <div style="
                                    width: 120px;
                                    height: 160px;
                                    background: linear-gradient(135deg, #FF4444 0%, #CC3333 100%);
                                    border-radius: 8px;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    color: white;
                                    font-size: 2rem;
                                    border: 2px solid rgba(255, 68, 68, 0.4);
                                    box-shadow: 0 3px 10px rgba(255, 68, 68, 0.2);
                                    margin: 0 auto;
                                ">
                                    📷
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="
                                width: 120px;
                                height: 160px;
                                background: linear-gradient(135deg, #FF4444 0%, #CC3333 100%);
                                border-radius: 8px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                color: white;
                                font-size: 2rem;
                                border: 2px solid rgba(255, 68, 68, 0.4);
                                box-shadow: 0 3px 10px rgba(255, 68, 68, 0.2);
                                margin: 0 auto;
                            ">
                                👤
                            </div>
                            """, unsafe_allow_html=True)

                        # Make thumbnail clickable for modal
                        if st.button("👁️", key=f"thumb_inactive_{model['model_id']}",
                                   help=f"Quick view {model['name']}"):
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

                if st.button("👀 View in Catalogue", key="view_inactive"):
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
                                resolved_path = apollo_image_handler.get_image_path(thumb_path)
                                if resolved_path and os.path.exists(resolved_path):
                                    try:
                                        from PIL import Image, ImageOps, ImageEnhance
                                        # Load image with maximum quality settings
                                        img = Image.open(resolved_path)

                                        # Enhance image quality for VIP client display
                                        if img.mode != 'RGB':
                                            img = img.convert('RGB')

                                        # Apply sharpness and contrast enhancement for luxury display
                                        sharpness_enhancer = ImageEnhance.Sharpness(img)
                                        img = sharpness_enhancer.enhance(1.1)  # Subtle sharpness boost

                                        contrast_enhancer = ImageEnhance.Contrast(img)
                                        img = contrast_enhancer.enhance(1.05)  # Slight contrast boost

                                        # Resize with high-quality resampling for ultra-sharp display
                                        target_size = (140, 175)  # Increased from 100px to 140px for luxury display
                                        img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)

                                        # Enhanced VIP client thumbnail display with CSS styling
                                        st.markdown("""
                                        <style>
                                        .vip-client-thumbnail img {
                                            border-radius: 8px !important;
                                            border: 2px solid rgba(255, 215, 0, 0.5) !important;
                                            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
                                            transition: all 0.3s ease !important;
                                            object-fit: cover !important;
                                            image-rendering: -webkit-optimize-contrast !important;
                                            image-rendering: crisp-edges !important;
                                        }
                                        .vip-client-thumbnail img:hover {
                                            transform: scale(1.05) !important;
                                            border-color: #FFD700 !important;
                                            box-shadow: 0 6px 20px rgba(255, 215, 0, 0.5) !important;
                                        }
                                        </style>
                                        <div class="vip-client-thumbnail">
                                        """, unsafe_allow_html=True)

                                        st.image(
                                            img,
                                            width=140,  # Increased from 100 to 140 for luxury display
                                            caption="",
                                            use_container_width=False
                                        )
                                        st.markdown("</div>", unsafe_allow_html=True)
                                    except Exception:
                                        st.markdown("""
                                        <div style="
                                            width: 140px;
                                            height: 175px;
                                            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                                            border-radius: 8px;
                                            display: flex;
                                            align-items: center;
                                            justify-content: center;
                                            color: white;
                                            font-size: 1.8rem;
                                            border: 2px solid rgba(255, 215, 0, 0.5);
                                            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
                                        ">
                                            📷
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.markdown("""
                                    <div style="
                                        width: 140px;
                                        height: 175px;
                                        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                                        border-radius: 8px;
                                        display: flex;
                                        align-items: center;
                                        justify-content: center;
                                        color: white;
                                        font-size: 1.8rem;
                                        border: 2px solid rgba(255, 215, 0, 0.5);
                                        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
                                    ">
                                        �
                                    </div>
                                    """, unsafe_allow_html=True)

                if st.button("💎 VIP Update via Athena", key="vip_update"):
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

                if st.button("🔄 Re-Engage via Athena", key="reengage_clients"):
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

        # Height Distribution Chart (if space allows)
        if not data['models'].empty:
            st.markdown('<h3 class="section-header">📏 Height Distribution Analysis</h3>', unsafe_allow_html=True)
            render_height_distribution(data['models'])
        
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
