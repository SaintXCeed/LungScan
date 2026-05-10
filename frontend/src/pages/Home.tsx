import React from 'react';
import Uploader from '../components/Uploader';
import { ContainerScroll } from '../components/ui/container-scroll-animation';
import { Testimonials } from '../components/Testimonials';
import { HeroSection } from '../components/blocks/hero-section-5';
import { ProjectCard } from '../components/ui/project-card';
import { CinematicFooter } from '../components/ui/motion-footer';

const Home: React.FC = () => {
  return (
    <div className="flex-1 w-full relative overflow-x-hidden bg-[#0a0f1c]">
      
      {/* 
        MAIN CONTENT AREA 
        Wrapped with high z-index and background to slide over the cinematic footer
      */}
      <main className="relative z-10 w-full bg-navy-900 flex flex-col items-center rounded-b-[2.5rem] border-b border-white/5 shadow-2xl pb-12">
        {/* New Hero Section 5 with DNA Video & Infinite Slider */}
        <div className="w-full">
          <HeroSection />
        </div>

        {/* Cinematic 3D Scroll Animation for Dashboard Mockup */}
        <div className="w-full flex flex-col overflow-hidden pb-12 mt-12 bg-navy-900/50">
          <ContainerScroll
            titleComponent={
              <div className="mb-12 px-6">
                <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4 text-center">
                  Antarmuka Transparan & <br />
                  <span className="text-emerald-400">Mudah Dipahami.</span>
                </h2>
                <p className="text-gray-400 max-w-xl mx-auto text-center">
                  Lihat hasil prediksi dengan visualisasi heatmap Grad-CAM yang menunjukkan area indikasi pada paru-paru secara persis.
                </p>
              </div>
            }
          >
            {/* Medical Dashboard Image within the 3D scroll card */}
            <img 
              src="/dashboard.png" 
              alt="LungScan AI Dashboard Preview" 
              className="w-full h-full object-cover object-center"
              draggable={false}
            />
          </ContainerScroll>
        </div>

        {/* Feature Highlights */}
        <div className="w-full max-w-6xl mx-auto px-6 pb-20 pt-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Mengapa Memilih LungScan AI?</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">Kami merancang platform ini dengan memprioritaskan privasi, kecepatan interpretasi, dan transparansi teknologi untuk mendukung langkah medis Anda selanjutnya.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full">
            <ProjectCard
              title="Analisis Instan"
              description="Hasil keluar dalam hitungan detik didukung oleh inferensi model AI (TensorFlow) yang telah dioptimasi, tanpa perlu waktu tunggu yang panjang."
              imgSrc="/feature_instant_analysis_1778147611545.png"
              link="#upload-section"
              linkText="Coba Sekarang"
            />

            <ProjectCard
              title="Grad-CAM Heatmap"
              description="Sistem kami sangat transparan. Visualisasi heatmap akan menunjukkan secara akurat area pada paru-paru yang memicu deteksi indikasi oleh AI."
              imgSrc="/feature_grad_cam_1778147629726.png"
              link="#heatmap-example"
              linkText="Lihat Contoh"
            />

            <ProjectCard
              title="Privasi Terjamin"
              description="Setiap citra CT-Scan yang diunggah hanya diproses secara temporal. Kami tidak menyimpan data rekam medis Anda di server kami secara permanen."
              imgSrc="/feature_privacy_1778147646489.png"
              link="/info"
              linkText="Pelajari Keamanan"
            />
          </div>
        </div>

        {/* Heatmap Example Section */}
        <div id="heatmap-example" className="w-full max-w-6xl mx-auto px-6 py-20 border-t border-white/5">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-6">Contoh Analisis <span className="text-emerald-400">Grad-CAM</span></h2>
            <p className="text-gray-400 max-w-2xl mx-auto text-lg">
              Berbeda dengan "Black Box" AI pada umumnya, LungScan AI menyertakan visualisasi heatmap. 
              Sistem menunjukkan secara persis area jaringan paru-paru mana yang memicu deteksi tumor atau anomali.
            </p>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 w-full mt-12">
            {/* Before */}
            <div className="flex flex-col group">
              <div className="relative aspect-[4/3] rounded-3xl overflow-hidden border border-white/10 mb-6 bg-black shadow-2xl">
                <img src="/ct_scan_normal_1778151120446.png" alt="CT Scan Normal" className="w-full h-full object-cover grayscale opacity-80 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="absolute top-6 left-6 bg-black/60 backdrop-blur-md px-5 py-2.5 rounded-full border border-white/10 text-sm font-bold tracking-wide">
                  Input: CT-Scan Asli
                </div>
              </div>
            </div>
            
            {/* After */}
            <div className="flex flex-col group">
              <div className="relative aspect-[4/3] rounded-3xl overflow-hidden border border-emerald-500/30 mb-6 bg-black shadow-[0_0_50px_rgba(16,185,129,0.15)]">
                <img src="/ct_scan_gradcam_1778151138210.png" alt="CT Scan Grad-CAM" className="w-full h-full object-cover" />
                <div className="absolute top-6 left-6 bg-navy-900/80 backdrop-blur-md px-5 py-2.5 rounded-full border border-emerald-500/30 text-sm font-bold tracking-wide text-emerald-400">
                  Output: Prediksi Tumor AI
                </div>
                {/* Glow overlay */}
                <div className="absolute inset-0 bg-emerald-500/10 mix-blend-overlay opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
              </div>
            </div>
          </div>
        </div>

        {/* Testimonials Section */}
        <Testimonials />

        {/* Uploader Section */}
        <div id="upload-section" className="w-full max-w-6xl mx-auto px-6 py-20 flex flex-col items-center relative z-10">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">Mulai Deteksi Sekarang</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">Unggah file CT-Scan dada Anda (JPEG, PNG, atau DCM) untuk memulai analisis awal yang cepat dan terjamin keamanannya.</p>
          </div>
          <div className="w-full max-w-2xl">
            <Uploader />
          </div>
        </div>
      </main>

      {/* The Cinematic Footer injected at the bottom layer */}
      <CinematicFooter />
      
    </div>
  );
};

export default Home;
