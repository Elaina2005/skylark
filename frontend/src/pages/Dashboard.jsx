import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../authContext'
import { getMyDonations, confirmDonationReceipt, getNearbyDonations, acceptDonation } from '../api'

function Dashboard() {
  const { user } = useAuth()
  const [donations, setDonations] = useState([])
  const [nearbyList, setNearbyList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const isNgo = user?.role === 'ngo'

  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  async function loadData() {
    setLoading(true)
    setError('')
    try {
      if (isNgo) {
        const [myDons, nearby] = await Promise.all([
          getMyDonations(),
          getNearbyDonations({ lat: 13.0827, lon: 80.2707 }),
        ])
        setDonations(myDons)
        setNearbyList(nearby)
      } else {
        const myDons = await getMyDonations()
        setDonations(myDons)
      }
    } catch (err) {
      setError('Unable to load dashboard data.')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmReceipt = async (donationId) => {
    setError('')
    setMessage('')
    try {
      await confirmDonationReceipt(donationId)
      setMessage(`Donation #${donationId} completed!`)
      loadData()
    } catch (err) {
      setError('Failed to confirm receipt.')
    }
  }

  const handleRequest = async (donationId) => {
    setError('')
    setMessage('')
    try {
      await acceptDonation(donationId)
      setMessage(`Donation #${donationId} requested!`)
      loadData()
    } catch (err) {
      setError('Failed to request donation.')
    }
  }

  const totalCount = donations.length
  const activeCount = donations.filter((d) => ['ACCEPTED', 'PICKUP_SCHEDULED', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED'].includes(d.status)).length
  const completedCount = donations.filter((d) => d.status === 'COMPLETED').length

  if (isNgo) {
    return (
      <div className="space-y-8 pb-12">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between border-b border-slate-800 pb-4">
          <h2 className="text-3xl font-extrabold text-white">NGO Dashboard</h2>
          <div className="flex gap-3">
            <Link
              to="/donations/nearby"
              className="rounded-2xl bg-amber-400 px-5 py-2.5 text-sm font-bold text-slate-950 hover:bg-amber-300 transition"
            >
              Food Available Nearby
            </Link>
          </div>
        </div>

        {message && <div className="rounded-2xl border border-emerald-800 bg-emerald-950/80 p-4 text-emerald-200 text-sm">{message}</div>}
        {error && <div className="rounded-2xl border border-rose-800 bg-rose-950/80 p-4 text-rose-200 text-sm">{error}</div>}

        {/* NGO Metrics */}
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl bg-slate-900 p-5 border border-slate-800">
            <p className="text-xs uppercase text-slate-400 font-semibold">Available Nearby</p>
            <p className="mt-2 text-3xl font-extrabold text-amber-300">{nearbyList.length}</p>
          </div>
          <div className="rounded-2xl bg-slate-900 p-5 border border-slate-800">
            <p className="text-xs uppercase text-slate-400 font-semibold">Active</p>
            <p className="mt-2 text-3xl font-extrabold text-indigo-400">{activeCount}</p>
          </div>
          <div className="rounded-2xl bg-slate-900 p-5 border border-slate-800">
            <p className="text-xs uppercase text-slate-400 font-semibold">Completed</p>
            <p className="mt-2 text-3xl font-extrabold text-emerald-400">{completedCount}</p>
          </div>
        </div>

        {/* Food Available Nearby */}
        <section className="space-y-4">
          <h3 className="text-xl font-bold text-white">Food Available Nearby</h3>
          {loading ? (
            <p className="text-slate-400 text-sm">Loading...</p>
          ) : nearbyList.length === 0 ? (
            <p className="text-slate-400 text-sm">No nearby food currently available.</p>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {nearbyList.slice(0, 6).map((item) => (
                <div key={item.id} className="rounded-2xl border border-slate-800 bg-slate-900 p-5 space-y-3">
                  <div>
                    <h4 className="text-xl font-extrabold text-white">{item.food}</h4>
                    <p className="text-xs text-amber-300 font-semibold">{item.quantity}</p>
                  </div>
                  <div className="flex justify-between text-xs text-slate-300 border-t border-slate-800 pt-2">
                    <span>{item.distance_km != null ? `${item.distance_km} km away` : 'Nearby'}</span>
                    <span>Freshness: <strong>{item.freshness}%</strong></span>
                    <span>Priority: <strong>{item.priority}</strong></span>
                  </div>
                  <div className="flex gap-2 pt-1">
                    <Link
                      to={`/track/${item.id}`}
                      className="flex-1 text-center rounded-xl border border-slate-700 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 transition"
                    >
                      View
                    </Link>
                    <button
                      onClick={() => handleRequest(item.id)}
                      className="flex-1 rounded-xl bg-emerald-500 py-2 text-xs font-bold text-white hover:bg-emerald-400 transition"
                    >
                      Request
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Active Accepted Requests */}
        {donations.length > 0 && (
          <section className="space-y-4 pt-4">
            <h3 className="text-xl font-bold text-white">My Active Requests</h3>
            <div className="grid gap-4">
              {donations.map((d) => (
                <div key={d.id} className="rounded-2xl border border-slate-800 bg-slate-900 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h4 className="text-lg font-bold text-white">{d.food} ({d.quantity})</h4>
                    <p className="text-xs text-slate-400">Status: <strong className="text-amber-300">{d.status}</strong> | Freshness: {d.freshness}%</p>
                  </div>
                  <div className="flex gap-2">
                    <Link
                      to={`/track/${d.id}`}
                      className="rounded-xl border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 transition"
                    >
                      Track
                    </Link>
                    {d.status === 'DELIVERED' && (
                      <button
                        onClick={() => handleConfirmReceipt(d.id)}
                        className="rounded-xl bg-emerald-500 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-400 transition"
                      >
                        Confirm Receipt
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    )
  }

  // Donor Dashboard
  return (
    <div className="space-y-8 pb-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <h2 className="text-3xl font-extrabold text-white">My Dashboard</h2>
        <div className="flex gap-3">
          <Link
            to="/#donate-form"
            className="rounded-2xl bg-amber-400 px-5 py-2.5 text-sm font-bold text-slate-950 hover:bg-amber-300 transition"
          >
            Donate Food
          </Link>
        </div>
      </div>

      {message && <div className="rounded-2xl border border-emerald-800 bg-emerald-950/80 p-4 text-emerald-200 text-sm">{message}</div>}
      {error && <div className="rounded-2xl border border-rose-800 bg-rose-950/80 p-4 text-rose-200 text-sm">{error}</div>}

      {/* Donor Metrics */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl bg-slate-900 p-5 border border-slate-800">
          <p className="text-xs uppercase text-slate-400 font-semibold">Total Donations</p>
          <p className="mt-2 text-3xl font-extrabold text-white">{totalCount}</p>
        </div>
        <div className="rounded-2xl bg-slate-900 p-5 border border-slate-800">
          <p className="text-xs uppercase text-slate-400 font-semibold">Active</p>
          <p className="mt-2 text-3xl font-extrabold text-amber-300">{activeCount}</p>
        </div>
        <div className="rounded-2xl bg-slate-900 p-5 border border-slate-800">
          <p className="text-xs uppercase text-slate-400 font-semibold">Completed</p>
          <p className="mt-2 text-3xl font-extrabold text-emerald-400">{completedCount}</p>
        </div>
      </div>

      {/* Recent Donations */}
      <section className="space-y-4">
        <h3 className="text-xl font-bold text-white">Recent Donations</h3>
        {loading ? (
          <p className="text-slate-400 text-sm">Loading...</p>
        ) : donations.length === 0 ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 text-center text-slate-400 text-sm">
            You haven't listed any food donations yet.
          </div>
        ) : (
          <div className="grid gap-4">
            {donations.map((d) => (
              <div key={d.id} className="rounded-2xl border border-slate-800 bg-slate-900 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="text-lg font-bold text-white">{d.food}</h4>
                  <p className="text-xs text-amber-300 font-semibold">{d.quantity}</p>
                  <p className="text-xs text-slate-400 mt-1">NGO: {d.ngo} | Status: <strong className="text-white">{d.status}</strong></p>
                </div>
                <div>
                  <Link
                    to={`/track/${d.id}`}
                    className="inline-block rounded-xl bg-amber-400/10 border border-amber-400/30 px-4 py-2 text-xs font-bold text-amber-300 hover:bg-amber-400 hover:text-slate-950 transition"
                  >
                    Track
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default Dashboard
