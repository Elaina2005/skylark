import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  getNGOs,
  createNGO,
  updateNGO,
  deleteNGO,
  getVolunteers,
  createVolunteer,
  updateVolunteer,
  deleteVolunteer,
  getAdminDonations,
  getAdminStats,
  exportAdminDonationsCSV,
  updateDonationStatus,
} from '../api'
import { useAuth } from '../authContext'

function Admin() {
  const [activeTab, setActiveTab] = useState('donations')
  const [ngos, setNgos] = useState([])
  const [volunteers, setVolunteers] = useState([])
  const [donations, setDonations] = useState([])
  const [stats, setStats] = useState({
    total_donations: 0,
    available_count: 0,
    accepted_count: 0,
    pickup_scheduled_count: 0,
    picked_up_count: 0,
    in_transit_count: 0,
    delivered_count: 0,
    completed_count: 0,
    cancelled_count: 0,
    fresh_count: 0,
    medium_count: 0,
    urgent_count: 0,
    expired_count: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [filters, setFilters] = useState({
    food: '',
    ngo: '',
    priority: '',
    status: '',
    start_date: '',
    end_date: '',
  })

  const [ngoForm, setNgoForm] = useState({ name: '', city: '', address: '', contact_email: '', phone: '' })
  const [volunteerForm, setVolunteerForm] = useState({ name: '', phone: '', email: '', ngo_id: '' })
  const [editingNgo, setEditingNgo] = useState(null)
  const [editingVolunteer, setEditingVolunteer] = useState(null)

  const navigate = useNavigate()
  const { isAuthenticated, loading: authLoading, signOut } = useAuth()

  useEffect(() => {
    if (authLoading) return
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    loadAllData()
  }, [authLoading, isAuthenticated, navigate])

  const loadAllData = async () => {
    setLoading(true)
    setError('')
    try {
      const [ngosData, volunteersData, statsData, donationsData] = await Promise.all([
        getNGOs(),
        getVolunteers(),
        getAdminStats(),
        getAdminDonations(cleanParams(filters)),
      ])
      setNgos(ngosData)
      setVolunteers(volunteersData)
      setStats(statsData)
      setDonations(donationsData)
    } catch (err) {
      setError('Unable to load data.')
    } finally {
      setLoading(false)
    }
  }

  const cleanParams = (f) => {
    const params = {}
    if (f.food) params.food = f.food
    if (f.ngo) params.ngo = f.ngo
    if (f.priority) params.priority = f.priority
    if (f.status) params.status = f.status
    if (f.start_date) params.start_date = f.start_date
    if (f.end_date) params.end_date = f.end_date
    return params
  }

  const handleApplyFilters = async () => {
    setLoading(true)
    try {
      const data = await getAdminDonations(cleanParams(filters))
      setDonations(data)
    } catch (err) {
      setError('Failed to filter donations.')
    } finally {
      setLoading(false)
    }
  }

  const handleResetFilters = async () => {
    const resetF = { food: '', ngo: '', priority: '', status: '', start_date: '', end_date: '' }
    setFilters(resetF)
    setLoading(true)
    try {
      const data = await getAdminDonations({})
      setDonations(data)
    } catch (err) {
      setError('Failed to reset filters.')
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (id, newStatus) => {
    setError('')
    setMessage('')
    try {
      await updateDonationStatus(id, {
        status: newStatus,
        note: `Updated by Admin to ${newStatus}`,
      })
      setMessage(`Donation #${id} status changed to ${newStatus}`)
      loadAllData()
    } catch (err) {
      setError('Failed to update donation status.')
    }
  }

  const handleExportCSV = async () => {
    try {
      const blob = await exportAdminDonationsCSV(cleanParams(filters))
      const url = window.URL.createObjectURL(new Blob([blob]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'donations.csv')
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
    } catch (err) {
      setError('Failed to export CSV.')
    }
  }

  const activeDonations = donations.filter((d) => ['ACCEPTED', 'PICKUP_SCHEDULED', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED'].includes(d.status))
  const urgentDonations = donations.filter((d) => d.priority === 'High' && d.status === 'AVAILABLE')

  return (
    <div className="space-y-8 pb-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <h2 className="text-3xl font-extrabold text-white">Admin Dashboard</h2>
        <div className="flex gap-2">
          <button
            onClick={handleExportCSV}
            className="rounded-2xl bg-emerald-500 px-5 py-2.5 text-sm font-bold text-white transition hover:bg-emerald-400 shadow-md"
          >
            Export CSV
          </button>
        </div>
      </div>

      {message && <div className="rounded-2xl border border-emerald-800 bg-emerald-950/80 p-4 text-emerald-200 text-sm">{message}</div>}
      {error && <div className="rounded-2xl border border-rose-800 bg-rose-950/80 p-4 text-rose-200 text-sm">{error}</div>}

      {/* Admin Statistics Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5 lg:grid-cols-10">
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase">Total</p>
          <p className="mt-1 text-xl font-extrabold text-white">{stats.total_donations}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase">Available</p>
          <p className="mt-1 text-xl font-extrabold text-amber-300">{stats.available_count}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase">Accepted</p>
          <p className="mt-1 text-xl font-extrabold text-blue-400">{stats.accepted_count}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase">Scheduled</p>
          <p className="mt-1 text-xl font-extrabold text-indigo-400">{stats.pickup_scheduled_count}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase">Picked Up</p>
          <p className="mt-1 text-xl font-extrabold text-purple-400">{stats.picked_up_count}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase">In Transit</p>
          <p className="mt-1 text-xl font-extrabold text-amber-400">{stats.in_transit_count}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase">Delivered</p>
          <p className="mt-1 text-xl font-extrabold text-emerald-400">{stats.delivered_count}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase">Completed</p>
          <p className="mt-1 text-xl font-extrabold text-emerald-300">{stats.completed_count}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase">Cancelled</p>
          <p className="mt-1 text-xl font-extrabold text-rose-400">{stats.cancelled_count}</p>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3 text-center">
          <p className="text-[11px] font-semibold text-slate-400 uppercase">Expired</p>
          <p className="mt-1 text-xl font-extrabold text-slate-400">{stats.expired_count}</p>
        </div>
      </div>

      {/* Tabs Bar */}
      <div className="flex border-b border-slate-800 gap-4">
        <button
          onClick={() => setActiveTab('donations')}
          className={`pb-3 text-sm font-bold border-b-2 transition ${
            activeTab === 'donations' ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          All Donations ({donations.length})
        </button>
        <button
          onClick={() => setActiveTab('active')}
          className={`pb-3 text-sm font-bold border-b-2 transition ${
            activeTab === 'active' ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          Active Deliveries ({activeDonations.length})
        </button>
        <button
          onClick={() => setActiveTab('urgent')}
          className={`pb-3 text-sm font-bold border-b-2 transition ${
            activeTab === 'urgent' ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-400 hover:text-white'
          }`}
        >
          Urgent ({urgentDonations.length})
        </button>
      </div>

      {/* Table Display */}
      <section className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-950 text-xs font-semibold uppercase text-slate-400">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Food</th>
                <th className="px-4 py-3">Quantity</th>
                <th className="px-4 py-3">Donor</th>
                <th className="px-4 py-3">NGO</th>
                <th className="px-4 py-3">Freshness</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {(activeTab === 'active' ? activeDonations : activeTab === 'urgent' ? urgentDonations : donations).length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-slate-500">
                    No records found.
                  </td>
                </tr>
              ) : (
                (activeTab === 'active' ? activeDonations : activeTab === 'urgent' ? urgentDonations : donations).map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3 font-mono text-xs text-slate-400">#{d.id}</td>
                    <td className="px-4 py-3 font-bold text-white">{d.food}</td>
                    <td className="px-4 py-3 text-amber-300 font-semibold text-xs">{d.quantity}</td>
                    <td className="px-4 py-3 text-slate-300">{d.donor_name || d.donor_email || 'Donor'}</td>
                    <td className="px-4 py-3 font-semibold text-amber-300">{d.ngo}</td>
                    <td className="px-4 py-3 font-bold text-emerald-400">{d.freshness}%</td>
                    <td className="px-4 py-3 font-semibold">{d.priority}</td>
                    <td className="px-4 py-3">
                      <select
                        value={d.status}
                        onChange={(e) => handleStatusChange(d.id, e.target.value)}
                        className="rounded-xl border border-slate-700 bg-slate-950 px-2.5 py-1 text-xs font-bold text-amber-300 focus:outline-none"
                      >
                        <option value="AVAILABLE">AVAILABLE</option>
                        <option value="ACCEPTED">ACCEPTED</option>
                        <option value="PICKUP_SCHEDULED">PICKUP_SCHEDULED</option>
                        <option value="PICKED_UP">PICKED_UP</option>
                        <option value="IN_TRANSIT">IN_TRANSIT</option>
                        <option value="DELIVERED">DELIVERED</option>
                        <option value="COMPLETED">COMPLETED</option>
                        <option value="CANCELLED">CANCELLED</option>
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        to={`/track/${d.id}`}
                        className="rounded-xl bg-amber-400/10 border border-amber-400/30 px-3 py-1 text-xs font-bold text-amber-300 hover:bg-amber-400 hover:text-slate-950 transition"
                      >
                        Track
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default Admin
