export default function ChainExplorer({ chain }) {
  if (!chain) return <p className="muted">Loading ledger…</p>

  return (
    <div className="chain">
      {[...chain.blocks].reverse().map((block) => (
        <div className="card block" key={block.index}>
          <div className="block-head">
            <span className="block-index">#{block.index}</span>
            <code className="hash" title={block.hash}>
              {block.hash.slice(0, 16)}…
            </code>
          </div>
          <div className="muted small">
            prev {block.previous_hash.slice(0, 12)}… · nonce {block.nonce}
          </div>
          <ul className="tx-list">
            {block.transactions.map((tx, i) => (
              <li key={i}>
                <code>{tx.type}</code>
                {tx.type === 'bet' && (
                  <>
                    {' '}
                    {tx.bettor} bet {tx.amount} on {tx.selection}
                  </>
                )}
                {tx.type === 'settlement' && <> outcome: {tx.outcome}</>}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
