import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Search, MapPin, Phone, Building, Navigation, ExternalLink, Map } from 'lucide-react';
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
  gmaps_embed: string;
}

// Fly-to controller — safely inside MapContainer context
function FlyToLocation({ lat, lng }: { lat: number | null; lng: number | null }) {
  const map = useMap();
  const prevKey = useRef('');
  useEffect(() => {
    if (lat === null || lng === null) return;
    const key = `${lat.toFixed(6)},${lng.toFixed(6)}`;
    if (key === prevKey.current) return;
    prevKey.current = key;
    map.flyTo([lat, lng], 14, { duration: 1.0 });
  }, [lat, lng, map]);
  return null;
}

export default function DoctorFinder() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [filtered, setFiltered] = useState<Doctor[]>([]);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [selected, setSelected] = useState<Doctor | null>(null);
  // 'leaflet' = overview all markers, 'gmaps' = Google Maps embed of selected
  const [mapMode, setMapMode] = useState<'leaflet' | 'gmaps'>('leaflet');
  const [flyCoords, setFlyCoords] = useState<{ lat: number | null; lng: number | null }>({ lat: null, lng: null });
  const cardRefs = useRef<Record<number, HTMLDivElement | null>>({});

  useEffect(() => {
    fetch('http://localhost:8000/api/doctors')
      .then(r => r.json())
      .then((data: Doctor[]) => { setDoctors(data); setFiltered(data); })
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
    setSelected(d);
    setFlyCoords({ lat: d.lat, lng: d.lng });
    // Auto-switch to Google Maps embed view when a doctor is selected
    setMapMode('gmaps');
    setTimeout(() => {
      cardRefs.current[d.id]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 50);
  }

  function backToOverview() {
    setMapMode('leaflet');
    setSelected(null);
  }

  return (
    <div className="flex-1 w-full relative overflow-x-hidden bg-[#0a0f1c]">
      <main className="relative z-10 w-full bg-navy-900 flex flex-col items-center rounded-b-[2.5rem] border-b border-white/5 shadow-2xl pb-12">
        <div className="w-full max-w-7xl mx-auto px-6 py-12 flex flex-col">

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">Temukan Dokter Spesialis</h1>
            <p className="text-gray-400">Klik nama dokter untuk menampilkan lokasi rumah sakit di Google Maps.</p>
          </div>

          {/* Search + Filter */}
          <div className="glass-panel p-4 rounded-2xl flex flex-col sm:flex-row gap-4 mb-8">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Cari nama, kota, atau fasilitas..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full bg-navy-900 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
            <div className="flex gap-2">
              {['All', 'BPJS', 'Swasta'].map(t => (
                <button key={t} onClick={() => setTypeFilter(t)}
                  className={clsx(
                    'px-6 py-3 rounded-xl border text-sm font-medium transition-colors',
                    typeFilter === t
                      ? 'bg-emerald-500 border-emerald-500 text-white'
                      : 'bg-surface border-white/10 text-gray-400 hover:text-white'
                  )}>{t === 'All' ? 'Semua' : t}</button>
              ))}
            </div>
          </div>

          {/* Two-column layout */}
          <div className="w-full grid grid-cols-1 lg:grid-cols-3 gap-8 h-[620px]">

            {/* ── Doctor List ─────────────────────────── */}
            <div className="lg:col-span-1 glass-panel rounded-3xl overflow-hidden flex flex-col h-full">
              <div className="p-5 border-b border-white/10 bg-surface/50 flex items-center justify-between">
                <h3 className="font-semibold">{filtered.length} Dokter Ditemukan</h3>
                {selected && (
                  <button onClick={backToOverview}
                    className="text-xs text-gray-400 hover:text-white flex items-center gap-1 transition-colors">
                    <Map className="w-3 h-3" /> Semua lokasi
                  </button>
                )}
              </div>
              <div className="flex-1 overflow-y-auto p-3 space-y-3">
                {filtered.length === 0 && (
                  <p className="p-6 text-center text-gray-500 text-sm">Tidak ada dokter ditemukan.</p>
                )}
                {filtered.map(d => {
                  const active = selected?.id === d.id;
                  return (
                    <div key={d.id}
                      ref={el => { cardRefs.current[d.id] = el; }}
                      onClick={() => selectDoctor(d)}
                      className={clsx(
                        'p-4 rounded-2xl border cursor-pointer transition-all duration-200',
                        active
                          ? 'bg-emerald-500/10 border-emerald-500 shadow-[0_0_16px_rgba(16,185,129,0.15)]'
                          : 'bg-surface border-white/5 hover:border-emerald-500/40'
                      )}
                    >
                      {/* Name + Badge */}
                      <div className="flex justify-between items-start gap-2 mb-1">
                        <h4 className={clsx('font-bold text-sm leading-snug', active ? 'text-emerald-400' : 'text-white')}>
                          {d.name}
                        </h4>
                        <span className={clsx(
                          'text-xs px-2 py-0.5 rounded border font-medium shrink-0',
                          d.type === 'BPJS'
                            ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
                            : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                        )}>{d.type}</span>
                      </div>

                      <p className="text-emerald-500 text-xs font-medium mb-3">{d.specialty}</p>

                      {/* Details */}
                      <div className="space-y-1.5 text-xs text-gray-400">
                        <span className="flex items-start gap-1.5">
                          <Building className="w-3.5 h-3.5 mt-0.5 shrink-0" />{d.facility}
                        </span>
                        <span className="flex items-start gap-1.5">
                          <MapPin className="w-3.5 h-3.5 mt-0.5 shrink-0" />{d.city}, {d.province}
                        </span>
                        <span className="flex items-start gap-1.5">
                          <Phone className="w-3.5 h-3.5 mt-0.5 shrink-0" />{d.phone}
                        </span>
                      </div>

                      {/* Actions shown when selected */}
                      {active && (
                        <div className="mt-3 pt-3 border-t border-emerald-500/20 flex items-center justify-between">
                          <p className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
                            <Navigation className="w-3 h-3" /> Ditampilkan di peta
                          </p>
                          {/* Open in Google Maps button */}
                          <a
                            href={d.gmaps_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={e => e.stopPropagation()}
                            className="flex items-center gap-1 text-xs bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded-lg transition-colors font-medium"
                          >
                            <ExternalLink className="w-3 h-3" />
                            Buka Google Maps
                          </a>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ── Map Panel ───────────────────────────── */}
            <div className="lg:col-span-2 rounded-3xl overflow-hidden border border-white/10 h-full relative" style={{ zIndex: 0 }}>

              {/* Google Maps Embed — shown when a doctor is selected */}
              {mapMode === 'gmaps' && selected && selected.gmaps_embed && (
                <div className="absolute inset-0 flex flex-col z-10">
                  {/* Top bar */}
                  <div className="flex items-center justify-between px-4 py-2.5 bg-[#0d1526] border-b border-white/10">
                    <div className="flex items-center gap-2 text-sm text-white font-medium">
                      <MapPin className="w-4 h-4 text-emerald-400" />
                      {selected.facility} — {selected.city}
                    </div>
                    <div className="flex items-center gap-2">
                      <a
                        href={selected.gmaps_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 text-xs bg-emerald-500 hover:bg-emerald-400 text-white px-3 py-1.5 rounded-lg transition-colors font-semibold"
                      >
                        <ExternalLink className="w-3 h-3" />
                        Buka di Google Maps
                      </a>
                      <button
                        onClick={backToOverview}
                        className="text-xs text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-lg transition-colors"
                      >
                        ← Semua lokasi
                      </button>
                    </div>
                  </div>
                  {/* iFrame */}
                  <iframe
                    key={selected.gmaps_embed}
                    src={selected.gmaps_embed}
                    className="flex-1 w-full border-0"
                    allowFullScreen
                    loading="lazy"
                    referrerPolicy="no-referrer-when-downgrade"
                    title={`Lokasi ${selected.facility}`}
                  />
                </div>
              )}

              {/* Leaflet overview — shown when no doctor is selected */}
              <div className={clsx('absolute inset-0', mapMode === 'gmaps' ? 'invisible' : 'visible')}>
                <MapContainer center={[-6.2, 106.816666]} zoom={5} style={{ height: '100%', width: '100%' }}>
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <FlyToLocation lat={flyCoords.lat} lng={flyCoords.lng} />
                  {filtered.map(d => (
                    <Marker key={d.id} position={[d.lat, d.lng]}
                      eventHandlers={{ click: () => selectDoctor(d) }}>
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

              {/* Hint overlay when no doctor selected */}
              {mapMode === 'leaflet' && (
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-[999] pointer-events-none">
                  <div className="bg-black/60 backdrop-blur text-white text-xs px-4 py-2 rounded-full border border-white/10 flex items-center gap-2">
                    <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                    Klik nama dokter atau marker untuk detail Google Maps
                  </div>
                </div>
              )}
            </div>

          </div>
        </div>
      </main>
      <CinematicFooter />
    </div>
  );
}
