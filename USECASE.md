# Use Case Diagram LungScan AI

Dokumen ini berisi dua diagram use case untuk jurnal sistem LungScan AI.
Diagram dibuat menggunakan sintaks Mermaid (`flowchart`) yang kompatibel dengan **mermaid.live**.

**Keterangan Notasi:**
- Bentuk oval `(["..."])` → **Use Case**
- Bentuk kotak `["..."]` → **Aktor**
- Panah putus `-.->` dengan label `<<extend>>` → **Relasi Perluasan** (kondisional)
- Panah putus `-.->` dengan label `<<include>>` → **Relasi Keharusan** (selalu dipanggil)
- `subgraph` → **Batas Sistem (System Boundary)**

---

## Gambar 4.5 Use Case Antarmuka Pengguna

```mermaid
flowchart LR
    ACTOR_USER["👤\nPengguna\n(Pasien / Dokter)"]
    ACTOR_MAP["🗺️\nLeaflet.js\n(Sistem Peta Eksternal)"]

    subgraph SYSTEM["Sistem LungScan AI — Antarmuka Pengguna"]
        direction TB
        UC1(["Mengakses\nHalaman Utama"])
        UC2(["Mengunggah\nCitra CT-Scan"])
        UC3(["Melihat\nPesan Error"])
        UC4(["Melihat\nHalaman Hasil"])
        UC5(["Mengaktifkan Toggle\nHeatmap Grad-CAM"])
        UC6(["Mengunduh\nLaporan PDF"])
        UC7(["Mencari\nDokter Spesialis"])
    end

    ACTOR_USER --> UC1
    ACTOR_USER --> UC2
    ACTOR_USER --> UC4
    ACTOR_USER --> UC6
    ACTOR_USER --> UC7

    UC1 --> UC2

    UC2 -.->|"<<extend>>\n[format/ukuran tidak valid]"| UC3

    UC4 -.->|"<<extend>>\n[pengguna memilih visualisasi]"| UC5

    UC4 --> UC6
    UC4 --> UC7

    UC7 --> ACTOR_MAP
```

---

## Gambar 4.6 Use Case Alur Inferensi AI

```mermaid
flowchart LR
    ACTOR_USER["👤\nPengguna"]
    ACTOR_JSON["📋\nguidance.json\n(Sumber Data Eksternal)"]

    subgraph SYSTEM["Sistem LungScan AI — Backend Inferensi"]
        direction TB
        UC1(["Melakukan\nInferensi Diagnostik"])

        UC2(["Mengeksekusi\nKlasifikasi Tipe\n(ResNet50)"])
        UC3(["Menghasilkan\nHeatmap Grad-CAM"])
        UC4(["Memuat Panduan\nCDSS"])

        UC5(["Mengeksekusi\nKlasifikasi Keparahan\n(Custom CNN)"])
    end

    ACTOR_USER -->|"Menginisiasi\nanalisis"| UC1

    UC1 -.->|"<<include>>"| UC2
    UC1 -.->|"<<include>>"| UC3
    UC1 -.->|"<<include>>"| UC4

    UC1 -.->|"<<extend>>\n[jika tipe = kanker]"| UC5

    ACTOR_JSON -->|"Menyediakan data\npanduan klinis"| UC4
```
