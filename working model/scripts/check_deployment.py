#!/usr/bin/env python3
"""
Check if contract is properly deployed and accessible.
"""

import json
import os
from brownie import network, accounts, Contract

def main():
    """Check deployment status."""
    print("Checking contract deployment...")
    
    # Connect to network
    if not network.is_connected():
        network.connect('development')
    
    print(f"Connected to network: {network.show_active()}")
    
    # Check deployment file
    deployment_file = f"deployments/{network.show_active()}_deployment.json"
    
    if os.path.exists(deployment_file):
        with open(deployment_file, 'r') as f:
            deployment_info = json.load(f)
            print(f"Deployment file found: {deployment_file}")
            print(f"Contract address: {deployment_info['contract_address']}")
            
            # Try to load contract
            try:
                from brownie import GreenHydrogenCreditSystem
                contract = GreenHydrogenCreditSystem.at(deployment_info['contract_address'])
                print(f"✓ Contract loaded successfully")
                
                # Test basic functionality
                owner, total_supply = contract.getContractInfo()
                print(f"✓ Contract owner: {owner}")
                print(f"✓ Total supply: {total_supply}")
                
                return contract
                
            except Exception as e:
                print(f"✗ Failed to load contract: {e}")
                return None
    else:
        print(f"✗ Deployment file not found: {deployment_file}")
        print("Run 'brownie run deploy' first")
        return None

if __name__ == "__main__":
    main()