#!/usr/bin/env python3
"""
Setup script for Gemini API integration
"""

import os
import sys

def setup_gemini_api():
    """Setup Gemini API key"""
    print("🚀 Setting up Gemini API for ANPR System")
    print("=" * 50)
    
    # Check if API key is already set
    api_key = os.getenv('GEMINI_API_KEY')
    
    if api_key:
        print(f"✅ Gemini API key is already set: {api_key[:10]}...")
        return True
    
    print("❌ No Gemini API key found.")
    print("\nTo get your Gemini API key:")
    print("1. Go to https://aistudio.google.com/app/apikey")
    print("2. Create a new API key")
    print("3. Copy the key")
    print("\nThen set it as an environment variable:")
    print("Windows PowerShell:")
    print('$env:GEMINI_API_KEY="your_api_key_here"')
    print("\nWindows Command Prompt:")
    print('set GEMINI_API_KEY=your_api_key_here')
    print("\nOr create a .env file in the project root with:")
    print("GEMINI_API_KEY=your_api_key_here")
    
    return False

def test_gemini_detector():
    """Test the Gemini detector"""
    print("\n🧪 Testing Gemini Detector")
    print("=" * 30)
    
    try:
        # Add the project root to Python path
        sys.path.append(os.path.abspath('.'))
        
        from src.processing.gemini_plate_detector import GeminiPlateDetector
        
        # Initialize detector
        detector = GeminiPlateDetector()
        
        # Test connection
        if detector.gemini_available:
            print("✅ Gemini API is available")
            
            # Test connection
            if detector.test_gemini_connection():
                print("✅ Gemini connection test successful")
            else:
                print("❌ Gemini connection test failed")
        else:
            print("❌ Gemini API is not available - check your API key")
            
    except Exception as e:
        print(f"❌ Error testing Gemini detector: {e}")

if __name__ == "__main__":
    setup_gemini_api()
    test_gemini_detector()

