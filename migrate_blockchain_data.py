#!/usr/bin/env python3
"""
Data migration script for GHCS blockchain migration.
Migrates existing user data and balances from simulated blockchain to real blockchain.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List
from services.blockchain_service import blockchain_adapter
from services.account_mapper import account_mapper
from config import config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlockchainDataMigrator:
    """Handles migration of data from simulated blockchain to real blockchain."""
    
    def __init__(self, data_file: str = "ghcs_data.json"):
        self.data_file = data_file
        self.app_data = {}
        self.migration_log = []
    
    def load_existing_data(self) -> bool:
        """Load existing application data."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.app_data = json.load(f)
                logger.info(f"Loaded existing data from {self.data_file}")
                return True
            else:
                logger.info("No existing data file found - starting fresh")
                self.app_data = {
                    'users': {},
                    'blockchain': {'chain': [], 'current_transactions': []},
                    'pending_issuances': {},
                    'quotas': {},
                    'issuance_counter': 0
                }
                return False
        except Exception as e:
            logger.error(f"Failed to load existing data: {e}")
            return False
    
    def setup_initial_users(self):
        """Setup initial users if no existing data."""
        initial_users_data = [
            {"name": "GovtAdmin", "password": "govpassword", "role": "Government"},
            {"name": "StatePollGujarat", "password": "sppassword", "role": "State Poll"},
            {"name": "SomnathProducers", "password": "prodpassword", "role": "Producer", 
             "state_verification_no": "SVN-GJ-001", "capacity": 5000},
            {"name": "Ammonia Factory", "password": "factpassword", "role": "Factory", 
             "industry_type": "Ammonia", "industry_consumption": 20000},
            {"name": "CitizenOne", "password": "citipassword", "role": "Citizen"}
        ]
        
        for user_data in initial_users_data:
            if user_data['name'] not in self.app_data['users']:
                password = user_data.pop("password")
                import hashlib
                user_data['password_hash'] = hashlib.sha256(password.encode()).hexdigest()
                user_data['frozen'] = False
                self.app_data['users'][user_data['name']] = user_data
        
        logger.info("Initial users setup completed")
    
    def register_users_on_blockchain(self) -> bool:
        """Register all users on the blockchain."""
        logger.info("Registering users on blockchain...")
        
        success_count = 0
        for username, user_data in self.app_data['users'].items():
            try:
                # Check if user already has an address mapping
                existing_address = account_mapper.get_address_by_username(username)
                if existing_address:
                    logger.info(f"User {username} already has address mapping: {existing_address}")
                    success_count += 1
                    continue
                
                # Register new user on blockchain
                if blockchain_adapter.register_account(username):
                    success_count += 1
                    self.migration_log.append(f"Registered user: {username}")
                    logger.info(f"Successfully registered user: {username}")
                else:
                    logger.error(f"Failed to register user: {username}")
                    self.migration_log.append(f"FAILED to register user: {username}")
                    
            except Exception as e:
                logger.error(f"Error registering user {username}: {e}")
                self.migration_log.append(f"ERROR registering user {username}: {e}")
        
        logger.info(f"User registration completed: {success_count}/{len(self.app_data['users'])} successful")
        return success_count == len(self.app_data['users'])
    
    def calculate_user_balances(self) -> Dict[str, int]:
        """Calculate current user balances from simulated blockchain."""
        balances = {}
        
        # Initialize all users with 0 balance
        for username in self.app_data['users'].keys():
            balances[username] = 0
        
        # Process all transactions in the simulated blockchain
        for block in self.app_data['blockchain']['chain']:
            for tx in block.get('transactions', []):
                sender = tx.get('sender')
                recipient = tx.get('recipient')
                amount = tx.get('amount', 0)
                
                # Handle special system accounts
                if sender == 'NETWORK_GENESIS' or sender == 'NETWORK_CERTIFIER' or sender == 'system':
                    if recipient in balances:
                        balances[recipient] += amount
                elif sender in balances and recipient in balances:
                    balances[sender] -= amount
                    balances[recipient] += amount
        
        # Remove negative balances (shouldn't happen but safety check)
        for username in balances:
            if balances[username] < 0:
                logger.warning(f"Negative balance detected for {username}: {balances[username]}")
                balances[username] = 0
        
        logger.info(f"Calculated balances for {len(balances)} users")
        return balances
    
    def migrate_balances_to_blockchain(self, balances: Dict[str, int]) -> bool:
        """Migrate calculated balances to the real blockchain."""
        logger.info("Migrating balances to blockchain...")
        
        success_count = 0
        total_credits_issued = 0
        
        for username, balance in balances.items():
            if balance > 0:
                try:
                    if blockchain_adapter.issue_credits(username, balance, f"Migration: Initial balance from simulated blockchain"):
                        success_count += 1
                        total_credits_issued += balance
                        self.migration_log.append(f"Issued {balance} credits to {username}")
                        logger.info(f"Successfully issued {balance} credits to {username}")
                    else:
                        logger.error(f"Failed to issue credits to {username}")
                        self.migration_log.append(f"FAILED to issue {balance} credits to {username}")
                        
                except Exception as e:
                    logger.error(f"Error issuing credits to {username}: {e}")
                    self.migration_log.append(f"ERROR issuing credits to {username}: {e}")
        
        logger.info(f"Balance migration completed: {success_count} users, {total_credits_issued} total credits issued")
        return success_count > 0
    
    def migrate_pending_issuances(self) -> bool:
        """Migrate pending issuances to the new system."""
        logger.info("Migrating pending issuances...")
        
        # Pending issuances don't need blockchain migration, just preserve the data
        # They will be processed through the normal workflow
        pending_count = len(self.app_data.get('pending_issuances', {}))
        logger.info(f"Preserved {pending_count} pending issuances")
        self.migration_log.append(f"Preserved {pending_count} pending issuances")
        
        return True
    
    def save_migrated_data(self):
        """Save the migrated data back to the data file."""
        try:
            # Clear the old blockchain data since we're now using real blockchain
            self.app_data['blockchain'] = {'chain': [], 'current_transactions': []}
            
            # Add migration metadata
            self.app_data['migration_info'] = {
                'migrated': True,
                'migration_timestamp': str(datetime.now()),
                'blockchain_backend': blockchain_adapter.get_backend_type(),
                'migration_log': self.migration_log
            }
            
            with open(self.data_file, 'w') as f:
                json.dump(self.app_data, f, indent=4)
            
            logger.info(f"Migrated data saved to {self.data_file}")
            
        except Exception as e:
            logger.error(f"Failed to save migrated data: {e}")
    
    def run_migration(self) -> bool:
        """Run the complete migration process."""
        logger.info("Starting blockchain data migration...")
        
        # Load existing data
        has_existing_data = self.load_existing_data()
        
        # Setup initial users if no existing data
        if not has_existing_data:
            self.setup_initial_users()
        
        # Register users on blockchain
        if not self.register_users_on_blockchain():
            logger.error("User registration failed - aborting migration")
            return False
        
        # Calculate and migrate balances
        balances = self.calculate_user_balances()
        if not self.migrate_balances_to_blockchain(balances):
            logger.warning("Balance migration had issues - check logs")
        
        # Migrate pending issuances
        self.migrate_pending_issuances()
        
        # Save migrated data
        self.save_migrated_data()
        
        logger.info("Blockchain data migration completed successfully!")
        return True
    
    def print_migration_summary(self):
        """Print a summary of the migration."""
        print("\n" + "="*60)
        print("BLOCKCHAIN MIGRATION SUMMARY")
        print("="*60)
        
        print(f"Backend Type: {blockchain_adapter.get_backend_type()}")
        print(f"Users: {len(self.app_data['users'])}")
        print(f"Pending Issuances: {len(self.app_data.get('pending_issuances', {}))}")
        
        print("\nMigration Log:")
        for log_entry in self.migration_log:
            print(f"  - {log_entry}")
        
        print("\nUser Balances on Blockchain:")
        for username in self.app_data['users'].keys():
            balance = blockchain_adapter.get_balance(username)
            print(f"  {username}: {balance} GHC")
        
        print("="*60)


def main():
    """Main migration function."""
    from datetime import datetime
    
    print("GHCS Blockchain Data Migration Tool")
    print("="*40)
    
    # Check blockchain adapter status
    print(f"Blockchain Backend: {blockchain_adapter.get_backend_type()}")
    if blockchain_adapter.get_initialization_error():
        print(f"Warning: {blockchain_adapter.get_initialization_error()}")
    
    # Run migration
    migrator = BlockchainDataMigrator()
    
    try:
        success = migrator.run_migration()
        migrator.print_migration_summary()
        
        if success:
            print("\n✅ Migration completed successfully!")
            return 0
        else:
            print("\n❌ Migration completed with errors!")
            return 1
            
    except Exception as e:
        logger.error(f"Migration failed with exception: {e}")
        print(f"\n❌ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())