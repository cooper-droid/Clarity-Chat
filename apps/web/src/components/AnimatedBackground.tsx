'use client'

import { useEffect, useRef } from 'react'
import { useTheme } from '@/contexts/ThemeContext'

interface AnimatedBackgroundProps {
  isActive: boolean
  targetElement?: HTMLElement | null
}

interface Star {
  x: number
  y: number
  originalX: number
  originalY: number
  vx: number
  vy: number
  size: number
  opacity: number
  twinkleSpeed: number
  twinklePhase: number
  depth: number // 0-1, where 1 is closest
  lastAttractionTime: number
  hasAmbientMovement: boolean
  ambientVx: number
  ambientVy: number
}

interface Planet {
  x: number
  y: number
  size: number
  color: string
  name: string
}

interface ShootingStar {
  x: number
  y: number
  length: number
  speed: number
  angle: number
  opacity: number
  life: number
  originalStarIndex: number
  replacementDelay: number
}

interface Supernova {
  x: number
  y: number
  radius: number
  maxRadius: number
  opacity: number
  expanding: boolean
}

export default function AnimatedBackground({ isActive, targetElement }: AnimatedBackgroundProps) {
  const { theme } = useTheme()
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mouseRef = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // Track mouse position
    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY }
    }
    window.addEventListener('mousemove', handleMouseMove)

    // Create planets (solar system) - star-sized
    const planets: Planet[] = [
      { x: canvas.width * 0.9, y: canvas.height * 0.1, size: 2.5, color: '#FDB813', name: 'Sun' },
      { x: canvas.width * 0.15, y: canvas.height * 0.3, size: 1.5, color: '#8C7853', name: 'Mercury' },
      { x: canvas.width * 0.25, y: canvas.height * 0.7, size: 2, color: '#FFC649', name: 'Venus' },
      { x: canvas.width * 0.4, y: canvas.height * 0.2, size: 2, color: '#4169E1', name: 'Earth' },
      { x: canvas.width * 0.6, y: canvas.height * 0.8, size: 1.8, color: '#CD5C5C', name: 'Mars' },
      { x: canvas.width * 0.75, y: canvas.height * 0.4, size: 2.5, color: '#DAA520', name: 'Jupiter' },
      { x: canvas.width * 0.85, y: canvas.height * 0.6, size: 2.3, color: '#F4A460', name: 'Saturn' },
      { x: canvas.width * 0.1, y: canvas.height * 0.5, size: 2, color: '#4FD5D6', name: 'Uranus' },
      { x: canvas.width * 0.3, y: canvas.height * 0.15, size: 2, color: '#4166F5', name: 'Neptune' },
    ]

    // Create stars with variable sizes and depths - multiple layers
    const stars: Star[] = []
    const starCount = 1200 // Much denser starfield
    for (let i = 0; i < starCount; i++) {
      // Cubic distribution - more far stars than close stars for realistic depth
      const depthRandom = Math.random()
      const depth = Math.pow(depthRandom, 1.5) // Bias toward smaller values (distant stars)

      // Brightness strongly tied to depth - far stars much dimmer
      const baseOpacity = 0.15 + (depth * 0.85) // Range: 0.15 (very far) to 1.0 (very close)

      const startX = Math.random() * canvas.width
      const startY = Math.random() * canvas.height

      // Give some stars ambient movement
      const hasAmbientMovement = Math.random() < 0.3 // 30% of stars drift
      const ambientSpeed = 0.3 // Drift speed
      const ambientAngle = Math.random() * Math.PI * 2
      const ambientVx = hasAmbientMovement ? Math.cos(ambientAngle) * ambientSpeed : 0
      const ambientVy = hasAmbientMovement ? Math.sin(ambientAngle) * ambientSpeed : 0

      stars.push({
        x: startX,
        y: startY,
        originalX: startX,
        originalY: startY,
        vx: ambientVx,
        vy: ambientVy,
        size: (Math.random() * 1.0 + 0.2) * (0.3 + depth * 0.7), // Far stars much smaller
        opacity: baseOpacity,
        twinkleSpeed: Math.random() * 0.02 + 0.005,
        twinklePhase: Math.random() * Math.PI * 2,
        depth: depth,
        lastAttractionTime: 0,
        hasAmbientMovement: hasAmbientMovement,
        ambientVx: ambientVx,
        ambientVy: ambientVy,
      })
    }

    // Shooting stars array
    const shootingStars: ShootingStar[] = []
    const hiddenStars = new Set<number>() // Track which stars are currently shooting stars

    // Create a shooting star occasionally - travels across entire screen
    const createShootingStar = () => {
      if (Math.random() < 0.0008) {
        // Random angle for shooting star (any direction)
        const angle = Math.random() * Math.PI * 2

        // Start from edge based on angle
        let startX, startY
        const margin = 100

        if (angle < Math.PI / 4 || angle > (7 * Math.PI) / 4) {
          // Coming from right
          startX = canvas.width + margin
          startY = Math.random() * canvas.height
        } else if (angle < (3 * Math.PI) / 4) {
          // Coming from bottom
          startX = Math.random() * canvas.width
          startY = canvas.height + margin
        } else if (angle < (5 * Math.PI) / 4) {
          // Coming from left
          startX = -margin
          startY = Math.random() * canvas.height
        } else {
          // Coming from top
          startX = Math.random() * canvas.width
          startY = -margin
        }

        shootingStars.push({
          x: startX,
          y: startY,
          length: Math.random() * 100 + 60,
          speed: Math.random() * 4 + 4, // Faster
          angle: angle,
          opacity: 1,
          life: 1,
          originalStarIndex: -1, // Not replacing any star
          replacementDelay: 0,
        })
      }
    }

    let animationId: number
    let currentTime = 0
    const animate = () => {
      currentTime += 1 / 60 // Assuming 60fps

      // Create trailing effect by not fully clearing the canvas - black hole trail fade
      ctx.fillStyle = theme === 'dark' ? 'rgba(0, 0, 0, 0.15)' : 'rgba(255, 255, 255, 0.15)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Draw planets
      planets.forEach((planet) => {
        ctx.beginPath()
        ctx.arc(planet.x, planet.y, planet.size, 0, Math.PI * 2)

        // Add glow for sun
        if (planet.name === 'Sun') {
          const gradient = ctx.createRadialGradient(planet.x, planet.y, 0, planet.x, planet.y, planet.size * 1.5)
          gradient.addColorStop(0, planet.color)
          gradient.addColorStop(0.5, planet.color + '88')
          gradient.addColorStop(1, planet.color + '00')
          ctx.fillStyle = gradient
          ctx.arc(planet.x, planet.y, planet.size * 1.5, 0, Math.PI * 2)
          ctx.fill()
          ctx.beginPath()
          ctx.arc(planet.x, planet.y, planet.size, 0, Math.PI * 2)
        }

        ctx.fillStyle = planet.color
        ctx.fill()
      })

      // Draw and update stars with twinkling and mouse interaction
      stars.forEach((star, index) => {
        // Skip stars that are currently shooting stars
        if (hiddenStars.has(index)) return

        star.twinklePhase += star.twinkleSpeed
        const twinkle = Math.sin(star.twinklePhase) * 0.3 + 0.7

        // Black hole attraction to mouse - smaller range
        const dx = mouseRef.current.x - star.x
        const dy = mouseRef.current.y - star.y
        const distance = Math.sqrt(dx * dx + dy * dy)

        if (distance < 120 && distance > 0) {
          // Gravitational pull based on depth - closer stars respond more
          const force = (120 - distance) / 120
          const depthMultiplier = star.depth * 0.8 + 0.2 // Far stars move less
          const acceleration = force * force * 0.15 * depthMultiplier

          star.vx += (dx / distance) * acceleration
          star.vy += (dy / distance) * acceleration
          star.lastAttractionTime = currentTime
        }

        // Return to original position after 3 seconds of no attraction (only for non-drifting stars)
        if (currentTime - star.lastAttractionTime > 3) {
          if (star.hasAmbientMovement) {
            // For drifting stars, restore their ambient velocity
            star.vx += (star.ambientVx - star.vx) * 0.02
            star.vy += (star.ambientVy - star.vy) * 0.02
          } else {
            // For stationary stars, return to original position
            const backDx = star.originalX - star.x
            const backDy = star.originalY - star.y
            const backDistance = Math.sqrt(backDx * backDx + backDy * backDy)

            if (backDistance > 1) {
              star.vx += (backDx / backDistance) * 0.01
              star.vy += (backDy / backDistance) * 0.01
            }
          }
        }

        // Apply friction to gradually slow down (but preserve ambient movement)
        if (!star.hasAmbientMovement || currentTime - star.lastAttractionTime < 3) {
          star.vx *= 0.92
          star.vy *= 0.92
        }

        // Update position based on velocity
        star.x += star.vx
        star.y += star.vy

        // Wrap around edges
        if (star.x < 0) star.x = canvas.width
        if (star.x > canvas.width) star.x = 0
        if (star.y < 0) star.y = canvas.height
        if (star.y > canvas.height) star.y = 0

        ctx.beginPath()
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2)
        ctx.fillStyle = theme === 'dark'
          ? `rgba(255, 255, 255, ${star.opacity * twinkle})`
          : `rgba(0, 0, 0, ${star.opacity * twinkle})`
        ctx.fill()
      })

      // Create new shooting stars
      createShootingStar()

      // Draw and update shooting stars
      for (let i = shootingStars.length - 1; i >= 0; i--) {
        const shootingStar = shootingStars[i]

        // Update position
        shootingStar.x += Math.cos(shootingStar.angle) * shootingStar.speed
        shootingStar.y += Math.sin(shootingStar.angle) * shootingStar.speed
        shootingStar.life -= 0.01
        shootingStar.opacity = shootingStar.life
        shootingStar.replacementDelay -= 1 / 60 // Decrease delay (assuming 60fps)

        // Replace the original star after delay
        if (shootingStar.replacementDelay <= 0 && hiddenStars.has(shootingStar.originalStarIndex)) {
          hiddenStars.delete(shootingStar.originalStarIndex)
        }

        if (shootingStar.life <= 0) {
          shootingStars.splice(i, 1)
          continue
        }

        // Draw shooting star trail
        const gradient = ctx.createLinearGradient(
          shootingStar.x,
          shootingStar.y,
          shootingStar.x - Math.cos(shootingStar.angle) * shootingStar.length,
          shootingStar.y - Math.sin(shootingStar.angle) * shootingStar.length
        )
        const starColor = theme === 'dark' ? '255, 255, 255' : '0, 0, 0'
        gradient.addColorStop(0, `rgba(${starColor}, ${shootingStar.opacity})`)
        gradient.addColorStop(1, `rgba(${starColor}, 0)`)

        ctx.beginPath()
        ctx.strokeStyle = gradient
        ctx.lineWidth = 1.5
        ctx.moveTo(shootingStar.x, shootingStar.y)
        ctx.lineTo(
          shootingStar.x - Math.cos(shootingStar.angle) * shootingStar.length,
          shootingStar.y - Math.sin(shootingStar.angle) * shootingStar.length
        )
        ctx.stroke()
      }

      animationId = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      window.removeEventListener('mousemove', handleMouseMove)
      cancelAnimationFrame(animationId)
    }
  }, [isActive, targetElement, theme])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0"
      style={{ background: 'transparent' }}
    />
  )
}
