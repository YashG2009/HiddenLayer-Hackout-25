#!/usr/bin/env python3
"""
Complete system test to verify all functionality works properly.
Tests AI, blockchain, and Flask integration thoroughly.
"""

import sys
import os
import json
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ai_service():
    """Test AI service functionality."""
    print("🤖 Testing AI Service...")
    
    try:
        from services.ai_service import ai_service
        
        if not ai_service.is_available():
            print(f"   ❌ AI Service not available: {ai_service.get_initialization_error()}")
            return False
        
        # Test AI analysis
        result = ai_service.get_risk_analysis(
            producer_name="TestProducer",
            capacity=1000,
            pending_amount=500,
            transaction_history=[
                {"amount": 100, "timestamp": "2024-01-01", "sender": "system", "recipient": "TestProducer"}
            ]
        )
        
        if "error" in result:
            print(f"   ❌ AI Analysis failed: {result['error']}")
            return False
        
        print("   ✅ AI Service working correctly")
        print(f"   📊 Risk Score: {result.get('risk_score', 'N/A')}")
        print(f"   📋 Assessment: {result.get('assessment', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"   ❌ AI Service test failed: {e}")
        return False

def test_blockchain_service():
    """Test blockchain service functionality."""
    print("⛓️  Testing Blockchain Service...")
    
    try:
        from services.blockchain_service import blockchain_adapter
        
        # Test initialization
        backend = blockchain_adapter.get_backend_type()
        print(f"   🔗 Backend: {backend}")
        
        # Test account registration
        result = blockchain_adapter.register_account("TestUser123")
        if not result:
            print("   ❌ Account registration failed")
            return False
        print("   ✅ Account registration working")
        
        # Test credit issuance
        result = blockchain_adapter.issue_credits("TestUser123", 500, "Test issuance")
        if not result:
            print("   ❌ Credit issuance failed")
            return False
        print("   ✅ Credit issuance working")
        
        # Test balance checking
        balance = blockchain_adapter.get_balance("TestUser123")
        print(f"   💰 Balance: {balance} GHC")
        
        # Test transaction history
        transactions = blockchain_adapter.get_user_transactions("TestUser123", 5)
        print(f"   📊 Transactions: {len(transactions)} found")
        
        # Test chain info
        chain_info = blockchain_adapter.get_chain_info()
        print(f"   📦 Chain Length: {chain_info.get('length', 0)} blocks")
        
        print("   ✅ Blockchain service working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Blockchain service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_integration():
    """Test Flask application integration."""
    print("🌐 Testing Flask Integration...")
    
    try:
        from proto_v3_migrated import app, load_data
        
        # Load data
        load_data()
        print("   ✅ Data loading working")
        
        # Test Flask app
        app.config['TESTING'] = True
        client = app.test_client()
        
        # Test login page
        response = client.get('/login')
        if response.status_code != 200:
            print(f"   ❌ Login page failed: {response.status_code}")
            return False
        print("   ✅ Login page working")
        
        # Test AI analysis endpoint
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'StatePollGujarat'
            sess['role'] = 'State Poll'
        
        # Create test data for AI analysis
        from proto_v3_migrated import APP_DATA
        APP_DATA['users']['TestProducer'] = {
            'name': 'TestProducer',
            'role': 'Producer',
            'capacity': 1000
        }
        APP_DATA['pending_issuances']['TEST-001'] = {
            'producer_name': 'TestProducer',
            'amount': 500,
            'status': 'Pending Verification'
        }
        
        response = client.post('/ai-analyze', 
                             json={
                                 'producer_name': 'TestProducer',
                                 'issuance_id': 'TEST-001'
                             },
                             content_type='application/json')
        
        if response.status_code != 200:
            print(f"   ❌ AI analysis endpoint failed: {response.status_code}")
            print(f"   Response: {response.data}")
            return False
        
        ai_result = json.loads(response.data)
        if "error" in ai_result:
            print(f"   ⚠️  AI analysis returned error: {ai_result['error']}")
        else:
            print("   ✅ AI analysis endpoint working")
        
        # Test service status endpoint
        with client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'GovtAdmin'
            sess['role'] = 'Government'
        
        response = client.get('/service-status')
        if response.status_code != 200:
            print(f"   ❌ Service status endpoint failed: {response.status_code}")
            return False
        
        status_data = json.loads(response.data)
        print(f"   📊 AI Available: {status_data['ai_service']['available']}")
        print(f"   📊 Blockchain Backend: {status_data['blockchain_service']['backend']}")
        
        print("   ✅ Flask integration working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Flask integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_end_to_end_workflow():
    """Test complete end-to-end workflow."""
    print("🔄 Testing End-to-End Workflow...")
    
    try:
        from services.blockchain_service import blockchain_adapter
        from proto_v3_migrated import app, APP_DATA, load_data
        
        # Initialize
        load_data()
        
        # Register users
        users = ["Producer1", "Factory1", "Admin1"]
        for user in users:
            blockchain_adapter.register_account(user)
        
        # Issue credits
        blockchain_adapter.issue_credits("Producer1", 1000, "Initial allocation")
        
        # Transfer credits
        blockchain_adapter.add_transaction("Producer1", "Factory1", 250, "Credit sale")
        
        # Check balances
        producer_balance = blockchain_adapter.get_balance("Producer1")
        factory_balance = blockchain_adapter.get_balance("Factory1")
        
        print(f"   💰 Producer1 Balance: {producer_balance} GHC")
        print(f"   💰 Factory1 Balance: {factory_balance} GHC")
        
        if producer_balance == 750 and factory_balance == 250:
            print("   ✅ End-to-end workflow working correctly")
            return True
        else:
            print("   ❌ Balance calculations incorrect")
            return False
        
    except Exception as e:
        print(f"   ❌ End-to-end workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 GHCS Complete System Test")
    print("=" * 50)
    
    tests = [
        ("AI Service", test_ai_service),
        ("Blockchain Service", test_blockchain_service),
        ("Flask Integration", test_flask_integration),
        ("End-to-End Workflow", test_end_to_end_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} Test:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} | {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)