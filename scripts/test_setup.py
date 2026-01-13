"""
Test script to verify the setup is working correctly.
Run this after setup to ensure all components are functional.
"""
import requests
import time
import sys

API_URL = "http://localhost:8000"
WEB_URL = "http://localhost:3000"

def test_api_health():
    """Test API health endpoint."""
    print("Testing API health endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ API is healthy")
            print(f"    - Dev mode: {data.get('dev_mode')}")
            print(f"    - Database: {data.get('database')}")
            return True
        else:
            print(f"  ✗ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Cannot connect to API: {e}")
        print(f"    Make sure backend is running: cd apps/api && uvicorn main:app --reload")
        return False

def test_chat_endpoint():
    """Test chat endpoint."""
    print("\nTesting chat endpoint...")
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "session_id": "test_session_123",
                "message": "What is a Roth conversion?"
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Chat endpoint working")
            print(f"    - Response length: {len(data.get('response', ''))}")
            print(f"    - Citations: {len(data.get('citations', []))}")
            return True
        else:
            print(f"  ✗ Chat endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Chat endpoint error: {e}")
        return False

def test_lead_gate():
    """Test lead gate functionality."""
    print("\nTesting lead gate...")
    try:
        # First message
        session_id = f"test_session_{int(time.time())}"

        response1 = requests.post(
            f"{API_URL}/chat",
            json={
                "session_id": session_id,
                "message": "Tell me about retirement planning"
            },
            timeout=10
        )

        if response1.status_code != 200:
            print(f"  ✗ First message failed")
            return False

        # Second message should trigger lead gate
        response2 = requests.post(
            f"{API_URL}/chat",
            json={
                "session_id": session_id,
                "message": "What about Social Security?"
            },
            timeout=10
        )

        if response2.status_code == 200:
            data = response2.json()
            if data.get('show_lead_gate'):
                print(f"  ✓ Lead gate triggered correctly")
                return True
            else:
                print(f"  ✗ Lead gate not triggered")
                return False
        else:
            print(f"  ✗ Second message failed")
            return False

    except Exception as e:
        print(f"  ✗ Lead gate test error: {e}")
        return False

def test_lead_creation():
    """Test lead creation."""
    print("\nTesting lead creation...")
    try:
        session_id = f"test_session_{int(time.time())}"

        # Send first message to create conversation
        requests.post(
            f"{API_URL}/chat",
            json={
                "session_id": session_id,
                "message": "I'm interested in Roth conversions"
            },
            timeout=10
        )

        # Create lead
        response = requests.post(
            f"{API_URL}/lead",
            json={
                "session_id": session_id,
                "first_name": "Test",
                "email": "test@example.com",
                "phone": "555-1234"
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Lead created successfully")
            print(f"    - Bucket: {data.get('bucket')}")
            print(f"    - Meeting type: {data.get('meeting_type')}")
            print(f"    - Booking URL: {data.get('booking_url')}")
            return True
        else:
            print(f"  ✗ Lead creation failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"  ✗ Lead creation error: {e}")
        return False

def test_frontend():
    """Test frontend is accessible."""
    print("\nTesting frontend...")
    try:
        response = requests.get(WEB_URL, timeout=5)
        if response.status_code == 200:
            print(f"  ✓ Frontend is accessible")
            return True
        else:
            print(f"  ✗ Frontend returned {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Cannot connect to frontend: {e}")
        print(f"    Make sure frontend is running: cd apps/web && npm run dev")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("Fiat Clarity Chat - Setup Verification")
    print("=" * 50)
    print()

    results = []

    # Test backend
    results.append(("API Health", test_api_health()))
    results.append(("Chat Endpoint", test_chat_endpoint()))
    results.append(("Lead Gate", test_lead_gate()))
    results.append(("Lead Creation", test_lead_creation()))

    # Test frontend
    results.append(("Frontend", test_frontend()))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed! Your setup is working correctly.")
        print("\nNext steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Try asking: 'What is a Roth conversion?'")
        print("3. Send a second message to see the lead gate")
        print("4. Fill in the contact form to continue")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
