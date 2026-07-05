from blockchain.wallet import Wallet
from blockchain.transaction import Transaction
from blockchain.blockchain import Blockchain

# Create wallets
alice = Wallet()
bob = Wallet()

print("Alice address:", alice.get_address())
print("Bob address:", bob.get_address())

# Create blockchain
chain = Blockchain(difficulty=2)

# Create and sign transaction
tx1 = Transaction(
    sender=alice.get_address(),
    recipient=bob.get_address(),
    amount=5
)
tx1.sign_transaction(alice)

# Add transaction
added = chain.add_transaction(tx1)
print("Transaction added:", added)

# Mine block
block = chain.mine_pending_transactions(miner_address=alice.get_address())
print("Block mined:", block.index)

# Validate chain
print("Is blockchain valid?", chain.is_chain_valid())
