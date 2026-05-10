import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import Results from './pages/Results';
import DoctorFinder from './pages/DoctorFinder';
import Info from './pages/Info';
import { Activity } from 'lucide-react';

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-navy-900 text-white font-sans">
        {/* Navigation Bar */}
        <nav className="sticky top-0 z-50 glass-panel border-b border-white/10 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <Link to="/" className="flex items-center gap-2 text-emerald-400 font-bold text-xl tracking-tight">
              <Activity className="w-6 h-6" />
              LungScan AI
            </Link>
            <div className="flex items-center gap-6 text-sm font-medium">
              <Link to="/" className="text-gray-300 hover:text-white transition-colors">Home</Link>
              <Link to="/doctor-finder" className="text-gray-300 hover:text-white transition-colors">Doctor Finder</Link>
              <Link to="/info" className="text-gray-300 hover:text-white transition-colors">Info & Disclaimer</Link>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/results" element={<Results />} />
            <Route path="/doctor-finder" element={<DoctorFinder />} />
            <Route path="/info" element={<Info />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t border-white/10 py-8 text-center text-sm text-gray-500">
          <p>© {new Date().getFullYear()} LungScan AI. Untuk keperluan skrining awal, BUKAN diagnosis medis resmi.</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
