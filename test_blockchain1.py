"""
Updated Test Suite for pet_blockchain.py
Compatible with the FINAL patched Blockchain & PetRegistry implementation.
"""

import unittest
from pet_blockchain import Blockchain, MINING_SENDER, PetRegistry
import hashlib


# -----------------------------------------------------------
# Node Management Tests
# -----------------------------------------------------------
class TestNodeEdgeCases(unittest.TestCase):

    def setUp(self):
        self.blockchain = Blockchain()

    def test_register_node_with_full_url(self):
        """Should accept http://127.0.0.1:5002"""
        self.blockchain.register_node("http://127.0.0.1:5002")
        self.assertIn("127.0.0.1:5002", self.blockchain.nodes)

    def test_register_node_with_host_only(self):
        """Should accept bare host:port"""
        self.blockchain.register_node("127.0.0.1:5003")
        self.assertIn("127.0.0.1:5003", self.blockchain.nodes)

    def test_register_duplicate_nodes(self):
        """Duplicate nodes should only be added once (set behavior)."""
        self.blockchain.register_node("http://127.0.0.1:5002")
        self.blockchain.register_node("http://127.0.0.1:5002")
        node_count = sum(1 for n in self.blockchain.nodes if "127.0.0.1:5002" in n)
        self.assertEqual(node_count, 1)


# -----------------------------------------------------------
# Core Blockchain Tests
# -----------------------------------------------------------
class TestBlockchainCoreEdgeCases(unittest.TestCase):

    def setUp(self):
        self.blockchain = Blockchain()

    def test_genesis_block_created(self):
        """Genesis block should exist on initialization."""
        self.assertEqual(len(self.blockchain.chain), 1)
        self.assertEqual(self.blockchain.chain[0]["block_number"], 1)
        self.assertEqual(self.blockchain.chain[0]["previous_hash"], "00")

    def test_create_block_clears_unconfirmed(self):
        """Creating a block should clear unconfirmed transactions."""
        self.blockchain.unconfirmed_transactions.append({
            "sender_public_key_hash": MINING_SENDER,
            "recipient_public_key_hash": "recipient",
            "amount": 1
        })
        
        nonce = self.blockchain.proof_of_work()
        prev_hash = self.blockchain.hash(self.blockchain.chain[-1])
        self.blockchain.create_block(nonce, prev_hash)
        
        self.assertEqual(len(self.blockchain.unconfirmed_transactions), 0)

    def test_proof_of_work_with_empty_pool(self):
        """PoW works even with no transactions."""
        nonce = self.blockchain.proof_of_work()
        self.assertIsInstance(nonce, int)

    def test_hash_consistency(self):
        """Same block should produce same hash."""
        dummy = {
            "block_number": 10,
            "timestamp": 12345,
            "transactions": [],
            "nonce": 99,
            "previous_hash": "00"
        }
        h1 = self.blockchain.hash(dummy)
        h2 = self.blockchain.hash(dummy)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_submit_transaction_mining_reward(self):
        """Mining reward transaction should be added without signature."""
        result = self.blockchain.submit_transaction(
            sender_public_key=MINING_SENDER,
            recipient_public_key="miner123",
            signature="",
            amount=1
        )
        self.assertIsInstance(result, int)
        self.assertGreater(len(self.blockchain.unconfirmed_transactions), 0)


# -----------------------------------------------------------
# Pet Registry Tests
# -----------------------------------------------------------
class TestPetRegistryEdgeCases(unittest.TestCase):

    def setUp(self):
        self.blockchain = Blockchain()
        self.owner_key = "owner_public_key_example"

    def test_register_pet_with_minimal_data(self):
        """Pet registration should work with minimal data and apply defaults."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "EdgeDog"},
            owner_public_key=self.owner_key
        )
        pet = self.blockchain.pet_registry.get_pet(pet_id)

        self.assertIsNotNone(pet)
        self.assertEqual(pet["name"], "EdgeDog")
        self.assertEqual(pet["species"], "dog")  # default applied
        self.assertEqual(pet["status"], "active")

    def test_register_pet_with_full_data(self):
        """Pet registration should store all provided data."""
        pet_id = self.blockchain.register_pet(
            pet_data={
                "name": "FullDog",
                "breed": "Golden Retriever",
                "species": "dog",
                "birth_date": "2020-01-01",
                "color": "Golden",
                "weight": "65 lbs",
                "microchip_id": "CHIP123",
                "photo": "base64photo",
                "owner_name": "John Doe",
                "owner_phone": "555-1234",
                "owner_email": "john@example.com"
            },
            owner_public_key=self.owner_key
        )
        pet = self.blockchain.pet_registry.get_pet(pet_id)

        self.assertEqual(pet["breed"], "Golden Retriever")
        self.assertEqual(pet["microchip_id"], "CHIP123")
        self.assertEqual(pet["owner_name"], "John Doe")

    def test_register_multiple_pets_same_microchip_allowed(self):
        """Multiple pets can share the same microchip (generates unique pet_id)."""
        chip = "MICROCHIP_DUPLICATE"

        p1 = self.blockchain.register_pet(
            pet_data={"name": "Dog1", "microchip_id": chip},
            owner_public_key=self.owner_key
        )
        p2 = self.blockchain.register_pet(
            pet_data={"name": "Dog2", "microchip_id": chip},
            owner_public_key=self.owner_key
        )

        self.assertNotEqual(p1, p2)

    def test_view_pet_profile_invalid_id_returns_false(self):
        """Viewing non-existent pet should return False."""
        res = self.blockchain.view_pet_profile("no-such-pet", "viewer123")
        self.assertFalse(res)

    def test_view_pet_profile_increments_count(self):
        """Viewing a pet should increment its view count."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "ViewDog"},
            owner_public_key=self.owner_key
        )
        
        self.blockchain.view_pet_profile(pet_id, "viewer1")
        self.blockchain.view_pet_profile(pet_id, "viewer2")
        
        pet = self.blockchain.pet_registry.get_pet(pet_id)
        self.assertEqual(pet["view_count"], 2)

    def test_add_vet_record_success(self):
        """Adding vet record with correct owner should succeed."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "VetDog"},
            owner_public_key=self.owner_key
        )

        rec_id = self.blockchain.add_vet_record_to_pet(
            pet_id,
            record={
                "record_type": "vaccination",
                "vet_name": "Dr. Smith",
                "vet_clinic": "City Vet",
                "vet_phone": "555-VET",
                "procedure": "Rabies Shot",
                "notes": "Annual vaccination"
            },
            owner_public_key=self.owner_key
        )

        self.assertIsNotNone(rec_id)
        pet = self.blockchain.pet_registry.get_pet(pet_id)
        self.assertEqual(len(pet["vet_records"]), 1)
        self.assertEqual(pet["vet_records"][0]["record_type"], "vaccination")

    def test_add_vet_record_wrong_owner_fails(self):
        """Adding vet record with wrong owner should fail."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "VetDog"},
            owner_public_key="correct_owner"
        )

        rec = self.blockchain.add_vet_record_to_pet(
            pet_id,
            record={
                "record_type": "vaccination",
                "vet_name": "Dr. Wrong",
                "procedure": "Rabies Shot"
            },
            owner_public_key="WRONG_OWNER"
        )

        self.assertFalse(rec)

    def test_report_pet_lost_success(self):
        """Reporting pet lost with correct owner should succeed."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "LostDog"},
            owner_public_key=self.owner_key
        )

        ok = self.blockchain.report_pet_lost(
            pet_id,
            owner_public_key=self.owner_key,
            location="Central Park",
            description="Ran away during walk"
        )

        self.assertTrue(ok)
        pet = self.blockchain.pet_registry.get_pet(pet_id)
        self.assertEqual(pet["status"], "lost")
        self.assertEqual(pet["lost_location"], "Central Park")

    def test_report_pet_lost_with_wrong_owner(self):
        """Reporting pet lost with wrong owner should fail."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "LostDog"},
            owner_public_key="yes_owner"
        )

        ok = self.blockchain.report_pet_lost(
            pet_id,
            owner_public_key="bad_owner",
            location="City",
            description="Gone"
        )

        self.assertFalse(ok)
        self.assertEqual(
            self.blockchain.pet_registry.get_pet(pet_id)["status"],
            "active"
        )

    def test_report_pet_found_success(self):
        """Reporting found pet when pet is lost should succeed."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "FoundDog"},
            owner_public_key=self.owner_key
        )

        # First mark as lost
        self.blockchain.report_pet_lost(
            pet_id,
            owner_public_key=self.owner_key,
            location="Park",
            description="Lost"
        )

        # Then report found
        ok = self.blockchain.report_pet_found(
            pet_id,
            finder_public_key="finder123",
            finder_contact="555-FIND"
        )

        self.assertTrue(ok)
        pet = self.blockchain.pet_registry.get_pet(pet_id)
        self.assertEqual(pet["status"], "active")
        self.assertEqual(pet["found_by"], "555-FIND")

    def test_report_pet_found_when_not_lost(self):
        """Reporting found pet when not lost should fail."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "ChillDog"},
            owner_public_key=self.owner_key
        )

        ok = self.blockchain.report_pet_found(
            pet_id,
            finder_public_key="finder123",
            finder_contact="555"
        )
        self.assertFalse(ok)

    def test_mark_pet_lost_twice_ok(self):
        """Marking pet lost multiple times should update location."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "TwiceLost"},
            owner_public_key=self.owner_key
        )

        self.blockchain.report_pet_lost(pet_id, self.owner_key, "City", "first")
        self.blockchain.report_pet_lost(pet_id, self.owner_key, "City2", "second")

        pet = self.blockchain.pet_registry.get_pet(pet_id)
        self.assertEqual(pet["status"], "lost")
        self.assertEqual(pet["lost_location"], "City2")


# -----------------------------------------------------------
# Search Tests
# -----------------------------------------------------------
class TestPetSearch(unittest.TestCase):

    def setUp(self):
        self.blockchain = Blockchain()
        self.owner_key = "search_owner"

    def test_search_pets_empty_registry(self):
        """Searching empty registry should return empty list."""
        results = self.blockchain.pet_registry.search_pets()
        self.assertEqual(len(results), 0)

    def test_search_pets_all(self):
        """Searching without query should return all pets."""
        self.blockchain.register_pet(
            pet_data={"name": "Dog1"},
            owner_public_key=self.owner_key
        )
        self.blockchain.register_pet(
            pet_data={"name": "Dog2"},
            owner_public_key=self.owner_key
        )

        results = self.blockchain.pet_registry.search_pets()
        self.assertEqual(len(results), 2)

    def test_search_pets_by_name(self):
        """Searching by name should return matching pets."""
        self.blockchain.register_pet(
            pet_data={"name": "Buddy"},
            owner_public_key=self.owner_key
        )
        self.blockchain.register_pet(
            pet_data={"name": "Max"},
            owner_public_key=self.owner_key
        )

        results = self.blockchain.pet_registry.search_pets(query="Buddy")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Buddy")

    def test_search_pets_by_microchip(self):
        """Searching by microchip should return matching pets."""
        self.blockchain.register_pet(
            pet_data={"name": "ChipDog", "microchip_id": "CHIP999"},
            owner_public_key=self.owner_key
        )

        results = self.blockchain.pet_registry.search_pets(query="CHIP999")
        self.assertEqual(len(results), 1)

    def test_search_pets_lost_only(self):
        """Searching with lost_only flag should return only lost pets."""
        p1 = self.blockchain.register_pet(
            pet_data={"name": "Active"},
            owner_public_key=self.owner_key
        )
        p2 = self.blockchain.register_pet(
            pet_data={"name": "Lost"},
            owner_public_key=self.owner_key
        )

        self.blockchain.report_pet_lost(p2, self.owner_key, "Park", "Lost")

        results = self.blockchain.pet_registry.search_pets(lost_only=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Lost")


# -----------------------------------------------------------
# History + Stats Tests
# -----------------------------------------------------------
class TestHistoryAndStatsEdgeCases(unittest.TestCase):

    def setUp(self):
        self.blockchain = Blockchain()
        self.owner = "stats_owner"

    def test_history_for_unknown_pet(self):
        """History for non-existent pet should return empty list."""
        history = self.blockchain.get_pet_blockchain_history("nope")
        self.assertEqual(history, [])

    def test_history_includes_pending(self):
        """History should include pending transactions."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "HistoryDog"},
            owner_public_key=self.owner
        )

        self.blockchain.report_pet_lost(
            pet_id,
            owner_public_key=self.owner,
            location="Nowhere",
            description="Pending"
        )

        history = self.blockchain.get_pet_blockchain_history(pet_id)
        pending = [h for h in history if h.get("status") == "pending"]

        self.assertGreaterEqual(len(pending), 1)

    def test_history_after_mining(self):
        """History should show transactions in mined blocks."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "MinedDog"},
            owner_public_key=self.owner
        )

        # Mine the block
        nonce = self.blockchain.proof_of_work()
        prev_hash = self.blockchain.hash(self.blockchain.chain[-1])
        self.blockchain.create_block(nonce, prev_hash)

        history = self.blockchain.get_pet_blockchain_history(pet_id)
        mined = [h for h in history if "block_number" in h]

        self.assertGreaterEqual(len(mined), 1)

    def test_stats_on_empty_registry(self):
        """Stats on empty registry should return zeros."""
        stats = self.blockchain.get_registry_stats()

        self.assertEqual(stats["total_pets"], 0)
        self.assertEqual(stats["active_pets"], 0)
        self.assertEqual(stats["lost_pets"], 0)
        self.assertEqual(stats["total_vet_records"], 0)
        self.assertEqual(stats["total_views"], 0)

    def test_stats_update_correctly(self):
        """Stats should accurately reflect registry state."""
        # Register pets
        p1 = self.blockchain.register_pet(
            pet_data={"name": "Stat1"},
            owner_public_key=self.owner
        )
        p2 = self.blockchain.register_pet(
            pet_data={"name": "Stat2"},
            owner_public_key=self.owner
        )

        # Mark p2 as lost
        self.blockchain.report_pet_lost(
            p2, self.owner, "Park", "Lost"
        )

        # Add vet record to p1
        self.blockchain.add_vet_record_to_pet(
            p1,
            record={
                "record_type": "checkup",
                "vet_name": "Dr. Edge",
                "procedure": "Exam"
            },
            owner_public_key=self.owner
        )

        # View p1 twice
        self.blockchain.view_pet_profile(p1, "viewer1")
        self.blockchain.view_pet_profile(p1, "viewer2")

        stats = self.blockchain.get_registry_stats()

        self.assertEqual(stats["total_pets"], 2)
        self.assertEqual(stats["active_pets"], 1)
        self.assertEqual(stats["lost_pets"], 1)
        self.assertGreaterEqual(stats["total_vet_records"], 1)
        self.assertGreaterEqual(stats["total_views"], 2)


# -----------------------------------------------------------
# QR Code Tests
# -----------------------------------------------------------
class TestQRCodeGeneration(unittest.TestCase):

    def setUp(self):
        self.blockchain = Blockchain()
        self.owner_key = "qr_owner"

    def test_generate_qr_code(self):
        """QR code should be generated for valid pet_id."""
        pet_id = self.blockchain.register_pet(
            pet_data={"name": "QRDog"},
            owner_public_key=self.owner_key
        )

        qr = self.blockchain.pet_registry.generate_qr(pet_id)
        self.assertIsNotNone(qr)
        self.assertTrue(qr.startswith("data:image/png;base64,"))


# -----------------------------------------------------------
# MAIN
# -----------------------------------------------------------
if __name__ == "__main__":
    unittest.main(verbosity=2)