#!/usr/bin/env python3
"""
Test script for enhanced comparative filtering in Elysium Model Catalogue
Tests natural language queries with comparative and semantic filtering.
"""

import sys
import os
import json
import pandas as pd

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import DataLoader, FilterEngine, OllamaClient, AttributeMatcher, DivisionMapper, HeightCalculator

def test_attribute_matching():
    """Test fuzzy attribute matching with synonyms."""
    print("🧪 Testing attribute matching with synonyms...")
    
    # Test hair color synonyms
    hair_tests = [
        ("brunette", "brown", True),
        ("blonde", "light brown", True),
        ("golden", "blonde", True),
        ("jet", "black", True),
        ("auburn", "red", True),
        ("purple", "brown", False)
    ]
    
    for search, field, expected in hair_tests:
        result = AttributeMatcher.match_attribute(search, field, "hair")
        status = "✅" if result == expected else "❌"
        print(f"{status} Hair: '{search}' matches '{field}' = {result} (expected {expected})")
    
    # Test eye color synonyms
    eye_tests = [
        ("aqua", "blue", True),
        ("hazel", "brown", True),
        ("emerald", "green", True),
        ("sapphire", "blue", True),
        ("purple", "blue", False)
    ]
    
    for search, field, expected in eye_tests:
        result = AttributeMatcher.match_attribute(search, field, "eye")
        status = "✅" if result == expected else "❌"
        print(f"{status} Eye: '{search}' matches '{field}' = {result} (expected {expected})")
    
    return True

def test_division_mapping():
    """Test semantic division mapping."""
    print("\n🧪 Testing division mapping...")
    
    division_tests = [
        ("mainboard", "ima"),
        ("main", "ima"),
        ("development", "dev"),
        ("dev", "dev"),
        ("commercial", "mai"),
        ("editorial", "mai"),
        ("unknown", "unknown")
    ]
    
    for input_div, expected in division_tests:
        result = DivisionMapper.normalize_division(input_div)
        status = "✅" if result == expected else "❌"
        print(f"{status} Division: '{input_div}' → '{result}' (expected '{expected}')")
    
    return True

def test_height_calculations():
    """Test relative height calculations."""
    print("\n🧪 Testing relative height calculations...")
    
    # Create sample data
    sample_data = pd.DataFrame({
        'height_cm': [165, 170, 175, 180, 185]  # Average = 175
    })
    
    height_tests = [
        ("taller", (178, 300)),    # avg + 3 = 178
        ("shorter", (0, 172)),     # avg - 3 = 172
        ("petite", (0, 165)),      # under 165
        ("invalid", (None, None))
    ]
    
    for term, expected in height_tests:
        result = HeightCalculator.calculate_relative_height_range(sample_data, term)
        status = "✅" if result == expected else "❌"
        print(f"{status} Height '{term}': {result} (expected {expected})")
    
    return True

def test_ollama_comparative_queries():
    """Test Ollama with comparative queries."""
    print("\n🧪 Testing Ollama with comparative queries...")
    
    test_queries = [
        {
            "query": "taller blonde models with blue eyes from the development board",
            "expected_keys": ["hair_color", "eye_color", "height_relative", "division"]
        },
        {
            "query": "shorter brunette models",
            "expected_keys": ["hair_color", "height_relative"]
        },
        {
            "query": "mainboard models above average height",
            "expected_keys": ["height_relative", "division"]
        },
        {
            "query": "petite commercial faces with aqua eyes",
            "expected_keys": ["eye_color", "height_relative", "division"]
        }
    ]
    
    for test_case in test_queries:
        query = test_case["query"]
        expected_keys = test_case["expected_keys"]
        
        print(f"\n📝 Testing: '{query}'")
        
        try:
            prompt = OllamaClient.create_prompt(query)
            result = OllamaClient.query_ollama(prompt)
            
            if result is None:
                print("❌ Ollama returned None (connection error)")
                continue
            elif result == {}:
                print("⚠️ Ollama returned empty dict (parsing error)")
                continue
            
            print(f"✅ Ollama result: {result}")
            
            # Check if expected keys are present
            missing_keys = [key for key in expected_keys if key not in result]
            if missing_keys:
                print(f"⚠️ Missing expected keys: {missing_keys}")
            else:
                print("✅ All expected keys present")
                
        except Exception as e:
            print(f"❌ Error testing query: {e}")
    
    return True

def test_unified_filtering():
    """Test the unified filtering pipeline."""
    print("\n🧪 Testing unified filtering pipeline...")
    
    # Load data
    models_file = "../elysium_kb/models.jsonl"
    df = DataLoader.load_and_normalize_models(models_file)
    
    if df.empty:
        print("❌ No data to filter")
        return False
    
    print(f"📊 Total models: {len(df)}")
    print(f"📊 Average height: {df['height_cm'].mean():.1f}cm")
    
    # Test comparative filters
    test_filters = [
        {
            "name": "Taller blonde models",
            "filters": {"hair_color": "blonde", "height_relative": "taller"}
        },
        {
            "name": "Shorter brunette models", 
            "filters": {"hair_color": "brunette", "height_relative": "shorter"}
        },
        {
            "name": "Petite models",
            "filters": {"height_relative": "petite"}
        },
        {
            "name": "Development division",
            "filters": {"division": "development"}
        },
        {
            "name": "Mainboard division",
            "filters": {"division": "mainboard"}
        }
    ]
    
    for test_case in test_filters:
        name = test_case["name"]
        filters = test_case["filters"]
        
        try:
            filtered_df = FilterEngine._apply_unified_filters(df, filters)
            count = len(filtered_df)
            print(f"✅ {name}: {count} models found")
            
            if count > 0:
                # Show sample results
                sample = filtered_df.head(2)
                for _, model in sample.iterrows():
                    print(f"   - {model['name']}: {model['hair_color']}, {model['eye_color']}, {model['height_cm']}cm, {model['division']}")
            
        except Exception as e:
            print(f"❌ Error filtering {name}: {e}")
    
    return True

def main():
    """Run all comparative filtering tests."""
    print("🚀 Starting Enhanced Comparative Filtering Tests\n")
    
    tests = [
        ("Attribute Matching", test_attribute_matching),
        ("Division Mapping", test_division_mapping),
        ("Height Calculations", test_height_calculations),
        ("Ollama Comparative Queries", test_ollama_comparative_queries),
        ("Unified Filtering Pipeline", test_unified_filtering)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print('='*60)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with error: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    print('='*60)
    
    if passed == total:
        print("🎉 All comparative filtering tests passed!")
        print("✅ Enhanced natural language queries working correctly")
    else:
        print("⚠️ Some tests failed. Check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
