# Pet Blockchain System

## Overview

A blockchain-based pet registry system that provides secure, immutable record-keeping for pet ownership, veterinary records, and lost & found tracking.

## What It Does

- **Pet Registration** - Register pets with complete profiles (name, breed, microchip ID, owner info)
- **Veterinary Records** - Track medical history, vaccinations, and treatments
- **Lost & Found** - Report lost pets and facilitate reunions with QR code scanning
- **Blockchain Security** - Immutable audit trail of all pet-related events
- **QR Code Generation** - Unique QR codes for each pet profile
- **Search** - Find pets by name, breed, or microchip ID

## System Components

### 1. `pet_blockchain.py` - Core Blockchain Engine
- Blockchain implementation with Proof of Work mining
- PetRegistry class for managing pet data
- Cryptographic transaction verification
- Flask API server

### 2. `blockchain_client.py` - Client Application
- User-facing web interface
- Imports and uses Blockchain from pet_blockchain.py
- Additional API endpoints for frontend

## Installation

```bash
# Install dependencies
pip install flask flask-cors pycryptodome qrcode pillow

# Or use requirements.txt
pip install -r requirements.txt
```

## How to Run

### Option 1: Run the blockchain server
```bash
cd my_blockchain
python pet_blockchain.py -p 5001
```

### Option 2: Run the client application
```bash
cd blockchain_client
python blockchain_client.py
```

### Run multiple nodes (for testing)
```bash
# Terminal 1
python pet_blockchain.py -p 5001

# Terminal 2
python pet_blockchain.py -p 5002

# Terminal 3
python pet_blockchain.py -p 5003
```

## Usage

### Access the Web Interface
Open your browser and navigate to:
```
http://localhost:5001
```

### API Examples

**Register a pet:**
```bash
curl -X POST http://localhost:5001/api/pet/register \
  -H "Content-Type: application/json" \
  -d '{
    "pet_data": {
      "name": "Max",
      "breed": "Golden Retriever",
      "species": "dog",
      "microchip_id": "123456789",
      "owner_name": "John Doe",
      "owner_phone": "+1234567890"
    },
    "owner_public_key": "test_key_123"
  }'
```

**Search for pets:**
```bash
curl -X GET "http://localhost:5001/api/pet/search?q=golden"
```

**Mine a block:**
```bash
curl http://localhost:5001/api/mine
```

**View blockchain:**
```bash
curl http://localhost:5001/api/chain
```

## Key Features Explained

### Blockchain Technology
- Each block contains transactions and is linked to the previous block
- Proof of Work mining ensures security
- Immutable record of all pet-related events

### Dual Storage System
- **Registry (In-Memory)**: Fast searches, current pet status
- **Blockchain (Immutable)**: Permanent audit trail, tamper-proof history

### Security
- Cryptographic signatures verify transaction authenticity
- Owner public keys are hashed for privacy
- Only owners can modify their pet records

### Lost & Found Workflow
1. Owner reports pet lost → Status updated + blockchain event
2. Finder scans QR code → Views pet profile
3. Finder reports found → Owner contact info revealed
4. All events recorded on blockchain

## API Endpoints

### Blockchain Operations
- `GET /api/chain` - View entire blockchain
- `GET /api/mine` - Mine pending transactions
- `POST /api/nodes/register` - Register peer nodes

### Pet Management
- `POST /api/pet/register` - Register new pet
- `GET /api/pet/<pet_id>` - Get pet profile
- `GET /api/pet/search` - Search pets
- `POST /api/pet/<pet_id>/vet-record` - Add veterinary record
- `POST /api/pet/<pet_id>/lost` - Report pet lost
- `POST /api/pet/<pet_id>/found` - Report pet found
- `GET /api/pet/<pet_id>/history` - Get blockchain history

### Statistics
- `GET /api/registry/stats` - Registry statistics
- `GET /stats` - Blockchain statistics

## Configuration

Edit constants in `pet_blockchain.py`:
```python
MINING_DIFFICULTY = 2  # Number of leading zeros required (higher = harder)
MINING_REWARD = 1      # Coins awarded per mined block
```

## Project Structure

```
.
├── my_blockchain/
│   ├── pet_blockchain.py      # Core blockchain engine
│   ├── templates/             # HTML templates
│   └── static/                # CSS and assets
├── blockchain_client/
│   ├── blockchain_client.py   # Client application
│   ├── templates/             # HTML templates
│   └── static/                # CSS and assets
└── requirements.txt           # Python dependencies
```

## License

This project is for educational purposes.
