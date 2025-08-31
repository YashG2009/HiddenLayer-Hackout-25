#!/usr/bin/env python3
"""
Simple test script for Green Hydrogen Credit System smart contract.
Tests basic functionality without complex error handling.
"""

from brownie import GreenHydrogenCreditSystem, accounts, network

def main():
    """Run basic contract tests."""
    print("Starting Green Hydrogen Credit System basic tests...")
    print(f"Network: {network.show_active()}")
    print(f"Test accounts: {len(accounts)}")
    
    # Deploy contract
    print("\n1. Deploying contract...")
    contract = GreenHydrogenCreditSystem.deploy({'from': accounts[0]})
    print(f"✓ Contract deployed at: {contract.address}")
    
    # Check initial state
    owner, total_supply = contract.getContractInfo()
    print(f"✓ Owner: {owner}")
    print(f"✓ Initial total supply: {total_supply}")
    
    # Register accounts
    print("\n2. Registering accounts...")
    test_accounts = [
        (accounts[1], "alice"),
        (accounts[2], "bob"),
        (accounts[3], "charlie")
    ]
    
    for account, name in test_accounts:
        tx = contract.registerAccount(account, name, {'from': accounts[0]})
        print(f"✓ Registered {name} -> {account}")
        
        # Verify registration
        assert contract.getAddressByName(name) == account
        assert contract.getNameByAddress(account) == name
    
    # Issue credits
    print("\n3. Issuing credits...")
    tx = contract.issueCredits(accounts[1], 1000, "Initial credits for Alice", {'from': accounts[0]})
    print(f"✓ Issued 1000 credits to Alice")
    
    tx = contract.issueCredits(accounts[2], 500, "Initial credits for Bob", {'from': accounts[0]})
    print(f"✓ Issued 500 credits to Bob")
    
    # Check balances
    alice_balance = contract.getBalance(accounts[1])
    bob_balance = contract.getBalance(accounts[2])
    print(f"✓ Alice's balance: {alice_balance}")
    print(f"✓ Bob's balance: {bob_balance}")
    
    # Transfer credits
    print("\n4. Testing transfers...")
    initial_alice = contract.getBalance(accounts[1])
    initial_bob = contract.getBalance(accounts[2])
    
    tx = contract.transferCredits(accounts[2], 200, "Test transfer", {'from': accounts[1]})
    print(f"✓ Alice transferred 200 credits to Bob")
    
    final_alice = contract.getBalance(accounts[1])
    final_bob = contract.getBalance(accounts[2])
    
    print(f"✓ Alice's balance: {initial_alice} -> {final_alice}")
    print(f"✓ Bob's balance: {initial_bob} -> {final_bob}")
    
    assert final_alice == initial_alice - 200
    assert final_bob == initial_bob + 200
    
    # Test account freezing
    print("\n5. Testing account freezing...")
    
    # Freeze Alice's account
    tx = contract.setAccountFrozen(accounts[1], True, {'from': accounts[0]})
    print("✓ Alice's account frozen")
    
    # Verify account is frozen
    assert contract.isAccountFrozen(accounts[1]) == True
    
    # Unfreeze account
    tx = contract.setAccountFrozen(accounts[1], False, {'from': accounts[0]})
    print("✓ Alice's account unfrozen")
    
    assert contract.isAccountFrozen(accounts[1]) == False
    
    # Final state
    print("\n" + "="*50)
    print("✅ ALL BASIC TESTS PASSED!")
    print("="*50)
    
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

if __name__ == "__main__":
    main()