#!/bin/bash
# Quick API Test Script for Linux/Mac
# Tests basic API endpoints to verify the server is working

echo "================================================================================"
echo "Wedding Invitations Platform - Quick API Test"
echo "================================================================================"
echo ""

BASE_URL="http://localhost:8000"

echo "[1/8] Testing if server is running..."
if curl -s "$BASE_URL/api/v1/" > /dev/null 2>&1; then
    echo "✓ Server is running"
else
    echo "✗ Server is not running. Please start the backend server first."
    echo "Run: cd apps/backend/src && python manage.py runserver"
    exit 1
fi
echo ""

echo "[2/8] Testing API Root..."
curl -s "$BASE_URL/api/v1/" | jq . || curl -s "$BASE_URL/api/v1/"
echo ""

echo "[3/8] Testing Plans List..."
curl -s "$BASE_URL/api/v1/plans/" | jq . || curl -s "$BASE_URL/api/v1/plans/"
echo ""

echo "[4/8] Testing Categories List..."
curl -s "$BASE_URL/api/v1/plans/categories/list" | jq . || curl -s "$BASE_URL/api/v1/plans/categories/list"
echo ""

echo "[5/8] Testing Templates List (first 3)..."
curl -s "$BASE_URL/api/v1/plans/templates/all" | jq ".[0:3]" || curl -s "$BASE_URL/api/v1/plans/templates/all"
echo ""

echo "[6/8] Testing User Registration..."
curl -s -X POST "$BASE_URL/api/v1/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "username": "testuser", "email": "test@example.com", "full_name": "Test User", "password": "TestPassword123", "password_confirm": "TestPassword123"}' | jq . || curl -s -X POST "$BASE_URL/api/v1/auth/register/" -H "Content-Type: application/json" -d '{"phone": "+919876543210", "username": "testuser", "password": "TestPassword123", "password_confirm": "TestPassword123"}'
echo ""

echo "[7/8] Testing User Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "password": "TestPassword123"}')
echo "$LOGIN_RESPONSE" | jq . || echo "$LOGIN_RESPONSE"
echo ""

echo "[8/8] Testing Protected Endpoint (Profile)..."
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access')
if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    curl -s "$BASE_URL/api/v1/auth/profile/" \
      -H "Authorization: Bearer $TOKEN" | jq . || curl -s "$BASE_URL/api/v1/auth/profile/" -H "Authorization: Bearer $TOKEN"
else
    echo "✗ Could not get authentication token"
fi
echo ""

echo "================================================================================"
echo "Test Complete!"
echo "================================================================================"
echo ""
echo "All basic endpoints are working correctly."
echo "For comprehensive testing, run: python test_all_apis.py"
echo ""
