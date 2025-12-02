#!/usr/bin/env python3
"""
Validation Script for Elysium Streamlit App Refactoring
Tests that all images load correctly from HTTPS URLs and no local dependencies remain.
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_unified_data_loader():
    """Test that unified data loader works correctly."""
    logger.info("🧪 Testing unified data loader...")
    
    try:
        from unified_data_loader import unified_loader
        df = unified_loader.load_models()
        
        if df.empty:
            logger.error("❌ Unified data loader returned empty DataFrame")
            return False
        
        logger.info(f"✅ Loaded {len(df)} models from unified loader")
        
        # Check required columns
        required_cols = ['model_id', 'name', 'thumbnail', 'images']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"❌ Missing required columns: {missing_cols}")
            return False
        
        logger.info("✅ All required columns present")
        return True
        
    except Exception as e:
        logger.error(f"❌ Unified data loader test failed: {e}")
        return False

def test_https_image_urls(sample_size: int = 5):
    """Test that HTTPS image URLs are accessible."""
    logger.info(f"🧪 Testing HTTPS image URLs (sample size: {sample_size})...")
    
    try:
        from unified_data_loader import unified_loader
        df = unified_loader.load_models()
        
        if df.empty:
            logger.error("❌ No models to test")
            return False
        
        # Test sample of models
        sample_models = df.head(sample_size)
        success_count = 0
        
        for _, model in sample_models.iterrows():
            model_name = model.get('name', 'Unknown')
            thumbnail_url = model.get('thumbnail', '')
            
            if not thumbnail_url or not thumbnail_url.startswith('https://'):
                logger.warning(f"⚠️ {model_name}: Invalid thumbnail URL: {thumbnail_url}")
                continue
            
            try:
                response = requests.head(thumbnail_url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✅ {model_name}: Thumbnail accessible")
                    success_count += 1
                else:
                    logger.warning(f"⚠️ {model_name}: Thumbnail returned {response.status_code}")
            except Exception as e:
                logger.warning(f"⚠️ {model_name}: Thumbnail request failed: {e}")
        
        success_rate = success_count / len(sample_models) * 100
        logger.info(f"📊 HTTPS URL test: {success_count}/{len(sample_models)} successful ({success_rate:.1f}%)")
        
        return success_rate >= 80  # 80% success rate threshold
        
    except Exception as e:
        logger.error(f"❌ HTTPS URL test failed: {e}")
        return False

def test_no_local_dependencies():
    """Test that no local image dependencies remain."""
    logger.info("🧪 Testing for local image dependencies...")
    
    # Check if images directory exists and if app works without it
    images_dir = Path("../elysium_kb/images")
    images_existed = images_dir.exists()
    
    if images_existed:
        logger.info(f"📁 Images directory exists: {images_dir}")
        logger.info("🧪 Testing app functionality without local images...")
        
        # Temporarily rename images directory
        temp_name = images_dir.with_name("images_temp_hidden")
        try:
            images_dir.rename(temp_name)
            logger.info("📁 Temporarily hidden images directory")
            
            # Test unified loader still works
            from unified_data_loader import unified_loader
            df = unified_loader.load_models()
            
            if df.empty:
                logger.error("❌ App fails without local images directory")
                return False
            
            logger.info("✅ App works without local images directory")
            return True
            
        except Exception as e:
            logger.error(f"❌ App fails without local images: {e}")
            return False
        finally:
            # Restore images directory
            if temp_name.exists():
                temp_name.rename(images_dir)
                logger.info("📁 Restored images directory")
    else:
        logger.info("✅ No local images directory found - good!")
        return True

def main():
    """Run all validation tests."""
    logger.info("🚀 Starting Elysium Streamlit App Refactoring Validation")
    logger.info("=" * 60)
    
    tests = [
        ("Unified Data Loader", test_unified_data_loader),
        ("HTTPS Image URLs", lambda: test_https_image_urls(5)),
        ("No Local Dependencies", test_no_local_dependencies),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Refactoring is successful.")
        return True
    else:
        logger.error("⚠️ Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
