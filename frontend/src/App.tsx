import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Home from './pages/Home';
import Results from './pages/Results';
import DoctorFinder from './pages/DoctorFinder';
import Info from './pages/Info';
import Dataset from './pages/Dataset';
import { Activity, Sun, Moon } from 'lucide-react';
import { useState, useEffect } from 'react';

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname === to;
  return (
    <Link
      to={to}
      className={`transition-colors text-sm font-medium ${
        isActive
          ? 'text-emerald-500 dark:text-emerald-400'
          : 'text-slate-600 hover:text-slate-900 dark:text-gray-300 dark:hover:text-white'
      }`}
    >
      {children}
    </Link>
  );
}

function AppInner() {
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('lungscan-theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('lungscan-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('lungscan-theme', 'light');
    }
  }, [isDark]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 dark:bg-navy-900 dark:text-white font-sans transition-colors duration-200">
      {/* Navigation Bar */}
      <nav className="sticky top-0 z-50 glass-panel border-b border-slate-200 dark:border-white/10 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-emerald-500 dark:text-emerald-400 font-bold text-xl tracking-tight">
            <Activity className="w-6 h-6" />
            LungScan AI
          </Link>
          <div className="flex items-center gap-6 text-sm font-medium">
            <NavLink to="/">Beranda</NavLink>
            <NavLink to="/doctor-finder">Cari Dokter</NavLink>
            <NavLink to="/dataset">Dataset</NavLink>
            <NavLink to="/info">Info & Sanggahan</NavLink>
            <button
              onClick={() => setIsDark(!isDark)}
              className="p-2 rounded-full hover:bg-slate-200 dark:hover:bg-white/10 transition-colors ml-2"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-5 h-5 text-gray-300 hover:text-white" /> : <Moon className="w-5 h-5 text-slate-600 hover:text-slate-900" />}
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/results" element={<Results />} />
          <Route path="/doctor-finder" element={<DoctorFinder />} />
          <Route path="/dataset" element={<Dataset />} />
          <Route path="/info" element={<Info />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-white/10 py-8 text-center text-sm text-slate-500 dark:text-gray-500 transition-colors duration-200">
        <p>© {new Date().getFullYear()} LungScan AI. Untuk keperluan skrining awal, BUKAN diagnosis medis resmi.</p>
      </footer>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppInner />
    </Router>
  );
}

export default App;
