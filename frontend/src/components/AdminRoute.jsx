import { Navigate } from 'react-router-dom'
import { useAuth } from '../authContext'

function AdminRoute({ children }) {
  const { loading, isAuthenticated, user } = useAuth()

  if (loading) {
    return (
      <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-8 text-slate-300 shadow-xl shadow-slate-950/20">
        Loading authentication status…
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!user?.is_admin) {
    return (
      <div className="rounded-3xl border border-rose-800 bg-rose-950/80 p-8 text-rose-200 shadow-xl shadow-rose-950/20">
        <h2 className="text-xl font-semibold">Access Denied</h2>
        <p className="mt-2">You do not have permission to access this page.</p>
      </div>
    )
  }

  return children
}

export default AdminRoute
