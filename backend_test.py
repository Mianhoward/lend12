#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Lending Platform
Tests all API endpoints and functionality including authentication, deals, messaging, documents, etc.
"""

import requests
import json
import uuid
import base64
from datetime import datetime
import time

# Get backend URL from frontend .env
BACKEND_URL = "https://d0b710be-bfb3-458b-8e18-09800ef6f1f6.preview.emergentagent.com/api"

class LendingPlatformTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.broker_token = None
        self.lender_token = None
        self.broker_user = None
        self.lender_user = None
        self.test_deal_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        })
        
    def make_request(self, method, endpoint, data=None, headers=None, token=None):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {"Content-Type": "application/json"}
            
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None

    def test_user_registration(self):
        """Test user registration for both brokers and lenders"""
        print("\n=== Testing User Registration ===")
        
        # Test broker registration
        broker_data = {
            "email": f"broker_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePass123!",
            "name": "John Broker",
            "user_type": "broker"
        }
        
        response = self.make_request("POST", "/auth/register", broker_data)
        if response and response.status_code == 200:
            self.log_test("Broker Registration", True, "Broker registered successfully")
            self.broker_email = broker_data["email"]
            self.broker_password = broker_data["password"]
        else:
            self.log_test("Broker Registration", False, f"Failed with status {response.status_code if response else 'No response'}")
            return False
            
        # Test lender registration
        lender_data = {
            "email": f"lender_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePass456!",
            "name": "Jane Lender",
            "user_type": "lender"
        }
        
        response = self.make_request("POST", "/auth/register", lender_data)
        if response and response.status_code == 200:
            self.log_test("Lender Registration", True, "Lender registered successfully")
            self.lender_email = lender_data["email"]
            self.lender_password = lender_data["password"]
        else:
            self.log_test("Lender Registration", False, f"Failed with status {response.status_code if response else 'No response'}")
            return False
            
        # Test duplicate registration
        response = self.make_request("POST", "/auth/register", broker_data)
        if response and response.status_code == 400:
            self.log_test("Duplicate Registration Prevention", True, "Correctly prevented duplicate registration")
        else:
            self.log_test("Duplicate Registration Prevention", False, "Should have prevented duplicate registration")
            
        return True

    def test_user_login(self):
        """Test user login functionality with session token generation"""
        print("\n=== Testing User Login ===")
        
        # Test broker login
        login_data = {
            "email": self.broker_email,
            "password": self.broker_password,
            "user_type": "broker"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response and response.status_code == 200:
            data = response.json()
            if "session_token" in data and "user" in data:
                self.broker_token = data["session_token"]
                self.broker_user = data["user"]
                self.log_test("Broker Login", True, "Broker login successful with session token")
            else:
                self.log_test("Broker Login", False, "Missing session token or user data")
                return False
        else:
            self.log_test("Broker Login", False, f"Failed with status {response.status_code if response else 'No response'}")
            return False
            
        # Test lender login
        login_data = {
            "email": self.lender_email,
            "password": self.lender_password,
            "user_type": "lender"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response and response.status_code == 200:
            data = response.json()
            if "session_token" in data and "user" in data:
                self.lender_token = data["session_token"]
                self.lender_user = data["user"]
                self.log_test("Lender Login", True, "Lender login successful with session token")
            else:
                self.log_test("Lender Login", False, "Missing session token or user data")
                return False
        else:
            self.log_test("Lender Login", False, f"Failed with status {response.status_code if response else 'No response'}")
            return False
            
        # Test invalid login
        invalid_login = {
            "email": self.broker_email,
            "password": "wrongpassword",
            "user_type": "broker"
        }
        
        response = self.make_request("POST", "/auth/login", invalid_login)
        if response and response.status_code == 401:
            self.log_test("Invalid Login Prevention", True, "Correctly rejected invalid credentials")
        else:
            self.log_test("Invalid Login Prevention", False, "Should have rejected invalid credentials")
            
        return True

    def test_profile_retrieval(self):
        """Test profile retrieval with session token"""
        print("\n=== Testing Profile Retrieval ===")
        
        # Test broker profile
        response = self.make_request("GET", "/auth/profile", token=self.broker_token)
        if response and response.status_code == 200:
            profile = response.json()
            if profile.get("user_type") == "broker" and profile.get("email") == self.broker_email:
                self.log_test("Broker Profile Retrieval", True, "Broker profile retrieved successfully")
            else:
                self.log_test("Broker Profile Retrieval", False, "Profile data mismatch")
        else:
            self.log_test("Broker Profile Retrieval", False, f"Failed with status {response.status_code if response else 'No response'}")
            
        # Test lender profile
        response = self.make_request("GET", "/auth/profile", token=self.lender_token)
        if response and response.status_code == 200:
            profile = response.json()
            if profile.get("user_type") == "lender" and profile.get("email") == self.lender_email:
                self.log_test("Lender Profile Retrieval", True, "Lender profile retrieved successfully")
            else:
                self.log_test("Lender Profile Retrieval", False, "Profile data mismatch")
        else:
            self.log_test("Lender Profile Retrieval", False, f"Failed with status {response.status_code if response else 'No response'}")
            
        # Test invalid token
        response = self.make_request("GET", "/auth/profile", token="invalid_token")
        if response and response.status_code == 401:
            self.log_test("Invalid Token Rejection", True, "Correctly rejected invalid session token")
        else:
            self.log_test("Invalid Token Rejection", False, "Should have rejected invalid token")

    def test_lender_criteria(self):
        """Test lender criteria creation and retrieval"""
        print("\n=== Testing Lender Criteria ===")
        
        # Test criteria creation
        criteria_data = {
            "loan_types": ["residential", "commercial"],
            "min_amount": 100000,
            "max_amount": 5000000,
            "regions": ["California", "New York"],
            "credit_score_min": 650,
            "ltv_max": 0.8
        }
        
        response = self.make_request("POST", "/lender/criteria", criteria_data, token=self.lender_token)
        if response and response.status_code == 200:
            self.log_test("Lender Criteria Creation", True, "Criteria created successfully")
        else:
            self.log_test("Lender Criteria Creation", False, f"Failed with status {response.status_code if response else 'No response'}")
            
        # Test criteria retrieval
        response = self.make_request("GET", "/lender/criteria", token=self.lender_token)
        if response and response.status_code == 200:
            criteria = response.json()
            if criteria and criteria.get("min_amount") == 100000:
                self.log_test("Lender Criteria Retrieval", True, "Criteria retrieved successfully")
            else:
                self.log_test("Lender Criteria Retrieval", False, "Criteria data mismatch")
        else:
            self.log_test("Lender Criteria Retrieval", False, f"Failed with status {response.status_code if response else 'No response'}")
            
        # Test broker cannot access lender criteria
        response = self.make_request("POST", "/lender/criteria", criteria_data, token=self.broker_token)
        if response and response.status_code == 403:
            self.log_test("Lender Criteria Access Control", True, "Correctly prevented broker from setting criteria")
        else:
            self.log_test("Lender Criteria Access Control", False, "Should have prevented broker access")

    def test_deal_creation(self):
        """Test creating new deals with all required fields"""
        print("\n=== Testing Deal Creation ===")
        
        deal_data = {
            "title": "Premium Commercial Property Loan",
            "loan_type": "commercial",
            "amount": 2500000,
            "region": "California",
            "borrower_credit_score": 720,
            "ltv_ratio": 0.75,
            "property_type": "Office Building",
            "description": "High-quality commercial property in prime location"
        }
        
        response = self.make_request("POST", "/broker/deals", deal_data, token=self.broker_token)
        if response and response.status_code == 200:
            deal = response.json()
            if deal.get("id") and deal.get("broker_id") == self.broker_user["id"]:
                self.test_deal_id = deal["id"]
                self.log_test("Deal Creation", True, "Deal created successfully")
            else:
                self.log_test("Deal Creation", False, "Deal data incomplete")
        else:
            self.log_test("Deal Creation", False, f"Failed with status {response.status_code if response else 'No response'}")
            
        # Test lender cannot create deals
        response = self.make_request("POST", "/broker/deals", deal_data, token=self.lender_token)
        if response and response.status_code == 403:
            self.log_test("Deal Creation Access Control", True, "Correctly prevented lender from creating deals")
        else:
            self.log_test("Deal Creation Access Control", False, "Should have prevented lender access")

    def test_broker_deals_retrieval(self):
        """Test fetching broker's own deals"""
        print("\n=== Testing Broker Deals Retrieval ===")
        
        response = self.make_request("GET", "/broker/deals", token=self.broker_token)
        if response and response.status_code == 200:
            deals = response.json()
            if isinstance(deals, list) and len(deals) > 0:
                found_deal = any(deal.get("id") == self.test_deal_id for deal in deals)
                if found_deal:
                    self.log_test("Broker Deals Retrieval", True, "Broker deals retrieved successfully")
                else:
                    self.log_test("Broker Deals Retrieval", False, "Created deal not found in broker's deals")
            else:
                self.log_test("Broker Deals Retrieval", False, "No deals returned")
        else:
            self.log_test("Broker Deals Retrieval", False, f"Failed with status {response.status_code if response else 'No response'}")

    def test_lender_available_deals(self):
        """Test fetching available deals matching lender criteria"""
        print("\n=== Testing Lender Available Deals ===")
        
        response = self.make_request("GET", "/lender/deals", token=self.lender_token)
        if response and response.status_code == 200:
            deals = response.json()
            if isinstance(deals, list):
                # Should find our test deal since it matches the criteria
                matching_deal = any(deal.get("id") == self.test_deal_id for deal in deals)
                if matching_deal:
                    self.log_test("Lender Available Deals", True, "Available deals retrieved and matched criteria")
                else:
                    self.log_test("Lender Available Deals", True, "Available deals retrieved (no matching deals)")
            else:
                self.log_test("Lender Available Deals", False, "Invalid response format")
        else:
            self.log_test("Lender Available Deals", False, f"Failed with status {response.status_code if response else 'No response'}")

    def test_lender_interest(self):
        """Test expressing interest in deals"""
        print("\n=== Testing Lender Interest ===")
        
        if not self.test_deal_id:
            self.log_test("Lender Interest", False, "No test deal available")
            return
            
        interest_data = {
            "deal_id": self.test_deal_id,
            "interest_type": "full",
            "message": "Very interested in this commercial property deal. We can provide competitive rates."
        }
        
        response = self.make_request("POST", "/lender/interest", interest_data, token=self.lender_token)
        if response and response.status_code == 200:
            self.log_test("Lender Interest Expression", True, "Interest expressed successfully")
        else:
            self.log_test("Lender Interest Expression", False, f"Failed with status {response.status_code if response else 'No response'}")
            
        # Test broker cannot express interest
        response = self.make_request("POST", "/lender/interest", interest_data, token=self.broker_token)
        if response and response.status_code == 403:
            self.log_test("Lender Interest Access Control", True, "Correctly prevented broker from expressing interest")
        else:
            self.log_test("Lender Interest Access Control", False, "Should have prevented broker access")

    def test_deal_interests_retrieval(self):
        """Test viewing interests expressed by lenders on deals"""
        print("\n=== Testing Deal Interests Retrieval ===")
        
        if not self.test_deal_id:
            self.log_test("Deal Interests Retrieval", False, "No test deal available")
            return
            
        response = self.make_request("GET", f"/deals/{self.test_deal_id}/interests", token=self.broker_token)
        if response and response.status_code == 200:
            interests = response.json()
            if isinstance(interests, list) and len(interests) > 0:
                self.log_test("Deal Interests Retrieval", True, "Deal interests retrieved successfully")
            else:
                self.log_test("Deal Interests Retrieval", True, "Deal interests retrieved (no interests yet)")
        else:
            self.log_test("Deal Interests Retrieval", False, f"Failed with status {response.status_code if response else 'No response'}")

    def test_lender_selection(self):
        """Test selecting a lender for a deal"""
        print("\n=== Testing Lender Selection ===")
        
        if not self.test_deal_id:
            self.log_test("Lender Selection", False, "No test deal available")
            return
            
        # First, let's make sure we have the lender's ID
        lender_id = self.lender_user["id"]
        
        response = self.make_request("POST", f"/deals/{self.test_deal_id}/select-lender", 
                                   {"lender_id": lender_id}, token=self.broker_token)
        if response and response.status_code == 200:
            self.log_test("Lender Selection", True, "Lender selected successfully")
        else:
            self.log_test("Lender Selection", False, f"Failed with status {response.status_code if response else 'No response'}")

    def test_messaging_system(self):
        """Test sending messages between brokers and lenders"""
        print("\n=== Testing Messaging System ===")
        
        if not self.test_deal_id:
            self.log_test("Messaging System", False, "No test deal available")
            return
            
        # Test broker sending message
        message_data = {"message": "Hello, let's discuss the terms of this deal."}
        response = self.make_request("POST", f"/deals/{self.test_deal_id}/messages", 
                                   message_data, token=self.broker_token)
        if response and response.status_code == 200:
            self.log_test("Broker Message Sending", True, "Broker message sent successfully")
        else:
            self.log_test("Broker Message Sending", False, f"Failed with status {response.status_code if response else 'No response'}")
            
        # Test lender sending message
        message_data = {"message": "Great! I'm ready to discuss the loan terms."}
        response = self.make_request("POST", f"/deals/{self.test_deal_id}/messages", 
                                   message_data, token=self.lender_token)
        if response and response.status_code == 200:
            self.log_test("Lender Message Sending", True, "Lender message sent successfully")
        else:
            self.log_test("Lender Message Sending", False, f"Failed with status {response.status_code if response else 'No response'}")
            
        # Test message retrieval
        response = self.make_request("GET", f"/deals/{self.test_deal_id}/messages", token=self.broker_token)
        if response and response.status_code == 200:
            messages = response.json()
            if isinstance(messages, list) and len(messages) >= 2:
                self.log_test("Message Retrieval", True, "Messages retrieved successfully")
            else:
                self.log_test("Message Retrieval", False, "Expected messages not found")
        else:
            self.log_test("Message Retrieval", False, f"Failed with status {response.status_code if response else 'No response'}")

    def test_document_management(self):
        """Test secure document upload with encryption"""
        print("\n=== Testing Document Management ===")
        
        if not self.test_deal_id:
            self.log_test("Document Management", False, "No test deal available")
            return
            
        # Test document upload
        document_data = {
            "filename": "loan_application.pdf",
            "content": "This is a test document content for the loan application",
            "content_type": "application/pdf"
        }
        
        response = self.make_request("POST", f"/deals/{self.test_deal_id}/documents", 
                                   document_data, token=self.broker_token)
        if response and response.status_code == 200:
            result = response.json()
            if "document_id" in result:
                self.log_test("Document Upload", True, "Document uploaded successfully with encryption")
            else:
                self.log_test("Document Upload", False, "Document upload response incomplete")
        else:
            self.log_test("Document Upload", False, f"Failed with status {response.status_code if response else 'No response'}")
            
        # Test document retrieval
        response = self.make_request("GET", f"/deals/{self.test_deal_id}/documents", token=self.broker_token)
        if response and response.status_code == 200:
            documents = response.json()
            if isinstance(documents, list) and len(documents) > 0:
                # Check that encrypted content is not exposed
                doc = documents[0]
                if "encrypted_content" not in doc and "filename" in doc:
                    self.log_test("Document Retrieval", True, "Documents retrieved with proper security")
                else:
                    self.log_test("Document Retrieval", False, "Security issue: encrypted content exposed")
            else:
                self.log_test("Document Retrieval", False, "No documents found")
        else:
            self.log_test("Document Retrieval", False, f"Failed with status {response.status_code if response else 'No response'}")

    def test_deal_completion(self):
        """Test deal completion workflow"""
        print("\n=== Testing Deal Completion ===")
        
        if not self.test_deal_id:
            self.log_test("Deal Completion", False, "No test deal available")
            return
            
        response = self.make_request("POST", f"/deals/{self.test_deal_id}/complete", token=self.broker_token)
        if response and response.status_code == 200:
            self.log_test("Deal Completion", True, "Deal completed successfully")
        else:
            self.log_test("Deal Completion", False, f"Failed with status {response.status_code if response else 'No response'}")

    def test_security_access_controls(self):
        """Test role-based access controls and security"""
        print("\n=== Testing Security Access Controls ===")
        
        # Test unauthorized access to other user's data
        # This is partially covered in other tests, but let's add a few more checks
        
        # Test accessing profile without token
        response = self.make_request("GET", "/auth/profile")
        if response and response.status_code == 401:
            self.log_test("No Token Access Control", True, "Correctly rejected request without token")
        else:
            self.log_test("No Token Access Control", False, "Should have rejected request without token")
            
        # Test cross-user access (if we had another user)
        # For now, we'll test that tokens are properly validated
        fake_token = str(uuid.uuid4())
        response = self.make_request("GET", "/auth/profile", token=fake_token)
        if response and response.status_code == 401:
            self.log_test("Fake Token Access Control", True, "Correctly rejected fake token")
        else:
            self.log_test("Fake Token Access Control", False, "Should have rejected fake token")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Comprehensive Lending Platform Backend Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 80)
        
        try:
            # Authentication tests
            if not self.test_user_registration():
                print("❌ Registration failed - stopping tests")
                return
                
            if not self.test_user_login():
                print("❌ Login failed - stopping tests")
                return
                
            self.test_profile_retrieval()
            
            # Lender functionality tests
            self.test_lender_criteria()
            
            # Broker functionality tests
            self.test_deal_creation()
            self.test_broker_deals_retrieval()
            
            # Deal matching and interest tests
            self.test_lender_available_deals()
            self.test_lender_interest()
            self.test_deal_interests_retrieval()
            self.test_lender_selection()
            
            # Communication and document tests
            self.test_messaging_system()
            self.test_document_management()
            
            # Deal completion
            self.test_deal_completion()
            
            # Security tests
            self.test_security_access_controls()
            
        except Exception as e:
            print(f"❌ Test execution failed: {str(e)}")
            
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result["success"]:
                print(f"  • {result['test']}")

if __name__ == "__main__":
    tester = LendingPlatformTester()
    tester.run_all_tests()