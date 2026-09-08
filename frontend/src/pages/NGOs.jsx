import { useEffect, useState } from 'react'
import { getNGOs } from '../api'

function NGOs() {
  const [ngos, setNgos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadNgos() {
      try {
        const data = await getNGOs()
        setNgos(data)
      } catch (err) {
        setError('Unable to load NGO list')
      } finally {
        setLoading(false)
      }
    }

    loadNgos()
  }, [])

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <h2 className="text-3xl font-extrabold text-white">Registered NGOs</h2>
      </div>

      {loading ? (
        <p className="text-slate-400 text-sm">Loading NGOs...</p>
      ) : error ? (
        <div className="rounded-2xl border border-rose-800 bg-rose-950/80 p-4 text-rose-200 text-sm">{error}</div>
      ) : ngos.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-center text-slate-400 text-sm">No NGOs registered yet.</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {ngos.map((ngo) => (
            <div key={ngo.id} className="rounded-2xl border border-slate-800 bg-slate-900 p-5 space-y-3">
              <div className="flex justify-between items-start">
                <h3 className="text-xl font-bold text-white">{ngo.name}</h3>
                <span className="text-xs text-amber-300 font-semibold">{ngo.city || 'Chennai'}</span>
              </div>
              <div className="text-xs space-y-1 text-slate-400 border-t border-slate-800 pt-2">
                <p>Email: <span className="text-slate-200 font-semibold">{ngo.contact_email || 'N/A'}</span></p>
                <p>Phone: <span className="text-slate-200 font-semibold">{ngo.phone || 'N/A'}</span></p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default NGOs
