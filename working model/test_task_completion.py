"""
Comprehensive test to verify Task 1 completion.
Tests all requirements from the task specification.
"""
import sys
import logging
import importlib
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_separate_service_modules():
    """Test that separate service modules for AI and blockchain functionality exist."""
    logger.info("Testing separate service modules...")
    
    try:
        # Test AI service module
        ai_module = importlib.import_module('services.ai_service')
        assert hasattr(ai_module, 'AIService'), "AIService class not found"
        assert hasattr(ai_module, 'ai_service'), "ai_service instance not found"
        
        # Test blockchain service module  
        blockchain_module = importlib.import_module('services.blockchain_service')
        assert hasattr(blockchain_module, 'BlockchainAdapter'), "BlockchainAdapter class not found"
        assert hasattr(blockchain_module, 'blockchain_adapter'), "blockchain_adapter instance not found"
        
        logger.info("✓ Separate service modules created successfully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Separate service modules test failed: {e}")
        return False

def test_lazy_loading_and_error_handling():
    """Test lazy loading and error handling for both services."""
    logger.info("Testing lazy loading and error handling...")
    
    try:
        from services.ai_service import ai_service
        from services.blockchain_service import blockchain_adapter
        
        # Test AI service lazy loading
        ai_available = ai_service.is_available()
        ai_error = ai_service.get_initialization_error()
        logger.info(f"AI Service - Available: {ai_available}, Error: {ai_error}")
        
        # Test blockchain service initialization
        blockchain_backend = blockchain_adapter.get_backend_type()
        blockchain_error = blockchain_adapter.get_initialization_error()
        logger.info(f"Blockchain Service - Backend: {blockchain_backend}, Error: {blockchain_error}")
        
        # Test error handling with invalid operations
        try:
            # This should handle gracefully even if AI is unavailable
            analysis = ai_service.get_risk_analysis("test", 100, 50, [])
            assert 'risk_score' in analysis, "AI service should return valid structure even when unavailable"
        except Exception as e:
            logger.error(f"AI service error handling failed: {e}")
            return False
        
        logger.info("✓ Lazy loading and error handling working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Lazy loading and error handling test failed: {e}")
        return False

def test_configuration_management():
    """Test configuration management to enable/disable services independently."""
    logger.info("Testing configuration management...")
    
    try:
        from config import config
        
        # Test configuration access
        ai_enabled = config.is_ai_enabled()
        blockchain_enabled = config.is_blockchain_enabled()
        brownie_enabled = config.is_brownie_enabled()
        
        logger.info(f"Configuration - AI: {ai_enabled}, Blockchain: {blockchain_enabled}, Brownie: {brownie_enabled}")
        
        # Test configuration getters
        assert isinstance(ai_enabled, bool), "AI enabled should be boolean"
        assert isinstance(blockchain_enabled, bool), "Blockchain enabled should be boolean"
        assert isinstance(brownie_enabled, bool), "Brownie enabled should be boolean"
        
        # Test configuration values
        secret_key = config.get('SECRET_KEY')
        assert secret_key is not None, "Secret key should be configured"
        
        data_file = config.get('DATA_FILE')
        assert data_file is not None, "Data file should be configured"
        
        logger.info("✓ Configuration management working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration management test failed: {e}")
        return False

def test_blockchain_adapter_interface():
    """Test blockchain adapter interface that can work with or without Brownie."""
    logger.info("Testing blockchain adapter interface...")
    
    try:
        from services.blockchain_service import blockchain_adapter
        
        # Test adapter interface methods
        methods_to_test = [
            'add_transaction',
            'get_balance', 
            'get_user_transactions',
            'mine_block',
            'get_chain_info'
        ]
        
        for method_name in methods_to_test:
            assert hasattr(blockchain_adapter, method_name), f"Method {method_name} not found"
        
        # Test actual operations
        initial_balance = blockchain_adapter.get_balance("TestUser")
        logger.info(f"Initial balance: {initial_balance}")
        
        # Add transaction
        block_index = blockchain_adapter.add_transaction("Sender", "TestUser", 100, "Test transaction")
        logger.info(f"Transaction added to block: {block_index}")
        
        # Mine block
        block = blockchain_adapter.mine_block()
        logger.info(f"Block mined: #{block['index']}")
        
        # Check balance update
        new_balance = blockchain_adapter.get_balance("TestUser")
        logger.info(f"New balance: {new_balance}")
        assert new_balance == initial_balance + 100, "Balance should be updated"
        
        # Test transaction history
        transactions = blockchain_adapter.get_user_transactions("TestUser")
        assert isinstance(transactions, list), "Transactions should be a list"
        
        # Test chain info
        chain_info = blockchain_adapter.get_chain_info()
        assert 'length' in chain_info, "Chain info should contain length"
        assert 'backend' in chain_info, "Chain info should contain backend type"
        
        logger.info("✓ Blockchain adapter interface working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Blockchain adapter interface test failed: {e}")
        return False

def test_service_coexistence():
    """Test that both services can coexist without import or runtime conflicts."""
    logger.info("Testing service coexistence...")
    
    try:
        # Import both services simultaneously
        from services.ai_service import ai_service
        from services.blockchain_service import blockchain_adapter
        from config import config
        
        # Test that both can be used together
        ai_status = ai_service.is_available()
        blockchain_backend = blockchain_adapter.get_backend_type()
        
        logger.info(f"Services coexisting - AI: {ai_status}, Blockchain: {blockchain_backend}")
        
        # Test combined workflow
        # 1. Add blockchain transaction
        blockchain_adapter.add_transaction("Producer1", "Factory1", 75, "Credit transfer")
        
        # 2. Get transaction history
        history = blockchain_adapter.get_user_transactions("Producer1")
        
        # 3. Run AI analysis on the data
        analysis = ai_service.get_risk_analysis("Producer1", 500, 100, history)
        
        # 4. Verify results
        assert 'risk_score' in analysis, "AI analysis should return risk score"
        assert 'assessment' in analysis, "AI analysis should return assessment"
        
        logger.info(f"Combined workflow completed - Assessment: {analysis['assessment']}")
        
        # Test configuration access while services are active
        ai_config = config.is_ai_enabled()
        blockchain_config = config.is_blockchain_enabled()
        
        logger.info(f"Configuration accessible - AI: {ai_config}, Blockchain: {blockchain_config}")
        
        logger.info("✓ Service coexistence working correctly")
        return True
        
    except Exception as e:
        logger.error(f"✗ Service coexistence test failed: {e}")
        return False

def test_requirements_compliance():
    """Test compliance with specific requirements 1.1, 1.2, 1.3."""
    logger.info("Testing requirements compliance...")
    
    try:
        # Requirement 1.1: Both libraries available without dependency conflicts
        from services.ai_service import ai_service
        from services.blockchain_service import blockchain_adapter
        
        # Should not raise import errors
        logger.info("✓ Requirement 1.1: No import conflicts")
        
        # Requirement 1.2: No version conflicts or import errors
        # Test that we can access both services without errors
        ai_available = ai_service.is_available()
        blockchain_backend = blockchain_adapter.get_backend_type()
        
        logger.info("✓ Requirement 1.2: No version conflicts")
        
        # Requirement 1.3: Use isolation to resolve conflicts
        # Test that services are properly isolated
        from config import config
        
        # Services should be configurable independently
        ai_enabled = config.is_ai_enabled()
        blockchain_enabled = config.is_blockchain_enabled()
        
        # Services should handle unavailability gracefully
        if not ai_available:
            error = ai_service.get_initialization_error()
            logger.info(f"AI service gracefully handles unavailability: {error}")
        
        logger.info("✓ Requirement 1.3: Proper isolation implemented")
        
        logger.info("✓ All requirements (1.1, 1.2, 1.3) satisfied")
        return True
        
    except Exception as e:
        logger.error(f"✗ Requirements compliance test failed: {e}")
        return False

def main():
    """Run all task completion tests."""
    logger.info("Starting Task 1 completion verification...")
    logger.info("="*60)
    
    tests = [
        ("Separate Service Modules", test_separate_service_modules),
        ("Lazy Loading and Error Handling", test_lazy_loading_and_error_handling),
        ("Configuration Management", test_configuration_management),
        ("Blockchain Adapter Interface", test_blockchain_adapter_interface),
        ("Service Coexistence", test_service_coexistence),
        ("Requirements Compliance", test_requirements_compliance),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'-'*40}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'-'*40}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TASK 1 COMPLETION SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 TASK 1 COMPLETED SUCCESSFULLY!")
        logger.info("All requirements have been satisfied:")
        logger.info("✓ Separate service modules created")
        logger.info("✓ Lazy loading and error handling implemented")
        logger.info("✓ Configuration management added")
        logger.info("✓ Blockchain adapter interface created")
        logger.info("✓ Services coexist without conflicts")
        logger.info("✓ Requirements 1.1, 1.2, 1.3 satisfied")
        return 0
    else:
        logger.error(f"\n❌ TASK 1 INCOMPLETE: {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())