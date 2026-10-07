# Activity Diagram LungScan AI

Dokumen ini berisi dua activity diagram untuk jurnal sistem LungScan AI.
Diagram dibuat menggunakan sintaks Mermaid `flowchart LR` + `subgraph` sebagai swimlane,
kompatibel dengan **[mermaid.live](https://mermaid.live)**.

**Keterangan Notasi:**

| Simbol Mermaid | Bentuk UML | Nama |
|---|---|---|
| `((" "))` diisi hitam | ● Lingkaran penuh | **Initial Node** — Titik mulai |
| `((" "))` bergaris ganda | ◉ Lingkaran berbingkai | **Activity Final Node** — Titik selesai |
| `[Teks]` | Persegi panjang sudut membulat | **Activity** — Aktivitas/aksi |
| `{Teks?}` | Belah ketupat | **Decision Node** — Gerbang keputusan |
| `subgraph` | Jalur horizontal | **Swimlane** — Kolom partisipan |

---

## Gambar 4.7 Activity Diagram Skrining Diagnostik

```mermaid
flowchart LR
    subgraph PENGGUNA["     Pengguna     "]
        direction TB
        S((" "))
        U1[Mengakses Halaman Utama]
        U2[Mengunggah Citra CT-Scan]
        U3[Mengunggah Ulang File]
        U4[Mengklik Tombol Analisis]
        U5[Membaca Hasil Diagnosis]
        U6[Mencetak Laporan PDF]
        E(("◉"))
    end

    subgraph FRONTEND["     Sistem Frontend     "]
        direction TB
        F1[Memeriksa Format File\nJPG atau PNG atau DCM\ndan Ukuran Maksimal 10 MB]
        D1{File Valid?}
        F2[Menampilkan Pesan Error\nFormat atau Ukuran Tidak Sesuai]
        F3[Mengaktifkan Tombol Analisis]
        F4[Menampilkan Layar Loading]
        F5[Merender Halaman Hasil\nDiagnosis dan Heatmap dan Panduan]
    end

    subgraph BACKEND["     Backend dan AI Engine     "]
        direction TB
        B1[Prapemrosesan Citra\nNormalisasi Matriks Piksel]
        B2[Klasifikasi Tipe Kanker\nResNet50 dan Ekstraksi Fitur\nGrad-CAM Bersamaan]
        D2{Tipe = Normal?}
        B3[Menetapkan Severity Normal\nKepercayaan 100 Persen]
        B4[Klasifikasi Keparahan\nCustom CNN\nBenign atau Malignant]
        B5[Mengambil Panduan Penanganan\ndari guidance.json]
        B6[Merakit Response JSON\nPrediksi dan Heatmap dan Panduan]
    end

    S --> U1
    U1 --> U2
    U2 --> F1
    F1 --> D1
    D1 -->|Tidak Valid| F2
    F2 --> U3
    U3 --> F1
    D1 -->|Valid| F3
    F3 --> U4
    U4 --> F4
    F4 --> B1
    B1 --> B2
    B2 --> D2
    D2 -->|Normal| B3
    D2 -->|Kanker| B4
    B3 --> B5
    B4 --> B5
    B5 --> B6
    B6 --> F5
    F5 --> U5
    U5 --> U6
    U6 --> E

    classDef startNode fill:#1a1a1a,color:#1a1a1a,stroke:#1a1a1a,shape:circle
    classDef finalNode fill:#fff,color:#1a1a1a,stroke:#1a1a1a,stroke-width:3px
    class S startNode
    class E finalNode
```

---

## Gambar 4.8 Activity Diagram Fitur Pencarian Dokter

```mermaid
flowchart LR
    subgraph PENGGUNA["     Pengguna     "]
        direction TB
        S((" "))
        U1[Menekan Tombol Cari Dokter]
        U2[Memasukkan Nama\nKota atau Provinsi]
        U3[Memilih Filter Fasilitas\nBPJS atau Swasta]
        U4[Mengklik Marker Lokasi\npada Peta]
        U5[Membaca Informasi\nDetail Dokter dan Rumah Sakit]
        E(("◉"))
    end

    subgraph SISTEM["     Sistem     "]
        direction TB
        S1[Memuat Halaman Doctor Finder]
        S2[Merender Kanvas Peta Interaktif\nmenggunakan Leaflet.js]
        D1{Metode\nPencarian?}
        S3[Mencocokkan Kueri Teks\nterhadap Data doctors.json]
        S4[Mencocokkan Filter Fasilitas\nterhadap Data doctors.json]
        S5[Memperbarui Marker Pin\npada Peta Interaktif sesuai\nKoordinat Faskes Hasil Pencarian]
        S6[Menampilkan Pop-up\nInformasi Detail\nNama Dokter\nSpesialisasi\nNama Rumah Sakit\nAlamat Operasional\nNomor Kontak]
    end

    S --> U1
    U1 --> S1
    S1 --> S2
    S2 --> D1
    D1 -->|Pencarian Teks| U2
    D1 -->|Filter Fasilitas| U3
    U2 --> S3
    U3 --> S4
    S3 --> S5
    S4 --> S5
    S5 --> U4
    U4 --> S6
    S6 --> U5
    U5 --> E

    classDef startNode fill:#1a1a1a,color:#1a1a1a,stroke:#1a1a1a
    classDef finalNode fill:#fff,color:#1a1a1a,stroke:#1a1a1a,stroke-width:3px
    class S startNode
    class E finalNode
```
