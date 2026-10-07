# Flowchart Sistem LungScan AI

Keterangan simbol:

| Simbol Mermaid | Bentuk | Nama Resmi |
|---|---|---|
| `([...])` | Oval | **Terminator** — Mulai / Selesai |
| `[/..../]` | Jajaran Genjang | **Input / Output** — Data masuk/keluar |
| `[...]` | Persegi Panjang | **Proses** — Pengolahan sistem |
| `{...}` | Belah Ketupat | **Decision** — Percabangan kondisi |

---

## Flowchart Sistem

```mermaid
flowchart TD
    A([Mulai])
    B[/Pengguna Mengakses Aplikasi LungScan AI/]
    C[Tampilkan Halaman Utama]
    D[/Pengguna Mengunggah Citra CT-Scan/]
    E{Validasi File}
    F[Kirim File ke Server Backend]
    G[Proses Inferensi ResNet50]
    H[Analisis Grad-CAM dan Heatmap]
    I[Proses Klasifikasi Keparahan]
    J[/Tampilkan Hasil Diagnosis\ndan Heatmap Grad-CAM/]
    K{Unduh\nLaporan PDF?}
    L[Cetak Laporan PDF]
    M([Selesai])

    A --> B
    B --> C
    C --> D
    D --> E
    E -->|Tidak Valid| D
    E -->|Valid| F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K -->|Ya| L
    K -->|Tidak| M
    L --> M
```

---

## Flowchart Pipeline CNN

```mermaid
flowchart TD
    A([Mulai])
    B[Buka Halaman Utama LungScan AI]
    C[/Unggah Gambar CT-Scan/]
    D{Gambar Valid?}
    E[Proses Analisis AI]

    subgraph CNN[" Tahapan CNN "]
        direction TB
        C1[Data Preparation]
        C2[Augmentasi Data]
        C3[Data Splitting]
        C4[Arsitektur Model - ResNet50]
        C5[Training]
        C6[Evaluasi]
        C7[Grad-CAM]
        C8[Ekspor Model]
        C9{Prediksi = Normal?}
        C10[Severity = Normal]
        C11[Klasifikasi Keparahan]
        C12[Output Hasil Diagnosis]

        C1 --> C2 --> C3 --> C4 --> C5 --> C6 --> C7 --> C8
        C8 --> C9
        C9 -->|Ya| C10
        C9 -->|Tidak| C11
        C10 --> C12
        C11 --> C12
    end

    F[/Tampilkan Hasil Diagnosis\nHeatmap · Severity · Panduan/]
    G([Selesai])

    A --> B --> C --> D
    D -->|Tidak| C
    D -->|Ya| E
    E --> CNN
    CNN --> F --> G
```

---

## Flowchart Proses Inferensi CNN

```mermaid
flowchart TD
    A([Mulai])
    B[/Unggah Citra CT-Scan/]
    C{Gambar Valid?}
    D[Proses Analisis AI]

    subgraph CNN[" Proses CNN "]
        direction TB
        P1[Preprocessing\nResize · Normalisasi]
        P2[Ekstraksi Fitur\nResNet50 Backbone]
        P3[Klasifikasi Jenis Kanker\n4 Kelas Output]
        P4{Hasil = Normal?}
        P5[Severity = Normal]
        P6[Klasifikasi Keparahan\n3 Kelas Output]
        P7[Grad-CAM Heatmap]

        P1 --> P2 --> P3 --> P4
        P4 -->|Ya| P5
        P4 -->|Tidak| P6
        P5 --> P7
        P6 --> P7
    end

    E[/Hasil Diagnosis\nJenis · Keparahan · Heatmap · Panduan/]
    F([Selesai])

    A --> B --> C
    C -->|Tidak| B
    C -->|Ya| D
    D --> CNN
    CNN --> E --> F
```
