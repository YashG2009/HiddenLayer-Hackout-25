#!/usr/bin/env python3
"""
Comprehensive integration tests for GHCS blockchain migration.
Tests all functionality with real blockchain integration.
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.blockchain_service import blockchain_adapter
from services.ai_service import ai_service
from services.account_mapper import account_mapper
from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestBlockchainIntegration(unittest.TestCase):
    """Test blockchain integration functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_users = [
            "TestProducer1",
            "TestFactory1", 
            "TestCitizen1",
            "TestAdmin"
        ]
        
        # Register test users
        for username in cls.test_users:
            try:
                blockchain_adapter.register_account(username)
                logger.info(f"Registered test user: {username}")
            except Exception as e:
                logger.warning(f"Could not register {username}: {e}")
    
    def setUp(self):
        """Set up each test."""
        self.initial_balances = {}
        for username in self.test_users:
            self.initial_balances[username] = blockchain_adapter.get_balance(username)
    
    def test_blockchain_adapter_initialization(self):
        """Test that blockchain adapter initializes correctly."""
        self.assertIsNotNone(blockchain_adapter)
        backend_type = blockchain_adapter.get_backend_type()
        self.assertIn(backend_type, ['brownie', 'simulated'])
        logger.info(f"Blockchain backend: {backend_type}")
    
    def test_account_registration(self):
        """Test account registration functionality."""
        test_username = "TestNewUser"
        
        # Clean up if exists
        try:
            account_mapper.remove_mapping(test_username)
        except:
            pass
        
        # Test registration
        result = blockchain_adapter.register_account(test_username)
        self.assertTrue(result, "Account registration should succeed")
        
        # Verify mapping exists (only for brownie backend)
        if blockchain_adapter.get_backend_type() == 'brownie':
            address = account_mapper.get_address_by_username(test_username)
            self.assertIsNotNone(address, "Address mapping should exist after registration")
        else:
            logger.info("Skipping address mapping check for simulated blockchain")
        
        # Clean up
        account_mapper.remove_mapping(test_username)
    
    def test_credit_issuance(self):
        """Test credit issuance functionality."""
        username = "TestProducer1"
        initial_balance = blockchain_adapter.get_balance(username)
        issue_amount = 100
        
        # Issue credits
        result = blockchain_adapter.issue_credits(username, issue_amount, "Test issuance")
        
        if blockchain_adapter.get_backend_type() == 'brownie':
            self.assertTrue(result, "Credit issuance should succeed")
            
            # Check balance increased
            new_balance = blockchain_adapter.get_balance(username)
            self.assertEqual(new_balance, initial_balance + issue_amount, 
                           f"Balance should increase by {issue_amount}")
        else:
            logger.info("Skipping balance check for simulated blockchain")
    
    def test_credit_transfer(self):
        """Test credit transfer functionality."""
        sender = "TestProducer1"
        recipient = "TestFactory1"
        transfer_amount = 50
        
        # Ensure sender has enough credits
        sender_initial = blockchain_adapter.get_balance(sender)
        if sender_initial < transfer_amount:
            blockchain_adapter.issue_credits(sender, transfer_amount, "Test setup")
            sender_initial = blockchain_adapter.get_balance(sender)
        
        recipient_initial = blockchain_adapter.get_balance(recipient)
        
        # Perform transfer
        try:
            result = blockchain_adapter.add_transaction(
                sender=sender,
                recipient=recipient, 
                amount=transfer_amount,
                details="Test transfer"
            )
            
            if blockchain_adapter.get_backend_type() == 'brownie':
                # Check balances updated correctly
                sender_final = blockchain_adapter.get_balance(sender)
                recipient_final = blockchain_adapter.get_balance(recipient)
                
                self.assertEqual(sender_final, sender_initial - transfer_amount,
                               "Sender balance should decrease")
                self.assertEqual(recipient_final, recipient_initial + transfer_amount,
                               "Recipient balance should increase")
            
            logger.info(f"Transfer successful: {sender} -> {recipient}, Amount: {transfer_amount}")
            
        except Exception as e:
            if blockchain_adapter.get_backend_type() == 'brownie':
                self.fail(f"Transfer should succeed with brownie backend: {e}")
            else:
                logger.info(f"Transfer test completed for simulated backend: {e}")
    
    def test_transaction_history(self):
        """Test transaction history retrieval."""
        username = "TestProducer1"
        
        # Get transaction history
        transactions = blockchain_adapter.get_user_transactions(username, limit=10)
        self.assertIsInstance(transactions, list, "Should return list of transactions")
        
        # Check transaction format
        if transactions:
            tx = transactions[0]
            required_fields = ['sender', 'recipient', 'amount', 'details']
            for field in required_fields:
                self.assertIn(field, tx, f"Transaction should have {field} field")
        
        logger.info(f"Retrieved {len(transactions)} transactions for {username}")
    
    def test_balance_retrieval(self):
        """Test balance retrieval for all users."""
        for username in self.test_users:
            balance = blockchain_adapter.get_balance(username)
            self.assertIsInstance(balance, int, f"Balance for {username} should be integer")
            self.assertGreaterEqual(balance, 0, f"Balance for {username} should be non-negative")
            logger.info(f"{username}: {balance} GHC")
    
    def test_chain_info(self):
        """Test blockchain information retrieval."""
        chain_info = blockchain_adapter.get_chain_info()
        self.assertIsInstance(chain_info, dict, "Chain info should be dictionary")
        
        if blockchain_adapter.get_backend_type() == 'brownie':
            required_fields = ['network', 'latest_block', 'backend']
            for field in required_fields:
                self.assertIn(field, chain_info, f"Chain info should have {field}")
        
        logger.info(f"Chain info: {chain_info}")
    
    def test_ai_service_integration(self):
        """Test AI service integration."""
        if ai_service.is_available():
            # Test AI analysis
            result = ai_service.get_risk_analysis(
                producer_name="TestProducer1",
                capacity=1000,
                pending_amount=100,
                transaction_history=[]
            )
            
            self.assertIsInstance(result, dict, "AI analysis should return dictionary")
            logger.info("AI service integration test passed")
        else:
            logger.info("AI service not available - skipping integration test")
    
    def test_error_handling(self):
        """Test error handling for invalid operations."""
        # Test invalid transfer (insufficient balance)
        try:
            blockchain_adapter.add_transaction(
                sender="TestCitizen1",
                recipient="TestFactory1",
                amount=999999,  # Very large amount
                details="Invalid transfer test"
            )
            
            if blockchain_adapter.get_backend_type() == 'brownie':
                self.fail("Should raise exception for insufficient balance")
                
        except Exception as e:
            logger.info(f"Correctly handled invalid transfer: {e}")
        
        # Test invalid user balance
        invalid_balance = blockchain_adapter.get_balance("NonExistentUser")
        self.assertEqual(invalid_balance, 0, "Non-existent user should have 0 balance")


class TestFlaskIntegration(unittest.TestCase):
    """Test Flask application integration."""
    
    def setUp(self):
        """Set up Flask test client."""
        # Import here to avoid circular imports
        from proto_v3_migrated import app
        
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.app = app
    
    def test_service_status_endpoint(self):
        """Test service status endpoint."""
        # Login as admin first
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'GovtAdmin'
            sess['role'] = 'Government'
        
        response = self.client.get('/service-status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('ai_service', data)
        self.assertIn('blockchain_service', data)
        self.assertIn('configuration', data)
        
        logger.info(f"Service status: {data}")
    
    def test_dashboard_loads(self):
        """Test that dashboard loads with blockchain data."""
        # Login as a producer
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
            sess['username'] = 'SomnathProducers'
            sess['role'] = 'Producer'
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)
        
        logger.info("Dashboard loads successfully with blockchain integration")


class TestDataMigration(unittest.TestCase):
    """Test data migration functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data_file = "test_ghcs_data.json"
        self.test_data = {
            'users': {
                'TestUser1': {
                    'name': 'TestUser1',
                    'role': 'Producer',
                    'password_hash': 'test_hash',
                    'frozen': False
                },
                'TestUser2': {
                    'name': 'TestUser2', 
                    'role': 'Factory',
                    'password_hash': 'test_hash',
                    'frozen': False
                }
            },
            'blockchain': {
                'chain': [
                    {
                        'index': 1,
                        'transactions': [
                            {
                                'sender': 'system',
                                'recipient': 'TestUser1',
                                'amount': 1000,
                                'details': 'Initial credits'
                            }
                        ]
                    }
                ]
            },
            'pending_issuances': {},
            'quotas': {},
            'issuance_counter': 0
        }
        
        # Write test data
        with open(self.test_data_file, 'w') as f:
            json.dump(self.test_data, f)
    
    def tearDown(self):
        """Clean up test data."""
        if os.path.exists(self.test_data_file):
            os.remove(self.test_data_file)
    
    def test_migration_script_import(self):
        """Test that migration script can be imported."""
        try:
            from migrate_blockchain_data import BlockchainDataMigrator
            migrator = BlockchainDataMigrator(self.test_data_file)
            self.assertIsNotNone(migrator)
            logger.info("Migration script imports successfully")
        except ImportError as e:
            self.fail(f"Could not import migration script: {e}")
    
    def test_balance_calculation(self):
        """Test balance calculation from simulated blockchain."""
        from migrate_blockchain_data import BlockchainDataMigrator
        
        migrator = BlockchainDataMigrator(self.test_data_file)
        migrator.load_existing_data()
        
        balances = migrator.calculate_user_balances()
        self.assertIn('TestUser1', balances)
        self.assertEqual(balances['TestUser1'], 1000)
        self.assertEqual(balances['TestUser2'], 0)
        
        logger.info(f"Calculated balances: {balances}")


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("="*60)
    print("GHCS BLOCKCHAIN INTEGRATION TESTS")
    print("="*60)
    
    # Check system status
    print(f"Blockchain Backend: {blockchain_adapter.get_backend_type()}")
    print(f"AI Service Available: {ai_service.is_available()}")
    
    if blockchain_adapter.get_initialization_error():
        print(f"Blockchain Warning: {blockchain_adapter.get_initialization_error()}")
    
    if not ai_service.is_available() and ai_service.get_initialization_error():
        print(f"AI Service Warning: {ai_service.get_initialization_error()}")
    
    print("-"*60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add blockchain integration tests
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestBlockchainIntegration))
    
    # Add Flask integration tests
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestFlaskIntegration))
    
    # Add data migration tests
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDataMigration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("-"*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall Result: {'✅ PASS' if success else '❌ FAIL'}")
    print("="*60)
    
    return success


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)