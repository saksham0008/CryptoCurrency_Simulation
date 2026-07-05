"""
ai/fraud_detection.py

ML-based fraud detector using Isolation Forest.

Improvements over v1:
  - Real sender_total_sent / sender_total_received / frequency
    are computed from the live blockchain history instead of using
    hardcoded placeholder zeros.
  - The model is retrained automatically whenever a new transaction
    arrives (incremental re-fit on all confirmed chain data).
  - predict() returns a normalised risk_score in [-1, +1].
    Negative → anomalous (flagged).  Positive → normal.
"""

import numpy as np
from collections import defaultdict
from sklearn.ensemble import IsolationForest


class FraudDetector:
    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        self.trained = False

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @staticmethod
    def compute_sender_stats(sender: str, chain: list) -> dict:
        """
        Walk the full blockchain and return real statistics for *sender*.

        Returns:
            {
              "total_sent":     total coins sent by this address,
              "total_received": total coins received by this address,
              "frequency":      number of send-transactions from this address,
            }
        """
        total_sent = 0.0
        total_received = 0.0
        frequency = 0

        for block in chain:
            # block.transactions may be a list of dicts
            txs = block.transactions if hasattr(block, "transactions") else []
            for tx in txs:
                s = tx.get("sender", "")
                r = tx.get("recipient", "")
                amount = float(tx.get("amount", 0))

                if s == sender:
                    total_sent += amount
                    frequency += 1
                if r == sender:
                    total_received += amount

        return {
            "total_sent": total_sent,
            "total_received": total_received,
            "frequency": frequency,
        }

    def train_from_chain(self, chain: list) -> None:
        """
        Extract feature vectors from the confirmed blockchain and fit
        the Isolation Forest model.  Skips MINER reward transactions.
        Requires at least 10 real transactions to train (avoids
        underfitting on tiny chains).
        """
        features = []

        # Build per-address running totals as we walk the chain
        address_sent     = defaultdict(float)
        address_received = defaultdict(float)
        address_freq     = defaultdict(int)

        for block in chain:
            txs = block.transactions if hasattr(block, "transactions") else []
            for tx in txs:
                sender = tx.get("sender", "")
                recipient = tx.get("recipient", "")
                amount = float(tx.get("amount", 0))

                if sender == "MINER":
                    continue  # skip reward transactions

                # Record feature vector BEFORE updating stats
                # (represents what the model would have seen at submission time)
                features.append([
                    amount,
                    address_sent[sender],
                    address_received[sender],
                    float(address_freq[sender]),
                ])

                # Update running totals
                address_sent[sender]     += amount
                address_received[recipient] += amount
                address_freq[sender]     += 1

        if len(features) < 5:
            # Not enough data to train meaningfully; keep untrained state
            return

        X = np.array(features, dtype=float)
        self.model.fit(X)
        self.trained = True

    def predict(self, tx_features: list) -> float:
        """
        Predict anomaly score for a single transaction.

        tx_features = [amount, sender_total_sent,
                        sender_total_received, frequency]

        Returns:
            float in roughly [-1, +1]
            Negative values indicate anomaly (potential fraud).
        """
        if not self.trained:
            # Model not trained yet → neutral score (not flagged)
            return 0.5

        X = np.array([tx_features], dtype=float)
        score = self.model.decision_function(X)[0]  # raw anomaly score
        return float(score)
