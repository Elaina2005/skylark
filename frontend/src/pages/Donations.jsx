import { useEffect, useState } from 'react'
import { getDonations } from '../api'

function Donations() {
  const [donations, setDonations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getDonations()
        setDonations(data)
      } catch (err) {
        setError('Could not load donations')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <h2 className="text-3xl font-extrabold text-white">Donations</h2>
      </div>

      {loading ? (
        <p className="text-slate-400 text-sm">Loading donations...</p>
      ) : error ? (
        <div className="rounded-2xl border border-rose-800 bg-rose-950/80 p-4 text-rose-200 text-sm">{error}</div>
      ) : donations.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-center text-slate-400 text-sm">No donations recorded yet.</div>
      ) : (
        <div className="grid gap-4">
          {donations.map((donation) => (
            <div key={donation.id} className="rounded-2xl border border-slate-800 bg-slate-900 p-5 space-y-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:justify-between sm:items-center border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-xl font-extrabold text-white">{donation.food}</h3>
                  <p className="text-xs text-amber-300 font-semibold">{donation.quantity}</p>
                </div>
                <div className="sm:text-right">
                  <span className="text-xs text-slate-400 font-semibold block">NGO</span>
                  <span className="text-sm font-bold text-amber-300">{donation.ngo}</span>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-3 text-xs pt-1">
                <div>
                  <span className="text-slate-500 block">Freshness</span>
                  <strong className="text-emerald-400 text-sm font-bold">{donation.freshness}%</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Remaining Hours</span>
                  <strong className="text-white text-sm font-bold">{donation.remaining_hours} hrs</strong>
                </div>
                <div>
                  <span className="text-slate-500 block">Status</span>
                  <strong className="text-amber-300 text-sm font-bold">{donation.status}</strong>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Donations
