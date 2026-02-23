import { Nav } from './components/Nav'
import { Hero } from './components/Hero'
import { Problem } from './components/Problem'
import { Architecture } from './components/Architecture'
import { Workflow } from './components/Workflow'
import { Ecosystem } from './components/Ecosystem'
import { GetStarted } from './components/GetStarted'
import { Footer } from './components/Footer'

function Divider() {
  return <div className="section-divider" />
}

export default function App() {
  return (
    <div className="min-h-screen bg-bg-base text-white font-sans">
      <Nav />
      <main>
        <Hero />
        <Divider />
        <Problem />
        <Divider />
        <Architecture />
        <Divider />
        <Workflow />
        <Divider />
        <Ecosystem />
        <Divider />
        <GetStarted />
      </main>
      <Footer />
    </div>
  )
}
