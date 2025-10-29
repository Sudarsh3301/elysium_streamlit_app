#!/usr/bin/env python3
"""
Final validation test for Apollo dashboard fixes.
Validates that the performance and image issues have been resolved.
"""

import os
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_page_load_performance():
    """Test that the Apollo dashboard loads quickly without performance issues."""
    print("🧪 Testing Page Load Performance...")
    
    # Setup Chrome options for headless testing
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Measure page load time
        start_time = time.time()
        driver.get("http://localhost:8505")
        
        # Wait for the main content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        load_time = time.time() - start_time
        print(f"   Page load time: {load_time:.2f} seconds")
        
        # Check if there are any error messages
        error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Failed to load') or contains(text(), 'Error')]")
        if error_elements:
            print(f"   ⚠️  Found {len(error_elements)} error messages on page")
            for error in error_elements:
                print(f"      - {error.text[:100]}")
        else:
            print("   ✅ No error messages found")
        
        # Check for base64 images (should be none now)
        page_source = driver.page_source
        base64_count = page_source.count('data:image/jpeg;base64,')
        print(f"   Base64 images found: {base64_count}")
        
        if base64_count == 0:
            print("   ✅ No base64 images found - performance issue resolved!")
        else:
            print(f"   ⚠️  Still found {base64_count} base64 images")
        
        # Check page size
        page_size = len(page_source)
        print(f"   Page size: {page_size:,} characters")
        
        if page_size < 500000:  # Less than 500KB
            print("   ✅ Page size is reasonable")
        else:
            print("   ⚠️  Page size is large, may affect performance")
        
        # Verify key dashboard elements are present
        dashboard_elements = [
            "Apollo — Agency Intelligence",
            "Total Revenue",
            "Model Intelligence"
        ]
        
        missing_elements = []
        for element_text in dashboard_elements:
            if element_text not in page_source:
                missing_elements.append(element_text)
        
        if missing_elements:
            print(f"   ⚠️  Missing dashboard elements: {missing_elements}")
        else:
            print("   ✅ All key dashboard elements present")
        
        return {
            'load_time': load_time,
            'base64_images': base64_count,
            'page_size': page_size,
            'errors': len(error_elements),
            'missing_elements': len(missing_elements)
        }
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return None
        
    finally:
        if driver:
            driver.quit()

def test_streamlit_server_status():
    """Test that the Streamlit server is running and responsive."""
    print("\n🧪 Testing Streamlit Server Status...")
    
    try:
        response = requests.get("http://localhost:8505", timeout=10)
        print(f"   Server response code: {response.status_code}")
        print(f"   Response time: {response.elapsed.total_seconds():.2f} seconds")
        
        if response.status_code == 200:
            print("   ✅ Server is running and responsive")
            return True
        else:
            print(f"   ⚠️  Server returned status code {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Server connection failed: {e}")
        return False

def test_image_path_resolution():
    """Test that image path resolution is working correctly."""
    print("\n🧪 Testing Image Path Resolution...")
    
    try:
        from apollo_image_utils import ApolloImageHandler
        
        handler = ApolloImageHandler()
        
        # Test with a known image path
        test_path = "images/eleena_mills/thumbnail.jpg"
        resolved_path = handler.get_image_path(test_path)
        
        print(f"   Test path: {test_path}")
        print(f"   Resolved path: {resolved_path}")
        
        if resolved_path and os.path.exists(resolved_path):
            print("   ✅ Image path resolution working correctly")
            return True
        else:
            print("   ⚠️  Image path resolution not working or file not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Image path test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Apollo Dashboard Final Validation Tests")
    print("=" * 60)
    
    # Test server status first
    server_ok = test_streamlit_server_status()
    if not server_ok:
        print("\n❌ Server is not running. Please start the Apollo dashboard first:")
        print("   streamlit run pages/apollo.py --server.port 8505")
        return
    
    # Test image path resolution
    image_paths_ok = test_image_path_resolution()
    
    # Test page performance
    performance_results = test_page_load_performance()
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    if performance_results:
        print(f"✅ Page Load Time: {performance_results['load_time']:.2f}s")
        print(f"✅ Base64 Images: {performance_results['base64_images']} (should be 0)")
        print(f"✅ Page Size: {performance_results['page_size']:,} chars")
        print(f"✅ Errors: {performance_results['errors']}")
        print(f"✅ Missing Elements: {performance_results['missing_elements']}")
        
        # Overall assessment
        issues = []
        if performance_results['load_time'] > 10:
            issues.append("Slow page load")
        if performance_results['base64_images'] > 0:
            issues.append("Base64 images still present")
        if performance_results['page_size'] > 500000:
            issues.append("Large page size")
        if performance_results['errors'] > 0:
            issues.append("Error messages present")
        if performance_results['missing_elements'] > 0:
            issues.append("Missing dashboard elements")
        
        if not issues:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Performance issues have been resolved")
            print("✅ Image display issues have been resolved")
            print("✅ Dashboard is loading correctly")
        else:
            print(f"\n⚠️  Issues found: {', '.join(issues)}")
    else:
        print("❌ Performance tests failed to run")
    
    if not image_paths_ok:
        print("⚠️  Image path resolution needs attention")

if __name__ == "__main__":
    main()
