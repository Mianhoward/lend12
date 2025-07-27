#!/usr/bin/env python3
"""
Debug script to test specific failing endpoints
"""

import requests
import json

BACKEND_URL = "https://d0b710be-bfb3-458b-8e18-09800ef6f1f6.preview.emergentagent.com/api"

def test_lender_criteria_debug():
    # First register and login a lender
    lender_data = {
        "email": f"debug_lender@example.com",
        "password": "SecurePass456!",
        "name": "Debug Lender",
        "user_type": "lender"
    }
    
    # Register
    response = requests.post(f"{BACKEND_URL}/auth/register", json=lender_data)
    print(f"Register response: {response.status_code}")
    
    # Login
    login_data = {
        "email": lender_data["email"],
        "password": lender_data["password"],
        "user_type": "lender"
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    print(f"Login response: {response.status_code}")
    if response.status_code == 200:
        token = response.json()["session_token"]
        print(f"Got token: {token[:20]}...")
        
        # Test criteria creation
        criteria_data = {
            "loan_types": ["residential", "commercial"],
            "min_amount": 100000,
            "max_amount": 5000000,
            "regions": ["California", "New York"],
            "credit_score_min": 650,
            "ltv_max": 0.8
        }
        
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.post(f"{BACKEND_URL}/lender/criteria", json=criteria_data, headers=headers)
        print(f"Criteria creation response: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code != 200:
            print("Trying with different data structure...")
            # Maybe the issue is with the model validation
            print(f"Sent data: {json.dumps(criteria_data, indent=2)}")

if __name__ == "__main__":
    test_lender_criteria_debug()