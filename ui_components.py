"""
Unified UI Components for Elysium Streamlit App
Provides consistent loading indicators, notifications, error cards, and other UI elements.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import time
from datetime import datetime, timedelta
from session_manager import SessionManager

class LoadingComponents:
    """Loading indicators and progress components."""
    
    @staticmethod
    def show_global_spinner(message: str = "Loading..."):
        """Show global loading spinner with message."""
        return st.spinner(f"🔄 {message}")
    
    @staticmethod
    def show_progress_bar(progress: float, message: str = ""):
        """Show progress bar with optional message."""
        progress_bar = st.progress(progress)
        if message:
            st.caption(message)
        return progress_bar
    
    @staticmethod
    def show_loading_skeleton(height: int = 200, count: int = 1):
        """Show loading skeleton placeholders."""
        for i in range(count):
            st.markdown(f"""
            <div style="
                height: {height}px;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: loading 1.5s infinite;
                border-radius: 8px;
                margin: 10px 0;
            "></div>
            <style>
            @keyframes loading {{
                0% {{ background-position: 200% 0; }}
                100% {{ background-position: -200% 0; }}
            }}
            </style>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def show_data_loading_placeholder():
        """Show placeholder for data loading."""
        st.markdown("""
        <div style="
            padding: 2rem;
            text-align: center;
            background: #f8f9fa;
            border-radius: 10px;
            border: 2px dashed #dee2e6;
            margin: 1rem 0;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
            <h3 style="color: #6c757d; margin-bottom: 0.5rem;">Loading Data...</h3>
            <p style="color: #6c757d;">Please wait while we fetch the latest information</p>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def show_ai_processing_indicator():
        """Show AI processing indicator."""
        st.markdown("""
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            margin: 1rem 0;
        ">
            <div style="
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255,255,255,0.3);
                border-top: 3px solid white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 1rem;
            "></div>
            <span>🧠 AI is processing your request...</span>
        </div>
        <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def show_pdf_generation_progress(progress: float = 0.0):
        """Show PDF generation progress."""
        st.markdown(f"""
        <div style="
            padding: 1rem;
            background: #fff3cd;
            border-radius: 8px;
            margin: 1rem 0;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="margin-right: 0.5rem;">📄</span>
                <strong>Generating PDF Portfolio...</strong>
            </div>
            <div style="
                width: 100%;
                height: 8px;
                background: #e9ecef;
                border-radius: 4px;
                overflow: hidden;
            ">
                <div style="
                    width: {progress}%;
                    height: 100%;
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    transition: width 0.3s ease;
                "></div>
            </div>
            <div style="font-size: 0.8rem; color: #856404; margin-top: 0.5rem;">
                {progress:.0f}% complete
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def show_model_grid_skeleton(num_cards: int = 6):
        """Show skeleton placeholder for model grid."""
        skeleton_html = """
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
        """

        for i in range(num_cards):
            skeleton_html += f"""
            <div class="skeleton-card" style="
                background: #f8f9fa;
                border-radius: 12px;
                padding: 1rem;
                border: 1px solid #e9ecef;
                animation: pulse 1.5s ease-in-out infinite alternate;
            ">
                <div class="skeleton-image" style="
                    width: 100%;
                    height: 200px;
                    background: linear-gradient(90deg, #e9ecef 25%, #f8f9fa 50%, #e9ecef 75%);
                    background-size: 200% 100%;
                    animation: shimmer 1.5s infinite;
                    border-radius: 8px;
                    margin-bottom: 1rem;
                "></div>
                <div class="skeleton-text" style="
                    height: 16px;
                    background: linear-gradient(90deg, #e9ecef 25%, #f8f9fa 50%, #e9ecef 75%);
                    background-size: 200% 100%;
                    animation: shimmer 1.5s infinite;
                    border-radius: 4px;
                    margin-bottom: 0.5rem;
                "></div>
                <div class="skeleton-text" style="
                    height: 14px;
                    width: 70%;
                    background: linear-gradient(90deg, #e9ecef 25%, #f8f9fa 50%, #e9ecef 75%);
                    background-size: 200% 100%;
                    animation: shimmer 1.5s infinite;
                    border-radius: 4px;
                "></div>
            </div>
            """

        skeleton_html += """
        </div>
        <style>
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        @keyframes pulse {
            0% { opacity: 1; }
            100% { opacity: 0.7; }
        }
        </style>
        """

        st.markdown(skeleton_html, unsafe_allow_html=True)

    @staticmethod
    def show_athena_results_skeleton():
        """Show skeleton placeholder for Athena results."""
        st.markdown("""
        <div style="margin: 1rem 0;">
            <div class="skeleton-header" style="
                height: 24px;
                width: 200px;
                background: linear-gradient(90deg, #e9ecef 25%, #f8f9fa 50%, #e9ecef 75%);
                background-size: 200% 100%;
                animation: shimmer 1.5s infinite;
                border-radius: 4px;
                margin-bottom: 1rem;
            "></div>
            <div class="skeleton-content" style="
                background: #f8f9fa;
                border-radius: 12px;
                padding: 1.5rem;
                border: 1px solid #e9ecef;
            ">
                <div class="skeleton-line" style="
                    height: 16px;
                    background: linear-gradient(90deg, #e9ecef 25%, #f8f9fa 50%, #e9ecef 75%);
                    background-size: 200% 100%;
                    animation: shimmer 1.5s infinite;
                    border-radius: 4px;
                    margin-bottom: 1rem;
                "></div>
                <div class="skeleton-line" style="
                    height: 16px;
                    width: 80%;
                    background: linear-gradient(90deg, #e9ecef 25%, #f8f9fa 50%, #e9ecef 75%);
                    background-size: 200% 100%;
                    animation: shimmer 1.5s infinite;
                    border-radius: 4px;
                    margin-bottom: 1rem;
                "></div>
                <div class="skeleton-line" style="
                    height: 16px;
                    width: 60%;
                    background: linear-gradient(90deg, #e9ecef 25%, #f8f9fa 50%, #e9ecef 75%);
                    background-size: 200% 100%;
                    animation: shimmer 1.5s infinite;
                    border-radius: 4px;
                "></div>
            </div>
        </div>
        <style>
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def show_apollo_dashboard_skeleton():
        """Show skeleton placeholder for Apollo dashboard."""
        st.markdown("""
        <div style="margin: 1rem 0;">
            <!-- Metrics Row Skeleton -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                <div class="skeleton-metric" style="
                    background: #2c3e50;
                    border-radius: 12px;
                    padding: 1.5rem;
                    border: 1px solid #34495e;
                ">
                    <div style="
                        height: 20px;
                        width: 60%;
                        background: linear-gradient(90deg, #34495e 25%, #2c3e50 50%, #34495e 75%);
                        background-size: 200% 100%;
                        animation: shimmer 1.5s infinite;
                        border-radius: 4px;
                        margin-bottom: 1rem;
                    "></div>
                    <div style="
                        height: 32px;
                        width: 80%;
                        background: linear-gradient(90deg, #34495e 25%, #2c3e50 50%, #34495e 75%);
                        background-size: 200% 100%;
                        animation: shimmer 1.5s infinite;
                        border-radius: 4px;
                    "></div>
                </div>
                <div class="skeleton-metric" style="
                    background: #2c3e50;
                    border-radius: 12px;
                    padding: 1.5rem;
                    border: 1px solid #34495e;
                ">
                    <div style="
                        height: 20px;
                        width: 70%;
                        background: linear-gradient(90deg, #34495e 25%, #2c3e50 50%, #34495e 75%);
                        background-size: 200% 100%;
                        animation: shimmer 1.5s infinite;
                        border-radius: 4px;
                        margin-bottom: 1rem;
                    "></div>
                    <div style="
                        height: 32px;
                        width: 90%;
                        background: linear-gradient(90deg, #34495e 25%, #2c3e50 50%, #34495e 75%);
                        background-size: 200% 100%;
                        animation: shimmer 1.5s infinite;
                        border-radius: 4px;
                    "></div>
                </div>
            </div>

            <!-- Chart Skeleton -->
            <div class="skeleton-chart" style="
                background: #2c3e50;
                border-radius: 12px;
                padding: 2rem;
                border: 1px solid #34495e;
                height: 300px;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div style="
                    width: 80%;
                    height: 200px;
                    background: linear-gradient(90deg, #34495e 25%, #2c3e50 50%, #34495e 75%);
                    background-size: 200% 100%;
                    animation: shimmer 1.5s infinite;
                    border-radius: 8px;
                "></div>
            </div>
        </div>
        <style>
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        </style>
        """, unsafe_allow_html=True)

class NotificationComponents:
    """Notification and alert components."""
    
    @staticmethod
    def show_notifications():
        """Display all current notifications."""
        notifications = SessionManager.get_notifications()
        current_time = datetime.now()
        
        # Filter out expired notifications
        active_notifications = []
        for notification in notifications:
            time_diff = (current_time - notification['timestamp']).total_seconds()
            if time_diff < notification['duration']:
                active_notifications.append(notification)
        
        # Update session state with active notifications
        st.session_state.notifications = active_notifications
        
        # Display active notifications
        for notification in active_notifications:
            NotificationComponents.show_notification(
                notification['message'],
                notification['type']
            )
    
    @staticmethod
    def show_notification(message: str, type: str = 'info'):
        """Show a single notification."""
        if type == 'success':
            st.success(f"✅ {message}")
        elif type == 'error':
            st.error(f"❌ {message}")
        elif type == 'warning':
            st.warning(f"⚠️ {message}")
        else:
            st.info(f"ℹ️ {message}")

    @staticmethod
    def show_integration_notification(message: str, source: str, target: str):
        """Show cross-assistant integration notification."""
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        ">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">🔄</span>
                <span>{message}</span>
            </div>
            <div style="font-size: 0.8rem; opacity: 0.8;">
                {source} → {target}
            </div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def show_integration_messages():
        """Display recent cross-assistant integration messages with enhanced styling."""
        messages = SessionManager.get_integration_messages()
        if messages:
            st.markdown("#### 🔄 Recent Integrations")
            for msg in messages[-3:]:  # Show last 3 messages
                icon = "✅" if msg['type'] == 'success' else "❌" if msg['type'] == 'error' else "ℹ️"
                color = "#00FF88" if msg['type'] == 'success' else "#FF4444" if msg['type'] == 'error' else "#2EF0FF"

                st.markdown(f"""
                <div style="
                    background: rgba(255,255,255,0.05);
                    border-left: 3px solid {color};
                    padding: 0.75rem;
                    margin: 0.5rem 0;
                    border-radius: 6px;
                ">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <span>{icon} {msg['message']}</span>
                        <small style="opacity: 0.7;">⏰ {msg['timestamp'].strftime('%H:%M:%S')}</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    @staticmethod
    def show_ai_processing_indicator(step: str, total_steps: int, current_step: int):
        """Show AI processing step indicator with personality."""
        progress = (current_step / total_steps) * 100

        step_messages = {
            "parsing": "🧠 Reading your brief and understanding your vision...",
            "matching": "🔍 Scanning our talent roster for perfect matches...",
            "generating": "✍️ Crafting your professional pitch email...",
            "finalizing": "✨ Adding the finishing touches..."
        }

        message = step_messages.get(step, f"🤖 Processing step {current_step} of {total_steps}...")

        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <div style="
                    width: 20px;
                    height: 20px;
                    border: 2px solid white;
                    border-top: 2px solid transparent;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: 0.5rem;
                "></div>
                <span>{message}</span>
            </div>
            <div style="
                width: 100%;
                height: 6px;
                background: rgba(255,255,255,0.3);
                border-radius: 3px;
                overflow: hidden;
            ">
                <div style="
                    width: {progress}%;
                    height: 100%;
                    background: white;
                    transition: width 0.3s ease;
                "></div>
            </div>
            <div style="text-align: center; margin-top: 0.5rem; font-size: 0.9rem;">
                Step {current_step} of {total_steps} • {progress:.0f}% complete
            </div>
        </div>
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def show_success_celebration(message: str, details: str = None):
        """Show success message with celebration animation."""
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #00FF88 0%, #00CC6A 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            margin: 1rem 0;
            animation: celebrate 0.6s ease-out;
        ">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🎉</div>
            <h3 style="margin: 0 0 0.5rem 0; color: white;">{message}</h3>
            {f'<p style="margin: 0; opacity: 0.9; color: white;">{details}</p>' if details else ''}
        </div>
        <style>
        @keyframes celebrate {{
            0% {{ transform: scale(0.8); opacity: 0; }}
            50% {{ transform: scale(1.1); }}
            100% {{ transform: scale(1); opacity: 1; }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def show_toast(message: str, type: str = 'info'):
        """Show a toast notification (temporary)."""
        toast_color = {
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8'
        }.get(type, '#17a2b8')
        
        st.markdown(f"""
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: {toast_color};
            color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        ">
            {message}
        </div>
        <style>
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        </style>
        """, unsafe_allow_html=True)

class ErrorComponents:
    """Error handling and display components."""
    
    @staticmethod
    def show_error_card(title: str, message: str, suggestions: List[str] = None):
        """Show user-friendly error card."""
        suggestions_html = ""
        if suggestions:
            suggestions_html = "<h4>💡 Suggestions:</h4><ul>"
            for suggestion in suggestions:
                suggestions_html += f"<li>{suggestion}</li>"
            suggestions_html += "</ul>"
        
        st.markdown(f"""
        <div style="
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="font-size: 1.5rem; margin-right: 0.5rem;">🚨</div>
                <h3 style="color: #c53030; margin: 0;">{title}</h3>
            </div>
            <p style="color: #742a2a; margin-bottom: 1rem;">{message}</p>
            {suggestions_html}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def show_connection_error():
        """Show connection error with specific suggestions."""
        ErrorComponents.show_error_card(
            "Connection Error",
            "Unable to connect to required services.",
            [
                "Check your internet connection",
                "Ensure Ollama is running on localhost:11434",
                "Verify all data files are present in the out/ directory",
                "Try refreshing the page"
            ]
        )
    
    @staticmethod
    def show_data_error(missing_files: List[str] = None):
        """Show data loading error with specific suggestions."""
        message = "Required data files are missing or corrupted."
        suggestions = [
            "Run the data generation scripts",
            "Check file permissions in the out/ directory",
            "Verify CSV files are properly formatted"
        ]
        
        if missing_files:
            message += f" Missing files: {', '.join(missing_files)}"
        
        ErrorComponents.show_error_card("Data Loading Error", message, suggestions)
    
    @staticmethod
    def show_ai_error():
        """Show AI service error with specific suggestions."""
        ErrorComponents.show_error_card(
            "AI Service Error",
            "The AI query processing service is unavailable.",
            [
                "Ensure Ollama is installed and running",
                "Check if the gemma3:4b model is available",
                "Try using manual filters instead",
                "Contact support if the issue persists"
            ]
        )

class HeaderComponents:
    """Header and navigation components."""
    
    @staticmethod
    def show_global_header():
        """Show global header with branding and status."""
        session_info = SessionManager.get_session_info()
        current_page = SessionManager.get_page()

        # Get basic info
        version = session_info.get('version', '0.4.0')
        session_id = session_info.get('session_id', 'Unknown')[-8:]

        # Build loading indicator separately to avoid nested f-strings
        loading_html = ""
        if SessionManager.is_loading():
            loading_message = SessionManager.get_loading_message() or 'Loading...'
            loading_html = f"""
            <div style="
                display: inline-flex;
                align-items: center;
                background: #fff3cd;
                color: #856404;
                padding: 0.25rem 0.75rem;
                border-radius: 15px;
                font-size: 0.8rem;
                margin-left: 1rem;
            ">
                <div style="
                    width: 12px;
                    height: 12px;
                    border: 2px solid #856404;
                    border-top: 2px solid transparent;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: 0.5rem;
                "></div>
                {loading_message}
            </div>
            """

        # Build the complete header HTML
        header_html = f"""
        <div style="
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 2rem;
            border-radius: 0 0 15px 15px;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center;">
                    <h1 style="margin: 0; font-size: 1.8rem;">🎭 Elysium</h1>
                    <span style="
                        background: rgba(255,255,255,0.2);
                        padding: 0.25rem 0.75rem;
                        border-radius: 15px;
                        font-size: 0.8rem;
                        margin-left: 1rem;
                    ">v{version} Demo</span>
                    {loading_html}
                </div>
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <span style="font-size: 0.9rem; opacity: 0.9;">📍 {current_page}</span>
                    <span style="font-size: 0.8rem; opacity: 0.7;">
                        Session: {session_id}
                    </span>
                </div>
            </div>
        </div>
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """

        # Try using st.html() instead of st.markdown() to avoid code wrapping
        try:
            st.html(header_html)
        except AttributeError:
            # Fallback to st.markdown if st.html is not available
            st.markdown(header_html, unsafe_allow_html=True)

class FooterComponents:
    """Footer and status components."""
    
    @staticmethod
    def show_global_footer():
        """Show enhanced global footer with comprehensive session info."""
        session_info = SessionManager.get_session_info()
        current_page = SessionManager.get_page()

        # Calculate session duration
        start_time = session_info.get('start_time')
        duration = "Unknown"
        if start_time:
            duration_delta = datetime.now() - start_time
            hours, remainder = divmod(duration_delta.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            duration = f"{int(hours):02d}:{int(minutes):02d}"

        # Get system status
        data_loaded = session_info.get('data_loaded', False)
        error_count = len(session_info.get('errors', []))
        notification_count = len(SessionManager.get_notifications())

        # Get memory usage (simplified)
        import sys
        memory_mb = sys.getsizeof(st.session_state) / (1024 * 1024)

        # Calculate error color and data status
        error_color = '#dc3545' if error_count > 0 else '#28a745'
        data_status = '✅ Loaded' if data_loaded else '❌ Not Loaded'
        last_update = session_info.get('last_update', 'Never')
        memory_formatted = f"{memory_mb:.1f}"

        footer_html = f"""
        <div style="
            margin-top: 3rem;
            padding: 1.5rem;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-top: 1px solid #dee2e6;
            border-radius: 15px 15px 0 0;
            color: #495057;
            font-size: 0.85rem;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
        ">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
                <div style="text-align: left;">
                    <div style="font-weight: 600; color: #667eea; margin-bottom: 0.25rem;">
                        🏛️ Elysium v0.4 Demo
                    </div>
                    <div style="font-size: 0.8rem;">
                        Current Page: <strong>{current_page}</strong>
                    </div>
                </div>

                <div style="text-align: center;">
                    <div style="font-weight: 600; margin-bottom: 0.25rem;">
                        📊 Session Status
                    </div>
                    <div style="font-size: 0.8rem;">
                        Duration: <strong>{duration}</strong><br>
                        Memory: <strong>{memory_formatted} MB</strong>
                    </div>
                </div>

                <div style="text-align: center;">
                    <div style="font-weight: 600; margin-bottom: 0.25rem;">
                        🔄 Data Status
                    </div>
                    <div style="font-size: 0.8rem;">
                        Models: <strong>{data_status}</strong><br>
                        Last Update: <strong>{last_update}</strong>
                    </div>
                </div>

                <div style="text-align: right;">
                    <div style="font-weight: 600; margin-bottom: 0.25rem;">
                        🚨 System Health
                    </div>
                    <div style="font-size: 0.8rem;">
                        Errors: <strong style="color: {error_color};">{error_count}</strong><br>
                        Notifications: <strong>{notification_count}</strong>
                    </div>
                </div>
            </div>

            <div style="
                text-align: center;
                padding-top: 1rem;
                border-top: 1px solid #dee2e6;
                font-size: 0.75rem;
                color: #6c757d;
            ">
                Built with ❤️ using Streamlit | Enhanced with Augment Agent |
                <a href="#" style="color: #667eea; text-decoration: none;">Documentation</a> |
                <a href="#" style="color: #667eea; text-decoration: none;">Support</a>
            </div>
        </div>
        """

        # Try using st.html() instead of st.markdown() to avoid code wrapping
        try:
            st.html(footer_html)
        except AttributeError:
            # Fallback to st.markdown if st.html is not available
            st.markdown(footer_html, unsafe_allow_html=True)

    @staticmethod
    def show_status_bar():
        """Show floating status bar with quick actions."""
        is_loading = SessionManager.is_loading()

        if is_loading:
            loading_message = st.session_state.get('loading_message', 'Loading...')
            st.markdown(f"""
            <div style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 25px;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
                z-index: 1000;
                font-size: 0.9rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            ">
                <div style="
                    width: 16px;
                    height: 16px;
                    border: 2px solid rgba(255,255,255,0.3);
                    border-top: 2px solid white;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                "></div>
                {loading_message}
            </div>
            <style>
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            </style>
            """, unsafe_allow_html=True)

class NavigationComponents:
    """Navigation and breadcrumb components."""

    # Navigation items - defined once globally
    NAV_ITEMS = [
        ("📚 Catalogue", "Catalogue", "Browse and search model catalogue"),
        ("🏛️ Athena", "Athena", "AI assistant for client briefs"),
        ("📊 Apollo", "Apollo", "Agency intelligence dashboard")
    ]

    @staticmethod
    def _ensure_sidebar_visible():
        """
        Ensure sidebar is always visible on app load/page change.
        This prevents the sidebar from being permanently hidden.
        """
        # Always reset sidebar_open to True on initialization
        # This ensures the navbar is NEVER permanently hidden
        if 'sidebar_open' not in st.session_state:
            st.session_state.sidebar_open = True

        # IMPORTANT: Reset sidebar visibility on page navigation
        # This ensures closing sidebar is only temporary for current view
        if 'last_nav_page' not in st.session_state:
            st.session_state.last_nav_page = None

        current_page = SessionManager.get_page()
        if st.session_state.last_nav_page != current_page:
            # Page changed - reset sidebar to visible
            st.session_state.sidebar_open = True
            st.session_state.last_nav_page = current_page

    @staticmethod
    def show_sidebar_toggle_button():
        """Show sidebar toggle button in main area when sidebar is hidden."""
        # Ensure sidebar visibility is properly managed
        NavigationComponents._ensure_sidebar_visible()

        # Show toggle button only when sidebar is temporarily closed
        if not st.session_state.get('sidebar_open', True):
            # Create a floating toggle button that won't be hidden by Apollo CSS
            # We use a specific key that Apollo CSS will target to keep visible
            st.markdown("""
            <style>
            /* Ensure the sidebar toggle button is ALWAYS visible, even on Apollo page */
            /* Target by the Streamlit key class */
            .st-key-open_sidebar_btn,
            .st-key-open_sidebar_btn .stButton,
            .st-key-open_sidebar_btn .stButton button {
                display: inline-flex !important;
                visibility: visible !important;
                opacity: 1 !important;
                height: auto !important;
                width: auto !important;
                min-width: 120px !important;
                min-height: 40px !important;
                position: fixed !important;
                top: 70px !important;
                left: 10px !important;
                z-index: 100000 !important;
                pointer-events: auto !important;
                cursor: pointer !important;
            }
            .st-key-open_sidebar_btn .stButton button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 8px 16px !important;
                font-weight: 600 !important;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
                pointer-events: auto !important;
                cursor: pointer !important;
            }
            .st-key-open_sidebar_btn .stButton button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
            }
            </style>
            """, unsafe_allow_html=True)

            # Toggle button with unique key that CSS will target
            if st.button("☰ Open Sidebar", key="open_sidebar_btn", help="Open navigation sidebar", type="primary"):
                st.session_state.sidebar_open = True
                st.rerun()

    @staticmethod
    def show_sidebar_navigation():
        """
        Show persistent GLOBAL sidebar navigation.
        This navigation is IDENTICAL across ALL pages including Apollo.
        """
        # Ensure sidebar visibility is properly managed
        NavigationComponents._ensure_sidebar_visible()

        current_page = SessionManager.get_page()

        # Only show sidebar content if it's open
        if not st.session_state.get('sidebar_open', True):
            return current_page

        # CRITICAL: Fully disable Streamlit's default << collapse button and style our custom close button
        st.sidebar.markdown("""
        <style>
        /* COMPLETELY DISABLE Streamlit's default << collapse button */
        [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }

        /* Style the custom close button to be prominent and in top-left position */
        .st-key-close_sidebar_btn {
            position: relative !important;
            margin-bottom: 1rem !important;
        }

        .st-key-close_sidebar_btn button {
            width: 100% !important;
            height: 50px !important;
            font-size: 1.5rem !important;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3) !important;
        }

        .st-key-close_sidebar_btn button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.5) !important;
            background: linear-gradient(135deg, #ff5252 0%, #e63946 100%) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Close button - prominent, large, and clearly visible
        # This replaces the << chevron button
        if st.sidebar.button("✖️ Close", key="close_sidebar_btn", help="Close sidebar (temporary)", use_container_width=True):
            st.session_state.sidebar_open = False
            st.rerun()

        # Navigation header
        st.sidebar.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 1rem;
            text-align: center;
        ">
            <h2 style="margin: 0; font-size: 1.2rem;">🎭 Navigation</h2>
        </div>
        """, unsafe_allow_html=True)

        # GLOBAL Navigation buttons - same for ALL pages
        for icon_name, page_name, description in NavigationComponents.NAV_ITEMS:
            is_current = current_page == page_name
            button_style = "primary" if is_current else "secondary"

            if st.sidebar.button(
                icon_name,
                key=f"nav_{page_name}",
                type=button_style,
                help=description,
                use_container_width=True
            ):
                if page_name != current_page:
                    SessionManager.set_page(page_name)
                    # Reset sidebar to visible when navigating
                    st.session_state.sidebar_open = True
                    st.rerun()

        # Return current page
        return current_page
    
    @staticmethod
    def show_breadcrumbs():
        """Show breadcrumb navigation."""
        current_page = SessionManager.get_page()
        previous_page = st.session_state.get('previous_page')
        
        breadcrumb_html = f"<span style='color: #667eea;'>🏠 Home</span> → <strong>{current_page}</strong>"
        
        if previous_page and previous_page != current_page:
            breadcrumb_html = f"<span style='color: #667eea;'>🏠 Home</span> → <span style='color: #6c757d;'>{previous_page}</span> → <strong>{current_page}</strong>"
        
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
            font-size: 0.9rem;
        ">
            {breadcrumb_html}
        </div>
        """, unsafe_allow_html=True)
