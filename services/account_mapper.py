"""
Account mapping system for converting usernames to Ethereum addresses.
Handles the mapping between GHCS usernames and blockchain addresses.
"""

import json
import os
import logging
from typing import Dict, Optional, List
from brownie import accounts, network

logger = logging.getLogger(__name__)

class AccountMapper:
    """
    Manages mapping between usernames and Ethereum addresses.
    Provides functionality to register, lookup, and manage account mappings.
    """
    
    def __init__(self, mapping_file: str = "account_mappings.json"):
        self.mapping_file = mapping_file
        self.username_to_address: Dict[str, str] = {}
        self.address_to_username: Dict[str, str] = {}
        self._load_mappings()
    
    def _load_mappings(self):
        """Load existing mappings from file."""
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r') as f:
                    data = json.load(f)
                    self.username_to_address = data.get('username_to_address', {})
                    self.address_to_username = data.get('address_to_username', {})
                logger.info(f"Loaded {len(self.username_to_address)} account mappings")
            else:
                logger.info("No existing mappings file found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load mappings: {e}")
            self.username_to_address = {}
            self.address_to_username = {}
    
    def _save_mappings(self):
        """Save current mappings to file."""
        try:
            data = {
                'username_to_address': self.username_to_address,
                'address_to_username': self.address_to_username
            }
            with open(self.mapping_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Mappings saved successfully")
        except Exception as e:
            logger.error(f"Failed to save mappings: {e}")
    
    def register_account(self, username: str, address: str) -> bool:
        """
        Register a new username-address mapping.
        
        Args:
            username: The username to register
            address: The Ethereum address to associate
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Validate inputs
            if not username or not address:
                logger.error("Username and address cannot be empty")
                return False
            
            # Check for existing mappings
            if username in self.username_to_address:
                existing_address = self.username_to_address[username]
                if existing_address.lower() == address.lower():
                    logger.info(f"Username {username} already mapped to {address}")
                    return True
                else:
                    logger.error(f"Username {username} already mapped to different address")
                    return False
            
            if address.lower() in [addr.lower() for addr in self.address_to_username.keys()]:
                existing_username = self.get_username_by_address(address)
                logger.error(f"Address {address} already mapped to username {existing_username}")
                return False
            
            # Add new mapping
            self.username_to_address[username] = address
            self.address_to_username[address] = username
            self._save_mappings()
            
            logger.info(f"Registered mapping: {username} -> {address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register account {username}: {e}")
            return False
    
    def get_address_by_username(self, username: str) -> Optional[str]:
        """
        Get Ethereum address for a username.
        
        Args:
            username: The username to lookup
            
        Returns:
            Ethereum address if found, None otherwise
        """
        return self.username_to_address.get(username)
    
    def get_username_by_address(self, address: str) -> Optional[str]:
        """
        Get username for an Ethereum address.
        
        Args:
            address: The Ethereum address to lookup
            
        Returns:
            Username if found, None otherwise
        """
        # Case-insensitive lookup
        for addr, username in self.address_to_username.items():
            if addr.lower() == address.lower():
                return username
        return None
    
    def remove_mapping(self, username: str) -> bool:
        """
        Remove a username-address mapping.
        
        Args:
            username: The username to remove
            
        Returns:
            True if removal successful, False otherwise
        """
        try:
            if username not in self.username_to_address:
                logger.warning(f"Username {username} not found in mappings")
                return False
            
            address = self.username_to_address[username]
            del self.username_to_address[username]
            del self.address_to_username[address]
            self._save_mappings()
            
            logger.info(f"Removed mapping for username: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove mapping for {username}: {e}")
            return False
    
    def get_all_mappings(self) -> Dict[str, str]:
        """
        Get all username-address mappings.
        
        Returns:
            Dictionary of username -> address mappings
        """
        return self.username_to_address.copy()
    
    def get_all_usernames(self) -> List[str]:
        """
        Get list of all registered usernames.
        
        Returns:
            List of usernames
        """
        return list(self.username_to_address.keys())
    
    def get_all_addresses(self) -> List[str]:
        """
        Get list of all registered addresses.
        
        Returns:
            List of addresses
        """
        return list(self.address_to_username.keys())
    
    def create_development_mappings(self) -> bool:
        """
        Create default mappings for development environment.
        Uses Brownie's default accounts.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if network.show_active() not in ['development', 'ganache-local']:
                logger.warning("Development mappings only available in development networks")
                return False
            
            # Default development account mappings
            dev_mappings = [
                ("alice", accounts[1].address),
                ("bob", accounts[2].address),
                ("charlie", accounts[3].address),
                ("system", accounts[4].address),
                ("admin", accounts[0].address)  # Contract owner
            ]
            
            success_count = 0
            for username, address in dev_mappings:
                if self.register_account(username, address):
                    success_count += 1
            
            logger.info(f"Created {success_count}/{len(dev_mappings)} development mappings")
            return success_count == len(dev_mappings)
            
        except Exception as e:
            logger.error(f"Failed to create development mappings: {e}")
            return False
    
    def validate_address(self, address: str) -> bool:
        """
        Validate Ethereum address format.
        
        Args:
            address: The address to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation - should be 42 characters starting with 0x
            if not address or len(address) != 42 or not address.startswith('0x'):
                return False
            
            # Check if it's a valid hex string
            int(address[2:], 16)
            return True
            
        except (ValueError, TypeError):
            return False

# Global account mapper instance
account_mapper = AccountMapper()