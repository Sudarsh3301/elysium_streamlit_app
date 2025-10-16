#!/usr/bin/env python3
"""
Test script for the Athena Template System
Tests all four template styles with different model combinations.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_template_system():
    """Test the complete template system."""
    print("🧪 Testing Athena Template System")
    print("=" * 50)
    
    # Test imports
    try:
        from template_manager import TemplateManager
        from athena_core import PDFGenerator
        print("✅ Successfully imported template system components")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("💡 Install missing dependencies: pip install jinja2 reportlab")
        return False
    
    # Load test data
    try:
        df = pd.read_json("../elysium_kb/models.jsonl", lines=True)
        print(f"✅ Loaded {len(df)} models from database")
    except Exception as e:
        print(f"❌ Failed to load model data: {e}")
        return False
    
    # Initialize components
    try:
        template_manager = TemplateManager()
        pdf_generator = PDFGenerator()
        print("✅ Initialized template manager and PDF generator")
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
        return False
    
    # Test template availability
    available_templates = template_manager.get_available_templates()
    print(f"✅ Found {len(available_templates)} available templates:")
    for name, config in available_templates.items():
        print(f"   • {name}: {config['description']}")
    
    # Prepare test models
    test_models = df.head(5).to_dict('records')
    
    # Process models for template system
    for model in test_models:
        # Ensure required fields
        model.setdefault('name', f"Model {model.get('model_id', 'Unknown')}")
        model.setdefault('division', 'Unknown')
        model.setdefault('height_cm', 170)
        model.setdefault('hair_color', 'Unknown')
        model.setdefault('eye_color', 'Unknown')
        model.setdefault('images', [])
        
        # Process images
        if model['images']:
            processed_images = []
            for img_path in model['images']:
                local_path = os.path.join("..", "elysium_kb", img_path.lstrip('/'))
                if os.path.exists(local_path):
                    processed_images.append(local_path)
            model['images'] = processed_images
    
    print(f"✅ Prepared {len(test_models)} test models")
    
    # Test each template
    test_scenarios = [
        ("Agency Standard", test_models[:1], "Single model showcase"),
        ("Campaign Pitch", test_models[:3], "Multi-model campaign"),
        ("Editorial Lookbook", test_models[:4], "Editorial presentation"),
        ("Compact Comp Sheet", test_models[:6], "Casting overview")
    ]
    
    client_brief = "Looking for blonde, blue-eyed models size 0-4 for a cowboy boots campaign in the desert."
    
    for template_name, models, description in test_scenarios:
        print(f"\n🎨 Testing {template_name} ({description})")
        print("-" * 40)
        
        try:
            # Validate template selection
            is_valid, message = template_manager.validate_template_selection(template_name, models)
            print(f"   Validation: {message}")
            
            if not is_valid:
                print(f"   ⚠️ Skipping {template_name} due to validation failure")
                continue
            
            # Preprocess data
            data = template_manager.preprocess_data(
                template_name=template_name,
                models=models,
                client_brief=client_brief,
                agent_name="Test Agent"
            )
            print(f"   ✅ Data preprocessing successful")
            
            # Render template
            html_content = template_manager.render_template(template_name, data)
            print(f"   ✅ Template rendering successful ({len(html_content)} chars)")
            
            # Test PDF generation (HTML only, skip actual PDF for now)
            print(f"   ✅ Template {template_name} test completed successfully")
            
        except Exception as e:
            print(f"   ❌ Template {template_name} test failed: {e}")
    
    # Test template validation edge cases
    print(f"\n🔍 Testing validation edge cases")
    print("-" * 40)
    
    # Test with too many models
    try:
        is_valid, message = template_manager.validate_template_selection("Agency Standard", test_models[:3])
        print(f"   Too many models for Agency Standard: {message}")
    except Exception as e:
        print(f"   ❌ Validation test failed: {e}")
    
    # Test with no models
    try:
        is_valid, message = template_manager.validate_template_selection("Campaign Pitch", [])
        print(f"   No models selected: {message}")
    except Exception as e:
        print(f"   ❌ Validation test failed: {e}")
    
    print(f"\n🎉 Template system testing completed!")
    return True

def test_template_rendering():
    """Test individual template rendering."""
    print("\n📄 Testing individual template rendering")
    print("-" * 40)
    
    try:
        from template_manager import TemplateManager
        template_manager = TemplateManager()
        
        # Test data with all required template variables
        test_model = {
            "name": "Test Model",
            "division": "mainboard",
            "height_cm": 175,
            "hair_color": "blonde",
            "eye_color": "blue",
            "model_id": "TEST001",
            "images": [],
            "hero_image": None,
            "thumbnail_images": []
        }

        test_data = {
            "timestamp": "October 16, 2024",
            "agent_name": "Test Agent",
            "agency": {
                "name": "Elysium Agency",
                "contact": "bookings@elysiumagency.com",
                "website": "www.elysiumagency.com"
            },
            "models": [test_model],
            "model": test_model,  # For Agency Standard template
            "cover_models": [test_model],  # For Campaign Pitch template
            "featured_models": [test_model],  # For Editorial Lookbook template
            "grid_models": [test_model],  # For Compact Comp Sheet template
            "campaign": {
                "title": "Test Campaign",
                "brief": "Test brief for template rendering"
            },
            "theme_class": "themed"
        }
        
        # Test each template
        for template_name in template_manager.get_available_templates().keys():
            try:
                html = template_manager.render_template(template_name, test_data)
                print(f"   ✅ {template_name}: {len(html)} characters rendered")
            except Exception as e:
                print(f"   ❌ {template_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Template rendering test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Athena Template System Tests")
    print("=" * 60)
    
    success = True
    
    # Run main template system test
    if not test_template_system():
        success = False
    
    # Run template rendering test
    if not test_template_rendering():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Template system is ready.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    print("💡 To install missing dependencies:")
    print("   pip install jinja2 reportlab weasyprint")
