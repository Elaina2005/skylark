import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getNearbyDonations, acceptDonation } from '../api'

function FoodNearby() {
  const [donations, setDonations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const navigate = useNavigate()
  
  const [searchFood, setSearchFood] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')

  useEffect(() => {
    loadNearby()
  }, [])

  const loadNearby = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getNearbyDonations({ lat: 13.0827, lon: 80.2707 })
      setDonations(data)
    } catch (err) {
      setError('Unable to load food donations.')
    } finally {
      setLoading(false)
    }
  }

  const handleAccept = async (id) => {
    setError('')
    setMessage('')
    try {
      await acceptDonation(id)
      setMessage(`Requested donation #${id}!`)
      loadNearby()
      setTimeout(() => navigate(`/track/${id}`), 1000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to accept donation.')
    }
  }

  const filteredDonations = donations.filter((d) => {
    if (searchFood && !d.food.toLowerCase().includes(searchFood.toLowerCase())) return false
    if (categoryFilter && !d.category?.toLowerCase().includes(categoryFilter.toLowerCase())) return false
    if (priorityFilter && d.priority !== priorityFilter) return false
    return true
  })

  return (
    <div className="space-y-8 pb-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <h2 className="text-3xl font-extrabold text-white">Food Available Nearby</h2>
        <div className="flex gap-3">
          <Link
            to="/map"
            className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-bold text-amber-300 hover:bg-slate-800 transition"
          >
            Map View
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="grid gap-3 sm:grid-cols-3">
        <input
          value={searchFood}
          onChange={(e) => setSearchFood(e.target.value)}
          placeholder="Search food"
          className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-amber-400 focus:outline-none"
        />
        <input
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          placeholder="Filter by category"
          className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-amber-400 focus:outline-none"
        />
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 focus:border-amber-400 focus:outline-none"
        >
          <option value="">All Priorities</option>
          <option value="Low">Low</option>
          <option value="Medium">Medium</option>
          <option value="High">High</option>
        </select>
      </div>

      {error && <div className="rounded-2xl border border-rose-800 bg-rose-950/80 p-4 text-rose-200 text-sm">{error}</div>}
      {message && <div className="rounded-2xl border border-emerald-800 bg-emerald-950/80 p-4 text-emerald-200 text-sm">{message}</div>}

      {loading ? (
        <p className="text-slate-400 text-sm">Loading available food...</p>
      ) : filteredDonations.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center text-slate-400 text-sm">
          No food available matching criteria.
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredDonations.map((d) => (
            <div key={d.id} className="rounded-3xl border border-slate-800 bg-slate-900 p-6 flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <h3 className="text-2xl font-extrabold text-white">{d.food}</h3>
                  <span className="rounded-full bg-emerald-500/10 border border-emerald-500/30 px-3 py-0.5 text-xs font-semibold text-emerald-400">
                    Available
                  </span>
                </div>

                <p className="text-sm font-semibold text-amber-300">{d.quantity}</p>
                <p className="text-xs text-slate-400">{d.distance_km != null ? `${d.distance_km} km away` : 'Nearby'}</p>

                <div className="flex gap-4 text-xs pt-2 border-t border-slate-800">
                  <div>
                    <span className="text-slate-500 block">Freshness</span>
                    <strong className="text-emerald-400 text-sm font-bold">{d.freshness}%</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Priority</span>
                    <strong className="text-white text-sm font-bold">{d.priority}</strong>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 pt-2 border-t border-slate-800">
                <Link
                  to={`/track/${d.id}`}
                  className="flex-1 text-center rounded-xl border border-slate-700 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 transition"
                >
                  View Details
                </Link>
                <button
                  onClick={() => handleAccept(d.id)}
                  className="flex-1 rounded-xl bg-emerald-500 py-2 text-xs font-bold text-white hover:bg-emerald-400 transition"
                >
                  Request Donation
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default FoodNearby
