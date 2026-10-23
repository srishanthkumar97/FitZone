import { Link } from 'react-router-dom'
import { FaDumbbell } from 'react-icons/fa'
import { FiArrowUpRight, FiClock, FiMapPin, FiPhone } from 'react-icons/fi'
import { gymInfo, socialLinks } from '../data/gymData'

const footerLinks = [
  { label: 'About', to: '/about' },
  { label: 'Facilities', to: '/facilities' },
  { label: 'Membership', to: '/membership' },
  { label: 'Trainers', to: '/trainers' },
  { label: 'Gallery', to: '/gallery' },
  { label: 'Contact', to: '/contact' },
]
const copyrightYear = new Date().getFullYear()

function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-footer-main">
        <div className="site-footer-brand">
          <Link className="brand" to="/" aria-label={`${gymInfo.name} home`}>
            <span className="brand-mark" aria-hidden="true"><FaDumbbell /></span>
            <span className="brand-name">{gymInfo.name.toUpperCase()}</span>
          </Link>
          <p>A welcoming space to train with purpose, find your strength, and keep moving forward.</p>
          <a className="footer-cta-link" href={`https://wa.me/${gymInfo.whatsapp}`} target="_blank" rel="noreferrer">
            Start a conversation <FiArrowUpRight aria-hidden="true" />
          </a>
          <nav className="site-footer-links" aria-label="Social media">
            {socialLinks.map(({ name, href }) => (
              <a key={name} href={href} target="_blank" rel="noreferrer">{name}</a>
            ))}
          </nav>
        </div>

        <div className="site-footer-links">
          <h2>Explore</h2>
          {footerLinks.map(({ label, to }) => <Link key={to} to={to}>{label}</Link>)}
        </div>

        <div className="site-footer-contact">
          <h2>Find {gymInfo.name}</h2>
          <p><FiMapPin aria-hidden="true" />{gymInfo.address}</p>
          <a href={`tel:${gymInfo.phone}`}><FiPhone aria-hidden="true" />{gymInfo.phoneDisplay}</a>
          <p><FiClock aria-hidden="true" />{gymInfo.hours[0].days} · {gymInfo.hours[0].time}</p>
        </div>
      </div>
      <div className="site-footer-bottom">
        <span>© {copyrightYear} {gymInfo.name}. All rights reserved.</span>
        <span>TRAIN WITH PURPOSE. EVERY DAY.</span>
      </div>
    </footer>
  )
}

export default Footer