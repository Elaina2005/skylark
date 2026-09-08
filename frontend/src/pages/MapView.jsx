import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDonations, getNGOs } from '../api'

function MapView() {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const [donations, setDonations] = useState([])
  const [ngos, setNgos] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [donationsData, ngosData] = await Promise.all([getDonations(), getNGOs()])
      setDonations(donationsData)
      setNgos(ngosData)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (loading || !mapRef.current) return
    if (!window.L) return

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove()
    }

    const map = window.L.map(mapRef.current).setView([13.0827, 80.2707], 12)
    mapInstanceRef.current = map

    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
    }).addTo(map)

    // Add NGO Markers
    ngos.forEach((ngo) => {
      const lat = ngo.latitude || 13.0827
      const lon = ngo.longitude || 80.2707
      const popupHtml = `
        <div style="color: #0f172a; font-family: sans-serif; padding: 4px;">
          <h4 style="margin:0; font-size: 14px; font-weight: bold; color: #d97706;">🏢 ${ngo.name}</h4>
          <p style="margin:4px 0; font-size: 12px;">City: ${ngo.city || 'Chennai'}</p>
        </div>
      `
      window.L.marker([lat, lon]).addTo(map).bindPopup(popupHtml)
    })

    // Add Donation Markers
    donations.forEach((d) => {
      const lat = d.latitude || 13.0827 + (Math.random() - 0.5) * 0.05
      const lon = d.longitude || 80.2707 + (Math.random() - 0.5) * 0.05

      const popupHtml = `
        <div style="color: #0f172a; font-family: sans-serif; padding: 4px; min-width: 160px;">
          <h4 style="margin:0; font-size: 14px; font-weight: bold; color: #059669;">🍲 ${d.food}</h4>
          <p style="margin:4px 0; font-size: 12px;">Quantity: <strong>${d.quantity}</strong></p>
          <p style="margin:2px 0; font-size: 12px;">Freshness: <strong>${d.freshness}%</strong></p>
          <div style="margin-top: 6px;">
            <a href="/track/${d.id}" style="display: inline-block; background: #d97706; color: #fff; text-decoration: none; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">Track →</a>
          </div>
        </div>
      `
      window.L.marker([lat, lon]).addTo(map).bindPopup(popupHtml)
    })

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [loading, donations, ngos])

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-4">
        <h2 className="text-3xl font-extrabold text-white">Interactive Map</h2>
        <Link
          to="/donations/nearby"
          className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-bold text-amber-300 hover:bg-slate-800 transition"
        >
          List View
        </Link>
      </div>

      <section className="rounded-3xl border border-slate-800 bg-slate-900 p-3 shadow-xl overflow-hidden">
        <div ref={mapRef} className="h-[550px] w-full rounded-2xl z-10"></div>
      </section>
    </div>
  )
}

export default MapView
