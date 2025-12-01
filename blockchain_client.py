from flask import Flask, jsonify, request, render_template, redirect
# from blockchain import Blockchain
import uuid
import qrcode
import io
import base64
import sys, os

# Go UP one directory (to project root)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from my_blockchain.pet_blockchain import Blockchain


app = Flask(__name__)
node_identifier = str(uuid.uuid4()).replace("-", "")

# Initialize blockchain
blockchain = Blockchain()

##############################################
# FRONTEND PAGES (HTML Templates)
##############################################

@app.route("/")
def home():
    return render_template("pets_home.html")

@app.route("/pet/search")
def pet_search_page():
    return render_template("pet_search.html")

@app.route("/pet/register")
def pet_register_page():
    return render_template("pet_register.html")

@app.route("/pet/<pet_id>")
def pet_profile_page(pet_id):
    pet = blockchain.pet_registry.get_pet(pet_id)
    if not pet:
        return "Pet not found", 404
    return render_template("pet_profile.html", pet=pet)

@app.route("/explorer")
def explorer_page():
    return render_template("block_explorer.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

##############################################
# BLOCKCHAIN REST API
##############################################

@app.route("/api/chain", methods=["GET"])
def full_chain():
    return jsonify({
        "chain": blockchain.chain,
        "length": len(blockchain.chain)
    }), 200

@app.route("/api/mine", methods=["GET"])
def mine_block():
    # mine the pending transactions
    last_block = blockchain.chain[-1]
    previous_hash = blockchain.hash(last_block)

    nonce = blockchain.proof_of_work()
    block = blockchain.create_block(nonce, previous_hash)

    return jsonify({
        "message": "Block mined successfully",
        "block": block
    }), 201

@app.route("/api/nodes/register", methods=["POST"])
def register_nodes():
    values = request.get_json()
    nodes = values.get("nodes")

    if nodes is None:
        return jsonify({"error": "Please supply a valid list of nodes"}), 400

    for node in nodes:
        blockchain.register_node(node)

    return jsonify({
        "message": "New nodes added",
        "total_nodes": list(blockchain.nodes)
    }), 201

@app.route("/api/nodes/resolve", methods=["GET"])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            "message": "Our chain was replaced",
            "new_chain": blockchain.chain
        }
    else:
        response = {
            "message": "Our chain is authoritative",
            "chain": blockchain.chain
        }
    return jsonify(response), 200


##############################################
# PET REGISTRY API
##############################################

@app.route("/api/pet/register", methods=["POST"])
def api_register_pet():
    data = request.get_json()

    pet_data = data.get("pet_data")
    owner_key = data.get("owner_public_key")

    pet_id = blockchain.register_pet(pet_data, owner_key)

    return jsonify({
        "message": "Pet registered successfully",
        "pet_id": pet_id
    }), 201


@app.route("/api/pet/search", methods=["POST"])
def api_search_pet():
    query = request.get_json().get("query", "").lower()

    results = blockchain.pet_registry.search_pets(query)
    return jsonify(results), 200


@app.route("/api/pet/<pet_id>/profile", methods=["GET"])
def api_pet_profile(pet_id):
    pet = blockchain.pet_registry.get_pet(pet_id)
    if not pet:
        return jsonify({"error": "Pet not found"}), 404

    return jsonify(pet), 200


@app.route("/api/pet/<pet_id>/view", methods=["POST"])
def api_view_pet(pet_id):
    viewer_key = request.get_json().get("viewer_public_key")
    success = blockchain.view_pet_profile(pet_id, viewer_key)

    return jsonify({"success": success}), 200


@app.route("/api/pet/<pet_id>/lost", methods=["POST"])
def api_report_lost(pet_id):
    data = request.get_json()
    owner_key = data.get("owner_public_key")
    location = data.get("location")
    description = data.get("description")

    success = blockchain.report_pet_lost(
        pet_id, owner_key, location, description
    )

    return jsonify({"success": success}), 200


@app.route("/api/pet/<pet_id>/found", methods=["POST"])
def api_report_found(pet_id):
    data = request.get_json()
    finder_key = data.get("finder_public_key")
    contact = data.get("finder_contact")

    success = blockchain.report_pet_found(pet_id, finder_key, contact)

    return jsonify({"success": success}), 200


@app.route("/api/pet/<pet_id>/vet", methods=["POST"])
def api_add_vet_record(pet_id):
    data = request.get_json()
    record = data.get("record")
    owner_key = data.get("owner_public_key")

    success = blockchain.add_vet_record_to_pet(pet_id, record, owner_key)

    return jsonify({"success": success}), 200


@app.route("/api/pet/<pet_id>/history", methods=["GET"])
def api_pet_history(pet_id):
    history = blockchain.get_pet_blockchain_history(pet_id)
    return jsonify(history), 200


@app.route("/api/registry/stats", methods=["GET"])
def api_registry_stats():
    stats = blockchain.get_registry_stats()
    return jsonify(stats), 200


##############################################
# QR CODE GENERATOR FOR PET PROFILE
##############################################

@app.route("/api/pet/<pet_id>/qrcode", methods=["GET"])
def api_pet_qr(pet_id):
    img = qrcode.make(f"https://yourdomain.com/pet/{pet_id}")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    return jsonify({"qr_code": qr_b64})


##############################################
# RUN APPLICATION
##############################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
