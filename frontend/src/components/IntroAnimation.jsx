import { lazy, Suspense, useEffect, useState } from 'react'
import { gymInfo, siteImages } from '../data/gymData'
import LightRays from './LightRays'
import './IntroAnimation.css'

const loadStrokeText = () => import('./StrokeText')
const StrokeText = lazy(loadStrokeText)

const INTRO_TIMING = {
  rays: 1200,
  athlete: 3400,
  exit: 9200,
  complete: 12600,
}

function IntroAnimation({ onComplete, onExitStart }) {
  const [phase, setPhase] = useState('dark')
  const [brandFontSize, setBrandFontSize] = useState(104)

  useEffect(() => {
    function updateBrandFontSize() {
      const width = window.innerWidth
      setBrandFontSize(width <= 480 ? 54 : width <= 800 ? 76 : 104)
    }

    updateBrandFontSize()
    window.addEventListener('resize', updateBrandFontSize)
    return () => window.removeEventListener('resize', updateBrandFontSize)
  }, [])

  useEffect(() => {
    loadStrokeText().catch((error) => {
      console.error('Failed to preload the intro brand text.', error)
    })
  }, [])

  useEffect(() => {
    const root = document.documentElement
    const previousOverflow = root.style.overflow
    const previousBodyOverflow = document.body.style.overflow
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const timers = []

    root.classList.add('intro-active')
    root.style.overflow = 'hidden'
    document.body.style.overflow = 'hidden'

    function schedule(callback, delay) {
      timers.push(window.setTimeout(callback, delay))
    }

    if (reducedMotion) {
      schedule(() => setPhase('athlete'), 0)
      schedule(() => setPhase('brand'), 300)
      schedule(() => {
        setPhase('exit')
        onExitStart()
      }, 2200)
      schedule(onComplete, 2800)
    } else {
      schedule(() => setPhase('rays'), INTRO_TIMING.rays)
      schedule(() => setPhase('athlete'), INTRO_TIMING.athlete)
      schedule(() => setPhase('brand'), 5500)
      schedule(() => {
        setPhase('exit')
        onExitStart()
      }, INTRO_TIMING.exit)
      schedule(onComplete, INTRO_TIMING.complete)
    }

    return () => {
      timers.forEach(window.clearTimeout)
      root.classList.remove('intro-active')
      root.style.overflow = previousOverflow
      document.body.style.overflow = previousBodyOverflow
    }
  }, [onComplete, onExitStart])

  const isExiting = phase === 'exit'

  return (
    <div
      className={`intro-overlay intro-overlay--${phase}${isExiting ? ' is-exiting' : ''}`}
      aria-hidden="true"
    >
      <div className="intro-atmosphere" />
      <LightRays
        raysOrigin="top-center"
        raysColor="#ffffff"
        raysSpeed={0.7}
        lightSpread={0.5}
        rayLength={3}
        glow={0.6}
        haze={0.25}
        followMouse
        mouseInfluence={0.1}
        rayDensity={1}
        tilt={0}
        raySharpness={0.35}
        atmosphere={1}
        intensity={0.8}
        fadeDistance={1}
        saturation={0.35}
        noiseAmount={0}
        distortion={0}
        pulsating={false}
        cursorShadow
        clickPulse
        intro
        lightMode={false}
      />
      <div className="intro-center">
        <img
          className={`intro-athlete${phase === 'athlete' || phase === 'brand' ? ' is-visible' : ''}`}
          src={siteImages.bodybuilder}
          alt=""
          draggable="false"
        />
      </div>
      {(phase === 'brand' || isExiting) && (
        <div className="intro-brand">
          <Suspense fallback={null}>
            <StrokeText
              text={gymInfo.name.toUpperCase()}
              strokeColor="#FF2A2A"
              fillColor="#FFFFFF"
              strokeStyle="solid"
              strokeWidth={1.4}
              drawDuration={1.6}
              fillDelay={0.2}
              stagger={0.05}
              ease="power2.out"
              trigger="mount"
              fillMode="wipe"
              wipeFrom="left"
              fontSize={brandFontSize}
              fontWeight={800}
              letterSpacing={-4}
              marching={false}
              hoverRedraw={false}
              shadow
              fontFamily="inherit"
              reverse={false}
            />
          </Suspense>
        </div>
      )}
    </div>
  )
}

export default IntroAnimation
