#!/usr/bin/env python3
"""
Comprehensive test for Task 2 completion.
Tests all implemented functionality:
1. Smart contract deployment and functionality
2. Brownie integration
3. Blockchain adapter implementation
4. Account mapping system
5. Error handling
"""

import sys
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_smart_contract():
    """Test smart contract deployment and basic functionality."""
    print("=" * 60)
    print("TESTING SMART CONTRACT FUNCTIONALITY")
    print("=" * 60)
    
    try:
        from brownie import GreenHydrogenCreditSystem, accounts, network
        
        # Connect to development network
        if not network.is_connected():
            network.connect('development')
        
        print(f"✓ Connected to network: {network.show_active()}")
        
        # Deploy contract
        contract = GreenHydrogenCreditSystem.deploy({'from': accounts[0]})
        print(f"✓ Contract deployed at: {contract.address}")
        
        # Test basic functionality
        owner, total_supply = contract.getContractInfo()
        assert owner == accounts[0]
        assert total_supply == 0
        print(f"✓ Contract owner: {owner}")
        print(f"✓ Initial total supply: {total_supply}")
        
        # Test account registration
        contract.registerAccount(accounts[1], "alice", {'from': accounts[0]})
        assert contract.getAddressByName("alice") == accounts[1]
        assert contract.getNameByAddress(accounts[1]) == "alice"
        print("✓ Account registration works")
        
        # Test credit issuance
        contract.issueCredits(accounts[1], 1000, "Test credits", {'from': accounts[0]})
        balance = contract.getBalance(accounts[1])
        assert balance == 1000
        print("✓ Credit issuance works")
        
        # Test transfers
        contract.registerAccount(accounts[2], "bob", {'from': accounts[0]})
        contract.transferCredits(accounts[2], 200, "Test transfer", {'from': accounts[1]})
        
        alice_balance = contract.getBalance(accounts[1])
        bob_balance = contract.getBalance(accounts[2])
        assert alice_balance == 800
        assert bob_balance == 200
        print("✓ Credit transfers work")
        
        # Test account freezing
        contract.setAccountFrozen(accounts[1], True, {'from': accounts[0]})
        assert contract.isAccountFrozen(accounts[1]) == True
        print("✓ Account freezing works")
        
        contract.setAccountFrozen(accounts[1], False, {'from': accounts[0]})
        assert contract.isAccountFrozen(accounts[1]) == False
        print("✓ Account unfreezing works")
        
        print("✅ Smart contract tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Smart contract tests FAILED: {e}")
        return False

def test_brownie_integration():
    """Test Brownie framework integration."""
    print("\n" + "=" * 60)
    print("TESTING BROWNIE INTEGRATION")
    print("=" * 60)
    
    try:
        from brownie import network, accounts, project
        
        print(f"✓ Brownie framework imported successfully")
        print(f"✓ Network: {network.show_active()}")
        print(f"✓ Available accounts: {len(accounts)}")
        
        # Test project structure
        assert os.path.exists("contracts/GreenHydrogenCreditSystem.sol")
        assert os.path.exists("scripts/deploy.py")
        assert os.path.exists("brownie-config.yaml")
        print("✓ Brownie project structure exists")
        
        # Test deployment info
        deployment_file = f"deployments/{network.show_active()}_deployment.json"
        assert os.path.exists(deployment_file)
        
        with open(deployment_file, 'r') as f:
            deployment_info = json.load(f)
            assert 'contract_address' in deployment_info
            assert 'deployer' in deployment_info
            assert 'network' in deployment_info
        print("✓ Deployment information saved correctly")
        
        print("✅ Brownie integration tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Brownie integration tests FAILED: {e}")
        return False

def test_blockchain_adapter():
    """Test blockchain adapter implementation."""
    print("\n" + "=" * 60)
    print("TESTING BLOCKCHAIN ADAPTER")
    print("=" * 60)
    
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from services.blockchain_service import blockchain_adapter
        from config import config
        
        # Test configuration
        assert config.is_brownie_enabled() == True
        print("✓ Brownie enabled in configuration")
        
        # Test adapter initialization
        print(f"✓ Backend type: {blockchain_adapter.get_backend_type()}")
        print(f"✓ Brownie available: {blockchain_adapter.is_brownie_available()}")
        
        if blockchain_adapter.get_initialization_error():
            print(f"⚠ Initialization note: {blockchain_adapter.get_initialization_error()}")
        
        # Test chain info
        chain_info = blockchain_adapter.get_chain_info()
        assert 'backend' in chain_info
        print("✓ Chain info retrieval works")
        
        print("✅ Blockchain adapter tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Blockchain adapter tests FAILED: {e}")
        return False

def test_account_mapping():
    """Test account mapping system."""
    print("\n" + "=" * 60)
    print("TESTING ACCOUNT MAPPING SYSTEM")
    print("=" * 60)
    
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from services.account_mapper import AccountMapper
        
        # Create test mapper
        mapper = AccountMapper("test_mappings.json")
        
        # Test registration
        success = mapper.register_account("test_user", "0x1234567890123456789012345678901234567890")
        assert success == True
        print("✓ Account registration works")
        
        # Test lookup
        address = mapper.get_address_by_username("test_user")
        assert address == "0x1234567890123456789012345678901234567890"
        print("✓ Username to address lookup works")
        
        username = mapper.get_username_by_address("0x1234567890123456789012345678901234567890")
        assert username == "test_user"
        print("✓ Address to username lookup works")
        
        # Test validation
        assert mapper.validate_address("0x1234567890123456789012345678901234567890") == True
        assert mapper.validate_address("invalid") == False
        print("✓ Address validation works")
        
        # Clean up
        if os.path.exists("test_mappings.json"):
            os.remove("test_mappings.json")
        
        print("✅ Account mapping tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Account mapping tests FAILED: {e}")
        return False

def test_error_handling():
    """Test error handling system."""
    print("\n" + "=" * 60)
    print("TESTING ERROR HANDLING")
    print("=" * 60)
    
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from services.blockchain_errors import (
            BlockchainErrorHandler, 
            NetworkError, 
            TransactionError,
            BlockchainErrorType
        )
        
        # Test error handler
        handler = BlockchainErrorHandler()
        
        # Test error classification
        network_error = handler.handle_error(Exception("Connection timeout"), "test_operation")
        assert network_error.error_type == BlockchainErrorType.NETWORK_ERROR
        print("✓ Network error classification works")
        
        # Test user-friendly messages
        message = handler.get_user_friendly_message(network_error)
        assert "Network connection issue" in message
        print("✓ User-friendly error messages work")
        
        # Test retryable error detection
        retryable = handler._is_retryable_error(Exception("timeout"))
        assert retryable == True
        print("✓ Retryable error detection works")
        
        non_retryable = handler._is_retryable_error(Exception("invalid input"))
        assert non_retryable == False
        print("✓ Non-retryable error detection works")
        
        print("✅ Error handling tests PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Error handling tests FAILED: {e}")
        return False

def test_file_structure():
    """Test that all required files are created."""
    print("\n" + "=" * 60)
    print("TESTING FILE STRUCTURE")
    print("=" * 60)
    
    required_files = [
        "contracts/GreenHydrogenCreditSystem.sol",
        "scripts/deploy.py",
        "scripts/simple_test.py",
        "brownie-config.yaml",
        "services/account_mapper.py",
        "services/blockchain_errors.py",
        "services/blockchain_service.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True

def main():
    """Run all tests."""
    print("TASK 2 COMPLETION TEST")
    print("Develop and deploy smart contract with Brownie integration")
    print("=" * 80)
    
    test_results = []
    
    # Run all tests
    test_results.append(("File Structure", test_file_structure()))
    test_results.append(("Smart Contract", test_smart_contract()))
    test_results.append(("Brownie Integration", test_brownie_integration()))
    test_results.append(("Blockchain Adapter", test_blockchain_adapter()))
    test_results.append(("Account Mapping", test_account_mapping()))
    test_results.append(("Error Handling", test_error_handling()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 TASK 2 COMPLETED SUCCESSFULLY!")
        print("\nImplemented features:")
        print("✓ Solidity smart contract with transfer, issuance, and freeze functionality")
        print("✓ Brownie project structure and deployment scripts")
        print("✓ Blockchain adapter class interfacing with deployed smart contract")
        print("✓ Account mapping system for username ↔ Ethereum address conversion")
        print("✓ Comprehensive error handling for blockchain operations")
        print("✓ Gas estimation and transaction retry logic")
        print("✓ Network failure and connection error handling")
        
        return True
    else:
        print(f"\n❌ TASK 2 INCOMPLETE - {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)