import { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getDonationById, getDonations, updateDonationStatus } from '../api'

const TIMELINE_STEPS = [
  { key: 'AVAILABLE', label: 'Available' },
  { key: 'ACCEPTED', label: 'Accepted' },
  { key: 'PICKUP_SCHEDULED', label: 'Pickup Scheduled' },
  { key: 'PICKED_UP', label: 'Picked Up' },
  { key: 'IN_TRANSIT', label: 'In Transit' },
  { key: 'DELIVERED', label: 'Delivered' },
  { key: 'COMPLETED', label: 'Completed' },
]

function TrackDonation() {
  const { id } = useParams()
  const [searchId, setSearchId] = useState(id || '')
  const [donation, setDonation] = useState(null)
  const [recentDonations, setRecentDonations] = useState([])
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)

  useEffect(() => {
    loadRecentDonations()
  }, [])

  useEffect(() => {
    if (id) {
      setSearchId(id)
      fetchDonation(id)
    }
  }, [id])

  const loadRecentDonations = async () => {
    try {
      const data = await getDonations()
      setRecentDonations(data.slice(0, 5))
      if (!id && data.length > 0) {
        setSearchId(String(data[0].id))
        fetchDonation(data[0].id)
      }
    } catch (err) {
      console.error('Failed to load recent donations:', err)
    }
  }

  const fetchDonation = async (donationId) => {
    if (!donationId) return
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const data = await getDonationById(donationId)
      setDonation(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to find donation.')
      setDonation(null)
    } finally {
      setLoading(false)
    }
  }

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    if (searchId && searchId.trim()) {
      fetchDonation(searchId.trim())
    }
  }

  const handleAdvanceStatus = async () => {
    if (!donation) return
    const currentIdx = TIMELINE_STEPS.findIndex((s) => s.key === donation.status)
    if (currentIdx < 0 || currentIdx >= TIMELINE_STEPS.length - 1) return

    const nextStep = TIMELINE_STEPS[currentIdx + 1]
    setActionLoading(true)
    setError('')
    setMessage('')
    try {
      await updateDonationStatus(donation.id, {
        status: nextStep.key,
        note: `Status updated to ${nextStep.label}`,
      })
      setMessage(`Status updated to ${nextStep.label}!`)
      fetchDonation(donation.id)
    } catch (err) {
      setError('Failed to update status.')
    } finally {
      setActionLoading(false)
    }
  }

  useEffect(() => {
    if (!donation || !mapRef.current || !window.L) return

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove()
    }

    const donorLat = donation.latitude || 13.0827
    const donorLon = donation.longitude || 80.2707
    const ngoLat = 13.0418
    const ngoLon = 80.2341

    const map = window.L.map(mapRef.current).setView([donorLat, donorLon], 12)
    mapInstanceRef.current = map

    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
    }).addTo(map)

    window.L.marker([donorLat, donorLon]).addTo(map).bindPopup(`<b>Donor Location</b><br/>${donation.location || 'Donor'}`).openPopup()
    window.L.marker([ngoLat, ngoLon]).addTo(map).bindPopup(`<b>NGO</b><br/>${donation.ngo}`)

    if (['IN_TRANSIT', 'PICKED_UP'].includes(donation.status)) {
      const midLat = (donorLat + ngoLat) / 2
      const midLon = (donorLon + ngoLon) / 2

      window.L.polyline([[donorLat, donorLon], [midLat, midLon], [ngoLat, ngoLon]], { color: '#f59e0b', weight: 4, dashArray: '8, 8' }).addTo(map)
      window.L.marker([midLat, midLon]).addTo(map).bindPopup(`<b>Vehicle</b><br/>In Transit`)
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [donation])

  const getStepIndex = (status) => {
    if (status === 'CANCELLED') return -1
    const idx = TIMELINE_STEPS.findIndex((s) => s.key === status)
    return idx >= 0 ? idx : 0
  }

  const currentStepIdx = donation ? getStepIndex(donation.status) : 0
  const isNextAvailable = currentStepIdx >= 0 && currentStepIdx < TIMELINE_STEPS.length - 1

  return (
    <div className="space-y-8 pb-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <h2 className="text-3xl font-extrabold text-white">Track Donation</h2>

        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <input
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            placeholder="Donation ID"
            className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-amber-400 focus:outline-none w-48"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="rounded-2xl bg-amber-400 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-amber-300 transition"
          >
            Track
          </button>
        </form>
      </div>

      {recentDonations.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {recentDonations.map((d) => (
            <button
              key={d.id}
              onClick={() => {
                setSearchId(String(d.id))
                fetchDonation(d.id)
              }}
              className={`rounded-xl px-3 py-1.5 text-xs font-bold transition ${
                donation?.id === d.id ? 'bg-amber-400 text-slate-950' : 'bg-slate-900 border border-slate-800 text-slate-300'
              }`}
            >
              #{d.id} {d.food} ({d.status})
            </button>
          ))}
        </div>
      )}

      {message && <div className="rounded-2xl border border-emerald-800 bg-emerald-950/80 p-4 text-emerald-200 text-sm">{message}</div>}
      {error && <div className="rounded-2xl border border-rose-800 bg-rose-950/80 p-4 text-rose-200 text-sm">{error}</div>}

      {donation && (
        <div className="space-y-8">
          {/* Summary Card */}
          <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs font-mono text-slate-400">Donation #{donation.id}</span>
                <h3 className="text-2xl font-extrabold text-white mt-1">{donation.food}</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Quantity: <strong className="text-white">{donation.quantity}</strong> | Donor: <strong className="text-white">{donation.donor_name || 'Donor'}</strong> | NGO: <strong className="text-amber-300">{donation.ngo}</strong>
                </p>
              </div>

              <div className="flex flex-col sm:items-end gap-2">
                <span
                  className={`px-4 py-1.5 rounded-full text-xs font-extrabold ${
                    donation.status === 'COMPLETED'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : donation.status === 'IN_TRANSIT'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                  }`}
                >
                  {donation.status}
                </span>

                {isNextAvailable && (
                  <button
                    onClick={handleAdvanceStatus}
                    disabled={actionLoading}
                    className="rounded-xl bg-amber-400 px-4 py-1.5 text-xs font-bold text-slate-950 hover:bg-amber-300 transition"
                  >
                    Advance Status ➔
                  </button>
                )}
              </div>
            </div>

            {/* Map */}
            <div ref={mapRef} className="h-64 w-full rounded-2xl border border-slate-800"></div>
          </section>

          {/* Clean Timeline */}
          <section className="rounded-3xl border border-slate-800 bg-slate-900 p-8 space-y-6">
            <h3 className="text-xl font-bold text-white">Timeline</h3>

            <div className="space-y-4">
              {TIMELINE_STEPS.map((step, idx) => {
                const isPassed = idx <= currentStepIdx
                const isCurrent = idx === currentStepIdx
                const historyEntry = donation.status_history?.find((h) => h.status === step.key)

                return (
                  <div key={step.key} className="flex items-center gap-4">
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                        isCurrent
                          ? 'bg-amber-400 text-slate-950 ring-4 ring-amber-400/20'
                          : isPassed
                          ? 'bg-emerald-500 text-white'
                          : 'bg-slate-800 text-slate-500'
                      }`}
                    >
                      {isPassed ? '✓' : idx + 1}
                    </div>

                    <div className="flex-1 rounded-2xl border border-slate-800 bg-slate-950 p-4 flex justify-between items-center">
                      <div>
                        <h4 className={`text-sm font-bold ${isPassed ? 'text-white' : 'text-slate-500'}`}>{step.label}</h4>
                        {historyEntry && historyEntry.note && <p className="text-xs text-slate-400 mt-0.5">{historyEntry.note}</p>}
                      </div>
                      {historyEntry && (
                        <span className="text-xs font-mono text-slate-500">
                          {new Date(historyEntry.created_at).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        </div>
      )}
    </div>
  )
}

export default TrackDonation
