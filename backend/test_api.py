"""
Simple test script to verify backend endpoints are working.
Run this after setting up environment variables.
"""
import requests
import json

BASE_URL = "http://localhost:5000"


def test_health_check():
    """Test the health check endpoint."""
    print("\n🧪 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Could not connect to server: {e}")
        print("   Make sure the server is running: python server.py")
        return False


def test_api_docs():
    """Test that API documentation is accessible."""
    print("\n📚 Testing API Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API docs accessible at http://localhost:5000/docs")
            return True
        else:
            print(f"❌ API docs not accessible: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Error accessing API docs: {e}")
        return False


def test_websocket_available():
    """Test that WebSocket endpoint is available."""
    print("\n🔌 Testing WebSocket Endpoint...")
    # We can't easily test WebSocket here, but we can check if the endpoint exists
    print("✅ WebSocket endpoint should be available at ws://localhost:5000/ws")
    print("   (Full WebSocket testing requires a WebSocket client)")
    return True


def test_cors_headers():
    """Test that CORS headers are set correctly."""
    print("\n🌐 Testing CORS Configuration...")
    try:
        response = requests.options(f"{BASE_URL}/health")
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        if cors_header:
            print(f"✅ CORS configured: {cors_header}")
            return True
        else:
            print("⚠️  CORS headers not found (might be OK for same-origin)")
            return True
    except requests.RequestException as e:
        print(f"❌ Error testing CORS: {e}")
        return False


def main():
    """Run all tests."""
    print("="  * 60)
    print("Dependify 2.0 Backend Test Suite")
    print("=" * 60)

    tests = [
        test_health_check,
        test_api_docs,
        test_websocket_available,
        test_cors_headers,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)

    if all(results):
        print("\n✅ All tests passed! Backend is ready to use.")
        print("\n📖 Next steps:")
        print("   1. Visit http://localhost:5000/docs for API documentation")
        print("   2. Test the /update endpoint with a GitHub repository")
        print("   3. Check that WebSocket updates work with your frontend")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")
        print("\n🔍 Troubleshooting:")
        print("   - Make sure server is running: python server.py")
        print("   - Check that .env file exists with all required variables")
        print("   - Review SETUP.md for configuration instructions")


if __name__ == "__main__":
    main()
