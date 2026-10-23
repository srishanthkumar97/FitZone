import { useCallback, useEffect, useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext.jsx'
import { useAuth } from './auth/authContext'
import ProtectedRoute from './auth/ProtectedRoute'
import Navbar from './components/Navbar'
import IntroAnimation from './components/IntroAnimation'
import HomePage from './components/HomePage'
import Footer from './components/Footer'
import {
  AboutPage,
  ContactPage,
  FacilitiesPage,
  GalleryPage,
  MembershipPage,
  TrainersPage,
} from './components/SitePages'
import {
  AdminAnnouncementsPage,
  AdminAttendancePage,
  AdminDashboardPage,
  AdminMembersPage,
  AdminMembershipPage,
  AttendancePage,
  LoginPage,
  MemberDashboardPage,
  MemberMembershipPage,
  ProfilePage,
  ProgressPage,
  RegisterPage,
  WorkoutsPage,
} from './components/PortalPages'
import './App.css'

function RouteContent() {
  const { user } = useAuth()
  const [introExiting, setIntroExiting] = useState(false)
  const [introComplete, setIntroComplete] = useState(false)
  const handleIntroExit = useCallback(() => setIntroExiting(true), [])
  const handleIntroComplete = useCallback(() => setIntroComplete(true), [])
  const location = useLocation()

  useEffect(() => {
    if (location.hash) {
      const frame = window.requestAnimationFrame(() => {
        document.querySelector(location.hash)?.scrollIntoView({ behavior: 'smooth' })
      })
      return () => window.cancelAnimationFrame(frame)
    }

    window.scrollTo({ top: 0, behavior: 'auto' })
    return undefined
  }, [location.pathname, location.hash])

  return (
    <>
      {!introComplete && (
        <IntroAnimation
          onExitStart={handleIntroExit}
          onComplete={handleIntroComplete}
        />
      )}
      <div
        className={`home-page ${
          introComplete ? 'home-visible' : introExiting ? 'home-entering' : 'home-hidden'
        }`}
        aria-hidden={!introComplete}
        inert={!introComplete}
      >
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/facilities" element={<FacilitiesPage />} />
          <Route
            path="/membership"
            element={
              user?.role === 'member'
                ? <ProtectedRoute><MemberMembershipPage /></ProtectedRoute>
                : user?.role === 'admin'
                  ? <Navigate to="/admin/membership" replace />
                  : <MembershipPage />
            }
          />
          <Route path="/trainers" element={<TrainersPage />} />
          <Route path="/gallery" element={<GalleryPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<ProtectedRoute><MemberDashboardPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/attendance" element={<ProtectedRoute><AttendancePage /></ProtectedRoute>} />
          <Route path="/workouts" element={<ProtectedRoute><WorkoutsPage /></ProtectedRoute>} />
          <Route path="/progress" element={<ProtectedRoute><ProgressPage /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute adminOnly><AdminDashboardPage /></ProtectedRoute>} />
          <Route path="/admin/members" element={<ProtectedRoute adminOnly><AdminMembersPage /></ProtectedRoute>} />
          <Route path="/admin/membership" element={<ProtectedRoute adminOnly><AdminMembershipPage /></ProtectedRoute>} />
          <Route path="/admin/attendance" element={<ProtectedRoute adminOnly><AdminAttendancePage /></ProtectedRoute>} />
          <Route path="/admin/announcements" element={<ProtectedRoute adminOnly><AdminAnnouncementsPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Footer />
      </div>
    </>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <RouteContent />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
