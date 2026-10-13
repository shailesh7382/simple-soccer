"""Core blockchain implementation.

A lightweight, dependency-free blockchain used to make betting records
tamper-evident. Each bet (and each settlement) is stored as a transaction
inside a block. Blocks are linked by SHA-256 hashes and sealed using a
proof-of-work scheme, so any retroactive modification of a recorded bet
invalidates every subsequent block and is detectable via :meth:`Blockchain.is_valid`.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


def _stable_hash(payload: Dict[str, Any]) -> str:
    """Return a deterministic SHA-256 hex digest for a dict payload."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass
class Block:
    """A single block in the chain."""

    index: int
    timestamp: float
    transactions: List[Dict[str, Any]]
    previous_hash: str
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        """Compute this block's hash from its content (excluding the stored hash)."""
        payload = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        return _stable_hash(payload)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Blockchain:
    """An append-only, proof-of-work secured chain of blocks.

    Args:
        difficulty: Number of leading zeroes required in a block hash. Kept low
            by default so the demo stays responsive while still demonstrating
            proof-of-work and tamper detection.
    """

    def __init__(self, difficulty: int = 3) -> None:
        self.difficulty = difficulty
        self.chain: List[Block] = []
        self._pending: List[Dict[str, Any]] = []
        self._create_genesis_block()

    # ------------------------------------------------------------------ #
    # Construction helpers
    # ------------------------------------------------------------------ #
    def _create_genesis_block(self) -> None:
        genesis = Block(
            index=0,
            timestamp=time.time(),
            transactions=[{"type": "genesis", "note": "World Cup 2026 betting ledger"}],
            previous_hash="0" * 64,
        )
        self._seal_block(genesis)
        self.chain.append(genesis)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    @property
    def pending_transactions(self) -> List[Dict[str, Any]]:
        return list(self._pending)

    # ------------------------------------------------------------------ #
    # Mining / proof-of-work
    # ------------------------------------------------------------------ #
    def _prefix(self) -> str:
        return "0" * self.difficulty

    def _seal_block(self, block: Block) -> Block:
        """Run proof-of-work, mutating the block's nonce/hash until valid."""
        prefix = self._prefix()
        block.nonce = 0
        computed = block.compute_hash()
        while not computed.startswith(prefix):
            block.nonce += 1
            computed = block.compute_hash()
        block.hash = computed
        return block

    def add_transaction(self, transaction: Dict[str, Any]) -> int:
        """Queue a transaction for inclusion in the next mined block.

        Returns the index of the block that will hold this transaction.
        """
        self._pending.append(dict(transaction))
        return self.last_block.index + 1

    def mine_pending_transactions(self) -> Optional[Block]:
        """Seal all pending transactions into a new block.

        Returns the new block, or ``None`` when there is nothing pending.
        """
        if not self._pending:
            return None
        block = Block(
            index=self.last_block.index + 1,
            timestamp=time.time(),
            transactions=self._pending,
            previous_hash=self.last_block.hash,
        )
        self._seal_block(block)
        self.chain.append(block)
        self._pending = []
        return block

    def commit_transaction(self, transaction: Dict[str, Any]) -> Block:
        """Add a single transaction and immediately mine it into a block."""
        self.add_transaction(transaction)
        block = self.mine_pending_transactions()
        assert block is not None  # we just added a transaction
        return block

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #
    def is_valid(self) -> bool:
        """Return ``True`` only if the entire chain is internally consistent."""
        prefix = self._prefix()
        for i, block in enumerate(self.chain):
            if block.hash != block.compute_hash():
                return False
            if i == 0:
                continue
            if block.previous_hash != self.chain[i - 1].hash:
                return False
            if not block.hash.startswith(prefix):
                return False
        return True

    def find_transactions(self, **match: Any) -> List[Dict[str, Any]]:
        """Return every committed transaction matching all key/value pairs."""
        results: List[Dict[str, Any]] = []
        for block in self.chain:
            for tx in block.transactions:
                if all(tx.get(k) == v for k, v in match.items()):
                    results.append(tx)
        return results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "difficulty": self.difficulty,
            "length": len(self.chain),
            "valid": self.is_valid(),
            "blocks": [b.to_dict() for b in self.chain],
            "pending": self.pending_transactions,
        }
