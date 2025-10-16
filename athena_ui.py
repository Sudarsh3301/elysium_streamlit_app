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

# Try to import Athena core components
try:
    from athena_core import AthenaClient, ModelMatcher, EmailGenerator, PDFGenerator
    from template_manager import TemplateManager
    ATHENA_AVAILABLE = True
except ImportError as e:
    ATHENA_AVAILABLE = False
    st.error(f"Athena functionality requires additional packages: {e}")
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
        """Render the complete Athena tab interface."""

        # Check if Athena is available
        if not ATHENA_AVAILABLE:
            st.error("🚫 Athena functionality is not available")
            st.info("📦 Please install required packages:")
            st.code("pip install reportlab pyperclip")
            st.info("🤖 Also ensure Ollama is running with the gemma3:4b model")
            return

        # Initialize session state for Athena
        self._initialize_athena_session_state()
        
        # Header section
        st.markdown("""
        <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
            <h2>🏛️ Athena - AI Agent Assistant</h2>
            <p>Paste a client brief, find matching models, and generate professional pitchbacks with PDF portfolios</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Client brief input section
        self._render_client_brief_section()
        
        # Show parsed filters if available
        if st.session_state.athena_filters:
            self._render_parsed_filters()
        
        # Show matching models if available
        if st.session_state.matched_models:
            self._render_matching_models()
        
        # Show email generation section if models are selected
        if st.session_state.selected_models:
            self._render_email_generation_section()
        
        # Show final preview if email is generated
        if st.session_state.pitch_email:
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
    
    def _render_client_brief_section(self):
        """Render the client brief input section."""
        st.subheader("📝 Client Brief")
        
        # Agent name input
        col1, col2 = st.columns([2, 1])
        with col1:
            client_brief = st.text_area(
                "Enter client brief:",
                value=st.session_state.client_brief,
                height=120,
                placeholder="Hey Athena, I'm looking for a blonde, blue-eyed model between 21–26, size 0–4, to shoot a cowboy boots campaign in the desert.",
                key="client_brief_input"
            )
        
        with col2:
            st.session_state.agent_name = st.text_input(
                "Agent Name:",
                value=st.session_state.agent_name,
                placeholder="Your name"
            )
            
            # Generate button
            if st.button("🔮 Generate Pitchback", type="primary", use_container_width=True):
                if client_brief.strip():
                    self._process_client_brief(client_brief.strip())
                else:
                    st.warning("⚠️ Please enter a client brief first")
        
        # Update session state
        st.session_state.client_brief = client_brief
    
    def _process_client_brief(self, client_brief: str):
        """Process the client brief through the AI pipeline."""
        with st.spinner("🧠 Processing client brief with AI..."):
            # Step 1: Parse filters
            filters = self.athena_client.parse_client_brief(client_brief)
            
            if filters is None:
                st.error("❌ Failed to connect to Ollama. Please ensure it's running.")
                return
            
            st.session_state.athena_filters = filters
            
            # Step 2: Find matching models
            if filters:
                df = st.session_state.get('df_cache')  # Get cached dataframe
                if df is not None and not df.empty:
                    matched_models = ModelMatcher.find_matching_models(df, filters, max_results=5)
                    st.session_state.matched_models = matched_models
                    
                    if matched_models:
                        st.success(f"✅ Found {len(matched_models)} matching models!")
                    else:
                        st.warning("⚠️ No models found matching the criteria. Try adjusting the brief.")
                else:
                    st.error("❌ Model data not available")
            else:
                st.warning("⚠️ Could not extract filters from the brief. Please try rephrasing.")
    
    def _render_parsed_filters(self):
        """Render the parsed filters section."""
        st.subheader("🎯 AI-Parsed Requirements")
        
        # Display filters in a nice format
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.athena_filters.get('hair_color'):
                st.info(f"💇 Hair: {st.session_state.athena_filters['hair_color'].title()}")
            if st.session_state.athena_filters.get('eye_color'):
                st.info(f"👁️ Eyes: {st.session_state.athena_filters['eye_color'].title()}")
            if st.session_state.athena_filters.get('division'):
                st.info(f"📋 Division: {st.session_state.athena_filters['division'].upper()}")
        
        with col2:
            if st.session_state.athena_filters.get('size_min') is not None or st.session_state.athena_filters.get('size_max') is not None:
                size_min = st.session_state.athena_filters.get('size_min', 0)
                size_max = st.session_state.athena_filters.get('size_max', 20)
                st.info(f"👗 Size: {size_min}-{size_max}")
            if st.session_state.athena_filters.get('campaign_type'):
                st.info(f"📸 Campaign: {st.session_state.athena_filters['campaign_type'].title()}")
            if st.session_state.athena_filters.get('location'):
                st.info(f"📍 Location: {st.session_state.athena_filters['location'].title()}")
        
        # Show raw filters in expander
        with st.expander("🔍 View Raw Filters"):
            st.json(st.session_state.athena_filters)
    
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
                st.markdown(f"📏 {model['height_cm']} cm")
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
        """Get the best available thumbnail for a model."""
        images = model.get('images', [])
        if images:
            # Look for thumbnail first
            for img in images:
                if 'thumbnail' in img.lower():
                    local_path = os.path.join("..", "elysium_kb", img.lstrip('/'))
                    if os.path.exists(local_path):
                        return local_path
            
            # Use first image if no thumbnail
            first_img = images[0]
            local_path = os.path.join("..", "elysium_kb", first_img.lstrip('/'))
            if os.path.exists(local_path):
                return local_path
        
        # Fallback to remote thumbnail
        if model.get('thumbnail'):
            return model['thumbnail']
        
        return "https://via.placeholder.com/250x300/cccccc/666666?text=No+Image"

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
