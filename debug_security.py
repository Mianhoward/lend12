#!/usr/bin/env python3
"""
Debug specific failing tests
"""

import requests
import json

BACKEND_URL = "https://d0b710be-bfb3-458b-8e18-09800ef6f1f6.preview.emergentagent.com/api"

def test_specific_issues():
    # Test 1: Duplicate registration
    print("=== Testing Duplicate Registration ===")
    user_data = {
        "email": "test_duplicate@example.com",
        "password": "SecurePass123!",
        "name": "Test User",
        "user_type": "broker"
    }
    
    # First registration
    response1 = requests.post(f"{BACKEND_URL}/auth/register", json=user_data)
    print(f"First registration: {response1.status_code}")
    
    # Duplicate registration
    response2 = requests.post(f"{BACKEND_URL}/auth/register", json=user_data)
    print(f"Duplicate registration: {response2.status_code}")
    print(f"Response text: {response2.text}")
    
    # Test 2: Invalid login
    print("\n=== Testing Invalid Login ===")
    invalid_login = {
        "email": user_data["email"],
        "password": "wrongpassword",
        "user_type": "broker"
    }
    
    response3 = requests.post(f"{BACKEND_URL}/auth/login", json=invalid_login)
    print(f"Invalid login: {response3.status_code}")
    print(f"Response text: {response3.text}")
    
    # Test 3: Invalid token
    print("\n=== Testing Invalid Token ===")
    headers = {"Authorization": "Bearer invalid_token_12345"}
    response4 = requests.get(f"{BACKEND_URL}/auth/profile", headers=headers)
    print(f"Invalid token: {response4.status_code}")
    print(f"Response text: {response4.text}")
    
    # Test 4: No token
    print("\n=== Testing No Token ===")
    response5 = requests.get(f"{BACKEND_URL}/auth/profile")
    print(f"No token: {response5.status_code}")
    print(f"Response text: {response5.text}")

if __name__ == "__main__":
    test_specific_issues()