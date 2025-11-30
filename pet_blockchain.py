from flask import Flask, request, jsonify, render_template
from time import time
from flask_cors import CORS
from collections import OrderedDict
from uuid import uuid4
from urllib.parse import urlparse
import hashlib
import json
import requests

# Crypto operations
import binascii
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA

# QR Code utilities
import qrcode
from io import BytesIO
import base64

# -------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------

MINING_SENDER = "BLOCKCHAIN_REWARD"
MINING_REWARD = 1
MINING_DIFFICULTY = 2


# -------------------------------------------------------------
# UTILITY: HASH PUBLIC KEYS (exposed to frontend)
# -------------------------------------------------------------

def hashed_key(raw_key: str):
    if not raw_key:
        return "UNKNOWN_KEY"
    return hashlib.sha256(raw_key.encode()).hexdigest()[:24]


# -------------------------------------------------------------
# PET REGISTRY CLASS
# -------------------------------------------------------------

class PetRegistry:
    def __init__(self):
        self.pets = {}  # pet_id -> pet_data

    def generate_pet_id(self, microchip_id, owner_public_key):
        combined = f"{microchip_id}_{owner_public_key}_{time()}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def create_pet_profile(self, pet_id, pet_data):
        public_hash = hashed_key(pet_data.get("owner_public_key"))

        profile = {
            "pet_id": pet_id,
            "name": pet_data.get("name"),
            "breed": pet_data.get("breed"),
            "species": pet_data.get("species", "dog"),
            "birth_date": pet_data.get("birth_date"),
            "color": pet_data.get("color"),
            "weight": pet_data.get("weight"),
            "microchip_id": pet_data.get("microchip_id"),
            "photo": pet_data.get("photo"),
            "owner_public_key_hash": public_hash,     # 🔥 hashed for UI
            "owner_public_key": pet_data.get("owner_public_key"),  # stored internally
            "owner_name": pet_data.get("owner_name"),
            "owner_phone": pet_data.get("owner_phone"),
            "owner_email": pet_data.get("owner_email"),
            "registered_at": time(),
            "vet_records": [],
            "view_count": 0,
            "status": "active"
        }

        self.pets[pet_id] = profile
        return self.pets[pet_id]

    def add_vet_record(self, pet_id, record):
        if pet_id not in self.pets:
            return None

        rec = {
            "record_id": hashlib.sha256(f"{pet_id}_{time()}".encode()).hexdigest()[:12],
            "record_type": record.get("record_type"),
            "vet_name": record.get("vet_name"),
            "vet_clinic": record.get("vet_clinic"),
            "vet_phone": record.get("vet_phone"),
            "procedure": record.get("procedure"),
            "notes": record.get("notes"),
            "date": record.get("date", time()),
            "next_due_date": record.get("next_due_date"),
            "timestamp": time(),
        }

        self.pets[pet_id]["vet_records"].append(rec)
        return rec

    def mark_pet_lost(self, pet_id, location=None, description=None):
        if pet_id not in self.pets:
            return False

        pet = self.pets[pet_id]
        pet["status"] = "lost"
        pet["lost_location"] = location
        pet["lost_description"] = description
        pet["lost_since"] = time()
        return True

    def mark_pet_found(self, pet_id, found_by=None):
        if pet_id not in self.pets:
            return False

        pet = self.pets[pet_id]
        pet["status"] = "active"
        pet["found_by"] = found_by
        pet["found_at"] = time()
        return True

    def increment_view_count(self, pet_id):
        if pet_id not in self.pets:
            return 0
        self.pets[pet_id]["view_count"] += 1
        return self.pets[pet_id]["view_count"]

    def search_pets(self, query=None, lost_only=False):
        results = []

        for pet_id, pet in self.pets.items():
            if lost_only and pet["status"] != "lost":
                continue

            if not query:
                results.append(pet)
                continue

            q = query.lower()
            if (
                q in pet.get("name", "").lower()
                or q in pet.get("microchip_id", "").lower()
                or q in pet.get("breed", "").lower()
                or q in pet_id.lower()
            ):
                results.append(pet)

        return results

    def get_pet(self, pet_id):
        return self.pets.get(pet_id)

    def generate_qr(self, pet_id):
        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        qr.add_data(f"http://127.0.0.1:5001/pet/{pet_id}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buff = BytesIO()
        img.save(buff, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buff.getvalue()).decode()


# -------------------------------------------------------------
# BLOCKCHAIN CLASS (FULLY PATCHED)
# -------------------------------------------------------------

class Blockchain:
    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.nodes = set()
        self.node_id = str(uuid4()).replace("-", "")
        self.pet_registry = PetRegistry()

        # create genesis block
        self.create_block(0, "00")

    # -----------------------------
    # Node Management
    # -----------------------------

    def register_node(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)

    # -----------------------------
    # Block Creation
    # -----------------------------

    def create_block(self, nonce, previous_hash):
        block = {
            "block_number": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": self.unconfirmed_transactions.copy(),
            "nonce": nonce,
            "previous_hash": previous_hash,
        }

        # reset pending list
        self.unconfirmed_transactions = []

        self.chain.append(block)
        return block

    # -----------------------------
    # PoW
    # -----------------------------

    def proof_of_work(self):
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)
        nonce = 0

        while True:
            guess = json.dumps(self.unconfirmed_transactions, sort_keys=True).encode() + \
                    str(last_hash).encode() + \
                    str(nonce).encode()

            guess_hash = hashlib.sha256(guess).hexdigest()

            if guess_hash[:MINING_DIFFICULTY] == "0" * MINING_DIFFICULTY:
                return nonce

            nonce += 1

    @staticmethod
    def hash(block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    # -----------------------------
    # Transaction Submission
    # -----------------------------

    def verify_transaction_signature(self, sender_public_key, signature, transaction):
        try:
            pub_key = RSA.importKey(binascii.unhexlify(sender_public_key))
            verifier = PKCS1_v1_5.new(pub_key)
            h = SHA.new(str(transaction).encode("utf-8"))
            return verifier.verify(h, binascii.unhexlify(signature))
        except:
            return False

    def submit_transaction(self, sender_public_key, recipient_public_key, signature, amount):
        tx = OrderedDict({
            "sender_public_key_hash": hashed_key(sender_public_key),
            "recipient_public_key_hash": hashed_key(recipient_public_key),
            "amount": float(amount),
            "timestamp": time()
        })

        # Mining reward (no signature)
        if sender_public_key == MINING_SENDER:
            self.unconfirmed_transactions.append(tx)
            return len(self.chain) + 1

        # Regular signed transaction
        transaction_data = {
            "sender_public_key": sender_public_key,
            "recipient_public_key": recipient_public_key,
            "amount": amount,
        }

        if not self.verify_transaction_signature(sender_public_key, signature, transaction_data):
            return False

        self.unconfirmed_transactions.append(tx)
        return len(self.chain) + 1

    # -----------------------------------------------------------
    # PET REGISTRY (writes events to blockchain)
    # -----------------------------------------------------------

    def register_pet(self, pet_data, owner_public_key):
        pet_id = self.pet_registry.generate_pet_id(
            pet_data.get("microchip_id", "NO_CHIP"),
            owner_public_key
        )

        self.pet_registry.create_pet_profile(
            pet_id,
            {**pet_data, "owner_public_key": owner_public_key}
        )

        tx = OrderedDict({
            "type": "PET_REGISTRATION",
            "pet_id": pet_id,
            "pet_name": pet_data.get("name"),
            "species": pet_data.get("species"),
            "microchip_id": pet_data.get("microchip_id"),
            "owner_public_key_hash": hashed_key(owner_public_key),
            "timestamp": time(),
        })

        self.unconfirmed_transactions.append(tx)
        return pet_id

    def add_vet_record_to_pet(self, pet_id, record, owner_public_key):
        pet = self.pet_registry.get_pet(pet_id)

        if not pet or pet["owner_public_key"] != owner_public_key:
            return False

        rc = self.pet_registry.add_vet_record(pet_id, record)

        tx = OrderedDict({
            "type": "VET_RECORD",
            "pet_id": pet_id,
            "record_id": rc["record_id"],
            "record_type": rc["record_type"],
            "vet_name": rc["vet_name"],
            "owner_public_key_hash": hashed_key(owner_public_key),
            "timestamp": time(),
        })

        self.unconfirmed_transactions.append(tx)
        return rc["record_id"]

    def view_pet_profile(self, pet_id, viewer_public_key):
        if pet_id not in self.pet_registry.pets:
            return False

        count = self.pet_registry.increment_view_count(pet_id)

        tx = OrderedDict({
            "type": "PROFILE_VIEW",
            "pet_id": pet_id,
            "viewer_public_key_hash": hashed_key(viewer_public_key),
            "view_count": count,
            "timestamp": time(),
        })

        self.unconfirmed_transactions.append(tx)
        return True

    def report_pet_lost(self, pet_id, owner_public_key, location, description):
        pet = self.pet_registry.get_pet(pet_id)

        if not pet or pet["owner_public_key"] != owner_public_key:
            return False

        self.pet_registry.mark_pet_lost(pet_id, location, description)

        tx = OrderedDict({
            "type": "PET_LOST",
            "pet_id": pet_id,
            "location": location,
            "description": description,
            "owner_public_key_hash": hashed_key(owner_public_key),
            "timestamp": time(),
        })

        self.unconfirmed_transactions.append(tx)
        return True

    def report_pet_found(self, pet_id, finder_public_key, finder_contact):
        pet = self.pet_registry.get_pet(pet_id)

        if not pet or pet["status"] != "lost":
            return False

        self.pet_registry.mark_pet_found(pet_id, finder_contact)

        tx = OrderedDict({
            "type": "PET_FOUND",
            "pet_id": pet_id,
            "finder_public_key_hash": hashed_key(finder_public_key),
            "finder_contact": finder_contact,
            "timestamp": time(),
        })

        self.unconfirmed_transactions.append(tx)
        return True

    # -----------------------------------------------------------
    # Blockchain History
    # -----------------------------------------------------------

    def get_pet_blockchain_history(self, pet_id):
        history = []

        for block in self.chain:
            for tx in block["transactions"]:
                if isinstance(tx, dict) and tx.get("pet_id") == pet_id:
                    entry = tx.copy()
                    entry["block_number"] = block["block_number"]
                    entry["block_timestamp"] = block["timestamp"]
                    history.append(entry)

        for tx in self.unconfirmed_transactions:
            if isinstance(tx, dict) and tx.get("pet_id") == pet_id:
                p = tx.copy()
                p["status"] = "pending"
                history.append(p)

        return history

    # -----------------------------------------------------------
    # Registry Stats
    # -----------------------------------------------------------

    def get_registry_stats(self):
        pets = list(self.pet_registry.pets.values())
        lost = [p for p in pets if p["status"] == "lost"]

        return {
            "total_pets": len(pets),
            "active_pets": len([p for p in pets if p["status"] == "active"]),
            "lost_pets": len(lost),
            "total_vet_records": sum(len(p["vet_records"]) for p in pets),
            "total_views": sum(p["view_count"] for p in pets),
        }


# -------------------------------------------------------------
# FLASK APP SETUP
# -------------------------------------------------------------

app = Flask(__name__)
CORS(app)

blockchain = Blockchain()


# -------------------------------------------------------------
# BASIC PAGE ROUTES
# -------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/configure")
def configure():
    return render_template("configure.html")


# -------------------------------------------------------------
# BLOCKCHAIN API
# -------------------------------------------------------------

@app.route("/transactions/get")
def get_pending():
    return jsonify({"transactions": blockchain.unconfirmed_transactions})


@app.route("/chain")
def full_chain():
    return jsonify({
        "chain": blockchain.chain,
        "length": len(blockchain.chain),
    })


@app.route("/mine")
def mine_block():
    nonce = blockchain.proof_of_work()

    blockchain.submit_transaction(
        sender_public_key=MINING_SENDER,
        recipient_public_key=blockchain.node_id,
        signature="",
        amount=MINING_REWARD
    )

    last_block = blockchain.chain[-1]
    previous_hash = blockchain.hash(last_block)

    block = blockchain.create_block(nonce, previous_hash)

    return jsonify({
        "message": "Block mined",
        "block_number": block["block_number"],
        "transactions": block["transactions"],
        "nonce": block["nonce"],
        "previous_hash": block["previous_hash"]
    })


# -------------------------------------------------------------
# NODE ROUTES
# -------------------------------------------------------------

@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    nodes = request.form.get("nodes", "").replace(" ", "").split(",")

    for node in nodes:
        blockchain.register_node(node)

    return jsonify({"message": "nodes added", "total_nodes": list(blockchain.nodes)})


@app.route("/nodes/resolve")
def resolve():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        return jsonify({"message": "chain replaced", "new_chain": blockchain.chain})
    return jsonify({"message": "authoritative chain", "chain": blockchain.chain})


# -------------------------------------------------------------
# PET FRONTEND PAGES
# -------------------------------------------------------------

@app.route("/pets")
def pets_home():
    return render_template("pets_home.html")


@app.route("/pet/register")
def pet_register_page():
    return render_template("pet_register.html")


@app.route("/pet/search")
def pet_search_page():
    return render_template("pet_search.html")


@app.route("/pet/<pet_id>")
def pet_profile_page(pet_id):
    return render_template("pet_profile.html", pet_id=pet_id)


# -------------------------------------------------------------
# PET API
# -------------------------------------------------------------

@app.route("/api/pet/register", methods=["POST"])
def api_register_pet():
    try:
        data = request.get_json()
        required = ["name", "owner_public_key", "owner_name", "owner_phone"]

        if not all(k in data for k in required):
            return jsonify({"error": "Missing required fields"}), 400

        pet_id = blockchain.register_pet(
            pet_data={
                "name": data["name"],
                "breed": data.get("breed", "Mixed"),
                "species": data.get("species", "dog"),
                "birth_date": data.get("birth_date", "Unknown"),
                "color": data.get("color", "Unknown"),
                "weight": data.get("weight", "Unknown"),
                "microchip_id": data.get("microchip_id", "NO_CHIP"),
                "photo": data.get("photo", ""),
                "owner_name": data["owner_name"],
                "owner_phone": data["owner_phone"],
                "owner_email": data.get("owner_email", "")
            },
            owner_public_key=data["owner_public_key"]
        )

        pet = blockchain.pet_registry.get_pet(pet_id)
        qr = blockchain.pet_registry.generate_qr(pet_id)

        return jsonify({
            "success": True,
            "pet_id": pet_id,
            "pet": pet,
            "qr_code": qr
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pet/<pet_id>", methods=["GET"])
def api_get_pet(pet_id):
    try:
        viewer_key = request.args.get("viewer_key", "ANON_VIEW")
        pet = blockchain.pet_registry.get_pet(pet_id)

        if not pet:
            return jsonify({"error": "Pet not found"}), 404

        blockchain.view_pet_profile(pet_id, viewer_key)
        history = blockchain.get_pet_blockchain_history(pet_id)
        qr = blockchain.pet_registry.generate_qr(pet_id)

        pet_safe = pet.copy()
        pet_safe.pop("owner_public_key", None)

        return jsonify({
            "success": True,
            "pet": pet_safe,
            "blockchain_history": history,
            "qr_code": qr
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pet/search", methods=["GET"])
def api_search():
    query = request.args.get("q", "")
    lost = request.args.get("lost_only", "false").lower() == "true"

    results = blockchain.pet_registry.search_pets(query or None, lost)
    return jsonify({"success": True, "count": len(results), "pets": results})


@app.route("/api/pet/<pet_id>/vet-record", methods=["POST"])
def api_vet_record(pet_id):
    try:
        data = request.get_json()
        required = ["owner_public_key", "record_type", "vet_name", "procedure"]

        if not all(k in data for k in required):
            return jsonify({"error": "Missing fields"}), 400

        rec_id = blockchain.add_vet_record_to_pet(
            pet_id,
            {
                "record_type": data["record_type"],
                "vet_name": data["vet_name"],
                "vet_clinic": data.get("vet_clinic", ""),
                "vet_phone": data.get("vet_phone", ""),
                "procedure": data["procedure"],
                "notes": data.get("notes", ""),
                "date": data.get("date", time()),
                "next_due_date": data.get("next_due_date"),
            },
            owner_public_key=data["owner_public_key"]
        )

        if not rec_id:
            return jsonify({"error": "Invalid owner key"}), 400

        return jsonify({"success": True, "record_id": rec_id})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/pet/<pet_id>/lost", methods=["POST"])
def api_lost(pet_id):
    data = request.get_json()
    if "owner_public_key" not in data:
        return jsonify({"error": "Missing owner key"}), 400

    ok = blockchain.report_pet_lost(
        pet_id,
        owner_public_key=data["owner_public_key"],
        location=data.get("location", ""),
        description=data.get("description", "")
    )

    if not ok:
        return jsonify({"error": "Ownership mismatch"}), 400

    return jsonify({"success": True, "message": "Marked as lost"})


@app.route("/api/pet/<pet_id>/found", methods=["POST"])
def api_found(pet_id):
    data = request.get_json()

    required = ["finder_public_key", "finder_contact"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400

    ok = blockchain.report_pet_found(
        pet_id,
        finder_public_key=data["finder_public_key"],
        finder_contact=data["finder_contact"]
    )

    if not ok:
        return jsonify({"error": "Pet not lost or missing"}), 400

    pet = blockchain.pet_registry.get_pet(pet_id)

    return jsonify({
        "success": True,
        "message": "Pet found report submitted",
        "owner_contact": {
            "name": pet["owner_name"],
            "phone": pet["owner_phone"],
            "email": pet["owner_email"]
        }
    })


# -------------------------------------------------------------
# STATS API (for your frontend dashboard)
# -------------------------------------------------------------

@app.route("/stats")
def stats():
    chain = blockchain.chain
    pending = blockchain.unconfirmed_transactions

    total_mined_tx = sum(len(block["transactions"]) for block in chain)

    return jsonify({
        "total_blocks": len(chain),
        "total_transactions": total_mined_tx,
        "pending_transactions": len(pending),
        "total_nodes": len(blockchain.nodes),
        "avg_transactions_per_block": (total_mined_tx / len(chain)) if len(chain) else 0,
        "difficulty": MINING_DIFFICULTY,
        "mining_reward": MINING_REWARD
    })


# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-p", "--port", default=5001, type=int)
    args = parser.parse_args()

    app.run(host="127.0.0.1", port=args.port, debug=True)
