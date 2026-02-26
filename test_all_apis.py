#!/usr/bin/env python3
"""
Comprehensive API Testing Script
Tests all endpoints in the Wedding Invitations Platform API

Usage:
    python test_all_apis.py

Requirements:
    pip install requests colorama
"""

import requests
import json
import time
from datetime import datetime
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

# Configuration
BASE_URL = "http://localhost:8000"
API_VERSION = "v1"
API_BASE = f"{BASE_URL}/api/{API_VERSION}"

# Test data
TEST_USER = {
    "phone": "+919876543210",
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "TestPassword123",
    "password_confirm": "TestPassword123"
}

TEST_ADMIN = {
    "phone": "+919876543211",
    "username": "adminuser",
    "email": "admin@example.com",
    "password": "AdminPassword123"
}

# Global variables for tokens and IDs
auth_token = None
refresh_token = None
user_id = None
invitation_slug = None
order_id = None


def print_header(title):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{title.center(80)}")
    print(f"{'=' * 80}\n")


def print_test(name, status, details=""):
    """Print test result."""
    if status == "PASS":
        print(f"{Fore.GREEN}✓ {name}")
    elif status == "FAIL":
        print(f"{Fore.RED}✗ {name}")
    elif status == "SKIP":
        print(f"{Fore.YELLOW}⊘ {name}")
    elif status == "INFO":
        print(f"{Fore.BLUE}ℹ {name}")

    if details:
        print(f"  {Fore.WHITE}{details}")


def make_request(method, endpoint, data=None, auth=False, files=None, params=None):
    """Make HTTP request and return response."""
    url = f"{API_BASE}{endpoint}"
    headers = {}

    if auth and auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    if data and not files:
        headers["Content-Type"] = "application/json"

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, data=data, files=files, timeout=10)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return None

        return response
    except requests.exceptions.RequestException as e:
        print_test(f"Request failed: {endpoint}", "FAIL", str(e))
        return None


def test_api_root():
    """Test API root endpoint."""
    print_header("1. API ROOT")

    response = make_request("GET", "/")
    if response and response.status_code == 200:
        data = response.json()
        print_test("API Root accessible", "PASS", f"Status: {data.get('status')}")
        print_test("Version", "INFO", data.get('version'))
        print(f"\n{Fore.CYAN}Available Endpoints:")
        for key, value in data.get('endpoints', {}).items():
            print(f"  - {key}: {value}")
    else:
        print_test("API Root accessible", "FAIL", "Server not responding")


def test_authentication():
    """Test authentication endpoints."""
    global auth_token, refresh_token, user_id

    print_header("2. AUTHENTICATION")

    # Test registration
    response = make_request("POST", "/auth/register/", TEST_USER)
    if response and response.status_code in [200, 201]:
        data = response.json()
        print_test("User registration", "PASS", f"User created: {data.get('user', {}).get('username')}")
        auth_token = data.get('access')
        refresh_token = data.get('refresh')
        user_id = data.get('user', {}).get('id')
    elif response and response.status_code == 400:
        print_test("User registration", "SKIP", "User already exists")
        # Try login instead
        response = make_request("POST", "/auth/login/", {
            "phone": TEST_USER["phone"],
            "password": TEST_USER["password"]
        })
        if response and response.status_code == 200:
            data = response.json()
            auth_token = data.get('access')
            refresh_token = data.get('refresh')
            user_id = data.get('user', {}).get('id')
            print_test("User login (fallback)", "PASS")
    else:
        print_test("User registration", "FAIL", response.text if response else "No response")

    # Test login
    response = make_request("POST", "/auth/login/", {
        "phone": TEST_USER["phone"],
        "password": TEST_USER["password"]
    })
    if response and response.status_code == 200:
        data = response.json()
        print_test("User login", "PASS", f"Token received: {data.get('access')[:20]}...")
        auth_token = data.get('access')
        refresh_token = data.get('refresh')
    else:
        print_test("User login", "FAIL", response.text if response else "No response")

    # Test token refresh
    if refresh_token:
        response = make_request("POST", "/auth/refresh/", {"refresh": refresh_token})
        if response and response.status_code == 200:
            data = response.json()
            print_test("Token refresh", "PASS")
            auth_token = data.get('access')
        else:
            print_test("Token refresh", "FAIL", response.text if response else "No response")

    # Test profile access
    response = make_request("GET", "/auth/profile/", auth=True)
    if response and response.status_code == 200:
        data = response.json()
        print_test("Profile access", "PASS", f"User: {data.get('username')}")
    else:
        print_test("Profile access", "FAIL", response.text if response else "No response")

    # Test logout
    response = make_request("POST", "/auth/logout/", {"refresh": refresh_token}, auth=True)
    if response and response.status_code == 200:
        print_test("User logout", "PASS")
        # Get new token for continuing tests
        response = make_request("POST", "/auth/login/", {
            "phone": TEST_USER["phone"],
            "password": TEST_USER["password"]
        })
        if response and response.status_code == 200:
            auth_token = response.json().get('access')
    else:
        print_test("User logout", "FAIL", response.text if response else "No response")


def test_plans():
    """Test plans endpoints."""
    print_header("3. PLANS & TEMPLATES")

    # Test plan list
    response = make_request("GET", "/plans/")
    if response and response.status_code == 200:
        data = response.json()
        plans_count = len(data)
        print_test("Plan list", "PASS", f"Found {plans_count} plans")
        if plans_count > 0:
            print(f"  Plans: {', '.join([p['name'] for p in data])}")
    else:
        print_test("Plan list", "FAIL", response.text if response else "No response")

    # Test plan detail
    response = make_request("GET", "/plans/FREE/")
    if response and response.status_code == 200:
        data = response.json()
        print_test("Plan detail (FREE)", "PASS", f"Price: {data.get('price')}")
    else:
        print_test("Plan detail (FREE)", "FAIL", response.text if response else "No response")

    # Test categories
    response = make_request("GET", "/plans/categories/list")
    if response and response.status_code == 200:
        data = response.json()
        print_test("Category list", "PASS", f"Found {len(data)} categories")
    else:
        print_test("Category list", "FAIL", response.text if response else "No response")

    # Test templates
    response = make_request("GET", "/plans/templates/all")
    if response and response.status_code == 200:
        data = response.json()
        print_test("Template list", "PASS", f"Found {len(data)} templates")
    else:
        print_test("Template list", "FAIL", response.text if response else "No response")

    # Test featured templates
    response = make_request("GET", "/plans/templates/featured")
    if response and response.status_code == 200:
        data = response.json()
        print_test("Featured templates", "PASS", f"Found {len(data)} featured")
    else:
        print_test("Featured templates", "FAIL", response.text if response else "No response")


def test_invitations():
    """Test invitations endpoints."""
    global invitation_slug, order_id

    print_header("4. INVITATIONS & ORDERS")

    # Test order creation
    response = make_request("POST", "/invitations/orders/create/", {
        "plan": "FREE",
        "template_id": None,
        "quantity": 1
    }, auth=True)

    if response and response.status_code in [200, 201]:
        data = response.json()
        order_id = data.get('id')
        print_test("Order creation", "PASS", f"Order ID: {order_id}")
    else:
        print_test("Order creation", "FAIL", response.text if response else "No response")

    # Test order list
    response = make_request("GET", "/invitations/orders/", auth=True)
    if response and response.status_code == 200:
        data = response.json()
        print_test("Order list", "PASS", f"Found {len(data)} orders")
    else:
        print_test("Order list", "FAIL", response.text if response else "No response")

    # Test invitation creation
    response = make_request("POST", "/invitations/create/", {
        "title": "Test Wedding",
        "event_type": "wedding",
        "bride_name": "Jane",
        "groom_name": "John",
        "event_date": "2026-12-31",
        "event_time": "18:00",
        "venue_name": "Test Venue",
        "venue_address": "123 Test St",
        "message": "Join us for our special day!"
    }, auth=True)

    if response and response.status_code in [200, 201]:
        data = response.json()
        invitation_slug = data.get('slug')
        print_test("Invitation creation", "PASS", f"Slug: {invitation_slug}")
    else:
        print_test("Invitation creation", "FAIL", response.text if response else "No response")

    # Test invitation list
    response = make_request("GET", "/invitations/", auth=True)
    if response and response.status_code == 200:
        data = response.json()
        print_test("Invitation list", "PASS", f"Found {len(data)} invitations")
    else:
        print_test("Invitation list", "FAIL", response.text if response else "No response")

    # Test invitation detail
    if invitation_slug:
        response = make_request("GET", f"/invitations/{invitation_slug}/", auth=True)
        if response and response.status_code == 200:
            data = response.json()
            print_test("Invitation detail", "PASS", f"Title: {data.get('title')}")
        else:
            print_test("Invitation detail", "FAIL", response.text if response else "No response")

        # Test invitation stats
        response = make_request("GET", f"/invitations/{invitation_slug}/stats/", auth=True)
        if response and response.status_code == 200:
            data = response.json()
            print_test("Invitation stats", "PASS", f"Views: {data.get('total_views', 0)}")
        else:
            print_test("Invitation stats", "FAIL", response.text if response else "No response")


def test_ai_features():
    """Test AI endpoints."""
    print_header("5. AI FEATURES")

    # Test message generation
    response = make_request("POST", "/ai/generate-messages/", {
        "event_type": "wedding",
        "bride_name": "Jane",
        "groom_name": "John",
        "style": "formal"
    }, auth=True)

    if response and response.status_code == 200:
        data = response.json()
        print_test("Message generation", "PASS", f"Generated {len(data.get('messages', []))} messages")
    else:
        print_test("Message generation", "FAIL", response.text if response else "No response")

    # Test hashtag generation
    response = make_request("POST", "/ai/generate-hashtags/", {
        "bride_name": "Jane",
        "groom_name": "John"
    }, auth=True)

    if response and response.status_code == 200:
        data = response.json()
        print_test("Hashtag generation", "PASS", f"Generated {len(data.get('hashtags', []))} hashtags")
    else:
        print_test("Hashtag generation", "FAIL", response.text if response else "No response")

    # Test AI usage stats
    response = make_request("GET", "/ai/usage/", auth=True)
    if response and response.status_code == 200:
        data = response.json()
        print_test("AI usage stats", "PASS", f"Used: {data.get('usage', {}).get('total_requests', 0)}")
    else:
        print_test("AI usage stats", "FAIL", response.text if response else "No response")

    # Test AI limits
    response = make_request("GET", "/ai/limits/", auth=True)
    if response and response.status_code == 200:
        data = response.json()
        print_test("AI limits", "PASS", f"Limit: {data.get('monthly_limit')}")
    else:
        print_test("AI limits", "FAIL", response.text if response else "No response")


def test_public_endpoints():
    """Test public invitation endpoints."""
    global invitation_slug

    print_header("6. PUBLIC ENDPOINTS")

    if not invitation_slug:
        print_test("Public endpoints", "SKIP", "No invitation slug available")
        return

    # Test public invitation view
    response = requests.get(f"{BASE_URL}/api/invite/{invitation_slug}/", timeout=10)
    if response and response.status_code == 200:
        data = response.json()
        print_test("Public invitation view", "PASS", f"Title: {data.get('title')}")
    else:
        print_test("Public invitation view", "FAIL", response.text if response else "No response")

    # Test guest registration
    response = requests.post(
        f"{BASE_URL}/api/invite/{invitation_slug}/register/",
        json={
            "name": "Guest User",
            "phone": "+919876543299",
            "email": "guest@example.com"
        },
        timeout=10
    )

    if response and response.status_code in [200, 201]:
        print_test("Guest registration", "PASS")
    else:
        print_test("Guest registration", "FAIL", response.text if response else "No response")


def test_admin_dashboard():
    """Test admin dashboard endpoints."""
    print_header("7. ADMIN DASHBOARD")

    # Note: These require admin authentication
    print_test("Admin endpoints", "SKIP", "Requires admin authentication")

    # Test dashboard stats (if user has permission)
    response = make_request("GET", "/admin-dashboard/dashboard/", auth=True)
    if response and response.status_code == 200:
        data = response.json()
        print_test("Dashboard stats", "PASS", "Stats retrieved")
    elif response and response.status_code == 403:
        print_test("Dashboard stats", "SKIP", "Requires admin permission")
    else:
        print_test("Dashboard stats", "FAIL", response.text if response else "No response")


def test_error_handling():
    """Test error handling."""
    print_header("8. ERROR HANDLING")

    # Test 404
    response = make_request("GET", "/nonexistent/")
    if response and response.status_code == 404:
        print_test("404 Not Found", "PASS")
    else:
        print_test("404 Not Found", "FAIL")

    # Test unauthorized access
    response = make_request("GET", "/auth/profile/", auth=False)
    if response and response.status_code == 401:
        print_test("401 Unauthorized", "PASS")
    else:
        print_test("401 Unauthorized", "FAIL")

    # Test invalid data
    response = make_request("POST", "/auth/login/", {"invalid": "data"})
    if response and response.status_code in [400, 401]:
        print_test("400 Bad Request", "PASS")
    else:
        print_test("400 Bad Request", "FAIL")


def generate_report():
    """Generate test summary report."""
    print_header("TEST SUMMARY")

    print(f"{Fore.CYAN}Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Fore.CYAN}Base URL: {BASE_URL}")
    print(f"{Fore.CYAN}API Version: {API_VERSION}")

    print(f"\n{Fore.YELLOW}Note: Some tests may be skipped if:")
    print(f"  - Server is not running")
    print(f"  - Database is not initialized")
    print(f"  - Admin permissions are required")
    print(f"  - Dependencies are missing")


def main():
    """Main test runner."""
    print(f"\n{Fore.GREEN}{Style.BRIGHT}{'*' * 80}")
    print(f"{Fore.GREEN}{Style.BRIGHT}Wedding Invitations Platform - API Test Suite".center(80))
    print(f"{Fore.GREEN}{Style.BRIGHT}{'*' * 80}")

    try:
        test_api_root()
        test_authentication()
        test_plans()
        test_invitations()
        test_ai_features()
        test_public_endpoints()
        test_admin_dashboard()
        test_error_handling()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Test interrupted by user")
    except Exception as e:
        print(f"\n\n{Fore.RED}Test failed with error: {str(e)}")
    finally:
        generate_report()
        print(f"\n{Fore.GREEN}{'*' * 80}\n")


if __name__ == "__main__":
    main()
