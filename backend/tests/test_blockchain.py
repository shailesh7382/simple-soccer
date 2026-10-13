from app.blockchain import Blockchain


def test_genesis_block_created():
    chain = Blockchain(difficulty=2)
    assert len(chain.chain) == 1
    assert chain.chain[0].index == 0
    assert chain.is_valid()


def test_commit_transaction_links_blocks():
    chain = Blockchain(difficulty=2)
    block = chain.commit_transaction({"type": "bet", "amount": 10})
    assert block.index == 1
    assert block.previous_hash == chain.chain[0].hash
    assert block.hash.startswith("00")
    assert chain.is_valid()


def test_proof_of_work_meets_difficulty():
    chain = Blockchain(difficulty=3)
    block = chain.commit_transaction({"type": "bet"})
    assert block.hash.startswith("000")


def test_tampering_is_detected():
    chain = Blockchain(difficulty=2)
    chain.commit_transaction({"type": "bet", "amount": 10})
    chain.commit_transaction({"type": "bet", "amount": 20})
    assert chain.is_valid()
    # Mutate a recorded bet -> chain must become invalid.
    chain.chain[1].transactions[0]["amount"] = 9999
    assert not chain.is_valid()


def test_find_transactions():
    chain = Blockchain(difficulty=1)
    chain.commit_transaction({"type": "bet", "event_id": "e1"})
    chain.commit_transaction({"type": "bet", "event_id": "e2"})
    chain.commit_transaction({"type": "settlement", "event_id": "e1"})
    bets = chain.find_transactions(type="bet")
    assert len(bets) == 2
    e1 = chain.find_transactions(event_id="e1")
    assert len(e1) == 2
