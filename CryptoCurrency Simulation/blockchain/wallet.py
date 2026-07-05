from ecdsa import SigningKey, SECP256k1
import hashlib

class Wallet:
    def __init__(self):
        # Generate private & public key
        self.private_key = SigningKey.generate(curve=SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

    def get_public_key(self):
        return self.public_key.to_string().hex()

    def get_address(self):
        """
        Wallet address = SHA256(public key)
        """
        return hashlib.sha256(self.public_key.to_string()).hexdigest()

    def sign(self, message: str):
        """
        Sign a message hash
        """
        return self.private_key.sign(message.encode()).hex()
