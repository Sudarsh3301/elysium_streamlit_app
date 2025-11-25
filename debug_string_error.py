#!/usr/bin/env python3
"""
Debug script to isolate the string concatenation error in the Catalogue tab.
"""

import pandas as pd
import sys
import traceback
from app import DataLoader, display_enhanced_model_card, display_model_grid_with_pagination

def test_data_loading():
    """Test data loading."""
    print("🔍 Testing data loading...")
    try:
        df = DataLoader.load_and_normalize_models('models_normalized.csv')
        print(f"✅ Data loaded successfully: {len(df)} models")
        print(f"✅ Columns: {df.columns.tolist()}")
        print(f"✅ Data types: {df.dtypes.to_dict()}")
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        traceback.print_exc()
        return None

def test_single_model_card(df):
    """Test rendering a single model card."""
    print("\n🔍 Testing single model card rendering...")
    try:
        if df is None or df.empty:
            print("❌ No data to test")
            return False
        
        # Get first model
        model_data = df.iloc[0].to_dict()
        print(f"✅ Testing model: {model_data['name']} (ID: {model_data['model_id']})")
        print(f"✅ Model data types: {[(k, type(v)) for k, v in model_data.items()]}")
        
        # Test individual components that might cause string concatenation errors
        print("\n🔍 Testing individual string operations...")
        
        # Test model_id string conversion
        model_id_str = str(model_data['model_id'])
        print(f"✅ model_id conversion: {model_id_str} (type: {type(model_id_str)})")
        
        # Test height_cm string conversion
        height_str = str(int(model_data['height_cm']))
        print(f"✅ height_cm conversion: {height_str} (type: {type(height_str)})")
        
        # Test f-string operations that were problematic
        card_id = f"card_{str(model_data['model_id'])}"
        print(f"✅ card_id f-string: {card_id}")
        
        height_display = f"📏 {int(model_data['height_cm'])}cm"
        print(f"✅ height_display f-string: {height_display}")
        
        model_id_display = f"**Model ID:** {str(model_data['model_id'])}"
        print(f"✅ model_id_display f-string: {model_id_display}")
        
        print("✅ All string operations successful")
        return True
        
    except Exception as e:
        print(f"❌ Error testing model card: {e}")
        traceback.print_exc()
        return False

def test_model_grid_data_preparation(df):
    """Test the data preparation for model grid."""
    print("\n🔍 Testing model grid data preparation...")
    try:
        if df is None or df.empty:
            print("❌ No data to test")
            return False
        
        # Test pagination logic
        total_models = len(df)
        models_per_page = 12
        current_page = 0
        start_idx = current_page * models_per_page
        end_idx = min(start_idx + models_per_page, total_models)
        
        print(f"✅ Pagination: {start_idx}-{end_idx} of {total_models}")
        
        # Test display_df creation
        display_df = df.iloc[start_idx:end_idx]
        print(f"✅ Display DataFrame: {len(display_df)} models")
        
        # Test model data conversion to dict
        for idx, (_, row) in enumerate(display_df.iterrows()):
            model_data = row.to_dict()
            print(f"✅ Model {idx}: {model_data['name']} - data types OK")
            
            # Test the specific operations that might fail
            try:
                card_id = f"card_{str(model_data['model_id'])}"
                height_display = f"📏 {int(model_data['height_cm'])}cm"
                print(f"   ✅ String operations OK for {model_data['name']}")
            except Exception as e:
                print(f"   ❌ String operation failed for {model_data['name']}: {e}")
                return False
            
            # Only test first few models to avoid spam
            if idx >= 3:
                break
        
        print("✅ Model grid data preparation successful")
        return True
        
    except Exception as e:
        print(f"❌ Error testing model grid preparation: {e}")
        traceback.print_exc()
        return False

def main():
    """Run debug tests."""
    print("🚀 Starting String Concatenation Error Debug\n")
    
    # Test 1: Data loading
    df = test_data_loading()
    if df is None:
        print("❌ Cannot proceed without data")
        return
    
    # Test 2: Single model card
    if not test_single_model_card(df):
        print("❌ Single model card test failed")
        return
    
    # Test 3: Model grid data preparation
    if not test_model_grid_data_preparation(df):
        print("❌ Model grid data preparation failed")
        return
    
    print("\n🎉 All debug tests passed!")
    print("💡 The string concatenation error might be occurring in Streamlit-specific code")
    print("💡 Try running the actual Streamlit app to see the full traceback")

if __name__ == "__main__":
    main()
