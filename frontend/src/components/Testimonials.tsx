import { TestimonialsColumn } from "./ui/testimonials-columns-1";
import { motion } from "framer-motion";

import img1 from "../assets/profil_testi/ChatGPT Image May 10, 2026, 02_46_39 PM (1).png";
import img2 from "../assets/profil_testi/ChatGPT Image May 10, 2026, 02_46_39 PM (2).png";
import img3 from "../assets/profil_testi/ChatGPT Image May 10, 2026, 02_46_39 PM (3).png";
import img4 from "../assets/profil_testi/ChatGPT Image May 10, 2026, 02_46_43 PM (4).png";
import img5 from "../assets/profil_testi/ChatGPT Image May 10, 2026, 02_46_43 PM (5).png";
import img6 from "../assets/profil_testi/ChatGPT Image May 10, 2026, 02_46_43 PM (6).png";
import img7 from "../assets/profil_testi/ChatGPT Image May 10, 2026, 02_46_44 PM (7).png";
import img8 from "../assets/profil_testi/ChatGPT Image May 10, 2026, 02_46_44 PM (8).png";
import img9 from "../assets/profil_testi/ChatGPT Image May 10, 2026, 02_46_46 PM (9).png";

const testimonials = [
  {
    text: "Saya tidak menyangka deteksi dini bisa semudah ini. Setelah upload CT-Scan saya, hasilnya keluar dalam hitungan detik dan langsung ada rekomendasi dokter terdekat. Alhamdulillah, saya bisa segera berkonsultasi.",
    image: img1,
    name: "Gilang Budi",
    role: "Pasien, Ngawi",
  },
  {
    text: "Awalnya saya ragu, tapi platform ini benar-benar membantu. Heatmap-nya menunjukkan tepat di mana area yang mencurigakan, sehingga saya lebih siap saat menemui dokter spesialis.",
    image: img2,
    name: "Ichwan Astori",
    role: "Pasien, Ngawi",
  },
  {
    text: "Fitur pencari dokter sangat membantu saya yang tinggal di luar kota. Saya bisa langsung tahu RSUP terdekat yang menerima BPJS tanpa harus repot tanya-tanya dulu.",
    image: img3,
    name: "Rahmad Yusuf",
    role: "Pasien, Semarang",
  },
  {
    text: "Panduan Do's dan Don'ts yang diberikan sangat jelas dan tidak membuat panik. Saya jadi tahu langkah apa yang harus diambil setelah mendapat hasil skrining.",
    image: img4,
    name: "Andy Fatra",
    role: "Pasien, Medan",
  },
  {
    text: "Sebagai mantan perokok, saya selalu khawatir dengan kondisi paru-paru saya. LungScan AI memberikan ketenangan pikiran karena saya bisa memantau kondisi secara berkala dengan mudah.",
    image: img5,
    name: "Kevin tjoa",
    role: "Pasien, Jakarta",
  },
  {
    text: "Tampilan aplikasinya bersih dan sangat mudah dipahami bahkan oleh orang tua saya yang kurang familiar dengan teknologi. Proses upload dan melihat hasil sangat intuitif.",
    image: img6,
    name: "Muhammad Arif",
    role: "Pasien, Yogyakarta",
  },
  {
    text: "Keamanan data adalah kekhawatiran utama saya sebelum mencoba. Setelah membaca Info & Disclaimer-nya, saya jadi lebih yakin bahwa data CT-Scan saya ditangani secara bertanggung jawab.",
    image: img7,
    name: "Salimy Ahsan",
    role: "Pasien, Makassar",
  },
  {
    text: "Confidence score dari AI membantu saya memahami seberapa pasti hasilnya. Saya tidak hanya mendapat kata 'positif' atau 'negatif', tapi juga persentase yang bisa saya diskusikan dengan dokter.",
    image: img8,
    name: "Bintang Rehandhika",
    role: "Pasien, Malang",
  },
  {
    text: "Proses skrining yang biasanya memakan waktu dan biaya, kini bisa dilakukan dari rumah sebagai langkah awal. Ini sangat membantu saya yang memiliki mobilitas terbatas.",
    image: img9,
    name: "Dimas Cakra",
    role: "Pasien, Palembang",
  },
];

const firstColumn = testimonials.slice(0, 3);
const secondColumn = testimonials.slice(3, 6);
const thirdColumn = testimonials.slice(6, 9);

export const Testimonials = () => {
  return (
    <section className="bg-transparent my-20 relative w-full overflow-hidden">
      <div className="max-w-7xl z-10 mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          viewport={{ once: true }}
          className="flex flex-col items-center justify-center max-w-[540px] mx-auto"
        >
          <h2 className="text-3xl md:text-5xl font-bold tracking-tighter text-center">
            Apa kata mereka?
          </h2>
          <p className="text-center mt-5 text-gray-400">
            Platform kami telah membantu banyak pasien mengambil langkah deteksi dini yang lebih cepat dan tepat.
          </p>
        </motion.div>

        <div className="flex justify-center gap-6 mt-14 [mask-image:linear-gradient(to_bottom,transparent,black_15%,black_85%,transparent)] max-h-[600px]">
          <TestimonialsColumn testimonials={firstColumn} duration={15} />
          <TestimonialsColumn testimonials={secondColumn} className="hidden md:block" duration={19} />
          <TestimonialsColumn testimonials={thirdColumn} className="hidden lg:block" duration={17} />
        </div>
      </div>
    </section>
  );
};
