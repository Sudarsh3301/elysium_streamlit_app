"""
Athena UI Components - User interface components for the Athena tab
Handles the client brief input, model selection, and results display.
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional
import os
import base64
import logging

# Import HTTPS image handling
from https_image_utils import https_image_handler

# Import enhanced UI components
from session_manager import SessionManager
from ui_components import LoadingComponents, NotificationComponents, ErrorComponents

# Try to import Athena core components
try:
    from athena_core import AthenaClient, ModelMatcher, EmailGenerator, PDFGenerator
    from template_manager import TemplateManager
    ATHENA_AVAILABLE = True
except ImportError as e:
    ATHENA_AVAILABLE = False
    # Create dummy classes to prevent import errors
    class AthenaClient:
        def __init__(self): pass
        def parse_client_brief(self, brief): return None
    class ModelMatcher:
        @staticmethod
        def find_matching_models(df, filters, max_results=5): return []
    class EmailGenerator:
        def __init__(self): pass
        def generate_email_pitch(self, brief, models, agent): return None
    class PDFGenerator:
        def __init__(self): pass
        def generate_multiple_pdfs(self, models, output_dir="pdfs"): return []
    class TemplateManager:
        def __init__(self): pass
        def get_available_templates(self): return {}

logger = logging.getLogger(__name__)

class AthenaUI:
    """Main UI controller for the Athena tab."""
    
    def __init__(self):
        self.athena_client = AthenaClient()
        self.email_generator = EmailGenerator()
        # Only initialize PDF generator and template manager if dependencies are available
        try:
            self.pdf_generator = PDFGenerator()
            self.template_manager = TemplateManager()
        except ImportError:
            self.pdf_generator = None
            self.template_manager = None
    
    def render_athena_tab(self, df: pd.DataFrame):
        """Render the complete Athena tab interface with enhanced split-view layout."""

        # Check if Athena is available
        if not ATHENA_AVAILABLE:
            ErrorComponents.show_error_card(
                "Athena Unavailable",
                "Athena functionality is not available due to missing dependencies.",
                [
                    "Install required packages: pip install reportlab pyperclip",
                    "Ensure Ollama is running with the gemma3:4b model",
                    "Check the requirements.txt file for complete dependencies"
                ]
            )
            return

        # Initialize session state for Athena
        self._initialize_athena_session_state()

        # Enhanced header with personality and status
        workflow_state = SessionManager.get_workflow_state()
        status_message = self._get_athena_status_message(workflow_state)

        st.markdown(f"""
        <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
            <h2>🏛️ Athena - Your AI Assistant</h2>
            <p>Transform client briefs into professional pitchbacks with intelligent model matching and PDF portfolios</p>
            <div style="margin-top: 1rem; padding: 0.5rem; background: rgba(255,255,255,0.1); border-radius: 6px;">
                <small>💬 {status_message}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Handle transfer data from other assistants with enhanced feedback
        transfer_data = SessionManager.get_transfer_data()
        if transfer_data and transfer_data.get('type') == 'model_transfer':
            self._render_transfer_notification(transfer_data)

        # Split-view layout: Client brief input on left, AI output on right
        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.markdown("### 📝 Client Brief Input")
            self._render_enhanced_client_brief_section()

            # Show parsed filters if available
            if st.session_state.athena_filters:
                self._render_parsed_filters()

            # Show matching models if available
            if st.session_state.matched_models:
                self._render_matching_models()

        with right_col:
            st.markdown("### 🤖 AI-Generated Output")
            self._render_ai_output_section()

        # Full-width sections below split view
        if st.session_state.selected_models:
            st.markdown("---")
            self._render_pdf_generation_section()

        # Show final preview if email is generated
        if st.session_state.pitch_email and st.session_state.pdf_paths:
            st.markdown("---")
            self._render_final_preview()
    
    def _initialize_athena_session_state(self):
        """Initialize session state variables for Athena."""
        if 'client_brief' not in st.session_state:
            st.session_state.client_brief = ""
        if 'athena_filters' not in st.session_state:
            st.session_state.athena_filters = {}
        if 'matched_models' not in st.session_state:
            st.session_state.matched_models = []
        if 'selected_models' not in st.session_state:
            st.session_state.selected_models = []
        if 'pitch_email' not in st.session_state:
            st.session_state.pitch_email = ""
        if 'pdf_paths' not in st.session_state:
            st.session_state.pdf_paths = []
        if 'agent_name' not in st.session_state:
            st.session_state.agent_name = "Athena"
    
    def _render_enhanced_client_brief_section(self):
        """Render the enhanced client brief input section with sample briefs and controls."""

        # Sample briefs dropdown
        sample_briefs = {
            "Select a sample brief...": "",
            "Cowboy Boots Campaign": "Hey Athena, I'm looking for a blonde, blue-eyed model between 21–26, size 0–4, to shoot a cowboy boots campaign in the desert. Need someone with a strong, confident look who can embody the rugged American spirit.",
            "Skincare Shoot in Miami": "Hi Athena, we need a fresh-faced model with clear skin for a luxury skincare campaign shooting in Miami next month. Looking for someone 5'7\" to 5'10\", natural beauty, minimal makeup look. Preferably brunette or dark blonde.",
            "Editorial Brand Launch": "Athena, seeking high-fashion editorial models for a luxury brand launch. Need tall, striking models (5'9\"+) with strong bone structure. Looking for diverse casting - different ethnicities and hair colors. Must have editorial experience."
        }

        selected_sample = st.selectbox(
            "📋 Sample Briefs",
            list(sample_briefs.keys()),
            help="Select a pre-written sample brief for quick testing"
        )

        # Auto-populate if sample selected
        if selected_sample != "Select a sample brief..." and sample_briefs[selected_sample]:
            if st.session_state.client_brief != sample_briefs[selected_sample]:
                st.session_state.client_brief = sample_briefs[selected_sample]
                st.rerun()

        # Client brief input
        client_brief = st.text_area(
            "Enter client brief:",
            value=st.session_state.client_brief,
            height=150,
            placeholder="Describe your casting needs, campaign details, and model requirements...",
            key="client_brief_input"
        )

        # Agent name input
        st.session_state.agent_name = st.text_input(
            "Agent Name:",
            value=st.session_state.agent_name,
            placeholder="Your name"
        )

        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔮 Generate Pitchback", type="primary", use_container_width=True):
                if client_brief.strip():
                    self._process_client_brief_with_status(client_brief.strip())
                else:
                    SessionManager.add_notification("Please enter a client brief first", "warning")

        with col2:
            if st.button("🔄 Clear Brief", use_container_width=True):
                st.session_state.client_brief = ""
                st.session_state.athena_filters = {}
                st.session_state.matched_models = []
                st.session_state.selected_models = []
                st.session_state.pitch_email = ""
                st.session_state.pdf_paths = []
                SessionManager.add_notification("Brief cleared successfully", "success")
                st.rerun()

        # Update session state
        st.session_state.client_brief = client_brief
    
    def _process_client_brief_with_status(self, client_brief: str):
        """Process the client brief through the AI pipeline with enhanced status feedback."""
        try:
            # Initialize processing status
            status_placeholder = st.empty()
            progress_bar = st.progress(0)

            # Step 1: Parse client brief
            status_placeholder.info("🧠 Parsing client brief...")
            progress_bar.progress(0.2)

            filters = self.athena_client.parse_client_brief(client_brief)

            if filters is None:
                status_placeholder.error("❌ Failed to connect to AI service")
                ErrorComponents.show_connection_error()
                return

            st.session_state.athena_filters = filters
            status_placeholder.success("✅ Client brief parsed successfully")
            progress_bar.progress(0.4)

            # Step 2: Find matching models
            status_placeholder.info("🔍 Finding matching models...")
            progress_bar.progress(0.6)

            if filters:
                df = st.session_state.get('df_cache')
                if df is not None and not df.empty:
                    matched_models = ModelMatcher.find_matching_models(df, filters, max_results=5)
                    st.session_state.matched_models = matched_models

                    if matched_models:
                        status_placeholder.success(f"✅ Found {len(matched_models)} matching models!")
                        progress_bar.progress(0.8)
                    else:
                        status_placeholder.warning("⚠️ No models found matching the criteria")
                        progress_bar.progress(0.8)
                else:
                    status_placeholder.error("❌ Model data not available")
                    ErrorComponents.show_data_error()
                    return

            # Step 3: Auto-generate email if models found
            if st.session_state.matched_models:
                status_placeholder.info("📧 Generating email draft...")
                progress_bar.progress(0.9)

                # Auto-select first 3 models for quick demo
                st.session_state.selected_models = st.session_state.matched_models[:3]

                # Generate email automatically
                email_content = self.email_generator.generate_email_pitch(
                    client_brief,
                    st.session_state.selected_models,
                    st.session_state.agent_name
                )

                if email_content:
                    st.session_state.pitch_email = email_content
                    status_placeholder.success("✅ Email draft generated successfully!")
                    progress_bar.progress(1.0)
                    SessionManager.add_notification("Pitchback ready for review!", "success")
                else:
                    status_placeholder.warning("⚠️ Email generation failed")

            # Clear status after delay
            import time
            time.sleep(2)
            status_placeholder.empty()
            progress_bar.empty()

        except Exception as e:
            SessionManager.log_error(e, "Client brief processing")
            st.error(f"❌ Processing failed: {str(e)}")
            ErrorComponents.show_error_card(
                "Processing Error",
                f"Failed to process client brief: {str(e)}",
                ["Check your internet connection", "Ensure Ollama is running", "Try simplifying the brief"]
            )
    
    def _render_ai_output_section(self):
        """Render the AI output section in the right column."""
        if not st.session_state.pitch_email:
            # Show placeholder when no output yet
            st.markdown("""
            <div style="
                padding: 2rem;
                text-align: center;
                background: #f8f9fa;
                border-radius: 10px;
                border: 2px dashed #dee2e6;
                margin: 1rem 0;
                min-height: 300px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📧</div>
                <h3 style="color: #6c757d; margin-bottom: 0.5rem;">AI Draft Ready</h3>
                <p style="color: #6c757d;">Enter a client brief and click Generate to see your AI-powered pitchback email here</p>
            </div>
            """, unsafe_allow_html=True)
            return

        # Show generated email with edit controls
        st.markdown("#### 📧 Generated Email Draft")

        # Regenerate and Edit controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Regenerate", help="Generate a new draft using the same brief"):
                if st.session_state.client_brief and st.session_state.selected_models:
                    with st.spinner("Regenerating email draft..."):
                        new_email = self.email_generator.generate_email_pitch(
                            st.session_state.client_brief,
                            st.session_state.selected_models,
                            st.session_state.agent_name
                        )
                        if new_email:
                            st.session_state.pitch_email = new_email
                            SessionManager.add_notification("New draft generated!", "success")
                            st.rerun()

        with col2:
            edit_mode = st.checkbox("✏️ Edit Inline", help="Enable inline editing of the generated text")

        # Display email content (editable or read-only)
        if edit_mode:
            edited_email = st.text_area(
                "Edit your email:",
                value=st.session_state.pitch_email,
                height=400,
                key="email_editor"
            )
            if edited_email != st.session_state.pitch_email:
                st.session_state.pitch_email = edited_email
                SessionManager.add_notification("Email updated", "info")
        else:
            # Read-only display with nice formatting
            st.markdown(f"""
            <div style="
                background: white;
                padding: 1.5rem;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                max-height: 400px;
                overflow-y: auto;
            ">
                {st.session_state.pitch_email.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

    def _render_parsed_filters(self):
        """Render the parsed filters section."""
        st.markdown("#### 🎯 AI-Parsed Requirements")

        if not st.session_state.athena_filters:
            st.info("No filters parsed yet")
            return

        # Display filters in a compact format
        filters = st.session_state.athena_filters
        filter_items = []

        if filters.get('hair_color'):
            filter_items.append(f"💇 {filters['hair_color'].title()}")
        if filters.get('eye_color'):
            filter_items.append(f"👁️ {filters['eye_color'].title()}")
        if filters.get('division'):
            filter_items.append(f"📋 {filters['division'].upper()}")
        if filters.get('campaign_type'):
            filter_items.append(f"📸 {filters['campaign_type'].title()}")
        if filters.get('location'):
            filter_items.append(f"📍 {filters['location'].title()}")

        # Display as tags
        if filter_items:
            tags_html = " ".join([f'<span style="background: #e3f2fd; padding: 0.2rem 0.5rem; border-radius: 12px; font-size: 0.8rem; margin: 0.1rem;">{item}</span>' for item in filter_items])
            st.markdown(f'<div style="margin: 0.5rem 0;">{tags_html}</div>', unsafe_allow_html=True)

        # Show raw filters in expander
        with st.expander("🔍 View Raw Filters"):
            st.json(filters)
    
    def _render_matching_models(self):
        """Render the matching models section with selection toggles."""
        st.subheader("🎭 Matching Models")
        
        if not st.session_state.matched_models:
            st.info("No matching models found.")
            return
        
        # Create model selection cards
        cols = st.columns(min(len(st.session_state.matched_models), 3))
        
        for idx, model in enumerate(st.session_state.matched_models):
            col_idx = idx % len(cols)
            
            with cols[col_idx]:
                self._render_model_selection_card(model, idx)
        
        # Show selected models summary
        if st.session_state.selected_models:
            st.success(f"✅ {len(st.session_state.selected_models)} models selected for pitchback")
    
    def _render_model_selection_card(self, model: Dict[str, Any], index: int):
        """Render a single model selection card."""
        with st.container():
            # Model image
            thumbnail_path = self._get_model_thumbnail(model)
            
            try:
                st.image(thumbnail_path, width=250, caption="")
            except:
                st.image("https://via.placeholder.com/250x300/cccccc/666666?text=No+Image", width=250)
            
            # Model details
            st.markdown(f"**{model['name']}**")
            st.markdown(f"*{model['division'].upper()} Division*")
            
            # Attributes
            attr_col1, attr_col2 = st.columns(2)
            with attr_col1:
                st.markdown(f"👁️ {model['eye_color'].title()}")
                st.markdown(f"📏 {int(model['height_cm'])} cm")
            with attr_col2:
                st.markdown(f"💇 {model['hair_color'].title()}")
                if model.get('waist'):
                    st.markdown(f"👗 {model['waist']} waist")
            
            # Selection toggle
            model_id = model['model_id']
            is_selected = any(m['model_id'] == model_id for m in st.session_state.selected_models)
            
            if st.checkbox(
                "Include in Pitchback",
                value=is_selected,
                key=f"select_model_{model_id}_{index}"
            ):
                # Add to selected models if not already there
                if not is_selected:
                    st.session_state.selected_models.append(model)
            else:
                # Remove from selected models if it was there
                if is_selected:
                    st.session_state.selected_models = [
                        m for m in st.session_state.selected_models 
                        if m['model_id'] != model_id
                    ]
            
            st.markdown("---")
    
    def _get_model_thumbnail(self, model: Dict[str, Any]) -> str:
        """
        REFACTORED: Get thumbnail HTTPS URL for a model.
        """
        return https_image_handler.get_thumbnail_url(model)

    def _generate_template_pdfs(self, models: List[Dict], template_name: str, client_brief: str) -> List[str]:
        """Generate PDFs using the selected template."""
        try:
            # Preprocess data for template
            data = self.template_manager.preprocess_data(
                template_name=template_name,
                models=models,
                client_brief=client_brief,
                agent_name=st.session_state.get('agent_name', 'Athena')
            )

            # Render HTML template
            html_content = self.template_manager.render_template(template_name, data)

            # Generate PDF using the enhanced PDF generator
            pdf_path = self.pdf_generator.generate_template_pdf(
                html_content=html_content,
                template_name=template_name,
                models=models
            )

            return [pdf_path] if pdf_path else []

        except Exception as e:
            logger.error(f"Error generating template PDFs: {e}")
            raise
    
    def _render_template_selection(self):
        """Render the PDF template selection section."""
        st.subheader("🎨 Choose PDF Template Style")

        if self.template_manager:
            available_templates = self.template_manager.get_available_templates()

            # Create template selection with descriptions
            template_options = []
            template_descriptions = []

            for template_name, config in available_templates.items():
                template_options.append(template_name)
                template_descriptions.append(f"**{template_name}**: {config['description']} (Max {config['max_models']} models)")

            # Display template descriptions
            st.markdown("**Available Templates:**")
            for desc in template_descriptions:
                st.markdown(f"• {desc}")

            # Template selection dropdown
            selected_template = st.selectbox(
                "Choose Deck Template:",
                template_options,
                index=0,
                key="selected_template",
                help="Select the PDF template style that best fits your campaign needs"
            )

            # Validate template selection with current models
            if 'selected_models' in st.session_state and st.session_state.selected_models:
                is_valid, message = self.template_manager.validate_template_selection(
                    selected_template,
                    st.session_state.selected_models
                )

                if not is_valid:
                    st.warning(f"⚠️ {message}")
                else:
                    st.success(f"✅ {message}")

            return selected_template
        else:
            st.warning("📄 Template selection not available - install jinja2")
            return "Agency Standard"

    def _render_email_generation_section(self):
        """Render the email generation section."""
        st.subheader("📧 Generate Pitchback Email")

        # Add template selection
        selected_template = self._render_template_selection()
        
        if st.button("✨ Generate Professional Email & PDFs", type="primary"):
            with st.spinner("🤖 Generating professional email pitch..."):
                email_content = self.email_generator.generate_email_pitch(
                    st.session_state.client_brief,
                    st.session_state.selected_models,
                    st.session_state.agent_name
                )

                if email_content:
                    st.session_state.pitch_email = email_content

                    # Generate PDFs using selected template
                    if self.pdf_generator and self.template_manager:
                        with st.spinner(f"📄 Generating {selected_template} PDF portfolios..."):
                            try:
                                # Use the new template-based PDF generation
                                pdf_paths = self._generate_template_pdfs(
                                    st.session_state.selected_models,
                                    selected_template,
                                    st.session_state.client_brief
                                )
                                st.session_state.pdf_paths = pdf_paths
                                st.session_state.selected_template_name = selected_template
                            except Exception as e:
                                st.error(f"❌ PDF generation failed: {e}")
                                st.session_state.pdf_paths = []
                    else:
                        st.warning("📄 PDF generation not available - install reportlab and jinja2")
                        st.session_state.pdf_paths = []

                    st.success("✅ Email and PDFs generated successfully!")
                else:
                    st.error("❌ Failed to generate email. Please try again.")
    
    def _render_final_preview(self):
        """Render the final preview section with email and PDFs."""
        st.subheader("📋 Final Pitchback Preview")
        
        # Email preview
        st.markdown("### 📧 Email Preview")
        st.text_area(
            "Generated Email:",
            value=st.session_state.pitch_email,
            height=300,
            key="email_preview"
        )
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Copy Email to Clipboard"):
                try:
                    import pyperclip
                    pyperclip.copy(st.session_state.pitch_email)
                    st.success("✅ Email copied to clipboard!")
                except ImportError:
                    st.warning("⚠️ Clipboard functionality not available")
        
        with col2:
            if st.session_state.pdf_paths:
                # Create a zip file with all PDFs for download
                import zipfile
                import tempfile
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                    with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                        for pdf_path in st.session_state.pdf_paths:
                            if os.path.exists(pdf_path):
                                zip_file.write(pdf_path, os.path.basename(pdf_path))
                    
                    with open(tmp_file.name, 'rb') as f:
                        st.download_button(
                            "📄 Download All PDFs",
                            data=f.read(),
                            file_name="model_portfolios.zip",
                            mime="application/zip"
                        )
        
        with col3:
            if st.button("🔄 Start New Brief"):
                # Reset all Athena session state
                for key in ['client_brief', 'athena_filters', 'matched_models', 
                           'selected_models', 'pitch_email', 'pdf_paths']:
                    if key in st.session_state:
                        if key == 'client_brief':
                            st.session_state[key] = ""
                        elif key in ['athena_filters']:
                            st.session_state[key] = {}
                        else:
                            st.session_state[key] = []
                st.rerun()
        
        # PDF thumbnails
        if st.session_state.pdf_paths:
            st.markdown("### 📄 Generated PDF Portfolios")
            
            pdf_cols = st.columns(min(len(st.session_state.pdf_paths), 4))
            
            for idx, pdf_path in enumerate(st.session_state.pdf_paths):
                col_idx = idx % len(pdf_cols)
                
                with pdf_cols[col_idx]:
                    if os.path.exists(pdf_path):
                        st.markdown(f"**{os.path.basename(pdf_path)}**")
                        st.markdown("📄 PDF Ready")
                        
                        # Individual download button
                        with open(pdf_path, 'rb') as f:
                            st.download_button(
                                "Download",
                                data=f.read(),
                                file_name=os.path.basename(pdf_path),
                                mime="application/pdf",
                                key=f"download_pdf_{idx}"
                            )
                    else:
                        st.error(f"PDF not found: {pdf_path}")

    def _render_pdf_generation_section(self):
        """Render the PDF generation section with template selection."""
        st.markdown("### 📄 PDF Portfolio Generation")

        # Template selection section
        col1, col2 = st.columns([2, 1])

        with col1:
            self._render_enhanced_template_selection()

        with col2:
            st.markdown("#### 📊 Generation Status")
            if st.session_state.pdf_paths:
                st.success("✅ PDF Ready")
                st.info(f"📁 {len(st.session_state.pdf_paths)} file(s) generated")
            else:
                st.info("⏳ Ready to generate")

        # Generate PDF button
        if st.button("📄 Generate PDF Portfolio", type="primary", use_container_width=True):
            if st.session_state.selected_models and st.session_state.pitch_email:
                self._generate_pdf_with_feedback()
            else:
                SessionManager.add_notification("Please ensure email is generated first", "warning")

    def _render_enhanced_template_selection(self):
        """Render enhanced PDF template selection with descriptions."""
        if not self.template_manager:
            st.warning("Template manager not available")
            return

        # Template options with descriptions
        template_options = {
            "Agency Standard": "Single-model one-pager with hero image and measurements",
            "Campaign Pitch": "Multi-model campaign deck with cover page",
            "Compact Comp": "Compact comparison sheet for multiple models"
        }

        # Template selection dropdown
        selected_template = st.selectbox(
            "Choose Deck Template:",
            list(template_options.keys()),
            index=0,
            key="selected_template",
            help="Select the PDF template style that best fits your campaign needs"
        )

        # Show template description
        if selected_template in template_options:
            st.info(f"📋 {template_options[selected_template]}")

    def _generate_pdf_with_feedback(self):
        """Generate PDF with comprehensive feedback."""
        try:
            # Get selected template
            selected_template = st.session_state.get('selected_template', 'Agency Standard')

            # Progress tracking
            progress_placeholder = st.empty()
            progress_bar = st.progress(0)

            progress_placeholder.info("📄 Preparing PDF template...")
            progress_bar.progress(0.2)

            if self.pdf_generator and self.template_manager:
                progress_placeholder.info(f"🎨 Rendering {selected_template} template...")
                progress_bar.progress(0.4)

                # Generate PDFs using selected template
                pdf_paths = self._generate_template_pdfs(
                    st.session_state.selected_models,
                    selected_template,
                    st.session_state.client_brief
                )

                progress_placeholder.info("💾 Saving PDF files...")
                progress_bar.progress(0.8)

                st.session_state.pdf_paths = pdf_paths
                st.session_state.selected_template_name = selected_template

                progress_placeholder.success("✅ PDF portfolio generated successfully!")
                progress_bar.progress(1.0)

                SessionManager.add_notification(f"PDF generated using {selected_template} template!", "success")

                # Show thumbnail preview if possible
                if pdf_paths:
                    st.info(f"📁 Generated {len(pdf_paths)} PDF file(s)")

                # Clear progress after delay
                import time
                time.sleep(2)
                progress_placeholder.empty()
                progress_bar.empty()

            else:
                progress_placeholder.error("❌ PDF generation not available")
                st.warning("📄 PDF generation requires additional dependencies")

        except Exception as e:
            SessionManager.log_error(e, "PDF generation")
            st.error(f"❌ PDF generation failed: {str(e)}")
            ErrorComponents.show_error_card(
                "PDF Generation Error",
                f"Failed to generate PDF: {str(e)}",
                ["Check template files", "Ensure all dependencies are installed", "Try with fewer models"]
            )

    def _get_athena_status_message(self, workflow_state: str) -> str:
        """Get personalized status message based on workflow state."""
        messages = {
            'idle': "Ready to help you create amazing client pitches! What's your vision today?",
            'apollo_to_athena': "I see you've sent me a model from Apollo - let's build something great together!",
            'catalogue_to_athena': "Perfect choice from the Catalogue! I'll help you craft the perfect pitch.",
            'processing': "Working my magic on your brief... almost there!",
            'complete': "Your pitch is ready! Need any adjustments or shall we generate the PDF?"
        }
        return messages.get(workflow_state, messages['idle'])

    def _render_transfer_notification(self, transfer_data: dict):
        """Render enhanced transfer notification with personality."""
        model_data = transfer_data['model_data']
        source = transfer_data['source']

        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            border-left: 4px solid #00FF88;
            animation: slideIn 0.5s ease-out;
        ">
            <h4 style="margin: 0 0 0.5rem 0; color: white;">🎯 Athena here! I've received a model from {source}</h4>
            <p style="margin: 0.5rem 0; color: white;">
                <strong>{model_data['name']}</strong> from {model_data['division'].upper()} division looks perfect for your campaign!
                Let me help you craft the perfect brief.
            </p>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-top: 1rem; color: #e0e0e0;">
                💡 <em>I'm your AI assistant for client briefs and model matching. I speak your language and understand fashion!</em>
            </div>
        </div>
        <style>
        @keyframes slideIn {{
            from {{ transform: translateX(-100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        </style>
        """, unsafe_allow_html=True)

        # Pre-fill brief with model context and personality
        suggested_brief = f"I'm looking for models with a similar vibe to {model_data['name']} from our {model_data['division']} division. "
        suggested_brief += f"Think {model_data['hair_color']} hair, {model_data['eye_color']} eyes, around {model_data['height_cm']}cm. "
        suggested_brief += "Perfect for a campaign that needs that same energy and look!"

        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("✨ Use Athena's Suggested Brief", type="primary", use_container_width=True):
                st.session_state.client_brief = suggested_brief
                SessionManager.clear_transfer_data()
                SessionManager.add_notification("Brief pre-filled with model context! Ready to find matches.", "success")
                st.rerun()

        with col2:
            if st.button("🗑️ Dismiss", type="secondary", use_container_width=True):
                SessionManager.clear_transfer_data()
                st.rerun()
