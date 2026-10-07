# Penjelasan Flowchart Sistem LungScan AI

Berdasarkan Gambar 4.1, alur sistem dimulai ketika pengguna membuka
aplikasi melalui website LungScan AI. Pada halaman utama, pengguna
disajikan dengan antarmuka unggah gambar yang memungkinkan pengguna
untuk mengunggah citra CT-Scan paru-paru dalam format JPEG, PNG, maupun
DCM.

Setelah gambar diunggah, sistem melakukan validasi terhadap file yang
diberikan. Apabila gambar tidak valid atau tidak sesuai dengan format yang
diterima, maka sistem akan menampilkan pesan kesalahan dan pengguna
diminta untuk mengunggah ulang gambar yang benar. Namun, apabila gambar
dinyatakan valid, sistem akan melanjutkan ke tahap pemrosesan.

Pada tahap pemrosesan, sistem mengirimkan citra CT-Scan ke model
kecerdasan buatan berbasis ResNet50 yang telah dilatih untuk mendeteksi
jenis dan tingkat keparahan kanker paru-paru. Model melakukan analisis
terhadap gambar secara otomatis dan menghasilkan prediksi berupa jenis
kanker (Adenokarsinoma, Karsinoma Sel Besar, Karsinoma Sel Skuamosa,
atau Normal) beserta tingkat keparahan (Benign, Malignant, atau Normal).

Setelah proses analisis selesai, sistem menampilkan halaman hasil
diagnosis kepada pengguna. Informasi yang ditampilkan mencakup diagnosis
utama beserta skor keyakinan model, visualisasi heatmap Grad-CAM yang
menunjukkan area paru-paru yang memicu deteksi, tingkat keparahan
kondisi, serta panduan penanganan pertama berupa anjuran dan larangan
yang sesuai dengan hasil diagnosis.

Tahap terakhir, sistem memberikan opsi kepada pengguna berdasarkan
kebutuhannya. Apabila pengguna membutuhkan konsultasi lebih lanjut dengan
tenaga medis, pengguna dapat diarahkan ke halaman Doctor Finder untuk
menemukan dokter spesialis onkologi atau paru-paru terdekat. Apabila
pengguna tidak membutuhkan layanan tersebut, alur sistem berakhir pada
tahap ini. Dengan adanya flowchart ini, alur kerja sistem dapat terlihat
lebih jelas sehingga memudahkan proses pemahaman dan implementasi sistem
pada tahap pengembangan.
