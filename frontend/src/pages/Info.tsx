import React from 'react';
import { ShieldAlert, Info as InfoIcon, HeartPulse, FileText } from 'lucide-react';
import { CinematicFooter } from '../components/ui/motion-footer';

const Info: React.FC = () => {
  return (
    <div className="flex-1 w-full relative overflow-x-hidden bg-[#0a0f1c]">
      <main className="relative z-10 w-full bg-navy-900 flex flex-col items-center rounded-b-[2.5rem] border-b border-white/5 shadow-2xl pb-12">
        <div className="w-full max-w-4xl mx-auto px-6 py-12 animate-fade-in">
          
          <div className="text-center mb-16 mt-8">
            <h1 className="text-4xl lg:text-5xl font-bold mb-6">Informasi & Disclaimer</h1>
            <p className="text-gray-400 text-lg">Mengenal platform LungScan AI dan batasan teknologi kecerdasan buatan dalam skrining medis.</p>
          </div>

          <div className="glass-panel p-8 md:p-12 rounded-3xl border-amber-500/30 relative overflow-hidden mb-12">
            <div className="absolute top-0 right-0 p-8 text-amber-500/10 pointer-events-none">
              <ShieldAlert className="w-64 h-64" />
            </div>
            
            <div className="relative z-10">
              <div className="flex items-center gap-3 text-amber-400 mb-6">
                <ShieldAlert className="w-8 h-8" />
                <h2 className="text-2xl font-bold">Disclaimer Medis Wajib</h2>
              </div>
              
              <div className="space-y-6 text-gray-300 text-lg leading-relaxed">
                <p>
                  <strong className="text-white">LungScan AI adalah alat bantu skrining awal, BUKAN perangkat diagnosis medis resmi.</strong>
                </p>
                <p>
                  Hasil analisis yang diberikan oleh platform ini berbasis kecerdasan buatan (Deep Learning). Meskipun telah dilatih dengan dataset medis, sistem ini <strong>tidak mencapai akurasi 100%</strong> dan dapat menghasilkan prediksi keliru (false positive atau false negative).
                </p>
                <p className="text-amber-300 font-medium">
                  Selalu konsultasikan hasil dari platform ini dengan dokter spesialis paru (Pulmonologi) atau Onkologi yang berkualifikasi. Jangan mengambil keputusan medis, menunda pengobatan, atau mengubah pengobatan Anda semata-mata berdasarkan hasil dari platform ini.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
            <div className="glass-panel p-8 rounded-3xl">
              <div className="flex items-center gap-3 text-emerald-400 mb-4">
                <HeartPulse className="w-6 h-6" />
                <h3 className="text-xl font-bold text-white">Tujuan Kami</h3>
              </div>
              <p className="text-gray-400 leading-relaxed">
                Meningkatkan kesadaran masyarakat terhadap kesehatan paru-paru dan memfasilitasi deteksi dini melalui teknologi agar pasien dapat segera merujuk ke dokter spesialis untuk penanganan lebih lanjut.
              </p>
            </div>

            <div className="glass-panel p-8 rounded-3xl">
              <div className="flex items-center gap-3 text-cyan-400 mb-4">
                <InfoIcon className="w-6 h-6" />
                <h3 className="text-xl font-bold text-white">Batasan Sistem</h3>
              </div>
              <ul className="text-gray-400 leading-relaxed space-y-2 list-disc list-inside">
                <li>Hanya dapat membedakan 4 kelas (Adenocarcinoma, SCC, Large Cell, Normal).</li>
                <li>Membutuhkan citra CT-Scan yang bersih dan jelas.</li>
                <li>Bukan pengganti biopsi klinis.</li>
              </ul>
            </div>
          </div>

          <div className="glass-panel p-8 rounded-3xl text-center">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-bold mb-2">Kebijakan Privasi</h3>
            <p className="text-gray-400 max-w-2xl mx-auto">
              File CT-scan yang Anda unggah hanya diproses untuk keperluan analisis pada saat itu juga. Kami <strong>tidak menyimpan</strong> file tersebut di server kami secara permanen dan data dihapus secara otomatis setelah analisis selesai.
            </p>
          </div>

        </div>
      </main>
      <CinematicFooter />
    </div>
  );
};

export default Info;
