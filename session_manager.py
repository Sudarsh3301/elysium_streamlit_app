"""
Centralized Session State Management for Elysium Streamlit App
Handles all session state initialization, management, and reset functionality.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SessionManager:
    """Centralized session state manager for the Elysium app."""
    
    # Default session state structure
    DEFAULT_STATE = {
        # Navigation and UI state
        'current_page': 'Catalogue',
        'previous_page': None,
        'sidebar_expanded': True,
        'loading_state': False,
        'loading_message': '',
        'notifications': [],
        
        # Catalogue state
        'ai_filters': {},
        'selected_model': None,
        'current_model_index': 0,
        'hover_model': None,
        'manual_filters': {
            'hair_colors': [],
            'eye_colors': [],
            'divisions': [],
            'height_range': (150, 200)
        },
        
        # Athena state
        'client_brief': '',
        'athena_filters': {},
        'matched_models': [],
        'selected_models': [],
        'pitch_email': '',
        'pdf_paths': [],
        'agent_name': 'Athena',
        'context_intent': 'general',
        'athena_prefill': {},
        'selected_template': 'Agency Standard',

        # Apollo state
        'selected_clients': [],
        'active_tab': 'Catalogue',
        'apollo_filters': {},
        'dashboard_data': {},
        'apollo_selected_model': None,
        'apollo_insights': [],

        # Cross-assistant integration state
        'transfer_data': {},
        'transfer_source': None,
        'transfer_target': None,
        'integration_messages': [],
        'shared_model_context': None,
        'workflow_state': 'idle',  # idle, apollo_to_athena, catalogue_to_apollo, etc.
        
        # Data cache
        'df_cache': None,
        'data_loaded': False,
        'data_load_time': None,
        
        # User preferences
        'theme': 'light',
        'results_per_page': 20,
        'auto_refresh': True,
        
        # Error handling
        'last_error': None,
        'error_count': 0,
        'error_history': [],
        
        # Session metadata
        'session_id': None,
        'session_start_time': None,
        'last_activity': None,
        'version': '0.4.0'
    }
    
    @staticmethod
    def initialize_session():
        """Initialize all session state variables with safe defaults."""
        try:
            # Set session metadata
            if 'session_start_time' not in st.session_state:
                st.session_state.session_start_time = datetime.now()
                st.session_state.session_id = f"elysium_{int(datetime.now().timestamp())}"
            
            # Initialize all default state variables
            for key, default_value in SessionManager.DEFAULT_STATE.items():
                if key not in st.session_state:
                    st.session_state[key] = default_value
                    
            # Update last activity
            st.session_state.last_activity = datetime.now()
            
            logger.info(f"Session initialized: {st.session_state.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize session state: {e}")
            # Fallback initialization
            for key, default_value in SessionManager.DEFAULT_STATE.items():
                try:
                    if key not in st.session_state:
                        st.session_state[key] = default_value
                except Exception:
                    pass
    
    @staticmethod
    def reset_session(preserve_data_cache: bool = True):
        """Reset session state to defaults, optionally preserving data cache."""
        try:
            # Preserve certain values if requested
            preserved_values = {}
            if preserve_data_cache:
                preserved_values = {
                    'df_cache': st.session_state.get('df_cache'),
                    'data_loaded': st.session_state.get('data_loaded'),
                    'data_load_time': st.session_state.get('data_load_time'),
                    'session_id': st.session_state.get('session_id'),
                    'session_start_time': st.session_state.get('session_start_time')
                }
            
            # Clear all session state
            for key in list(st.session_state.keys()):
                if not key.startswith('_'):  # Don't clear Streamlit internal keys
                    del st.session_state[key]
            
            # Reinitialize with defaults
            SessionManager.initialize_session()
            
            # Restore preserved values
            for key, value in preserved_values.items():
                if value is not None:
                    st.session_state[key] = value
            
            # Add notification about reset
            SessionManager.add_notification("Session reset successfully", "success")
            
            logger.info("Session state reset completed")
            
        except Exception as e:
            logger.error(f"Failed to reset session state: {e}")
            SessionManager.add_notification(f"Reset failed: {str(e)}", "error")
    
    @staticmethod
    def set_page(page_name: str):
        """Set current page and update navigation history."""
        try:
            if 'current_page' in st.session_state:
                st.session_state.previous_page = st.session_state.current_page
            st.session_state.current_page = page_name
            st.session_state.last_activity = datetime.now()
            logger.debug(f"Page changed to: {page_name}")
        except Exception as e:
            logger.error(f"Failed to set page: {e}")
    
    @staticmethod
    def get_page() -> str:
        """Get current page name."""
        return st.session_state.get('current_page', 'Catalogue')
    
    @staticmethod
    def set_loading(is_loading: bool, message: str = ''):
        """Set global loading state."""
        try:
            st.session_state.loading_state = is_loading
            st.session_state.loading_message = message
            if is_loading:
                logger.debug(f"Loading started: {message}")
            else:
                logger.debug("Loading completed")
        except Exception as e:
            logger.error(f"Failed to set loading state: {e}")
    
    @staticmethod
    def is_loading() -> bool:
        """Check if app is in loading state."""
        return st.session_state.get('loading_state', False)
    
    @staticmethod
    def get_loading_message() -> str:
        """Get current loading message."""
        return st.session_state.get('loading_message', '')
    
    @staticmethod
    def add_notification(message: str, type: str = 'info', duration: int = 5):
        """Add a notification to the queue."""
        try:
            if 'notifications' not in st.session_state:
                st.session_state.notifications = []
            
            notification = {
                'message': message,
                'type': type,  # 'success', 'error', 'warning', 'info'
                'timestamp': datetime.now(),
                'duration': duration
            }
            
            st.session_state.notifications.append(notification)
            logger.debug(f"Notification added: {type} - {message}")
            
        except Exception as e:
            logger.error(f"Failed to add notification: {e}")
    
    @staticmethod
    def get_notifications() -> List[Dict[str, Any]]:
        """Get all current notifications."""
        return st.session_state.get('notifications', [])
    
    @staticmethod
    def clear_notifications():
        """Clear all notifications."""
        try:
            st.session_state.notifications = []
        except Exception as e:
            logger.error(f"Failed to clear notifications: {e}")
    
    @staticmethod
    def log_error(error: Exception, context: str = ''):
        """Log an error and add to error history."""
        try:
            error_info = {
                'error': str(error),
                'context': context,
                'timestamp': datetime.now(),
                'page': st.session_state.get('current_page', 'Unknown')
            }
            
            st.session_state.last_error = error_info
            st.session_state.error_count = st.session_state.get('error_count', 0) + 1
            
            if 'error_history' not in st.session_state:
                st.session_state.error_history = []
            
            st.session_state.error_history.append(error_info)
            
            # Keep only last 10 errors
            if len(st.session_state.error_history) > 10:
                st.session_state.error_history = st.session_state.error_history[-10:]
            
            logger.error(f"Error logged: {context} - {error}")
            
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    @staticmethod
    def get_session_info() -> Dict[str, Any]:
        """Get session information for debugging/status display."""
        try:
            from datetime import datetime

            # Calculate session duration
            start_time = st.session_state.get('session_start_time')
            session_duration = "Unknown"
            if start_time:
                duration_delta = datetime.now() - start_time
                hours, remainder = divmod(duration_delta.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                session_duration = f"{int(hours):02d}:{int(minutes):02d}"

            # Get last update time
            last_update = "Never"
            data_load_time = st.session_state.get('data_load_time')
            if data_load_time:
                last_update = data_load_time.strftime("%H:%M:%S")

            return {
                'session_id': st.session_state.get('session_id'),
                'start_time': st.session_state.get('session_start_time'),
                'session_duration': session_duration,
                'last_activity': st.session_state.get('last_activity'),
                'last_update': last_update,
                'current_page': st.session_state.get('current_page'),
                'error_count': st.session_state.get('error_count', 0),
                'errors': st.session_state.get('errors', []),
                'data_loaded': st.session_state.get('data_loaded', False),
                'version': st.session_state.get('version', '0.4.0')
            }
        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return {}
    
    @staticmethod
    def update_user_preference(key: str, value: Any):
        """Update a user preference."""
        try:
            if key in ['theme', 'results_per_page', 'auto_refresh']:
                st.session_state[key] = value
                logger.debug(f"User preference updated: {key} = {value}")
            else:
                logger.warning(f"Invalid preference key: {key}")
        except Exception as e:
            logger.error(f"Failed to update preference: {e}")
    
    @staticmethod
    def get_user_preference(key: str, default: Any = None) -> Any:
        """Get a user preference value."""
        return st.session_state.get(key, default)

    # Cross-Assistant Integration Methods

    @staticmethod
    def transfer_model_to_athena(model_data: Dict[str, Any], source: str = "Apollo"):
        """Transfer model data from another assistant to Athena."""
        try:
            st.session_state.transfer_data = {
                'type': 'model_transfer',
                'model_data': model_data,
                'timestamp': datetime.now(),
                'source': source
            }
            st.session_state.transfer_source = source
            st.session_state.transfer_target = 'Athena'
            st.session_state.workflow_state = f'{source.lower()}_to_athena'

            # Pre-populate Athena with model context
            st.session_state.athena_prefill = {
                'model_name': model_data.get('name', ''),
                'model_id': model_data.get('model_id', ''),
                'division': model_data.get('division', ''),
                'attributes': {
                    'hair_color': model_data.get('hair_color', ''),
                    'eye_color': model_data.get('eye_color', ''),
                    'height_cm': model_data.get('height_cm', 0)
                }
            }

            # Add integration message
            SessionManager.add_integration_message(
                f"Model {model_data.get('name', 'Unknown')} sent to Athena from {source}",
                "success"
            )

            logger.info(f"Model transferred to Athena from {source}: {model_data.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Failed to transfer model to Athena: {e}")
            SessionManager.add_integration_message("Failed to transfer model to Athena", "error")

    @staticmethod
    def set_shared_model_context(model_data: Dict[str, Any]):
        """Set shared model context for cross-assistant analytics."""
        try:
            st.session_state.shared_model_context = {
                'model_data': model_data,
                'timestamp': datetime.now(),
                'active': True
            }

            # Update Apollo to reflect this model's analytics
            st.session_state.apollo_selected_model = model_data.get('model_id')

            logger.info(f"Shared model context set: {model_data.get('name', 'Unknown')}")

        except Exception as e:
            logger.error(f"Failed to set shared model context: {e}")

    @staticmethod
    def add_integration_message(message: str, message_type: str = "info"):
        """Add a cross-assistant integration message."""
        try:
            if 'integration_messages' not in st.session_state:
                st.session_state.integration_messages = []

            st.session_state.integration_messages.append({
                'message': message,
                'type': message_type,
                'timestamp': datetime.now(),
                'id': f"msg_{int(datetime.now().timestamp())}"
            })

            # Keep only last 10 messages
            if len(st.session_state.integration_messages) > 10:
                st.session_state.integration_messages = st.session_state.integration_messages[-10:]

        except Exception as e:
            logger.error(f"Failed to add integration message: {e}")

    @staticmethod
    def get_integration_messages() -> List[Dict[str, Any]]:
        """Get recent integration messages."""
        return st.session_state.get('integration_messages', [])

    @staticmethod
    def clear_integration_messages():
        """Clear all integration messages."""
        st.session_state.integration_messages = []

    @staticmethod
    def get_transfer_data() -> Optional[Dict[str, Any]]:
        """Get pending transfer data."""
        return st.session_state.get('transfer_data')

    @staticmethod
    def clear_transfer_data():
        """Clear transfer data after processing."""
        st.session_state.transfer_data = {}
        st.session_state.transfer_source = None
        st.session_state.transfer_target = None
        st.session_state.workflow_state = 'idle'

    @staticmethod
    def get_workflow_state() -> str:
        """Get current cross-assistant workflow state."""
        return st.session_state.get('workflow_state', 'idle')
