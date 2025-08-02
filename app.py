from flask import Flask, request, render_template, redirect, url_for, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import time
from hashlib import sha256
from uuid import uuid4
from collections import defaultdict
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key!

BLOCKCHAIN_FILE = 'blockchain_data.json'
USERS_FILE = 'users.json'

users = {}  # username -> {password, wallet}

# ---------------- Blockchain Classes ----------------
class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.difficulty = 3
        self.balances = defaultdict(float)
        self.load_chain()

    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), [], "0")
        self.chain.append(genesis_block)

    def get_last_block(self):
        return self.chain[-1]

    def add_transaction(self, sender, recipient, amount):
        amount = float(amount)
        if sender != "MINER" and self.balances[sender] < amount:
            return False
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': time.time()
        })
        if sender != "MINER":
            self.balances[sender] -= amount
        self.balances[recipient] += amount
        return True

    def proof_of_work(self, block):
        block.nonce = 0
        block.hash = block.compute_hash()
        while not block.hash.startswith('0' * self.difficulty):
            block.nonce += 1
            block.hash = block.compute_hash()
        return block.hash

    def mine_block(self, miner):
        if not self.current_transactions:
            return None
        self.add_transaction("MINER", miner, 10.0)
        last_block = self.get_last_block()
        new_block = Block(index=last_block.index + 1,
                          timestamp=time.time(),
                          transactions=self.current_transactions[:],
                          previous_hash=last_block.hash)
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
                txn_copy = txn.copy()
                txn_copy['block'] = block.index
                history.append(txn_copy)
        return history

    def save_chain(self):
        with open(BLOCKCHAIN_FILE, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def load_chain(self):
        if os.path.exists(BLOCKCHAIN_FILE):
            with open(BLOCKCHAIN_FILE, 'r') as f:
                chain_data = json.load(f)
                for block_data in chain_data:
                    block = Block(**block_data)
                    self.chain.append(block)
                for block in self.chain:
                    for txn in block.transactions:
                        sender = txn['sender']
                        recipient = txn['recipient']
                        amount = txn['amount']
                        if sender != "MINER":
                            self.balances[sender] -= amount
                        self.balances[recipient] += amount
        else:
            self.create_genesis_block()

# ---------------- App Initialization ----------------
blockchain = Blockchain()
node_id = str(uuid4()).replace('-', '')

# ---------------- User Management ----------------
def save_users():
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def load_users():
    global users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)

load_users()

# ---------------- Routes ----------------
@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html', username=session['username'], wallet=session['wallet'])

@app.route('/login_page')
def login_page():
    return render_template('index.html', username=None, wallet=None)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username'].strip()
    password = request.form['password'].strip()
    user = users.get(username)

    if not user:
        return jsonify({'success': False, 'message': 'User does not exist.'})
    if not check_password_hash(user['password'], password):
        return jsonify({'success': False, 'message': 'Incorrect password.'})

    session['username'] = username
    session['wallet'] = user['wallet']
    return jsonify({'success': True, 'wallet': user['wallet']})

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username'].strip()
    password = request.form['password'].strip()

    if username in users:
        return jsonify({'success': False, 'message': 'Username already exists.'})

    wallet_id = str(uuid4())[:16]
    users[username] = {
        'password': generate_password_hash(password),
        'wallet': wallet_id
    }
    blockchain.balances[wallet_id] = 10.0
    save_users()
    return jsonify({'success': True, 'wallet': wallet_id})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ---------------- Blockchain Functionalities ----------------
@app.route('/send', methods=['POST'])
def send():
    if 'wallet' not in session:
        return redirect(url_for('login_page'))

    sender = request.form['sender']
    recipient = request.form['recipient']
    amount = request.form['amount']
    success = blockchain.add_transaction(sender, recipient, amount)
    if not success:
        return "Insufficient funds!", 400
    blockchain.save_chain()
    return redirect(url_for('home'))

@app.route('/mine', methods=['POST'])
def mine():
    if 'wallet' not in session:
        return redirect(url_for('login_page'))

    miner = request.form['miner']
    new_block = blockchain.mine_block(miner)
    if not new_block:
        return "Nothing to mine!"
    return redirect(url_for('home'))

@app.route('/chain')
def get_chain():
    return jsonify(blockchain.to_dict())

@app.route('/balances')
def get_balances():
    return jsonify(blockchain.balances)

@app.route('/transactions')
def get_transactions():
    return jsonify(blockchain.get_transaction_history())

@app.route('/pending')
def get_pending():
    return jsonify(blockchain.current_transactions)

@app.route('/create_wallet')
def create_wallet():
    new_wallet = str(uuid4())[:16]
    blockchain.balances[new_wallet] = 10.0
    return jsonify({'wallet': new_wallet})

@app.route('/api/send', methods=['POST'])
def api_send():
    if 'wallet' not in session:
        return jsonify({'success': False, 'message': 'User not logged in.'}), 401

    sender = request.form['sender']
    recipient = request.form['recipient']
    amount = request.form['amount']

    success = blockchain.add_transaction(sender, recipient, amount)
    if not success:
        return jsonify({'success': False, 'message': 'Insufficient funds!'})

    blockchain.save_chain()
    return jsonify({'success': True, 'message': 'Transaction successful.'})


# ---------------- Main ----------------
if __name__ == '__main__':
    app.run(debug=True)
