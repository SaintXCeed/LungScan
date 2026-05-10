import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { AlertTriangle, Download, ArrowLeft, MapPin } from 'lucide-react';
import clsx from 'clsx';

const badgeColors: Record<string, string> = {
  adenocarcinoma: 'bg-red-500/20 text-red-400 border-red-500/50',
  large_cell_carcinoma: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
  squamous_cell_carcinoma: 'bg-amber-500/20 text-amber-400 border-amber-500/50',
  normal: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50'
};

const formatLabel = (key: string) => {
  return key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
};

const Results: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as any;

  const [guidance, setGuidance] = useState<any>(null);
  const [showHeatmap, setShowHeatmap] = useState(true);

  useEffect(() => {
    if (!state || !state.result) {
      navigate('/');
      return;
    }

    // Fetch guidance data based on prediction
    fetch('http://localhost:8000/api/guidance')
      .then(res => res.json())
      .then(data => {
        if (data[state.result.prediction]) {
          setGuidance(data[state.result.prediction]);
        }
      })
      .catch(console.error);
  }, [state, navigate]);

  if (!state || !state.result) return null;

  const { result, previewImage } = state;
  const predictionKey = result.prediction;
  const badgeClass = badgeColors[predictionKey] || 'bg-gray-500/20 text-gray-400 border-gray-500/50';

  return (
    <div className="w-full max-w-6xl mx-auto px-6 py-12 animate-fade-in">
      
      {/* Disclaimer */}
      <div className="glass-panel border-amber-500/30 bg-amber-500/5 p-4 rounded-xl flex items-start gap-4 mb-8">
        <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-gray-300 leading-relaxed">
          <strong className="text-white">DISCLAIMER MEDIS:</strong> Hasil analisis LungScan AI adalah alat bantu skrining awal berbasis kecerdasan buatan, BUKAN diagnosis medis resmi. Akurasi sistem tidak mencapai 100% dan model dapat menghasilkan prediksi yang keliru. Selalu konsultasikan hasil ini dengan dokter spesialis yang berkualifikasi.
        </p>
      </div>

      <button onClick={() => navigate('/')} className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors mb-8 text-sm font-medium">
        <ArrowLeft className="w-4 h-4" /> Kembali ke Upload
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Image and Heatmap */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div className="glass-panel p-6 rounded-3xl">
            <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
              CT-Scan Analysis
              <div className="flex items-center gap-2 text-sm font-normal">
                <span className={clsx("transition-colors", showHeatmap ? "text-white" : "text-gray-500")}>Heatmap</span>
                <button 
                  onClick={() => setShowHeatmap(!showHeatmap)}
                  className={clsx("w-10 h-6 rounded-full transition-colors relative", showHeatmap ? "bg-emerald-500" : "bg-surface border border-white/20")}
                >
                  <span className={clsx("absolute top-1 w-4 h-4 rounded-full bg-white transition-all", showHeatmap ? "left-5" : "left-1")} />
                </button>
              </div>
            </h3>
            
            <div className="relative w-full aspect-square bg-navy-900 rounded-2xl overflow-hidden border border-white/10">
              {previewImage && (
                <img src={previewImage} alt="Original Scan" className="absolute inset-0 w-full h-full object-cover" />
              )}
              {showHeatmap && result.heatmap_base64 && (
                <img src={result.heatmap_base64} alt="Grad-CAM Heatmap" className="absolute inset-0 w-full h-full object-cover" style={{ opacity: 0.75, mixBlendMode: 'hard-light' }} />
              )}
            </div>
            
            <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
              <span>Timestamp: {new Date().toLocaleString('id-ID')}</span>
              <span>Model Acc: {result.model_accuracy}%</span>
            </div>
          </div>
        </div>

        {/* Right Column: Results & Guidance */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <div className="glass-panel p-8 rounded-3xl">
            <div className="flex items-start justify-between mb-8">
              <div>
                <p className="text-sm text-gray-400 font-medium mb-2 uppercase tracking-widest">Diagnosis Utama</p>
                <h2 className="text-3xl font-bold mb-3">{formatLabel(predictionKey)}</h2>
                <span className={clsx("px-4 py-1.5 rounded-full border text-sm font-semibold", badgeClass)}>
                  Confidence: {result.confidence}%
                </span>
              </div>
              <button onClick={() => window.print()} className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white text-navy-900 font-semibold hover:bg-emerald-400 hover:text-navy-900 transition-colors shadow-lg">
                <Download className="w-4 h-4" /> PDF Report
              </button>
            </div>

            <div className="mb-8">
              <h4 className="text-sm text-gray-400 font-medium mb-4 uppercase tracking-widest">Confidence Scores</h4>
              <div className="space-y-4">
                {Object.entries(result.all_scores).map(([key, score]: [string, any]) => (
                  <div key={key}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-300">{formatLabel(key)}</span>
                      <span className="font-semibold">{score}%</span>
                    </div>
                    <div className="w-full h-2 bg-surface rounded-full overflow-hidden">
                      <div 
                        className={clsx("h-full rounded-full transition-all duration-1000", key === predictionKey ? "bg-emerald-400" : "bg-white/20")}
                        style={{ width: `${score}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {guidance && (
              <div className="border-t border-white/10 pt-8">
                <h4 className="text-sm text-gray-400 font-medium mb-4 uppercase tracking-widest">Panduan Penanganan Pertama</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div className="bg-surface/50 p-5 rounded-2xl border border-white/5">
                    <h5 className="font-semibold text-emerald-400 mb-3 flex items-center gap-2">Do's</h5>
                    <ul className="space-y-2 text-sm text-gray-300">
                      {guidance.dos.map((item: string, i: number) => <li key={i} className="flex items-start gap-2"><span className="text-emerald-500 mt-0.5">•</span> {item}</li>)}
                    </ul>
                  </div>
                  <div className="bg-surface/50 p-5 rounded-2xl border border-white/5">
                    <h5 className="font-semibold text-red-400 mb-3 flex items-center gap-2">Don'ts</h5>
                    <ul className="space-y-2 text-sm text-gray-300">
                      {guidance.donts.map((item: string, i: number) => <li key={i} className="flex items-start gap-2"><span className="text-red-500 mt-0.5">•</span> {item}</li>)}
                    </ul>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-surface/50 p-5 rounded-2xl border border-white/5">
                  <div>
                    <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Tingkat Urgensi</p>
                    <p className="font-semibold">{guidance.urgency} ({guidance.consultation_timeframe})</p>
                  </div>
                  <Link to="/doctor-finder" className="flex items-center gap-2 px-6 py-2.5 rounded-full border border-white/20 hover:bg-white hover:text-navy-900 transition-colors text-sm font-medium w-full sm:w-auto justify-center">
                    <MapPin className="w-4 h-4" /> Cari Dokter
                  </Link>
                </div>
              </div>
            )}
            
          </div>
        </div>
      </div>
    </div>
  );
};

export default Results;
