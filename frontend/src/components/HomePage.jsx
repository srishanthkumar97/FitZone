import { useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  FaBicycle,
  FaDumbbell,
  FaHeartbeat,
  FaShieldAlt,
  FaUserTie,
  FaWeight,
} from 'react-icons/fa'
import {
  FiArrowDown,
  FiArrowRight,
  FiArrowUpRight,
  FiClock,
  FiMapPin,
  FiMessageCircle,
  FiPhone,
  FiZap,
} from 'react-icons/fi'
import {
  gymInfo,
  homeFacilities,
  homeMembershipPlans,
  homeTrainers,
  siteImages,
  testimonials,
  trainingPrograms,
} from '../data/gymData'
import './HomePage.css'

const iconMap = {
  strength: FaDumbbell,
  cardio: FaHeartbeat,
  weights: FaWeight,
  functional: FaBicycle,
  personal: FaUserTie,
}

const featureItems = [
  { icon: FaDumbbell, title: 'Modern Equipment', detail: 'Built for every goal' },
  { icon: FaUserTie, title: 'Expert Trainers', detail: 'Coaching that counts' },
  { icon: FiZap, title: 'Personal Training', detail: 'Your plan, your pace' },
  { icon: FaShieldAlt, title: 'Clean & Safe', detail: 'Space to train with confidence' },
]

const revealVariants = {
  hidden: { opacity: 0, y: 26 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: [0.22, 0.61, 0.36, 1] },
  },
}

function Reveal({ children, className = '', delay = 0, reducedMotion }) {
  return (
    <motion.div
      className={className}
      variants={
        reducedMotion
          ? {
              hidden: { opacity: 1, y: 0 },
              visible: { opacity: 1, y: 0 },
            }
          : revealVariants
      }
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.16 }}
      transition={{ delay }}
    >
      {children}
    </motion.div>
  )
}

function ImageWithFallback({ src, alt, className = '', ...props }) {
  const [failed, setFailed] = useState(false)

  if (failed) {
    return (
      <div className={`home-image-fallback ${className}`} role="img" aria-label={alt}>
        <FaDumbbell aria-hidden="true" />
      </div>
    )
  }

  return (
    <img
      className={className}
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
      {...props}
    />
  )
}

function SectionHeading({ eyebrow, title, description, light = false }) {
  return (
    <div className={`home-section-heading${light ? ' home-section-heading--light' : ''}`}>
      <p className="home-eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {description && <p className="home-section-description">{description}</p>}
    </div>
  )
}

function HomePage() {
  const reducedMotion = useReducedMotion()

  return (
    <main className="home-content">
      <section className="home-hero" id="home" aria-labelledby="hero-title">
        <ImageWithFallback
          className="home-hero-image"
          src={siteImages.hero}
          alt="Dark, modern gym floor with strength and cardio equipment"
          loading="eager"
        />
        <div className="home-hero-overlay" />
        <div className="home-container home-hero-inner">
          <Reveal className="home-hero-copy" reducedMotion={reducedMotion}>
            <p className="home-eyebrow">
              <span /> STRONGER EVERY DAY
            </p>
            <h1 id="hero-title">
              YOUR FITNESS
              <br />
              JOURNEY <span>STARTS HERE</span>
            </h1>
            <p className="home-hero-description">
              Train harder. Move stronger. Become the best version of yourself.
            </p>
            <div className="home-hero-actions">
              <a className="home-button home-button--red"               href="#contact">
                JOIN NOW <FiArrowUpRight aria-hidden="true" />
              </a>
              <a
                className="home-button home-button--outline"
                href={`https://wa.me/${gymInfo.whatsapp}`}
                target="_blank"
                rel="noreferrer"
              >
                <FiMessageCircle aria-hidden="true" /> CHAT ON WHATSAPP
              </a>
            </div>
            <div className="home-hero-proof">
              <div className="home-proof-avatars" aria-hidden="true">
                <span>A</span>
                <span>M</span>
                <span>R</span>
              </div>
              <p>
                <strong>Your next chapter starts here</strong>
                <span>Good coaching. Great energy. Real progress.</span>
              </p>
            </div>
          </Reveal>
          <a className="home-scroll-cue" href="#about" aria-label="Scroll to facilities">
            <FiArrowDown aria-hidden="true" />
          </a>
          <div className="home-hero-index" aria-hidden="true">
            <span>01</span> / 04
          </div>
        </div>
      </section>

      <section className="home-feature-strip" id="about" aria-label={`Why train at ${gymInfo.name}`}>
        <div className="home-container home-feature-grid">
          {featureItems.map(({ icon: Icon, title, detail }, index) => (
            <Reveal
              className="home-feature"
              delay={index * 0.07}
              reducedMotion={reducedMotion}
              key={title}
            >
              <span className="home-feature-icon">
                <Icon aria-hidden="true" />
              </span>
              <span className="home-feature-copy">
                <strong>{title}</strong>
                <small>{detail}</small>
              </span>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="home-section home-facilities" id="facilities">
        <div className="home-container">
          <Reveal reducedMotion={reducedMotion}>
            <SectionHeading
              eyebrow="YOUR SPACE TO GET STRONGER"
              title="TRAIN. BUILD. TRANSFORM."
              description="Purpose-built spaces, great equipment, and room to make every session count."
            />
          </Reveal>
          <div className="home-facility-grid">
            {homeFacilities.map(({ title, description, image, icon }, index) => {
              const Icon = iconMap[icon] || FaDumbbell
              return (
              <Reveal
                className="home-facility-card"
                delay={index * 0.06}
                reducedMotion={reducedMotion}
                key={title}
              >
                <ImageWithFallback src={image} alt={`${title} at ${gymInfo.name}`} />
                <div className="home-facility-shade" />
                <div className="home-facility-content">
                  <span className="home-card-icon">
                    <Icon aria-hidden="true" />
                  </span>
                  <h3>{title}</h3>
                  <p>{description}</p>
                  <Link to="/facilities" aria-label={`Explore ${title}`}>
                    Explore facility <FiArrowRight aria-hidden="true" />
                  </Link>
                </div>
              </Reveal>
              )
            })}
          </div>
          <div className="home-section-action">
            <Link className="home-text-link" to="/facilities">
              VIEW ALL FACILITIES <FiArrowUpRight aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      <section className="home-section home-programs" id="programs">
        <div className="home-container">
          <Reveal reducedMotion={reducedMotion}>
            <SectionHeading
              eyebrow="PURPOSEFUL TRAINING"
              title="TRAIN FOR YOUR GOAL."
              description="Whatever you are working toward, build a plan that moves you forward."
            />
          </Reveal>
          <div className="home-program-grid">
            {trainingPrograms.map(({ title, text, image, icon, number }, index) => {
              const Icon = iconMap[icon] || FaDumbbell
              return (
              <Reveal
                className="home-program-card"
                delay={index * 0.06}
                reducedMotion={reducedMotion}
                key={title}
              >
                <div className="home-program-image">
                  <ImageWithFallback src={image} alt="" />
                  <span className="home-program-number">{number}</span>
                </div>
                <div className="home-program-body">
                  <span className="home-program-icon">
                    <Icon aria-hidden="true" />
                  </span>
                  <h3>{title}</h3>
                  <p>{text}</p>
                  <a href="#contact" aria-label={`Ask us about ${title}`}>
                    Find your program <FiArrowRight aria-hidden="true" />
                  </a>
                </div>
              </Reveal>
              )
            })}
          </div>
        </div>
      </section>

      <section className="home-section home-memberships" id="membership">
        <div className="home-container">
          <Reveal reducedMotion={reducedMotion}>
            <SectionHeading
              eyebrow="DEMO PRICING · EASY TO UPDATE"
              title="MEMBERSHIP PLANS."
              description="Straightforward options for every kind of training journey."
            />
          </Reveal>
          <div className="home-membership-grid">
            {homeMembershipPlans.map(({ name, price, period, note, features, popular }, index) => (
              <Reveal
                className={`home-membership-card${popular ? ' is-popular' : ''}`}
                delay={index * 0.08}
                reducedMotion={reducedMotion}
                key={name}
              >
                {popular && <div className="home-popular-label">MOST POPULAR</div>}
                <p className="home-plan-name">{name}</p>
                <p className="home-plan-note">{note}</p>
                <p className="home-plan-price">
                  {price}
                  <span>{period}</span>
                </p>
                <div className="home-plan-divider" />
                <ul>
                  {features.map((feature) => (
                    <li key={feature}>
                      <span aria-hidden="true">+</span> {feature}
                    </li>
                  ))}
                </ul>
                <a
                  className={popular ? 'home-button home-button--red' : 'home-button home-button--outline'}
                  href="#contact"
                >
                  GET STARTED <FiArrowUpRight aria-hidden="true" />
                </a>
              </Reveal>
            ))}
          </div>
          <p className="home-pricing-note">Demo pricing shown. Contact the team to confirm current plans.</p>
        </div>
      </section>

      <section className="home-section home-trainers" id="trainers">
        <div className="home-container">
          <Reveal reducedMotion={reducedMotion}>
            <SectionHeading
              eyebrow="GOOD PEOPLE. GREAT COACHING."
              title="MEET OUR TRAINERS."
              description="Coaches who listen, meet you where you are, and help you go further."
            />
          </Reveal>
          <div className="home-trainer-grid">
            {homeTrainers.map(({ name, role, experience, specialty, image }, index) => (
              <Reveal
                className="home-trainer-card"
                delay={index * 0.07}
                reducedMotion={reducedMotion}
                key={name}
              >
                <div className="home-trainer-image">
                  <ImageWithFallback src={image} alt={`Portrait of ${name}`} />
                  <span>{experience}</span>
                </div>
                <div className="home-trainer-info">
                  <div>
                    <h3>{name}</h3>
                    <p>{role}</p>
                  </div>
                  <FiArrowUpRight aria-hidden="true" />
                </div>
                <p className="home-trainer-specialty">
                  <span>FOCUS</span> {specialty}
                </p>
              </Reveal>
            ))}
          </div>
          <div className="home-section-action">
            <Link className="home-text-link" to="/trainers">
              VIEW ALL TRAINERS <FiArrowUpRight aria-hidden="true" />
            </Link>
          </div>
        </div>
      </section>

      <section className="home-section home-results" id="gallery">
        <div className="home-container">
          <Reveal reducedMotion={reducedMotion}>
            <SectionHeading
              eyebrow="PROGRESS LOOKS DIFFERENT ON EVERYONE"
              title="REAL PEOPLE. REAL RESULTS."
              description={`A little consistency can change a lot. These sample stories show the spirit of ${gymInfo.name}.`}
            />
          </Reveal>
          <div className="home-results-grid">
            {testimonials.map(({ name, result, quote, image, stat }, index) => (
              <Reveal
                className="home-result-card"
                delay={index * 0.07}
                reducedMotion={reducedMotion}
                key={name}
              >
                <div className="home-result-image">
                  <ImageWithFallback src={image} alt="" />
                  <span>{stat}</span>
                </div>
                <div className="home-result-copy">
                  <p className="home-eyebrow">MEMBER STORY</p>
                  <h3>{result}</h3>
                  <blockquote>“{quote}”</blockquote>
                  <p className="home-result-name">— {name}</p>
                </div>
              </Reveal>
            ))}
          </div>
          <p className="home-demo-note">Sample testimonials for preview. Replace with verified member stories.</p>
        </div>
      </section>

      <section className="home-cta" aria-labelledby="home-cta-title">
        <ImageWithFallback
          className="home-cta-image"
          src={siteImages.hero}
          alt=""
        />
        <div className="home-cta-shade" />
        <Reveal className="home-container home-cta-content" reducedMotion={reducedMotion}>
          <p className="home-eyebrow">YOUR NEXT REP IS A NEW BEGINNING</p>
          <h2 id="home-cta-title">READY TO BUILD A STRONGER YOU?</h2>
          <p>Start where you are. We will help you take it from here.</p>
          <a className="home-button home-button--red" href="#contact">
            START YOUR JOURNEY <FiArrowUpRight aria-hidden="true" />
          </a>
        </Reveal>
      </section>

      <section className="home-section home-contact" id="contact">
        <div className="home-container home-contact-layout">
          <Reveal className="home-contact-copy" reducedMotion={reducedMotion}>
            <p className="home-eyebrow">YOUR LOCAL TRAINING CLUB</p>
            <h2>MAKE YOUR NEXT MOVE.</h2>
            <p className="home-contact-intro">
              Drop by, give us a call, or send a message. We would love to show you around.
            </p>
            <div className="home-contact-details">
              <div>
                <FiMapPin aria-hidden="true" />
                <p>
                  <strong>Location</strong>
                  <span>{gymInfo.shortAddress}</span>
                </p>
              </div>
              <div>
                <FiPhone aria-hidden="true" />
                <p>
                  <strong>Call us</strong>
                  <a href={`tel:${gymInfo.phone}`}>{gymInfo.phoneDisplay}</a>
                </p>
              </div>
              <div>
                <FiClock aria-hidden="true" />
                <p>
                  <strong>Opening hours</strong>
                  <span>{gymInfo.hours[0].days} · {gymInfo.hours[0].time}</span>
                </p>
              </div>
            </div>
            <div className="home-contact-actions">
              <a
                className="home-button home-button--red"
                href={gymInfo.mapsUrl}
                target="_blank"
                rel="noreferrer"
              >
                GET DIRECTIONS <FiArrowUpRight aria-hidden="true" />
              </a>
              <a
                className="home-button home-button--outline"
                href={`https://wa.me/${gymInfo.whatsapp}`}
                target="_blank"
                rel="noreferrer"
              >
                <FiMessageCircle aria-hidden="true" /> CHAT ON WHATSAPP
              </a>
            </div>
            <p className="home-demo-note">Sample contact details — update before publishing.</p>
          </Reveal>
          <Reveal className="home-contact-visual" delay={0.12} reducedMotion={reducedMotion}>
            <ImageWithFallback
              src={siteImages.hero}
              alt={`Interior view of ${gymInfo.name}`}
            />
            <div className="home-contact-visual-overlay">
              <span className="home-contact-pin">
                <FiMapPin aria-hidden="true" />
              </span>
              <div>
                <strong>{gymInfo.name.toUpperCase()}</strong>
                <span>{gymInfo.shortAddress}</span>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <div className="home-bottom-line">
        <div className="home-container">
          <span>{gymInfo.name.toUpperCase()}</span>
          <span>TRAIN WITH PURPOSE. EVERY DAY.</span>
        </div>
      </div>
    </main>
  )
}

export default HomePage
