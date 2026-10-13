import { useState, useEffect } from 'react'
import { api } from '../api'

// Default context fields rendered per plugin type. Falls back to a raw JSON
// textarea for any plugin not explicitly known to the UI.
const CONTEXT_FIELDS = {
  match_winner: [
    { key: 'home_team', label: 'Home team', default: 'Brazil' },
    { key: 'away_team', label: 'Away team', default: 'France' },
  ],
  total_goals: [{ key: 'line', label: 'Goals line', default: '2.5', number: true }],
  first_scorer: [
    { key: 'players', label: 'Players (comma separated)', default: 'Messi, Mbappe, Neymar', list: true },
  ],
}

export default function CreateEventForm({ plugins, onCreated, onError }) {
  const [typeId, setTypeId] = useState('')
  const [title, setTitle] = useState('')
  const [lockMinutes, setLockMinutes] = useState(60)
  const [fields, setFields] = useState({})
  const [rawContext, setRawContext] = useState('{}')

  useEffect(() => {
    if (!typeId && plugins.length) setTypeId(plugins[0].type_id)
  }, [plugins, typeId])

  useEffect(() => {
    const defs = CONTEXT_FIELDS[typeId]
    if (defs) {
      const init = {}
      defs.forEach((f) => (init[f.key] = f.default))
      setFields(init)
    }
  }, [typeId])

  const knownFields = CONTEXT_FIELDS[typeId]

  function buildContext() {
    if (!knownFields) return JSON.parse(rawContext || '{}')
    const ctx = {}
    knownFields.forEach((f) => {
      let val = fields[f.key]
      if (f.list) val = String(val).split(',').map((s) => s.trim()).filter(Boolean)
      else if (f.number) val = parseFloat(val)
      ctx[f.key] = val
    })
    return ctx
  }

  async function submit(e) {
    e.preventDefault()
    try {
      const context = buildContext()
      const lock_time = Date.now() / 1000 + lockMinutes * 60
      await api.createEvent({ type_id: typeId, title, context, lock_time })
      setTitle('')
      onCreated()
    } catch (err) {
      onError(err.message)
    }
  }

  return (
    <form className="card form" onSubmit={submit}>
      <label>
        Market type
        <select value={typeId} onChange={(e) => setTypeId(e.target.value)}>
          {plugins.map((p) => (
            <option key={p.type_id} value={p.type_id}>
              {p.display_name}
            </option>
          ))}
        </select>
      </label>

      <label>
        Title
        <input
          required
          placeholder="e.g. Round of 16: Brazil vs France"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
      </label>

      {knownFields ? (
        knownFields.map((f) => (
          <label key={f.key}>
            {f.label}
            <input
              value={fields[f.key] ?? ''}
              onChange={(e) => setFields({ ...fields, [f.key]: e.target.value })}
            />
          </label>
        ))
      ) : (
        <label>
          Context (JSON)
          <textarea value={rawContext} onChange={(e) => setRawContext(e.target.value)} />
        </label>
      )}

      <label>
        Locks in (minutes)
        <input
          type="number"
          min="1"
          value={lockMinutes}
          onChange={(e) => setLockMinutes(Number(e.target.value))}
        />
      </label>

      <button type="submit">Create event</button>
    </form>
  )
}
