import { Nav } from './components/Nav'
import { Hero } from './components/Hero'
import { Concept } from './components/Concept'
import { Features } from './components/Features'
import { HowItWorks } from './components/HowItWorks'
import { Tools } from './components/Tools'
import { Install } from './components/Install'
import { Footer } from './components/Footer'

export default function App() {
  return (
    <div className="min-h-screen bg-bg-base text-white font-sans">
      <Nav />
      <main>
        <Hero />
        <Concept />
        <Features />
        <HowItWorks />
        <Tools />
        <Install />
      </main>
      <Footer />
    </div>
  )
}
