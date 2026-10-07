import { useState, useEffect, useRef } from "react";
import { FlipReveal, FlipRevealItem } from "@/components/ui/flip-reveal";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  Database,
  Images,
  Loader2,
  X,
  ChevronLeft,
  ChevronRight,
  Info,
} from "lucide-react";

/* ─── Types ──────────────────────────────────────────────────────────────── */
interface ClassInfo {
  label: string;
  color: string;
  description: string;
  dataset: string;
  total: number;
}

interface ImageItem {
  filename: string;
  src: string;
  classKey?: string; // used in "all" flat grid
  classLabel?: string;
  classColor?: string;
}

interface ClassImages {
  class_key: string;
  label: string;
  color: string;
  description: string;
  dataset: string;
  images: ImageItem[];
}

/* ─── Constants ──────────────────────────────────────────────────────────── */
// Removed normal_iq — only one Normal class
const REAL_KEYS = [
  "adenocarcinoma",
  "large_cell_carcinoma",
  "squamous_cell_carcinoma",
  "normal",
  "benign",
  "malignant",
];

const CLASS_KEYS = ["all", ...REAL_KEYS];

const CLASS_LABELS: Record<string, string> = {
  all: "Semua",
  adenocarcinoma: "Adenokarsinoma",
  large_cell_carcinoma: "Sel Besar",
  squamous_cell_carcinoma: "Sel Skuamosa",
  normal: "Normal",
  benign: "Jinak",
  malignant: "Ganas",
};

const DATASET_BADGES: Record<string, { bg: string; text: string }> = {
  "Chest CT-Scan Images": { bg: "bg-blue-500/20", text: "text-blue-300" },
  "IQ-OTH/NCCD Dataset": { bg: "bg-violet-500/20", text: "text-violet-300" },
};

/* ─── Lightbox ───────────────────────────────────────────────────────────── */
function Lightbox({
  images,
  index,
  label,
  color,
  onClose,
}: {
  images: ImageItem[];
  index: number;
  label: string;
  color: string;
  onClose: () => void;
}) {
  const [cur, setCur] = useState(index);

  const prev = () => setCur((c) => (c - 1 + images.length) % images.length);
  const next = () => setCur((c) => (c + 1) % images.length);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // In "all" mode, label/color may come from the image itself
  const displayLabel = images[cur].classLabel ?? label;
  const displayColor = images[cur].classColor ?? color;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-white/90 dark:bg-black/90 backdrop-blur-md"
      onClick={onClose}
    >
      <div
        className="relative max-w-2xl w-full mx-4 flex flex-col items-center gap-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ background: displayColor }}
            />
            <span className="text-slate-900 dark:text-white font-semibold text-lg">
              {displayLabel}
            </span>
            <span className="text-slate-600 dark:text-gray-400 text-sm">
              ({cur + 1}/{images.length})
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white transition-colors p-1 rounded-full hover:bg-slate-200 dark:hover:bg-white/10"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Image */}
        <div className="relative w-full aspect-square bg-slate-100 dark:bg-gray-900 rounded-2xl overflow-hidden border border-slate-300 dark:border-white/10">
          <img
            src={images[cur].src}
            alt={images[cur].filename}
            className="w-full h-full object-contain"
          />
          <button
            onClick={prev}
            className="absolute left-3 top-1/2 -translate-y-1/2 p-2 bg-white/80 hover:bg-white text-slate-900 dark:bg-black/60 dark:hover:bg-black/90 rounded-full dark:text-white transition-all hover:scale-110 shadow-md"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={next}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-white/80 hover:bg-white text-slate-900 dark:bg-black/60 dark:hover:bg-black/90 rounded-full dark:text-white transition-all hover:scale-110 shadow-md"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>

        {/* Filename */}
        <p className="text-slate-500 dark:text-gray-500 text-xs font-mono">
          {images[cur].filename}
        </p>

        {/* Thumbnails strip */}
        <div className="flex gap-2 overflow-x-auto pb-1 max-w-full">
          {images.map((img, i) => (
            <button
              key={i}
              onClick={() => setCur(i)}
              className={`flex-shrink-0 w-12 h-12 rounded-lg overflow-hidden border-2 transition-all ${
                i === cur
                  ? "border-slate-900 dark:border-white scale-105"
                  : "border-transparent opacity-50 hover:opacity-80"
              }`}
            >
              <img src={img.src} alt="" className="w-full h-full object-cover" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── Image Card ─────────────────────────────────────────────────────────── */
function ImageCard({
  img,
  color,
  label,
  onClick,
}: {
  img: ImageItem;
  color: string;
  label: string;
  onClick: () => void;
}) {
  const displayColor = img.classColor ?? color;
  const displayLabel = img.classLabel ?? label;

  return (
    <div
      onClick={onClick}
      className="group relative aspect-square rounded-xl overflow-hidden cursor-zoom-in border border-slate-200 dark:border-white/5 hover:border-slate-400 dark:hover:border-white/20 transition-all duration-300 hover:scale-105 hover:shadow-2xl"
    >
      <img
        src={img.src}
        alt={img.filename}
        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        loading="lazy"
      />
      {/* Hover overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <div className="absolute bottom-0 left-0 right-0 p-3">
          <div className="flex items-center gap-1.5">
            <div
              className="w-2 h-2 rounded-full"
              style={{ background: displayColor }}
            />
            <span className="text-white text-xs font-medium truncate">
              {displayLabel}
            </span>
          </div>
          <p className="text-gray-400 text-[10px] font-mono mt-0.5 truncate">
            {img.filename}
          </p>
        </div>
      </div>
      {/* Color accent top */}
      <div
        className="absolute top-0 left-0 right-0 h-0.5 opacity-60"
        style={{ background: displayColor }}
      />
    </div>
  );
}

/* ─── Class Header Card (shown only in specific class view) ──────────────── */
function ClassCard({
  info,
}: {
  info: ClassInfo;
}) {
  const badge = DATASET_BADGES[info.dataset] ?? {
    bg: "bg-gray-500/20",
    text: "text-gray-300",
  };

  return (
    <div
      className="flex items-start gap-4 p-5 rounded-2xl border border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.03] shadow-sm dark:shadow-none mb-5"
      style={{ borderLeftColor: info.color, borderLeftWidth: 3 }}
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 text-base font-bold"
        style={{ background: info.color + "25", color: info.color }}
      >
        {info.label[0]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-slate-900 dark:text-white font-semibold text-lg">{info.label}</h3>
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide ${badge.bg} ${badge.text}`}
          >
            {info.dataset}
          </span>
        </div>
        <p className="text-slate-600 dark:text-gray-400 text-sm mt-1 leading-relaxed">
          {info.description}
        </p>
        <p className="text-slate-500 dark:text-gray-600 text-xs mt-1.5">
          {info.total} gambar tersedia dalam dataset
        </p>
      </div>
    </div>
  );
}

/* ─── Main Page ──────────────────────────────────────────────────────────── */
export default function Dataset() {
  const [activeFilter, setActiveFilter] = useState("all");
  const [classInfo, setClassInfo] = useState<Record<string, ClassInfo>>({});
  const [classImages, setClassImages] = useState<Record<string, ClassImages>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [lightbox, setLightbox] = useState<{
    images: ImageItem[];
    index: number;
    label: string;
    color: string;
  } | null>(null);
  const loadedRef = useRef<Set<string>>(new Set());

  // Load class info on mount
  useEffect(() => {
    fetch("http://localhost:8000/api/dataset/info")
      .then((r) => r.json())
      .then((data) => setClassInfo(data))
      .catch(console.error);
  }, []);

  // Lazy load images for a class
  const loadClass = async (key: string) => {
    if (loadedRef.current.has(key)) return;
    loadedRef.current.add(key);
    setLoading((prev) => ({ ...prev, [key]: true }));
    try {
      const res = await fetch(
        `http://localhost:8000/api/dataset/images/${key}?n=10`
      );
      const data: ClassImages = await res.json();
      setClassImages((prev) => ({ ...prev, [key]: data }));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading((prev) => ({ ...prev, [key]: false }));
    }
  };

  // Load when filter changes
  useEffect(() => {
    const keysToLoad = activeFilter === "all" ? REAL_KEYS : [activeFilter];
    keysToLoad.forEach(loadClass);
  }, [activeFilter]);

  // Count total loaded images
  const totalImages = Object.values(classImages).reduce(
    (s, c) => s + c.images.length,
    0
  );

  // Flat "all" grid: merge all images with per-image class metadata
  const allImages: ImageItem[] = REAL_KEYS.flatMap((key) => {
    const cls = classImages[key];
    if (!cls) return [];
    return cls.images.map((img) => ({
      ...img,
      classKey: key,
      classLabel: cls.label,
      classColor: cls.color,
    }));
  });

  const isAllLoading = REAL_KEYS.some(
    (k) => loading[k] && !classImages[k]
  );

  const openLightboxAll = (idx: number) =>
    setLightbox({ images: allImages, index: idx, label: "", color: "" });

  const openLightboxClass = (classKey: string, idx: number) => {
    const cls = classImages[classKey];
    if (!cls) return;
    setLightbox({
      images: cls.images,
      index: idx,
      label: cls.label,
      color: cls.color,
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-navy-900 dark:text-white transition-colors duration-200">
      {/* Hero */}
      <div className="relative overflow-hidden bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 border-b border-slate-200 dark:border-white/10">
        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,0.3) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.3) 1px, transparent 1px)`,
            backgroundSize: "40px 40px",
          }}
        />
        <div className="relative max-w-7xl mx-auto px-6 py-16">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
              <Database className="w-5 h-5 text-emerald-400" />
            </div>
            <span className="text-emerald-400 font-mono text-sm uppercase tracking-widest">
              Dataset Docs
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 dark:text-white mb-4 leading-tight">
            Dokumentasi{" "}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-emerald-400">
              Dataset CT Scan
            </span>
          </h1>
          <p className="text-slate-600 dark:text-gray-400 text-lg max-w-2xl leading-relaxed">
            Koleksi gambar CT scan paru-paru yang digunakan untuk melatih model
            LungScan AI. Setiap kelas menampilkan 10 sampel representatif dari
            dataset.
          </p>

          {/* Stats row — no "Sumber Dataset" */}
          <div className="flex flex-wrap gap-8 mt-8">
            {[
              {
                label: "Total Kelas",
                value: String(REAL_KEYS.length),
                color: "text-emerald-400",
              },
              {
                label: "Gambar Ditampilkan",
                value: `${totalImages}`,
                color: "text-emerald-400",
              },
              {
                label: "Akurasi Model",
                value: "88%",
                color: "text-violet-400",
              },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className={`text-2xl font-bold ${stat.color}`}>
                  {stat.value}
                </div>
                <div className="text-gray-500 text-xs mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Info banner */}
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center gap-3 text-sm text-amber-300/80 bg-amber-500/10 border border-amber-500/20 rounded-xl px-4 py-3">
          <Info className="w-4 h-4 flex-shrink-0 text-amber-400" />
          <span>
            Gambar ditampilkan sebagai thumbnail. Klik untuk memperbesar dan
            navigasi antar sampel dengan tombol panah atau keyboard.
          </span>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="sticky top-[65px] z-30 bg-white/90 dark:bg-slate-900/90 backdrop-blur-lg border-b border-slate-200 dark:border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-3">
          <ToggleGroup
            type="single"
            value={activeFilter}
            onValueChange={(v) => v && setActiveFilter(v)}
            className="flex-wrap justify-start gap-1"
          >
            {CLASS_KEYS.map((key) => (
              <ToggleGroupItem
                key={key}
                value={key}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all text-slate-600 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white data-[state=on]:text-slate-900 dark:data-[state=on]:text-white data-[state=on]:bg-slate-200 dark:data-[state=on]:bg-white/10"
              >
                {CLASS_LABELS[key]}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">

        {/* ── "Semua" mode: flat grid, no class headers ── */}
        {activeFilter === "all" && (
          <>
            {isAllLoading && allImages.length === 0 ? (
              <div className="flex items-center justify-center py-24">
                <div className="flex flex-col items-center gap-3">
                  <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                  <p className="text-gray-500 text-sm">Memuat semua gambar...</p>
                </div>
              </div>
            ) : allImages.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-3">
                {allImages.map((img, i) => (
                  <ImageCard
                    key={`all-${i}`}
                    img={img}
                    color={img.classColor ?? "#fff"}
                    label={img.classLabel ?? ""}
                    onClick={() => openLightboxAll(i)}
                  />
                ))}
                {/* Loading placeholders for classes still fetching */}
                {REAL_KEYS.filter(
                  (k) => loading[k] && !classImages[k]
                ).map((k) =>
                  Array.from({ length: 10 }).map((_, i) => (
                    <div
                      key={`skeleton-${k}-${i}`}
                      className="aspect-square rounded-xl bg-white/5 animate-pulse"
                    />
                  ))
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center py-16">
                <div className="flex flex-col items-center gap-2 text-gray-600">
                  <Images className="w-8 h-8" />
                  <p className="text-sm">Memuat gambar dataset...</p>
                </div>
              </div>
            )}
          </>
        )}

        {/* ── Specific class mode: header card + image grid ── */}
        {activeFilter !== "all" && (
          <FlipReveal
            keys={[activeFilter]}
            showClass="block"
            hideClass="hidden"
            className="space-y-0"
          >
            {REAL_KEYS.map((classKey) => {
              const info = classInfo[classKey];
              const loaded = classImages[classKey];
              const isLoading = loading[classKey];

              return (
                <FlipRevealItem key={classKey} flipKey={classKey}>
                  <section>
                    {/* Class header — shown only in specific class view */}
                    {info && <ClassCard info={info} />}

                    {/* Images grid */}
                    {isLoading ? (
                      <div className="flex items-center justify-center py-16">
                        <div className="flex flex-col items-center gap-3">
                          <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                          <p className="text-gray-500 text-sm">
                            Memuat gambar {CLASS_LABELS[classKey]}...
                          </p>
                        </div>
                      </div>
                    ) : loaded ? (
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                        {loaded.images.map((img, i) => (
                          <ImageCard
                            key={i}
                            img={img}
                            color={loaded.color}
                            label={loaded.label}
                            onClick={() => openLightboxClass(classKey, i)}
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="flex items-center justify-center py-12">
                        <div className="flex flex-col items-center gap-2 text-gray-600">
                          <Images className="w-8 h-8" />
                          <p className="text-sm">Belum ada gambar dimuat</p>
                        </div>
                      </div>
                    )}
                  </section>
                </FlipRevealItem>
              );
            })}
          </FlipReveal>
        )}
      </div>

      {/* Lightbox */}
      {lightbox && (
        <Lightbox
          images={lightbox.images}
          index={lightbox.index}
          label={lightbox.label}
          color={lightbox.color}
          onClose={() => setLightbox(null)}
        />
      )}
    </div>
  );
}
