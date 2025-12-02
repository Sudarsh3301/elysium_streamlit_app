"""
Athena Core Module - AI-powered client brief processing and model matching
Handles LLM parsing, model search/ranking, and PDF generation for the Athena tab.
"""

import json
import os
import base64
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from pathlib import Path
import logging
import tempfile

# Import Groq client
from groq_client import GroqClient

# Optional imports for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    from io import BytesIO
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)

class AthenaClient:
    """Handles AI query parsing specifically for client briefs using Groq API."""

    def __init__(self):
        """Initialize Groq client for AI-powered brief parsing."""
        try:
            self.client = GroqClient()
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.client = None

    def create_system_prompt(self) -> str:
        """Create system prompt for the AI assistant."""
        return """You are Athena, an AI fashion assistant that extracts structured filters from client briefs.

Given a client brief, extract structured filters in JSON with these optional keys:
hair_color, eye_color, size_min, size_max, age_min, age_max, division, campaign_type, location.

Rules:
- Map clothing sizes (0-4, 6-8, etc.) to size_min/size_max
- Extract campaign context (e.g., "cowboy boots", "desert shoot", "editorial")
- Map division terms: "mainboard"→"ima", "development"→"dev", "commercial"→"mai"
- Normalize colors: "brunette"→"brown", "golden"→"blonde"
- Extract age ranges if mentioned
- Include location/setting if specified

Examples:

Input: "Looking for a blonde, blue-eyed model size 0–4 for a cowboy boots campaign in the desert"
Output:
{
  "hair_color": "blonde",
  "eye_color": "blue",
  "size_min": 0,
  "size_max": 4,
  "campaign_type": "cowboy boots",
  "location": "desert"
}

Input: "Need brunette models from development board, ages 21-26, for editorial shoot"
Output:
{
  "hair_color": "brown",
  "division": "dev",
  "age_min": 21,
  "age_max": 26,
  "campaign_type": "editorial"
}

Input: "Petite blonde commercial faces with blue eyes for beauty campaign"
Output:
{
  "hair_color": "blonde",
  "eye_color": "blue",
  "division": "mai",
  "size_max": 4,
  "campaign_type": "beauty"
}

Return ONLY the JSON object, no additional text."""

    def create_user_prompt(self, client_brief: str) -> str:
        """Create user prompt with the actual client brief."""
        return f'Input: "{client_brief}"\nOutput:'

    def parse_client_brief(self, client_brief: str) -> Optional[Dict[str, Any]]:
        """Parse client brief using Groq API and return structured filters."""
        try:
            if not self.client:
                logger.error("Groq client not initialized")
                return None

            system_prompt = self.create_system_prompt()
            user_prompt = self.create_user_prompt(client_brief)

            # Use temperature 0.6 as specified in requirements
            result = self.client.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.6,
                max_tokens=1024
            )

            if result is None:
                logger.error("Failed to get response from Groq API")
                return None

            return result if result else {}

        except Exception as e:
            logger.error(f"Error parsing client brief: {e}")
            return None

class ModelMatcher:
    """Handles model search, filtering, and ranking based on client requirements."""
    
    @staticmethod
    def calculate_match_score(model: Dict[str, Any], filters: Dict[str, Any]) -> float:
        """Calculate relevance score for a model based on filters."""
        score = 0.0
        
        # Hair color matching (weight: 2.0)
        if filters.get('hair_color'):
            if ModelMatcher._fuzzy_match(filters['hair_color'], model.get('hair_color', '')):
                score += 2.0
        
        # Eye color matching (weight: 2.0)
        if filters.get('eye_color'):
            if ModelMatcher._fuzzy_match(filters['eye_color'], model.get('eye_color', '')):
                score += 2.0
        
        # Size matching (weight: 1.5)
        if filters.get('size_min') is not None or filters.get('size_max') is not None:
            if ModelMatcher._size_matches(model, filters):
                score += 1.5
        
        # Division matching (weight: 1.0)
        if filters.get('division'):
            if ModelMatcher._division_matches(model.get('division', ''), filters['division']):
                score += 1.0
        
        # Age matching (weight: 0.5) - placeholder for future implementation
        if filters.get('age_min') or filters.get('age_max'):
            score += 0.5  # Assume match for now
        
        return score
    
    @staticmethod
    def _fuzzy_match(search_term: str, field_value: str) -> bool:
        """Fuzzy matching for text fields."""
        if not search_term or not field_value:
            return False
        
        search_lower = search_term.lower().strip()
        field_lower = field_value.lower().strip()
        
        # Direct substring match
        return search_lower in field_lower or field_lower in search_lower
    
    @staticmethod
    def _size_matches(model: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if model size matches filter criteria."""
        # Extract numeric waist size as proxy for clothing size
        waist = model.get('waist', '')
        if not waist:
            return False
        
        # Extract numeric part from waist measurement
        waist_match = re.search(r'(\d+)', str(waist))
        if not waist_match:
            return False
        
        waist_inches = int(waist_match.group(1))
        
        # Convert clothing sizes to approximate waist measurements
        # Size 0-2: ~24-25", Size 4-6: ~26-27", Size 8-10: ~28-29", etc.
        size_min = filters.get('size_min', 0)
        size_max = filters.get('size_max', 20)
        
        waist_min = 24 + (size_min // 2) * 2
        waist_max = 24 + (size_max // 2) * 2 + 2
        
        return waist_min <= waist_inches <= waist_max
    
    @staticmethod
    def _division_matches(model_division: str, filter_division: str) -> bool:
        """Check if model division matches filter."""
        if not model_division or not filter_division:
            return False
        
        # Normalize division mappings
        division_map = {
            "mainboard": "ima", "main": "ima", "ima": "ima",
            "development": "dev", "dev": "dev",
            "commercial": "mai", "mai": "mai", "editorial": "mai"
        }
        
        normalized_filter = division_map.get(filter_division.lower(), filter_division.lower())
        return normalized_filter in model_division.lower()
    
    @staticmethod
    def find_matching_models(df: pd.DataFrame, filters: Dict[str, Any], 
                           max_results: int = 5) -> List[Dict[str, Any]]:
        """Find and rank models based on client brief filters."""
        if df.empty:
            return []
        
        # Calculate scores for all models
        scored_models = []
        for _, model in df.iterrows():
            model_dict = model.to_dict()
            score = ModelMatcher.calculate_match_score(model_dict, filters)
            if score > 0:  # Only include models with some match
                scored_models.append((score, model_dict))
        
        # Sort by score (descending) and return top results
        scored_models.sort(key=lambda x: x[0], reverse=True)
        return [model for score, model in scored_models[:max_results]]

class EmailGenerator:
    """Generates professional email pitches using Groq API."""

    def __init__(self):
        """Initialize Groq client for email generation."""
        try:
            self.client = GroqClient()
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            self.client = None

    def create_system_prompt(self) -> str:
        """Create system prompt for email generation."""
        return """You are Athena, an AI assistant that drafts professional, brand-aligned emails for fashion agencies.

Generate a short, elegant email pitch suitable for brand communication.

Generate a professional email with:
1. Subject line
2. Body text (2-3 paragraphs maximum)
3. Professional closing

Format as:
Subject: [subject line]

[email body]

Best regards,
[Agent Name]
Elysium Agency

Keep it concise, professional, and highlight how the selected models fit the client's requirements."""

    def create_user_prompt(self, client_brief: str, selected_models: List[Dict[str, Any]]) -> str:
        """Create user prompt with client brief and model details."""
        # Format model details for the prompt
        model_details = []
        for model in selected_models:
            details = f"- {model['name']} ({model['division'].upper()}): {model['height_cm']}cm, {model['hair_color']} hair, {model['eye_color']} eyes"
            if model.get('bust') and model.get('waist'):
                details += f", {model['bust']} bust, {model['waist']} waist"
            model_details.append(details)

        models_text = "\n".join(model_details)

        return f"""Client Brief: "{client_brief}"

Selected Models:
{models_text}

Generate the email pitch now."""

    def generate_email_pitch(self, client_brief: str, selected_models: List[Dict[str, Any]],
                           agent_name: str = "Athena") -> Optional[str]:
        """Generate email pitch using Groq API."""
        try:
            if not self.client:
                logger.error("Groq client not initialized")
                return None

            system_prompt = self.create_system_prompt()
            user_prompt = self.create_user_prompt(client_brief, selected_models)

            # Use temperature 0.6 as specified in requirements
            email_text = self.client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.6,
                max_tokens=1024,
                stream=False
            )

            if not email_text:
                logger.error("Failed to generate email pitch")
                return None

            # Replace placeholder agent name
            email_text = email_text.replace("[Agent Name]", agent_name)

            return email_text

        except Exception as e:
            logger.error(f"Error generating email pitch: {e}")
            return None

class PDFGenerator:
    """Generates PDF portfolios for selected models using ReportLab."""

    def __init__(self):
        if not PDF_AVAILABLE:
            raise ImportError("PDF generation requires 'reportlab' package. Install with: pip install reportlab")

        # Set up styles
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#333333')
        )
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#666666')
        )
        self.normal_style = self.styles['Normal']
    
    def get_image_for_pdf(self, image_url: str, max_width: float = 180, max_height: float = 216):
        """
        REFACTORED: Get image object for PDF from HTTPS URL.
        """
        try:
            # Handle HTTPS URLs directly
            if image_url.startswith('http'):
                # Use ImageReader to load from URL
                img = Image(ImageReader(image_url), width=max_width, height=max_height)
                img.hAlign = 'CENTER'
                return img
            else:
                logger.warning(f"Non-HTTPS image URL provided: {image_url}")
                return None

        except Exception as e:
            logger.warning(f"Could not load image from URL {image_url}: {e}")
            return None
    
    def generate_model_pdf(self, model: Dict[str, Any], output_dir: str = "pdfs") -> Optional[str]:
        """Generate PDF portfolio for a single model using ReportLab."""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Generate PDF filename
            model_name_clean = re.sub(r'[^\w\s-]', '', model['name']).strip().replace(' ', '_')
            pdf_filename = f"{model_name_clean}_{model['model_id']}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)

            # Create PDF document
            doc = SimpleDocTemplate(pdf_path, pagesize=letter)
            story = []

            # Header section
            story.append(Paragraph(model['name'], self.title_style))
            story.append(Paragraph(f"{model['division'].upper()} Division", self.subtitle_style))
            story.append(Spacer(1, 20))

            # Measurements table
            measurements_data = [
                ['Attribute', 'Value'],
                ['Height', f"{int(model['height_cm'])} cm"],
                ['Hair', model['hair_color'].title()],
                ['Eyes', model['eye_color'].title()],
            ]

            # Add optional measurements
            if model.get('bust'):
                measurements_data.append(['Bust', model['bust']])
            if model.get('waist'):
                measurements_data.append(['Waist', model['waist']])
            if model.get('hips'):
                measurements_data.append(['Hips', model['hips']])
            if model.get('shoes'):
                measurements_data.append(['Shoes', model['shoes']])

            # Create and style the table
            measurements_table = Table(measurements_data, colWidths=[144, 216])
            measurements_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(measurements_table)
            story.append(Spacer(1, 30))

            # Images section
            images = model.get('images', [])
            if images:
                story.append(Paragraph("Portfolio Images", self.subtitle_style))
                story.append(Spacer(1, 10))

                # Add up to 4 images in a 2x2 grid
                image_objects = []
                for img_path in images[:4]:
                    img_obj = self.get_image_for_pdf(img_path)
                    if img_obj:
                        image_objects.append(img_obj)

                # Create image grid
                if image_objects:
                    if len(image_objects) >= 2:
                        # Create table for image layout
                        image_rows = []
                        for i in range(0, len(image_objects), 2):
                            row = image_objects[i:i+2]
                            if len(row) == 1:
                                row.append('')  # Empty cell for odd number of images
                            image_rows.append(row)

                        image_table = Table(image_rows, colWidths=[180, 180])
                        image_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ('TOPPADDING', (0, 0), (-1, -1), 6),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ]))
                        story.append(image_table)
                    else:
                        # Single image, center it
                        story.append(image_objects[0])

            story.append(Spacer(1, 30))

            # Footer
            story.append(Paragraph("Elysium Agency Portfolio Preview", self.normal_style))
            story.append(Paragraph(f"Model ID: {model['model_id']}", self.normal_style))

            # Build PDF
            doc.build(story)

            logger.info(f"Generated PDF: {pdf_path}")
            return pdf_path

        except Exception as e:
            logger.error(f"Error generating PDF for model {model.get('name', 'Unknown')}: {e}")
            return None
    
    def generate_multiple_pdfs(self, models: List[Dict[str, Any]], 
                             output_dir: str = "pdfs") -> List[str]:
        """Generate PDF portfolios for multiple models."""
        pdf_paths = []
        
        for model in models:
            pdf_path = self.generate_model_pdf(model, output_dir)
            if pdf_path:
                pdf_paths.append(pdf_path)
        
        return pdf_paths

    def generate_template_pdf(self, html_content: str, template_name: str, models: List[Dict[str, Any]], output_dir: str = "pdfs") -> Optional[str]:
        """Generate PDF from HTML template content using WeasyPrint fallback."""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Generate PDF filename based on template and models
            if len(models) == 1:
                model_name_clean = re.sub(r'[^\w\s-]', '', models[0]['name']).strip().replace(' ', '_')
                pdf_filename = f"{template_name.replace(' ', '_')}_{model_name_clean}.pdf"
            else:
                pdf_filename = f"{template_name.replace(' ', '_')}_Campaign_{len(models)}_models.pdf"

            pdf_path = os.path.join(output_dir, pdf_filename)

            # Try to use WeasyPrint for HTML to PDF conversion
            try:
                import weasyprint
                weasyprint.HTML(string=html_content, base_url=".").write_pdf(pdf_path)
                logger.info(f"Generated template PDF using WeasyPrint: {pdf_path}")
                return pdf_path
            except (ImportError, OSError, Exception) as e:
                # Fallback to ReportLab-based generation for any WeasyPrint issues
                logger.warning(f"WeasyPrint not available ({e}), falling back to ReportLab")
                return self._generate_reportlab_fallback(models, template_name, output_dir)

        except Exception as e:
            logger.error(f"Error generating template PDF: {e}")
            return None

    def _generate_reportlab_fallback(self, models: List[Dict[str, Any]], template_name: str, output_dir: str) -> Optional[str]:
        """Fallback PDF generation using ReportLab when WeasyPrint is not available."""
        try:
            # Use the existing ReportLab-based generation for the first model
            if models:
                return self.generate_model_pdf(models[0], output_dir)
            return None
        except Exception as e:
            logger.error(f"Error in ReportLab fallback: {e}")
            return None
