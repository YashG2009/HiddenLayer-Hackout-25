"""
Test script to verify service isolation and dependency conflict resolution.
Tests that both AI and blockchain services can coexist without import or runtime conflicts.
"""
import sys
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_config_module():
    """Test configuration module."""
    logger.info("Testing configuration module...")
    try:
        from config import config
        
        # Test basic configuration access
        assert config.get('AI_SERVICE_ENABLED') is not None
        assert config.get('BLOCKCHAIN_SERVICE_ENABLED') is not None
        assert isinstance(config.is_ai_enabled(), bool)
        assert isinstance(config.is_blockchain_enabled(), bool)
        
        logger.info("✓ Configuration module working correctly")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration module failed: {e}")
        return False

def test_ai_service_isolation():
    """Test AI service isolation and lazy loading."""
    logger.info("Testing AI service isolation...")
    try:
        from services.ai_service import ai_service
        
        # Test service availability check
        is_available = ai_service.is_available()
        logger.info(f"AI service available: {is_available}")
        
        if not is_available:
            error = ai_service.get_initialization_error()
            logger.info(f"AI service initialization error (expected): {error}")
        
        # Test risk analysis with fallback behavior
        test_history = [
            {'amount': 100, 'timestamp': '2024-01-01T10:00:00'},
            {'amount': 150, 'timestamp': '2024-01-02T10:00:00'}
        ]
        
        analysis = ai_service.get_risk_analysis(
            producer_name="TestProducer",
            capacity=1000,
            pending_amount=200,
            transaction_history=test_history
        )
        
        # Verify analysis structure
        required_keys = ['risk_score', 'assessment', 'summary', 'detailed_analysis']
        for key in required_keys:
            assert key in analysis, f"Missing key: {key}"
        
        logger.info(f"✓ AI service isolation working correctly")
        logger.info(f"  Analysis result: {analysis['assessment']}")
        return True
        
    except ImportError as e:
        logger.error(f"✗ AI service import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ AI service test failed: {e}")
        return False

def test_blockchain_service_isolation():
    """Test blockchain service isolation and adapter pattern."""
    logger.info("Testing blockchain service isolation...")
    try:
        from services.blockchain_service import blockchain_adapter
        
        # Test backend type
        backend_type = blockchain_adapter.get_backend_type()
        logger.info(f"Blockchain backend: {backend_type}")
        
        # Test basic blockchain operations
        initial_balance = blockchain_adapter.get_balance("TestUser")
        logger.info(f"Initial balance for TestUser: {initial_balance}")
        
        # Add a test transaction
        block_index = blockchain_adapter.add_transaction(
            sender="NETWORK_TEST",
            recipient="TestUser", 
            amount=100,
            details="Test transaction"
        )
        logger.info(f"Transaction added to block: {block_index}")
        
        # Mine a block
        block = blockchain_adapter.mine_block()
        logger.info(f"Block mined: #{block['index']}")
        
        # Check updated balance
        new_balance = blockchain_adapter.get_balance("TestUser")
        logger.info(f"New balance for TestUser: {new_balance}")
        assert new_balance == initial_balance + 100, "Balance not updated correctly"
        
        # Test transaction history
        transactions = blockchain_adapter.get_user_transactions("TestUser", limit=5)
        logger.info(f"Transaction count for TestUser: {len(transactions)}")
        
        # Test chain info
        chain_info = blockchain_adapter.get_chain_info()
        logger.info(f"Chain length: {chain_info['length']}")
        
        logger.info("✓ Blockchain service isolation working correctly")
        return True
        
    except ImportError as e:
        logger.error(f"✗ Blockchain service import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Blockchain service test failed: {e}")
        return False

def test_service_coexistence():
    """Test that both services can be imported and used together."""
    logger.info("Testing service coexistence...")
    try:
        # Import both services simultaneously
        from services.ai_service import ai_service
        from services.blockchain_service import blockchain_adapter
        
        # Test that both services can be used in the same context
        ai_available = ai_service.is_available()
        blockchain_backend = blockchain_adapter.get_backend_type()
        
        logger.info(f"AI service available: {ai_available}")
        logger.info(f"Blockchain backend: {blockchain_backend}")
        
        # Test a combined workflow
        # 1. Add transaction
        blockchain_adapter.add_transaction("Producer1", "Factory1", 50, "Test credit transfer")
        
        # 2. Get transaction history for AI analysis
        history = blockchain_adapter.get_user_transactions("Producer1", limit=10)
        
        # 3. Run AI analysis
        analysis = ai_service.get_risk_analysis(
            producer_name="Producer1",
            capacity=500,
            pending_amount=75,
            transaction_history=history
        )
        
        logger.info(f"Combined workflow completed successfully")
        logger.info(f"AI assessment: {analysis['assessment']}")
        
        logger.info("✓ Service coexistence working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Service coexistence test failed: {e}")
        return False

def test_error_handling():
    """Test error handling and graceful degradation."""
    logger.info("Testing error handling...")
    try:
        from services.ai_service import ai_service
        from services.blockchain_service import blockchain_adapter
        
        # Test AI service error handling with invalid data
        invalid_analysis = ai_service.get_risk_analysis(
            producer_name="",
            capacity=-1,
            pending_amount=0,
            transaction_history=[]
        )
        
        # Should still return a valid structure even with invalid input
        assert 'risk_score' in invalid_analysis
        assert 'assessment' in invalid_analysis
        
        # Test blockchain service with edge cases
        zero_balance = blockchain_adapter.get_balance("NonExistentUser")
        assert zero_balance == 0
        
        empty_history = blockchain_adapter.get_user_transactions("NonExistentUser")
        assert isinstance(empty_history, list)
        
        logger.info("✓ Error handling working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error handling test failed: {e}")
        return False

def main():
    """Run all service isolation tests."""
    logger.info("Starting service isolation tests...")
    
    tests = [
        ("Configuration Module", test_config_module),
        ("AI Service Isolation", test_ai_service_isolation),
        ("Blockchain Service Isolation", test_blockchain_service_isolation),
        ("Service Coexistence", test_service_coexistence),
        ("Error Handling", test_error_handling),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ All service isolation tests passed!")
        return 0
    else:
        logger.error("✗ Some tests failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())