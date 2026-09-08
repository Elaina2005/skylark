import { NavLink, Routes, Route, Link } from 'react-router-dom'
import Home from './pages/Home'
import Donations from './pages/Donations'
import NGOs from './pages/NGOs'
import Volunteers from './pages/Volunteers'
import Register from './pages/Register'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Admin from './pages/Admin'
import TrackDonation from './pages/TrackDonation'
import FoodNearby from './pages/FoodNearby'
import MapView from './pages/MapView'
import PrivateRoute from './components/PrivateRoute'
import AdminRoute from './components/AdminRoute'
import { AuthProvider, useAuth } from './authContext'

const navClass = ({ isActive }) =>
  isActive
    ? 'text-slate-950 bg-amber-400 font-bold rounded-xl px-4 py-2 text-sm shadow-md transition'
    : 'text-slate-300 hover:text-white hover:bg-slate-800/60 rounded-xl px-4 py-2 text-sm font-medium transition'

function AppContent() {
  const { isAuthenticated, user, signOut } = useAuth()
  const isNgo = user?.role === 'ngo'
  const isAdmin = user?.is_admin || user?.role === 'admin'

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100 selection:bg-amber-400 selection:text-slate-950">
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md py-4 px-6">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-400 text-slate-950 font-bold text-xl shadow-lg shadow-amber-400/20 group-hover:scale-105 transition">
              🥗
            </div>
            <div>
              <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
                Food Donation Network
              </h1>
            </div>
          </Link>

          <nav className="flex flex-wrap items-center gap-2">
            <NavLink to="/" className={navClass} end>
              Home
            </NavLink>

            {/* Role-tailored Navigation Links */}
            {isAdmin ? (
              <>
                <NavLink to="/admin" className={navClass}>
                  Dashboard
                </NavLink>
                <NavLink to="/donations" className={navClass}>
                  Donations
                </NavLink>
                <NavLink to="/ngos" className={navClass}>
                  NGOs
                </NavLink>
                <NavLink to="/volunteers" className={navClass}>
                  Volunteers
                </NavLink>
                <NavLink to="/track" className={navClass}>
                  Track
                </NavLink>
              </>
            ) : isNgo ? (
              <>
                <NavLink to="/donations/nearby" className={navClass}>
                  Food Nearby
                </NavLink>
                <NavLink to="/dashboard" className={navClass}>
                  My Requests
                </NavLink>
                <NavLink to="/map" className={navClass}>
                  Map View
                </NavLink>
                <NavLink to="/track" className={navClass}>
                  Track
                </NavLink>
              </>
            ) : (
              <>
                <Link to="/#donate-form" className="text-slate-300 hover:text-white hover:bg-slate-800/60 rounded-xl px-4 py-2 text-sm font-medium transition">
                  Donate Food
                </Link>
                <NavLink to="/donations/nearby" className={navClass}>
                  Food Nearby
                </NavLink>
                {isAuthenticated && (
                  <NavLink to="/dashboard" className={navClass}>
                    My Donations
                  </NavLink>
                )}
                <NavLink to="/track" className={navClass}>
                  Track
                </NavLink>
              </>
            )}

            {isAuthenticated ? (
              <div className="flex items-center gap-2 border-l border-slate-800 pl-3">
                <span className="text-xs text-amber-300 font-semibold hidden sm:inline bg-amber-400/10 border border-amber-400/20 px-2.5 py-1 rounded-full">
                  👤 {user?.username} ({user?.role?.toUpperCase() || 'DONOR'})
                </span>
                <button
                  onClick={signOut}
                  className="rounded-xl bg-slate-800 px-3.5 py-2 text-xs font-semibold text-slate-200 hover:bg-rose-500 hover:text-white transition"
                >
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 border-l border-slate-800 pl-3">
                <NavLink to="/login" className={navClass}>
                  Sign In
                </NavLink>
                <NavLink
                  to="/register"
                  className="rounded-xl bg-amber-400 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-amber-300 transition shadow-md shadow-amber-400/10"
                >
                  Register
                </NavLink>
              </div>
            )}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/donations" element={<Donations />} />
          <Route path="/donations/nearby" element={<FoodNearby />} />
          <Route path="/track" element={<TrackDonation />} />
          <Route path="/track/:id" element={<TrackDonation />} />
          <Route path="/map" element={<MapView />} />
          <Route path="/ngos" element={<NGOs />} />
          <Route path="/volunteers" element={<Volunteers />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <Admin />
              </AdminRoute>
            }
          />
        </Routes>
      </main>

      <footer className="border-t border-slate-800/80 bg-slate-950 py-8 px-6 text-center text-xs text-slate-500">
        <div className="mx-auto max-w-6xl flex flex-col md:flex-row justify-between items-center gap-4">
          <p>© 2026 Food Donation Network. Connecting Surplus Food With People Who Need It.</p>
          <div className="flex gap-6 text-slate-400">
            <Link to="/" className="hover:text-amber-300 transition">Home</Link>
            <Link to="/donations/nearby" className="hover:text-amber-300 transition">Food Nearby</Link>
            <Link to="/track" className="hover:text-amber-300 transition">Track</Link>
            <Link to="/map" className="hover:text-amber-300 transition">Map</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
