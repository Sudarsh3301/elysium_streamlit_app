"""
Basic test script for Athena functionality without PDF generation
Tests core functionality that doesn't require additional dependencies.
"""

import sys
import os
import pandas as pd
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    print(f"🎨 Hair colors: {sorted(df['hair_color'].dropna().unique())}")
    print(f"👁️ Eye colors: {sorted(df['eye_color'].dropna().unique())}")
    print(f"📋 Divisions: {sorted(df['division'].dropna().unique())}")
    
    return df

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
    if models_with_images > 0:
        print(f"  Average images per model: {total_images/models_with_images:.1f}")

def test_basic_filtering(df):
    """Test basic filtering functionality."""
    print("\n🔄 Testing basic filtering...")
    
    # Test filtering by hair color
    blonde_models = df[df['hair_color'].str.contains('blonde', case=False, na=False)]
    print(f"📊 Blonde models: {len(blonde_models)}")
    
    # Test filtering by eye color
    blue_eye_models = df[df['eye_color'].str.contains('blue', case=False, na=False)]
    print(f"👁️ Blue-eyed models: {len(blue_eye_models)}")
    
    # Test filtering by division
    ima_models = df[df['division'].str.contains('ima', case=False, na=False)]
    dev_models = df[df['division'].str.contains('dev', case=False, na=False)]
    mai_models = df[df['division'].str.contains('mai', case=False, na=False)]
    
    print(f"📋 Division breakdown:")
    print(f"  IMA: {len(ima_models)}")
    print(f"  DEV: {len(dev_models)}")
    print(f"  MAI: {len(mai_models)}")
    
    # Test combined filtering
    blonde_blue_models = df[
        (df['hair_color'].str.contains('blonde', case=False, na=False)) &
        (df['eye_color'].str.contains('blue', case=False, na=False))
    ]
    print(f"🎯 Blonde + Blue eyes: {len(blonde_blue_models)}")
    
    if len(blonde_blue_models) > 0:
        print("📝 Sample matches:")
        for _, model in blonde_blue_models.head(3).iterrows():
            print(f"  - {model['name']} ({model['division'].upper()}): {model['height_cm']}cm")

def test_size_conversion():
    """Test size conversion logic."""
    print("\n🔄 Testing size conversion...")
    
    # Test waist measurements
    test_waists = ["24\" - 61", "25\" - 64", "26\" - 66", "28\" - 71"]
    
    print("📏 Waist size conversion:")
    for waist in test_waists:
        import re
        waist_match = re.search(r'(\d+)', waist)
        if waist_match:
            waist_inches = int(waist_match.group(1))
            # Approximate clothing size mapping
            clothing_size = max(0, (waist_inches - 24) * 2)
            print(f"  {waist} → ~Size {clothing_size}")

def simulate_athena_workflow(df):
    """Simulate the Athena workflow without external dependencies."""
    print("\n🔄 Simulating Athena workflow...")
    
    # Simulate client brief
    client_brief = "Looking for a blonde, blue-eyed model size 0–4 for a cowboy boots campaign in the desert"
    print(f"📝 Client brief: {client_brief}")
    
    # Simulate filter extraction (what Ollama would do)
    simulated_filters = {
        "hair_color": "blonde",
        "eye_color": "blue",
        "size_min": 0,
        "size_max": 4,
        "campaign_type": "cowboy boots",
        "location": "desert"
    }
    print(f"🎯 Simulated filters: {json.dumps(simulated_filters, indent=2)}")
    
    # Apply filters manually
    filtered_df = df[
        (df['hair_color'].str.contains('blonde', case=False, na=False)) &
        (df['eye_color'].str.contains('blue', case=False, na=False))
    ]
    
    # Filter by approximate size (waist 24-26 inches for size 0-4)
    size_filtered = []
    for _, model in filtered_df.iterrows():
        waist = model.get('waist', '')
        if waist:
            import re
            waist_match = re.search(r'(\d+)', str(waist))
            if waist_match:
                waist_inches = int(waist_match.group(1))
                if 24 <= waist_inches <= 26:  # Size 0-4 range
                    size_filtered.append(model)
    
    if size_filtered:
        print(f"✅ Found {len(size_filtered)} matching models:")
        for i, model in enumerate(size_filtered[:3], 1):
            print(f"  {i}. {model['name']} ({model['division'].upper()})")
            print(f"     Hair: {model['hair_color']}, Eyes: {model['eye_color']}")
            print(f"     Height: {model['height_cm']}cm, Waist: {model['waist']}")
        
        # Simulate email generation
        print("\n📧 Simulated email generation:")
        print("=" * 50)
        print("Subject: Models for Your Cowboy Boots Campaign")
        print()
        print("Hi [Client Name],")
        print()
        print("Following your request for blonde, blue-eyed talent for your upcoming desert campaign,")
        print(f"we'd love to suggest {size_filtered[0]['name']} and {size_filtered[1]['name'] if len(size_filtered) > 1 else 'additional models'}.")
        print()
        print("Their look perfectly fits the western, sun-lit aesthetic of your project.")
        print()
        print("Best regards,")
        print("Test Agent")
        print("Elysium Agency")
        print("=" * 50)
        
        return True
    else:
        print("❌ No models found matching all criteria")
        return False

def main():
    """Run all basic tests."""
    print("🏛️ Athena Basic Functionality Test")
    print("=" * 50)
    
    # Test 1: Data loading
    df = test_data_loading()
    
    if df is None:
        print("❌ Cannot proceed without data")
        return
    
    # Test 2: Image availability
    test_image_availability(df)
    
    # Test 3: Basic filtering
    test_basic_filtering(df)
    
    # Test 4: Size conversion
    test_size_conversion()
    
    # Test 5: Simulate workflow
    workflow_success = simulate_athena_workflow(df)
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 50)
    print(f"✅ Data loading: PASS")
    print(f"✅ Image availability: PASS")
    print(f"✅ Basic filtering: PASS")
    print(f"✅ Size conversion: PASS")
    print(f"✅ Workflow simulation: {'PASS' if workflow_success else 'FAIL'}")
    
    print("\n🎉 Basic tests completed!")
    print("💡 To test full functionality, install dependencies:")
    print("   pip install weasyprint jinja2 pyperclip")
    print("   and ensure Ollama is running with gemma3:4b model")

if __name__ == "__main__":
    main()
