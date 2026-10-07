import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  AlertTriangle, Download, ArrowLeft, MapPin,
  Activity, ShieldAlert, ShieldCheck, Shield,
  Target, TrendingUp, BarChart2, Cpu, Stethoscope,
} from 'lucide-react';
import clsx from 'clsx';

/* ── Helpers ──────────────────────────────────────────────────────────────── */
const predNames: Record<string, string> = {
  'adenocarcinoma': 'Adenokarsinoma',
  'large.cell.carcinoma': 'Karsinoma Sel Besar',
  'squamous.cell.carcinoma': 'Karsinoma Sel Skuamosa',
  'normal': 'Normal'
};

const fmt = (key: string) =>
  predNames[key.toLowerCase()] || key.replace(/[._]/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/* ── Prediction badge colours ─────────────────────────────────────────────── */
const predBadge: Record<string, string> = {
  adenocarcinoma:            'bg-red-500/20     text-red-400     border-red-500/50',
  'large.cell.carcinoma':    'bg-orange-500/20  text-orange-400  border-orange-500/50',
  'squamous.cell.carcinoma': 'bg-amber-500/20   text-amber-400   border-amber-500/50',
  normal:                    'bg-emerald-500/20 text-emerald-400 border-emerald-500/50',
};

/* ── Severity config ─────────────────────────────────────────────────────── */
const SEV: Record<string, { label: string; color: string; bar: string; icon: any; desc: string; ring: string }> = {
  Normal: {
    label: 'Normal', color: 'text-emerald-300', bar: 'bg-emerald-400',
    icon: ShieldCheck, ring: 'shadow-[0_0_20px_rgba(52,211,153,0.35)] bg-emerald-500/20',
    desc: 'Tidak terdeteksi kelainan ganas. Pemeriksaan rutin tetap dianjurkan.',
  },
  Benign: {
    label: 'Jinak (Benign)', color: 'text-amber-300', bar: 'bg-amber-400',
    icon: Shield, ring: 'shadow-[0_0_20px_rgba(251,191,36,0.35)] bg-amber-500/20',
    desc: 'Terdeteksi kelainan jinak. Konsultasi dengan dokter untuk evaluasi lebih lanjut.',
  },
  Malignant: {
    label: 'Ganas (Malignant)', color: 'text-red-300', bar: 'bg-red-500',
    icon: ShieldAlert, ring: 'shadow-[0_0_20px_rgba(239,68,68,0.45)] bg-red-500/20',
    desc: 'Terdeteksi indikasi ganas. Segera konsultasikan dengan dokter spesialis onkologi.',
  },
};

/* ── RadialGauge ─────────────────────────────────────────────────────────── */
const RadialGauge: React.FC<{ value: number; color: string; size?: number }> = ({ value, color, size = 52 }) => {
  const safe = isFinite(value) && !isNaN(value) ? Math.max(0, Math.min(100, value)) : 0;
  const r = (size - 7) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (safe / 100) * circ;
  return (
    <svg width={size} height={size} style={{ display: 'block' }} className="rotate-[-90deg]">
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={4.5} />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={4.5}
        strokeDasharray={`${dash.toFixed(2)} ${circ.toFixed(2)}`} strokeLinecap="round"
        style={{ transition: 'stroke-dasharray 1s ease-out' }} />
    </svg>
  );
};

/* ── MetricTile ──────────────────────────────────────────────────────────── */
const MetricTile: React.FC<{
  label: string; value: number | null | undefined;
  color: string; hexColor: string; icon: React.FC<any>;
}> = ({ label, value, color, hexColor, icon: Icon }) => {
  const safe = (value !== null && value !== undefined && isFinite(value as number)) ? value as number : null;
  return (
    <div className="bg-white dark:bg-surface/60 border border-slate-200 dark:border-white/5 rounded-2xl p-4 flex items-center gap-3">
      <div className="relative flex-shrink-0" style={{ width: 52, height: 52 }}>
        <RadialGauge value={safe ?? 0} color={hexColor} size={52} />
        <div className="absolute inset-0 flex items-center justify-center">
          <Icon className={clsx('w-4 h-4', color)} />
        </div>
      </div>
      <div>
        <p className="text-xs text-slate-600 dark:text-gray-400 uppercase tracking-wide">{label}</p>
        <p className={clsx('text-xl font-bold', color)}>{safe !== null ? `${safe.toFixed(1)}%` : '—'}</p>
      </div>
    </div>
  );
};

/* ── ClassMetricRow ──────────────────────────────────────────────────────── */
const ClassMetricRow: React.FC<{
  cls: string;
  data: { precision: number; recall: number; f1_score: number; support: number };
  animated: boolean;
}> = ({ cls, data, animated }) => (
  <div className="bg-slate-50 dark:bg-surface/40 border border-slate-200 dark:border-white/5 rounded-xl p-3">
    <div className="flex justify-between mb-2">
      <span className="font-medium text-sm">{fmt(cls)}</span>
      <span className="text-xs text-slate-500 dark:text-gray-500">n={data.support}</span>
    </div>
    {[
      { k: 'Presisi',      v: data.precision, c: 'bg-violet-400' },
      { k: 'Sensitivitas', v: data.recall,    c: 'bg-emerald-400'   },
      { k: 'Skor F1',      v: data.f1_score,  c: 'bg-emerald-400'},
    ].map(({ k, v, c }) => (
      <div key={k} className="flex items-center gap-2 mb-1 last:mb-0">
        <span className="text-xs text-slate-600 dark:text-gray-400 w-16 flex-shrink-0">{k}</span>
        <div className="flex-1 h-1.5 bg-slate-200 dark:bg-surface rounded-full overflow-hidden">
          <div className={clsx('h-full rounded-full transition-all duration-1000 ease-out', c)}
            style={{ width: animated ? `${v}%` : '0%' }} />
        </div>
        <span className="text-xs font-semibold w-11 text-right">{v.toFixed(1)}%</span>
      </div>
    ))}
  </div>
);

/* ── ModelMetricsPanel ───────────────────────────────────────────────────── */
const ModelMetricsPanel: React.FC<{
  title: string;
  subtitle: string;
  icon: React.FC<any>;
  iconColor: string;
  iconBg: string;
  metrics: any;
  animated: boolean;
  note?: string;
}> = ({ title, subtitle, icon: Icon, iconColor, iconBg, metrics, animated, note }) => {
  const ov = metrics?.overall;
  const pc = metrics?.per_class ?? {};
  const activeClasses = Object.entries(pc).filter(([, d]: [string, any]) => d.support > 0);

  return (
    <div className="glass-panel p-6 rounded-3xl flex flex-col gap-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className={clsx('w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0', iconBg)}>
          <Icon className={clsx('w-4 h-4', iconColor)} />
        </div>
        <div>
          <h4 className="font-semibold text-sm">{title}</h4>
          <p className="text-xs text-slate-600 dark:text-gray-400">{subtitle}</p>
        </div>
      </div>

      {/* 4 gauge tiles */}
      <div className="grid grid-cols-2 gap-2">
        <MetricTile label="Akurasi"      value={ov?.accuracy}           color="text-emerald-400" hexColor="#34d399" icon={Activity}   />
        <MetricTile label="Presisi"      value={ov?.weighted_precision} color="text-violet-400"  hexColor="#a78bfa" icon={Target}     />
        <MetricTile label="Sensitivitas" value={ov?.weighted_recall}    color="text-emerald-400"    hexColor="#22d3ee" icon={TrendingUp} />
        <MetricTile label="Skor F1"      value={ov?.weighted_f1}        color="text-amber-400"   hexColor="#fbbf24" icon={BarChart2}  />
      </div>

      {/* Weighted vs Macro table */}
      {ov && (ov.weighted_precision || ov.macro_precision) && (
        <div className="bg-slate-50 dark:bg-surface/40 border border-slate-200 dark:border-white/5 rounded-xl p-3">
          <p className="text-xs text-slate-600 dark:text-gray-400 uppercase tracking-wide mb-2">Overall Average</p>
          <div className="grid grid-cols-3 text-xs">
            <div />
            <div className="text-slate-600 dark:text-gray-400 font-medium uppercase text-center pb-1">Weighted</div>
            <div className="text-slate-600 dark:text-gray-400 font-medium uppercase text-center pb-1">Macro</div>
            {[
              { l: 'Precision', w: ov.weighted_precision, m: ov.macro_precision },
              { l: 'Recall',    w: ov.weighted_recall,    m: ov.macro_recall    },
              { l: 'F1-Score',  w: ov.weighted_f1,        m: ov.macro_f1        },
            ].map(({ l, w, m }) => (
              <React.Fragment key={l}>
                <div className="text-slate-700 dark:text-gray-300 py-0.5">{l}</div>
                <div className="font-semibold text-slate-900 dark:text-white py-0.5 text-center">{w?.toFixed(1)}%</div>
                <div className="font-semibold text-slate-600 dark:text-gray-400 py-0.5 text-center">{m?.toFixed(1)}%</div>
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* Per-class */}
      {activeClasses.length > 0 && (
        <>
          <p className="text-xs text-slate-600 dark:text-gray-400 uppercase tracking-wide -mb-2">Per Kelas</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {activeClasses.map(([cls, data]: [string, any]) => (
              <ClassMetricRow key={cls} cls={cls} data={data} animated={animated} />
            ))}
          </div>
        </>
      )}

      {/* Note */}
      {note && <p className="text-xs text-slate-500 dark:text-gray-500 italic leading-relaxed">{note}</p>}
    </div>
  );
};

/* ══════════════════════════════════════════════════════════════════════════════
   Main Results Page
══════════════════════════════════════════════════════════════════════════════ */
const Results: React.FC = () => {
  const location = useLocation();
  const navigate  = useNavigate();
  const state     = location.state as any;

  const [guidance,       setGuidance]       = useState<any>(null);
  const [typeMetrics,    setTypeMetrics]    = useState<any>(null);
  const [severityMetrics,setSeverityMetrics]= useState<any>(null);
  const [showHeatmap,    setShowHeatmap]    = useState(true);
  const [animated,       setAnimated]       = useState(false);

  useEffect(() => {
    if (!state?.result) { navigate('/'); return; }
    const t = setTimeout(() => setAnimated(true), 200);

    fetch(`${API}/api/guidance`)
      .then(r => r.json())
      .then(d => {
        const key = state.result.prediction;
        const normKey = key ? key.replace(/\./g, '_') : '';
        const match = d[key] || d[normKey] || d[key?.replace(/_/g, '.')];
        if (match) setGuidance(match);
      })
      .catch(console.error);

    fetch(`${API}/api/metrics`)
      .then(r => r.json()).then(setTypeMetrics)
      .catch(console.error);

    fetch(`${API}/api/severity-metrics`)
      .then(r => r.json()).then(setSeverityMetrics)
      .catch(console.error);

    return () => clearTimeout(t);
  }, [state, navigate]);

  if (!state?.result) return null;

  const { result, previewImage } = state;
  const predKey  = result.prediction as string;
  const sevKey   = (result.severity as string) || 'Normal';
  const sevCfg   = SEV[sevKey] ?? SEV.Normal;
  const SevIcon  = sevCfg.icon;
  const sevConf  = Number(result.severity_confidence ?? 0);
  const badgeCls = predBadge[predKey] ?? 'bg-gray-500/20 text-gray-400 border-gray-500/50';

  return (
    <div className="w-full max-w-6xl mx-auto px-6 py-12 animate-fade-in">

      {/* ── Medical Disclaimer ── */}
      <div className="glass-panel border-amber-300 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-500/5 p-4 rounded-xl flex items-start gap-4 mb-8">
        <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
          <strong className="text-slate-900 dark:text-white">DISCLAIMER MEDIS:</strong> Hasil analisis LungScan AI adalah alat bantu skrining awal berbasis kecerdasan buatan, BUKAN diagnosis medis resmi. Selalu konsultasikan hasil ini dengan dokter spesialis yang berkualifikasi.
        </p>
      </div>

      {/* ── Low-confidence / non-CT warning ── */}
      {result.body_part_warning && (
        <div className="glass-panel border-orange-400/40 bg-orange-500/5 p-4 rounded-xl flex items-start gap-4 mb-4">
          <AlertTriangle className="w-6 h-6 text-orange-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-orange-400 text-sm mb-1">⚠️ Peringatan: Kemungkinan Bukan CT-Scan Paru</p>
            <p className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
              {result.body_part_reason || "Gambar ini kemungkinan bukan CT-Scan dada (thorax). CT-Scan kepala, perut, atau bagian tubuh lain dapat menghasilkan prediksi yang tidak akurat."}
            </p>
            <p className="text-xs text-orange-400/70 mt-2 italic">
              Model tetap berjalan dan menampilkan hasil, namun harap verifikasi dengan dokter menggunakan CT-Scan dada yang benar.
            </p>
          </div>
        </div>
      )}

      {result.validation_warning && !result.body_part_warning && (
        <div className="glass-panel border-orange-400/40 bg-orange-500/5 p-4 rounded-xl flex items-start gap-4 mb-4">
          <AlertTriangle className="w-6 h-6 text-orange-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-orange-400 text-sm mb-1">Peringatan: Keyakinan Model Rendah</p>
            <p className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
              Model menunjukkan keyakinan yang rendah ({result.confidence}%) pada gambar ini.
              Hal ini bisa terjadi jika gambar bukan CT-Scan paru yang standar,
              kualitas gambar kurang baik, atau kondisi klinis yang tidak umum.
              Harap konfirmasi dengan tenaga medis profesional.
            </p>
          </div>
        </div>
      )}


      <button onClick={() => navigate('/')} className="flex items-center gap-2 text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white transition-colors mb-8 text-sm font-medium">
        <ArrowLeft className="w-4 h-4" /> Kembali ke Upload
      </button>

      {/* ══ Top 2-column grid ═══════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">

        {/* ── Left: CT-Scan + Severity ── */}
        <div className="lg:col-span-5 flex flex-col gap-6">

          {/* CT-Scan image */}
          <div className="glass-panel p-5 rounded-3xl">
            <h3 className="text-base font-semibold mb-3 flex items-center justify-between">
              Analisis CT-Scan
              <div className="flex items-center gap-2 text-sm font-normal">
                <span className={clsx('transition-colors', showHeatmap ? 'text-slate-900 dark:text-white' : 'text-slate-500 dark:text-gray-500')}>Heatmap</span>
                <button onClick={() => setShowHeatmap(p => !p)}
                  className={clsx('w-10 h-6 rounded-full transition-colors relative', showHeatmap ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-surface border border-slate-300 dark:border-white/20')}>
                  <span className={clsx('absolute top-1 w-4 h-4 rounded-full bg-white transition-all', showHeatmap ? 'left-5' : 'left-1')} />
                </button>
              </div>
            </h3>
            <div className="relative w-full aspect-square bg-slate-100 dark:bg-navy-900 rounded-2xl overflow-hidden border border-slate-200 dark:border-white/10">
              {previewImage && <img src={previewImage} alt="CT-Scan" className="absolute inset-0 w-full h-full object-cover" />}
              {showHeatmap && result.heatmap_base64 && (
                <img src={result.heatmap_base64} alt="CAM Heatmap" className="absolute inset-0 w-full h-full object-cover"
                  style={{ opacity: 0.75, mixBlendMode: 'hard-light' }} />
              )}
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-slate-600 dark:text-gray-400">
              <span>Waktu: {new Date().toLocaleString('id-ID')}</span>
              <span>Akurasi Model: {result.model_accuracy}%</span>
            </div>
          </div>

          {/* Severity card */}
          <div className="glass-panel p-5 rounded-3xl border border-white/10">
            <p className="text-xs text-slate-600 dark:text-gray-400 uppercase tracking-widest font-medium mb-4">Tingkat Keparahan (Severity)</p>
            <div className="flex items-center gap-4 mb-4">
              <div className={clsx('w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0', sevCfg.ring)}>
                <SevIcon className={clsx('w-7 h-7', sevCfg.color)} />
              </div>
              <div>
                <h3 className={clsx('text-2xl font-bold', sevCfg.color)}>{sevCfg.label}</h3>
                <p className="text-slate-600 dark:text-gray-400 text-sm">Keyakinan: {sevConf.toFixed(1)}%</p>
              </div>
            </div>
            <div className="mb-3">
              <div className="w-full h-2.5 bg-slate-200 dark:bg-surface rounded-full overflow-hidden">
                <div className={clsx('h-full rounded-full transition-all duration-1000 ease-out', sevCfg.bar)}
                  style={{ width: animated ? `${sevConf}%` : '0%' }} />
              </div>
            </div>
            <p className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed">{sevCfg.desc}</p>
          </div>
        </div>

        {/* ── Right: Diagnosis + Confidence + Guidance ── */}
        <div className="lg:col-span-7">
          <div className="glass-panel p-8 rounded-3xl h-full">

            {/* Diagnosis header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <p className="text-sm text-slate-600 dark:text-gray-400 font-medium mb-2 uppercase tracking-widest">Diagnosis Utama</p>
                <h2 className="text-3xl font-bold mb-3">{fmt(predKey)}</h2>
                <span className={clsx('px-4 py-1.5 rounded-full border text-sm font-semibold', badgeCls)}>
                  Keyakinan: {result.confidence}%
                </span>
              </div>
              <button onClick={() => window.print()}
                className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-slate-900 text-white dark:bg-white dark:text-navy-900 font-semibold hover:bg-emerald-500 dark:hover:bg-emerald-400 transition-colors shadow-lg flex-shrink-0">
                <Download className="w-4 h-4" /> Laporan PDF
              </button>
            </div>

            {/* Confidence bars */}
            <div className="mb-6">
              <h4 className="text-sm text-slate-600 dark:text-gray-400 font-medium mb-4 uppercase tracking-widest">Skor Keyakinan</h4>
              <div className="space-y-4">
                {Object.entries(result.all_scores).map(([key, score]: [string, any]) => (
                  <div key={key}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-700 dark:text-gray-300">{fmt(key)}</span>
                      <span className="font-semibold">{score}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-200 dark:bg-surface rounded-full overflow-hidden">
                      <div className={clsx('h-full rounded-full transition-all duration-1000', key === predKey ? 'bg-emerald-400' : 'bg-white/20')}
                        style={{ width: animated ? `${score}%` : '0%' }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Guidance */}
            {guidance && (
              <div className="border-t border-white/10 pt-6">
                <h4 className="text-sm text-slate-600 dark:text-gray-400 font-medium mb-4 uppercase tracking-widest">Panduan Penanganan Pertama</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="bg-slate-50 dark:bg-surface/50 p-4 rounded-2xl border border-slate-200 dark:border-white/5">
                    <h5 className="font-semibold text-emerald-400 mb-3 text-sm">Anjuran</h5>
                    <ul className="space-y-1.5 text-sm text-slate-700 dark:text-gray-300">
                      {guidance.dos.map((item: string, i: number) => (
                        <li key={i} className="flex items-start gap-2"><span className="text-emerald-500 mt-0.5">•</span>{item}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="bg-slate-50 dark:bg-surface/50 p-4 rounded-2xl border border-slate-200 dark:border-white/5">
                    <h5 className="font-semibold text-red-400 mb-3 text-sm">Larangan</h5>
                    <ul className="space-y-1.5 text-sm text-slate-700 dark:text-gray-300">
                      {guidance.donts.map((item: string, i: number) => (
                        <li key={i} className="flex items-start gap-2"><span className="text-red-500 mt-0.5">•</span>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-slate-50 dark:bg-surface/50 p-4 rounded-2xl border border-slate-200 dark:border-white/5">
                  <div>
                    <p className="text-xs text-slate-600 dark:text-gray-400 uppercase tracking-wider mb-1">Tingkat Urgensi</p>
                    <p className="font-semibold text-sm">{guidance.urgency} ({guidance.consultation_timeframe})</p>
                  </div>
                  <Link to="/doctor-finder" className="flex items-center gap-2 px-6 py-2.5 rounded-full border border-slate-300 dark:border-white/20 hover:bg-slate-900 hover:text-white dark:hover:bg-white dark:hover:text-navy-900 transition-colors text-sm font-medium w-full sm:w-auto justify-center">
                    <MapPin className="w-4 h-4" /> Cari Dokter
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ══ Full-width Metrics Row ═══════════════════════════════════════════════ */}
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-5">
          <div className="h-px flex-1 bg-slate-200 dark:bg-white/10" />
          <span className="text-xs text-slate-500 dark:text-gray-500 uppercase tracking-widest font-medium">Performa Model</span>
          <div className="h-px flex-1 bg-slate-200 dark:bg-white/10" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Type Classification Model */}
          <ModelMetricsPanel
            title="Model Klasifikasi Jenis"
            subtitle={`ResNet50 — diuji pada ${typeMetrics?.overall?.total_test_samples ?? 315} gambar test set`}
            icon={Cpu}
            iconColor="text-violet-400"
            iconBg="bg-violet-500/20"
            metrics={typeMetrics}
            animated={animated}
          />

          {/* Severity Model */}
          <ModelMetricsPanel
            title="Model Tingkat Keparahan"
            subtitle={`Diuji pada ${severityMetrics?.overall?.total_test_samples ?? 360} gambar (Benign · Malignant · Normal)`}
            icon={Stethoscope}
            iconColor="text-rose-400"
            iconBg="bg-rose-500/20"
            metrics={severityMetrics}
            animated={animated}
            note={severityMetrics?.overall?.avg_confidence ? `Rata-rata keyakinan model: ${severityMetrics.overall.avg_confidence}% (max ${severityMetrics.overall.max_confidence}%, min ${severityMetrics.overall.min_confidence}%)` : undefined}
          />
        </div>
      </div>

    </div>
  );
};

export default Results;
