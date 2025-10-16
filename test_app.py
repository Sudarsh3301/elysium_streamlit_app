#!/usr/bin/env python3
"""
Test script for Elysium Model Catalogue
Tests the core functionality without requiring Streamlit UI
"""

import sys
import os
import json
import pandas as pd

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import DataLoader, FilterEngine, OllamaClient

def test_data_loading():
    """Test that data loads correctly with new field names."""
    print("🧪 Testing data loading...")
    
    models_file = "../elysium_kb/models.jsonl"
    df = DataLoader.load_and_normalize_models(models_file)
    
    if df.empty:
        print("❌ Failed to load data")
        return False
    
    print(f"✅ Loaded {len(df)} models")
    
    # Check that new field names exist
    required_fields = ['model_id', 'name', 'division', 'hair_color', 'eye_color', 'height_cm']
    missing_fields = [field for field in required_fields if field not in df.columns]
    
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        return False
    
    print("✅ All required fields present")
    
    # Check data types and ranges
    if not df['height_cm'].dtype in ['int64', 'float64']:
        print("❌ Height not numeric")
        return False
    
    height_range = (df['height_cm'].min(), df['height_cm'].max())
    print(f"✅ Height range: {height_range[0]}-{height_range[1]} cm")
    
    # Check unique values
    unique_hair = df['hair_color'].dropna().unique()
    unique_eyes = df['eye_color'].dropna().unique()
    unique_divisions = df['division'].dropna().unique()
    
    print(f"✅ Hair colors: {len(unique_hair)} unique values")
    print(f"✅ Eye colors: {len(unique_eyes)} unique values")
    print(f"✅ Divisions: {list(unique_divisions)}")
    
    return True

def test_filtering():
    """Test the filtering engine."""
    print("\n🧪 Testing filtering engine...")
    
    models_file = "../elysium_kb/models.jsonl"
    df = DataLoader.load_and_normalize_models(models_file)
    
    if df.empty:
        print("❌ No data to filter")
        return False
    
    # Test manual filters
    print("Testing manual filters...")
    
    # Hair color filter
    blonde_models = FilterEngine.apply_filters(df, hair_colors=['blonde'])
    print(f"✅ Blonde models: {len(blonde_models)}")
    
    # Eye color filter
    blue_eye_models = FilterEngine.apply_filters(df, eye_colors=['blue'])
    print(f"✅ Blue eye models: {len(blue_eye_models)}")
    
    # Combined filter
    blonde_blue = FilterEngine.apply_filters(df, hair_colors=['blonde'], eye_colors=['blue'])
    print(f"✅ Blonde hair + blue eyes: {len(blonde_blue)}")
    
    # Height filter
    tall_models = FilterEngine.apply_filters(df, height_range=(175, 190))
    print(f"✅ Tall models (175-190cm): {len(tall_models)}")
    
    # Division filter
    dev_models = FilterEngine.apply_filters(df, divisions=['dev'])
    print(f"✅ Dev division models: {len(dev_models)}")
    
    # Test AI filters
    print("Testing AI filters...")
    
    ai_filters = {
        'hair_color': 'brown',
        'eye_color': 'green',
        'height_min': 170,
        'height_max': 180
    }
    
    ai_filtered = FilterEngine.apply_filters(df, ai_filters=ai_filters)
    print(f"✅ AI filtered models: {len(ai_filtered)}")
    
    # Test combined manual + AI filters
    combined = FilterEngine.apply_filters(
        df, 
        hair_colors=['brown'], 
        height_range=(165, 185),
        ai_filters={'eye_color': 'green'}
    )
    print(f"✅ Combined manual + AI filters: {len(combined)}")
    
    return True

def test_ollama_prompt():
    """Test the Ollama prompt generation."""
    print("\n🧪 Testing Ollama prompt generation...")
    
    test_query = "Looking for blonde models with blue eyes around 175 cm"
    prompt = OllamaClient.create_prompt(test_query)
    
    # Check that prompt contains the correct field names
    if 'hair_color' not in prompt:
        print("❌ Prompt missing hair_color field")
        return False
    
    if 'eye_color' not in prompt:
        print("❌ Prompt missing eye_color field")
        return False
    
    if 'height_min' not in prompt:
        print("❌ Prompt missing height_min field")
        return False
    
    if 'height_max' not in prompt:
        print("❌ Prompt missing height_max field")
        return False
    
    print("✅ Prompt contains correct field names")
    print("✅ Prompt generation working")
    
    return True

def main():
    """Run all tests."""
    print("🚀 Starting Elysium Model Catalogue Tests\n")
    
    tests = [
        test_data_loading,
        test_filtering,
        test_ollama_prompt
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} failed with error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
