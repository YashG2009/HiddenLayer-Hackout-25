#!/usr/bin/env python3
"""
Test script for Green Hydrogen Credit System smart contract.
Tests all major functionality including transfers, issuance, and account management.
"""

from brownie import GreenHydrogenCreditSystem, accounts, network
from brownie.exceptions import VirtualMachineError
import pytest

def test_contract_deployment():
    """Test contract deployment and initial state."""
    print("Testing contract deployment...")
    
    # Deploy contract
    contract = GreenHydrogenCreditSystem.deploy({'from': accounts[0]})
    
    # Check initial state
    owner, total_supply = contract.getContractInfo()
    assert owner == accounts[0]
    assert total_supply == 0
    
    print(f"✓ Contract deployed at: {contract.address}")
    print(f"✓ Owner: {owner}")
    print(f"✓ Initial total supply: {total_supply}")
    
    return contract

def test_account_registration(contract):
    """Test account registration functionality."""
    print("\nTesting account registration...")
    
    # Register test accounts
    test_accounts = [
        (accounts[1], "alice"),
        (accounts[2], "bob"),
        (accounts[3], "charlie")
    ]
    
    for account, name in test_accounts:
        tx = contract.registerAccount(account, name, {'from': accounts[0]})
        
        # Verify registration
        assert contract.getAddressByName(name) == account
        assert contract.getNameByAddress(account) == name
        
        print(f"✓ Registered {name} -> {account}")
    
    # Test duplicate registration (should fail)
    try:
        contract.registerAccount(accounts[4], "alice", {'from': accounts[0]})
        assert False, "Should have failed"
    except VirtualMachineError as e:
        assert "Name already taken" in str(e)
    
    print("✓ Duplicate name registration properly rejected")

def test_credit_issuance(contract):
    """Test credit issuance functionality."""
    print("\nTesting credit issuance...")
    
    # Issue credits to Alice
    tx = contract.issueCredits(accounts[1], 1000, "Initial credits", {'from': accounts[0]})
    
    # Verify balance
    balance = contract.getBalance(accounts[1])
    assert balance == 1000
    
    # Verify total supply
    _, total_supply = contract.getContractInfo()
    assert total_supply == 1000
    
    print(f"✓ Issued 1000 credits to Alice")
    print(f"✓ Alice's balance: {balance}")
    print(f"✓ Total supply: {total_supply}")
    
    # Issue more credits to Bob
    tx = contract.issueCredits(accounts[2], 500, "Initial credits", {'from': accounts[0]})
    
    balance_bob = contract.getBalance(accounts[2])
    assert balance_bob == 500
    
    print(f"✓ Issued 500 credits to Bob")

def test_credit_transfers(contract):
    """Test credit transfer functionality."""
    print("\nTesting credit transfers...")
    
    # Alice transfers 200 credits to Bob
    initial_alice = contract.getBalance(accounts[1])
    initial_bob = contract.getBalance(accounts[2])
    
    tx = contract.transferCredits(accounts[2], 200, "Test transfer", {'from': accounts[1]})
    
    # Verify balances
    final_alice = contract.getBalance(accounts[1])
    final_bob = contract.getBalance(accounts[2])
    
    assert final_alice == initial_alice - 200
    assert final_bob == initial_bob + 200
    
    print(f"✓ Alice transferred 200 credits to Bob")
    print(f"✓ Alice's balance: {initial_alice} -> {final_alice}")
    print(f"✓ Bob's balance: {initial_bob} -> {final_bob}")
    
    # Test insufficient balance (should fail)
    try:
        contract.transferCredits(accounts[2], 10000, "Too much", {'from': accounts[1]})
        assert False, "Should have failed"
    except VirtualMachineError as e:
        assert "Insufficient balance" in str(e)
    
    print("✓ Insufficient balance transfer properly rejected")

def test_account_freezing(contract):
    """Test account freezing functionality."""
    print("\nTesting account freezing...")
    
    # Freeze Alice's account
    tx = contract.setAccountFrozen(accounts[1], True, {'from': accounts[0]})
    
    # Verify account is frozen
    assert contract.isAccountFrozen(accounts[1]) == True
    
    print("✓ Alice's account frozen")
    
    # Try to transfer from frozen account (should fail)
    try:
        contract.transferCredits(accounts[2], 100, "Should fail", {'from': accounts[1]})
        assert False, "Should have failed"
    except VirtualMachineError as e:
        assert "Account is frozen" in str(e)
    
    print("✓ Transfer from frozen account properly rejected")
    
    # Try to transfer to frozen account (should fail)
    try:
        contract.transferCredits(accounts[1], 100, "Should fail", {'from': accounts[2]})
        assert False, "Should have failed"
    except VirtualMachineError as e:
        assert "Account is frozen" in str(e)
    
    print("✓ Transfer to frozen account properly rejected")
    
    # Unfreeze account
    tx = contract.setAccountFrozen(accounts[1], False, {'from': accounts[0]})
    assert contract.isAccountFrozen(accounts[1]) == False
    
    print("✓ Alice's account unfrozen")
    
    # Transfer should work now
    tx = contract.transferCredits(accounts[2], 50, "Should work", {'from': accounts[1]})
    print("✓ Transfer from unfrozen account successful")

def test_access_control(contract):
    """Test access control functionality."""
    print("\nTesting access control...")
    
    # Non-owner tries to issue credits (should fail)
    try:
        contract.issueCredits(accounts[1], 100, "Unauthorized", {'from': accounts[1]})
        assert False, "Should have failed"
    except VirtualMachineError as e:
        assert "Only owner can perform this action" in str(e)
    
    print("✓ Non-owner credit issuance properly rejected")
    
    # Non-owner tries to register account (should fail)
    try:
        contract.registerAccount(accounts[4], "unauthorized", {'from': accounts[1]})
        assert False, "Should have failed"
    except VirtualMachineError as e:
        assert "Only owner can perform this action" in str(e)
    
    print("✓ Non-owner account registration properly rejected")
    
    # Non-owner tries to freeze account (should fail)
    try:
        contract.setAccountFrozen(accounts[2], True, {'from': accounts[1]})
        assert False, "Should have failed"
    except VirtualMachineError as e:
        assert "Only owner can perform this action" in str(e)
    
    print("✓ Non-owner account freezing properly rejected")

def test_edge_cases(contract):
    """Test edge cases and validation."""
    print("\nTesting edge cases...")
    
    # Zero amount transfer (should fail)
    try:
        contract.transferCredits(accounts[2], 0, "Zero amount", {'from': accounts[1]})
        assert False, "Should have failed"
    except VirtualMachineError as e:
        assert "Amount must be greater than zero" in str(e)
    
    print("✓ Zero amount transfer properly rejected")
    
    # Transfer to self (should fail)
    try:
        contract.transferCredits(accounts[1], 100, "Self transfer", {'from': accounts[1]})
        assert False, "Should have failed"
    except VirtualMachineError as e:
        assert "Cannot transfer to self" in str(e)
    
    print("✓ Self transfer properly rejected")
    
    # Transfer to zero address (should fail)
    try:
        contract.transferCredits("0x0000000000000000000000000000000000000000", 100, "Zero address", {'from': accounts[1]})
        assert False, "Should have failed"
    except VirtualMachineError as e:
        assert "Cannot transfer to zero address" in str(e)
    
    print("✓ Transfer to zero address properly rejected")

def main():
    """Run all tests."""
    print("Starting Green Hydrogen Credit System contract tests...")
    print(f"Network: {network.show_active()}")
    print(f"Test accounts: {len(accounts)}")
    
    try:
        # Deploy and test contract
        contract = test_contract_deployment()
        test_account_registration(contract)
        test_credit_issuance(contract)
        test_credit_transfers(contract)
        test_account_freezing(contract)
        test_access_control(contract)
        test_edge_cases(contract)
        
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED!")
        print("="*50)
        
        # Print final state
        print(f"\nFinal contract state:")
        print(f"Contract address: {contract.address}")
        owner, total_supply = contract.getContractInfo()
        print(f"Owner: {owner}")
        print(f"Total supply: {total_supply}")
        
        for i in range(1, 4):
            name = contract.getNameByAddress(accounts[i])
            balance = contract.getBalance(accounts[i])
            frozen = contract.isAccountFrozen(accounts[i])
            print(f"{name} ({accounts[i]}): {balance} credits {'(FROZEN)' if frozen else ''}")
        
        return contract
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    main()