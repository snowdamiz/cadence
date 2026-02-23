import { Nav } from './components/Nav'
import { Hero } from './components/Hero'
import { Problem } from './components/Problem'
import { Architecture } from './components/Architecture'
import { Workflow } from './components/Workflow'
import { Ecosystem } from './components/Ecosystem'
import { GetStarted } from './components/GetStarted'
import { Footer } from './components/Footer'

export default function App() {
  return (
    <div className="min-h-screen bg-bg-base text-white font-sans">
      <Nav />
      <main>
        <Hero />
        <Problem />
        <Architecture />
        <Workflow />
        <Ecosystem />
        <GetStarted />
      </main>
      <Footer />
    </div>
  )
}
