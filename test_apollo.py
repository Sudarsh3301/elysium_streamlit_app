"""
Test Apollo Dashboard Module
Quick test to verify Apollo components work correctly.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_apollo_imports():
    """Test that Apollo modules can be imported."""
    print("🧪 Testing Apollo imports...")
    
    try:
        from apollo_data import ApolloDataLoader, ApolloMetrics
        print("✅ Apollo data modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import Apollo data modules: {e}")
        return False

def test_data_files():
    """Test that required data files exist."""
    print("🧪 Testing data file availability...")
    
    data_files = [
        'models_normalized.csv',
        'bookings.csv', 
        'model_performance.csv',
        'clients.csv',
        'athena_events.csv'
    ]
    
    missing_files = []
    for file in data_files:
        file_path = Path(__file__).parent.parent / 'out' / file
        if file_path.exists():
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_data_loading():
    """Test data loading functionality."""
    print("🧪 Testing data loading...")
    
    try:
        from apollo_data import ApolloDataLoader, ApolloMetrics
        
        # Initialize loader
        loader = ApolloDataLoader(data_dir="../out")
        print("✅ ApolloDataLoader initialized")
        
        # Load data
        data = loader.load_all_data()
        print("✅ Data loading completed")
        
        # Check data
        for key, df in data.items():
            print(f"📊 {key}: {len(df)} records")
        
        # Test metrics calculation
        metrics_calc = ApolloMetrics(data)
        kpi_metrics = metrics_calc.calculate_kpi_metrics()
        print(f"✅ KPI metrics calculated: {len(kpi_metrics)} metrics")
        
        return True
        
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_apollo_page():
    """Test Apollo page components."""
    print("🧪 Testing Apollo page components...")
    
    try:
        from pages.apollo import (
            apply_apollo_styling, 
            render_kpi_tile, 
            navigate_to_athena,
            get_client_churn_risk,
            generate_predictive_insights
        )
        print("✅ Apollo page functions imported")
        
        # Test KPI tile rendering
        tile_html = render_kpi_tile("Test Metric", "$1,000", 5.5, "Test insight", "📊")
        assert "kpi-tile" in tile_html
        print("✅ KPI tile rendering works")
        
        return True
        
    except Exception as e:
        print(f"❌ Apollo page test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Apollo tests."""
    print("🚀 Starting Apollo Dashboard Tests\n")
    
    tests = [
        test_apollo_imports,
        test_data_files,
        test_data_loading,
        test_apollo_page
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED\n")
            else:
                print("❌ FAILED\n")
        except Exception as e:
            print(f"❌ FAILED with error: {e}\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Apollo dashboard is ready.")
        print("\n🚀 To run the app:")
        print("   cd elysium_streamlit_app")
        print("   streamlit run app.py")
        print("\n📊 Then navigate to the Apollo tab to see the intelligence dashboard.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
