import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getFoods, predictFreshness, donateFood, getNearbyDonations } from '../api'

const QUICK_PRESETS = [
  { food: 'Biryani', quantity: '20 portions', storageCondition: 'Room Temperature' },
  { food: 'Chapati', quantity: '15 portions', storageCondition: 'Room Temperature' },
  { food: 'Idli', quantity: '25 portions', storageCondition: 'Hot/Heated' },
  { food: 'Fried Rice', quantity: '10 portions', storageCondition: 'Refrigerated' },
  { food: 'Paneer Curry', quantity: '12 portions', storageCondition: 'Hot/Heated' },
]

function Home() {
  const [foodsList, setFoodsList] = useState([])
  const [food, setFood] = useState('Biryani')
  const [selectedFoodMeta, setSelectedFoodMeta] = useState(null)
  const [quantity, setQuantity] = useState('20 portions')
  const [cookedDate, setCookedDate] = useState(() => new Date().toISOString().split('T')[0])
  const [cookedTime, setCookedTime] = useState('12:00')
  const [storageCondition, setStorageCondition] = useState('Room Temperature')
  const [location, setLocation] = useState('Anna Nagar, Chennai')

  const [loading, setLoading] = useState(false)
  const [prediction, setPrediction] = useState(null)
  const [nearbyNgos, setNearbyNgos] = useState([])
  const [saved, setSaved] = useState(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchFoodDataset()
  }, [])

  const fetchFoodDataset = async () => {
    try {
      const data = await getFoods()
      setFoodsList(data)
      const defaultItem = data.find((f) => f.food.toLowerCase() === 'biryani') || data[0]
      if (defaultItem) {
        setFood(defaultItem.food)
        setSelectedFoodMeta(defaultItem)
      }
    } catch (err) {
      console.error('Could not load foods list:', err)
    }
  }

  const handleFoodSelect = (foodName) => {
    setFood(foodName)
    const item = foodsList.find((f) => f.food.toLowerCase() === foodName.toLowerCase())
    setSelectedFoodMeta(item || null)
  }

  const handleQuickPreset = async (preset) => {
    handleFoodSelect(preset.food)
    setQuantity(preset.quantity)
    setStorageCondition(preset.storageCondition)
    
    // Instant auto check
    setError('')
    setSaved(null)
    setPrediction(null)
    setLoading(true)

    try {
      const result = await predictFreshness({
        food: preset.food,
        quantity: preset.quantity,
        cooked_time: cookedTime,
        cooked_date: cookedDate,
        storage_condition: preset.storageCondition,
        location,
      })
      setPrediction(result)

      const nearby = await getNearbyDonations({ lat: 13.0827, lon: 80.2707 })
      setNearbyNgos(nearby.slice(0, 3))
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to calculate freshness')
    } finally {
      setLoading(false)
    }
  }

  const handlePredict = async (event) => {
    event.preventDefault()
    setError('')
    setSaved(null)
    setPrediction(null)
    setLoading(true)

    try {
      const result = await predictFreshness({
        food,
        quantity,
        cooked_time: cookedTime,
        cooked_date: cookedDate,
        storage_condition: storageCondition,
        location,
      })
      setPrediction(result)

      const nearby = await getNearbyDonations({ lat: 13.0827, lon: 80.2707 })
      setNearbyNgos(nearby.slice(0, 3))
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to calculate freshness')
    } finally {
      setLoading(false)
    }
  }

  const handleDonate = async () => {
    if (!prediction) return
    setError('')
    setLoading(true)

    try {
      const result = await donateFood({
        food,
        quantity,
        cooked_time: cookedTime,
        cooked_date: cookedDate,
        storage_condition: storageCondition,
        location,
      })
      setSaved(result)
      setTimeout(() => {
        navigate(`/track/${result.id}`)
      }, 500)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to create donation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-10 pb-12">
      {/* Clean Hero Banner */}
      <section className="relative overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/90 p-8 md:p-12 shadow-xl">
        <div className="relative z-10 max-w-3xl space-y-4">
          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl lg:text-5xl leading-tight">
            Connect Surplus Food With People Who Need It
          </h1>
          <p className="text-base text-slate-300">
            Donate surplus food, find nearby NGOs and track every delivery.
          </p>
          <div className="flex flex-wrap gap-4 pt-2">
            <a
              href="#donate-form"
              className="inline-flex items-center justify-center rounded-2xl bg-amber-400 px-6 py-3.5 font-bold text-slate-950 shadow-md transition hover:bg-amber-300 text-sm"
            >
              Donate Food
            </a>
            <Link
              to="/donations/nearby"
              className="inline-flex items-center justify-center rounded-2xl border border-slate-700 bg-slate-950 px-6 py-3.5 font-bold text-amber-300 transition hover:bg-slate-800 text-sm"
            >
              Find Food Nearby
            </Link>
          </div>
        </div>
      </section>

      {/* Donate Food Section */}
      <section id="donate-form" className="rounded-3xl border border-slate-800 bg-slate-900/90 p-8 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <h2 className="text-2xl font-bold text-white">Donate Food</h2>

          {/* Quick Preset Buttons */}
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-xs font-semibold text-slate-400">⚡ Quick Presets:</span>
            {QUICK_PRESETS.map((p) => (
              <button
                key={p.food}
                type="button"
                onClick={() => handleQuickPreset(p)}
                className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-1 text-xs font-bold text-amber-300 hover:bg-amber-400 hover:text-slate-950 transition"
              >
                + {p.food}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handlePredict} className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <label className="space-y-2 text-slate-200 text-sm font-semibold sm:col-span-2 lg:col-span-1">
            Food Name
            <select
              value={food}
              onChange={(e) => handleFoodSelect(e.target.value)}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 font-bold focus:border-amber-400 focus:outline-none"
              required
            >
              {foodsList.map((f) => (
                <option key={f.food} value={f.food}>
                  {f.food} ({f.category})
                </option>
              ))}
            </select>
          </label>

          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 flex flex-col justify-center text-xs space-y-1 sm:col-span-2 lg:col-span-2">
            <p className="text-slate-400">
              Category: <span className="text-white font-semibold">{selectedFoodMeta?.category || 'Rice and Meat'}</span>
            </p>
            <p className="text-slate-400">
              Estimated Freshness Duration: <span className="text-amber-300 font-bold text-sm">{selectedFoodMeta?.estimated_freshness_hours || 3} hours</span>
            </p>
          </div>

          <label className="space-y-2 text-slate-200 text-sm font-semibold">
            Quantity
            <input
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 placeholder-slate-500 focus:border-amber-400 focus:outline-none"
              placeholder="e.g. 20 portions"
              required
            />
          </label>

          <label className="space-y-2 text-slate-200 text-sm font-semibold">
            Cooking Date
            <input
              type="date"
              value={cookedDate}
              onChange={(e) => setCookedDate(e.target.value)}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-amber-400 focus:outline-none"
              required
            />
          </label>

          <label className="space-y-2 text-slate-200 text-sm font-semibold">
            Cooking Time
            <input
              type="time"
              value={cookedTime}
              onChange={(e) => setCookedTime(e.target.value)}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-amber-400 focus:outline-none"
              required
            />
          </label>

          <label className="space-y-2 text-slate-200 text-sm font-semibold sm:col-span-2 lg:col-span-1">
            Storage Condition
            <select
              value={storageCondition}
              onChange={(e) => setStorageCondition(e.target.value)}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-amber-400 focus:outline-none"
              required
            >
              <option value="Room Temperature">Room Temperature</option>
              <option value="Refrigerated">Refrigerated</option>
              <option value="Hot/Heated">Hot / Heated</option>
            </select>
          </label>

          <label className="space-y-2 text-slate-200 text-sm font-semibold sm:col-span-2">
            Location
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 placeholder-slate-500 focus:border-amber-400 focus:outline-none"
              placeholder="e.g. Anna Nagar, Chennai"
              required
            />
          </label>

          <div className="sm:col-span-2 lg:col-span-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto rounded-2xl bg-amber-400 px-8 py-3.5 font-bold text-slate-950 transition hover:bg-amber-300 disabled:opacity-60 text-sm"
            >
              {loading ? 'Checking…' : 'Check Freshness'}
            </button>
          </div>
        </form>

        {error && <p className="mt-4 rounded-2xl bg-rose-500/15 border border-rose-500/30 px-4 py-3 text-sm text-rose-200">{error}</p>}
      </section>

      {/* Freshness Result Card */}
      {prediction && (
        <section className="rounded-3xl border border-slate-800 bg-slate-900/90 p-8 shadow-xl space-y-6">
          <h3 className="text-xl font-bold text-white border-b border-slate-800 pb-4">
            Freshness Result
          </h3>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-950 p-5 border border-slate-800">
              <span className="text-slate-400 text-xs block font-medium">Estimated Freshness</span>
              <strong className="text-emerald-400 text-3xl font-bold mt-1 block">{prediction.freshness}%</strong>
            </div>
            <div className="rounded-2xl bg-slate-950 p-5 border border-slate-800">
              <span className="text-slate-400 text-xs block font-medium">Remaining Time</span>
              <strong className="text-amber-300 text-3xl font-bold mt-1 block">{prediction.remaining_hours} hrs</strong>
            </div>
            <div className="rounded-2xl bg-slate-950 p-5 border border-slate-800">
              <span className="text-slate-400 text-xs block font-medium">Priority</span>
              <strong className={`text-3xl font-bold mt-1 block ${prediction.priority === 'High' ? 'text-rose-400' : 'text-emerald-400'}`}>
                {prediction.priority}
              </strong>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 text-xs text-slate-400">
            Note: {prediction.disclaimer}
          </div>

          {/* Nearby NGOs List */}
          <div className="pt-4 border-t border-slate-800 space-y-4">
            <h4 className="text-lg font-bold text-white">Nearby NGOs</h4>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl bg-slate-950 p-4 border border-slate-800 flex justify-between items-center">
                <div>
                  <h5 className="font-bold text-white">{prediction.ngo}</h5>
                  <p className="text-xs text-slate-400">1.8 km away</p>
                </div>
                <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">Available</span>
              </div>
              <div className="rounded-2xl bg-slate-950 p-4 border border-slate-800 flex justify-between items-center">
                <div>
                  <h5 className="font-bold text-white">Food Bank</h5>
                  <p className="text-xs text-slate-400">3.2 km away</p>
                </div>
                <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">Available</span>
              </div>
              <div className="rounded-2xl bg-slate-950 p-4 border border-slate-800 flex justify-between items-center">
                <div>
                  <h5 className="font-bold text-white">Helping Hands</h5>
                  <p className="text-xs text-slate-400">5.1 km away</p>
                </div>
                <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">Available</span>
              </div>
            </div>
          </div>

          <div className="pt-2 flex gap-4">
            <button
              type="button"
              onClick={handleDonate}
              disabled={loading}
              className="rounded-2xl bg-emerald-500 px-6 py-3.5 text-sm font-bold text-white transition hover:bg-emerald-400 shadow-md"
            >
              Confirm Donation
            </button>
          </div>
        </section>
      )}

      {saved && (
        <section className="rounded-3xl border border-emerald-500/40 bg-emerald-950/80 p-6 text-emerald-100 shadow-xl">
          <p className="text-sm font-bold text-emerald-300">
            Donation created successfully! Redirecting to tracking…
          </p>
        </section>
      )}
    </div>
  )
}

export default Home
