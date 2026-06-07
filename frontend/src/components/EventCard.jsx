import { useEffect, useState } from 'react'
import { api } from '../api'

export default function EventCard({ event, onChanged, onError }) {
  const [bets, setBets] = useState([])
  const [bettor, setBettor] = useState('')
  const [selection, setSelection] = useState(event.options[0]?.id || '')
  const [amount, setAmount] = useState(10)
  const [outcome, setOutcome] = useState(event.options[0]?.id || '')

  async function loadBets() {
    try {
      setBets(await api.listBets(event.id))
    } catch (e) {
      onError(e.message)
    }
  }

  useEffect(() => {
    loadBets()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [event.id, event.status])

  async function placeBet(e) {
    e.preventDefault()
    try {
      await api.placeBet({ event_id: event.id, bettor, selection, amount: Number(amount) })
      setBettor('')
      await loadBets()
      onChanged()
    } catch (err) {
      onError(err.message)
    }
  }

  async function settle() {
    try {
      await api.settleEvent(event.id, outcome)
      onChanged()
    } catch (err) {
      onError(err.message)
    }
  }

  const lockDate = new Date(event.lock_time * 1000)

  return (
    <div className="card event">
      <div className="event-head">
        <strong>{event.title}</strong>
        <span className={`status status-${event.status}`}>{event.status}</span>
      </div>
      <div className="muted small">
        {event.type_id} · locks {lockDate.toLocaleString()}
        {event.outcome && <> · outcome: <b>{event.outcome}</b></>}
      </div>

      {event.open_for_betting ? (
        <form className="bet-form" onSubmit={placeBet}>
          <input
            required
            placeholder="Your name"
            value={bettor}
            onChange={(e) => setBettor(e.target.value)}
          />
          <select value={selection} onChange={(e) => setSelection(e.target.value)}>
            {event.options.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label} (x{o.odds})
              </option>
            ))}
          </select>
          <input
            type="number"
            min="1"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
          <button type="submit">Place bet</button>
        </form>
      ) : (
        <p className="muted small">Betting closed for this event.</p>
      )}

      {event.status !== 'settled' && (
        <div className="settle-row">
          <select value={outcome} onChange={(e) => setOutcome(e.target.value)}>
            {event.options.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
          <button className="secondary" onClick={settle}>
            Settle as outcome
          </button>
        </div>
      )}

      {bets.length > 0 && (
        <ul className="bet-list">
          {bets.map((b) => (
            <li key={b.id} className={`bet bet-${b.status}`}>
              <span>
                {b.bettor} → <b>{b.selection}</b> · {b.amount} @ x{b.odds}
              </span>
              <span className="bet-meta">
                blk #{b.block_index} · {b.status}
                {b.payout > 0 && <> · won {b.payout}</>}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
