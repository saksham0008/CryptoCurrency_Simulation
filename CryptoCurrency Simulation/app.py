"""
app.py  –  CryptoCurrency Simulation
=====================================
Two independent blockchains run side-by-side:

  Legacy    – simple dict-based blockchain used by the HTML dashboard
  CryptoSim – ECDSA-signed, ML-analysed, persistence-backed blockchain
               exposed via  /api/cryptosim/*  REST endpoints
"""

# ── Imports ──────────────────────────────────────────────────────────────────
from ai.fraud_detection import FraudDetector
from ai.explainer import explain_block
from blockchain.wallet import Wallet
from blockchain.transaction import Transaction
from blockchain.blockchain import Blockchain as NewBlockchain
from blockchain.block import Block as CryptoBlock

from flask import (
    Flask, request, render_template,
    redirect, url_for, jsonify, session,
)
from werkzeug.security import generate_password_hash, check_password_hash
import json
import time
from hashlib import sha256
from uuid import uuid4
from collections import defaultdict
import os

# ── Flask app ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "your_secret_key_here"   # replace in production

# ── File paths ────────────────────────────────────────────────────────────────
BLOCKCHAIN_FILE = "blockchain_data.json"
USERS_FILE      = "users.json"
CRYPTOSIM_FILE  = "cryptosim_chain.json"

# ─────────────────────────────────────────────────────────────────────────────
#  LEGACY BLOCKCHAIN  (used by the web dashboard)
# ─────────────────────────────────────────────────────────────────────────────

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash,
                 nonce=0, hash=None):
        self.index          = index
        self.timestamp      = timestamp
        self.transactions   = transactions
        self.previous_hash  = previous_hash
        self.nonce          = nonce
        self.hash           = hash if hash else self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(
            {
                "index":         self.index,
                "timestamp":     self.timestamp,
                "transactions":  self.transactions,
                "previous_hash": self.previous_hash,
                "nonce":         self.nonce,
            },
            sort_keys=True,
        )
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain               = []
        self.current_transactions = []
        self.difficulty          = 3
        self.balances            = defaultdict(float)
        self.load_chain()

    def create_genesis_block(self):
        self.chain.append(Block(0, time.time(), [], "0"))

    def get_last_block(self):
        return self.chain[-1]

    def add_transaction(self, sender, recipient, amount):
        amount = float(amount)
        if sender != "MINER" and self.balances[sender] < amount:
            return False
        self.current_transactions.append(
            {
                "sender":    sender,
                "recipient": recipient,
                "amount":    amount,
                "timestamp": time.time(),
            }
        )
        if sender != "MINER":
            self.balances[sender] -= amount
        self.balances[recipient] += amount
        return True

    def proof_of_work(self, block):
        block.nonce = 0
        block.hash  = block.compute_hash()
        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1
            block.hash  = block.compute_hash()
        return block.hash

    def mine_block(self, miner):
        if not self.current_transactions:
            return None
        self.add_transaction("MINER", miner, 10.0)
        last = self.get_last_block()
        new_block = Block(
            index=last.index + 1,
            timestamp=time.time(),
            transactions=self.current_transactions[:],
            previous_hash=last.hash,
        )
        new_block.hash = self.proof_of_work(new_block)
        self.chain.append(new_block)
        self.current_transactions = []
        self.save_chain()
        return new_block

    def to_dict(self):
        return [block.__dict__ for block in self.chain]

    def get_transaction_history(self):
        history = []
        for block in self.chain:
            for txn in block.transactions:
                t = txn.copy()
                t["block"] = block.index
                history.append(t)
        return history

    def save_chain(self):
        with open(BLOCKCHAIN_FILE, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def load_chain(self):
        if os.path.exists(BLOCKCHAIN_FILE):
            with open(BLOCKCHAIN_FILE, "r") as f:
                chain_data = json.load(f)
            for bd in chain_data:
                block = Block(
                    index=bd["index"],
                    timestamp=bd["timestamp"],
                    transactions=bd["transactions"],
                    previous_hash=bd["previous_hash"],
                    nonce=bd["nonce"],
                    hash=bd.get("hash"),
                )
                self.chain.append(block)
            # Rebuild balances
            for block in self.chain:
                for txn in block.transactions:
                    s, r, a = txn["sender"], txn["recipient"], txn["amount"]
                    if s != "MINER":
                        self.balances[s] -= a
                    self.balances[r] += a
        else:
            self.create_genesis_block()


# ── Instantiate both blockchains ──────────────────────────────────────────────
blockchain     = Blockchain()               # legacy
new_blockchain = NewBlockchain(difficulty=3)  # CryptoSim

# ── Fraud detector ────────────────────────────────────────────────────────────
fraud_detector = FraudDetector()

# ── In-memory wallet store for CryptoSim ─────────────────────────────────────
crypto_wallets: dict[str, Wallet] = {}   # address -> Wallet object
node_id = str(uuid4()).replace("-", "")

# ─────────────────────────────────────────────────────────────────────────────
#  CryptoSim persistence helpers
# ─────────────────────────────────────────────────────────────────────────────

def save_cryptosim_chain():
    data = []
    for block in new_blockchain.chain:
        data.append(
            {
                "index":         block.index,
                "timestamp":     block.timestamp,
                "transactions":  block.transactions,
                "previous_hash": block.previous_hash,
                "nonce":         block.nonce,
                "hash":          block.hash,
            }
        )
    with open(CRYPTOSIM_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_cryptosim_chain():
    if os.path.exists(CRYPTOSIM_FILE):
        with open(CRYPTOSIM_FILE, "r") as f:
            chain_data = json.load(f)

        if chain_data:
            new_blockchain.chain = []
            for bd in chain_data:
                block = CryptoBlock(
                    index=bd["index"],
                    transactions=bd["transactions"],
                    previous_hash=bd["previous_hash"],
                    nonce=bd["nonce"],
                    timestamp=bd["timestamp"],
                )
                block.hash = bd["hash"]
                new_blockchain.chain.append(block)

    # Always ensure genesis block exists
    if not new_blockchain.chain:
        new_blockchain.create_genesis_block()


# ── Retrain fraud detector from chain on startup ──────────────────────────────

def retrain_fraud_detector():
    """Train the Isolation Forest on all confirmed CryptoSim chain data."""
    fraud_detector.train_from_chain(new_blockchain.chain)


# ── Startup: load chain then retrain ─────────────────────────────────────────
load_cryptosim_chain()
retrain_fraud_detector()

# ─────────────────────────────────────────────────────────────────────────────
#  User management
# ─────────────────────────────────────────────────────────────────────────────
users: dict = {}

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_users():
    global users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)

load_users()

# ─────────────────────────────────────────────────────────────────────────────
#  Utility: compute real sender stats
# ─────────────────────────────────────────────────────────────────────────────

def get_sender_stats(sender: str) -> dict:
    """Return live sender stats from the confirmed CryptoSim chain."""
    return FraudDetector.compute_sender_stats(sender, new_blockchain.chain)


def calculate_cryptosim_balances() -> dict:
    balances: dict[str, float] = defaultdict(float)
    for block in new_blockchain.chain:
        for tx in block.transactions:
            s, r, a = tx["sender"], tx["recipient"], float(tx["amount"])
            if s != "MINER":
                balances[s] -= a
            balances[r] += a
    return dict(balances)

# ─────────────────────────────────────────────────────────────────────────────
#  LEGACY ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login_page"))
    return render_template(
        "index.html",
        username=session["username"],
        wallet=session["wallet"],
    )

@app.route("/login_page")
def login_page():
    return render_template("index.html", username=None, wallet=None)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"].strip()
    password = request.form["password"].strip()
    user     = users.get(username)

    if not user:
        return jsonify({"success": False, "message": "User does not exist."})
    if not check_password_hash(user["password"], password):
        return jsonify({"success": False, "message": "Incorrect password."})

    session["username"] = username
    session["wallet"]   = user["wallet"]
    return jsonify({"success": True, "wallet": user["wallet"]})

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"].strip()
    password = request.form["password"].strip()

    if username in users:
        return jsonify({"success": False, "message": "Username already exists."})

    wallet_id = str(uuid4())[:16]
    users[username] = {
        "password": generate_password_hash(password),
        "wallet":   wallet_id,
    }
    blockchain.balances[wallet_id] = 10.0
    save_users()
    return jsonify({"success": True, "wallet": wallet_id})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.route("/send", methods=["POST"])
def send():
    if "wallet" not in session:
        return redirect(url_for("login_page"))
    success = blockchain.add_transaction(
        request.form["sender"],
        request.form["recipient"],
        request.form["amount"],
    )
    if not success:
        return "Insufficient funds!", 400
    blockchain.save_chain()
    return redirect(url_for("home"))

@app.route("/mine", methods=["POST"])
def mine():
    if "wallet" not in session:
        return redirect(url_for("login_page"))
    new_block = blockchain.mine_block(request.form["miner"])
    if not new_block:
        return "Nothing to mine!"
    return redirect(url_for("home"))

@app.route("/chain")
def get_chain():
    return jsonify(blockchain.to_dict())

@app.route("/balances")
def get_balances():
    return jsonify(blockchain.balances)

@app.route("/transactions")
def get_transactions():
    return jsonify(blockchain.get_transaction_history())

@app.route("/pending")
def get_pending():
    return jsonify(blockchain.current_transactions)

@app.route("/create_wallet")
def create_wallet():
    new_wallet = str(uuid4())[:16]
    blockchain.balances[new_wallet] = 10.0
    return jsonify({"wallet": new_wallet})

@app.route("/api/send", methods=["POST"])
def api_send():
    if "wallet" not in session:
        return jsonify({"success": False, "message": "User not logged in."}), 401
    success = blockchain.add_transaction(
        request.form["sender"],
        request.form["recipient"],
        request.form["amount"],
    )
    if not success:
        return jsonify({"success": False, "message": "Insufficient funds!"})
    blockchain.save_chain()
    return jsonify({"success": True, "message": "Transaction successful."})

# ─────────────────────────────────────────────────────────────────────────────
#  CRYPTOSIM REST ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/cryptosim/create_wallet", methods=["POST"])
def cryptosim_create_wallet():
    """Create a new ECDSA wallet and return address + public key."""
    wallet  = Wallet()
    address = wallet.get_address()
    crypto_wallets[address] = wallet

    return jsonify(
        {
            "address":    address,
            "public_key": wallet.get_public_key(),
        }
    )


@app.route("/api/cryptosim/send_transaction", methods=["POST"])
def cryptosim_send_transaction():
    """
    Sign and submit a transaction.
    Computes real sender stats from chain history before fraud scoring.
    Retrains the model after each accepted transaction.
    """
    data      = request.get_json()
    sender    = data.get("sender")
    recipient = data.get("recipient")
    amount    = data.get("amount")

    if not sender or not recipient or amount is None:
        return jsonify({"error": "sender, recipient, and amount are required"}), 400

    if sender not in crypto_wallets:
        return jsonify({"error": "Sender wallet not found. Create a wallet first."}), 400

    # --- Real sender stats from chain ---
    stats = get_sender_stats(sender)

    features = [
        float(amount),
        stats["total_sent"],
        stats["total_received"],
        float(stats["frequency"]),
    ]

    risk_score = fraud_detector.predict(features)
    flagged    = risk_score < 0

    if flagged:
        return jsonify(
            {
                "error":      "Transaction flagged as suspicious by ML model.",
                "risk_score": risk_score,
                "flagged":    True,
            }
        ), 400

    # --- Sign and add ---
    tx = Transaction(sender, recipient, float(amount))
    tx.sign_transaction(crypto_wallets[sender])
    tx.risk_score = risk_score
    tx.flagged    = flagged

    added = new_blockchain.add_transaction(tx)
    if not added:
        return jsonify({"error": "Invalid transaction signature."}), 400

    # Retrain fraud detector with latest chain + this new pending tx
    retrain_fraud_detector()

    return jsonify(
        {
            "message":    "Signed transaction submitted successfully.",
            "risk_score": risk_score,
            "flagged":    False,
        }
    )


@app.route("/api/cryptosim/mine", methods=["POST"])
def cryptosim_mine():
    """Mine all pending transactions into a new block."""
    data  = request.get_json()
    miner = data.get("miner")

    if not miner:
        return jsonify({"error": "miner address is required"}), 400

    block = new_blockchain.mine_pending_transactions(miner)
    if not block:
        return jsonify({"message": "No pending transactions to mine."})

    save_cryptosim_chain()
    retrain_fraud_detector()   # retrain after confirmed block

    return jsonify(
        {
            "message":     "Block mined successfully.",
            "block_index": block.index,
            "hash":        block.hash,
            "transactions": len(block.transactions),
        }
    )


@app.route("/api/cryptosim/chain", methods=["GET"])
def cryptosim_chain():
    """Return the full CryptoSim chain."""
    chain_data = [
        {
            "index":         block.index,
            "timestamp":     block.timestamp,
            "transactions":  block.transactions,
            "previous_hash": block.previous_hash,
            "hash":          block.hash,
        }
        for block in new_blockchain.chain
    ]
    return jsonify(chain_data)


@app.route("/api/cryptosim/balances", methods=["GET"])
def cryptosim_balances():
    """Return current balances across the CryptoSim chain."""
    return jsonify(calculate_cryptosim_balances())


@app.route("/api/cryptosim/analyze", methods=["POST"])
def analyze_transaction():
    """
    Standalone fraud analysis endpoint.
    Accepts manual feature values OR auto-computes sender stats.
    """
    data   = request.get_json()
    amount = data.get("amount", 0)
    sender = data.get("sender")

    if sender:
        stats = get_sender_stats(sender)
        features = [
            float(amount),
            stats["total_sent"],
            stats["total_received"],
            float(stats["frequency"]),
        ]
    else:
        features = [
            float(amount),
            float(data.get("sender_total_sent",     0)),
            float(data.get("sender_total_received", 0)),
            float(data.get("frequency",             1)),
        ]

    score = fraud_detector.predict(features)

    return jsonify(
        {
            "risk_score": score,
            "flagged":    score < 0,
            "features_used": {
                "amount":               features[0],
                "sender_total_sent":    features[1],
                "sender_total_received": features[2],
                "frequency":            features[3],
            },
        }
    )


@app.route("/api/cryptosim/explain/<int:block_index>", methods=["GET"])
def explain(block_index):
    """Return an AI-generated (or mock) explanation of a block."""
    if block_index >= len(new_blockchain.chain):
        return jsonify({"error": f"Block {block_index} not found."}), 404

    block = new_blockchain.chain[block_index]

    explanation = explain_block(
        {
            "block_index":  block_index,
            "transactions": block.transactions,
        }
    )

    return jsonify(
        {
            "block_index":  block_index,
            "ai_explanation": explanation,
        }
    )


@app.route("/api/cryptosim/security_report", methods=["GET"])
def security_report():
    """
    Pure-backend security report.  No AI involved.

    Returns:
      - chain_length
      - chain_valid  (full validation with signature checks)
      - validation_errors
      - total_transactions
      - flagged_transactions  (count + list)
      - highest_risk_transaction
      - wallet_statistics
      - pending_transactions_count
    """
    # --- Chain validation ---
    validation = new_blockchain.is_chain_valid()

    # --- Aggregate transaction data ---
    all_tx      = []
    flagged_tx  = []
    highest_risk = None

    for block in new_blockchain.chain:
        for tx in block.transactions:
            if tx.get("sender") == "MINER":
                continue  # skip reward transactions

            all_tx.append(tx)

            if tx.get("flagged", False):
                flagged_tx.append(
                    {
                        "sender":     tx.get("sender"),
                        "recipient":  tx.get("recipient"),
                        "amount":     tx.get("amount"),
                        "risk_score": tx.get("risk_score"),
                    }
                )

            # Track highest risk (most negative score = most anomalous)
            rs = tx.get("risk_score")
            if rs is not None:
                if highest_risk is None or rs < highest_risk["risk_score"]:
                    highest_risk = {
                        "sender":     tx.get("sender"),
                        "recipient":  tx.get("recipient"),
                        "amount":     tx.get("amount"),
                        "risk_score": rs,
                    }

    # --- Wallet statistics ---
    balances = calculate_cryptosim_balances()
    wallet_stats = {
        "total_wallets":  len(balances),
        "top_balances":   sorted(
            [{"address": k, "balance": v} for k, v in balances.items()],
            key=lambda x: x["balance"],
            reverse=True,
        )[:5],
    }

    return jsonify(
        {
            "chain_length":              len(new_blockchain.chain),
            "chain_valid":               validation["valid"],
            "validation_errors":         validation["errors"],
            "total_transactions":        len(all_tx),
            "flagged_transactions_count": len(flagged_tx),
            "flagged_transactions":      flagged_tx,
            "highest_risk_transaction":  highest_risk,
            "wallet_statistics":         wallet_stats,
            "pending_transactions_count": len(new_blockchain.pending_transactions),
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)
