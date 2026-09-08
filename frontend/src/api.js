import axios from 'axios'
import { getToken } from './auth'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const login = (payload) => api.post('/login', payload).then((res) => res.data)
export const predictFreshness = (payload) => api.post('/predict', payload).then((res) => res.data)
export const donateFood = (payload) => api.post('/donate', payload).then((res) => res.data)
export const getDonations = (params) => api.get('/donations', { params }).then((res) => res.data)
export const getMyDonations = (params) => api.get('/my-donations', { params }).then((res) => res.data)
export const registerUser = (payload) => api.post('/register', payload).then((res) => res.data)
export const getNGOs = () => api.get('/ngos').then((res) => res.data)
export const createNGO = (payload) => api.post('/ngos', payload).then((res) => res.data)
export const updateNGO = (id, payload) => api.put(`/ngos/${id}`, payload).then((res) => res.data)
export const deleteNGO = (id) => api.delete(`/ngos/${id}`)
export const getVolunteers = () => api.get('/volunteers').then((res) => res.data)
export const createVolunteer = (payload) => api.post('/volunteers', payload).then((res) => res.data)
export const updateVolunteer = (id, payload) => api.put(`/volunteers/${id}`, payload).then((res) => res.data)
export const deleteVolunteer = (id) => api.delete(`/volunteers/${id}`)
export const getMe = () => api.get('/me').then((res) => res.data)
export const getNearbyDonations = (params) => api.get('/donations/nearby', { params }).then((res) => res.data)
export const getDonationById = (id) => api.get(`/donations/${id}`).then((res) => res.data)
export const getDonationTrackingHistory = (id) => api.get(`/donations/${id}/tracking`).then((res) => res.data)
export const updateDonationStatus = (id, payload) => api.put(`/donations/${id}/status`, payload).then((res) => res.data)
export const acceptDonation = (id) => api.post(`/donations/${id}/accept`).then((res) => res.data)
export const confirmDonationReceipt = (id) => api.post(`/donations/${id}/confirm-receipt`).then((res) => res.data)
export const getAdminDonations = (params) => api.get('/admin/donations', { params }).then((res) => res.data)
export const getAdminStats = () => api.get('/admin/stats').then((res) => res.data)
export const exportAdminDonationsCSV = (params) =>
  api.get('/admin/donations/export', { params, responseType: 'blob' }).then((res) => res.data)

export const getFoods = () => api.get('/foods').then((res) => res.data)

export default api

