#!/usr/bin/env python3
"""
Deployment script for Green Hydrogen Credit System smart contract.
"""

from brownie import GreenHydrogenCreditSystem, accounts, network, config
import json
import os

def main():
    """Deploy the GreenHydrogenCreditSystem contract."""
    
    # Get deployment account
    if network.show_active() in ['development', 'ganache-local']:
        # Use local account for development
        deployer = accounts[0]
        print(f"Deploying with local account: {deployer}")
    else:
        # Use account from environment or brownie accounts
        try:
            deployer = accounts.load('deployer')
        except:
            deployer = accounts[0]
        print(f"Deploying with account: {deployer}")
    
    print(f"Network: {network.show_active()}")
    print(f"Deployer balance: {deployer.balance() / 1e18} ETH")
    
    # Deploy the contract
    print("Deploying GreenHydrogenCreditSystem...")
    
    contract = GreenHydrogenCreditSystem.deploy(
        {'from': deployer},
        publish_source=False  # Set to True if you want to verify on Etherscan
    )
    
    print(f"Contract deployed at: {contract.address}")
    print(f"Transaction hash: {contract.tx.txid}")
    print(f"Gas used: {contract.tx.gas_used}")
    
    # Save deployment info
    deployment_info = {
        'contract_address': contract.address,
        'deployer': str(deployer),
        'network': network.show_active(),
        'transaction_hash': contract.tx.txid,
        'gas_used': contract.tx.gas_used,
        'block_number': contract.tx.block_number
    }
    
    # Create deployment info file
    os.makedirs('deployments', exist_ok=True)
    deployment_file = f"deployments/{network.show_active()}_deployment.json"
    
    with open(deployment_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    print(f"Deployment info saved to: {deployment_file}")
    
    # Register some initial accounts for testing
    if network.show_active() in ['development', 'ganache-local']:
        print("\nRegistering test accounts...")
        
        test_accounts = [
            (accounts[1], "alice"),
            (accounts[2], "bob"), 
            (accounts[3], "charlie"),
            (accounts[4], "system")
        ]
        
        for account, name in test_accounts:
            try:
                tx = contract.registerAccount(account, name, {'from': deployer})
                print(f"Registered {name} ({account}) - Gas used: {tx.gas_used}")
            except Exception as e:
                print(f"Failed to register {name}: {e}")
        
        # Issue some initial credits for testing
        print("\nIssuing initial credits...")
        try:
            tx = contract.issueCredits(accounts[1], 1000, "Initial credits for Alice", {'from': deployer})
            print(f"Issued 1000 credits to Alice - Gas used: {tx.gas_used}")
            
            tx = contract.issueCredits(accounts[2], 500, "Initial credits for Bob", {'from': deployer})
            print(f"Issued 500 credits to Bob - Gas used: {tx.gas_used}")
        except Exception as e:
            print(f"Failed to issue initial credits: {e}")
    
    print(f"\nDeployment complete!")
    print(f"Contract address: {contract.address}")
    
    return contract

if __name__ == "__main__":
    main()