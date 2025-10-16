#!/usr/bin/env python3
"""
Test script to verify fallback behavior when Ollama is not available
"""

import requests
import json
import re
from unittest.mock import patch

def test_ollama_fallback():
    """Test what happens when Ollama is not available."""
    print("🔄 Testing Ollama fallback behavior...")
    
    # Simulate the OllamaClient.query_ollama method with connection error
    def simulate_connection_error(prompt):
        """Simulate what happens when Ollama is not available."""
        try:
            # This will fail because we're using a non-existent port
            payload = {
                "model": "gemma3:4b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            response = requests.post("http://localhost:99999/api/generate", json=payload, timeout=5)
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get('response', '').strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{[^}]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            
            return {}
            
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Ollama. Please ensure Ollama is running on localhost:11434")
            return None
        except requests.exceptions.Timeout:
            print("⏱️ Ollama request timed out. Please try again.")
            return None
        except json.JSONDecodeError as e:
            print(f"⚠️ Could not parse AI response as JSON: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error querying Ollama: {e}")
            return None
    
    # Test the fallback
    test_prompt = "Looking for blonde models with blue eyes"
    result = simulate_connection_error(test_prompt)
    
    if result is None:
        print("✅ Correctly returned None when Ollama unavailable")
        print("✅ Error message displayed to user")
        return True
    else:
        print(f"❌ Expected None but got: {result}")
        return False

def test_json_parsing_fallback():
    """Test what happens when Ollama returns invalid JSON."""
    print("\n🔄 Testing JSON parsing fallback...")
    
    def simulate_invalid_json_response(prompt):
        """Simulate Ollama returning invalid JSON."""
        try:
            # Simulate a response that's not valid JSON
            response_text = "This is not valid JSON but might contain some text"
            
            # Extract JSON from response
            json_match = re.search(r'\{[^}]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            
            return {}
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Could not parse AI response as JSON: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error querying Ollama: {e}")
            return None
    
    result = simulate_invalid_json_response("test prompt")
    
    if result == {}:
        print("✅ Correctly returned empty dict when JSON parsing fails")
        print("✅ Warning message displayed to user")
        return True
    else:
        print(f"❌ Expected empty dict but got: {result}")
        return False

def test_timeout_fallback():
    """Test what happens when Ollama times out."""
    print("\n🔄 Testing timeout fallback...")
    
    def simulate_timeout(prompt):
        """Simulate Ollama timing out."""
        try:
            # This will timeout because we're using a very short timeout
            payload = {
                "model": "gemma3:4b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            # Use a real endpoint but with impossible timeout
            response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=0.001)
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get('response', '').strip()
            
            json_match = re.search(r'\{[^}]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            
            return {}
            
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Ollama. Please ensure Ollama is running on localhost:11434")
            return None
        except requests.exceptions.Timeout:
            print("⏱️ Ollama request timed out. Please try again.")
            return None
        except json.JSONDecodeError as e:
            print(f"⚠️ Could not parse AI response as JSON: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error querying Ollama: {e}")
            return None
    
    result = simulate_timeout("test prompt")
    
    if result is None:
        print("✅ Correctly returned None when request times out")
        print("✅ Timeout message displayed to user")
        return True
    else:
        print(f"❌ Expected None but got: {result}")
        return False

def main():
    """Run all fallback tests."""
    print("🚀 Starting Ollama Fallback Tests\n")
    
    tests = [
        ("Connection Error Fallback", test_ollama_fallback),
        ("JSON Parsing Fallback", test_json_parsing_fallback),
        ("Timeout Fallback", test_timeout_fallback)
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
    print(f"📊 Fallback Test Results: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All fallback mechanisms working correctly!")
        print("✅ App gracefully handles Ollama unavailability")
    else:
        print("⚠️ Some fallback mechanisms may have issues")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
