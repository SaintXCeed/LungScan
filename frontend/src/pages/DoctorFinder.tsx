import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Search, MapPin, Phone, Building, Navigation, ExternalLink } from 'lucide-react';
import clsx from 'clsx';
import { CinematicFooter } from '../components/ui/motion-footer';

import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

interface Doctor {
  id: number;
  name: string;
  specialty: string;
  facility: string;
  address: string;
  phone: string;
  type: string;
  lat: number;
  lng: number;
  city: string;
  province: string;
  gmaps_link: string;
}

// Child component that handles flyTo
function FlyToLocation({ target }: { target: [number, number] | null }) {
  const map = useMap();
  const prevTarget = useRef<string | null>(null);

  useEffect(() => {
    if (!target) return;
    const key = `${target[0]},${target[1]}`;
    if (key === prevTarget.current) return;
    prevTarget.current = key;
    map.flyTo(target, 14, { duration: 1.2 });
  }, [target, map]);

  return null;
}

export default function DoctorFinder() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [filtered, setFiltered] = useState<Doctor[]>([]);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [flyTarget, setFlyTarget] = useState<[number, number] | null>(null);

  const cardRefs = useRef<Record<number, HTMLDivElement | null>>({});

  useEffect(() => {
    fetch('http://localhost:8000/api/doctors')
      .then(r => r.json())
      .then((data: Doctor[]) => {
        setDoctors(data);
        setFiltered(data);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    let f = [...doctors];
    if (search) {
      const q = search.toLowerCase();
      f = f.filter(d =>
        d.name.toLowerCase().includes(q) ||
        d.city.toLowerCase().includes(q) ||
        d.facility.toLowerCase().includes(q)
      );
    }
    if (typeFilter !== 'All') f = f.filter(d => d.type === typeFilter);
    setFiltered(f);
  }, [search, typeFilter, doctors]);

  function selectDoctor(d: Doctor) {
    setSelectedId(d.id);
    setFlyTarget([d.lat, d.lng]);
    setTimeout(() => {
      cardRefs.current[d.id]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 50);
  }

  return (
    <div className="flex-1 w-full relative overflow-x-hidden bg-white dark:bg-[#0a0f1c] transition-colors duration-200">
      <main className="relative z-10 w-full bg-slate-50 dark:bg-navy-900 flex flex-col items-center rounded-b-[2.5rem] border-b border-slate-200 dark:border-white/5 shadow-2xl pb-12 transition-colors duration-200">
        <div className="w-full max-w-7xl mx-auto px-6 py-12 flex flex-col">
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">Temukan Dokter Spesialis</h1>
            <p className="text-slate-600 dark:text-gray-400">Peta sebaran dokter spesialis paru dan onkologi di Indonesia.</p>
          </div>

          {/* Search */}
          <div className="glass-panel p-4 rounded-2xl flex flex-col sm:flex-row gap-4 mb-8">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 dark:text-gray-400" />
              <input
                type="text"
                placeholder="Cari nama, kota, atau fasilitas..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full bg-slate-100 dark:bg-navy-900 border border-slate-300 dark:border-white/10 rounded-xl py-3 pl-12 pr-4 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <div className="flex gap-2">
              {['All', 'BPJS', 'Swasta'].map(t => (
                <button
                  key={t}
                  onClick={() => setTypeFilter(t)}
                  className={clsx(
                    'px-6 py-3 rounded-xl border text-sm font-medium transition-colors',
                    typeFilter === t
                      ? 'bg-emerald-500 border-emerald-500 text-white'
                      : 'bg-white dark:bg-surface border-slate-300 dark:border-white/10 text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white'
                  )}
                >{t === 'All' ? 'Semua' : t}</button>
              ))}
            </div>
          </div>

          {/* Layout Grid */}
          <div className="w-full grid grid-cols-1 lg:grid-cols-3 gap-8 h-[600px]">
            {/* List */}
            <div className="lg:col-span-1 glass-panel rounded-3xl overflow-hidden flex flex-col h-full">
              <div className="p-5 border-b border-slate-200 dark:border-white/10 bg-slate-100 dark:bg-surface/50">
                <h3 className="font-semibold">{filtered.length} Dokter Ditemukan</h3>
              </div>
              <div className="flex-1 overflow-y-auto p-3 space-y-3 custom-scrollbar">
                {filtered.length === 0 && (
                  <p className="p-6 text-center text-slate-500 dark:text-gray-500 text-sm">Tidak ada dokter ditemukan.</p>
                )}
                {filtered.map(d => {
                  const active = selectedId === d.id;
                  return (
                    <div
                      key={d.id}
                      ref={el => { cardRefs.current[d.id] = el; }}
                      onClick={() => selectDoctor(d)}
                      className={clsx(
                        'p-4 rounded-2xl border cursor-pointer transition-all duration-200',
                        active
                          ? 'bg-emerald-50 dark:bg-emerald-500/10 border-emerald-500 shadow-[0_0_16px_rgba(16,185,129,0.15)]'
                          : 'bg-white dark:bg-surface border-slate-200 dark:border-white/5 hover:border-emerald-500/40'
                      )}
                    >
                      <div className="flex justify-between items-start gap-2 mb-1">
                        <h4 className={clsx('font-bold text-sm leading-snug', active ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-900 dark:text-white')}>
                          {d.name}
                        </h4>
                        <span className={clsx(
                          'text-xs px-2 py-0.5 rounded border font-medium shrink-0',
                          d.type === 'BPJS'
                            ? 'bg-emerald-50 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/30'
                            : 'bg-amber-50 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-500/30'
                        )}>{d.type}</span>
                      </div>
                      <p className="text-emerald-500 text-xs font-medium mb-3">{d.specialty}</p>
                      <div className="space-y-1.5 text-xs text-slate-600 dark:text-gray-400">
                        <span className="flex items-start gap-1.5"><Building className="w-3.5 h-3.5 mt-0.5 shrink-0" />{d.facility}</span>
                        <span className="flex items-start gap-1.5"><MapPin className="w-3.5 h-3.5 mt-0.5 shrink-0" />{d.city}, {d.province}</span>
                        <span className="flex items-start gap-1.5"><Phone className="w-3.5 h-3.5 mt-0.5 shrink-0" />{d.phone}</span>
                      </div>
                      {active && (
                        <div className="mt-3 pt-3 border-t border-emerald-500/20 flex items-center justify-between">
                          <p className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                            <Navigation className="w-3 h-3" /> Lokasi di peta
                          </p>
                          <a
                            href={d.gmaps_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={e => e.stopPropagation()}
                            className="flex items-center gap-1 text-xs bg-slate-200 hover:bg-slate-300 dark:bg-white/10 dark:hover:bg-white/20 text-slate-900 dark:text-white px-3 py-1.5 rounded-lg transition-colors font-medium"
                          >
                            <ExternalLink className="w-3 h-3" />
                            Buka di Google Maps
                          </a>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Map */}
            <div className="lg:col-span-2 rounded-3xl overflow-hidden border border-slate-200 dark:border-white/10 h-full relative" style={{ zIndex: 0 }}>
              <MapContainer center={[-0.789275, 113.921327]} zoom={5} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <FlyToLocation target={flyTarget} />
                {filtered.map(d => (
                  <Marker
                    key={d.id}
                    position={[d.lat, d.lng]}
                    eventHandlers={{ click: () => selectDoctor(d) }}
                  >
                    <Popup>
                      <div style={{ fontFamily: 'sans-serif', minWidth: 160 }}>
                        <strong style={{ fontSize: 13 }}>{d.name}</strong>
                        <p style={{ color: '#059669', fontSize: 11, margin: '4px 0' }}>{d.specialty}</p>
                        <p style={{ fontSize: 12 }}>{d.facility}</p>
                        <p style={{ fontSize: 11, color: '#6b7280', marginBottom: 8 }}>{d.city}, {d.province}</p>
                        <a href={d.gmaps_link} target="_blank" rel="noopener noreferrer"
                          style={{ fontSize: 11, color: '#059669', fontWeight: 600 }}>
                          🗺 Buka di Google Maps →
                        </a>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </div>
        </div>
      </main>
      <CinematicFooter />
    </div>
  );
}
