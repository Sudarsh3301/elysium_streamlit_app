"""
Test script for Athena functionality
Tests the complete workflow from client brief parsing to PDF generation.
"""

import sys
import os
import pandas as pd
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from athena_core import AthenaClient, ModelMatcher, EmailGenerator, PDFGenerator
from app import DataLoader

def test_data_loading():
    """Test loading and normalizing model data."""
    print("🔄 Testing data loading...")
    
    models_file = "../elysium_kb/models.jsonl"
    df = DataLoader.load_and_normalize_models(models_file)
    
    if df.empty:
        print("❌ Failed to load model data")
        return None
    
    print(f"✅ Loaded {len(df)} models")
    print(f"📊 Columns: {list(df.columns)}")
    print(f"🎭 Sample model: {df.iloc[0]['name']}")
    
    return df

def test_client_brief_parsing():
    """Test client brief parsing with Ollama."""
    print("\n🔄 Testing client brief parsing...")
    
    athena_client = AthenaClient()
    
    # Test brief
    client_brief = "Looking for a blonde, blue-eyed model size 0–4 for a cowboy boots campaign in the desert"
    
    print(f"📝 Client brief: {client_brief}")
    
    try:
        filters = athena_client.parse_client_brief(client_brief)
        
        if filters is None:
            print("❌ Failed to connect to Ollama - make sure it's running")
            return None
        
        print(f"✅ Parsed filters: {json.dumps(filters, indent=2)}")
        return filters
        
    except Exception as e:
        print(f"❌ Error parsing client brief: {e}")
        return None

def test_model_matching(df, filters):
    """Test model matching and ranking."""
    print("\n🔄 Testing model matching...")
    
    if df is None or filters is None:
        print("❌ Cannot test matching - missing data or filters")
        return []
    
    matched_models = ModelMatcher.find_matching_models(df, filters, max_results=3)
    
    print(f"✅ Found {len(matched_models)} matching models:")
    
    for i, model in enumerate(matched_models, 1):
        score = ModelMatcher.calculate_match_score(model, filters)
        print(f"  {i}. {model['name']} (Score: {score:.1f})")
        print(f"     Hair: {model['hair_color']}, Eyes: {model['eye_color']}")
        print(f"     Height: {model['height_cm']}cm, Division: {model['division']}")
    
    return matched_models

def test_email_generation(client_brief, selected_models):
    """Test email pitch generation."""
    print("\n🔄 Testing email generation...")
    
    if not selected_models:
        print("❌ No models to generate email for")
        return None
    
    email_generator = EmailGenerator()
    
    try:
        email_content = email_generator.generate_email_pitch(
            client_brief, 
            selected_models[:2],  # Use first 2 models
            "Test Agent"
        )
        
        if email_content:
            print("✅ Generated email:")
            print("=" * 50)
            print(email_content)
            print("=" * 50)
            return email_content
        else:
            print("❌ Failed to generate email")
            return None
            
    except Exception as e:
        print(f"❌ Error generating email: {e}")
        return None

def test_pdf_generation(selected_models):
    """Test PDF portfolio generation."""
    print("\n🔄 Testing PDF generation...")
    
    if not selected_models:
        print("❌ No models to generate PDFs for")
        return []
    
    pdf_generator = PDFGenerator()
    
    try:
        # Create test output directory
        output_dir = "test_pdfs"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate PDFs for first 2 models
        test_models = selected_models[:2]
        pdf_paths = pdf_generator.generate_multiple_pdfs(test_models, output_dir)
        
        print(f"✅ Generated {len(pdf_paths)} PDFs:")
        for pdf_path in pdf_paths:
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path) / 1024  # KB
                print(f"  📄 {pdf_path} ({file_size:.1f} KB)")
            else:
                print(f"  ❌ {pdf_path} (not found)")
        
        return pdf_paths
        
    except Exception as e:
        print(f"❌ Error generating PDFs: {e}")
        return []

def test_image_availability(df):
    """Test if model images are available locally."""
    print("\n🔄 Testing image availability...")
    
    total_models = len(df)
    models_with_images = 0
    total_images = 0
    
    for _, model in df.iterrows():
        images = model.get('images', [])
        if images:
            models_with_images += 1
            
            # Check if images exist locally
            local_images = 0
            for img_path in images:
                local_path = os.path.join("..", "elysium_kb", img_path.lstrip('/'))
                if os.path.exists(local_path):
                    local_images += 1
            
            total_images += local_images
    
    print(f"📊 Image statistics:")
    print(f"  Models with images: {models_with_images}/{total_models}")
    print(f"  Total local images: {total_images}")
    print(f"  Average images per model: {total_images/models_with_images:.1f}")

def main():
    """Run all tests."""
    print("🏛️ Athena Functionality Test Suite")
    print("=" * 50)
    
    # Test 1: Data loading
    df = test_data_loading()
    
    # Test 2: Image availability
    if df is not None:
        test_image_availability(df)
    
    # Test 3: Client brief parsing
    client_brief = "Looking for a blonde, blue-eyed model size 0–4 for a cowboy boots campaign in the desert"
    filters = test_client_brief_parsing()
    
    # Test 4: Model matching
    matched_models = test_model_matching(df, filters)
    
    # Test 5: Email generation
    email_content = test_email_generation(client_brief, matched_models)
    
    # Test 6: PDF generation
    pdf_paths = test_pdf_generation(matched_models)
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 50)
    print(f"✅ Data loading: {'PASS' if df is not None else 'FAIL'}")
    print(f"✅ Brief parsing: {'PASS' if filters else 'FAIL'}")
    print(f"✅ Model matching: {'PASS' if matched_models else 'FAIL'}")
    print(f"✅ Email generation: {'PASS' if email_content else 'FAIL'}")
    print(f"✅ PDF generation: {'PASS' if pdf_paths else 'FAIL'}")
    
    if all([df is not None, filters, matched_models, email_content, pdf_paths]):
        print("\n🎉 All tests passed! Athena is ready to use.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
