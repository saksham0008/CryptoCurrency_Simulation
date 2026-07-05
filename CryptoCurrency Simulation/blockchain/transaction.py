import json
import hashlib
from ecdsa import VerifyingKey, SECP256k1

class Transaction:
    def __init__(self, sender, recipient, amount, signature=None, public_key=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = float(amount)
        self.signature = signature
        self.public_key = public_key

    def to_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount
        }

    def hash(self):
        tx_string = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()

    def sign_transaction(self, wallet):
        self.public_key = wallet.get_public_key()
        self.signature = wallet.sign(self.hash())

    def is_valid(self):
        # Mining reward
        if self.sender == "MINER":
            return True

        if not self.signature or not self.public_key:
            return False

        try:
            vk = VerifyingKey.from_string(
                bytes.fromhex(self.public_key),
                curve=SECP256k1
            )
            return vk.verify(
                bytes.fromhex(self.signature),
                self.hash().encode()
            )
        except Exception:
            return False
