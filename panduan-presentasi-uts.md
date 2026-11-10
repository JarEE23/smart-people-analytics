# PANDUAN LENGKAP PRESENTASI UTS (8 MENIT)
## Mata Kuliah: Kapita Selekta AI Engineering — Minggu 8
**Presenter:** Fajar  
**Judul Sistem:** Smart People Analytics — AI Chat Analyst  
**Format:** 8 Slide Ketat (Maksimal 8), 8 Menit Presentasi, 7 Menit Tanya Jawab  

---

## ⏱️ Manajemen Waktu Presentasi (Total 8 Menit / 480 Detik)

| No. Slide | Topik Wajib | Alokasi Waktu | Target Kata |
|---|---|---|---|
| **Slide 1** | Persoalan (Problem Formulation) | 00:00 – 01:00 (60 dtk) | ~120 kata |
| **Slide 2** | Mengapa AI Generatif? | 01:00 – 02:00 (60 dtk) | ~125 kata |
| **Slide 3** | Rancangan Sistem (Alur Input–Output) | 02:00 – 03:00 (60 dtk) | ~120 kata |
| **Slide 4** | Kendali Output (Schema & Guardrails) | 03:00 – 04:00 (60 dtk) | ~120 kata |
| **Slide 5** | Tool & Batas Akses | 04:00 – 05:00 (60 dtk) | ~120 kata |
| **Slide 6** | Grounding & Retrieval Data | 05:00 – 06:00 (60 dtk) | ~120 kata |
| **Slide 7** | Bukti Sejauh Ini: 1 Keberhasilan & 1 Kegagalan Nyata | 06:00 – 07:05 (65 dtk) | ~135 kata |
| **Slide 8** | Risiko & Rencana Kerja Minggu 9–16 | 07:05 – 08:00 (55 dtk) | ~110 kata |

---

## 📑 Rincian Konten 8 Slide & Naskah Bicara (*Speaker Notes*)

---

### SLIDE 1: PERSOALAN
**Judul Slide:** Persoalan: Pemantauan Arus Manusia & Okupansi Ruang Publik  
**Poin-Poin Visual di Slide:**
- **Siapa yang mengalami:** Pengelola fasilitas kampus/gedung, manajer lab, dan petugas keamanan.
- **Bagaimana diselesaikan sekarang:** 
  1. Penghitungan manual berkala (buku catatan / *tally counter*).
  2. Log data mentah dan monitor CCTV tabular pasif.
- **Mengapa belum cukup:**
  - Ribuan baris log data menyulitkan ekstraksi wawasan cepat (misal: *"Jam berapa paling ramai hari ini?"*).
  - Tidak ada penjelasan naratif atau analisis tren antarhari.
  - Pengguna non-teknis tidak bisa menulis kueri SQL secara instan untuk agregasi waktu.

🗣️ **Naskah Bicara (Menit 00:00 – 01:00):**
> *"Selamat pagi Bapak/Ibu dosen dan rekan-rekan penilai. Persoalan yang saya angkat berakar dari penelitian Tugas Akhir saya di bidang Computer Vision. Pengelola fasilitas gedung dan laboratorium kampus membutuhkan informasi cepat mengenai tingkat keterisian ruangan dan arus masuk-keluar manusia. Saat ini, mereka mengandalkan pencatatan manual atau harus memeriksa ribuan baris log rekaman CCTV di basis data. Cara ini tidak cukup karena membutuhkan keahlian teknis kueri database dan memakan waktu hanya untuk menjawab pertanyaan sederhana seperti jam tersibuk atau tren kenaikan pengunjung dibanding kemarin. Sistem yang saya rancang menjembatani data tabular tersebut dengan kecerdasan buatan analitik."*

---

### SLIDE 2: MENGAPA AI GENERATIF?
**Judul Slide:** Mengapa AI Generatif? (Dan Batasan Ketatnya)  
**Poin-Poin Visual di Slide:**
- **Mengapa Bukan Basis Data Biasa?** Basis data kaku; tidak memahami ragam bahasa alami pengguna, konteks waktu relatif (*"kemarin"*, *"tadi siang"*), dan tidak dapat menyusun narasi ringkas.
- **Mengapa Bukan Formulir / Aturan Biasa?** Formulir kaku membutuhkan puluhan filter *dropdown*; aturan biasa (*if-else*) runtuh saat struktur kalimat pengguna berubah.
- **Mengapa AI Generatif Tepat?** Unggul dalam pemahaman niat (*intent parsing*) dan sintesis wawasan naratif dalam bahasa Indonesia.
- **Batas Kritis:** AI Generatif memiliki kelemahan halusinasi angka. Oleh karena itu, AI **DILARANG** menghitung data sendiri, melainkan dikendalikan melalui pola *Tool Calling* deterministik.

🗣️ **Naskah Bicara (Menit 01:00 – 02:00):**
> *"Pertanyaannya: mengapa harus AI generatif? Mengapa bukan basis data atau formulir biasa? Basis data dan aturan kaku tidak mampu memahami variasi bahasa alami pengguna, seperti konteks waktu 'kemarin' atau perbandingan persentase. Di sisi lain, antarmuka formulir biasa sangat kaku dan membingungkan pengguna non-teknis. Namun, AI generatif memiliki risiko fatal: halusinasi numerik. Oleh karena itu, pada rancangan ini saya memisahkan tanggung jawab secara tegas: basis data menyimpan fakta kejadian, backend menghitung angka yang valid secara deterministik, dan AI generatif bertugas memahami maksud pengguna serta merangkai hasil perhitungan menjadi narasi yang mudah dipahami."*

---

### SLIDE 3: RANCANGAN SISTEM
**Judul Slide:** Arsitektur Sistem: Alur Input hingga Output  
**Poin-Poin Visual di Slide:**
- *[Tampilkan Diagram Arsitektur dari dokumen rancangan-sistem.md]*
- 3 Lapisan Terisolasi:
  1. **Frontend Web**: Input pertanyaan pengguna + Kartu Bukti (*Evidence Card*).
  2. **Backend Flask & AI Service**: Intent Parser $\to$ Analytics Service $\to$ Response Synthesizer.
  3. **Basis Data SQLite**: Tabel `count_events` (IN/OUT, timestamp, source: SIMULATED/YOLO).

🗣️ **Naskah Bicara (Menit 02:00 – 03:00):**
> *"Berikut adalah arsitektur sistem dalam satu gambar. Ketika pengguna mengajukan pertanyaan di web, misalnya 'Jam berapa paling ramai hari ini?', endpoint backend meneruskannya ke AI Service. AI tidak langsung menjawab dari ingatannya, melainkan mengidentifikasi fungsi analitik yang dibutuhkan—dalam kasus ini memanggil fungsi `get_peak_period`. Backend mengeksekusi kueri terstruktur ke basis data SQLite, menghitung nilai agregasi 24 jam secara eksak, lalu mengembalikan data terstruktur ke AI. AI kemudian menyusun respons dalam bahasa Indonesia dengan menyertakan kartu bukti analitik yang dapat diverifikasi oleh pengguna."*

---

### SLIDE 4: KENDALI OUTPUT
**Judul Slide:** Kendali Output: Schema, Validasi & Guardrails  
**Poin-Poin Visual di Slide:**
- **Struktur Payload Terstandar:** JSON wajib memuat `answer`, `source`, `period`, dan `evidence` ({tool, arguments, result}).
- **Batas Nilai Valid (*Guardrails*):**
  - Nilai hitungan wajib $\ge 0$.
  - Proteksi nilai okupansi non-negatif dengan penanda anomali (*negative anomaly flag*).
  - Wajib mencantumkan metadata: periode, angka kalkulasi, dan label sumber data (`SIMULATED` vs `YOLO`).
- **Penanganan Input di Luar Domain (*Out-of-Scope*):**
  - Pertanyaan di luar topik people analytics (misal resep masakan/politik) langsung ditolak secara sopan tanpa halusinasi.
  - Data kosong dinyatakan secara eksplisit tanpa mengarang angka perkiraan.

🗣️ **Naskah Bicara (Menit 03:00 – 04:00):**
> *"Untuk memastikan luaran selalu andal, sistem menerapkan kendali output yang ketat. Luaran API dibatasi oleh skema JSON yang wajib menyertakan objek bukti analitik atau evidence. Terdapat tiga guardrails utama: pertama, nilai hitungan wajib non-negatif dan nilai okupansi diproteksi dari deviasi negatif. Kedua, AI dilarang menyebutkan angka di luar data numerik yang dikembalikan backend. Ketiga, untuk pertanyaan di luar cakupan analitik pergerakan orang, seperti menanyakan resep makanan atau hal umum lainnya, sistem secara tegas menolak dan menjelaskan batas kapabilitasnya secara sopan."*

---

### SLIDE 5: TOOL DAN BATAS AKSES
**Judul Slide:** Whitelisted Tools & Hak Akses Terkendali  
**Poin-Poin Visual di Slide:**
- **Daftar Tool Backend yang Diberikan ke AI:**
  1. `get_summary(start, end)`: Total IN, OUT, Net Flow, estimasi okupansi.
  2. `get_hourly_counts(date)`: Distribusi 24 jam untuk grafik aktivitas.
  3. `compare_periods(p1, p2, metric)`: Menghitung selisih dan persentase perubahan.
  4. `get_peak_period(start, end, metric)`: Mencari jendela jam tersibuk.
  5. `get_occupancy_estimate(date)`: Menghitung sisa orang di dalam area.
- **Batas Akses:** **Read-Only Analitik**. LLM sama sekali tidak memiliki akses bebas untuk mengeksekusi kueri SQL modifikasi (`INSERT`, `UPDATE`, `DELETE`, `DROP`).
- **Persetujuan Manusia (*Human-in-the-Loop*):** Pembersihan histori log atau re-seed database memerlukan konfirmasi dialog eksplisit dari pengguna.

🗣️ **Naskah Bicara (Menit 04:00 – 05:00):**
> *"Sistem menggunakan pendekatan Whitelisted Tools. Kami hanya menyediakan 5 fungsi inti: get_summary, get_hourly_counts, compare_periods, get_peak_period, dan get_occupancy_estimate. Seluruh fungsi ini bersifat Read-Only. Keputusan ini sangat krusial: LLM tidak diberi izin menulis atau mengeksekusi SQL bebas ke database, sehingga mencegah SQL injection dan manipulasi data. Tindakan yang berdampak besar seperti pembersihan histori data atau reset simulasi wajib melalui persetujuan pengguna via antarmuka modal."*

---

### SLIDE 6: GROUNDING DAN RETRIEVAL
**Judul Slide:** Grounding Terstruktur vs Text RAG  
**Poin-Poin Visual di Slide:**
- **Mengapa Structured Grounding, Bukan Text/Vector RAG?**
  - Data pergerakan orang adalah data terstruktur runtun waktu (*time-series tabular*), bukan kumpulan dokumen teks.
  - Vector similarity / embedding tidak mampu melakukan kalkulasi matematis eksak (sum, max, persentase selisih).
- **Strategi Grounding:**
  - AI diikat (*grounded*) langsung pada parameter dan hasil kembalian fungsi agregasi SQLite.
- **Penanganan Jawaban Tidak Ditemukan:**
  - Bila tanggal kueri tidak memiliki data, backend mengembalikan `has_data: false`.
  - AI secara transparan menginformasikan bahwa data belum tercatat di database, meniadakan halusinasi.

🗣️ **Naskah Bicara (Menit 05:00 – 06:00):**
> *"Terkait strategi grounding: sistem ini tidak menggunakan Vector RAG berbasis chunking dokumen teks. Mengapa? Karena data people analytics berbentuk data runtun waktu terstruktur. Metode semantic search pada embedding vektor tidak mampu menjumlahkan baris, mencari jam puncak, atau menghitung persentase perubahan secara presisi matematis. Oleh karena itu, grounding kami lakukan langsung pada fungsi analitik terstruktur. Jika pengguna menanyakan tanggal yang tidak ada di database, sistem mengembalikan status has_data: false, dan AI secara jujur menyampaikan bahwa data belum tersedia tanpa mengarang angka."*

---

### SLIDE 7: BUKTI SEJAUH INI (KEBERHASILAN & KEGAGALAN NYATA)
**Judul Slide:** Bukti Pengujian: 1 Keberhasilan & 1 Kegagalan Nyata  
**Poin-Poin Visual di Slide:**
- **Satu Keberhasilan Terverifikasi:**
  - Kueri perbandingan dua periode (misal: 11 Okt [60 IN] vs 10 Okt [40 IN]).
  - Menghasilkan selisih $+20$ orang, persentase $+50.00\%$, tren `NAIK`, dan diverifikasi 100% cocok dengan uji otomatis Pytest.
- **Satu Kegagalan yang Ditemukan Sendiri (*Self-Discovered Failure*):**
  - **Kasus Uji:** Kueri perbandingan saat periode sebelumnya bernilai 0 ($N_{lama} = 0$).
  - **Penyebab Utama:** *ZeroDivisionError* pada formula $\frac{N_{baru} - N_{lama}}{N_{lama}} \times 100\%$, memicu AI crash atau salah menyebut kenaikan 0%.
  - **Tindakan Perbaikan:** Ditambahkan penanganan kondisional khusus yang mengembalikan `change_percent: None` dengan string `"+N (Basis awal 0)"`. Lulus pada pengujian unit otomatis `test_compare_periods_zero_division`.

🗣️ **Naskah Bicara (Menit 06:00 – 07:05):**
> *"Pada slide ketujuh ini, saya menunjukkan hasil pengujian mandiri. Untuk keberhasilan: sistem berhasil memvalidasi kueri komparatif antarhari dengan hasil selisih dan persentase yang 100% cocok dengan perhitungan matematis. Namun, dalam pengujian batas, saya menemukan satu kegagalan nyata: ketika membandingkan data hari ini dengan hari sebelumnya yang bernilai nol—misalnya hari libur atau tanggal sebelum perekaman dimulai—sistem mengalami ZeroDivisionError pada rumus persentase perubahan. Akibatnya sistem sempat error dan AI berhalusinasi menyatakan angka nol persen. Setelah menganalisis akar masalahnya, saya menambahkan penanganan kondisi batas di backend yang mendeteksi penyebut nol dan mengembalikan keterangan bahwa basis data awal bernilai nol. Kasus ini kini telah teruji dan lulus pada pengujian otomatis Pytest."*

---

### SLIDE 8: RISIKO DAN RENCANA MINGGU 9–16
**Judul Slide:** Mitigasi Risiko & Rencana Kerja AI Chat Analyst (Minggu 9–16)  
**Poin-Poin Visual di Slide:**
- **Risiko Utama:**
  1. *Ambiguitas Waktu Alami*: Frasa relatif (*"jam sibuk tadi siang"*, *"dua hari lalu"*) rawan salah ekstrak parameter tanggal.
  2. *Keterbatasan Single-Turn*: Kueri komposit multi-langkah belum didukung *chained tool calling*.
  3. *Halusinasi Kausalitas*: Risiko AI mengarang alasan eksternal saat ditanya *"mengapa sepi?"*.
- **Rencana Kerja AI Engineering Minggu 9–16:**
  - **Minggu 9–10:** *Multi-Step Chained Tool Calling* untuk mengeksekusi beberapa fungsi analitik berantai.
  - **Minggu 11–12:** Memori percakapan multi-turn & ekspansi mesin resolusi waktu bahasa Indonesia.
  - **Minggu 13–14:** *Causal Guardrails* anti-spekulasi & benchmark evaluasi otomatis (50+ variasi kueri).
  - **Minggu 15–16:** *Proactive Insights* (deteksi anomali tanpa ditanya) & generator laporan eksekutif harian.

🗣️ **Naskah Bicara (Menit 07:05 – 08:00):**
> *"Terakhir, terkait risiko dan rencana pengembangan AI Chat Analyst ke depan. Risiko terbesar dalam interaksi pengguna adalah ambiguitas waktu bahasa alami dan kueri komposit multi-langkah yang belum bisa diselesaikan dengan satu panggilan tool. Selain itu, terdapat risiko halusinasi kausalitas jika pengguna menanyakan alasan di luar data, seperti 'mengapa sepi?'. Oleh karena itu, rencana kerja saya di Minggu 9 hingga 16 berfokus pada AI Engineering: pertama, mengimplementasikan chained tool calling untuk analisis berantai; kedua, menambahkan memori percakapan multi-turn; ketiga, menerapkan causal guardrail dan benchmark evaluasi otomatis dengan 50 kueri uji; serta keempat, menambahkan fitur deteksi anomali proaktif dan generator laporan otomatis. Terima kasih, saya siap untuk sesi tanya jawab."*

---

## 🎯 Panduan Menjawab 3 Pertanyaan Wajib UTS

### Pertanyaan 1: "Sebutkan satu keputusan rancangan Anda yang dapat dibuat berbeda, dan jelaskan mengapa Anda memilih yang ini."
**Cara Menjawab yang Dinilai "Sangat Baik":**
> *"Salah satu keputusan rancangan yang dapat dibuat berbeda adalah penggunaan **Text-to-SQL bebas berbasis LLM** versus **Deterministic Tool Calling**. Alternatif Text-to-SQL memang memberi kebebasan kueri lebih luas. Namun, saya memilih Tool Calling karena pada data analitik operasional fasilitas, kebenaran numerik dan keamanan data adalah harga mati. Text-to-SQL rentan halusinasi sintaks, kesalahan agregasi waktu, dan risiko keamanan injeksi database. Dengan Tool Calling, LLM dibatasi memanggil fungsi terverifikasi yang menghasilkan angka pasti dari SQLite."*

---

### Pertanyaan 2: "Tunjukkan satu input yang membuat sistem Anda gagal, dan jelaskan penyebab utamanya."
**Cara Menjawab yang Dinilai "Sangat Baik":**
> *"Input yang membuat sistem saya gagal adalah kueri perbandingan antarperiode di mana periode pembandingnya bernilai nol, misalnya: 'Bandingkan jumlah orang masuk hari ini dengan tanggal 1 Januari 2026' (saat sistem belum aktif). Penyebab utamanya adalah ZeroDivisionError pada implementasi rumus persentase perubahan $(N_{baru} - N_{lama}) / N_{lama}$. Saya menemukan kegagalan ini saat pengujian batas numerik, dan telah memperbaikinya dengan logika kondisional khusus di backend yang mengembalikan status bahwa basis awal bernilai nol, sehingga sistem tetap stabil."*

---

### Pertanyaan 3: "Bagian mana dari karya Anda yang dibuat dengan bantuan AI, dan bagaimana Anda memverifikasinya?"
**Cara Menjawab yang Dinilai "Sangat Baik":**
> *"Sebagian besar kode boilerplate Flask, antarmuka visual CSS Chart.js, serta kerangka fungsi analitik diinisiasi dengan bantuan asisten AI. Saya memverifikasinya secara ketat melalui tiga cara: pertama, membuat test suite otomatis dengan **Pytest berisi 10 skenario pengujian** yang menguji kalkulasi manual, boundary condition, dan out-of-scope intent; kedua, melakukan inspeksi langsung skema basis data SQLite dan log HTTP; dan ketiga, menguji akurasi angka hasil fungsi analitik terhadap perhitungan manual."*

---

## 👥 Format Lembar Peer Review (Komponen Tugas 5%)

Saat kamu menjadi reviewer untuk 2 rekan dari program studi lain:

```markdown
### Lembar Peer Review UTS
**Reviewer:** Fajar (Prodi Anda)
**Peserta yang Direview:** [Nama Teman] (Prodi: [Prodi Teman])
**Judul Sistem:** [Judul Sistem Teman]

1. Satu keputusan rancangan yang menurut saya paling kuat, beserta alasannya:
   [Jelaskan keputusan rancangan terbaiknya, misal: pemilihan model lokal untuk privasi, atau isolasi skema input].

2. Satu keputusan yang menurut saya berisiko, beserta alasannya:
   [Jelaskan titik lemah teknisnya secara spesifik, misal: ketergantungan pada prompt unconstrained tanpa validasi skema output].

3. Satu pertanyaan yang tidak sempat diajukan di sesi, tetapi layak dijawab:
   [Ajukan pertanyaan arsitektural yang kritis, misal: bagaimana sistem menangani latensi jika pengguna memasukkan input panjang?].

4. Satu hal dari rancangan teman yang ingin saya tiru untuk produk saya sendiri:
   [Sebutkan satu teknik/pola desain yang inspiratif dan aplikatif].
```
