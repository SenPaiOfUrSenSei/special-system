import React, { useEffect, useRef } from 'react'
import * as THREE from 'three'

export default function ThreeBackground() {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    let width = window.innerWidth
    let height = window.innerHeight

    // 1. Scene Setup
    const scene = new THREE.Scene()

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 100)
    camera.position.z = 30

    // 3. Renderer Setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // 4. Create Round Glowing Dot Texture
    const createCircleTexture = () => {
      const canvas = document.createElement('canvas')
      canvas.width = 32
      canvas.height = 32
      const ctx = canvas.getContext('2d')
      const gradient = ctx.createRadialGradient(16, 16, 0, 16, 16, 16)
      gradient.addColorStop(0, 'rgba(255, 255, 255, 1)')
      gradient.addColorStop(0.3, 'rgba(255, 255, 255, 0.4)')
      gradient.addColorStop(1, 'rgba(255, 255, 255, 0)')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, 32, 32)
      return new THREE.CanvasTexture(canvas)
    }

    const dotTexture = createCircleTexture()

    // 5. Particles Setup (Constellation Cloud)
    const particleCount = 120
    const geometry = new THREE.BufferGeometry()
    const positions = new Float32Array(particleCount * 3)
    const colors = new Float32Array(particleCount * 3)

    for (let i = 0; i < particleCount * 3; i += 3) {
      // Sphere distribution
      const u = Math.random()
      const v = Math.random()
      const theta = u * 2.0 * Math.PI
      const phi = Math.acos(2.0 * v - 1.0)
      const r = 12 + Math.random() * 8 // radius layer

      positions[i] = r * Math.sin(phi) * Math.cos(theta)
      positions[i + 1] = r * Math.sin(phi) * Math.sin(theta)
      positions[i + 2] = r * Math.cos(phi)

      // Random opacity-shading by color brightness
      const colorVal = 0.5 + Math.random() * 0.5
      colors[i] = colorVal
      colors[i + 1] = colorVal
      colors[i + 2] = colorVal
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

    const material = new THREE.PointsMaterial({
      size: 0.7,
      map: dotTexture,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      vertexColors: true
    })

    const particleSystem = new THREE.Points(geometry, material)
    scene.add(particleSystem)

    // 6. Central Holographic Grid Sphere
    const sphereGeometry = new THREE.SphereGeometry(6, 12, 12)
    const sphereMaterial = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      wireframe: true,
      transparent: true,
      opacity: 0.035,
      blending: THREE.AdditiveBlending
    })
    const wireSphere = new THREE.Mesh(sphereGeometry, sphereMaterial)
    scene.add(wireSphere)

    // 7. Interactive Mouse Tracking
    let mouseX = 0
    let mouseY = 0
    let targetX = 0
    let targetY = 0

    const handleMouseMove = (event) => {
      mouseX = (event.clientX - width / 2) / 150
      mouseY = (event.clientY - height / 2) / 150
    }

    window.addEventListener('mousemove', handleMouseMove)

    // 8. Handle Window Resize
    const handleResize = () => {
      width = window.innerWidth
      height = window.innerHeight

      camera.aspect = width / height
      camera.updateProjectionMatrix()

      renderer.setSize(width, height)
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    }

    window.addEventListener('resize', handleResize)

    // 9. Animation Loop
    let animationId = null
    const clock = new THREE.Clock()

    const animate = () => {
      animationId = requestAnimationFrame(animate)

      const elapsedTime = clock.getElapsedTime()

      // Smooth mouse follow (easing)
      targetX += (mouseX - targetX) * 0.05
      targetY += (mouseY - targetY) * 0.05

      // Rotations
      particleSystem.rotation.y = elapsedTime * 0.02 + targetX
      particleSystem.rotation.x = elapsedTime * 0.01 + targetY
      
      wireSphere.rotation.y = -elapsedTime * 0.04
      wireSphere.rotation.z = elapsedTime * 0.015

      renderer.render(scene, camera)
    }

    animate()

    // 10. Memory Clean Up
    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('resize', handleResize)
      
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
      
      // Dispose resources
      geometry.dispose()
      material.dispose()
      sphereGeometry.dispose()
      sphereMaterial.dispose()
      dotTexture.dispose()
      renderer.dispose()
    }
  }, [])

  return (
    <div
      ref={containerRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: -1,
        pointerEvents: 'none',
        background: 'transparent'
      }}
    />
  )
}
