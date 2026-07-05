# CryptoCurrency Simulation

A portfolio-quality cryptocurrency and blockchain simulation built with **Python**, **Flask**, **ECDSA cryptography**, **Machine Learning**, and **Generative AI**.

> Designed to demonstrate blockchain fundamentals, REST API design, cryptographic security, ML-based fraud detection, and AI-powered data explanation — all in a single project.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [API Endpoints](#api-endpoints)
- [Machine Learning — Fraud Detection](#machine-learning--fraud-detection)
- [Generative AI — Block Explanation](#generative-ai--block-explanation)
- [Project Structure](#project-structure)
- [Future Scope](#future-scope)
- [Screenshots](#screenshots)

---

## Features

| Feature | Details |
|---|---|
| **Dual Blockchain** | Legacy dict-based chain (dashboard) + CryptoSim ECDSA chain (REST API) |
| **ECDSA Wallets** | Elliptic Curve keypairs, SHA-256 addresses |
| **Digital Signatures** | Every transaction is signed and verified |
| **Proof of Work Mining** | Configurable difficulty, nonce-based hash puzzle |
| **Blockchain Persistence** | JSON-based chain storage survives server restarts |
| **ML Fraud Detection** | Isolation Forest trained on real chain data |
| **AI Block Explanation** | Mock AI engine (OpenAI-ready when API key provided) |
| **Security Report** | Chain validity, flagged transactions, wallet stats |
| **REST API** | Full CryptoSim API tested via VS Code REST Client |
| **Web Dashboard** | Login, signup, send, mine, explorer, history tabs |

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│                    Flask App (app.py)            │
│                                                  │
│  ┌─────────────────┐   ┌───────────────────────┐ │
│  │  Legacy Chain   │   │   CryptoSim Chain     │ │
│  │  (dashboard)    │   │   (REST API)          │ │
│  │  blockchain_    │   │   cryptosim_chain.json│ │
│  │  data.json      │   │                       │ │
│  └─────────────────┘   └───────────────────────┘ │
│                                                  │
│  ┌──────────────┐   ┌─────────────────────────┐  │
│  │  ML Module   │   │   AI Explainer Module   │  │
│  │  Isolation   │   │   Mock / OpenAI GPT     │  │
│  │  Forest      │   │                         │  │
│  └──────────────┘   └─────────────────────────┘  │
└──────────────────────────────────────────────────┘

blockchain/
  wallet.py       ← ECDSA key generation, signing
  transaction.py  ← TX creation, signature verification
  block.py        ← Block structure, SHA-256 hash
  blockchain.py   ← Chain management, PoW, validation

ai/
  fraud_detection.py  ← Isolation Forest, real sender stats
  explainer.py        ← Mock + OpenAI block explainer
```

---

## Tech Stack

- **Backend**: Python 3, Flask
- **Cryptography**: ECDSA (secp256k1), SHA-256
- **Machine Learning**: scikit-learn (Isolation Forest)
- **AI Explanation**: OpenAI SDK v1+ (mock fallback included)
- **Persistence**: JSON files
- **Frontend**: HTML, CSS, JavaScript (Toastify, QRCode.js)
- **Testing**: VS Code REST Client (`test.http`)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/cryptocurrency-simulation.git
cd "CryptoCurrency Simulation"

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install flask werkzeug ecdsa scikit-learn numpy openai
```

### Optional — Enable Real OpenAI Explanations

```bash
# Set your OpenAI API key as an environment variable
set OPENAI_API_KEY=sk-...       # Windows CMD
# export OPENAI_API_KEY=sk-...  # macOS / Linux
```

If the key is not set, the project uses a built-in mock explainer automatically.

---

## Running the Project

```bash
cd "CryptoCurrency Simulation"
python app.py
```

Open your browser at **http://127.0.0.1:5000**

---

## API Endpoints

### CryptoSim API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/cryptosim/create_wallet` | Generate a new ECDSA wallet |
| POST | `/api/cryptosim/send_transaction` | Sign and submit a transaction |
| POST | `/api/cryptosim/mine` | Mine pending transactions |
| GET  | `/api/cryptosim/chain` | Retrieve the full blockchain |
| GET  | `/api/cryptosim/balances` | Get all wallet balances |
| POST | `/api/cryptosim/analyze` | Fraud analysis on a transaction |
| GET  | `/api/cryptosim/explain/<index>` | AI explanation of a block |
| GET  | `/api/cryptosim/security_report` | Full chain security audit |

### Legacy API (Web Dashboard)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | User login |
| POST | `/signup` | User registration |
| GET  | `/logout` | Logout |
| POST | `/send` | Send coins |
| POST | `/mine` | Mine a block |
| GET  | `/chain` | Get chain |
| GET  | `/balances` | Get balances |
| GET  | `/transactions` | Transaction history |

---

## Machine Learning — Fraud Detection

The `FraudDetector` class uses **Isolation Forest** (an unsupervised anomaly detection algorithm) to score transactions.

### Features used

| Feature | Source |
|---------|--------|
| `amount` | Transaction amount |
| `sender_total_sent` | Computed from confirmed chain history |
| `sender_total_received` | Computed from confirmed chain history |
| `frequency` | Number of prior sends from this address |

### Workflow

1. On startup, the model is trained on all confirmed chain transactions.
2. Before each new transaction is accepted, the sender's real stats are fetched from the chain.
3. A risk score is computed. Negative scores are flagged as suspicious and rejected.
4. The model retrains after each new transaction and each new mined block.

---

## Generative AI — Block Explanation

The `explain_block()` function in `ai/explainer.py`:

- **With `OPENAI_API_KEY` set**: Uses OpenAI `gpt-4o-mini` to explain the block in natural language.
- **Without API key**: Falls back to a deterministic mock engine that produces structured explanations covering transactions, mining rewards, fraud flags, and signature verification.

---

## Project Structure

```
CryptoCurrency Simulation/
│
├── app.py                      # Flask application, all routes
│
├── blockchain/
│   ├── block.py                # Block class with PoW hashing
│   ├── blockchain.py           # Chain class with full validation
│   ├── transaction.py          # ECDSA-signed transaction
│   └── wallet.py               # ECDSA wallet, signing
│
├── ai/
│   ├── fraud_detection.py      # Isolation Forest fraud detector
│   └── explainer.py            # Mock + OpenAI block explainer
│
├── templates/
│   └── index.html              # Web dashboard
│
├── static/
│   ├── style.css
│   └── script.js
│
├── blockchain_data.json        # Legacy chain persistence
├── cryptosim_chain.json        # CryptoSim chain persistence
├── users.json                  # Registered users
├── test.http                   # REST Client test file
└── README.md
```

---

## Future Scope

- [ ] P2P networking — multiple nodes with consensus
- [ ] Merkle tree for transaction hashing
- [ ] Wallet import/export via private key
- [ ] Real-time dashboard with WebSockets
- [ ] Smart contract simulation layer
- [ ] Replace JSON persistence with SQLite
- [ ] Docker containerization
- [ ] Full ML training pipeline with labelled fraud dataset

---

## Screenshots

> _Add screenshots of the dashboard, REST API responses, and security report here._

---

## Author

Built as a portfolio project demonstrating blockchain, cryptography, REST APIs, machine learning, and generative AI in Python.
