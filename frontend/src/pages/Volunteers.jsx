import { useEffect, useState } from 'react'
import { getVolunteers } from '../api'

function Volunteers() {
  const [volunteers, setVolunteers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadVolunteers() {
      try {
        const data = await getVolunteers()
        setVolunteers(data)
      } catch (err) {
        setError('Unable to load volunteers')
      } finally {
        setLoading(false)
      }
    }

    loadVolunteers()
  }, [])

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <h2 className="text-3xl font-extrabold text-white">Volunteers</h2>
      </div>

      {loading ? (
        <p className="text-slate-400 text-sm">Loading volunteers...</p>
      ) : error ? (
        <div className="rounded-2xl border border-rose-800 bg-rose-950/80 p-4 text-rose-200 text-sm">{error}</div>
      ) : volunteers.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-center text-slate-400 text-sm">No volunteers registered yet.</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {volunteers.map((v) => (
            <div key={v.id} className="rounded-2xl border border-slate-800 bg-slate-900 p-5 space-y-3">
              <div className="flex justify-between items-start">
                <h3 className="text-lg font-bold text-white">{v.name}</h3>
                <span className="text-xs text-amber-300 font-semibold">{v.phone}</span>
              </div>
              <div className="text-xs text-slate-400 border-t border-slate-800 pt-2">
                <p>Email: <span className="text-slate-200 font-semibold">{v.email || 'N/A'}</span></p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Volunteers
