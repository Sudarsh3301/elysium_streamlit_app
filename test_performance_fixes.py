#!/usr/bin/env python3
"""
Test script to validate Apollo dashboard performance fixes.
Tests image optimization, caching, and lazy loading improvements.
"""

import os
import sys
import time
import tempfile
from PIL import Image
import io

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apollo_image_utils import ApolloImageHandler

def create_test_image(size=(800, 600), format='JPEG'):
    """Create a test image for performance testing."""
    # Create a test image with some content
    img = Image.new('RGB', size, color='red')
    
    # Add some visual content to make it more realistic
    for i in range(0, size[0], 50):
        for j in range(0, size[1], 50):
            color = (i % 255, j % 255, (i + j) % 255)
            for x in range(i, min(i + 25, size[0])):
                for y in range(j, min(j + 25, size[1])):
                    img.putpixel((x, y), color)
    
    return img

def test_image_optimization():
    """Test image optimization functionality."""
    print("🧪 Testing Image Optimization...")
    
    handler = ApolloImageHandler()
    
    # Create a temporary large image
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        test_img = create_test_image((1200, 800))
        test_img.save(tmp_file.name, 'JPEG', quality=95)
        tmp_path = tmp_file.name
    
    try:
        # Test original image size
        original_size = os.path.getsize(tmp_path)
        print(f"   Original image size: {original_size:,} bytes")
        
        # Test optimized base64 conversion
        start_time = time.time()
        optimized_base64 = handler.get_image_base64(tmp_path, optimize=True)
        optimization_time = time.time() - start_time
        
        # Calculate optimized size (approximate from base64 length)
        # Base64 encoding increases size by ~33%, so divide by 1.33 to get approximate binary size
        optimized_size = len(optimized_base64.split(',')[1]) * 3 // 4
        
        print(f"   Optimized image size: {optimized_size:,} bytes")
        print(f"   Size reduction: {((original_size - optimized_size) / original_size * 100):.1f}%")
        print(f"   Optimization time: {optimization_time:.3f} seconds")
        
        # Test unoptimized base64 conversion
        start_time = time.time()
        unoptimized_base64 = handler.get_image_base64(tmp_path, optimize=False)
        unoptimized_time = time.time() - start_time
        
        unoptimized_size = len(unoptimized_base64.split(',')[1]) * 3 // 4
        
        print(f"   Unoptimized base64 size: {unoptimized_size:,} bytes")
        print(f"   Unoptimized time: {unoptimized_time:.3f} seconds")
        
        # Verify optimization worked
        assert optimized_size < original_size, "Optimization should reduce file size"
        assert optimized_base64.startswith('data:image/jpeg;base64,'), "Should return proper data URL"
        
        print("   ✅ Image optimization working correctly!")
        
    finally:
        # Clean up
        os.unlink(tmp_path)

def test_caching_performance():
    """Test caching performance improvements."""
    print("\n🧪 Testing Caching Performance...")
    
    handler = ApolloImageHandler()
    
    # Create multiple test images
    test_images = []
    for i in range(5):
        with tempfile.NamedTemporaryFile(suffix=f'_test_{i}.jpg', delete=False) as tmp_file:
            test_img = create_test_image((400, 300))
            test_img.save(tmp_file.name, 'JPEG', quality=80)
            test_images.append(tmp_file.name)
    
    try:
        # Test first access (cache miss)
        start_time = time.time()
        for img_path in test_images:
            handler.get_image_base64(img_path, optimize=True)
        first_access_time = time.time() - start_time
        
        print(f"   First access (cache miss): {first_access_time:.3f} seconds")
        print(f"   Cache hits: {handler._cache_hits}, Cache misses: {handler._cache_misses}")
        
        # Reset counters
        initial_misses = handler._cache_misses
        
        # Test second access (cache hit)
        start_time = time.time()
        for img_path in test_images:
            handler.get_image_base64(img_path, optimize=True)
        second_access_time = time.time() - start_time
        
        print(f"   Second access (cache hit): {second_access_time:.3f} seconds")
        print(f"   Cache hits: {handler._cache_hits}, Cache misses: {handler._cache_misses}")
        
        # Verify caching worked
        assert handler._cache_misses == initial_misses, "Should not have additional cache misses"
        assert second_access_time < first_access_time, "Cached access should be faster"
        
        speedup = first_access_time / second_access_time if second_access_time > 0 else float('inf')
        print(f"   Cache speedup: {speedup:.1f}x faster")
        print("   ✅ Caching working correctly!")
        
    finally:
        # Clean up
        for img_path in test_images:
            os.unlink(img_path)

def test_lazy_loading():
    """Test lazy loading functionality."""
    print("\n🧪 Testing Lazy Loading...")
    
    handler = ApolloImageHandler()
    
    # Create test thumbnail paths
    test_thumbnails = [f"test_thumb_{i}.jpg" for i in range(10)]
    
    # Test lazy loading (should only render 1 initially)
    lazy_html = handler.render_thumbnail_strip(test_thumbnails, size=32, max_count=5, lazy_load=True)
    
    # Count how many thumbnails are actually rendered
    thumbnail_count = lazy_html.count('apollo-thumbnail')
    more_indicator = '+' in lazy_html
    
    print(f"   Lazy loading rendered: {thumbnail_count} thumbnails")
    print(f"   More indicator present: {more_indicator}")
    
    # Test non-lazy loading
    non_lazy_html = handler.render_thumbnail_strip(test_thumbnails, size=32, max_count=5, lazy_load=False)
    non_lazy_count = non_lazy_html.count('apollo-thumbnail')
    
    print(f"   Non-lazy loading rendered: {non_lazy_count} thumbnails")
    
    # Verify lazy loading worked
    assert thumbnail_count < non_lazy_count, "Lazy loading should render fewer thumbnails"
    assert thumbnail_count == 1, "Lazy loading should render only 1 thumbnail initially"
    assert more_indicator, "Should show more indicator when there are additional thumbnails"
    
    print("   ✅ Lazy loading working correctly!")

def test_cache_size_management():
    """Test cache size management."""
    print("\n🧪 Testing Cache Size Management...")
    
    handler = ApolloImageHandler()
    
    # Create more images than cache limit
    test_images = []
    cache_limit = handler._max_cache_size
    num_images = cache_limit + 10
    
    for i in range(num_images):
        with tempfile.NamedTemporaryFile(suffix=f'_cache_test_{i}.jpg', delete=False) as tmp_file:
            test_img = create_test_image((200, 150))
            test_img.save(tmp_file.name, 'JPEG', quality=70)
            test_images.append(tmp_file.name)
    
    try:
        # Load all images (should trigger cache management)
        for img_path in test_images:
            handler.get_image_base64(img_path, optimize=True)
        
        cache_size = len(handler.image_cache)
        print(f"   Cache limit: {cache_limit}")
        print(f"   Images processed: {num_images}")
        print(f"   Final cache size: {cache_size}")
        
        # Verify cache size is managed
        assert cache_size <= cache_limit, f"Cache size ({cache_size}) should not exceed limit ({cache_limit})"
        
        print("   ✅ Cache size management working correctly!")
        
    finally:
        # Clean up
        for img_path in test_images:
            os.unlink(img_path)

def main():
    """Run all performance tests."""
    print("🚀 Apollo Dashboard Performance Tests")
    print("=" * 50)
    
    try:
        test_image_optimization()
        test_caching_performance()
        test_lazy_loading()
        test_cache_size_management()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Performance fixes are working correctly.")
        print("\nKey improvements:")
        print("• Images are automatically resized and compressed for thumbnails")
        print("• Caching provides significant speedup for repeated access")
        print("• Lazy loading reduces initial page load by showing fewer thumbnails")
        print("• Cache size is managed to prevent memory issues")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
