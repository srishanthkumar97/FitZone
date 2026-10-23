import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { FaDumbbell } from 'react-icons/fa'
import { FiArrowUpRight, FiMenu, FiX } from 'react-icons/fi'
import { gymInfo } from '../data/gymData'
import { useAuth } from '../auth/authContext'

const navigationItems = [
  { label: 'Home', to: '/#home', section: 'home' },
  { label: 'About', to: '/#about', section: 'about' },
  { label: 'Facilities', to: '/#facilities', section: 'facilities' },
  { label: 'Programs', to: '/#programs', section: 'programs' },
  { label: 'Membership', to: '/#membership', section: 'membership' },
  { label: 'Trainers', to: '/#trainers', section: 'trainers' },
  { label: 'Gallery', to: '/#gallery', section: 'gallery' },
  { label: 'Contact', to: '/#contact', section: 'contact' },
]

const memberNavigationItems = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Profile', to: '/profile' },
  { label: 'Membership', to: '/membership' },
  { label: 'Attendance', to: '/attendance' },
  { label: 'Workouts', to: '/workouts' },
  { label: 'Progress', to: '/progress' },
]

const adminNavigationItems = [
  { label: 'Admin Dashboard', to: '/admin' },
  { label: 'Members', to: '/admin/members' },
  { label: 'Membership Plans', to: '/admin/membership' },
  { label: 'Attendance', to: '/admin/attendance' },
  { label: 'Announcements', to: '/admin/announcements' },
]

function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [activeSection, setActiveSection] = useState('home')
  const navbarRef = useRef(null)
  const toggleRef = useRef(null)
  const location = useLocation()
  const { token, user, signOut } = useAuth()
  const role = token && user ? user.role : null
  const isPortal = role === 'member' || role === 'admin'
  const items = role === 'member'
    ? memberNavigationItems
    : role === 'admin'
      ? adminNavigationItems
      : navigationItems

  function closeMenu() {
    setMenuOpen(false)
  }

  useEffect(() => {
    if (!menuOpen) return undefined

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        closeMenu()
        toggleRef.current?.focus()
      }
    }

    function handleOutsideClick(event) {
      if (!navbarRef.current?.contains(event.target)) closeMenu()
    }

    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('pointerdown', handleOutsideClick)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('pointerdown', handleOutsideClick)
    }
  }, [menuOpen])

  useEffect(() => {
    if (location.pathname !== '/' || isPortal) {
      return undefined
    }

    let frame = 0
    function updateActiveSection() {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        const headerHeight = navbarRef.current?.offsetHeight ?? 72
        const marker = headerHeight + window.innerHeight * 0.22
        let currentSection = 'home'

        navigationItems.forEach(({ section }) => {
          const element = document.getElementById(section)
          if (element && element.getBoundingClientRect().top <= marker) {
            currentSection = section
          }
        })

        setActiveSection((current) => (
          current === currentSection ? current : currentSection
        ))
      })
    }

    updateActiveSection()
    window.addEventListener('scroll', updateActiveSection, { passive: true })
    window.addEventListener('resize', updateActiveSection)

    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('scroll', updateActiveSection)
      window.removeEventListener('resize', updateActiveSection)
    }
  }, [location.pathname, isPortal])

  return (
    <header className={`site-header${isPortal ? ' site-header--portal' : ''}`}>
      <nav className={`navbar${isPortal ? ' navbar--portal' : ''}`} aria-label="Main navigation" ref={navbarRef}>
        <Link className="brand" to={isPortal ? (role === 'admin' ? '/admin' : '/dashboard') : '/#home'} onClick={closeMenu} aria-label={`${gymInfo.name} home`}>
          <span className="brand-mark" aria-hidden="true">
            <FaDumbbell />
          </span>
          <span className="brand-name">{gymInfo.name.toUpperCase()}</span>
        </Link>

        <button
          ref={toggleRef}
          className="menu-toggle"
          type="button"
          aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={menuOpen}
          aria-controls="primary-navigation"
          onClick={() => setMenuOpen((isOpen) => !isOpen)}
        >
          {menuOpen ? <FiX aria-hidden="true" /> : <FiMenu aria-hidden="true" />}
        </button>

        <ul
          className={`nav-links${isPortal ? ' portal-nav-links' : ''}${menuOpen ? ' is-open' : ''}`}
          id="primary-navigation"
        >
          {items.map((item) => {
            const active = item.section
              ? location.pathname === '/' && activeSection === item.section
              : location.pathname === item.to
            return (
            <li key={item.label}>
              <Link
                to={item.to}
                onClick={closeMenu}
                className={active ? 'is-active' : ''}
                aria-current={active ? 'page' : undefined}
              >
                {item.label}
              </Link>
            </li>
            )
          })}
          {isPortal
            ? <li><button className="nav-account-action" type="button" onClick={() => { closeMenu(); signOut() }}>Sign Out</button></li>
            : <>
                <li><Link to="/login" onClick={closeMenu}>Login</Link></li>
                <li>
                  <Link className="nav-join" to="/#membership" onClick={closeMenu}>
                    Join Now
                    <FiArrowUpRight aria-hidden="true" />
                  </Link>
                </li>
              </>}
        </ul>
      </nav>
    </header>
  )
}

export default Navbar