#!/usr/bin/env python3
"""
Deployment Readiness Test Suite
Tests all critical functionality to ensure the application is ready for cloud deployment.
"""

import os
import sys
from pathlib import Path
import logging

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_path_configuration():
    """Test that the centralized path configuration works correctly."""
    print("🧪 Testing Path Configuration...")
    
    try:
        from path_config import paths
        
        # Test project root detection
        print(f"   Project root: {paths.project_root}")
        
        # Test data directory
        print(f"   Data directory: {paths.data_dir}")
        if not paths.data_dir.exists():
            print("   ❌ Data directory not found")
            return False
        
        # Test images directory
        print(f"   Images directory: {paths.images_dir}")
        if not paths.images_dir.exists():
            print("   ❌ Images directory not found")
            return False
        
        # Test data file validation
        data_status = paths.validate_data_files()
        missing_files = [f for f, status in data_status.items() if not status['exists']]
        
        if missing_files:
            print(f"   ❌ Missing data files: {', '.join(missing_files)}")
            return False
        else:
            print(f"   ✅ All {len(data_status)} data files found")
        
        # Test image path resolution
        test_image = "images/eleena_mills/thumbnail.jpg"
        resolved_path = paths.get_image_path(test_image)
        if resolved_path and resolved_path.exists():
            print(f"   ✅ Image path resolution working: {test_image}")
        else:
            print(f"   ⚠️  Image path resolution test failed for: {test_image}")
        
        print("   ✅ Path configuration test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Path configuration test failed: {e}")
        return False

def test_data_loading():
    """Test that data loading works correctly."""
    print("\n🧪 Testing Data Loading...")
    
    try:
        from apollo_data import ApolloDataLoader
        
        # Initialize data loader
        loader = ApolloDataLoader()
        print(f"   Data loader initialized with directory: {loader.data_dir}")
        
        # Load all data
        data = loader.load_all_data()
        
        # Check each dataset
        expected_datasets = ['models', 'bookings', 'performance', 'clients', 'athena_events']
        for dataset in expected_datasets:
            if dataset in data and len(data[dataset]) > 0:
                print(f"   ✅ {dataset}: {len(data[dataset])} records")
            else:
                print(f"   ❌ {dataset}: No data loaded")
                return False
        
        print("   ✅ Data loading test passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Data loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_image_handling():
    """Test that image handling works correctly."""
    print("\n🧪 Testing Image Handling...")
    
    try:
        from apollo_image_utils import ApolloImageHandler
        
        handler = ApolloImageHandler()
        
        # Test image path resolution
        test_paths = [
            "images/eleena_mills/thumbnail.jpg",
            "images/andrea_kostovick/thumbnail.jpg"
        ]
        
        resolved_count = 0
        for path in test_paths:
            resolved = handler.get_local_image_path(path)
            if os.path.exists(resolved):
                resolved_count += 1
                print(f"   ✅ {path} → resolved and exists")
            else:
                print(f"   ⚠️  {path} → not found")
        
        if resolved_count > 0:
            print(f"   ✅ Image handling test passed ({resolved_count}/{len(test_paths)} images found)")
            return True
        else:
            print("   ❌ No images could be resolved")
            return False
        
    except Exception as e:
        print(f"   ❌ Image handling test failed: {e}")
        return False

def test_imports():
    """Test that all critical imports work."""
    print("\n🧪 Testing Critical Imports...")
    
    critical_modules = [
        'path_config',
        'apollo_data',
        'apollo_image_utils',
        'athena_ui',
        'template_manager'
    ]
    
    failed_imports = []
    
    for module in critical_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"   ❌ Failed to import: {', '.join(failed_imports)}")
        return False
    else:
        print("   ✅ All critical imports successful")
        return True

def test_streamlit_compatibility():
    """Test Streamlit compatibility."""
    print("\n🧪 Testing Streamlit Compatibility...")
    
    try:
        import streamlit as st
        print("   ✅ Streamlit import successful")
        
        # Check if we can import the main app module
        import app
        print("   ✅ Main app module import successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Streamlit compatibility test failed: {e}")
        return False

def test_requirements():
    """Test that all required packages are available."""
    print("\n🧪 Testing Package Requirements...")
    
    required_packages = [
        'streamlit',
        'pandas', 
        'requests',
        'PIL',  # Pillow
        'plotly',
        'jinja2',
        'reportlab'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"   ⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Install with: pip install -r requirements.txt")
        return False
    else:
        print("   ✅ All required packages available")
        return True

def main():
    """Run all deployment readiness tests."""
    print("🚀 Elysium Deployment Readiness Test Suite")
    print("=" * 60)
    
    tests = [
        ("Path Configuration", test_path_configuration),
        ("Critical Imports", test_imports),
        ("Package Requirements", test_requirements),
        ("Data Loading", test_data_loading),
        ("Image Handling", test_image_handling),
        ("Streamlit Compatibility", test_streamlit_compatibility)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        try:
            if test_func():
                passed_tests += 1
            else:
                print(f"   ❌ {test_name} test failed")
        except Exception as e:
            print(f"   ❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Application is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please address the issues before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
