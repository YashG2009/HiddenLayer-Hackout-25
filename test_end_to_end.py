#!/usr/bin/env python3
"""
End-to-end test of blockchain integration functionality.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_end_to_end():
    """Test end-to-end blockchain functionality."""
    try:
        from services.blockchain_service import blockchain_adapter
        from services.ai_service import ai_service
        
        print("🚀 Starting End-to-End Blockchain Test")
        print("="*50)
        
        # Test 1: Blockchain adapter initialization
        print(f"Backend Type: {blockchain_adapter.get_backend_type()}")
        print(f"Brownie Available: {blockchain_adapter.is_brownie_available()}")
        
        # Test 2: User registration
        test_users = ["Alice", "Bob", "Charlie"]
        print(f"\n📝 Registering {len(test_users)} test users...")
        
        for user in test_users:
            result = blockchain_adapter.register_account(user)
            print(f"   {user}: {'✅' if result else '❌'}")
        
        # Test 3: Credit issuance
        print(f"\n💰 Issuing credits...")
        issue_result = blockchain_adapter.issue_credits("Alice", 1000, "Initial credits")
        print(f"   Issue 1000 credits to Alice: {'✅' if issue_result else '❌'}")
        
        # Test 4: Balance checking
        print(f"\n💳 Checking balances...")
        for user in test_users:
            balance = blockchain_adapter.get_balance(user)
            print(f"   {user}: {balance} GHC")
        
        # Test 5: Credit transfer
        print(f"\n🔄 Testing credit transfer...")
        try:
            blockchain_adapter.add_transaction("Alice", "Bob", 250, "Test transfer")
            print("   Transfer Alice -> Bob (250 GHC): ✅")
        except Exception as e:
            print(f"   Transfer Alice -> Bob (250 GHC): ❌ ({e})")
        
        # Test 6: Updated balances
        print(f"\n💳 Updated balances...")
        for user in test_users:
            balance = blockchain_adapter.get_balance(user)
            print(f"   {user}: {balance} GHC")
        
        # Test 7: Transaction history
        print(f"\n📊 Transaction history for Alice...")
        transactions = blockchain_adapter.get_user_transactions("Alice", 5)
        print(f"   Found {len(transactions)} transactions")
        for i, tx in enumerate(transactions[:3]):
            print(f"   {i+1}. {tx['sender']} -> {tx['recipient']}: {tx['amount']} GHC")
        
        # Test 8: AI Service integration
        print(f"\n🤖 AI Service integration...")
        if ai_service.is_available():
            try:
                analysis = ai_service.get_risk_analysis(
                    producer_name="Alice",
                    capacity=1000,
                    pending_amount=500,
                    transaction_history=transactions
                )
                print(f"   AI Analysis: ✅")
                print(f"   Risk Score: {analysis.get('risk_score', 'N/A')}")
                print(f"   Assessment: {analysis.get('assessment', 'N/A')}")
            except Exception as e:
                print(f"   AI Analysis: ❌ ({e})")
        else:
            print(f"   AI Service: ❌ (Not available)")
        
        # Test 9: Chain information
        print(f"\n⛓️  Blockchain information...")
        chain_info = blockchain_adapter.get_chain_info()
        if 'backend' in chain_info:
            print(f"   Backend: {chain_info['backend']}")
        if 'length' in chain_info:
            print(f"   Chain Length: {chain_info['length']} blocks")
        if 'latest_block' in chain_info:
            print(f"   Latest Block: #{chain_info['latest_block'].get('index', 'N/A')}")
        
        print("\n" + "="*50)
        print("🎉 End-to-End Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ End-to-End Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_end_to_end()
    sys.exit(0 if success else 1)