# Sequence Diagram LungScan AI

Dokumen ini berisi dua sequence diagram untuk jurnal sistem LungScan AI.
Diagram dibuat menggunakan sintaks `sequenceDiagram` Mermaid, kompatibel dengan **[mermaid.live](https://mermaid.live)**.

**Keterangan Notasi:**

| Simbol Mermaid | Makna |
|---|---|
| `actor` | Aktor manusia (Pengguna) |
| `participant` | Komponen sistem |
| `->>` | Pesan sinkron (synchronous message) |
| `-->>` | Pesan balasan (return / response) |
| `alt / else` | Blok kondisional (percabangan) |
| `activate / deactivate` | Aktivasi lifeline (eksekusi aktif) |
| `Note` | Anotasi / keterangan tambahan |

---

## Gambar 4.9 Sequence Diagram Skrining Diagnostik

```mermaid
sequenceDiagram
    autonumber
    actor Pengguna
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant AI as TensorFlow AI Engine

    Pengguna ->> FE: Mengunggah file citra CT-Scan dada

    activate FE
    FE ->> FE: validateFile()
    Note right of FE: Memeriksa ekstensi (JPG/PNG/DCM)<br/>dan ukuran file (maks. 10 MB)

    alt File tidak valid
        FE -->> Pengguna: Menampilkan error message<br/>(format atau ukuran tidak sesuai)
    else File valid
        FE ->> BE: POST /api/predict<br/>(multipart/form-data)
        deactivate FE

        activate BE
        BE ->> BE: preprocess_image()
        Note right of BE: Normalisasi nilai piksel (÷ 255.0)<br/>Resize ke 460×460 dan 224×224 piksel

        BE ->> AI: predict_type(image_460x460)
        activate AI
        AI -->> BE: array probabilitas kelas kanker<br/>+ fitur konvolusi conv5_block3_out
        deactivate AI

        BE ->> BE: calculate_gradcam()
        Note right of BE: Kalkulasi Class Activation Map<br/>dengan bobot BN-Corrected Dense Layer<br/>→ Overlay heatmap pada citra asli

        alt Tipe prediksi = Normal
            BE ->> BE: Set severity = Normal<br/>confidence = 100%
            Note right of BE: Bypass model keparahan<br/>demi efisiensi komputasi
        else Tipe prediksi = Kanker (Adeno / Large Cell / Squamous)
            BE ->> AI: predict_severity(image_224x224)
            activate AI
            AI -->> BE: kelas keparahan (Benign / Malignant)<br/>+ nilai confidence
            deactivate AI
        end

        BE ->> BE: Encode Grad-CAM → Base64 PNG string
        BE ->> BE: load_clinical_guidance(guidance.json)
        Note right of BE: Mencocokkan label tipe dan severity<br/>dengan template panduan Do's and Don'ts<br/>serta tingkat urgensi konsultasi

        BE -->> FE: HTTP 200 Response JSON<br/>{type, confidence, severity,<br/>heatmap_base64, guidance, metrics}
        deactivate BE

        activate FE
        FE ->> FE: Menghentikan loading spinner<br/>Merender kartu diagnosis
        Note right of FE: Render grafik batang probabilitas,<br/>overlay heatmap interaktif,<br/>dan panduan penanganan klinis
        FE -->> Pengguna: Menampilkan halaman hasil diagnosis
        deactivate FE
    end
```

---

## Gambar 4.10 Sequence Diagram Fitur Pencarian Dokter dan Cetak Laporan

```mermaid
sequenceDiagram
    autonumber
    actor Pengguna
    participant FE as React Frontend
    participant DJ as doctors.json
    participant LF as Leaflet.js

    Note over Pengguna, LF: Skenario A — Pencarian Dokter Spesialis

    Pengguna ->> FE: Memasukkan kueri wilayah (kota/provinsi)<br/>atau memilih filter asuransi (BPJS/Swasta)

    activate FE
    FE ->> FE: searchDoctor(query, filter)
    Note right of FE: Parsing input pengguna<br/>dan menyiapkan parameter pencarian

    FE ->> DJ: Membaca data direktori secara asinkronus
    activate DJ
    DJ -->> FE: Array of objects<br/>{nama_dokter, spesialisasi,<br/>nama_rs, koordinat, kontak}
    deactivate DJ

    FE ->> LF: renderMarkers(data_koordinat)
    activate LF
    LF -->> FE: Memperbarui kanvas peta digital<br/>dengan pin lokasi interaktif
    deactivate LF

    FE -->> Pengguna: Menampilkan peta dengan<br/>marker faskes hasil pencarian
    deactivate FE

    Pengguna ->> LF: Mengklik salah satu pin lokasi pada peta
    activate LF
    LF ->> LF: showPopup()
    Note right of LF: Mengambil data detail dari<br/>marker yang dipilih pengguna
    LF -->> Pengguna: Menampilkan pop-up informasi detail<br/>{Nama Dokter, Spesialisasi,<br/>Nama RS, Alamat, Nomor Kontak}
    deactivate LF

    Note over Pengguna, LF: Skenario B — Cetak Laporan PDF

    Pengguna ->> FE: Mengklik tombol Cetak Laporan PDF
    activate FE
    FE ->> FE: window.print()
    Note right of FE: Mengeksekusi API pencetakan<br/>bawaan runtime peramban
    FE -->> Pengguna: Memunculkan dialog Print Preview<br/>Konversi layout halaman hasil<br/>menjadi dokumen PDF siap cetak
    deactivate FE
```
