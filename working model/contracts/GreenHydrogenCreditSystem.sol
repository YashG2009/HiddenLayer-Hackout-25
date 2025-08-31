// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Green Hydrogen Credit System
 * @dev Smart contract for managing green hydrogen credits with transfer, issuance, and freeze functionality
 */
contract GreenHydrogenCreditSystem {
    
    // State variables
    mapping(address => uint256) public balances;
    mapping(address => bool) public frozenAccounts;
    mapping(address => string) public accountNames;
    mapping(string => address) public nameToAddress;
    
    address public owner;
    uint256 public totalSupply;
    
    // Events
    event CreditTransfer(address indexed from, address indexed to, uint256 amount, string details);
    event CreditIssuance(address indexed to, uint256 amount, string details);
    event AccountFrozen(address indexed account, bool frozen);
    event AccountRegistered(address indexed account, string name);
    
    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }
    
    modifier notFrozen(address account) {
        require(!frozenAccounts[account], "Account is frozen");
        _;
    }
    
    modifier validAmount(uint256 amount) {
        require(amount > 0, "Amount must be greater than zero");
        _;
    }
    
    /**
     * @dev Constructor sets the contract deployer as owner
     */
    constructor() {
        owner = msg.sender;
        totalSupply = 0;
    }
    
    /**
     * @dev Register an account with a username
     * @param account The Ethereum address to register
     * @param name The username to associate with the address
     */
    function registerAccount(address account, string memory name) external onlyOwner {
        require(account != address(0), "Invalid address");
        require(bytes(name).length > 0, "Name cannot be empty");
        require(nameToAddress[name] == address(0), "Name already taken");
        require(bytes(accountNames[account]).length == 0, "Account already registered");
        
        accountNames[account] = name;
        nameToAddress[name] = account;
        
        emit AccountRegistered(account, name);
    }
    
    /**
     * @dev Issue credits to an account
     * @param to The address to issue credits to
     * @param amount The amount of credits to issue
     * @param details Additional details about the issuance
     */
    function issueCredits(address to, uint256 amount, string memory details) 
        external 
        onlyOwner 
        notFrozen(to) 
        validAmount(amount) 
    {
        require(to != address(0), "Cannot issue to zero address");
        
        balances[to] += amount;
        totalSupply += amount;
        
        emit CreditIssuance(to, amount, details);
    }
    
    /**
     * @dev Transfer credits between accounts
     * @param to The address to transfer credits to
     * @param amount The amount of credits to transfer
     * @param details Additional details about the transfer
     */
    function transferCredits(address to, uint256 amount, string memory details) 
        external 
        notFrozen(msg.sender) 
        notFrozen(to) 
        validAmount(amount) 
    {
        require(to != address(0), "Cannot transfer to zero address");
        require(to != msg.sender, "Cannot transfer to self");
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        balances[msg.sender] -= amount;
        balances[to] += amount;
        
        emit CreditTransfer(msg.sender, to, amount, details);
    }
    
    /**
     * @dev Freeze or unfreeze an account
     * @param account The address to freeze/unfreeze
     * @param frozen Whether to freeze (true) or unfreeze (false) the account
     */
    function setAccountFrozen(address account, bool frozen) external onlyOwner {
        require(account != address(0), "Invalid address");
        require(account != owner, "Cannot freeze owner account");
        
        frozenAccounts[account] = frozen;
        
        emit AccountFrozen(account, frozen);
    }
    
    /**
     * @dev Get the balance of an account
     * @param account The address to query
     * @return The balance of the account
     */
    function getBalance(address account) external view returns (uint256) {
        return balances[account];
    }
    
    /**
     * @dev Get the address associated with a username
     * @param name The username to query
     * @return The address associated with the username
     */
    function getAddressByName(string memory name) external view returns (address) {
        return nameToAddress[name];
    }
    
    /**
     * @dev Get the username associated with an address
     * @param account The address to query
     * @return The username associated with the address
     */
    function getNameByAddress(address account) external view returns (string memory) {
        return accountNames[account];
    }
    
    /**
     * @dev Check if an account is frozen
     * @param account The address to check
     * @return Whether the account is frozen
     */
    function isAccountFrozen(address account) external view returns (bool) {
        return frozenAccounts[account];
    }
    
    /**
     * @dev Get contract information
     * @return owner_ The contract owner
     * @return totalSupply_ The total supply of credits
     */
    function getContractInfo() external view returns (address owner_, uint256 totalSupply_) {
        return (owner, totalSupply);
    }
}