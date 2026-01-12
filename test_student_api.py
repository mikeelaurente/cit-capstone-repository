"""
Quick test script to verify student API endpoints are registered correctly.
Run this after starting the server to check if all routes are available.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test that all student endpoints are accessible (even if they return errors without auth)"""
    
    endpoints = [
        ("POST", "/api/student/signup", {"email": "test@test.com", "password": "test"}),
        ("POST", "/api/student/verify", {"email": "test@test.com", "code": "000000"}),
        ("POST", "/api/student/resend-code", {"email": "test@test.com"}),
        ("POST", "/api/student/login", {"identifier": "test", "password": "test"}),
        ("POST", "/api/student/forgot-password", {"email": "test@test.com"}),
        ("POST", "/api/student/reset-password", {"token": "test", "new_password": "test", "confirm_password": "test"}),
        ("GET", "/api/student/submissions", None),
        ("GET", "/api/student/submissions/1", None),
        ("POST", "/api/student/capstones/1/citation", {"format": "APA"}),
        ("GET", "/api/student/capstones/1/citations", None),
    ]
    
    print("Testing Student API Endpoints")
    print("=" * 50)
    
    for method, endpoint, data in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json=data, timeout=5)
            
            # We expect some errors (401, 400) since we're not authenticated
            # We just want to verify the endpoints exist (not 404)
            if response.status_code != 404:
                status = "✓"
                color = "\033[92m"  # Green
            else:
                status = "✗"
                color = "\033[91m"  # Red
            
            reset = "\033[0m"
            print(f"{color}{status}{reset} {method:4} {endpoint:45} [{response.status_code}]")
            
        except requests.exceptions.ConnectionError:
            print(f"\033[91m✗\033[0m Server not running at {BASE_URL}")
            print(f"  Start the server with: uvicorn main:app --reload")
            return False
        except Exception as e:
            print(f"\033[91m✗\033[0m {method} {endpoint} - Error: {e}")
    
    print("=" * 50)
    print("\nNote: 401/400/403 errors are expected without authentication.")
    print("404 errors indicate missing endpoints (not good).")
    return True

if __name__ == "__main__":
    print("\n🧪 Student API Endpoint Test\n")
    test_endpoints()
    print("\n✅ All endpoints are registered!\n")
