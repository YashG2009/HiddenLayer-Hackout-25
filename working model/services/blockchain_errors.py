"""
Comprehensive error handling for blockchain operations.
Handles network failures, gas issues, transaction failures, and other blockchain-related errors.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class BlockchainErrorType(Enum):
    """Types of blockchain errors."""
    NETWORK_ERROR = "network_error"
    GAS_ERROR = "gas_error"
    TRANSACTION_ERROR = "transaction_error"
    CONTRACT_ERROR = "contract_error"
    ACCOUNT_ERROR = "account_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"

class BlockchainError(Exception):
    """Base class for blockchain-related errors."""
    
    def __init__(self, message: str, error_type: BlockchainErrorType, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.message = message

class NetworkError(BlockchainError):
    """Network connectivity related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, BlockchainErrorType.NETWORK_ERROR, details)

class GasError(BlockchainError):
    """Gas estimation and gas price related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, BlockchainErrorType.GAS_ERROR, details)

class TransactionError(BlockchainError):
    """Transaction execution related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, BlockchainErrorType.TRANSACTION_ERROR, details)

class ContractError(BlockchainError):
    """Smart contract related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, BlockchainErrorType.CONTRACT_ERROR, details)

class AccountError(BlockchainError):
    """Account management related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, BlockchainErrorType.ACCOUNT_ERROR, details)

class ValidationError(BlockchainError):
    """Input validation related errors."""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, BlockchainErrorType.VALIDATION_ERROR, details)

class BlockchainErrorHandler:
    """Handles blockchain errors with retry logic and graceful degradation."""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def handle_error(self, error: Exception, operation: str = "blockchain operation") -> BlockchainError:
        """
        Convert generic exceptions to blockchain-specific errors.
        
        Args:
            error: The original exception
            operation: Description of the operation that failed
            
        Returns:
            BlockchainError with appropriate type and details
        """
        error_str = str(error).lower()
        
        # Network-related errors
        if any(keyword in error_str for keyword in ['connection', 'network', 'timeout', 'unreachable']):
            return NetworkError(
                f"Network error during {operation}: {str(error)}",
                details={'original_error': str(error), 'operation': operation}
            )
        
        # Gas-related errors
        elif any(keyword in error_str for keyword in ['gas', 'out of gas', 'gas limit', 'gas price']):
            return GasError(
                f"Gas error during {operation}: {str(error)}",
                details={'original_error': str(error), 'operation': operation}
            )
        
        # Transaction-related errors
        elif any(keyword in error_str for keyword in ['transaction', 'revert', 'failed', 'reverted']):
            return TransactionError(
                f"Transaction error during {operation}: {str(error)}",
                details={'original_error': str(error), 'operation': operation}
            )
        
        # Contract-related errors
        elif any(keyword in error_str for keyword in ['contract', 'abi', 'function', 'method']):
            return ContractError(
                f"Contract error during {operation}: {str(error)}",
                details={'original_error': str(error), 'operation': operation}
            )
        
        # Account-related errors
        elif any(keyword in error_str for keyword in ['account', 'address', 'balance', 'insufficient']):
            return AccountError(
                f"Account error during {operation}: {str(error)}",
                details={'original_error': str(error), 'operation': operation}
            )
        
        # Validation errors
        elif any(keyword in error_str for keyword in ['invalid', 'validation', 'format', 'required']):
            return ValidationError(
                f"Validation error during {operation}: {str(error)}",
                details={'original_error': str(error), 'operation': operation}
            )
        
        # Unknown errors
        else:
            return BlockchainError(
                f"Unknown error during {operation}: {str(error)}",
                BlockchainErrorType.UNKNOWN_ERROR,
                details={'original_error': str(error), 'operation': operation}
            )
    
    def execute_with_retry(self, operation_func, *args, **kwargs):
        """
        Execute an operation with retry logic.
        
        Args:
            operation_func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the operation
            
        Raises:
            BlockchainError: If all retries fail
        """
        import time
        
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return operation_func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if attempt < self.max_retries:
                    # Determine if error is retryable
                    if self._is_retryable_error(e):
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {self.retry_delay}s: {str(e)}")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        # Non-retryable error, fail immediately
                        break
                else:
                    # Max retries reached
                    break
        
        # All retries failed, raise the last error
        blockchain_error = self.handle_error(last_error, operation_func.__name__)
        logger.error(f"Operation {operation_func.__name__} failed after {self.max_retries} retries: {blockchain_error.message}")
        raise blockchain_error
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error: The exception to check
            
        Returns:
            True if the error is retryable, False otherwise
        """
        error_str = str(error).lower()
        
        # Retryable errors (usually temporary)
        retryable_keywords = [
            'timeout', 'connection', 'network', 'temporary', 'busy',
            'rate limit', 'throttle', 'congestion'
        ]
        
        # Non-retryable errors (usually permanent)
        non_retryable_keywords = [
            'invalid', 'unauthorized', 'forbidden', 'not found',
            'insufficient balance', 'revert', 'validation'
        ]
        
        # Check for non-retryable errors first
        if any(keyword in error_str for keyword in non_retryable_keywords):
            return False
        
        # Check for retryable errors
        if any(keyword in error_str for keyword in retryable_keywords):
            return True
        
        # Default to non-retryable for unknown errors
        return False
    
    def get_user_friendly_message(self, error: BlockchainError) -> str:
        """
        Get a user-friendly error message.
        
        Args:
            error: The blockchain error
            
        Returns:
            User-friendly error message
        """
        if error.error_type == BlockchainErrorType.NETWORK_ERROR:
            return "Network connection issue. Please check your internet connection and try again."
        
        elif error.error_type == BlockchainErrorType.GAS_ERROR:
            return "Transaction failed due to gas issues. Please try again with higher gas limit or price."
        
        elif error.error_type == BlockchainErrorType.TRANSACTION_ERROR:
            return "Transaction failed. Please check your account balance and try again."
        
        elif error.error_type == BlockchainErrorType.CONTRACT_ERROR:
            return "Smart contract error. Please contact support if this persists."
        
        elif error.error_type == BlockchainErrorType.ACCOUNT_ERROR:
            return "Account error. Please check your account details and try again."
        
        elif error.error_type == BlockchainErrorType.VALIDATION_ERROR:
            return "Invalid input. Please check your data and try again."
        
        else:
            return "An unexpected error occurred. Please try again or contact support."

# Global error handler instance
error_handler = BlockchainErrorHandler()