import { useEffect, useState, useCallback } from 'react'
import { api } from './api'
import CreateEventForm from './components/CreateEventForm'
import EventCard from './components/EventCard'
import ChainExplorer from './components/ChainExplorer'

export default function App() {
  const [plugins, setPlugins] = useState([])
  const [events, setEvents] = useState([])
  const [chain, setChain] = useState(null)
  const [error, setError] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const [pl, ev, ch] = await Promise.all([
        api.listPlugins(),
        api.listEvents(),
        api.getChain(),
      ])
      setPlugins(pl)
      setEvents(ev)
      setChain(ch)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 5000)
    return () => clearInterval(id)
  }, [refresh])

  return (
    <div className="app">
      <header className="header">
        <h1>⚽ World Cup 2026 Blockchain Betting</h1>
        <p className="subtitle">
          Predict tournament events at any time. Every bet is sealed on a
          tamper-evident blockchain and locks the moment the event starts.
        </p>
        {chain && (
          <span className={`chain-badge ${chain.valid ? 'ok' : 'bad'}`}>
            {chain.valid ? '🔒 Chain verified' : '⚠️ Chain tampered'} ·{' '}
            {chain.length} blocks
          </span>
        )}
      </header>

      {error && <div className="error-banner">⚠️ {error}</div>}

      <main className="layout">
        <section className="column">
          <h2>Create Event</h2>
          <CreateEventForm plugins={plugins} onCreated={refresh} onError={setError} />

          <h2>Open & Settled Events</h2>
          {events.length === 0 && <p className="muted">No events yet.</p>}
          {events.map((ev) => (
            <EventCard key={ev.id} event={ev} onChanged={refresh} onError={setError} />
          ))}
        </section>

        <section className="column">
          <h2>Blockchain Ledger</h2>
          <ChainExplorer chain={chain} />
        </section>
      </main>
    </div>
  )
}
