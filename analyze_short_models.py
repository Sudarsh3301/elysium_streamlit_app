#!/usr/bin/env python3
"""
Analyze short models in the dataset to understand what's available.
"""

import sys
import os
import pandas as pd

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import DataLoader

def analyze_short_models():
    """Analyze models in the shorter height ranges."""
    print("🔍 Analyzing short models in dataset...")
    
    # Load data
    models_file = "../elysium_kb/models.jsonl"
    df = DataLoader.load_and_normalize_models(models_file)
    
    print(f"📊 Total models: {len(df)}")
    print(f"📊 Height range: {df['height_cm'].min()}-{df['height_cm'].max()}cm")
    print(f"📊 Average height: {df['height_cm'].mean():.1f}cm")
    
    # Analyze by height ranges
    height_ranges = [
        ("≤165cm (petite)", df[df['height_cm'] <= 165]),
        ("166-168cm (short with variance)", df[(df['height_cm'] >= 166) & (df['height_cm'] <= 168)]),
        ("≤168cm (total with variance)", df[df['height_cm'] <= 168]),
        ("169-175cm (average)", df[(df['height_cm'] >= 169) & (df['height_cm'] <= 175)]),
        (">175cm (tall)", df[df['height_cm'] > 175])
    ]
    
    print("\n📏 Height Distribution:")
    for range_name, range_df in height_ranges:
        print(f"   {range_name}: {len(range_df)} models")
    
    # Focus on short models (≤168cm with variance)
    short_models = df[df['height_cm'] <= 168]
    
    if len(short_models) > 0:
        print(f"\n👥 Short Models (≤168cm): {len(short_models)} total")
        print("\n📋 All short models:")
        for _, model in short_models.iterrows():
            print(f"   - {model['name']}: {model['hair_color']}, {model['eye_color']}, {model['height_cm']}cm, {model['division']}")
        
        # Analyze hair colors in short models
        print(f"\n🎨 Hair colors in short models:")
        hair_counts = short_models['hair_color'].value_counts()
        for hair, count in hair_counts.items():
            print(f"   - {hair}: {count} models")
        
        # Analyze eye colors in short models
        print(f"\n👁️ Eye colors in short models:")
        eye_counts = short_models['eye_color'].value_counts()
        for eye, count in eye_counts.items():
            print(f"   - {eye}: {count} models")
        
        # Check for blonde models in short range
        blonde_short = short_models[short_models['hair_color'].str.contains('blonde', case=False, na=False)]
        print(f"\n👱 Blonde models ≤168cm: {len(blonde_short)}")
        if len(blonde_short) > 0:
            for _, model in blonde_short.iterrows():
                print(f"   - {model['name']}: {model['hair_color']}, {model['eye_color']}, {model['height_cm']}cm")
        
        # Check for blue-eyed models in short range
        blue_short = short_models[short_models['eye_color'].str.contains('blue', case=False, na=False)]
        print(f"\n👁️ Blue-eyed models ≤168cm: {len(blue_short)}")
        if len(blue_short) > 0:
            for _, model in blue_short.iterrows():
                print(f"   - {model['name']}: {model['hair_color']}, {model['eye_color']}, {model['height_cm']}cm")
    
    else:
        print("\n⚠️ No models found ≤168cm")
    
    # Suggest alternative queries
    print(f"\n💡 Alternative query suggestions:")
    
    # Find shortest blonde models
    blonde_models = df[df['hair_color'].str.contains('blonde', case=False, na=False)]
    if len(blonde_models) > 0:
        shortest_blonde = blonde_models.nsmallest(3, 'height_cm')
        print(f"\n👱 Shortest blonde models:")
        for _, model in shortest_blonde.iterrows():
            print(f"   - {model['name']}: {model['height_cm']}cm, {model['eye_color']} eyes")
    
    # Find shortest blue-eyed models
    blue_models = df[df['eye_color'].str.contains('blue', case=False, na=False)]
    if len(blue_models) > 0:
        shortest_blue = blue_models.nsmallest(3, 'height_cm')
        print(f"\n👁️ Shortest blue-eyed models:")
        for _, model in shortest_blue.iterrows():
            print(f"   - {model['name']}: {model['height_cm']}cm, {model['hair_color']} hair")
    
    # Find models that would match with relaxed criteria
    print(f"\n🔍 Relaxed matching suggestions:")
    
    # Blonde + blue eyes (any height)
    blonde_blue = df[
        (df['hair_color'].str.contains('blonde', case=False, na=False)) &
        (df['eye_color'].str.contains('blue', case=False, na=False))
    ]
    if len(blonde_blue) > 0:
        shortest_blonde_blue = blonde_blue.nsmallest(3, 'height_cm')
        print(f"\n👱👁️ Shortest blonde + blue-eyed models (any height):")
        for _, model in shortest_blonde_blue.iterrows():
            print(f"   - {model['name']}: {model['height_cm']}cm")
    
    return True

if __name__ == "__main__":
    analyze_short_models()
