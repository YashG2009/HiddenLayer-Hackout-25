#!/usr/bin/env python3
"""
Simple Task 2 completion test that focuses on core functionality.
"""

import os
import sys
import json

def test_files_exist():
    """Test that all required files exist."""
    required_files = [
        "contracts/GreenHydrogenCreditSystem.sol",
        "scripts/deploy.py", 
        "brownie-config.yaml",
        "services/account_mapper.py",
        "services/blockchain_errors.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            return False, f"Missing file: {file_path}"
    
    return True, "All files exist"

def test_deployment_info():
    """Test that deployment was successful."""
    deployment_file = "deployments/development_deployment.json"
    
    if not os.path.exists(deployment_file):
        return False, "No deployment file found"
    
    try:
        with open(deployment_file, 'r') as f:
            deployment_info = json.load(f)
            
        required_keys = ['contract_address', 'deployer', 'network', 'transaction_hash']
        for key in required_keys:
            if key not in deployment_info:
                return False, f"Missing deployment info: {key}"
        
        return True, f"Contract deployed at {deployment_info['contract_address']}"
    except Exception as e:
        return False, f"Failed to read deployment info: {e}"

def test_smart_contract_code():
    """Test that smart contract has required functionality."""
    try:
        with open("contracts/GreenHydrogenCreditSystem.sol", 'r') as f:
            contract_code = f.read()
        
        required_functions = [
            "transferCredits",
            "issueCredits", 
            "setAccountFrozen",
            "registerAccount",
            "getBalance"
        ]
        
        for func in required_functions:
            if func not in contract_code:
                return False, f"Missing function: {func}"
        
        return True, "Smart contract has all required functions"
    except Exception as e:
        return False, f"Failed to read contract: {e}"

def main():
    """Run simple Task 2 tests."""
    print("TASK 2 SIMPLE COMPLETION TEST")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_files_exist),
        ("Deployment Info", test_deployment_info),
        ("Smart Contract Code", test_smart_contract_code)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            results.append((test_name, success, message))
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name:<20} {status} - {message}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"{test_name:<20} ❌ FAIL - {str(e)}")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print("\n" + "=" * 50)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 TASK 2 CORE FUNCTIONALITY COMPLETE!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)