"""
Comprehensive Test Suite for Blockchain Implementation
Tests all blockchain functionality including new features

Run with: python -m pytest test_blockchain.py -v
or: python test_blockchain.py
"""

import unittest
import sys
import os
import json
import hashlib
from collections import OrderedDict

# Add parent directory to path to import blockchain module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the blockchain module (adjust import based on your file structure)
try:
    from blockchain import Blockchain, MINING_SENDER, MINING_REWARD, MINING_DIFFICULTY
except ImportError:
    print("Error: Could not import blockchain module. Make sure blockchain.py is in the correct location.")
    sys.exit(1)


class TestBlockchainBasics(unittest.TestCase):
    """Test basic blockchain functionality"""
    
    def setUp(self):
        """Set up test blockchain before each test"""
        self.blockchain = Blockchain()
    
    def test_genesis_block_creation(self):
        """Test if genesis block is created correctly"""
        self.assertEqual(len(self.blockchain.chain), 1, "Chain should have genesis block")
        self.assertEqual(self.blockchain.chain[0]['block_number'], 1, "Genesis block number should be 1")
        self.assertEqual(self.blockchain.chain[0]['previous_hash'], '00', "Genesis block previous hash should be '00'")
        self.assertEqual(len(self.blockchain.chain[0]['transactions']), 0, "Genesis block should have no transactions")
        print("✓ Genesis block creation test passed")
    
    def test_create_block(self):
        """Test block creation"""
        initial_length = len(self.blockchain.chain)
        self.blockchain.create_block(12345, 'previous_hash_test')
        
        self.assertEqual(len(self.blockchain.chain), initial_length + 1, "Chain length should increase by 1")
        new_block = self.blockchain.chain[-1]
        self.assertEqual(new_block['nonce'], 12345, "Block should have correct nonce")
        self.assertEqual(new_block['previous_hash'], 'previous_hash_test', "Block should have correct previous hash")
        print("✓ Block creation test passed")
    
    def test_hash_consistency(self):
        """Test if hashing is consistent"""
        block = self.blockchain.chain[0]
        hash1 = self.blockchain.hash(block)
        hash2 = self.blockchain.hash(block)
        
        self.assertEqual(hash1, hash2, "Hash should be consistent for same input")
        self.assertIsInstance(hash1, str, "Hash should be a string")
        self.assertEqual(len(hash1), 64, "SHA-256 hash should be 64 characters")
        print("✓ Hash consistency test passed")


# ==================== NEW FEATURE START: Merkle Tree Tests ====================
class TestMerkleTree(unittest.TestCase):
    """Test Merkle tree implementation"""
    
    def setUp(self):
        self.blockchain = Blockchain()
    
    def test_empty_merkle_root(self):
        """Test Merkle root calculation with no transactions"""
        merkle_root = self.blockchain.calculate_merkle_root([])
        self.assertIsInstance(merkle_root, str, "Merkle root should be a string")
        self.assertEqual(len(merkle_root), 64, "Merkle root should be 64 characters (SHA-256)")
        print("✓ Empty Merkle root test passed")
    
    def test_single_transaction_merkle_root(self):
        """Test Merkle root with single transaction"""
        transaction = {'sender': 'A', 'recipient': 'B', 'amount': 10}
        merkle_root = self.blockchain.calculate_merkle_root([transaction])
        self.assertIsInstance(merkle_root, str)
        print("✓ Single transaction Merkle root test passed")
    
    def test_multiple_transactions_merkle_root(self):
        """Test Merkle root with multiple transactions"""
        transactions = [
            {'sender': 'A', 'recipient': 'B', 'amount': 10},
            {'sender': 'B', 'recipient': 'C', 'amount': 5},
            {'sender': 'C', 'recipient': 'D', 'amount': 3}
        ]
        merkle_root = self.blockchain.calculate_merkle_root(transactions)
        self.assertIsInstance(merkle_root, str)
        self.assertEqual(len(merkle_root), 64)
        print("✓ Multiple transactions Merkle root test passed")
    
    def test_merkle_root_in_block(self):
        """Test that Merkle root is included in created blocks"""
        self.blockchain.transactions = [{'sender': 'test', 'recipient': 'test2', 'amount': 1}]
        block = self.blockchain.create_block(123, 'prev_hash')
        
        self.assertIn('merkle_root', block, "Block should contain merkle_root")
        self.assertIsInstance(block['merkle_root'], str)
        print("✓ Merkle root in block test passed")
# ==================== NEW FEATURE END ====================


# ==================== NEW FEATURE START: Balance System Tests ====================
class TestBalanceSystem(unittest.TestCase):
    """Test balance checking and validation"""
    
    def setUp(self):
        self.blockchain = Blockchain()
        self.test_public_key = "test_public_key_123"
    
    def test_initial_balance(self):
        """Test that new wallet has zero balance"""
        balance = self.blockchain.get_balance(self.test_public_key)
        self.assertEqual(balance, 0, "New wallet should have zero balance")
        print("✓ Initial balance test passed")
    
    def test_balance_after_receiving(self):
        """Test balance increases after receiving coins"""
        # Add transaction where test wallet receives coins
        transaction = OrderedDict({
            'sender_public_key': MINING_SENDER,
            'recipient_public_key': self.test_public_key,
            'amount': 10
        })
        self.blockchain.transactions.append(transaction)
        
        # Mine block
        nonce = self.blockchain.proof_of_work()
        last_block = self.blockchain.chain[-1]
        previous_hash = self.blockchain.hash(last_block)
        self.blockchain.create_block(nonce, previous_hash)
        
        balance = self.blockchain.get_balance(self.test_public_key)
        self.assertEqual(balance, 10, "Balance should be 10 after receiving")
        print("✓ Balance after receiving test passed")
    
    def test_validate_insufficient_balance(self):
        """Test validation rejects transaction with insufficient balance"""
        is_valid = self.blockchain.validate_transaction_amount(self.test_public_key, 100)
        self.assertFalse(is_valid, "Should reject transaction exceeding balance")
        print("✓ Insufficient balance validation test passed")
    
    def test_validate_sufficient_balance(self):
        """Test validation accepts transaction with sufficient balance"""
        # First give the wallet some balance
        transaction = OrderedDict({
            'sender_public_key': MINING_SENDER,
            'recipient_public_key': self.test_public_key,
            'amount': 50
        })
        self.blockchain.transactions.append(transaction)
        
        nonce = self.blockchain.proof_of_work()
        last_block = self.blockchain.chain[-1]
        previous_hash = self.blockchain.hash(last_block)
        self.blockchain.create_block(nonce, previous_hash)
        
        # Now validate a transaction
        is_valid = self.blockchain.validate_transaction_amount(self.test_public_key, 30)
        self.assertTrue(is_valid, "Should accept transaction within balance")
        print("✓ Sufficient balance validation test passed")
# ==================== NEW FEATURE END ====================


class TestProofOfWork(unittest.TestCase):
    """Test proof of work algorithm"""
    
    def setUp(self):
        self.blockchain = Blockchain()
    
    def test_proof_of_work_returns_integer(self):
        """Test proof of work returns a valid nonce"""
        self.blockchain.transactions.append({
            'sender': 'test_sender',
            'recipient': 'test_recipient',
            'amount': 10
        })
        nonce = self.blockchain.proof_of_work()
        
        self.assertIsInstance(nonce, int, "Nonce should be an integer")
        self.assertGreaterEqual(nonce, 0, "Nonce should be non-negative")
        print("✓ Proof of work returns integer test passed")
    
    def test_valid_proof(self):
        """Test that valid proof is accepted"""
        transactions = [{'sender': 'A', 'recipient': 'B', 'amount': 5}]
        last_hash = 'test_hash'
        nonce = 0
        
        # Find a valid nonce
        while not self.blockchain.valid_proof(transactions, last_hash, nonce):
            nonce += 1
            if nonce > 10000:  # Safety limit for test
                break
        
        is_valid = self.blockchain.valid_proof(transactions, last_hash, nonce)
        self.assertTrue(is_valid, "Found nonce should create valid proof")
        print("✓ Valid proof test passed")


class TestChainValidation(unittest.TestCase):
    """Test blockchain validation"""
    
    def setUp(self):
        self.blockchain = Blockchain()
    
    def test_valid_chain_single_block(self):
        """Test validation of chain with only genesis block"""
        is_valid = self.blockchain.valid_chain(self.blockchain.chain)
        self.assertTrue(is_valid, "Chain with only genesis block should be valid")
        print("✓ Single block chain validation test passed")
    
    def test_valid_chain_multiple_blocks(self):
        """Test validation of chain with multiple blocks"""
        # Add several blocks
        for i in range(3):
            self.blockchain.transactions.append({
                'sender_public_key': MINING_SENDER,
                'recipient_public_key': f'recipient_{i}',
                'amount': i + 1
            })
            nonce = self.blockchain.proof_of_work()
            last_block = self.blockchain.chain[-1]
            previous_hash = self.blockchain.hash(last_block)
            self.blockchain.create_block(nonce, previous_hash)
        
        is_valid = self.blockchain.valid_chain(self.blockchain.chain)
        self.assertTrue(is_valid, "Valid chain should pass validation")
        print("✓ Multiple blocks chain validation test passed")
    
    def test_invalid_chain_tampered_data(self):
        """Test detection of tampered blockchain"""
        # Create valid chain
        self.blockchain.transactions.append({
            'sender_public_key': MINING_SENDER,
            'recipient_public_key': 'recipient',
            'amount': 10
        })
        nonce = self.blockchain.proof_of_work()
        last_block = self.blockchain.chain[-1]
        previous_hash = self.blockchain.hash(last_block)
        self.blockchain.create_block(nonce, previous_hash)
        
        # Tamper with the chain
        if len(self.blockchain.chain) > 1:
            self.blockchain.chain[1]['transactions'] = []
            
            is_valid = self.blockchain.valid_chain(self.blockchain.chain)
            self.assertFalse(is_valid, "Tampered chain should be invalid")
            print("✓ Invalid chain detection test passed")


# ==================== NEW FEATURE START: Smart Contract Tests ====================
class TestSmartContracts(unittest.TestCase):
    """Test smart contract functionality"""
    
    def setUp(self):
        self.blockchain = Blockchain()
    
    def test_deploy_contract(self):
        """Test smart contract deployment"""
        contract_id = self.blockchain.deploy_smart_contract(
            'contract_001',
            'simple_contract_code',
            'creator_public_key'
        )
        
        self.assertEqual(contract_id, 'contract_001', "Should return correct contract ID")
        self.assertIn('contract_001', self.blockchain.smart_contracts, "Contract should be stored")
        print("✓ Smart contract deployment test passed")
    
    def test_execute_contract_get_state(self):
        """Test smart contract state retrieval"""
        self.blockchain.deploy_smart_contract(
            'contract_002',
            'code',
            'creator'
        )
        
        result = self.blockchain.execute_smart_contract('contract_002', 'get_state', {})
        self.assertIsInstance(result, dict, "Should return state dictionary")
        print("✓ Smart contract get state test passed")
    
    def test_execute_contract_set_state(self):
        """Test smart contract state modification"""
        self.blockchain.deploy_smart_contract(
            'contract_003',
            'code',
            'creator'
        )
        
        result = self.blockchain.execute_smart_contract(
            'contract_003',
            'set_state',
            {'key': 'value'}
        )
        
        self.assertTrue(result.get('success'), "State update should succeed")
        self.assertEqual(result['state']['key'], 'value', "State should be updated")
        print("✓ Smart contract set state test passed")
    
    def test_execute_nonexistent_contract(self):
        """Test executing non-existent contract"""
        result = self.blockchain.execute_smart_contract('nonexistent', 'get_state', {})
        self.assertIn('error', result, "Should return error for non-existent contract")
        print("✓ Non-existent contract test passed")
# ==================== NEW FEATURE END ====================


# ==================== NEW FEATURE START: Statistics Tests ====================
class TestBlockchainStatistics(unittest.TestCase):
    """Test blockchain statistics functionality"""
    
    def setUp(self):
        self.blockchain = Blockchain()
    
    def test_get_stats_genesis_only(self):
        """Test statistics with only genesis block"""
        stats = self.blockchain.get_blockchain_stats()
        
        self.assertEqual(stats['total_blocks'], 1, "Should have 1 block")
        self.assertEqual(stats['total_transactions'], 0, "Should have 0 transactions")
        self.assertEqual(stats['pending_transactions'], 0, "Should have 0 pending")
        print("✓ Genesis block statistics test passed")
    
    def test_get_stats_with_blocks(self):
        """Test statistics with multiple blocks"""
        # Add some transactions and mine blocks
        for i in range(3):
            self.blockchain.transactions.append({
                'sender_public_key': MINING_SENDER,
                'recipient_public_key': f'recipient_{i}',
                'amount': i + 1
            })
            nonce = self.blockchain.proof_of_work()
            last_block = self.blockchain.chain[-1]
            previous_hash = self.blockchain.hash(last_block)
            self.blockchain.create_block(nonce, previous_hash)
        
        stats = self.blockchain.get_blockchain_stats()
        
        self.assertEqual(stats['total_blocks'], 4, "Should have 4 blocks")
        self.assertGreater(stats['total_transactions'], 0, "Should have transactions")
        print("✓ Multiple blocks statistics test passed")
# ==================== NEW FEATURE END ====================


# ==================== NEW FEATURE START: Hashing Algorithm Tests ====================
class TestHashingAlgorithms(unittest.TestCase):
    """Test multiple hashing algorithm support"""
    
    def setUp(self):
        self.blockchain = Blockchain()
        self.test_data = "test_data_for_hashing"
    
    def test_sha256_hashing(self):
        """Test SHA-256 hashing"""
        hash_result = self.blockchain.hash_with_algorithm(self.test_data, 'sha256')
        self.assertEqual(len(hash_result), 64, "SHA-256 should produce 64-char hash")
        print("✓ SHA-256 hashing test passed")
    
    def test_sha3_256_hashing(self):
        """Test SHA3-256 hashing"""
        hash_result = self.blockchain.hash_with_algorithm(self.test_data, 'sha3_256')
        self.assertEqual(len(hash_result), 64, "SHA3-256 should produce 64-char hash")
        print("✓ SHA3-256 hashing test passed")
    
    def test_blake2b_hashing(self):
        """Test BLAKE2b hashing"""
        hash_result = self.blockchain.hash_with_algorithm(self.test_data, 'blake2b')
        self.assertEqual(len(hash_result), 128, "BLAKE2b should produce 128-char hash")
        print("✓ BLAKE2b hashing test passed")
    
    def test_different_algorithms_produce_different_hashes(self):
        """Test that different algorithms produce different hashes"""
        sha256 = self.blockchain.hash_with_algorithm(self.test_data, 'sha256')
        sha3 = self.blockchain.hash_with_algorithm(self.test_data, 'sha3_256')
        blake2b = self.blockchain.hash_with_algorithm(self.test_data, 'blake2b')
        
        self.assertNotEqual(sha256, sha3, "SHA-256 and SHA3-256 should differ")
        self.assertNotEqual(sha256, blake2b, "SHA-256 and BLAKE2b should differ")
        print("✓ Different algorithms produce different hashes test passed")
    
    def test_invalid_algorithm(self):
        """Test invalid algorithm raises error"""
        with self.assertRaises(ValueError):
            self.blockchain.hash_with_algorithm(self.test_data, 'invalid_algo')
        print("✓ Invalid algorithm test passed")
# ==================== NEW FEATURE END ====================


# ==================== NEW FEATURE START: Transaction History Tests ====================
class TestTransactionHistory(unittest.TestCase):
    """Test transaction history functionality"""
    
    def setUp(self):
        self.blockchain = Blockchain()
        self.test_public_key = "test_wallet_key"
    
    def test_empty_history(self):
        """Test transaction history for new wallet"""
        history = self.blockchain.get_transaction_history(self.test_public_key)
        self.assertEqual(len(history), 0, "New wallet should have no history")
        print("✓ Empty transaction history test passed")
    
    def test_history_with_transactions(self):
        """Test transaction history retrieval"""
        # Add transactions involving test wallet
        for i in range(3):
            self.blockchain.transactions.append({
                'sender_public_key': MINING_SENDER,
                'recipient_public_key': self.test_public_key,
                'amount': i + 1
            })
            nonce = self.blockchain.proof_of_work()
            last_block = self.blockchain.chain[-1]
            previous_hash = self.blockchain.hash(last_block)
            self.blockchain.create_block(nonce, previous_hash)
        
        history = self.blockchain.get_transaction_history(self.test_public_key)
        self.assertGreater(len(history), 0, "Should have transaction history")
        
        # Check that history contains required fields
        if len(history) > 0:
            self.assertIn('block_number', history[0], "Should include block number")
            self.assertIn('timestamp', history[0], "Should include timestamp")
        print("✓ Transaction history retrieval test passed")
    
    def test_history_limit(self):
        """Test transaction history limit parameter"""
        # Add many transactions
        for i in range(15):
            self.blockchain.transactions.append({
                'sender_public_key': self.test_public_key,
                'recipient_public_key': f'recipient_{i}',
                'amount': 1
            })
            nonce = self.blockchain.proof_of_work()
            last_block = self.blockchain.chain[-1]
            previous_hash = self.blockchain.hash(last_block)
            self.blockchain.create_block(nonce, previous_hash)
        
        history = self.blockchain.get_transaction_history(self.test_public_key, limit=5)
        self.assertLessEqual(len(history), 5, "Should respect limit parameter")
        print("✓ Transaction history limit test passed")
# ==================== NEW FEATURE END ====================


def run_all_tests():
    """Run all test suites"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestBlockchainBasics))
    suite.addTests(loader.loadTestsFromTestCase(TestMerkleTree))
    suite.addTests(loader.loadTestsFromTestCase(TestBalanceSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestProofOfWork))
    suite.addTests(loader.loadTestsFromTestCase(TestChainValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestSmartContracts))
    suite.addTests(loader.loadTestsFromTestCase(TestBlockchainStatistics))
    suite.addTests(loader.loadTestsFromTestCase(TestHashingAlgorithms))
    suite.addTests(loader.loadTestsFromTestCase(TestTransactionHistory))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)