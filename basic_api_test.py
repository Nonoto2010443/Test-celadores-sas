import requests
import sys
import json

def test_basic_connectivity():
    """Test basic API connectivity without AI generation"""
    base_url = "https://hospital-test-prep.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 Testing Basic API Connectivity...")
    print(f"Base URL: {base_url}")
    
    try:
        # Test root endpoint
        print("\n1. Testing root endpoint...")
        response = requests.get(f"{api_url}/", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            print("✅ Root endpoint working")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
            
        # Test stats endpoint (should work even with no data)
        print("\n2. Testing stats endpoint...")
        response = requests.get(f"{api_url}/exams/stats/summary", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"   Stats: {stats}")
            print("✅ Stats endpoint working")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            return False
            
        # Test history endpoint
        print("\n3. Testing history endpoint...")
        response = requests.get(f"{api_url}/exams/history", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            history = response.json()
            print(f"   History count: {len(history)}")
            print("✅ History endpoint working")
        else:
            print(f"❌ History endpoint failed: {response.status_code}")
            return False
            
        print("\n🎉 Basic connectivity tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def test_ai_generation():
    """Test AI generation endpoint (may fail due to budget)"""
    base_url = "https://hospital-test-prep.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("\n🤖 Testing AI Generation (may fail due to budget limits)...")
    
    try:
        response = requests.post(f"{api_url}/exams/generate", timeout=60)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            questions = response.json()
            print(f"✅ AI generation successful! Generated {len(questions)} questions")
            return True, questions
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ AI generation failed: {error_data}")
            return False, []
            
    except Exception as e:
        print(f"❌ AI generation error: {str(e)}")
        return False, []

if __name__ == "__main__":
    print("🚀 SAS Exam API Basic Tests")
    print("=" * 50)
    
    # Test basic connectivity first
    if test_basic_connectivity():
        # Try AI generation
        ai_success, questions = test_ai_generation()
        
        if ai_success:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print("\n⚠️  Basic API works, but AI generation failed (likely budget issue)")
            sys.exit(1)
    else:
        print("\n❌ Basic connectivity failed")
        sys.exit(1)