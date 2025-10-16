# 🏛️ Athena Demo Script

## Overview
Athena is the new AI-powered agent assistant tab in the Elysium Model Catalogue that automates the entire pitchback process from client brief to professional email and PDF portfolios.

## Demo Flow

### 1. Setup and Launch
```bash
# Navigate to the app directory
cd elysium_streamlit_app

# Install dependencies (if not already installed)
pip install weasyprint jinja2 pyperclip

# Ensure Ollama is running with the required model
ollama pull gemma3:4b
ollama serve

# Launch the Streamlit app
streamlit run app.py
```

### 2. Navigate to Athena Tab
- Open the app in your browser (usually http://localhost:8501)
- Click on the **"🏛️ Athena"** tab (second tab)
- You should see the Athena interface with the gradient header

### 3. Demo Script - Client Brief Input

**Scenario**: A client wants models for a cowboy boots campaign

**Sample Client Brief** (paste this into the text area):
```
Looking for a blonde, blue-eyed model between 21–26, size 0–4, to shoot a cowboy boots campaign in the desert. Need someone with a western, sun-kissed look for outdoor photography.
```

**Alternative Briefs to Try**:
```
Need brunette models from development board for editorial shoot, ages 22-28, with green or hazel eyes.
```

```
Looking for petite commercial faces with blue eyes for beauty campaign, preferably from mainboard division.
```

### 4. Generate Pitchback Workflow

1. **Enter Agent Name**: Type your name in the "Agent Name" field (e.g., "Sarah Johnson")

2. **Paste Client Brief**: Use one of the sample briefs above

3. **Click "🔮 Generate Pitchback"**: This triggers the AI pipeline:
   - Ollama parses the brief into structured filters
   - System searches and ranks matching models
   - Shows top 3-5 results with model cards

### 5. Model Selection

**What You'll See**:
- Model cards with thumbnails, names, and key attributes
- Division information (IMA, DEV, MAI)
- Physical attributes (height, hair, eyes, measurements)
- "Include in Pitchback" checkboxes

**Demo Actions**:
- Toggle 2-3 models for inclusion
- Notice the selection summary updates
- Observe how the UI responds to selections

### 6. Email Generation

1. **Click "✨ Generate Professional Email"**
2. **Watch the AI work**:
   - Generates professional email pitch
   - Creates PDF portfolios (if dependencies installed)
   - Shows success confirmation

### 7. Final Preview and Export

**Email Preview**:
- Professional subject line
- 2-3 paragraph body highlighting selected models
- Proper agency signature

**Export Options**:
- **📋 Copy Email to Clipboard**: Copies the email text
- **📄 Download All PDFs**: Downloads a ZIP file with model portfolios
- **🔄 Start New Brief**: Resets the workflow

### 8. PDF Portfolio Features (if dependencies installed)

Each PDF includes:
- Model name and division
- Complete measurements table
- First 4 portfolio images
- Professional Elysium branding
- Model ID for reference

## Expected Results

### Successful Demo Outcomes

1. **AI Parsing**: 
   - Extracts hair color, eye color, size range
   - Identifies campaign type and location
   - Maps semantic terms (e.g., "mainboard" → "ima")

2. **Model Matching**:
   - Shows 3-5 relevant models
   - Ranks by relevance score
   - Displays key attributes clearly

3. **Email Generation**:
   - Professional, brand-appropriate tone
   - Highlights model fit for campaign
   - Includes agent name and signature

4. **PDF Generation**:
   - Clean, professional layout
   - High-quality images
   - Complete model information

### Sample Expected Output

**Parsed Filters**:
```json
{
  "hair_color": "blonde",
  "eye_color": "blue",
  "size_min": 0,
  "size_max": 4,
  "age_min": 21,
  "age_max": 26,
  "campaign_type": "cowboy boots",
  "location": "desert"
}
```

**Sample Generated Email**:
```
Subject: Models for Your Cowboy Boots Campaign

Hi [Client Name],

Following your request for blonde, blue-eyed talent for your upcoming desert campaign, we'd love to suggest Amber Black and Clementine Chalfant from our roster.

Amber (DEV, 175cm) and Clementine (IMA, 180cm) both have the sun-kissed, western aesthetic perfect for outdoor cowboy boots photography. Their measurements align with your size 0-4 requirement, and their experience with lifestyle campaigns makes them ideal for this project.

Best regards,
Sarah Johnson
Elysium Agency
```

## Troubleshooting

### Common Issues

1. **"Athena functionality is not available"**
   - Install missing packages: `pip install weasyprint jinja2 pyperclip`
   - Restart the Streamlit app

2. **"Cannot connect to Ollama"**
   - Ensure Ollama is running: `ollama serve`
   - Check if gemma3:4b model is available: `ollama list`
   - Pull model if needed: `ollama pull gemma3:4b`

3. **"No models found matching criteria"**
   - Try a broader brief (remove specific requirements)
   - Check if the model data loaded correctly
   - Verify the brief uses recognizable terms

4. **PDF generation fails**
   - WeasyPrint requires additional system dependencies
   - On Windows: May need Visual C++ redistributables
   - Alternative: Use the email functionality without PDFs

### Fallback Demo (Without Dependencies)

If PDF generation isn't available:
1. Focus on the AI parsing and model matching
2. Demonstrate email generation
3. Show the copy-to-clipboard functionality
4. Explain that PDFs would be generated with full setup

## Success Metrics

A successful demo should show:
- ✅ Athena tab loads without errors
- ✅ Client brief parsing works with Ollama
- ✅ Model matching returns relevant results
- ✅ Email generation produces professional content
- ✅ UI is responsive and intuitive
- ✅ Export functionality works as expected

## Demo Tips

1. **Prepare Ollama**: Ensure it's running before starting
2. **Use Realistic Briefs**: Stick to attributes that exist in the data
3. **Show Flexibility**: Demonstrate different types of requests
4. **Highlight AI**: Emphasize the automated parsing and generation
5. **Professional Context**: Frame it as a real agency workflow tool

## Next Steps After Demo

1. **Install Full Dependencies**: For complete PDF functionality
2. **Customize Email Templates**: Modify the prompt for brand voice
3. **Add More Models**: Expand the model database
4. **Integration**: Connect with actual email systems
5. **Analytics**: Track usage and success rates
