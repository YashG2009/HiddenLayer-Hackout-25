#!/usr/bin/env python3
"""
Auto-deployment script for GHCS smart contract.
Ensures contract is always deployed and available.
"""

import json
import os
import logging
from brownie import accounts, network, GreenHydrogenCreditSystem, Contract

logger = logging.getLogger(__name__)

def deploy_contract():
    """Deploy the GHCS smart contract."""
    try:
        logger.info("🚀 ETHEREUM DEPLOYMENT: Starting smart contract deployment")
        
        # Get deployer account
        deployer = accounts[0]
        logger.info(f"🔐 Deployer Account: {deployer.address}")
        logger.info(f"💰 Account Balance: {deployer.balance() / 1e18:.4f} ETH")
        
        # Deploy contract
        logger.info("📝 Compiling smart contract...")
        contract = GreenHydrogenCreditSystem.deploy({'from': deployer})
        
        logger.info("⛓️  SMART CONTRACT DEPLOYED SUCCESSFULLY!")
        logger.info(f"📍 Contract Address: {contract.address}")
        logger.info(f"🔗 Transaction Hash: {contract.tx.txid}")
        logger.info(f"⛽ Gas Used: {contract.tx.gas_used:,}")
        logger.info(f"📦 Block Number: {contract.tx.block_number}")
        
        # Save deployment info
        deployment_info = {
            'contract_address': contract.address,
            'deployer': str(deployer.address),
            'network': network.show_active(),
            'transaction_hash': contract.tx.txid,
            'gas_used': contract.tx.gas_used,
            'block_number': contract.tx.block_number,
            'deployment_timestamp': contract.tx.timestamp
        }
        
        os.makedirs('deployments', exist_ok=True)
        deployment_file = f"deployments/{network.show_active()}_deployment.json"
        
        with open(deployment_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        logger.info(f"💾 Deployment info saved to: {deployment_file}")
        
        # Initialize contract with test data
        initialize_contract(contract, deployer)
        
        return contract
        
    except Exception as e:
        logger.error(f"❌ DEPLOYMENT FAILED: {e}")
        raise

def initialize_contract(contract, deployer):
    """Initialize contract with test accounts and data."""
    try:
        logger.info("🔧 INITIALIZING CONTRACT: Setting up test accounts")
        
        # Register test accounts
        test_accounts = [
            (accounts[1], "SomnathProducers"),
            (accounts[2], "Ammonia Factory"),
            (accounts[3], "GovtAdmin"),
            (accounts[4], "StatePollGujarat"),
            (accounts[5], "CitizenOne")
        ]
        
        for account, name in test_accounts:
            try:
                tx = contract.registerAccount(account.address, name, {'from': deployer})
                logger.info(f"✅ Registered: {name} ({account.address})")
                logger.info(f"   TX Hash: {tx.txid}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to register {name}: {e}")
        
        # Issue initial credits
        try:
            tx = contract.issueCredits(
                accounts[1].address, 
                1000, 
                "Initial credit allocation", 
                {'from': deployer}
            )
            logger.info("💰 INITIAL CREDITS: 1000 GHC issued to SomnathProducers")
            logger.info(f"   TX Hash: {tx.txid}")
            logger.info(f"   Gas Used: {tx.gas_used:,}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to issue initial credits: {e}")
        
        logger.info("✅ CONTRACT INITIALIZATION: Complete")
        
    except Exception as e:
        logger.error(f"❌ INITIALIZATION FAILED: {e}")

def main():
    """Main deployment function."""
    try:
        # Connect to network
        if not network.is_connected():
            logger.info("🔗 Connecting to development network...")
            network.connect('development')
        
        logger.info(f"🌐 Connected to network: {network.show_active()}")
        
        # Deploy contract
        contract = deploy_contract()
        
        logger.info("🎉 DEPLOYMENT COMPLETE!")
        logger.info(f"📍 Contract available at: {contract.address}")
        
        return contract
        
    except Exception as e:
        logger.error(f"❌ DEPLOYMENT PROCESS FAILED: {e}")
        raise

if __name__ == "__main__":
    main()