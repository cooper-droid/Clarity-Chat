'use client'

import { useEffect, useRef } from 'react'
import { useTheme } from '@/contexts/ThemeContext'
import * as THREE from 'three'
import { gsap } from 'gsap'

export default function DataScienceBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { theme } = useTheme()

  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    let width = canvas.offsetWidth
    let height = canvas.offsetHeight

    // Color scheme based on theme
    const colors = theme === 'dark'
      ? [
          new THREE.Color(0xac1122),
          new THREE.Color(0x96789f),
          new THREE.Color(0x535353)
        ]
      : [
          new THREE.Color(0x2563eb), // blue
          new THREE.Color(0x7c3aed), // purple
          new THREE.Color(0x059669)  // green
        ]

    const renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      antialias: true,
      alpha: true
    })
    renderer.setPixelRatio(window.devicePixelRatio > 1 ? 2 : 1)
    renderer.setSize(width, height)
    renderer.setClearColor(0x000000, 0)

    const scene = new THREE.Scene()

    const raycaster = new THREE.Raycaster()
    raycaster.params.Points!.threshold = 6

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 2000)
    camera.position.set(0, 0, 350)

    const galaxy = new THREE.Group()
    scene.add(galaxy)

    // Create dots
    const loader = new THREE.TextureLoader()
    const dotTexture = loader.load('/dotTexture.png')
    const dotsAmount = 3000
    const dotsGeometry: any = new THREE.BufferGeometry()
    const positions = new Float32Array(dotsAmount * 3)
    const sizes = new Float32Array(dotsAmount)
    const colorsAttribute = new Float32Array(dotsAmount * 3)

    const vertices: any[] = []

    for (let i = 0; i < dotsAmount; i++) {
      const vector: any = new THREE.Vector3()

      vector.color = Math.floor(Math.random() * colors.length)
      vector.theta = Math.random() * Math.PI * 2
      vector.phi = (1 - Math.sqrt(Math.random())) * Math.PI / 2 * (Math.random() > 0.5 ? 1 : -1)

      vector.x = Math.cos(vector.theta) * Math.cos(vector.phi)
      vector.y = Math.sin(vector.phi)
      vector.z = Math.sin(vector.theta) * Math.cos(vector.phi)
      vector.multiplyScalar(120 + (Math.random() - 0.5) * 5)
      vector.scaleX = 5

      if (Math.random() > 0.5) {
        moveDot(vector, i)
      }

      vertices.push(vector)
      vector.toArray(positions, i * 3)
      colors[vector.color].toArray(colorsAttribute, i * 3)
      sizes[i] = 5
    }

    function moveDot(vector: any, index: number) {
      const tempVector = vector.clone()
      tempVector.multiplyScalar((Math.random() - 0.5) * 0.2 + 1)
      gsap.to(vector, {
        x: tempVector.x,
        y: tempVector.y,
        z: tempVector.z,
        duration: Math.random() * 3 + 3,
        yoyo: true,
        repeat: -1,
        delay: -Math.random() * 3,
        ease: 'none',
        onUpdate: function () {
          attributePositions.array[index * 3] = vector.x
          attributePositions.array[index * 3 + 1] = vector.y
          attributePositions.array[index * 3 + 2] = vector.z
        }
      })
    }

    const attributePositions = new THREE.BufferAttribute(positions, 3)
    dotsGeometry.setAttribute('position', attributePositions)
    const attributeSizes = new THREE.BufferAttribute(sizes, 1)
    dotsGeometry.setAttribute('size', attributeSizes)
    const attributeColors = new THREE.BufferAttribute(colorsAttribute, 3)
    dotsGeometry.setAttribute('color', attributeColors)

    const shaderMaterial = new THREE.ShaderMaterial({
      uniforms: {
        texture: {
          value: dotTexture
        }
      },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        void main() {
          vColor = color;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = size * (350.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        uniform sampler2D texture;
        void main() {
          vec4 textureColor = texture2D(texture, gl_PointCoord);
          if (textureColor.a < 0.3) discard;
          vec4 color = vec4(vColor.xyz, 1.0) * textureColor;
          gl_FragColor = color;
        }
      `,
      transparent: true
    })
    const wrap = new THREE.Points(dotsGeometry, shaderMaterial)
    scene.add(wrap)

    // Create white segments
    const segmentsGeom = new THREE.BufferGeometry()
    const segmentPositions: number[] = []
    const segmentColors: number[] = []

    for (let i = vertices.length - 1; i >= 0; i--) {
      const vector = vertices[i]
      for (let j = vertices.length - 1; j >= 0; j--) {
        if (i !== j && vector.distanceTo(vertices[j]) < 12) {
          segmentPositions.push(vector.x, vector.y, vector.z)
          segmentPositions.push(vertices[j].x, vertices[j].y, vertices[j].z)
          const color = colors[vector.color]
          segmentColors.push(color.r, color.g, color.b)
          segmentColors.push(color.r, color.g, color.b)
        }
      }
    }

    segmentsGeom.setAttribute('position', new THREE.Float32BufferAttribute(segmentPositions, 3))
    segmentsGeom.setAttribute('color', new THREE.Float32BufferAttribute(segmentColors, 3))

    const segmentsMat = new THREE.LineBasicMaterial({
      transparent: true,
      opacity: 0.3,
      vertexColors: true
    })
    const segments = new THREE.LineSegments(segmentsGeom, segmentsMat)
    galaxy.add(segments)

    let hovered: number[] = []
    let prevHovered: number[] = []

    function render() {
      raycaster.setFromCamera(mouse, camera)
      const intersections = raycaster.intersectObjects([wrap])
      hovered = []

      if (intersections.length) {
        for (let i = 0; i < intersections.length; i++) {
          const index = intersections[i].index!
          hovered.push(index)
          if (prevHovered.indexOf(index) === -1) {
            onDotHover(index)
          }
        }
      }

      for (let i = 0; i < prevHovered.length; i++) {
        if (hovered.indexOf(prevHovered[i]) === -1) {
          mouseOut(prevHovered[i])
        }
      }

      prevHovered = hovered.slice(0)
      attributeSizes.needsUpdate = true
      attributePositions.needsUpdate = true

      // Update segment positions
      for (let i = 0; i < vertices.length; i++) {
        const pos = segmentsGeom.attributes.position as THREE.BufferAttribute
        let segmentIndex = 0
        for (let j = 0; j < vertices.length; j++) {
          if (i !== j && vertices[i].distanceTo(vertices[j]) < 12) {
            pos.array[segmentIndex * 3] = vertices[i].x
            pos.array[segmentIndex * 3 + 1] = vertices[i].y
            pos.array[segmentIndex * 3 + 2] = vertices[i].z
            segmentIndex++
            pos.array[segmentIndex * 3] = vertices[j].x
            pos.array[segmentIndex * 3 + 1] = vertices[j].y
            pos.array[segmentIndex * 3 + 2] = vertices[j].z
            segmentIndex++
          }
        }
      }
      segmentsGeom.attributes.position.needsUpdate = true

      renderer.render(scene, camera)
    }

    function onDotHover(index: number) {
      if (!vertices[index].tl) {
        vertices[index].tl = gsap.timeline()
      }
      vertices[index].tl.clear()
      vertices[index].tl.to(vertices[index], {
        scaleX: 10,
        duration: 1,
        ease: 'elastic.out(2, 0.2)',
        onUpdate: function () {
          attributeSizes.array[index] = vertices[index].scaleX
        }
      })
    }

    function mouseOut(index: number) {
      if (vertices[index].tl) {
        vertices[index].tl.to(vertices[index], {
          scaleX: 5,
          duration: 0.4,
          ease: 'power2.out',
          onUpdate: function () {
            attributeSizes.array[index] = vertices[index].scaleX
          }
        })
      }
    }

    function onResize() {
      canvas.style.width = ''
      canvas.style.height = ''
      width = canvas.offsetWidth
      height = canvas.offsetHeight
      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(width, height)
    }

    const mouse = new THREE.Vector2(-100, -100)
    function onMouseMove(e: MouseEvent) {
      const canvasBounding = canvas.getBoundingClientRect()
      mouse.x = ((e.clientX - canvasBounding.left) / width) * 2 - 1
      mouse.y = -((e.clientY - canvasBounding.top) / height) * 2 + 1
    }

    gsap.ticker.add(render)
    window.addEventListener('mousemove', onMouseMove)

    let resizeTm: NodeJS.Timeout
    const handleResize = () => {
      clearTimeout(resizeTm)
      resizeTm = setTimeout(onResize, 200)
    }
    window.addEventListener('resize', handleResize)

    return () => {
      gsap.ticker.remove(render)
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('resize', handleResize)
      renderer.dispose()
      dotsGeometry.dispose()
      shaderMaterial.dispose()
      segmentsGeom.dispose()
      segmentsMat.dispose()
    }
  }, [theme])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 z-0"
      style={{ width: '100%', height: '100vh' }}
    />
  )
}
