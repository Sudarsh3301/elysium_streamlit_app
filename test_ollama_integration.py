#!/usr/bin/env python3
"""
Test script to verify Ollama integration in the Elysium Model Catalogue
This will test if Ollama is being called correctly or if fallbacks are being used.
"""

import requests
import json
import time
from app import OllamaClient

def test_ollama_direct():
    """Test direct connection to Ollama API."""
    print("🔍 Testing direct Ollama connection...")
    
    try:
        # Test if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running with {len(models)} models available")
            for model in models:
                print(f"   - {model['name']}")
            return True
        else:
            print(f"❌ Ollama responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama - service not running")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return False

def test_ollama_generate():
    """Test Ollama generation directly."""
    print("\n🧠 Testing Ollama generation...")
    
    test_prompt = """You are a model search assistant.
Given a text client brief, extract structured filters as a valid JSON object.

Only return a JSON object with these keys if mentioned:
hair_color, eye_color, height_min, height_max, division.

Example:
Input: "Looking for blonde models around 175cm with blue eyes"
Output:
{
  "hair_color": "blonde",
  "eye_color": "blue",
  "height_min": 170,
  "height_max": 180
}

Input: "blonde models with blue eyes"
Output:"""

    try:
        payload = {
            "model": "gemma3:4b",
            "prompt": test_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }
        
        print("📤 Sending request to Ollama...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:11434/api/generate", 
            json=payload, 
            timeout=30
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').strip()
            print(f"✅ Ollama responded in {response_time:.2f} seconds")
            print(f"📝 Raw response: {response_text[:200]}...")
            
            # Try to extract JSON
            import re
            json_match = re.search(r'\{[^}]*\}', response_text)
            if json_match:
                try:
                    parsed_json = json.loads(json_match.group())
                    print(f"✅ Successfully parsed JSON: {parsed_json}")
                    return True
                except json.JSONDecodeError:
                    print("⚠️ Found JSON-like text but couldn't parse it")
                    return False
            else:
                print("⚠️ No JSON found in response")
                return False
        else:
            print(f"❌ Ollama generation failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Ollama request timed out")
        return False
    except Exception as e:
        print(f"❌ Error during Ollama generation: {e}")
        return False

def test_app_ollama_client():
    """Test the app's OllamaClient class."""
    print("\n🎯 Testing app's OllamaClient...")
    
    test_queries = [
        "blonde models with blue eyes",
        "tall brunette models around 175cm",
        "green eyes from dev division"
    ]
    
    for query in test_queries:
        print(f"\n📝 Testing query: '{query}'")
        
        try:
            # Create prompt using app's method
            prompt = OllamaClient.create_prompt(query)
            print("✅ Prompt created successfully")
            
            # Query using app's method
            start_time = time.time()
            result = OllamaClient.query_ollama(prompt)
            end_time = time.time()
            response_time = end_time - start_time
            
            if result is None:
                print("❌ OllamaClient returned None (connection error)")
                return False
            elif result == {}:
                print("⚠️ OllamaClient returned empty dict (parsing error)")
            else:
                print(f"✅ OllamaClient returned result in {response_time:.2f}s: {result}")
                
        except Exception as e:
            print(f"❌ Error in OllamaClient: {e}")
            return False
    
    return True

def main():
    """Run all Ollama integration tests."""
    print("🚀 Starting Ollama Integration Tests\n")
    
    tests = [
        ("Direct Ollama Connection", test_ollama_direct),
        ("Ollama Generation", test_ollama_generate),
        ("App OllamaClient", test_app_ollama_client)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}")
        print('='*50)
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with error: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All Ollama integration tests passed!")
        print("✅ Ollama is being called correctly, no fallbacks in use")
    elif passed >= 2:  # If at least direct connection and generation work
        print("⚠️ Ollama is working but some app integration issues detected")
    else:
        print("❌ Ollama integration has significant issues")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
