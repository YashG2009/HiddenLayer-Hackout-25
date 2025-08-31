#!/usr/bin/env python3
"""
Test script for blockchain adapter integration with deployed smart contract.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.blockchain_service import blockchain_adapter
from services.account_mapper import account_mapper
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_blockchain_adapter():
    """Test the blockchain adapter with deployed contract."""
    print("Testing Blockchain Adapter Integration")
    print("=" * 50)
    
    # Check adapter initialization
    print(f"Backend type: {blockchain_adapter.get_backend_type()}")
    print(f"Brownie available: {blockchain_adapter.is_brownie_available()}")
    
    if blockchain_adapter.get_initialization_error():
        print(f"Initialization error: {blockchain_adapter.get_initialization_error()}")
    
    # Test chain info
    print("\n1. Testing chain info...")
    chain_info = blockchain_adapter.get_chain_info()
    print(f"Chain info: {chain_info}")
    
    # Test account registration
    print("\n2. Testing account registration...")
    success = blockchain_adapter.register_account("test_user", None)
    print(f"Account registration successful: {success}")
    
    # Test account mappings
    print("\n3. Testing account mappings...")
    mappings = account_mapper.get_all_mappings()
    print(f"Current mappings: {mappings}")
    
    # Test balance queries
    print("\n4. Testing balance queries...")
    for username in ["alice", "bob", "charlie"]:
        balance = blockchain_adapter.get_balance(username)
        print(f"{username} balance: {balance}")
    
    # Test credit issuance
    print("\n5. Testing credit issuance...")
    if "test_user" in account_mapper.get_all_usernames():
        success = blockchain_adapter.issue_credits("test_user", 100, "Test issuance")
        print(f"Credit issuance successful: {success}")
        
        if success:
            balance = blockchain_adapter.get_balance("test_user")
            print(f"test_user balance after issuance: {balance}")
    
    # Test transaction history
    print("\n6. Testing transaction history...")
    for username in ["alice", "bob"]:
        transactions = blockchain_adapter.get_user_transactions(username, 5)
        print(f"{username} transactions: {len(transactions)}")
        for tx in transactions[:2]:  # Show first 2 transactions
            print(f"  - {tx['sender']} -> {tx['recipient']}: {tx['amount']} ({tx['details']})")
    
    print("\n" + "=" * 50)
    print("✅ Blockchain Adapter Test Complete!")

if __name__ == "__main__":
    test_blockchain_adapter()